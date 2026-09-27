import os
from pathlib import Path
from core.models import FileInfo, ProjectSource
from core.config import SKIP_DIRS, SKIP_EXTENSIONS, SKIP_FILES, MAX_FILE_SIZE_BYTES, EXTENSION_TO_LANGUAGE


def detect_language(file_path: str) -> str | None:
    ext = Path(file_path).suffix.lower()
    if ext in EXTENSION_TO_LANGUAGE:
        return EXTENSION_TO_LANGUAGE[ext]
    name = Path(file_path).name.lower()
    if name == "dockerfile":
        return "Dockerfile"
    if name == "makefile":
        return "Makefile"
    return None


def should_skip(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    for part in parts:
        if part in SKIP_DIRS or part.startswith("."):
            return True
    if path.is_file():
        if path.name in SKIP_FILES:
            return True
        if path.suffix.lower() in SKIP_EXTENSIONS:
            return True
        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            return True
    return False


def build_file_tree(root: Path, max_depth: int = 4) -> str:
    lines = [root.name + "/"]

    def _walk(dir_path: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
        except PermissionError:
            return
        dirs = [e for e in entries if e.is_dir() and not should_skip(e, root)]
        files = [e for e in entries if e.is_file() and not should_skip(e, root)]
        items = dirs + files
        for i, entry in enumerate(items):
            is_last = (i == len(items) - 1)
            connector = "└── " if is_last else "├── "
            if entry.is_dir():
                lines.append(f"{prefix}{connector}{entry.name}/")
                extension = "    " if is_last else "│   "
                _walk(entry, prefix + extension, depth + 1)
            else:
                lines.append(f"{prefix}{connector}{entry.name}")

    _walk(root, "", 0)
    return "\n".join(lines[:500])


def walk_project(root_path: str) -> ProjectSource:
    root = Path(root_path)
    files: list[FileInfo] = []
    languages: dict[str, int] = {}
    total_size = 0

    for dirpath, dirnames, filenames in os.walk(root):
        dir_p = Path(dirpath)
        dirnames[:] = [d for d in dirnames if not should_skip(dir_p / d, root)]

        for fname in filenames:
            fpath = dir_p / fname
            if should_skip(fpath, root):
                continue
            rel_path = str(fpath.relative_to(root))
            lang = detect_language(str(fpath))
            size = fpath.stat().st_size
            total_size += size
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            content = None
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                pass
            files.append(FileInfo(
                path=str(fpath),
                relative_path=rel_path,
                language=lang,
                size_bytes=size,
                content=content,
            ))

    return ProjectSource(
        root_path=root_path,
        files=files,
        total_files=len(files),
        total_size_bytes=total_size,
        languages=languages,
        file_tree=build_file_tree(root),
    )
