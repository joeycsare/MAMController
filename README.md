# mam-controller complete

Pinned supplied MightyMouse with MAM API health gate, 300 GiB planning/admission limits, Jellyfin bandwidth controller, and full dry-run controls.

Defaults are `DRY_RUN=true` and `BANDWIDTH_DRY_RUN=true`. No torrents are downloaded, no qBittorrent categories or watched-folder files are changed, no bonus purchases occur, and no upload limit is changed. Read-only API checks and plans still run.

Configure `/config/config.py`, use `AUTO_EXTRACT_DIR="/staging"`, and keep `MAM_DOWNLOAD_ENABLED=False` initially. For live operation set both dry-run variables to `false`, set `MAM_DOWNLOAD_ENABLED=True`, and recreate the container. qBittorrent watches `/watch`, never `/staging`.
