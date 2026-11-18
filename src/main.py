import argparse
import re
import xml.etree.ElementTree as element_tree
from pathlib import Path
from urllib.parse import urlsplit

from src.graph_service import build_graph, find_reverse_dependencies
from src.visualization_service import save_graph_visualization

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MIN_DEPTH = 0
REQUIRED_PARAMETERS = (
    "package_name",
    "repository_url",
    "test_repository_path",
    "test_mode",
    "package_version",
    "output_file",
    "max_depth",
    "filter_substring",
)


def load_config(config_path=None):
    path = Path(config_path) if config_path else PROJECT_ROOT / "config.xml"
    try:
        root = element_tree.parse(path).getroot()
    except element_tree.ParseError as error:
        raise ValueError(f"Ошибка формата XML-файла: {error}") from error
    except (FileNotFoundError, IsADirectoryError) as error:
        raise ValueError(f"Файл конфигурации не найден: {path}") from error
    if root.tag != "configuration":
        raise ValueError("Неверный корневой элемент XML")
    config = {}
    for parameter in REQUIRED_PARAMETERS:
        element = root.find(parameter)
        if element is None:
            raise ValueError(f"Отсутствует параметр: {parameter}")
        config[parameter] = (element.text or "").strip()
    return config


def validate_config(config):
    errors = []
    _validate_required(config, errors)
    _validate_mode(config, errors)
    _validate_name(config, errors)
    _validate_version(config, errors)
    _validate_url(config, errors)
    _validate_test_path(config, errors)
    _validate_output(config, errors)
    _validate_depth(config, errors)
    return errors


def _validate_required(config, errors):
    labels = {
        "package_name": "имя пакета",
        "package_version": "версия пакета",
        "output_file": "имя выходного файла",
    }
    for field, label in labels.items():
        if not config[field]:
            errors.append(f"Не задано {label}")


def _validate_name(config, errors):
    name = config["package_name"]
    if not name:
        return
    if config["test_mode"].lower() == "true":
        pattern = r"[A-Z]+"
    else:
        pattern = r"[A-Za-z0-9][A-Za-z0-9_-]*"
    if re.fullmatch(pattern, name) is None:
        errors.append("Некорректное имя анализируемого пакета")


def _validate_version(config, errors):
    version = config["package_version"]
    if not version:
        return
    part = r"(0|[1-9][0-9]*)"
    suffix = r"(?:-[A-Za-z0-9.-]+)?(?:\+[A-Za-z0-9.-]+)?"
    if re.fullmatch(rf"{part}\.{part}\.{part}{suffix}", version) is None:
        errors.append("Версия пакета должна иметь формат MAJOR.MINOR.PATCH")


def _validate_url(config, errors):
    address = config["repository_url"]
    try:
        parts = urlsplit(address)
        valid = (
            parts.scheme in ("http", "https")
            and bool(parts.hostname)
            and parts.port != 0
        )
    except ValueError:
        valid = False
    if not valid:
        errors.append("Некорректный URL репозитория")


def _validate_mode(config, errors):
    if config["test_mode"].lower() not in ("true", "false"):
        errors.append("test_mode должен быть true или false")


def _validate_test_path(config, errors):
    if config["test_mode"].lower() != "true":
        return
    path = config["test_repository_path"]
    if not path:
        errors.append("Не задан путь к тестовому графу")
    elif not (PROJECT_ROOT / path).is_file():
        errors.append("Файл тестового графа не найден")


def _validate_output(config, errors):
    filename = config["output_file"]
    if filename and Path(filename).suffix.lower() != ".svg":
        errors.append("Выходной файл должен иметь расширение .svg")


def _validate_depth(config, errors):
    try:
        depth = int(config["max_depth"])
    except ValueError:
        errors.append("Максимальная глубина должна быть целым числом")
        return
    if depth < MIN_DEPTH:
        errors.append("Максимальная глубина не может быть отрицательной")


def print_graph(graph):
    print("\nГраф зависимостей:")
    for package, dependencies in graph.items():
        output = ", ".join(dependencies) or "нет зависимостей"
        print(f"{package} -> {output}")


def print_reverse_dependencies(graph, package_name):
    dependencies = find_reverse_dependencies(graph, package_name)
    print(f"\nОбратные зависимости: {package_name}")
    if not dependencies:
        print("Обратные зависимости не найдены")
        return
    for dependency in dependencies:
        print(f"- {dependency}")


def run_application(config):
    graph = build_graph(
        package_name=config["package_name"],
        package_version=config["package_version"],
        repository_url=config["repository_url"],
        max_depth=int(config["max_depth"]),
        filter_substring=config["filter_substring"],
        test_mode=config["test_mode"].lower() == "true",
        test_repository_path=str(
            PROJECT_ROOT / config["test_repository_path"]
        ),
    )
    print_graph(graph)
    print_reverse_dependencies(graph, config["package_name"])
    output_path = PROJECT_ROOT / config["output_file"]
    mermaid_file, svg_file = save_graph_visualization(graph, output_path)
    print("\nВизуализация графа:")
    print(f"Mermaid-файл: {mermaid_file}")
    print(f"SVG-файл: {svg_file}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=PROJECT_ROOT / "config.xml",
        help="путь к XML-конфигурации",
    )
    args = parser.parse_args(argv)
    try:
        config = load_config(args.config)
        print("Параметры конфигурации:")
        for key, value in config.items():
            print(f"{key}: {value}")
        errors = validate_config(config)
        if errors:
            print("\nОбнаружены ошибки:")
            for error in errors:
                print(f"- {error}")
            return 1
        run_application(config)
    except (ValueError, OSError) as error:
        print(f"\nОшибка: {error}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())