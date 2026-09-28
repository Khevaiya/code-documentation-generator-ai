import asyncio
import json
import re
import traceback

import google.generativeai as genai

from core.config import GEMINI_API_KEY, GEMINI_MODEL
from mermaid import Mermaid
from mermaid.__main__ import MermaidError

MAX_OUTPUT_TOKENS = 65536


import os

def get_client():
    api_key = os.getenv("GEMINI_API_KEY") or GEMINI_API_KEY
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    genai.configure(api_key=api_key)
    return genai



def repair_truncated_json(text: str) -> str:
    """
    Repair JSON cut off mid-stream. Handles:
    - String cut mid-key   → close key + add null value
    - String cut mid-value → close value string
    - Open arrays / objects → close them in order
    - Trailing commas → strip before closing
    """
    stack = []          # 'o' = object, 'a' = array
    in_string = False
    is_key = False      # inside an object, before the colon
    escape_next = False
    last_colon_pos = -1

    for i, ch in enumerate(text):
        if escape_next:
            escape_next = False
            continue
        if ch == '\\' and in_string:
            escape_next = True
            continue
        if ch == '"':
            if not in_string:
                in_string = True
                # If we're in an object and just opened a string,
                # track whether this is likely a key
                if stack and stack[-1] == 'o':
                    # We're a key if the last non-whitespace char before us
                    # was '{' or ','
                    preceding = text[:i].rstrip()
                    if preceding and preceding[-1] in ('{', ','):
                        is_key = True
                    else:
                        is_key = False
            else:
                in_string = False
                is_key = False
            continue
        if in_string:
            continue
        if ch == ':':
            last_colon_pos = i
            is_key = False
        elif ch == '{':
            stack.append('o')
        elif ch == '[':
            stack.append('a')
        elif ch == '}':
            if stack and stack[-1] == 'o':
                stack.pop()
        elif ch == ']':
            if stack and stack[-1] == 'a':
                stack.pop()

    repaired = text

    # Case 1: We ended inside a string
    if in_string:
        if is_key:
            # We were mid-key → close key + add null value
            repaired += '": null'
        else:
            # We were mid-value → just close the string
            repaired += '"'

    # Remove trailing comma (invalid before closing bracket)
    stripped = repaired.rstrip()
    if stripped and stripped[-1] == ',':
        repaired = stripped[:-1]

    # Close all open containers in reverse order
    for frame in reversed(stack):
        repaired += '}' if frame == 'o' else ']'

    return repaired


def _fix_invalid_escapes(text: str) -> str:
    """Replace invalid JSON escape sequences (e.g. \\p, \\U, \\s) with \\\\."""
    valid_escapes = set('"\\/bfnrtu')
    result = []
    i = 0
    while i < len(text):
        if text[i] == '\\' and i + 1 < len(text):
            if text[i + 1] in valid_escapes:
                result.append(text[i])
            else:
                result.append('\\\\')
            i += 1
        else:
            result.append(text[i])
        i += 1
    return ''.join(result)


def _try_parse(candidate: str) -> dict | None:
    """Try direct parse, then with invalid-escape fix."""
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        pass
    try:
        return json.loads(_fix_invalid_escapes(candidate))
    except json.JSONDecodeError:
        return None


def extract_json(text: str) -> dict:
    if not text:
        raise ValueError("Gemini returned empty response")

    text = text.strip()

    # 1. Direct parse (with escape fix fallback)
    result = _try_parse(text)
    if result is not None:
        return result

    # 2. Strip markdown code fences
    for pattern in [r"```json\s*(.*?)\s*```", r"```\s*(.*?)\s*```"]:
        match = re.search(pattern, text, re.DOTALL)
        if match:
            result = _try_parse(match.group(1).strip())
            if result is not None:
                return result

    # 3. First { ... last } extraction
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        result = _try_parse(text[first:last + 1])
        if result is not None:
            return result

    # 4. JSON repair — truncated response recovery
    if first != -1:
        json_body = text[first:]
        try:
            repaired = repair_truncated_json(json_body)
            result = _try_parse(repaired)
            if result is not None:
                print(f"[gemini_client] WARNING: Used JSON repair — response truncated at {len(text)} chars")
                return result
        except json.JSONDecodeError as e:
            print(f"[gemini_client] JSON repair failed: {e}")

    raise ValueError(
        f"Could not extract valid JSON.\n"
        f"Response length: {len(text)} chars\n"
        f"Preview: {text[:300]}"
    )


def _sanitize_mermaid_code(code: str) -> str:
    """Auto-fix common LLM mermaid mistakes before validation."""
    # Replace flowchart with graph
    code = re.sub(r'^flowchart\s+(TD|LR|BT|RL)', r'graph \1', code, flags=re.MULTILINE)

    is_sequence = code.strip().startswith('sequenceDiagram')

    def strip_parens(text):
        text = re.sub(r'\s*\([^)]*\)', '', text)
        text = re.sub(r'\{[^}]*\}', '', text)
        return text.strip()

    if is_sequence:
        # Sequence diagrams: clean arrow labels line by line
        def clean_seq_line(line):
            # Match: anything ->> / --> / -->> / -- participant: label
            m = re.match(r'^(\s*(?:[\w]+)\s*(?:->>|-->|-->>|--)\s*(?:[\w]+))\s*:\s*(.+)$', line)
            if not m:
                return line
            prefix, label = m.group(1), m.group(2)
            label = re.sub(r'\|([^|]*)\|', r'\1', label)   # strip |...|
            label = re.sub(r'"([^"]*)"', r'\1', label)      # strip quotes
            label = re.sub(r':', ' -', label).strip()        # colons -> dash
            return prefix + ': ' + label
        code = '\n'.join(clean_seq_line(l) for l in code.splitlines())
        return code

    # --- graph/flowchart fixes below ---

    def fix_bracket_label(m):
        open_b, content, close_b = m.group(1), m.group(2), m.group(3)
        if content.startswith('"') and content.endswith('"'):
            return m.group(0)
        fixed = strip_parens(content)
        if re.search(r'[^\w\s\-]', fixed):
            return f'{open_b}"{fixed}"{close_b}'
        return f'{open_b}{fixed}{close_b}'

    # Fix node labels [...] and {...}
    code = re.sub(r'(\[)([^\]"]{2,})(\])', fix_bracket_label, code)
    code = re.sub(r'(\{)([^\}"]{2,})(\})', fix_bracket_label, code)

    # Fix edge labels |...| — strip colons, parentheses and special chars
    def fix_edge_label(m):
        content = m.group(1)
        if '(' in content or ')' in content:
            content = strip_parens(content)
        content = re.sub(r'[{}:]', '', content).strip()
        return f'|{content}|'

    code = re.sub(r'\|([^|\n]+)\|', fix_edge_label, code)

    # Fix "-->|label| NODE(label): extra text" and "--> NODE(label): extra text"
    def fix_node_colon(m):
        prefix, node_expr, colon_text = m.group(1), m.group(2), m.group(3).strip()
        colon_text = re.sub(r'[{}:|]', '', colon_text).strip()
        if '|' in prefix:
            return f'{prefix} {node_expr}'
        if colon_text:
            return f'-->|"{colon_text}"| {node_expr}'
        return f'--> {node_expr}'

    code = re.sub(
        r'(-->(?:\s*\|[^|\n]*\|)?)\s*([A-Za-z0-9_]+(?:\([^)\n]*\)|\[[^\]\n]*\])?):\s*([^\n]+)',
        fix_node_colon, code
    )

    return code


def _validate_diagrams(diagrams: list) -> list[tuple[int, str]]:
    """Sanitize then validate each diagram using mermaid-py (calls mermaid.ink API).
    Falls back to local mermaid_validator.py if the API is unreachable.
    Returns list of (index, error_message) for invalid diagrams."""
    errors = []
    for i, d in enumerate(diagrams):
        if not isinstance(d, dict):
            continue
        code = d.get("mermaid_code", "")
        if not code:
            continue
        # Auto-fix common issues before hitting the validator
        sanitized = _sanitize_mermaid_code(code)
        d["mermaid_code"] = sanitized  # update in-place so renderer uses fixed code
        try:
            Mermaid(sanitized)
        except MermaidError as e:
            errors.append((i, str(e)))
        except Exception as e:
            # Network/timeout — fall back to local regex validator
            print(f"[gemini_client] mermaid.ink unreachable ({e}), using local validator")
            from analyzer.mermaid_validator import validate_mermaid, format_errors
            local_errors = validate_mermaid(sanitized)
            if local_errors:
                errors.append((i, format_errors(local_errors)))
    return errors


async def call_gemini(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.2,
) -> dict:
    get_client()
    loop = asyncio.get_event_loop()

    def _sync_call(prompt: str) -> str:
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=MAX_OUTPUT_TOKENS,
                response_mime_type="application/json",
            ),
        )
        response = model.generate_content(prompt)
        if not response.text:
            raise ValueError("Gemini returned empty text")
        return response.text

    try:
        current_prompt = f"{system_prompt}\n\n{user_prompt}"

        for attempt in range(3):
            text = await loop.run_in_executor(None, _sync_call, current_prompt)
            result = extract_json(text)

            # Validate diagrams with real Mermaid parser
            diagram_errors = _validate_diagrams(result.get("diagrams", []))
            if not diagram_errors:
                return result

            # Build correction prompt for next turn
            error_details = "\n".join(
                f"Diagram {i} ('{result['diagrams'][i].get('title', '')}'): {err}"
                for i, err in diagram_errors
            )
            print(f"[gemini_client] Mermaid validation failed (attempt {attempt + 1}/3):\n{error_details}")

            if attempt < 2:
                current_prompt = (
                    f"{system_prompt}\n\n{user_prompt}\n\n"
                    f"IMPORTANT: Your previous response had invalid Mermaid diagram syntax. "
                    f"Fix ONLY the diagrams array. Errors:\n{error_details}\n"
                    f"Rules: use 'graph TD' not 'flowchart', quote labels with special chars using [\"label\"], "
                    f"no parentheses () inside node labels, single-word participant names, "
                    f"NO colons inside edge labels |label| (colons cause parse errors)."
                )

        # After 3 attempts, fall back to graph SVG for invalid diagrams
        print("[gemini_client] Mermaid validation failed after 3 attempts — falling back to graph SVG")
        from renderers.graph_svg_renderer import render_graph_svg
        bad_indices = {i for i, _ in diagram_errors}
        for j in bad_indices:
            d = result["diagrams"][j]
            graph = d.get("graph") if isinstance(d, dict) else None
            if graph:
                d["svg"] = render_graph_svg(graph, d.get("title", ""))
                d["use_svg"] = True
            else:
                # No graph data either — remove the diagram
                result["diagrams"][j] = None
        result["diagrams"] = [d for d in result["diagrams"] if d is not None]
        return result

    except RuntimeError:
        raise
    except Exception as e:
        traceback.print_exc()
        raise RuntimeError(f"Gemini API call failed: {type(e).__name__}: {str(e)}")


async def call_gemini_text(
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.3,
) -> str:
    get_client()
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    loop = asyncio.get_event_loop()

    def _sync_call():
        model = genai.GenerativeModel(
            model_name=GEMINI_MODEL,
            generation_config=genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=MAX_OUTPUT_TOKENS,
            ),
        )
        response = model.generate_content(full_prompt)
        return response.text

    return await loop.run_in_executor(None, _sync_call)