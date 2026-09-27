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
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core.models import InputType, LensType, OutputFormat, AudienceRole, JobStatus, JobResponse
from core.config import UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR
from ingestion.zip_handler import ingest_zip
from ingestion.github_handler import ingest_github
from analyzer.static_analyzer import run_static_analysis
from core.context_builder import build_context
from core.orchestrator import run_analysis
from renderers.markdown_renderer import render_markdown
from renderers.docx_renderer import render_docx
from renderers.pdf_renderer import render_pdf
from renderers.html_renderer import render_html
from renderers.pptx_renderer import render_pptx


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="CodeLens AI — Codebase Analysis Agent", version="1.0.0")

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
def update_job(job_id, status, progress=0, message="", output_files=None, error=None):
    if job_id in jobs:
        jobs[job_id].status = status
        jobs[job_id].progress = progress
        jobs[job_id].message = message
        if output_files:
            jobs[job_id].output_files.update(output_files)
        if error:
            jobs[job_id].error = error


async def run_pipeline(job_id, input_type, source_path, github_url, lenses, output_formats, audience_role, project_name):
    try:
        update_job(job_id, JobStatus.INGESTING, 10, "Ingesting source code...")
        project = await (ingest_zip(source_path) if input_type == InputType.ZIP_UPLOAD else ingest_github(github_url))
        if not project_name:
            project_name = Path(project.root_path).name

        update_job(job_id, JobStatus.ANALYZING, 25, "Running static analysis...")
        static_result = run_static_analysis(project)

        update_job(job_id, JobStatus.ANALYZING, 35, "Building context...")
        context = build_context(project, static_result)

        update_job(job_id, JobStatus.GENERATING, 45, f"Analyzing with {len(lenses)} lenses...")

        def on_lens_progress(lens_type, status):
            jobs[job_id].progress = min(jobs[job_id].progress + 8, 85)
            jobs[job_id].message = f"Completed {lens_type.value} analysis"

        doc_model = await run_analysis(
            lenses=lenses, context=context, static_analysis=static_result,
            input_type=input_type, source_url=github_url, project_name=project_name,
            audience_role=audience_role, on_progress=on_lens_progress,
        )

        update_job(job_id, JobStatus.RENDERING, 85, "Generating output files...")
        job_output_dir = OUTPUT_DIR / job_id
        job_output_dir.mkdir(exist_ok=True)
        output_files = {}

        for fmt in output_formats:
            if fmt in RENDERER_MAP:
                ext, renderer = RENDERER_MAP[fmt]
                filename = f"{project_name.replace(' ', '_')}_report.{ext}"
                out_path = str(job_output_dir / filename)
                try:
                    print(f"[render] Starting {fmt.value} generation: {out_path}")
                    renderer(doc_model, out_path)
                    print(f"[render] Successfully generated {fmt.value}: {out_path}")
                    output_files[fmt.value] = f"/download/{job_id}/{filename}"
                except Exception as e:
                    error_msg = f"Renderer {fmt.value} failed: {e}"
                    print(error_msg)
                    traceback.print_exc()
                    # Continue with other formats instead of failing the entire job
                    pass

        update_job(job_id, JobStatus.COMPLETED, 100, "Analysis complete!", output_files=output_files)

    except Exception as e:
        traceback.print_exc()
        update_job(job_id, JobStatus.FAILED, 0, error=str(e))


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"name": "CodeLens AI", "version": "1.0.0"}


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
    job = JobResponse(job_id=job_id, status=JobStatus.PENDING, message="Job created")
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
    job = JobResponse(job_id=job_id, status=JobStatus.PENDING, message="Job created")
    jobs[job_id] = job
    background_tasks.add_task(run_pipeline, job_id, InputType.GITHUB_URL, "", github_url, lens_list, format_list, role, project_name)
    return job


@app.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    return jobs[job_id]


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
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
