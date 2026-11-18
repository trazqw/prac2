import json
import re
from .dependency_service import (
    get_direct_dependencies,
    get_latest_version,
)

MIN_DEPTH = 0
PACKAGE_PATTERN = re.compile(r"[A-Z]+")
NORMAL_DEPENDENCY = "normal"


def load_test_graph(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            graph = json.load(file)
    except FileNotFoundError as error:
        message = "Файл тестового графа не найден"
        raise ValueError(message) from error
    except json.JSONDecodeError as error:
        message = "Некорректный формат JSON"
        raise ValueError(message) from error

    if not isinstance(graph, dict):
        message = "Тестовый граф должен быть JSON-объектом"
        raise ValueError(message)
    for package, dependencies in graph.items():
        _validate_package(package)
        if not isinstance(dependencies, list):
            message = (
                f"Зависимости пакета {package} должны быть списком"
            )
            raise ValueError(message)
        for dependency in dependencies:
            _validate_package(dependency)
    return graph


def _validate_package(package):
    if not isinstance(package, str):
        message = f"Некорректное имя пакета: {package}"
        raise ValueError(message)
    if PACKAGE_PATTERN.fullmatch(package) is None:
        message = f"Некорректное имя пакета: {package}"
        raise ValueError(message)


def _dependency_loader(args):
    if args["test_mode"]:
        graph = load_test_graph(args["test_path"])
        if args["package"] not in graph:
            message = (
                f"Пакет {args['package']} отсутствует в тестовом графе"
            )
            raise ValueError(message)
        return lambda package: graph.get(package, [])
    return _create_api_loader(args)


def _create_api_loader(args):
    versions = {args["package"]: args["version"]}

    def get_dependencies(package):
        if package not in versions:
            versions[package] = get_latest_version(args["url"], package)
        items = get_direct_dependencies(
            args["url"], package, versions[package]
        )
        names = [
            item["crate_id"] for item in items
            if item.get("kind") in (None, NORMAL_DEPENDENCY)
            and isinstance(item.get("crate_id"), str)
        ]
        return list(dict.fromkeys(names))

    return get_dependencies


def _filter_dependencies(dependencies, filter_substring):
    if not filter_substring:
        return dependencies
    return [
        item for item in dependencies
        if filter_substring not in item
    ]


def _bfs_graph(package, max_depth, filter_substring, loader):
    graph = {}
    visited = {package}

    def visit_level(level, depth):
        if not level:
            return
        next_level = []
        for current in level:
            if depth >= max_depth:
                graph[current] = []
                continue
            dependencies = _filter_dependencies(
                loader(current), filter_substring
            )
            graph[current] = dependencies
            _enqueue_new_dependencies(dependencies, visited, next_level)
        visit_level(next_level, depth + 1)

    visit_level([package], 0)
    return graph


def _enqueue_new_dependencies(dependencies, visited, queue):
    for dependency in dependencies:
        if dependency not in visited:
            visited.add(dependency)
            queue.append(dependency)


def build_graph(
    package_name,
    package_version,
    repository_url,
    max_depth,
    filter_substring,
    test_mode,
    test_repository_path,
):
    if max_depth < MIN_DEPTH:
        message = "Глубина анализа не может быть отрицательной"
        raise ValueError(message)
    args = {
        "package": package_name,
        "version": package_version,
        "url": repository_url,
        "test_mode": test_mode,
        "test_path": test_repository_path,
    }
    loader = _dependency_loader(args)
    return _bfs_graph(
        package_name, max_depth, filter_substring, loader
    )


def _reverse_graph(graph):
    reverse = {package: [] for package in graph}
    for package, dependencies in graph.items():
        for dependency in dependencies:
            reverse.setdefault(dependency, []).append(package)
    return reverse


def find_reverse_dependencies(graph, package_name):
    reverse = _reverse_graph(graph)
    if package_name not in reverse:
        message = f"Пакет {package_name} отсутствует в графе"
        raise ValueError(message)
    result = []
    visited = {package_name}

    def visit_level(level):
        if not level:
            return
        next_level = []
        for current in level:
            for dependent in reverse[current]:
                if dependent not in visited:
                    visited.add(dependent)
                    result.append(dependent)
                    next_level.append(dependent)
        visit_level(next_level)

    visit_level([package_name])
    return result