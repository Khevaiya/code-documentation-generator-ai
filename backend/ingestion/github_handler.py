import subprocess
import uuid
import re
import shutil
from core.config import TEMP_DIR
from core.models import ProjectSource
from .walker import walk_project


def parse_github_url(url: str) -> dict:
    patterns = [
        r"github\.com[:/](?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?(?:/tree/(?P<branch>.+))?$",
        r"github\.com[:/](?P<owner>[\w.-]+)/(?P<repo>[\w.-]+?)(?:\.git)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url.strip())
        if match:
            groups = match.groupdict()
            return {"owner": groups["owner"], "repo": groups["repo"], "branch": groups.get("branch")}
    raise ValueError(f"Invalid GitHub URL: {url}")


async def ingest_github(github_url: str) -> ProjectSource:
    parsed = parse_github_url(github_url)
    clone_dir = TEMP_DIR / f"gh_{parsed['repo']}_{uuid.uuid4().hex[:8]}"
    clone_dir.mkdir(parents=True, exist_ok=True)
    clone_url = f"https://github.com/{parsed['owner']}/{parsed['repo']}.git"
    cmd = ["git", "clone", "--depth", "1"]
    if parsed.get("branch"):
        cmd.extend(["--branch", parsed["branch"]])
    cmd.extend([clone_url, str(clone_dir)])
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"git clone failed: {result.stderr}")
    return walk_project(str(clone_dir))


def cleanup_clone(root_path: str):
    shutil.rmtree(root_path, ignore_errors=True)
