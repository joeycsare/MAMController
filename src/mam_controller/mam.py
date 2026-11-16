from __future__ import annotations
from dataclasses import dataclass
import logging
import requests

log = logging.getLogger(__name__)


class MamApiError(RuntimeError):
    pass


def booleanish(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


@dataclass(frozen=True)
class Candidate:
    torrent_id: str
    title: str
    size_bytes: int
    seeders: int
    leechers: int
    free: bool
    vip: bool


class MamClient:
    def __init__(self, base_url: str, mam_id: str, timeout: int = 20):
        if not mam_id:
            raise ValueError("MAM_ID is required")
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.cookies.set("mam_id", mam_id)
        self.session.headers.update({"Accept": "application/json", "User-Agent": "mam-controller/0.1"})

    def _json(self, response: requests.Response, operation: str) -> dict:
        if response.status_code != 200:
            raise MamApiError(f"{operation}: HTTP {response.status_code}")
        content_type = response.headers.get("content-type", "")
        if "json" not in content_type.lower():
            raise MamApiError(f"{operation}: expected JSON, got {content_type or 'unknown content type'}")
        try:
            data = response.json()
        except ValueError as exc:
            raise MamApiError(f"{operation}: invalid JSON") from exc
        if not isinstance(data, dict):
            raise MamApiError(f"{operation}: expected JSON object")
        return data

    def get_user_data(self, include_snatch_summary: bool = True) -> dict:
        params = {"snatch_summary": ""} if include_snatch_summary else None
        response = self.session.get(f"{self.base_url}/jsonLoad.php", params=params, timeout=self.timeout)
        data = self._json(response, "get user data")
        required = {"username", "uid", "classname", "ratio", "uploaded", "downloaded"}
        missing = sorted(required - data.keys())
        if missing:
            raise MamApiError(f"get user data: missing fields {', '.join(missing)}")
        return data

    def search(self, *, main_category: int, search_type: str, start_number: int, per_page: int) -> dict:
        payload = {
            "tor": {
                "text": "",
                "srchIn": ["title", "author", "narrator", "series"],
                "searchType": search_type,
                "searchIn": "torrents",
                "main_cat": [main_category],
                "sortType": "seedersAsc",
                "startNumber": start_number,
            },
            "perpage": per_page,
        }
        response = self.session.post(
            f"{self.base_url}/tor/js/loadSearchJSONbasic.php",
            json=payload,
            timeout=self.timeout,
        )
        data = self._json(response, "torrent search")
        if not isinstance(data.get("data"), list):
            raise MamApiError("torrent search: missing data array")
        return data

    @staticmethod
    def candidate(raw: dict) -> Candidate:
        torrent_id = str(raw["id"])
        title = str(raw.get("title") or raw.get("name") or f"MAM {torrent_id}")
        size_text = str(raw["size"])
        if not size_text.isdigit():
            raise MamApiError(f"torrent {torrent_id}: size is not decimal digits")
        return Candidate(
            torrent_id=torrent_id,
            title=title,
            size_bytes=int(size_text),
            seeders=int(raw.get("seeders", 0) or 0),
            leechers=int(raw.get("leechers", 0) or 0),
            free=booleanish(raw.get("free")),
            vip=booleanish(raw.get("vip")),
        )

    def download_torrent(self, torrent_id: str) -> bytes:
        response = self.session.get(
            f"{self.base_url}/tor/download.php",
            params={"tid": torrent_id},
            headers={"Accept": "application/x-bittorrent, application/octet-stream"},
            timeout=self.timeout,
        )
        if response.status_code != 200:
            raise MamApiError(f"download torrent {torrent_id}: HTTP {response.status_code}")
        body = response.content
        if not body or body[:1] != b"d":
            raise MamApiError(f"download torrent {torrent_id}: response is not bencoded torrent data")
        return body
