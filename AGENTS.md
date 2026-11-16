# Coding-agent rules

Canonical API sources:
- `docs/MAM_API_REFERENCE.md` for meaning, uncertainties, and source fidelity.
- `spec/mam-api.openapi.yaml` for the machine-readable contract.

Hard rules:
1. Authentication uses only `MAM_ID` as a session cookie. Never add username/password or headless-login code.
2. Do not automate `gift` or `sendWedge`.
3. Never add the torrent-download `fl` parameter implicitly.
4. Any MAM schema mismatch must fail closed.
5. Every mutation must respect its dry-run switch.
6. Farm payload in `MAM_UNSAT` + `MAM_SAT`, plus reserve, must remain under `STORAGE_LIMIT_GIB`.
7. Search-result size is treated as decimal bytes only after validating digits; actual `.torrent` metadata is authoritative before adding.
8. Do not silently resolve source inconsistencies. Update documentation, OpenAPI, fixtures, and tests together.
