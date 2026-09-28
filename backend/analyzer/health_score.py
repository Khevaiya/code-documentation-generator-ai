import re
from typing import Any
from core.models import ProjectSource, StaticAnalysisResult, KnowledgeGraph, HealthScore, RemediationItem


def compute_health_score(
    project: ProjectSource,
    static: StaticAnalysisResult,
    kg: KnowledgeGraph
) -> HealthScore:
    """Calculates weighted 0-100 scores across 5 pillars, a letter grade, and actionable remediations."""
    remediations: list[RemediationItem] = []
    
    # ── 1. Security Posture Score (0-100) ────────────────────────────────────
    sec_deductions = 0
    
    # Check for hardcoded secrets
    secret_patterns = [
        (r'''(?i)(?:api_key|secret|password|auth_token)\s*=\s*['"][a-zA-Z0-9_\-]{16,}['"]''', "Hardcoded secret or API token detected in source code", "CRITICAL"),
        (r'''(?i)eval\s*\(|exec\s*\(|shell\s*=\s*True''', "Dangerous code execution primitive (`eval`/`exec`/`shell=True`) found", "HIGH"),
        (r'''allow_origins\s*=\s*\[\s*["']\*["']\s*\]''', "Wildcard CORS origin enabled (`allow_origins=['*']`)", "MEDIUM"),
        (r'''(?i)cursor\.execute\s*\(\s*f['"]|query\s*\+\s*['"]''', "Potential SQL injection vulnerability via string interpolation", "HIGH"),
    ]

    for f in project.files:
        if not f.content or f.is_test:
            continue
        for pattern, desc, sev in secret_patterns:
            match = re.search(pattern, f.content)
            if match:
                deduct = 20 if sev == "CRITICAL" else (12 if sev == "HIGH" else 6)
                sec_deductions += deduct
                remediations.append(RemediationItem(
                    id=f"sec-{len(remediations)+1}",
                    title=desc,
                    description=f"Found pattern in `{f.relative_path}` around: `{match.group(0)[:60]}...`",
                    severity=sev,
                    category="Security",
                    file_path=f.relative_path,
                    suggested_fix="Move sensitive values to environment variables (.env) or use parameterized queries."
                ))

    # Check env template
    if not static.has_env_file:
        sec_deductions += 10
        remediations.append(RemediationItem(
            id=f"sec-env",
            title="Missing `.env.example` template",
            description="No environment variable configuration template found in the root or backend directories.",
            severity="MEDIUM",
            category="Security",
            suggested_fix="Create a `.env.example` detailing all required configuration variables."
        ))

    security_score = max(20, min(100, 100 - sec_deductions))

    # ── 2. Architectural Modularity Score (0-100) ───────────────────────────
    arch_score = 90
    if kg.metrics.get("has_cycles", False):
        arch_score -= 25
        cycles = kg.metrics.get("circular_dependencies", [])
        remediations.append(RemediationItem(
            id="arch-cycle",
            title="Circular Dependency Detected",
            description=f"Found circular dependency loop: {cycles[0] if cycles else 'Inter-module circular references'}",
            severity="HIGH",
            category="Architecture",
            suggested_fix="Refactor shared types or helper functions into a separate `core` or `common` module to break the import cycle."
        ))

    if len(kg.metrics.get("hub_nodes", [])) > 5:
        arch_score -= 10
        remediations.append(RemediationItem(
            id="arch-god-object",
            title="High Coupling / God Object Warning",
            description=f"High centrality hub files detected: {', '.join(kg.metrics.get('hub_nodes', [])[:3])}",
            severity="MEDIUM",
            category="Architecture",
            suggested_fix="Split monolithic files into specialized domain modules to decrease coupling."
        ))

    architecture_score = max(30, min(100, arch_score))

    # ── 3. Performance & Scalability (0-100) ─────────────────────────────────
    perf_score = 85
    # Check async route adoption in Python/JS
    async_funcs = len([n for n in kg.nodes if n.type == "function" and n.details and n.details.get("is_async")])
    total_funcs = len([n for n in kg.nodes if n.type == "function"])
    
    if total_funcs > 0 and (async_funcs / total_funcs) > 0.5:
        perf_score += 10
    
    large_files = [f for f in project.files if f.size_bytes > 80_000]
    if len(large_files) > 3:
        perf_score -= 15
        remediations.append(RemediationItem(
            id="perf-large-file",
            title="Excessive Single-File Size",
            description=f"Found {len(large_files)} files exceeding 80KB. May impact bundle size and memory allocation.",
            severity="LOW",
            category="Performance",
            file_path=large_files[0].relative_path,
            suggested_fix="Break down oversized components or modules with code splitting and lazy loading."
        ))

    performance_score = max(30, min(100, perf_score))

    # ── 4. Maintainability & Tech Debt (0-100) ───────────────────────────────
    maint_score = 88
    if not static.readme_exists:
        maint_score -= 20
        remediations.append(RemediationItem(
            id="maint-no-readme",
            title="Missing README documentation",
            description="No README.md found in the root directory to guide new developers.",
            severity="MEDIUM",
            category="TechDebt",
            suggested_fix="Generate comprehensive project documentation using CodeLens AI."
        ))

    maintainability_score = max(25, min(100, maint_score))

    # ── 5. Reliability & Testing Coverage (0-100) ────────────────────────────
    rel_score = 40
    if static.has_tests:
        rel_score += 35
    else:
        remediations.append(RemediationItem(
            id="rel-no-tests",
            title="Missing Automated Unit / Integration Tests",
            description="No test directory or test files (`test_*.py`, `*.spec.js`, `*.test.ts`) detected.",
            severity="HIGH",
            category="Testing",
            suggested_fix="Add automated tests using Pytest, Jest, or Vitest to safeguard business logic."
        ))

    if static.has_ci:
        rel_score += 15
    else:
        remediations.append(RemediationItem(
            id="rel-no-ci",
            title="Missing CI/CD Workflow",
            description="No GitHub Actions, GitLab CI, or Jenkins pipelines detected.",
            severity="MEDIUM",
            category="Testing",
            suggested_fix="Configure a GitHub Actions workflow (`.github/workflows/ci.yml`) for automated linting and testing."
        ))

    if static.has_docker:
        rel_score += 10

    reliability_score = max(20, min(100, rel_score))

    # ── Overall Weighted Score & Grade ───────────────────────────────────────
    overall_score = round(
        (security_score * 0.25) +
        (architecture_score * 0.25) +
        (performance_score * 0.15) +
        (maintainability_score * 0.15) +
        (reliability_score * 0.20)
    )

    if overall_score >= 90:
        grade = "A+"
    elif overall_score >= 80:
        grade = "A"
    elif overall_score >= 70:
        grade = "B"
    elif overall_score >= 60:
        grade = "C"
    else:
        grade = "D"

    radar_data = [
        {"subject": "Security", "score": security_score, "fullMark": 100},
        {"subject": "Architecture", "score": architecture_score, "fullMark": 100},
        {"subject": "Performance", "score": performance_score, "fullMark": 100},
        {"subject": "Maintainability", "score": maintainability_score, "fullMark": 100},
        {"subject": "Reliability", "score": reliability_score, "fullMark": 100},
    ]

    summary_text = (
        f"Overall Health Grade: {grade} ({overall_score}/100). "
        f"Security Posture: {security_score}%, Architecture: {architecture_score}%, "
        f"Performance: {performance_score}%, Maintainability: {maintainability_score}%, "
        f"Reliability: {reliability_score}%. {len(remediations)} action items identified."
    )

    return HealthScore(
        overall_score=overall_score,
        grade=grade,
        security_score=security_score,
        architecture_score=architecture_score,
        performance_score=performance_score,
        maintainability_score=maintainability_score,
        reliability_score=reliability_score,
        radar_data=radar_data,
        remediations=remediations,
        summary_text=summary_text,
    )
