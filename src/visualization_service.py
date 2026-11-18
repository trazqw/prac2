import shutil
import subprocess
from pathlib import Path

def generate_mermaid(graph):
    lines = ["flowchart TD"]
    packages = set(graph)
    for dependencies in graph.values():
        packages.update(dependencies)
    node_ids = _make_node_ids(packages)
    _append_nodes(lines, packages, node_ids)
    _append_edges(lines, graph, node_ids)
    return "\n".join(lines) + "\n"


def _make_node_ids(packages):
    return {
        package: f"node_{index}"
        for index, package in enumerate(sorted(packages))
    }


def _append_nodes(lines, packages, node_ids):
    for package in sorted(packages):
        label = package.replace('"', "'")
        lines.append(f'    {node_ids[package]}["{label}"]')


def _append_edges(lines, graph, node_ids):
    for package, dependencies in graph.items():
        for dependency in dependencies:
            source = node_ids[package]
            target = node_ids[dependency]
            lines.append(f"    {source} --> {target}")


def _find_mmdc():
    executable = shutil.which("mmdc")
    if executable:
        return executable
    project_root = Path(__file__).resolve().parent.parent
    local = project_root / "node_modules" / ".bin" / "mmdc"
    return str(local) if local.is_file() else None


def save_graph_visualization(graph, output_file):
    output_path = Path(output_file)
    if output_path.suffix.lower() != ".svg":
        raise ValueError("Имя выходного файла должно оканчиваться на .svg")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mermaid_path = output_path.with_suffix(".mmd")
    mermaid_path.write_text(generate_mermaid(graph), encoding="utf-8")
    _render_svg(mermaid_path, output_path)
    return str(mermaid_path), str(output_path)


def _render_svg(mermaid_path, output_path):
    executable = _find_mmdc()
    if executable is None:
        message = "Mermaid CLI не найден. Выполните npm install."
        raise ValueError(message)
    command = [executable, "-i", str(mermaid_path), "-o", str(output_path)]
    try:
        subprocess.run(
            command, check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError as error:
        details = error.stderr or error.stdout or str(error)
        message = f"Не удалось создать SVG: {details}"
        raise ValueError(message) from error
