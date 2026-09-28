import re
import traceback
from typing import Any, Optional
import google.generativeai as genai

from core.config import GEMINI_API_KEY, GEMINI_MODEL
from core.models import ChatMessage, ChatResponse, DocumentModel, KnowledgeGraph, HealthScore
from analyzer.graph_engine import calculate_blast_radius


_sessions: dict[str, list[dict]] = {}


import os

def _get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")
    genai.configure(api_key=api_key)
    return genai


async def ask_copilot(
    job_id: str,
    user_message: str,
    doc_model: Optional[dict] = None,
    kg_data: Optional[dict] = None,
    health_data: Optional[dict] = None,
    history: Optional[list[ChatMessage]] = None
) -> ChatResponse:
    """Answers architectural and technical questions using multi-turn session memory and Knowledge Graph grounding."""
    try:
        genai_client = _get_gemini_client()
    except Exception as e:
        return ChatResponse(
            response=f"⚠️ Gemini API Key not configured: {str(e)}",
            diagrams=[],
            citations=[],
            suggested_followups=["Configure GEMINI_API_KEY in backend/.env"]
        )

    # Initialize or load session history
    session_history = _sessions.setdefault(job_id, [])
    if history:
        session_history = [{"role": m.role, "parts": [m.content]} for m in history]
        _sessions[job_id] = session_history

    # Check for blast radius request
    blast_radius_summary = ""
    if kg_data and ("blast radius" in user_message.lower() or "what breaks" in user_message.lower() or "impact of" in user_message.lower()):
        # Try to find a mentioned file or function
        for node in kg_data.get("nodes", []):
            if node.get("label", "").lower() in user_message.lower() or (node.get("path") and node["path"].lower() in user_message.lower()):
                # Compute blast radius for this node
                kg_obj = KnowledgeGraph(**kg_data)
                br = calculate_blast_radius(kg_obj, node["id"])
                blast_radius_summary = (
                    f"\n[GRAPH ANALYSIS: Blast Radius for '{node['label']}']:\n"
                    f"- Upstream affected callers ({br['upstream_affected_count']}): {', '.join(n['label'] for n in br['upstream_affected_nodes'][:8])}\n"
                    f"- Downstream dependencies ({br['downstream_dependency_count']}): {', '.join(n['label'] for n in br['downstream_dependency_nodes'][:8])}\n"
                )
                break

    # Build Grounding Context
    context_lines = [
        "You are CodeLens Copilot — an expert AI Software Architect and Staff Engineer.",
        "You have complete visibility into the analyzed codebase, its AST symbol table, and its Knowledge Graph.",
        "",
        "=== ARCHITECTURAL CONTEXT ===",
    ]

    if doc_model:
        context_lines.append(f"Project Name: {doc_model.get('project_name', 'Codebase')}")
        sa = doc_model.get("static_analysis", {})
        context_lines.append(f"Frameworks: {', '.join(f.get('name', '') for f in sa.get('frameworks', []))}")
        context_lines.append(f"Primary Language: {sa.get('primary_language', 'Unknown')}")
        context_lines.append(f"Entry Points: {', '.join(sa.get('entry_points', []))}")
        context_lines.append(f"API Routes: {', '.join(sa.get('api_routes', []))}")

        # Add Lens Summaries
        context_lines.append("\n=== GENERATED LENS FINDINGS ===")
        for lr in doc_model.get("lens_results", [])[:6]:
            context_lines.append(f"\n[Lens: {lr.get('title', lr.get('lens_type', ''))}]")
            context_lines.append(lr.get("summary", "")[:600])

    if kg_data:
        metrics = kg_data.get("metrics", {})
        context_lines.append("\n=== CODE KNOWLEDGE GRAPH TOPOLOGY ===")
        context_lines.append(f"Total Nodes: {metrics.get('total_nodes', 0)} | Total Edges: {metrics.get('total_edges', 0)}")
        context_lines.append(f"Central Hub Files: {', '.join(metrics.get('hub_nodes', []))}")
        if metrics.get("circular_dependencies"):
            context_lines.append(f"Circular Dependencies: {', '.join(metrics.get('circular_dependencies', []))}")

    if health_data:
        context_lines.append("\n=== HEALTH SCORE & REMEDIATIONS ===")
        context_lines.append(f"Health Grade: {health_data.get('grade')} ({health_data.get('overall_score')}/100)")
        for rem in health_data.get("remediations", [])[:4]:
            context_lines.append(f"- [{rem.get('severity')}] {rem.get('title')}: {rem.get('description')}")

    if blast_radius_summary:
        context_lines.append(blast_radius_summary)

    system_instruction = "\n".join(context_lines)

    guidelines = (
        "\n\nGUIDELINES FOR YOUR RESPONSE:\n"
        "1. Be precise, technical, and actionable.\n"
        "2. Cite exact files and line numbers whenever possible in format `[file_path:line]`.\n"
        "3. When explaining flows, architectures, or sequences, ALWAYS generate a valid Mermaid diagram block (```mermaid ... ```).\n"
        "4. Provide step-by-step code fixes for security or refactoring questions.\n"
    )

    model = genai_client.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system_instruction + guidelines,
    )

    # Format history for Gemini chat
    chat_session = model.start_chat(history=session_history)

    try:
        response = await chat_session.send_message_async(user_message)
        response_text = response.text
    except Exception as err:
        traceback.print_exc()
        return ChatResponse(
            response=f"Error generating response: {str(err)}",
            diagrams=[],
            citations=[],
            suggested_followups=[]
        )

    # Update session history in memory
    session_history.append({"role": "user", "parts": [user_message]})
    session_history.append({"role": "model", "parts": [response_text]})
    _sessions[job_id] = session_history[-10:] # Keep last 10 turns

    # Extract Mermaid Diagrams
    diagrams = re.findall(r"```mermaid\s*([\s\S]*?)```", response_text)

    # Extract Citations
    citation_matches = re.findall(r"\[([a-zA-Z0-9_\-./\\]+\.[a-zA-Z0-9]+(?::\d+)?)\]", response_text)
    citations = [{"file_path": c.split(":")[0], "line": int(c.split(":")[1]) if ":" in c else None} for c in set(citation_matches)]

    # Generate Followup Questions
    suggested_followups = [
        "How can I refactor this module for better testability?",
        "What are the top security risks in this codebase?",
        "Show me an end-to-end sequence diagram for the main API route.",
    ]

    return ChatResponse(
        response=response_text,
        diagrams=diagrams,
        citations=citations[:6],
        suggested_followups=suggested_followups,
    )
