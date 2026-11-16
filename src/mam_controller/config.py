from __future__ import annotations
from dataclasses import dataclass
import os


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name, str(default)).strip().lower()
    if value not in {"1", "0", "true", "false", "yes", "no", "on", "off"}:
        raise ValueError(f"{name} must be boolean, got {value!r}")
    return value in {"1", "true", "yes", "on"}


def _int(name: str, default: int, minimum: int = 0) -> int:
    value = int(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


def _float(name: str, default: float, minimum: float = 0.0) -> float:
    value = float(os.getenv(name, str(default)))
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return value


@dataclass(frozen=True)
class Settings:
    mam_id: str
    mam_base_url: str
    dry_run: bool
    run_ratio_controller: bool
    run_bandwidth_controller: bool
    ratio_interval_seconds: int
    storage_limit_gib: float
    storage_reserve_gib: float
    mam_main_category: int
    mam_search_type: str
    mam_search_pages: int
    mam_search_per_page: int
    mam_max_add_per_run: int
    mam_min_candidate_mib: int
    mam_max_candidate_gib: float
    qbit_host: str
    qbit_port: int
    qbit_username: str
    qbit_password: str
    qbit_category_unsat: str
    qbit_category_sat: str
    qbit_save_path: str
    jellyfin_url: str
    jellyfin_api_key: str
    bandwidth_dry_run: bool
    bandwidth_poll_seconds: int
    bandwidth_increase_delay_seconds: int
    qbit_limit_0_mib: float
    qbit_limit_1_mib: float
    qbit_limit_2_mib: float
    qbit_limit_3plus_mib: float
    local_networks: tuple[str, ...]

    @classmethod
    def from_env(cls) -> "Settings":
        settings = cls(
            mam_id=os.getenv("MAM_ID", "").strip(),
            mam_base_url=os.getenv("MAM_BASE_URL", "https://www.myanonamouse.net").rstrip("/"),
            dry_run=_bool("DRY_RUN", True),
            run_ratio_controller=_bool("RUN_RATIO_CONTROLLER", True),
            run_bandwidth_controller=_bool("RUN_BANDWIDTH_CONTROLLER", True),
            ratio_interval_seconds=_int("RATIO_INTERVAL_SECONDS", 3600, 60),
            storage_limit_gib=_float("STORAGE_LIMIT_GIB", 300.0, 1.0),
            storage_reserve_gib=_float("STORAGE_RESERVE_GIB", 5.0, 0.0),
            mam_main_category=_int("MAM_MAIN_CATEGORY", 13, 1),
            mam_search_type=os.getenv("MAM_SEARCH_TYPE", "fl").strip(),
            mam_search_pages=_int("MAM_SEARCH_PAGES", 5, 1),
            mam_search_per_page=_int("MAM_SEARCH_PER_PAGE", 100, 5),
            mam_max_add_per_run=_int("MAM_MAX_ADD_PER_RUN", 3, 0),
            mam_min_candidate_mib=_int("MAM_MIN_CANDIDATE_MIB", 0, 0),
            mam_max_candidate_gib=_float("MAM_MAX_CANDIDATE_GIB", 25.0, 0.0),
            qbit_host=os.getenv("QBIT_HOST", "gluetun").strip(),
            qbit_port=_int("QBIT_PORT", 8080, 1),
            qbit_username=os.getenv("QBIT_USERNAME", "").strip(),
            qbit_password=os.getenv("QBIT_PASSWORD", ""),
            qbit_category_unsat=os.getenv("QBIT_CATEGORY_UNSAT", "MAM_UNSAT").strip(),
            qbit_category_sat=os.getenv("QBIT_CATEGORY_SAT", "MAM_SAT").strip(),
            qbit_save_path=os.getenv("QBIT_SAVE_PATH", "/data/mam-seed").strip(),
            jellyfin_url=os.getenv("JELLYFIN_URL", "http://jellyfin:8096").rstrip("/"),
            jellyfin_api_key=os.getenv("JELLYFIN_API_KEY", "").strip(),
            bandwidth_dry_run=_bool("BANDWIDTH_DRY_RUN", True),
            bandwidth_poll_seconds=_int("BANDWIDTH_POLL_SECONDS", 10, 5),
            bandwidth_increase_delay_seconds=_int("BANDWIDTH_INCREASE_DELAY_SECONDS", 60, 0),
            qbit_limit_0_mib=_float("QBIT_LIMIT_0_STREAMS_MIB", 4.0, 0.05),
            qbit_limit_1_mib=_float("QBIT_LIMIT_1_STREAM_MIB", 2.0, 0.05),
            qbit_limit_2_mib=_float("QBIT_LIMIT_2_STREAMS_MIB", 1.0, 0.05),
            qbit_limit_3plus_mib=_float("QBIT_LIMIT_3PLUS_STREAMS_MIB", 0.5, 0.05),
            local_networks=tuple(x.strip() for x in os.getenv(
                "LOCAL_NETWORKS", "192.168.0.0/16,10.0.0.0/8,172.16.0.0/12"
            ).split(",") if x.strip()),
        )
        if settings.mam_search_type not in {"all", "active", "inactive", "fl", "fl-VIP", "VIP", "nVIP", "nMeta"}:
            raise ValueError("Unsupported MAM_SEARCH_TYPE")
        if settings.mam_search_per_page > 1000:
            raise ValueError("MAM_SEARCH_PER_PAGE must be <= 1000")
        if settings.storage_reserve_gib >= settings.storage_limit_gib:
            raise ValueError("STORAGE_RESERVE_GIB must be below STORAGE_LIMIT_GIB")
        return settings
