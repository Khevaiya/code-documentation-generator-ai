import asyncio
import traceback
from datetime import datetime
from typing import Callable

from core.models import (
    LensType, LensResult, Finding, Citation, DiagramSpec, GapItem,
    DocumentModel, StaticAnalysisResult, InputType, AudienceRole,
)
from core.gemini_client import call_gemini
from lenses.prompts import get_lens_prompt, LENS_SYSTEM_PROMPT
from core.context_builder import format_context_for_prompt
from renderers.graph_svg_renderer import render_graph_svg
import html as _html_mod


def _unescape(s: str) -> str:
    return _html_mod.unescape(s) if s else s


def _flatten_sections(sections: dict) -> dict:
    """Pass sections through as-is; renderers handle formatting."""
    return dict(sections)


def _parse_lens_result(lens_type: LensType, raw: dict) -> LensResult:
    findings = [
        Finding(
            title=f.get("title", ""), description=f.get("description", ""),
            severity=f.get("severity", "info"), category=f.get("category", ""),
            citations=[Citation(
                file_path=c.get("file_path", ""),
                line_start=c.get("line_start"),
                line_end=c.get("line_end"),
                snippet=c.get("snippet"),
                confidence=c.get("confidence") or "inferred_from_code",
            ) for c in f.get("citations", [])],
            recommendation=f.get("recommendation"),
        ) for f in raw.get("findings", [])
    ]
    diagrams = []
    for d in raw.get("diagrams", []):
        graph = d.get("graph") if isinstance(d.get("graph"), dict) else None
        svg = render_graph_svg(graph, d.get("title", "")) if graph else None
        diagrams.append(DiagramSpec(
            title=d.get("title", ""),
            diagram_type=d.get("diagram_type", "architecture"),
            mermaid_code=_unescape(d.get("mermaid_code", "")),
            graph=graph,
            svg=svg,
        ))
    gaps = [GapItem(area=g.get("area",""), description=g.get("description",""), severity=g.get("severity","medium"), recommendation=g.get("recommendation","")) for g in raw.get("gaps", [])]
    return LensResult(
        lens_type=lens_type,
        title=raw.get("title", lens_type.value.replace("_"," ").title()),
        summary=raw.get("summary", ""),
        findings=findings, diagrams=diagrams, gaps=gaps,
        raw_sections=_flatten_sections(raw.get("sections", {})),
    )


async def _run_single_lens(lens_type: LensType, context: dict, on_progress: Callable | None = None) -> LensResult:
    formatted_context = format_context_for_prompt(context)
    prompt = get_lens_prompt(lens_type, formatted_context)
    try:
        raw_result = await call_gemini(system_prompt=LENS_SYSTEM_PROMPT, user_prompt=prompt, temperature=0.2)
        result = _parse_lens_result(lens_type, raw_result)
        if on_progress:
            on_progress(lens_type, "completed")
        return result
    except Exception as e:
        traceback.print_exc()
        return LensResult(
            lens_type=lens_type,
            title=lens_type.value.replace("_"," ").title(),
            summary=f"Analysis failed: {str(e)}",
        )


async def run_analysis(
    lenses: list[LensType], context: dict, static_analysis: StaticAnalysisResult,
    input_type: InputType, source_url: str | None = None, project_name: str | None = None,
    audience_role: AudienceRole | None = None, on_progress: Callable | None = None,
) -> DocumentModel:
    tasks = [_run_single_lens(lens, context, on_progress) for lens in lenses]
    lens_results = await asyncio.gather(*tasks)

    exec_summary = next((lr.summary for lr in lens_results if lr.lens_type == LensType.EXECUTIVE_SUMMARY), None)

    return DocumentModel(
        project_name=project_name or "Analyzed Project",
        generated_at=datetime.utcnow(),
        input_type=input_type,
        source_url=source_url,
        static_analysis=static_analysis,
        lens_results=list(lens_results),
        audience_role=audience_role,
        executive_summary=exec_summary,
    )