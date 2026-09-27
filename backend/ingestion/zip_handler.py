import zipfile
import shutil
import uuid
from pathlib import Path
from core.config import TEMP_DIR
from core.models import ProjectSource
from .walker import walk_project


async def ingest_zip(zip_path: str) -> ProjectSource:
    extract_dir = TEMP_DIR / f"zip_{uuid.uuid4().hex[:8]}"
    extract_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
    except zipfile.BadZipFile:
        raise ValueError("Invalid zip file.")
    contents = list(extract_dir.iterdir())
    actual_root = contents[0] if len(contents) == 1 and contents[0].is_dir() else extract_dir
    return walk_project(str(actual_root))


def cleanup_temp(root_path: str):
    shutil.rmtree(root_path, ignore_errors=True)
