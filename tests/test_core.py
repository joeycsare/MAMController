import os
from mam_controller.bandwidth import endpoint_ip, target_mib
from mam_controller.config import Settings
from mam_controller.mam import booleanish, MamClient
from mam_controller.qbit import torrent_metadata


def bstr(value: bytes) -> bytes:
    return str(len(value)).encode() + b":" + value


def settings():
    os.environ.setdefault("MAM_ID", "x")
    return Settings.from_env()


def test_booleanish():
    assert booleanish("1") is True
    assert booleanish("0") is False
    assert booleanish(1) is True


def test_candidate_accepts_name_and_decimal_size():
    item = MamClient.candidate({"id": "42", "name": "Book", "size": "1024", "free": "1"})
    assert item.title == "Book"
    assert item.size_bytes == 1024
    assert item.free is True


def test_torrent_metadata_single_file():
    info = b"d" + bstr(b"length") + b"i123e" + bstr(b"name") + bstr(b"a") + b"e"
    raw = b"d" + bstr(b"announce") + bstr(b"x") + bstr(b"info") + info + b"e"
    digest, size = torrent_metadata(raw)
    assert len(digest) == 40
    assert size == 123


def test_endpoint_ip():
    assert str(endpoint_ip("192.168.1.2:8096")) == "192.168.1.2"
    assert str(endpoint_ip("[2001:db8::1]:8096")) == "2001:db8::1"


def test_bandwidth_targets():
    cfg = settings()
    assert target_mib(cfg, 0) == 4.0
    assert target_mib(cfg, 3) == 0.5
