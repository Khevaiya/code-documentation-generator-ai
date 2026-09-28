import ast
import re
from pathlib import Path
from typing import Any, Optional
from core.models import ProjectSource, StaticAnalysisResult, KnowledgeGraph, GraphNode, GraphEdge


def _parse_python_ast(file_path: str, content: str):
    """Parses a Python file using AST to extract classes, functions, routes, imports, and calls."""
    classes = []
    functions = []
    routes = []
    imports = []
    calls = []

    try:
        tree = ast.parse(content, filename=file_path)
    except Exception:
        return classes, functions, routes, imports, calls

    for node in ast.walk(tree):
        # Imports
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            for alias in node.names:
                imports.append(f"{mod}.{alias.name}" if mod else alias.name)

        # Classes
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
                "bases": [b.id for b in node.bases if isinstance(b, ast.Name)],
            })

        # Functions / Methods
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_route = False
            route_path = None
            route_method = None

            # Detect route decorators (@app.get, @router.post, etc.)
            for dec in node.decorator_list:
                dec_repr = ""
                if isinstance(dec, ast.Call):
                    if isinstance(dec.func, ast.Attribute):
                        dec_repr = f"{dec.func.attr}"
                    elif isinstance(dec.func, ast.Name):
                        dec_repr = dec.func.id
                    # Extract path argument
                    if dec.args and isinstance(dec.args[0], ast.Constant):
                        route_path = str(dec.args[0].value)
                elif isinstance(dec, ast.Attribute):
                    dec_repr = dec.attr

                if dec_repr.lower() in ("get", "post", "put", "delete", "patch", "options", "head"):
                    is_route = True
                    route_method = dec_repr.upper()

            if is_route and route_path:
                routes.append({
                    "method": route_method or "GET",
                    "path": route_path,
                    "handler": node.name,
                    "line": node.lineno,
                })

            functions.append({
                "name": node.name,
                "line": node.lineno,
                "is_async": isinstance(node, ast.AsyncFunctionDef),
                "args": [a.arg for a in node.args.args],
            })

        # Function Calls
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.append(node.func.attr)

    return classes, functions, routes, imports, calls


def _parse_js_ts(file_path: str, content: str):
    """Regex-based AST scanner for JavaScript / TypeScript files."""
    classes = []
    functions = []
    routes = []
    imports = []
    calls = []

    # Imports: import ... from '...'
    import_matches = re.findall(r'''import\s+.*?\s+from\s+['"]([^'"]+)['"]''', content)
    imports.extend(import_matches)
    require_matches = re.findall(r'''require\(['"]([^'"]+)['"]\)''', content)
    imports.extend(require_matches)

    # Classes: class X
    for match in re.finditer(r'class\s+([A-Za-z0-9_$]+)(?:\s+extends\s+([A-Za-z0-9_$]+))?', content):
        classes.append({
            "name": match.group(1),
            "line": content[:match.start()].count('\n') + 1,
            "bases": [match.group(2)] if match.group(2) else [],
        })

    # Functions: function x() / const x = () => / async function x()
    func_patterns = [
        r'(?:export\s+)?(?:async\s+)?function\s+([A-Za-z0-9_$]+)',
        r'(?:export\s+)?const\s+([A-Za-z0-9_$]+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>',
    ]
    for pat in func_patterns:
        for match in re.finditer(pat, content):
            functions.append({
                "name": match.group(1),
                "line": content[:match.start()].count('\n') + 1,
                "is_async": "async" in match.group(0),
                "args": [],
            })

    # Routes (Express / Next / Koa): app.get('/...', ...), router.post('/...', ...)
    route_matches = re.finditer(r'''(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*['"]([^'"]+)['"]''', content, re.IGNORECASE)
    for rm in route_matches:
        routes.append({
            "method": rm.group(1).upper(),
            "path": rm.group(2),
            "handler": f"{rm.group(1)}_{rm.group(2).replace('/', '_')}",
            "line": content[:rm.start()].count('\n') + 1,
        })

    return classes, functions, routes, imports, calls


def build_knowledge_graph(project: ProjectSource, static_analysis: StaticAnalysisResult) -> KnowledgeGraph:
    """Constructs a comprehensive Code Knowledge Graph (CodeKG) from AST & static analysis."""
    nodes: dict[str, GraphNode] = {}
    edges: list[GraphEdge] = []
    file_to_id: dict[str, str] = {}

    # 1. Add File Nodes
    for f in project.files:
        norm_path = f.relative_path.replace("\\", "/")
        file_id = f"file::{norm_path}"
        file_to_id[norm_path] = file_id

        # Determine layer based on path/role
        layer = "logic"
        lower_path = norm_path.lower()
        if any(w in lower_path for w in ["route", "controller", "endpoint", "api", "handler"]):
            layer = "api"
        elif any(w in lower_path for w in ["model", "schema", "entity", "migration", "db", "repository"]):
            layer = "data"
        elif any(w in lower_path for w in ["frontend", "components", "pages", "views", "ui", "src/app"]):
            layer = "frontend"
        elif any(w in lower_path for w in ["auth", "security", "guard", "crypto", "jwt"]):
            layer = "security"
        elif f.is_config:
            layer = "config"
        elif f.is_test:
            layer = "test"

        complexity = max(1, f.size_bytes // 800)

        nodes[file_id] = GraphNode(
            id=file_id,
            label=Path(norm_path).name,
            type="file",
            layer=layer,
            path=norm_path,
            complexity=complexity,
            details={"language": f.language, "size_bytes": f.size_bytes, "is_entry": f.is_entry_point},
        )

    # 2. Add External Library Nodes (from static analysis)
    for dep in static_analysis.dependencies[:30]:
        lib_id = f"lib::{dep.name}"
        if lib_id not in nodes:
            nodes[lib_id] = GraphNode(
                id=lib_id,
                label=dep.name,
                type="library",
                layer="library",
                complexity=1,
                details={"version": dep.version, "dev_only": dep.dev_only},
            )

    # 3. Parse AST for Code Symbols & Inter-File Relationships
    for f in project.files:
        if not f.content:
            continue

        norm_path = f.relative_path.replace("\\", "/")
        file_id = f"file::{norm_path}"
        ext = Path(norm_path).suffix.lower()

        classes, functions, routes, imports, calls = [], [], [], [], []

        if ext == ".py":
            classes, functions, routes, imports, calls = _parse_python_ast(norm_path, f.content)
        elif ext in (".js", ".jsx", ".ts", ".tsx"):
            classes, functions, routes, imports, calls = _parse_js_ts(norm_path, f.content)

        # Connect File -> Classes
        for cls in classes:
            cls_id = f"class::{norm_path}::{cls['name']}"
            is_model = any(m in cls['name'].lower() for m in ["model", "schema", "entity", "dto"])
            nodes[cls_id] = GraphNode(
                id=cls_id,
                label=cls["name"],
                type="model" if is_model else "class",
                layer="data" if is_model else "logic",
                path=norm_path,
                details={"line": cls["line"], "bases": cls["bases"]},
            )
            edges.append(GraphEdge(source=file_id, target=cls_id, type="contains", label="declares"))

            # Base class inheritance edges
            for base in cls.get("bases", []):
                for other_id, other_node in nodes.items():
                    if other_node.type in ("class", "model") and other_node.label == base:
                        edges.append(GraphEdge(source=cls_id, target=other_id, type="inherits", label="extends"))

        # Connect File -> Functions
        for fn in functions:
            fn_id = f"fn::{norm_path}::{fn['name']}"
            nodes[fn_id] = GraphNode(
                id=fn_id,
                label=f"{fn['name']}()",
                type="function",
                layer=nodes[file_id].layer,
                path=norm_path,
                details={"line": fn["line"], "is_async": fn["is_async"]},
            )
            edges.append(GraphEdge(source=file_id, target=fn_id, type="contains", label="defines"))

        # Connect API Routes
        for rt in routes:
            route_id = f"route::{rt['method']}::{rt['path']}"
            nodes[route_id] = GraphNode(
                id=route_id,
                label=f"{rt['method']} {rt['path']}",
                type="route",
                layer="api",
                path=norm_path,
                details={"method": rt["method"], "path": rt["path"], "handler": rt["handler"]},
            )
            edges.append(GraphEdge(source=file_id, target=route_id, type="handles_route", label="exposes"))

            # Link route to handler function
            handler_id = f"fn::{norm_path}::{rt['handler']}"
            if handler_id in nodes:
                edges.append(GraphEdge(source=route_id, target=handler_id, type="calls", label="routes_to"))

        # Connect Imports (File -> File or File -> Library)
        for imp in imports:
            # Check external libraries
            clean_imp = imp.split('.')[0].replace('@', '').lower()
            lib_id = f"lib::{clean_imp}"
            if lib_id in nodes:
                edges.append(GraphEdge(source=file_id, target=lib_id, type="imports", label="uses"))
            else:
                # Check internal files
                for other_path, other_id in file_to_id.items():
                    if other_id != file_id:
                        other_stem = Path(other_path).stem
                        if other_stem in imp or imp in other_path:
                            edges.append(GraphEdge(source=file_id, target=other_id, type="imports", label="imports"))
                            break

    # 4. Compute Graph Metrics (Degrees, Centrality, Hub Detection, Cycles)
    in_degrees: dict[str, int] = {nid: 0 for nid in nodes}
    out_degrees: dict[str, int] = {nid: 0 for nid in nodes}
    adjacency: dict[str, list[str]] = {nid: [] for nid in nodes}

    for edge in edges:
        if edge.source in out_degrees:
            out_degrees[edge.source] += 1
        if edge.target in in_degrees:
            in_degrees[edge.target] += 1
        if edge.source in adjacency:
            adjacency[edge.source].append(edge.target)

    # Degree centrality & Hub detection
    max_degree = 1
    for nid, node in nodes.items():
        node.in_degree = in_degrees.get(nid, 0)
        node.out_degree = out_degrees.get(nid, 0)
        node.degree = node.in_degree + node.out_degree
        if node.degree > max_degree:
            max_degree = node.degree

    for nid, node in nodes.items():
        node.centrality = round(node.degree / max_degree, 3)
        if node.degree >= 4 or (node.type == "file" and node.in_degree >= 3):
            node.is_hub = True

    # Detect Circular Dependencies
    circular_deps = []
    visited = set()
    rec_stack = set()

    def _find_cycles(curr, path):
        visited.add(curr)
        rec_stack.add(curr)
        for neighbor in adjacency.get(curr, []):
            if neighbor not in visited:
                _find_cycles(neighbor, path + [neighbor])
            elif neighbor in rec_stack:
                cycle_nodes = path[path.index(neighbor):] + [neighbor] if neighbor in path else [curr, neighbor]
                cycle_labels = [nodes[n].label for n in cycle_nodes if n in nodes]
                if len(cycle_labels) > 1 and " -> ".join(cycle_labels) not in circular_deps:
                    circular_deps.append(" -> ".join(cycle_labels))
        rec_stack.remove(curr)

    for nid in list(nodes.keys()):
        if nid not in visited and nodes[nid].type == "file":
            _find_cycles(nid, [nid])

    hub_nodes = [node.label for node in nodes.values() if node.is_hub][:10]
    unique_layers = sorted(list({node.layer for node in nodes.values()}))

    metrics = {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "total_files": len(project.files),
        "total_routes": len([n for n in nodes.values() if n.type == "route"]),
        "total_models": len([n for n in nodes.values() if n.type == "model"]),
        "total_functions": len([n for n in nodes.values() if n.type == "function"]),
        "hub_nodes": hub_nodes,
        "circular_dependencies": circular_deps[:5],
        "has_cycles": len(circular_deps) > 0,
        "layer_counts": {layer: len([n for n in nodes.values() if n.layer == layer]) for layer in unique_layers},
    }

    return KnowledgeGraph(
        nodes=list(nodes.values()),
        edges=edges,
        metrics=metrics,
        layers=unique_layers,
    )


def calculate_blast_radius(kg: KnowledgeGraph, target_node_id: str) -> dict[str, Any]:
    """Finds all upstream callers and downstream dependencies of a specific node."""
    forward_adj: dict[str, list[str]] = {}
    reverse_adj: dict[str, list[str]] = {}

    for edge in kg.edges:
        forward_adj.setdefault(edge.source, []).append(edge.target)
        reverse_adj.setdefault(edge.target, []).append(edge.source)

    downstream = set()  # what this node depends on
    q = [target_node_id]
    while q:
        curr = q.pop(0)
        for nxt in forward_adj.get(curr, []):
            if nxt not in downstream:
                downstream.add(nxt)
                q.append(nxt)

    upstream = set()    # what breaks if this node changes (callers)
    q = [target_node_id]
    while q:
        curr = q.pop(0)
        for prev in reverse_adj.get(curr, []):
            if prev not in upstream:
                upstream.add(prev)
                q.append(prev)

    node_dict = {n.id: n for n in kg.nodes}
    target_node = node_dict.get(target_node_id)

    return {
        "target_node": target_node.dict() if target_node else None,
        "upstream_affected_count": len(upstream),
        "upstream_affected_nodes": [node_dict[nid].dict() for nid in upstream if nid in node_dict],
        "downstream_dependency_count": len(downstream),
        "downstream_dependency_nodes": [node_dict[nid].dict() for nid in downstream if nid in node_dict],
    }
