import hashlib
from pathlib import Path


def content_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def relative_path_for(digest: str, suffix: str = ".pdf") -> Path:
    # Two-character prefix directory. A single flat directory holding thousands
    # of files is slow to list and unpleasant to inspect by hand.
    return Path(digest[:2]) / f"{digest}{suffix}"


def store(root: Path, payload: bytes, suffix: str = ".pdf") -> tuple[str, Path]:
    """Write payload under its own hash. Returns the digest and relative path.

    Idempotent: an identical file written twice occupies one path and is not
    rewritten, which is what makes re-running a crawl free.
    """
    digest = content_hash(payload)
    relative = relative_path_for(digest, suffix)
    absolute = root / relative
    if not absolute.exists():
        absolute.parent.mkdir(parents=True, exist_ok=True)
        absolute.write_bytes(payload)
    return digest, relative
