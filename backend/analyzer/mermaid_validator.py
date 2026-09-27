import re
from dataclasses import dataclass


VALID_DIAGRAM_TYPES = {
    "graph", "flowchart", "sequenceDiagram", "classDiagram",
    "erDiagram", "gantt", "pie", "gitGraph", "stateDiagram",
    "stateDiagram-v2", "mindmap", "timeline",
}

SPECIAL_CHARS_PATTERN = re.compile(r'[(){}|<>:;@#$%^&*+=\'`~]')
NODE_DEF_PATTERN = re.compile(r'^(\s*)([A-Za-z0-9_]+)([\[\(\{>])([^\]\)\}]*)[\]\)\}]', re.MULTILINE)
ARROW_PATTERN = re.compile(r'--?>|==?>|-=-|-\.->')


@dataclass
class ValidationError:
    line: int
    message: str

    def __str__(self):
        return f"Line {self.line}: {self.message}"


def validate_mermaid(code: str) -> list[ValidationError]:
    errors = []
    lines = code.strip().splitlines()

    if not lines:
        return [ValidationError(0, "Empty diagram")]

    # Check diagram type declaration
    first_line = lines[0].strip()
    diagram_type = first_line.split()[0] if first_line else ""
    if diagram_type not in VALID_DIAGRAM_TYPES:
        errors.append(ValidationError(1, f"Invalid diagram type '{diagram_type}'. Must be one of: {', '.join(sorted(VALID_DIAGRAM_TYPES))}"))
        return errors  # can't validate further without knowing the type

    is_graph = diagram_type in ("graph", "flowchart")
    is_sequence = diagram_type == "sequenceDiagram"
    is_er = diagram_type == "erDiagram"

    for i, raw_line in enumerate(lines[1:], start=2):
        line = raw_line.strip()
        if not line or line.startswith("%%"):
            continue

        if is_graph:
            # Check node labels for unquoted special characters
            for m in NODE_DEF_PATTERN.finditer(raw_line):
                label = m.group(4)
                # Skip if already quoted
                if label.startswith('"') and label.endswith('"'):
                    continue
                if SPECIAL_CHARS_PATTERN.search(label):
                    errors.append(ValidationError(i, f"Node label '{label}' contains special characters — wrap in double quotes: [\"{label}\"]"))

            # Check for 'flowchart' keyword used as diagram type (should be 'graph')
            if re.match(r'^flowchart\s+(TD|LR|BT|RL)\s*$', line):
                errors.append(ValidationError(i, "Use 'graph TD/LR' instead of 'flowchart TD/LR' for Mermaid v10 compatibility"))

            # Subgraph must have a title
            if line.startswith("subgraph") and len(line.split()) < 2:
                errors.append(ValidationError(i, "subgraph must have a title"))

        if is_sequence:
            # participant names with spaces must be aliased
            m = re.match(r'^participant\s+(.+)$', line)
            if m:
                name = m.group(1).strip()
                if ' ' in name and ' as ' not in name.lower():
                    errors.append(ValidationError(i, f"Participant '{name}' has spaces — use alias: participant {name.replace(' ', '')} as \"{name}\""))

            # arrows must use valid syntax
            if '->' in line or '-->' in line:
                if not re.search(r'\w.*-[-\.]?>>?\s*\w', line):
                    errors.append(ValidationError(i, f"Invalid sequence arrow syntax: '{line}'"))

        if is_er:
            # relationship lines must follow: EntityA ||--o{ EntityB : "label"
            if re.search(r'\|\||\}o|o\{|--', line):
                if not re.search(r'\w+\s+[\|\}o\{]+[-\.]+[\|\}o\{]+\s+\w+\s*:', line):
                    errors.append(ValidationError(i, f"Invalid ER relationship syntax: '{line}'"))

    return errors


def is_valid(code: str) -> bool:
    return len(validate_mermaid(code)) == 0


def format_errors(errors: list[ValidationError]) -> str:
    return "\n".join(str(e) for e in errors)
