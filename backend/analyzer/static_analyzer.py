import json
import re
from pathlib import Path
from core.models import ProjectSource, StaticAnalysisResult, DependencyInfo, FrameworkInfo, FileInfo


def _parse_package_json(content):
    deps, frameworks = [], []
    try:
        pkg = json.loads(content)
    except json.JSONDecodeError:
        return deps, frameworks
    framework_map = {
        "react": ("React","frontend"), "next": ("Next.js","frontend"), "vue": ("Vue.js","frontend"),
        "nuxt": ("Nuxt.js","frontend"), "angular": ("Angular","frontend"), "svelte": ("Svelte","frontend"),
        "express": ("Express","web"), "fastify": ("Fastify","web"), "koa": ("Koa","web"),
        "@nestjs/core": ("NestJS","web"), "mongoose": ("Mongoose","orm"),
        "sequelize": ("Sequelize","orm"), "prisma": ("Prisma","orm"),
        "@prisma/client": ("Prisma","orm"), "typeorm": ("TypeORM","orm"),
        "jest": ("Jest","testing"), "mocha": ("Mocha","testing"), "vitest": ("Vitest","testing"),
        "tailwindcss": ("Tailwind CSS","styling"), "socket.io": ("Socket.IO","realtime"),
        "graphql": ("GraphQL","api"), "typescript": ("TypeScript","language"),
    }
    for section, is_dev in [("dependencies", False), ("devDependencies", True)]:
        for name, version in pkg.get(section, {}).items():
            deps.append(DependencyInfo(name=name, version=version, dev_only=is_dev))
            key = name.lower()
            if key in framework_map:
                fn, cat = framework_map[key]
                frameworks.append(FrameworkInfo(name=fn, version=version, category=cat))
    return deps, frameworks


def _parse_requirements_txt(content):
    deps, frameworks = [], []
    framework_map = {
        "django": ("Django","web"), "flask": ("Flask","web"), "fastapi": ("FastAPI","web"),
        "tornado": ("Tornado","web"), "starlette": ("Starlette","web"),
        "sqlalchemy": ("SQLAlchemy","orm"), "djangorestframework": ("DRF","api"),
        "celery": ("Celery","task_queue"), "pytest": ("Pytest","testing"),
        "tensorflow": ("TensorFlow","ml"), "torch": ("PyTorch","ml"),
        "scikit-learn": ("scikit-learn","ml"), "pandas": ("Pandas","data"), "numpy": ("NumPy","data"),
    }
    for line in content.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("-"):
            continue
        match = re.match(r"^([a-zA-Z0-9_.-]+)\s*([><=!~].*)?$", line)
        if match:
            name = match.group(1)
            version = match.group(2) or None
            deps.append(DependencyInfo(name=name, version=version))
            if name.lower() in framework_map:
                fn, cat = framework_map[name.lower()]
                frameworks.append(FrameworkInfo(name=fn, version=version, category=cat))
    return deps, frameworks


def _parse_go_mod(content):
    deps, frameworks = [], []
    framework_map = {
        "gin-gonic/gin": ("Gin","web"), "gorilla/mux": ("Gorilla Mux","web"),
        "labstack/echo": ("Echo","web"), "gofiber/fiber": ("Fiber","web"),
        "gorm.io/gorm": ("GORM","orm"),
    }
    in_require = False
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("require"):
            in_require = True; continue
        if in_require and line == ")":
            in_require = False; continue
        if in_require:
            parts = line.split()
            if len(parts) >= 2:
                name, version = parts[0], parts[1]
                deps.append(DependencyInfo(name=name, version=version))
                for key, (fn, cat) in framework_map.items():
                    if key in name:
                        frameworks.append(FrameworkInfo(name=fn, version=version, category=cat))
    return deps, frameworks


def _detect_entry_points(files):
    entry_patterns = {
        "main.py","app.py","server.py","index.py","manage.py","wsgi.py","asgi.py",
        "main.ts","main.js","index.ts","index.js","server.ts","server.js","app.ts","app.js",
        "main.go","main.rs","main.java","Main.java","Program.cs","Startup.cs",
    }
    entries = []
    for f in files:
        if Path(f.relative_path).name in entry_patterns:
            entries.append(f.relative_path)
            f.is_entry_point = True
    return entries


def _detect_architecture(files):
    paths = {f.relative_path.lower().replace("\\", "/") for f in files}
    dir_names = set()
    for p in paths:
        dir_names.update(p.split("/")[:-1])
    if len({"models","views","controllers","templates"} & dir_names) >= 3:
        return "MVC"
    if {"services","routes","middleware"} & dir_names:
        return "Layered / Service-based"
    if any("docker-compose" in p for p in paths):
        if len([p for p in paths if "dockerfile" in p]) > 1:
            return "Microservices"
    if {"packages","libs","apps"} & dir_names:
        return "Monorepo"
    if {"components","pages","hooks"} & dir_names:
        return "Component-based (Frontend SPA)"
    return "Monolith"


def _detect_api_routes(files):
    routes = []
    patterns = [
        r'@app\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
        r'router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)',
        r'@(Get|Post|Put|Delete|Patch)Mapping\s*\(\s*["\']?([^"\')\s]+)',
        r'path\s*\(\s*["\']([^"\']+)',
    ]
    for f in files:
        if not f.content:
            continue
        for pattern in patterns:
            for match in re.finditer(pattern, f.content):
                routes.append(match.groups()[-1])
    return list(set(routes))[:50]


def _detect_ci(files):
    ci_files = {
        ".github/workflows": "GitHub Actions", ".gitlab-ci.yml": "GitLab CI",
        "Jenkinsfile": "Jenkins", ".circleci/config.yml": "CircleCI",
        ".travis.yml": "Travis CI", "azure-pipelines.yml": "Azure Pipelines",
    }
    for f in files:
        for ci_path, ci_name in ci_files.items():
            if ci_path in f.relative_path:
                return True, ci_name
    return False, None


def run_static_analysis(project: ProjectSource) -> StaticAnalysisResult:
    all_deps, all_frameworks = [], []
    readme_content = None
    dep_parsers = {
        "package.json": _parse_package_json,
        "requirements.txt": _parse_requirements_txt,
        "go.mod": _parse_go_mod,
    }
    for f in project.files:
        fname = Path(f.relative_path).name.lower()
        if fname in dep_parsers and f.content:
            deps, fws = dep_parsers[fname](f.content)
            all_deps.extend(deps); all_frameworks.extend(fws)
        config_names = {
            "package.json","tsconfig.json","docker-compose.yml","dockerfile",
            "makefile","pyproject.toml","setup.py","settings.py","config.py",
        }
        if fname in config_names:
            f.is_config = True
        if "test" in fname or "spec" in fname or "/tests/" in f.relative_path.lower():
            f.is_test = True
        if fname in ("readme.md","readme.rst","readme.txt","readme"):
            readme_content = f.content

    entry_points = _detect_entry_points(project.files)
    architecture = _detect_architecture(project.files)
    api_routes = _detect_api_routes(project.files)
    has_ci, ci_tool = _detect_ci(project.files)
    test_files = [f.relative_path for f in project.files if f.is_test]
    has_docker = any("dockerfile" in f.relative_path.lower() or "docker-compose" in f.relative_path.lower() for f in project.files)
    has_env = any(f.relative_path.endswith(".env") or f.relative_path.endswith(".env.example") for f in project.files)
    primary_language = max(project.languages, key=project.languages.get) if project.languages else None
    db_schemas = [f.relative_path for f in project.files if any(kw in f.relative_path.lower() for kw in ["migration","schema","model",".sql","entity"])]

    return StaticAnalysisResult(
        frameworks=all_frameworks, dependencies=all_deps, entry_points=entry_points,
        architecture_pattern=architecture, has_tests=len(test_files) > 0,
        test_files=test_files[:30], has_ci=has_ci, ci_tool=ci_tool,
        has_docker=has_docker, has_env_file=has_env, readme_exists=readme_content is not None,
        readme_content=readme_content[:5000] if readme_content else None,
        primary_language=primary_language, api_routes=api_routes, db_schemas=db_schemas[:20],
    )
