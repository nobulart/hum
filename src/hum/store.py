"""Atomic persistence primitives: locking, temp-file writes, run ids."""
from __future__ import annotations

import fcntl
import os
import tempfile
import uuid


def run_id() -> str:
    return uuid.uuid4().hex[:12]


def ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)


def atomic_write(path: str, text: str) -> None:
    """Write text to path via a temp file + os.replace (atomic on POSIX)."""
    ensure_dir(path)
    directory = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, path)
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def read_text(path: str) -> str:
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def existing_surfaced_ids(path: str) -> set[str]:
    """Ids already present in a SURFACE-style file (for idempotent appends)."""
    if not os.path.exists(path):
        return set()
    from . import parser
    ids = set()
    for b in parser.parse_document(read_text(path)):
        if b["fm_ok"]:
            try:
                import yaml
                fm = yaml.safe_load(b["raw_fm"]) or {}
                if fm.get("id"):
                    ids.add(str(fm["id"]))
            except Exception:
                pass
    return ids


class FileLock:
    """Exclusive advisory lock on ``path`` (blocks concurrent capture/surface)."""

    def __init__(self, path: str):
        self.lock_path = path + ".lock"
        self._fh = None

    def __enter__(self) -> "FileLock":
        self._fh = open(self.lock_path, "w")
        fcntl.flock(self._fh, fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc) -> None:
        assert self._fh is not None
        try:
            fcntl.flock(self._fh, fcntl.LOCK_UN)
        except Exception:
            pass
        try:
            self._fh.close()
        except Exception:
            pass
