import os
import sys
import uuid
import shutil
import asyncio
import traceback
from pathlib import Path
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, 'reconfigure'):
    try: sys.stdout.reconfigure(encoding='utf-8')
    except Exception: pass
if hasattr(sys.stderr, 'reconfigure'):
    try: sys.stderr.reconfigure(encoding='utf-8')
    except Exception: pass

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.models import (
    InputType, LensType, OutputFormat, AudienceRole, JobStatus, JobResponse,
    TerminalLog, ChatRequest, ChatResponse
)
from core.config import UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR
from ingestion.zip_handler import ingest_zip
from ingestion.github_handler import ingest_github
from analyzer.static_analyzer import run_static_analysis
from analyzer.graph_engine import build_knowledge_graph, calculate_blast_radius
from analyzer.health_score import compute_health_score
from core.context_builder import build_context
from core.orchestrator import run_analysis
from core.copilot import ask_copilot
from renderers.markdown_renderer import render_markdown
from renderers.docx_renderer import render_docx
from renderers.pdf_renderer import render_pdf
from renderers.html_renderer import render_html
from renderers.pptx_renderer import render_pptx
from renderers.export_bundler import (
    create_docusaurus_bundle, create_github_wiki_bundle, generate_pr_review_markdown
)


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="CodeLens AI — Codebase Analysis & Intelligence Agent", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR.mkdir(exist_ok=True)
app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

jobs: dict[str, JobResponse] = {}

RENDERER_MAP = {
    OutputFormat.MARKDOWN: ("md", render_markdown),
    OutputFormat.DOCX: ("docx", render_docx),
    OutputFormat.PDF: ("pdf", render_pdf),
    OutputFormat.HTML: ("html", render_html),
    OutputFormat.PPTX: ("pptx", render_pptx),
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def add_log(job_id: str, level: str, message: str, phase: str):
    if job_id in jobs:
        timestamp = datetime.utcnow().strftime("%H:%M:%S")
        log_entry = TerminalLog(timestamp=timestamp, level=level, message=message, phase=phase)
        jobs[job_id].terminal_logs.append(log_entry)


def update_job(job_id, status, progress=0, message="", output_files=None, error=None, doc_model=None, kg=None, health=None):
    if job_id in jobs:
        jobs[job_id].status = status
        jobs[job_id].progress = progress
        jobs[job_id].message = message
        if output_files:
            jobs[job_id].output_files.update(output_files)
        if error:
            jobs[job_id].error = error
        if doc_model:
            jobs[job_id].doc_model = doc_model
        if kg:
            jobs[job_id].knowledge_graph = kg
        if health:
            jobs[job_id].health_score = health


async def run_pipeline(job_id, input_type, source_path, github_url, lenses, output_formats, audience_role, project_name):
    try:
        update_job(job_id, JobStatus.INGESTING, 10, "Ingesting source code...")
        add_log(job_id, "INFO", f"Ingesting codebase from {github_url or source_path}...", "Ingestion")

        project = await (ingest_zip(source_path) if input_type == InputType.ZIP_UPLOAD else ingest_github(github_url))
        if not project_name:
            project_name = Path(project.root_path).name

        add_log(job_id, "SUCCESS", f"Ingested {project.total_files} source files ({project.total_size_bytes // 1024} KB)", "Ingestion")

        # Step 2: Static Analysis
        update_job(job_id, JobStatus.ANALYZING, 20, "Running static code analysis...")
        add_log(job_id, "AST", "Running AST & dependency heuristic analysis...", "Analysis")
        static_result = run_static_analysis(project)
        add_log(job_id, "SUCCESS", f"Identified {len(static_result.frameworks)} frameworks & {len(static_result.api_routes)} API routes", "Analysis")

        # Step 3: Build Code Knowledge Graph
        update_job(job_id, JobStatus.ANALYZING, 30, "Constructing Code Knowledge Graph (CodeKG)...")
        add_log(job_id, "GRAPH", "Constructing in-memory Code Knowledge Graph (AST symbols, call hierarchy, imports)...", "KnowledgeGraph")
        kg = build_knowledge_graph(project, static_result)
        add_log(job_id, "SUCCESS", f"Knowledge Graph built: {kg.metrics['total_nodes']} nodes, {kg.metrics['total_edges']} relationships", "KnowledgeGraph")

        # Step 4: Compute Executive Health Scorecard
        update_job(job_id, JobStatus.ANALYZING, 40, "Calculating Executive Health Scorecard...")
        add_log(job_id, "INFO", "Evaluating Security Posture, Modularity, Performance, and Reliability...", "HealthScore")
        health = compute_health_score(project, static_result, kg)
        add_log(job_id, "SUCCESS", f"Executive Health Grade: {health.grade} ({health.overall_score}/100) — {len(health.remediations)} action items", "HealthScore")

        # Step 5: Build Token-Budgeted Context
        update_job(job_id, JobStatus.ANALYZING, 45, "Building token-budgeted prompt context...")
        context = build_context(project, static_result)
        add_log(job_id, "INFO", f"Prioritized {context['files_with_content']} core architectural files (~{context['total_tokens']:,} tokens)", "Context")

        # Step 6: Multi-Lens LLM Synthesis
        update_job(job_id, JobStatus.GENERATING, 50, f"Synthesizing {len(lenses)} analysis lenses with Gemini...")
        add_log(job_id, "LLM", f"Dispatching Gemini AI reasoning for {len(lenses)} lenses...", "Synthesis")

        def on_lens_progress(lens_type, status):
            jobs[job_id].progress = min(jobs[job_id].progress + 6, 85)
            jobs[job_id].message = f"Completed {lens_type.value} lens analysis"
            add_log(job_id, "SUCCESS", f"Generated {lens_type.value} analysis lens with verified Mermaid diagrams", "Synthesis")

        doc_model = await run_analysis(
            lenses=lenses, context=context, static_analysis=static_result,
            input_type=input_type, source_url=github_url, project_name=project_name,
            audience_role=audience_role, on_progress=on_lens_progress,
        )

        # Step 7: Render Output Documents
        update_job(job_id, JobStatus.RENDERING, 85, "Generating output documents & bundles...")
        job_output_dir = OUTPUT_DIR / job_id
        job_output_dir.mkdir(exist_ok=True)
        output_files = {}

        for fmt in output_formats:
            if fmt in RENDERER_MAP:
                ext, renderer = RENDERER_MAP[fmt]
                filename = f"{project_name.replace(' ', '_')}_report.{ext}"
                out_path = str(job_output_dir / filename)
                try:
                    add_log(job_id, "INFO", f"Rendering {fmt.value.upper()} report...", "Rendering")
                    renderer(doc_model, out_path)
                    output_files[fmt.value] = f"/download/{job_id}/{filename}"
                    add_log(job_id, "SUCCESS", f"Generated {filename}", "Rendering")
                except Exception as e:
                    add_log(job_id, "WARN", f"Renderer {fmt.value} skipped: {str(e)[:100]}", "Rendering")
                    traceback.print_exc()

        # Step 8: Complete Job
        update_job(
            job_id, JobStatus.COMPLETED, 100, "Analysis complete!",
            output_files=output_files,
            doc_model=doc_model.dict(),
            kg=kg.dict(),
            health=health.dict()
        )
        add_log(job_id, "SUCCESS", "All documentation lenses, Knowledge Graph, and Health Scorecards ready!", "Complete")

    except Exception as e:
        traceback.print_exc()
        add_log(job_id, "ERROR", f"Pipeline failed: {str(e)}", "Error")
        update_job(job_id, JobStatus.FAILED, 0, error=str(e))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"name": "CodeLens AI", "version": "2.0.0", "status": "active"}


@app.post("/analyze/upload", response_model=JobResponse)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    lenses: str = Form(...),
    output_formats: str = Form(...),
    audience_role: Optional[str] = Form(None),
    project_name: Optional[str] = Form(None),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(400, "Only .zip files accepted")
    job_id = uuid.uuid4().hex[:12]
    zip_path = UPLOAD_DIR / f"{job_id}.zip"
    with open(zip_path, "wb") as f:
        f.write(await file.read())
    lens_list = [LensType(l.strip()) for l in lenses.split(",") if l.strip()]
    format_list = [OutputFormat(f.strip()) for f in output_formats.split(",") if f.strip()]
    role = AudienceRole(audience_role) if audience_role else None
    job = JobResponse(job_id=job_id, status=JobStatus.PENDING, message="Job created", terminal_logs=[])
    jobs[job_id] = job
    background_tasks.add_task(run_pipeline, job_id, InputType.ZIP_UPLOAD, str(zip_path), None, lens_list, format_list, role, project_name)
    return job


@app.post("/analyze/github", response_model=JobResponse)
async def analyze_github(
    background_tasks: BackgroundTasks,
    github_url: str = Form(...),
    lenses: str = Form(...),
    output_formats: str = Form(...),
    audience_role: Optional[str] = Form(None),
    project_name: Optional[str] = Form(None),
):
    if "github.com" not in github_url:
        raise HTTPException(400, "Please provide a valid GitHub URL")
    job_id = uuid.uuid4().hex[:12]
    lens_list = [LensType(l.strip()) for l in lenses.split(",") if l.strip()]
    format_list = [OutputFormat(f.strip()) for f in output_formats.split(",") if f.strip()]
    role = AudienceRole(audience_role) if audience_role else None
    job = JobResponse(job_id=job_id, status=JobStatus.PENDING, message="Job created", terminal_logs=[])
    jobs[job_id] = job
    background_tasks.add_task(run_pipeline, job_id, InputType.GITHUB_URL, "", github_url, lens_list, format_list, role, project_name)
    return job


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]


@app.get("/jobs/{job_id}/graph")
async def get_job_graph(job_id: str):
    if job_id not in jobs or not jobs[job_id].knowledge_graph:
        raise HTTPException(404, "Knowledge Graph not found for this job")
    return jobs[job_id].knowledge_graph


@app.get("/jobs/{job_id}/blast-radius/{node_id:path}")
async def get_blast_radius(job_id: str, node_id: str):
    if job_id not in jobs or not jobs[job_id].knowledge_graph:
        raise HTTPException(404, "Knowledge Graph not found")
    kg_obj = build_knowledge_graph.__annotations__
    from core.models import KnowledgeGraph
    kg_instance = KnowledgeGraph(**jobs[job_id].knowledge_graph)
    return calculate_blast_radius(kg_instance, node_id)


@app.post("/jobs/{job_id}/chat", response_model=ChatResponse)
async def chat_with_codebase(job_id: str, req: ChatRequest):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    job = jobs[job_id]
    return await ask_copilot(
        job_id=job_id,
        user_message=req.message,
        doc_model=job.doc_model,
        kg_data=job.knowledge_graph,
        health_data=job.health_score,
        history=req.history
    )


@app.get("/download/{job_id}/export/{export_type}")
async def export_ecosystem(job_id: str, export_type: str):
    if job_id not in jobs or not jobs[job_id].doc_model:
        raise HTTPException(404, "Analysis not found")
    from core.models import DocumentModel
    doc = DocumentModel(**jobs[job_id].doc_model)
    out_dir = OUTPUT_DIR / job_id

    if export_type == "docusaurus":
        zip_path = out_dir / f"{doc.project_name}_docusaurus_site.zip"
        create_docusaurus_bundle(doc, str(zip_path))
        return FileResponse(str(zip_path), filename=f"{doc.project_name}_docusaurus_site.zip")
    elif export_type == "github_wiki":
        zip_path = out_dir / f"{doc.project_name}_github_wiki.zip"
        create_github_wiki_bundle(doc, str(zip_path))
        return FileResponse(str(zip_path), filename=f"{doc.project_name}_github_wiki.zip")
    elif export_type == "pr_review":
        pr_md = generate_pr_review_markdown(doc)
        return PlainTextResponse(pr_md)
    else:
        raise HTTPException(400, "Unsupported export type")


@app.get("/download/{job_id}/{filename}")
async def download_file(job_id: str, filename: str):
    file_path = OUTPUT_DIR / job_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    if job_id in jobs:
        del jobs[job_id]
    shutil.rmtree(OUTPUT_DIR / job_id, ignore_errors=True)
    (UPLOAD_DIR / f"{job_id}.zip").unlink(missing_ok=True)
    return {"message": "Cleaned up"}


@app.get("/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat(), "version": "2.0.0"}
