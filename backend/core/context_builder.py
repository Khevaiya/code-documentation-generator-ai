from core.models import ProjectSource, StaticAnalysisResult, FileInfo
from core.config import MAX_CONTEXT_TOKENS, CHARS_PER_TOKEN, MAX_FILES_FULL_CONTENT


def estimate_tokens(text: str) -> int:
    return len(text) // CHARS_PER_TOKEN


def _assign_priority(file: FileInfo, analysis: StaticAnalysisResult) -> int:
    score = 0
    if file.is_entry_point: score += 100
    if file.is_config: score += 80
    if file.relative_path.lower().startswith("readme"): score += 90
    route_keywords = ["route", "controller", "endpoint", "api", "handler", "view"]
    if any(kw in file.relative_path.lower() for kw in route_keywords): score += 70
    model_keywords = ["model", "schema", "entity", "migration"]
    if any(kw in file.relative_path.lower() for kw in model_keywords): score += 60
    if any(kw in file.relative_path.lower() for kw in ["middleware", "auth", "security"]): score += 65
    if "service" in file.relative_path.lower(): score += 55
    if file.is_test: score += 20
    score -= file.relative_path.count("/") * 3
    if file.size_bytes > 100_000: score -= 30
    code_langs = {"Python","JavaScript","TypeScript","Java","Go","Rust","C#","Ruby","PHP","Kotlin"}
    if file.language in code_langs: score += 15
    return max(score, 0)


def build_context(project: ProjectSource, analysis: StaticAnalysisResult) -> dict:
    for f in project.files:
        f.priority = _assign_priority(f, analysis)
    sorted_files = sorted(project.files, key=lambda f: f.priority, reverse=True)

    overview = "\n".join([
        f"Project: {project.root_path.split('/')[-1]}",
        f"Total files: {project.total_files}",
        f"Languages: {', '.join(f'{lang} ({count})' for lang, count in sorted(project.languages.items(), key=lambda x: -x[1])[:10])}",
        f"Architecture: {analysis.architecture_pattern or 'Unknown'}",
        f"Primary language: {analysis.primary_language or 'Unknown'}",
        f"Frameworks: {', '.join(fw.name for fw in analysis.frameworks) or 'None detected'}",
        f"Entry points: {', '.join(analysis.entry_points[:5]) or 'None detected'}",
        f"Has tests: {analysis.has_tests} ({len(analysis.test_files)} test files)",
        f"Has CI: {analysis.has_ci} ({analysis.ci_tool or 'N/A'})",
        f"Has Docker: {analysis.has_docker}",
        f"API routes found: {len(analysis.api_routes)}",
    ])

    dep_summary = "Dependencies:\n" + "".join(
        f"  - {dep.name} {dep.version or ''} {'(dev)' if dep.dev_only else ''}\n"
        for dep in analysis.dependencies[:50]
    )
    tree_section = f"\nFile Tree:\n{project.file_tree}\n"

    base_tokens = estimate_tokens(overview + dep_summary + tree_section)
    remaining_budget = MAX_CONTEXT_TOKENS - base_tokens

    file_contents, file_summaries = [], []
    used_tokens, files_included = 0, 0

    for f in sorted_files:
        if files_included >= MAX_FILES_FULL_CONTENT:
            break
        if f.content and f.priority > 0:
            ct = estimate_tokens(f.content)
            if used_tokens + ct <= remaining_budget:
                file_contents.append({"path": f.relative_path, "language": f.language or "unknown", "content": f.content})
                used_tokens += ct
                files_included += 1
            else:
                file_summaries.append({"path": f.relative_path, "language": f.language or "unknown", "size": f.size_bytes})
        else:
            file_summaries.append({"path": f.relative_path, "language": f.language or "unknown", "size": f.size_bytes})

    return {
        "project_overview": overview,
        "dependency_summary": dep_summary,
        "file_tree": tree_section,
        "file_contents": file_contents,
        "file_summaries": file_summaries[:100],
        "total_tokens": base_tokens + used_tokens,
        "files_with_content": len(file_contents),
        "files_summarized": len(file_summaries),
    }


def format_context_for_prompt(context: dict) -> str:
    parts = [
        "=== PROJECT OVERVIEW ===", context["project_overview"], "",
        "=== DEPENDENCIES ===", context["dependency_summary"], "",
        "=== FILE TREE ===", context["file_tree"], "",
    ]
    if context["file_contents"]:
        parts.append("=== FILE CONTENTS (Priority Files) ===")
        for fc in context["file_contents"]:
            parts.append(f"\n--- {fc['path']} ({fc['language']}) ---")
            parts.append(fc["content"])
    if context["file_summaries"]:
        parts.append("\n=== OTHER FILES ===")
        for fs in context["file_summaries"]:
            parts.append(f"  {fs['path']} ({fs['language']}, {fs['size']} bytes)")
    return "\n".join(parts)
