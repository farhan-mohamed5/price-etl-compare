import os
from pathlib import Path
from .config import settings

def ensure_storage_dir() -> str:
    Path(settings.storage_dir).mkdir(parents=True, exist_ok=True)
    return settings.storage_dir

def save_upload_bytes(file_name: str, data: bytes) -> str:
    storage = ensure_storage_dir()
    # avoid collisions
    safe = file_name.replace("/", "_").replace("\\", "_")
    path = Path(storage) / safe
    if path.exists():
        stem, suffix = path.stem, path.suffix
        i = 1
        while True:
            candidate = Path(storage) / f"{stem}_{i}{suffix}"
            if not candidate.exists():
                path = candidate
                break
            i += 1
    path.write_bytes(data)
    return str(path)
