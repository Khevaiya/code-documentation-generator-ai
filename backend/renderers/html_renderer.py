import re
from core.models import DocumentModel
from renderers.section_renderer import to_html as _sec_html, SECTION_STYLES


def _sanitize_mermaid(code: str) -> str:
    code = re.sub(r'^flowchart\s+(TD|LR|BT|RL)', r'graph \1', code, flags=re.MULTILINE)
    def quote_label(m):
        bracket, content, close = m.group(1), m.group(2), m.group(3)
        open_q, close_q = ('("', '")') if bracket == '(' else ('["', '"]')
        if '"' not in content and re.search(r'[^\w\s\-]', content):
            return f'{open_q}{content}{close_q}'
        return m.group(0)
    code = re.sub(r'([\[\(])([^\]\)"]{15,})([\]\)])', quote_label, code)
    return code


def _badge(sev):
    colors = {"critical": "#dc2626", "high": "#ea580c", "medium": "#d97706", "low": "#2563eb", "info": "#6b7280"}
    c = colors.get(sev, "#6b7280")
    return f'<span class="badge" style="background:{c}">{(sev or "info").upper()}</span>'


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_html(doc: DocumentModel, output_path: str) -> str:
    sa = doc.static_analysis

    lens_html = ""
    for i, lr in enumerate(doc.lens_results):
        findings_html = ""
        for f in lr.findings:
            cit = ""
            if f.citations:
                cit = '<div class="citations"><strong>Evidence:</strong><ul>'
                for c in f.citations:
                    loc = f"<code>{_esc(c.file_path)}</code>"
                    if c.line_start:
                        loc += f" (L{c.line_start})"
                    cit += f"<li>{loc} <em>[{_esc(c.confidence)}]</em>"
                    if c.snippet:
                        cit += f"<pre>{_esc(c.snippet)}</pre>"
                    cit += "</li>"
                cit += "</ul></div>"
            rec = f'<div class="recommendation"><strong>Rec:</strong> {_esc(f.recommendation)}</div>' if f.recommendation else ""
            findings_html += (
                f'<div class="finding">'
                f'<div class="finding-header">{_badge(f.severity)}'
                f'<span class="finding-title">{_esc(f.title)}</span></div>'
                f'<p>{_esc(f.description)}</p>{cit}{rec}</div>'
            )

        diagrams_html = ""
        for d in lr.diagrams:
            if d.use_svg and d.svg:
                diagrams_html += f'<div class="diagram-container"><h4>{_esc(d.title)}</h4>{d.svg}</div>'
            else:
                safe_code = _esc(_sanitize_mermaid(d.mermaid_code))
                diagrams_html += f'<div class="diagram-container"><h4>{_esc(d.title)}</h4><pre class="mermaid">{safe_code}</pre></div>'

        gaps_html = ""
        if lr.gaps:
            gaps_html = '<div class="gaps"><h3>Gaps</h3><ul>'
            for g in lr.gaps:
                rec_part = f"<br><em>{_esc(g.recommendation)}</em>" if g.recommendation else ""
                gaps_html += f'<li>{_badge(g.severity)}<strong>{_esc(g.area)}:</strong> {_esc(g.description)}{rec_part}</li>'
            gaps_html += "</ul></div>"

        sections_html = "".join(
            f'<div class="section-block"><h3>{_esc(k)}</h3>{_sec_html(v)}</div>'
            for k, v in lr.raw_sections.items()
        )

        findings_block = f'<h3>Findings ({len(lr.findings)})</h3>{findings_html}' if findings_html else ""
        lens_html += (
            f'<section class="lens-section" id="lens-{i}">'
            f'<h2 class="lens-title" onclick="toggleSection(this)">'
            f'<span class="toggle-icon">&#9660;</span> {_esc(lr.title)}</h2>'
            f'<div class="lens-content">'
            f'<div class="summary">{_esc(lr.summary)}</div>'
            f'{diagrams_html}{findings_block}{sections_html}{gaps_html}'
            f'</div></section>'
        )

    fw_table = ""
    if sa.frameworks:
        rows = "".join(
            f"<tr><td>{_esc(fw.name)}</td><td>{_esc(fw.category)}</td><td>{_esc(fw.version or 'N/A')}</td></tr>"
            for fw in sa.frameworks
        )
        fw_table = (
            '<h3>Frameworks &amp; Libraries</h3>'
            '<table class="data-table"><thead><tr><th>Framework</th><th>Category</th><th>Version</th></tr></thead>'
            f'<tbody>{rows}</tbody></table>'
        )

    nav = "".join(
        f'<a href="#lens-{i}" class="nav-link">{_esc(lr.title)}</a>'
        for i, lr in enumerate(doc.lens_results)
    )

    stat_cards = (
        f'<div class="stat-card"><div class="label">Primary Language</div><div class="value">{_esc(sa.primary_language or "Unknown")}</div></div>'
        f'<div class="stat-card"><div class="label">Architecture</div><div class="value">{_esc(sa.architecture_pattern or "Unknown")}</div></div>'
        f'<div class="stat-card"><div class="label">Test Files</div><div class="value">{len(sa.test_files)}</div></div>'
        f'<div class="stat-card"><div class="label">API Routes</div><div class="value">{len(sa.api_routes)}</div></div>'
        f'<div class="stat-card"><div class="label">CI/CD</div><div class="value">{"Yes" if sa.has_ci else "No"}</div></div>'
        f'<div class="stat-card"><div class="label">Docker</div><div class="value">{"Yes" if sa.has_docker else "No"}</div></div>'
    )

    source_meta = f' &bull; Source: {_esc(doc.source_url)}' if doc.source_url else ''
    generated = doc.generated_at.strftime('%B %d, %Y at %H:%M UTC')
    generated_footer = doc.generated_at.strftime('%Y-%m-%d %H:%M UTC')

    # Build CSS separately to avoid brace escaping issues in f-strings
    css = (
        ":root{--primary:#1E3A5F;--primary-light:#2E5984;--accent:#3B82F6;"
        "--bg:#F8FAFC;--card:#FFF;--text:#1E293B;--text2:#64748B;--border:#E2E8F0;}"
        "*{box-sizing:border-box;margin:0;padding:0;}"
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;"
        "background:var(--bg);color:var(--text);line-height:1.6;}"
        ".container{max-width:1200px;margin:0 auto;padding:0 24px;}"
        "header{background:linear-gradient(135deg,var(--primary),var(--primary-light));"
        "color:#fff;padding:48px 0 36px;}"
        "header h1{font-size:2.2rem;margin-bottom:8px;}"
        "header .meta{opacity:.8;font-size:.9rem;}"
        ".sidebar{position:fixed;top:0;left:0;width:260px;height:100vh;background:var(--primary);"
        "color:#fff;padding:20px 0;overflow-y:auto;z-index:100;transform:translateX(-100%);transition:transform .3s;}"
        ".sidebar.open{transform:translateX(0);}"
        ".nav-link{display:block;padding:10px 24px;color:rgba(255,255,255,.8);text-decoration:none;"
        "font-size:.9rem;border-left:3px solid transparent;}"
        ".nav-link:hover{background:rgba(255,255,255,.1);color:#fff;border-left-color:var(--accent);}"
        ".menu-btn{position:fixed;top:16px;left:16px;z-index:200;background:var(--primary);color:#fff;"
        "border:none;padding:8px 12px;border-radius:6px;cursor:pointer;font-size:1.2rem;}"
        ".main-content{padding:32px 0;}"
        ".overview-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px;margin:24px 0;}"
        ".stat-card{background:var(--card);border-radius:10px;padding:20px;box-shadow:0 1px 3px rgba(0,0,0,.08);}"
        ".stat-card .label{font-size:.8rem;color:var(--text2);text-transform:uppercase;letter-spacing:.05em;}"
        ".stat-card .value{font-size:1.4rem;font-weight:700;color:var(--primary);margin-top:4px;}"
        ".lens-section{background:var(--card);border-radius:12px;margin:20px 0;"
        "box-shadow:0 1px 3px rgba(0,0,0,.08);overflow:hidden;}"
        ".lens-title{padding:20px 24px;cursor:pointer;font-size:1.3rem;color:var(--primary);"
        "border-bottom:1px solid var(--border);display:flex;align-items:center;gap:8px;user-select:none;}"
        ".lens-title:hover{background:#F1F5F9;}"
        ".toggle-icon{font-size:.8rem;transition:transform .2s;}"
        ".lens-content{padding:24px;}"
        ".lens-content.collapsed{display:none;}"
        ".summary{color:var(--text2);margin-bottom:20px;font-size:1rem;line-height:1.7;}"
        ".finding{border:1px solid var(--border);border-radius:8px;padding:16px;margin:12px 0;}"
        ".finding-header{display:flex;align-items:center;gap:10px;margin-bottom:8px;}"
        ".finding-title{font-weight:600;}"
        ".badge{display:inline-block;padding:2px 10px;border-radius:12px;color:#fff;font-size:.7rem;font-weight:700;}"
        ".citations{background:#F8FAFC;border-radius:6px;padding:12px;margin-top:10px;font-size:.9rem;}"
        ".citations ul{margin-left:16px;}"
        ".citations pre{background:#1E293B;color:#E2E8F0;padding:8px 12px;border-radius:4px;"
        "margin-top:4px;font-size:.8rem;overflow-x:auto;}"
        ".recommendation{background:#EFF6FF;border-left:3px solid var(--accent);padding:10px 14px;"
        "margin-top:10px;border-radius:0 6px 6px 0;font-size:.9rem;}"
        ".gaps ul{list-style:none;}"
        ".gaps li{padding:10px 0;border-bottom:1px solid var(--border);}"
        ".diagram-container{margin:20px 0;}"
        ".data-table{width:100%;border-collapse:collapse;margin:16px 0;}"
        ".data-table th{background:var(--primary);color:#fff;padding:10px 14px;text-align:left;font-size:.85rem;}"
        ".data-table td{padding:10px 14px;border-bottom:1px solid var(--border);font-size:.9rem;}"
        ".data-table tr:nth-child(even){background:#F8FAFC;}"
        ".search-box{margin:20px 0;padding:12px 16px;width:100%;border:1px solid var(--border);"
        "border-radius:8px;font-size:1rem;outline:none;}"
        ".search-box:focus{border-color:var(--accent);box-shadow:0 0 0 3px rgba(59,130,246,.1);}"
        ".section-block{margin:20px 0;}"
        + SECTION_STYLES
    )

    html = (
        '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1.0">'
        f'<title>{_esc(doc.project_name)} \u2014 Analysis Report</title>'
        '<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>'
        f'<style>{css}</style></head><body>'
        '<button class="menu-btn" onclick="document.querySelector(\'.sidebar\').classList.toggle(\'open\')">&#9776;</button>'
        '<nav class="sidebar">'
        '<div style="padding:20px 24px;font-weight:700;font-size:1.1rem;'
        'border-bottom:1px solid rgba(255,255,255,.1);margin-bottom:10px;">Navigation</div>'
        '<a href="#overview" class="nav-link">Project Overview</a>'
        f'{nav}</nav>'
        f'<header><div class="container"><h1>{_esc(doc.project_name)}</h1>'
        f'<div class="meta">Codebase Analysis Report &bull; Generated {generated}{source_meta}</div>'
        '</div></header>'
        '<div class="container main-content">'
        '<input type="text" class="search-box" placeholder="Search findings..." oninput="searchFindings(this.value)">'
        '<section id="overview">'
        '<h2 style="color:var(--primary);margin-bottom:16px;">Project Overview</h2>'
        f'<div class="overview-grid">{stat_cards}</div>{fw_table}'
        '</section>'
        f'{lens_html}'
        '</div>'
        f'<footer style="text-align:center;padding:40px 0;color:var(--text2);font-size:.85rem;">'
        f'Generated by Codebase Analysis Agent &bull; {generated_footer}</footer>'
        '<script>'
        'mermaid.initialize({startOnLoad:true,theme:\'neutral\'});'
        'function toggleSection(el){const c=el.nextElementSibling,ico=el.querySelector(\'.toggle-icon\');'
        'c.classList.toggle(\'collapsed\');ico.style.transform=c.classList.contains(\'collapsed\')?\'rotate(-90deg)\':\'\';}' 
        'function searchFindings(q){document.querySelectorAll(\'.finding\').forEach(f=>{f.style.display=f.textContent.toLowerCase().includes(q.toLowerCase())||!q?\'\':\'none\';});}'
        '</script></body></html>'
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path
