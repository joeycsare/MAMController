from __future__ import annotations
import logging
from .config import Settings
from .mam import MamClient, MamApiError, Candidate
from .qbit import QbitClient, torrent_metadata

log = logging.getLogger(__name__)
GIB = 1024 ** 3
MIB = 1024 ** 2


def score(candidate: Candidate) -> tuple[int, int, int]:
    # Prefer lower seed saturation, then more leechers, then smaller payloads.
    return (candidate.seeders, -candidate.leechers, candidate.size_bytes)


def run_ratio_cycle(settings: Settings) -> None:
    mam = MamClient(settings.mam_base_url, settings.mam_id)
    account = mam.get_user_data(include_snatch_summary=True)
    log.info("MAM account=%s class=%s ratio=%s", account["username"], account["classname"], account["ratio"])

    qbit = QbitClient(settings.qbit_host, settings.qbit_port, settings.qbit_username, settings.qbit_password)
    categories = {settings.qbit_category_unsat, settings.qbit_category_sat}
    state = qbit.farm_state(categories)
    cap = int(settings.storage_limit_gib * GIB)
    reserve = int(settings.storage_reserve_gib * GIB)
    available = max(0, cap - reserve - state.used_bytes)
    log.info("Farm used %.2f GiB, available %.2f GiB, cap %.2f GiB, reserve %.2f GiB",
             state.used_bytes / GIB, available / GIB, cap / GIB, reserve / GIB)
    if available <= 0 or settings.mam_max_add_per_run == 0:
        return

    raw_candidates: list[dict] = []
    for page in range(settings.mam_search_pages):
        result = mam.search(
            main_category=settings.mam_main_category,
            search_type=settings.mam_search_type,
            start_number=page * settings.mam_search_per_page,
            per_page=settings.mam_search_per_page,
        )
        raw_candidates.extend(result["data"])

    candidates: list[Candidate] = []
    for raw in raw_candidates:
        try:
            item = mam.candidate(raw)
        except (KeyError, TypeError, ValueError, MamApiError) as exc:
            log.warning("Skip malformed search result: %s", exc)
            continue
        if item.torrent_id in state.mam_ids:
            continue
        if settings.mam_search_type == "fl" and not item.free:
            continue
        if item.size_bytes < settings.mam_min_candidate_mib * MIB:
            continue
        if settings.mam_max_candidate_gib and item.size_bytes > settings.mam_max_candidate_gib * GIB:
            continue
        candidates.append(item)

    selected: list[Candidate] = []
    planned = 0
    for item in sorted(candidates, key=score):
        if len(selected) >= settings.mam_max_add_per_run:
            break
        if planned + item.size_bytes > available:
            continue
        selected.append(item)
        planned += item.size_bytes

    if not selected:
        log.info("No candidate fits the filters and storage budget")
        return

    log.info("Selected %d torrent(s), API-planned payload %.2f GiB", len(selected), planned / GIB)
    for item in selected:
        if settings.dry_run:
            log.info("DRY RUN: would add MAM %s, %.2f GiB, seeders=%d, leechers=%d, title=%s",
                     item.torrent_id, item.size_bytes / GIB, item.seeders, item.leechers, item.title)
            continue
        torrent = mam.download_torrent(item.torrent_id)
        info_hash, actual_size = torrent_metadata(torrent)
        # Fail closed if documented search size and actual torrent metadata disagree materially.
        if actual_size != item.size_bytes:
            raise RuntimeError(
                f"MAM {item.torrent_id}: search size {item.size_bytes} differs from torrent payload {actual_size}"
            )
        current = qbit.farm_state(categories)
        if info_hash in current.all_hashes:
            log.info("MAM %s already present by info hash", item.torrent_id)
            continue
        if current.used_bytes + actual_size + reserve > cap:
            log.warning("MAM %s blocked by hard storage cap", item.torrent_id)
            continue
        qbit.ensure_category(settings.qbit_category_unsat, settings.qbit_save_path)
        qbit.add(
            torrent=torrent,
            torrent_id=item.torrent_id,
            category=settings.qbit_category_unsat,
            save_path=settings.qbit_save_path,
        )
        log.info("Added MAM %s to qBittorrent", item.torrent_id)
