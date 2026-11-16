from __future__ import annotations
import logging
import signal
import threading
import time
from .bandwidth import run_bandwidth_loop
from .config import Settings
from .ratio import run_ratio_cycle

log = logging.getLogger(__name__)
stop = threading.Event()


def _signal(*_):
    stop.set()


def ratio_loop(settings: Settings) -> None:
    while not stop.is_set():
        try:
            run_ratio_cycle(settings)
        except Exception:
            log.exception("Ratio cycle failed closed")
        stop.wait(settings.ratio_interval_seconds)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")
    settings = Settings.from_env()
    signal.signal(signal.SIGTERM, _signal)
    signal.signal(signal.SIGINT, _signal)
    threads: list[threading.Thread] = []
    if settings.run_ratio_controller:
        threads.append(threading.Thread(target=ratio_loop, args=(settings,), name="ratio", daemon=True))
    if settings.run_bandwidth_controller:
        threads.append(threading.Thread(target=run_bandwidth_loop, args=(settings,), name="bandwidth", daemon=True))
    if not threads:
        raise RuntimeError("No controller enabled")
    for thread in threads:
        thread.start()
    while not stop.is_set():
        if any(not thread.is_alive() for thread in threads):
            raise RuntimeError("Controller thread exited unexpectedly")
        stop.wait(5)


if __name__ == "__main__":
    main()
