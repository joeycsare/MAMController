from __future__ import annotations
import sys
from .config import Settings
from .mam import MamClient
from .qbit import QbitClient


def main() -> int:
    try:
        settings = Settings.from_env()
        MamClient(settings.mam_base_url, settings.mam_id).get_user_data(include_snatch_summary=True)
        qbit = QbitClient(settings.qbit_host, settings.qbit_port, settings.qbit_username, settings.qbit_password)
        qbit.farm_state({settings.qbit_category_unsat, settings.qbit_category_sat})
        return 0
    except Exception as exc:
        print(f"healthcheck failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
