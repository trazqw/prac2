import os
import shutil
import subprocess


def generate_mermaid(graph):
    lines = ["flowchart TD"]

    packages = set(graph.keys())
    for dependencies in graph.values():
        packages.update(dependencies)


    node_ids = {
        package: f"node_{index}"
        for index, package in enumerate(sorted(packages))
    }

    for package in sorted(packages):
        lines.append(f'    {node_ids[package]}["{package}"]')

    for package, dependencies in graph.items():
        for dependency in dependencies:
            lines.append(
                f"    {node_ids[package]} --> {node_ids[dependency]}"
            )

    return "\n".join(lines) + "\n"


def _find_mmdc():
    executable = shutil.which("mmdc")
    if executable:
        return executable

    local_executable = os.path.join(
        os.getcwd(), "node_modules", ".bin", "mmdc"
    )
    if os.path.isfile(local_executable):
        return local_executable

    return None


def save_graph_visualization(graph, output_file):
    mermaid_code = generate_mermaid(graph)

    base_name = os.path.splitext(output_file)[0]
    mermaid_file = base_name + ".mmd"

    output_directory = os.path.dirname(output_file)
    if output_directory:
        os.makedirs(output_directory, exist_ok=True)

    with open(mermaid_file, "w", encoding="utf-8") as file:
        file.write(mermaid_code)

    mmdc_path = _find_mmdc()
    if mmdc_path is None:
        raise ValueError(
            "Mermaid CLI не найден. В корне проекта выполните: "
            "npm install"
        )

    try:
        subprocess.run(
            [mmdc_path, "-i", mermaid_file, "-o", output_file],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        details = error.stderr or error.stdout or str(error)
        raise ValueError(f"Не удалось создать SVG: {details}") from error

    return mermaid_file, output_file
