
from dotenv import load_dotenv

load_dotenv()
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
TEMP_DIR = BASE_DIR / "temp"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

MAX_FILE_SIZE_BYTES = 500_000
MAX_CONTEXT_TOKENS = 800_000
CHARS_PER_TOKEN = 4
MAX_FILES_FULL_CONTENT = 150

SKIP_DIRS = {
    "node_modules", ".git", "__pycache__", ".venv", "venv", "env",
    ".env", "dist", "build", ".next", ".nuxt", "vendor", ".idea",
    ".vscode", "coverage", ".mypy_cache", ".pytest_cache", "target",
    ".gradle", "bin", "obj", ".DS_Store", ".svn", "bower_components",
    ".tox", "eggs", "*.egg-info", ".sass-cache", ".cache",
}

SKIP_EXTENSIONS = {
    ".pyc", ".pyo", ".class", ".o", ".so", ".dll", ".exe",
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".bmp",
    ".mp3", ".mp4", ".wav", ".avi", ".mov",
    ".zip", ".tar", ".gz", ".rar", ".7z",
    ".pdf", ".doc", ".xls", ".ppt",
    ".woff", ".woff2", ".ttf", ".eot",
    ".lock", ".map", ".min.js", ".min.css", ".DS_Store",
}

SKIP_FILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
    "composer.lock", "Gemfile.lock", "Pipfile.lock",
    "poetry.lock", ".gitignore", ".dockerignore",
}

EXTENSION_TO_LANGUAGE = {
    ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
    ".jsx": "React JSX", ".tsx": "React TSX",
    ".java": "Java", ".kt": "Kotlin", ".scala": "Scala",
    ".go": "Go", ".rs": "Rust", ".rb": "Ruby",
    ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C",
    ".swift": "Swift", ".m": "Objective-C",
    ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".less": "LESS",
    ".sql": "SQL", ".graphql": "GraphQL", ".gql": "GraphQL",
    ".sh": "Shell", ".bash": "Shell", ".zsh": "Shell",
    ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML",
    ".json": "JSON", ".xml": "XML",
    ".md": "Markdown", ".rst": "reStructuredText",
    ".r": "R", ".jl": "Julia", ".lua": "Lua",
    ".dart": "Dart", ".vue": "Vue", ".svelte": "Svelte",
    ".tf": "Terraform", ".hcl": "HCL",
    ".proto": "Protocol Buffers",
}
