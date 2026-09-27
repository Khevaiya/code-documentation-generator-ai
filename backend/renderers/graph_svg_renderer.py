"""
Pure-Python SVG generator from nodes+edges JSON.
No external dependencies — works everywhere.
"""
import math


NODE_COLORS = {
    "service":  {"fill": "#DBEAFE", "stroke": "#2563EB", "text": "#1E3A5F"},
    "database": {"fill": "#D1FAE5", "stroke": "#059669", "text": "#065F46"},
    "queue":    {"fill": "#FEF3C7", "stroke": "#D97706", "text": "#92400E"},
    "external": {"fill": "#F3E8FF", "stroke": "#7C3AED", "text": "#4C1D95"},
    "client":   {"fill": "#FFE4E6", "stroke": "#E11D48", "text": "#881337"},
    "process":  {"fill": "#F1F5F9", "stroke": "#64748B", "text": "#1E293B"},
}
DEFAULT_COLOR = {"fill": "#F1F5F9", "stroke": "#64748B", "text": "#1E293B"}

NODE_W, NODE_H = 160, 48
H_GAP, V_GAP = 60, 60


def _layout(nodes: list, edges: list) -> dict[str, tuple[float, float]]:
    """Simple layered layout: topological sort → assign rows → center columns."""
    ids = [n["id"] for n in nodes]
    # Build adjacency
    children: dict[str, list] = {i: [] for i in ids}
    parents: dict[str, list]  = {i: [] for i in ids}
    for e in edges:
        if e["from"] in children and e["to"] in parents:
            children[e["from"]].append(e["to"])
            parents[e["to"]].append(e["from"])

    # Topological layers (Kahn's algorithm)
    in_degree = {i: len(parents[i]) for i in ids}
    queue = [i for i in ids if in_degree[i] == 0]
    layers: list[list[str]] = []
    visited: set = set()

    while queue:
        layers.append(queue[:])
        next_q = []
        for node in queue:
            visited.add(node)
            for child in children[node]:
                in_degree[child] -= 1
                if in_degree[child] == 0 and child not in visited:
                    next_q.append(child)
        queue = next_q

    # Any remaining nodes (cycles) go in last layer
    remaining = [i for i in ids if i not in visited]
    if remaining:
        layers.append(remaining)

    # Assign (x, y) positions
    positions: dict[str, tuple[float, float]] = {}
    for row, layer in enumerate(layers):
        total_w = len(layer) * NODE_W + (len(layer) - 1) * H_GAP
        start_x = -total_w / 2 + NODE_W / 2
        for col, node_id in enumerate(layer):
            x = start_x + col * (NODE_W + H_GAP)
            y = row * (NODE_H + V_GAP)
            positions[node_id] = (x, y)

    return positions


def _wrap(text: str, max_chars: int = 20) -> list[str]:
    """Wrap text into lines of max_chars."""
    words = text.split()
    lines, current = [], ""
    for w in words:
        if len(current) + len(w) + 1 <= max_chars:
            current = f"{current} {w}".strip()
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines or [text]


def render_graph_svg(graph: dict, title: str = "") -> str:
    """Render nodes+edges dict to SVG string."""
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])

    if not nodes:
        return _empty_svg(title)

    positions = _layout(nodes, edges)
    node_map = {n["id"]: n for n in nodes}

    # Compute canvas size
    xs = [p[0] for p in positions.values()]
    ys = [p[1] for p in positions.values()]
    min_x, max_x = min(xs) - NODE_W / 2, max(xs) + NODE_W / 2
    min_y, max_y = min(ys) - NODE_H / 2, max(ys) + NODE_H / 2

    padding = 60
    title_h = 36 if title else 0
    vb_x = min_x - padding
    vb_y = min_y - padding - title_h
    vb_w = (max_x - min_x) + padding * 2
    vb_h = (max_y - min_y) + padding * 2 + title_h
    svg_w = max(vb_w, 400)
    svg_h = max(vb_h, 200)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_w}" height="{svg_h}" '
        f'viewBox="{vb_x} {vb_y} {vb_w} {vb_h}">',
        '<defs>'
        '<marker id="arrow" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">'
        '<polygon points="0 0, 10 3.5, 0 7" fill="#64748B"/>'
        '</marker>'
        '</defs>',
        f'<rect x="{vb_x}" y="{vb_y}" width="{vb_w}" height="{vb_h}" fill="#F8FAFC" rx="8"/>',
    ]

    # Title
    if title:
        parts.append(
            f'<text x="{vb_x + vb_w/2}" y="{min_y - padding/2}" '
            f'text-anchor="middle" font-family="Arial" font-size="16" '
            f'font-weight="bold" fill="#1E3A5F">{_esc(title)}</text>'
        )

    # Edges first (drawn behind nodes)
    for edge in edges:
        src = edge.get("from", "")
        dst = edge.get("to", "")
        if src not in positions or dst not in positions:
            continue
        x1, y1 = positions[src]
        x2, y2 = positions[dst]

        # Arrow from bottom of src to top of dst (or side if same row)
        if abs(y1 - y2) > abs(x1 - x2):
            # vertical connection
            sy = y1 + NODE_H / 2
            ey = y2 - NODE_H / 2 - 6
            ex, ey2 = x2, ey
            sx = x1
        else:
            # horizontal connection
            sx = x1 + NODE_W / 2 if x2 > x1 else x1 - NODE_W / 2
            sy = y1
            ex = x2 - NODE_W / 2 - 6 if x2 > x1 else x2 + NODE_W / 2 + 6
            ey2 = y2

        mx, my = (sx + ex) / 2, (sy + ey2) / 2
        parts.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{ex:.1f}" y2="{ey2:.1f}" '
            f'stroke="#94A3B8" stroke-width="1.5" marker-end="url(#arrow)"/>'
        )

        label = edge.get("label", "")
        if label:
            parts.append(
                f'<rect x="{mx - len(label)*3:.1f}" y="{my - 9:.1f}" '
                f'width="{len(label)*6:.1f}" height="14" fill="white" opacity="0.85"/>'
                f'<text x="{mx:.1f}" y="{my:.1f}" text-anchor="middle" '
                f'font-family="Arial" font-size="9" fill="#64748B">{_esc(label)}</text>'
            )

    # Nodes
    for node in nodes:
        nid = node["id"]
        if nid not in positions:
            continue
        cx, cy = positions[nid]
        x, y = cx - NODE_W / 2, cy - NODE_H / 2
        ntype = node.get("type", "process")
        colors = NODE_COLORS.get(ntype, DEFAULT_COLOR)
        label = node.get("label", nid)
        lines = _wrap(label, 20)
        line_h = 13
        text_total = len(lines) * line_h
        text_y_start = cy - text_total / 2 + line_h / 2

        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{NODE_W}" height="{NODE_H}" '
            f'rx="6" fill="{colors["fill"]}" stroke="{colors["stroke"]}" stroke-width="1.5"/>'
        )
        for li, line in enumerate(lines):
            ty = text_y_start + li * line_h
            parts.append(
                f'<text x="{cx:.1f}" y="{ty:.1f}" text-anchor="middle" dominant-baseline="middle" '
                f'font-family="Arial" font-size="11" fill="{colors["text"]}">{_esc(line)}</text>'
            )

    parts.append('</svg>')
    return "\n".join(parts)


def _empty_svg(title: str = "") -> str:
    msg = title or "No diagram data"
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="80">'
        f'<rect width="400" height="80" fill="#F8FAFC" rx="8"/>'
        f'<text x="200" y="40" text-anchor="middle" font-family="Arial" '
        f'font-size="13" fill="#94A3B8">{_esc(msg)}</text></svg>'
    )


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")
