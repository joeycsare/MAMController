from __future__ import annotations
import ipaddress
import logging
import time
import requests
from .config import Settings
from .qbit import QbitClient

log = logging.getLogger(__name__)


def endpoint_ip(value: str | None):
    if not value:
        return None
    value = value.strip()
    if value.startswith("[") and "]" in value:
        value = value[1:value.index("]")]
    elif value.count(":") == 1:
        value = value.rsplit(":", 1)[0]
    try:
        return ipaddress.ip_address(value)
    except ValueError:
        return None


def count_external_streams(settings: Settings, session: requests.Session) -> int:
    response = session.get(f"{settings.jellyfin_url}/Sessions", timeout=10)
    response.raise_for_status()
    networks = [ipaddress.ip_network(item) for item in settings.local_networks]
    count = 0
    for item in response.json():
        if not item.get("NowPlayingItem"):
            continue
        if item.get("PlayState", {}).get("IsPaused", False):
            continue
        address = endpoint_ip(item.get("RemoteEndPoint"))
        # Unknown addresses are external by policy, protecting stream quality.
        if address is not None and any(address in network for network in networks):
            continue
        count += 1
    return count


def target_mib(settings: Settings, streams: int) -> float:
    if streams <= 0:
        return settings.qbit_limit_0_mib
    if streams == 1:
        return settings.qbit_limit_1_mib
    if streams == 2:
        return settings.qbit_limit_2_mib
    return settings.qbit_limit_3plus_mib


def run_bandwidth_loop(settings: Settings) -> None:
    if not settings.jellyfin_api_key:
        raise ValueError("JELLYFIN_API_KEY is required when bandwidth controller is enabled")
    session = requests.Session()
    session.headers["X-Emby-Token"] = settings.jellyfin_api_key
    qbit = QbitClient(settings.qbit_host, settings.qbit_port, settings.qbit_username, settings.qbit_password)
    applied: int | None = None
    pending: int | None = None
    pending_since = 0.0
    while True:
        try:
            streams = count_external_streams(settings, session)
            apply_now = applied is None or streams > applied
            if applied is not None and streams < applied:
                if pending != streams:
                    pending = streams
                    pending_since = time.monotonic()
                elif time.monotonic() - pending_since >= settings.bandwidth_increase_delay_seconds:
                    if count_external_streams(settings, session) == streams:
                        apply_now = True
            elif streams == applied:
                pending = None
            if apply_now:
                mib = target_mib(settings, streams)
                if settings.bandwidth_dry_run:
                    log.info("BANDWIDTH DRY RUN: %d external stream(s), would set %.2f MiB/s", streams, mib)
                else:
                    target = int(mib * 1024 ** 2)
                    if qbit.upload_limit() != target:
                        qbit.set_upload_limit(target)
                        log.info("%d external stream(s), set %.2f MiB/s", streams, mib)
                applied = streams
                pending = None
            time.sleep(settings.bandwidth_poll_seconds)
        except Exception:
            log.exception("Bandwidth cycle failed; not raising qBittorrent limit")
            time.sleep(settings.bandwidth_poll_seconds)
