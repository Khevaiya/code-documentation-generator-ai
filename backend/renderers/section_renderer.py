"""
Converts arbitrary nested section data (dict/list/str) from LLM output
into clean HTML or Markdown — no raw JSON ever shown to users.
"""
import html as _html


def _esc(s: str) -> str:
    return _html.escape(str(s))


def to_html(value, depth: int = 0) -> str:
    """Recursively render a section value as HTML."""
    if value is None:
        return ""

    if isinstance(value, str):
        # Preserve line breaks
        return f"<p>{'<br>'.join(_esc(line) for line in value.splitlines())}</p>"

    if isinstance(value, list):
        # List of strings → <ul>, list of dicts → grouped cards
        if all(isinstance(i, str) for i in value):
            items = "".join(f"<li>{_esc(i)}</li>" for i in value)
            return f"<ul>{items}</ul>"
        parts = []
        for item in value:
            parts.append(to_html(item, depth + 1))
        return "".join(parts)

    if isinstance(value, dict):
        # Well-known compliance-style keys get special treatment
        parts = []
        for k, v in value.items():
            label = k.replace("_", " ").title()
            inner = to_html(v, depth + 1)

            if depth == 0:
                parts.append(
                    f'<div class="section-card">'
                    f'<div class="section-card-title">{_esc(label)}</div>'
                    f'{inner}</div>'
                )
            else:
                parts.append(
                    f'<div class="section-row">'
                    f'<span class="section-key">{_esc(label)}:</span> {inner}</div>'
                )
        return "".join(parts)

    # Scalar fallback
    return f"<span>{_esc(str(value))}</span>"


def to_md(value, depth: int = 0) -> str:
    """Recursively render a section value as Markdown."""
    if value is None:
        return ""

    if isinstance(value, str):
        return value

    if isinstance(value, list):
        if all(isinstance(i, str) for i in value):
            return "\n".join(f"- {i}" for i in value)
        return "\n\n".join(to_md(i, depth + 1) for i in value)

    if isinstance(value, dict):
        lines = []
        prefix = "#" * min(depth + 4, 6)
        for k, v in value.items():
            label = k.replace("_", " ").title()
            rendered = to_md(v, depth + 1)
            if isinstance(v, (dict, list)):
                lines += [f"{prefix} {label}", "", rendered, ""]
            else:
                lines.append(f"**{label}:** {rendered}")
        return "\n".join(lines)

    return str(value)


SECTION_STYLES = """
.section-card{background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:16px;margin:12px 0;}
.section-card-title{font-weight:700;font-size:1rem;color:#1E3A5F;margin-bottom:10px;text-transform:capitalize;}
.section-row{margin:4px 0;font-size:.9rem;line-height:1.6;}
.section-key{font-weight:600;color:#2E5984;}
.section-card ul{margin:6px 0 0 18px;}
.section-card li{margin:3px 0;font-size:.9rem;}
"""
