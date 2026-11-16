# mam-controller

Clean, environment-only replacement for the earlier bundled MightyMouse container.

## Features
- Uses only a pre-created `MAM_ID` session cookie. No email/password or Selenium login.
- Searches documented MAM torrent API endpoints for audiobook freeleech candidates.
- Verifies actual `.torrent` payload size before adding to qBittorrent.
- Enforces a hard qBittorrent category budget with a configurable reserve.
- Starts safely in complete dry-run mode.
- Dynamically reduces qBittorrent upload bandwidth for external Jellyfin streams.
- Publishes `edge`, `main`, semantic-version, and SHA images using GitHub Actions.

## Important limitation
The supplied API reference does not document the structure required to determine whether an individual torrent has become satisfied. This build therefore adds new farm torrents to `MAM_UNSAT` but does not automatically move them to `MAM_SAT`. Do not auto-delete `MAM_UNSAT` torrents. Add SAT synchronization only after a documented or verified API contract and tests are available.

## Start
1. Copy `.env.example` to `.env` and fill `MAM_ID`, qBittorrent, and Jellyfin values.
2. Replace `YOUR_GITHUB_USER` in `compose.yaml`.
3. Keep `DRY_RUN=true` and `BANDWIDTH_DRY_RUN=true` for first deployment.
4. Run `docker compose up -d`.
5. Review logs: `docker logs -f mam-controller`.
6. Enable each mutation independently after validation.
