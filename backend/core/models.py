from pydantic import BaseModel, Field
from enum import Enum
from typing import Any, Optional
from datetime import datetime


class InputType(str, Enum):
    ZIP_UPLOAD = "zip_upload"
    GITHUB_URL = "github_url"


class LensType(str, Enum):
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    ONBOARDING = "onboarding"
    COMPLIANCE = "compliance"
    COST_OPTIMIZATION = "cost_optimization"
    TECHNICAL_DEBT = "technical_debt"
    API_CONSUMER = "api_consumer"
    EXECUTIVE_SUMMARY = "executive_summary"


class OutputFormat(str, Enum):
    MARKDOWN = "markdown"
    DOCX = "docx"
    PDF = "pdf"
    HTML = "html"
    PPTX = "pptx"


class AudienceRole(str, Enum):
    CTO = "cto"
    ENGINEER = "engineer"
    AUDITOR = "auditor"
    PRODUCT_MANAGER = "product_manager"


class JobStatus(str, Enum):
    PENDING = "pending"
    INGESTING = "ingesting"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class FileInfo(BaseModel):
    path: str
    relative_path: str
    language: Optional[str] = None
    size_bytes: int = 0
    is_entry_point: bool = False
    is_config: bool = False
    is_test: bool = False
    content: Optional[str] = None
    priority: int = 0


class ProjectSource(BaseModel):
    root_path: str
    files: list[FileInfo] = []
    total_files: int = 0
    total_size_bytes: int = 0
    languages: dict[str, int] = {}
    file_tree: str = ""


class DependencyInfo(BaseModel):
    name: str
    version: Optional[str] = None
    dev_only: bool = False
    has_known_cve: bool = False
    cve_details: Optional[str] = None


class FrameworkInfo(BaseModel):
    name: str
    version: Optional[str] = None
    category: str = ""


class StaticAnalysisResult(BaseModel):
    frameworks: list[FrameworkInfo] = []
    dependencies: list[DependencyInfo] = []
    entry_points: list[str] = []
    architecture_pattern: Optional[str] = None
    has_tests: bool = False
    test_files: list[str] = []
    has_ci: bool = False
    ci_tool: Optional[str] = None
    has_docker: bool = False
    has_env_file: bool = False
    readme_exists: bool = False
    readme_content: Optional[str] = None
    license_type: Optional[str] = None
    primary_language: Optional[str] = None
    api_routes: list[str] = []
    db_schemas: list[str] = []


class Citation(BaseModel):
    file_path: str
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    snippet: Optional[str] = None
    confidence: Optional[str] = "inferred_from_code"


class Finding(BaseModel):
    title: str
    description: str
    severity: Optional[str] = None
    category: str = ""
    citations: list[Citation] = []
    recommendation: Optional[str] = None


class DiagramSpec(BaseModel):
    title: str
    diagram_type: str
    mermaid_code: str
    graph: Optional[dict] = None        # nodes+edges from LLM
    svg: Optional[str] = None           # rendered SVG (set at runtime)
    use_svg: bool = False               # True when mermaid failed, SVG is fallback


class GapItem(BaseModel):
    area: str
    description: str
    severity: str = "medium"
    recommendation: str = ""


class LensResult(BaseModel):
    lens_type: LensType
    title: str
    summary: str
    findings: list[Finding] = []
    diagrams: list[DiagramSpec] = []
    gaps: list[GapItem] = []
    raw_sections: dict[str, Any] = {}
    metadata: dict = {}


class DocumentModel(BaseModel):
    project_name: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    input_type: InputType
    source_url: Optional[str] = None
    static_analysis: StaticAnalysisResult
    lens_results: list[LensResult] = []
    audience_role: Optional[AudienceRole] = None
    executive_summary: Optional[str] = None


# ── Knowledge Graph Models ───────────────────────────────────────────────────

class GraphNode(BaseModel):
    id: str
    label: str
    type: str                         # file, class, function, route, model, library, risk
    layer: str                        # api, logic, data, library, security
    path: Optional[str] = None
    complexity: int = 1
    degree: int = 0
    in_degree: int = 0
    out_degree: int = 0
    centrality: float = 0.0
    is_hub: bool = False
    details: Optional[dict] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str                         # imports, calls, inherits, handles_route, references, contains
    label: Optional[str] = None


class KnowledgeGraph(BaseModel):
    nodes: list[GraphNode] = []
    edges: list[GraphEdge] = []
    metrics: dict[str, Any] = {}
    layers: list[str] = []


# ── Health Score Models ──────────────────────────────────────────────────────

class RemediationItem(BaseModel):
    id: str
    title: str
    description: str
    severity: str                     # CRITICAL, HIGH, MEDIUM, LOW
    category: str                     # Security, Architecture, Performance, TechDebt, Testing
    file_path: Optional[str] = None
    suggested_fix: Optional[str] = None


class HealthScore(BaseModel):
    overall_score: int
    grade: str                        # A+, A, B, C, D
    security_score: int
    architecture_score: int
    performance_score: int
    maintainability_score: int
    reliability_score: int
    radar_data: list[dict[str, Any]] = []
    remediations: list[RemediationItem] = []
    summary_text: str = ""


# ── Terminal Log Model ───────────────────────────────────────────────────────

class TerminalLog(BaseModel):
    timestamp: str
    level: str                        # INFO, SUCCESS, WARN, AST, GRAPH, LLM
    message: str
    phase: str


# ── Job & Analysis Models ───────────────────────────────────────────────────

class AnalysisRequest(BaseModel):
    input_type: InputType
    github_url: Optional[str] = None
    lenses: list[LensType]
    output_formats: list[OutputFormat]
    audience_role: Optional[AudienceRole] = None
    project_name: Optional[str] = None


class JobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str = ""
    progress: int = 0
    output_files: dict[str, str] = {}
    error: Optional[str] = None
    # Rich payloads for the Interactive Studio:
    doc_model: Optional[dict] = None
    knowledge_graph: Optional[dict] = None
    health_score: Optional[dict] = None
    terminal_logs: list[TerminalLog] = []


class ChatMessage(BaseModel):
    role: str                         # user, assistant
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    response: str
    diagrams: list[str] = []
    citations: list[dict[str, Any]] = []
    suggested_followups: list[str] = []