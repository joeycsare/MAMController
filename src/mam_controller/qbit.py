from __future__ import annotations
from dataclasses import dataclass
import hashlib
import requests


@dataclass(frozen=True)
class FarmState:
    used_bytes: int
    all_hashes: frozenset[str]
    mam_ids: frozenset[str]


class BencodeError(ValueError):
    pass


def _decode(data: bytes, pos: int = 0):
    if pos >= len(data):
        raise BencodeError("unexpected end of bencode data")
    token = data[pos:pos + 1]
    if token == b"i":
        end = data.find(b"e", pos)
        if end < 0:
            raise BencodeError("unterminated integer")
        return int(data[pos + 1:end]), end + 1
    if token == b"l":
        result = []
        pos += 1
        while data[pos:pos + 1] != b"e":
            value, pos = _decode(data, pos)
            result.append(value)
        return result, pos + 1
    if token == b"d":
        result = {}
        pos += 1
        while data[pos:pos + 1] != b"e":
            key, pos = _decode(data, pos)
            if not isinstance(key, bytes):
                raise BencodeError("dictionary key is not bytes")
            value, pos = _decode(data, pos)
            result[key] = value
        return result, pos + 1
    if token.isdigit():
        colon = data.find(b":", pos)
        if colon < 0:
            raise BencodeError("invalid byte string")
        length = int(data[pos:colon])
        start = colon + 1
        end = start + length
        if end > len(data):
            raise BencodeError("truncated byte string")
        return data[start:end], end
    raise BencodeError(f"invalid token at byte {pos}")


def torrent_metadata(data: bytes) -> tuple[str, int]:
    # Locate the exact bencoded value following top-level key `info`, because
    # BitTorrent hashes the original encoded bytes rather than a re-encoding.
    if not data.startswith(b"d"):
        raise BencodeError("torrent root is not a dictionary")
    pos = 1
    info = None
    raw_info = None
    while data[pos:pos + 1] != b"e":
        key, pos = _decode(data, pos)
        value_start = pos
        value, pos = _decode(data, pos)
        if key == b"info":
            info = value
            raw_info = data[value_start:pos]
    if not isinstance(info, dict) or raw_info is None:
        raise BencodeError("torrent has no info dictionary")
    if b"length" in info:
        size = int(info[b"length"])
    else:
        files = info.get(b"files")
        if not isinstance(files, list):
            raise BencodeError("torrent payload has neither length nor files")
        size = sum(int(item[b"length"]) for item in files)
    if size <= 0:
        raise BencodeError("torrent payload size must be positive")
    return hashlib.sha1(raw_info).hexdigest(), size


class QbitClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.base = f"http://{host}:{port}/api/v2"
        self.session = requests.Session()
        response = self.session.post(
            f"{self.base}/auth/login",
            data={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code != 200 or response.text.strip() != "Ok.":
            raise RuntimeError(f"qBittorrent authentication failed: HTTP {response.status_code}")

    def _get_json(self, path: str):
        response = self.session.get(f"{self.base}{path}", timeout=15)
        response.raise_for_status()
        return response.json()

    def ensure_category(self, category: str, save_path: str) -> None:
        categories = self._get_json("/torrents/categories")
        if category not in categories:
            response = self.session.post(
                f"{self.base}/torrents/createCategory",
                data={"category": category, "savePath": save_path},
                timeout=10,
            )
            response.raise_for_status()

    def farm_state(self, categories: set[str]) -> FarmState:
        torrents = self._get_json("/torrents/info")
        used = 0
        hashes: set[str] = set()
        mam_ids: set[str] = set()
        for torrent in torrents:
            hashes.add(str(torrent.get("hash", "")).lower())
            tags = {x.strip() for x in str(torrent.get("tags", "")).split(",") if x.strip()}
            for tag in tags:
                if tag.startswith("mam-id-"):
                    mam_ids.add(tag.removeprefix("mam-id-"))
            if str(torrent.get("category", "")) in categories:
                used += int(torrent.get("total_size") or torrent.get("size") or 0)
        return FarmState(used, frozenset(hashes), frozenset(mam_ids))

    def add(self, *, torrent: bytes, torrent_id: str, category: str, save_path: str) -> None:
        response = self.session.post(
            f"{self.base}/torrents/add",
            files={"torrents": (f"mam-{torrent_id}.torrent", torrent, "application/x-bittorrent")},
            data={
                "savepath": save_path,
                "category": category,
                "tags": f"mam-controller,mam-id-{torrent_id}",
                "autoTMM": "true",
            },
            timeout=20,
        )
        response.raise_for_status()
        if response.text.strip() not in {"Ok.", ""}:
            raise RuntimeError(f"qBittorrent add failed: {response.text[:200]}")

    def upload_limit(self) -> int:
        response = self.session.get(f"{self.base}/transfer/uploadLimit", timeout=10)
        response.raise_for_status()
        return int(response.text)

    def set_upload_limit(self, limit_bytes_per_second: int) -> None:
        response = self.session.post(
            f"{self.base}/transfer/setUploadLimit",
            data={"limit": limit_bytes_per_second},
            timeout=10,
        )
        response.raise_for_status()
