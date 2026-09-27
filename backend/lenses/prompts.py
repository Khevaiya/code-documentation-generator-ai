from core.models import LensType

LENS_SYSTEM_PROMPT = """You are an expert software architect and code analyst.
You analyze codebases thoroughly and provide structured, actionable insights.
Every claim should be traceable to specific files or code patterns you observed.
CRITICAL: Respond ONLY with valid JSON. No markdown, no explanation, no preamble."""

JSON_SCHEMA_INSTRUCTION = """
Return your analysis as a JSON object with this exact structure:
{
    "title": "string",
    "summary": "string - 2-3 paragraph summary",
    "findings": [
        {
            "title": "string",
            "description": "string",
            "severity": "critical|high|medium|low|info",
            "category": "string",
            "citations": [{"file_path": "string", "line_start": null, "line_end": null, "snippet": "string", "confidence": "inferred_from_code|stated_in_readme"}],
            "recommendation": "string"
        }
    ],
    "diagrams": [
        {
            "title": "string",
            "diagram_type": "architecture|sequence|er|flowchart|class",
            "mermaid_code": "string",
            "graph": {
                "nodes": [{"id": "string", "label": "string", "type": "service|database|queue|external|client|process"}],
                "edges": [{"from": "string", "to": "string", "label": "string"}]
            }
        }
    ],
    "gaps": [
        {"area": "string", "description": "string", "severity": "critical|high|medium|low", "recommendation": "string"}
    ],
    "sections": {"key": "value"}
}

MERMAID DIAGRAM RULES (strictly follow to avoid syntax errors):
- flowchart: use `graph TD` not `flowchart TD`
- Node IDs must be plain alphanumeric with no spaces: A, B, node1, etc.
- Node labels with spaces or special chars MUST use quotes: A["My Label"]
- Never use parentheses () inside node labels or edge labels
- Sequence diagrams: participant names must be single words or quoted
- ER diagrams: attribute names must be single words, no spaces
- Never use colons : inside unquoted labels or inside edge labels |label|
- Keep diagrams simple — max 20 nodes
- mermaid_code must be a single-line string with \\n for newlines (valid JSON string)

GRAPH RULES (nodes+edges JSON — always required alongside mermaid_code):
- id: short alphanumeric, no spaces
- label: human readable, any text allowed
- type: one of service|database|queue|external|client|process
- edge label: short description of the relationship, no special chars
- max 20 nodes
"""

def _architecture_prompt(context):
    return f"""Analyze this codebase from an ARCHITECTURE perspective.
Focus on: overall pattern, module structure, data flow, design patterns, DB architecture, external integrations, error handling, configuration management.
Generate diagrams: high-level architecture, data flow, ER diagram if DB models exist.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _security_prompt(context):
    return f"""Analyze this codebase from a SECURITY perspective.
Focus on: auth/authorization, input validation, secrets management, CORS, rate limiting, dependency CVEs, file upload security, error handling leaks, HTTPS/TLS, encryption.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _onboarding_prompt(context):
    return f"""Analyze this codebase to create a comprehensive DEVELOPER ONBOARDING guide.
Focus on: project overview, prerequisites, setup instructions, project structure explanation, key concepts, dev workflow, common tasks, debugging tips.
Make it specific to THIS codebase with actual file paths and commands.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _compliance_prompt(context):
    return f"""Analyze this codebase from a COMPLIANCE & REGULATORY perspective.
Map findings against: SOC 2, GDPR, HIPAA (if healthcare), OWASP Top 10.
For each area: current state, evidence, gaps, remediation priority.
Include a compliance matrix in sections.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _cost_optimization_prompt(context):
    return f"""Analyze this codebase from a COST OPTIMIZATION perspective.
Focus on: infrastructure implications, N+1 queries, caching opportunities, DB optimization, asset optimization, API call efficiency, scaling bottlenecks, third-party costs.
For each finding: cost impact (high/medium/low), fix effort, potential savings.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _technical_debt_prompt(context):
    return f"""Analyze this codebase for TECHNICAL DEBT.
Focus on: duplicated code, complex functions, outdated dependencies, missing tests, inconsistent patterns, TODO/FIXME comments, dead code, documentation gaps, migration debt.
For each item: severity, fix effort, risk of leaving, suggested priority.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _api_consumer_prompt(context):
    return f"""Analyze this codebase to generate API CONSUMER documentation.
Focus on: all endpoints (method, path, description), request/response schemas with examples, auth requirements, error formats, rate limiting, pagination, filtering, webhooks, WebSocket endpoints.
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

def _executive_summary_prompt(context):
    return f"""Create an EXECUTIVE SUMMARY of this codebase for non-technical leadership.
Focus on: what it does (plain language), tech stack summary, health score (1-10), key risks (business impact), team/resource implications, scalability, technical debt in business terms, competitive positioning, recommended actions (top 3-5 with effort/impact).
{JSON_SCHEMA_INSTRUCTION}
=== CODEBASE CONTEXT ===\n{context}"""

LENS_PROMPT_MAP = {
    LensType.ARCHITECTURE: _architecture_prompt,
    LensType.SECURITY: _security_prompt,
    LensType.ONBOARDING: _onboarding_prompt,
    LensType.COMPLIANCE: _compliance_prompt,
    LensType.COST_OPTIMIZATION: _cost_optimization_prompt,
    LensType.TECHNICAL_DEBT: _technical_debt_prompt,
    LensType.API_CONSUMER: _api_consumer_prompt,
    LensType.EXECUTIVE_SUMMARY: _executive_summary_prompt,
}

def get_lens_prompt(lens_type: LensType, context: str) -> str:
    prompt_fn = LENS_PROMPT_MAP.get(lens_type)
    if not prompt_fn:
        raise ValueError(f"Unknown lens type: {lens_type}")
    return prompt_fn(context)
