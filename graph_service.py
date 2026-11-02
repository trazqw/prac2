import json
import re
from dependency_service import get_direct_dependencies, get_latest_version

def load_test_graph(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            graph = json.load(file)
    except FileNotFoundError:
        raise ValueError("Файл тестового графа не найден")
    except json.JSONDecodeError:
        raise ValueError("Некорректный формат JSON")
    if not isinstance(graph, dict):
        raise ValueError("Тестовый граф должен быть JSON-объектом")
    for package, dependencies in graph.items():
        if not isinstance(package, str) or not re.fullmatch(r"[A-Z]+", package):
            raise ValueError(f"Некорректное имя пакета: {package}")
        if not isinstance(dependencies, list):
            raise ValueError(f"Зависимости пакета {package} должны быть списком")
        for dependency in dependencies:
            if (not isinstance(dependency, str)
                    or not re.fullmatch(r"[A-Z]+", dependency)):
                raise ValueError(f"Некорректное имя зависимости: {dependency}")
    return graph

def build_graph(package_name, package_version, repository_url, max_depth,
                filter_substring, test_mode, test_repository_path):
    if max_depth < 0:
        raise ValueError("Глубина анализа не может быть отрицательной")

    if test_mode:
        source_graph = load_test_graph(test_repository_path)
        if package_name not in source_graph:
            raise ValueError(f"Пакет {package_name} отсутствует в тестовом графе")
        def get_dependencies(package):
            return source_graph.get(package, [])
    else:
        version_cache = {package_name: package_version}
        def get_dependencies(package):
            if package not in version_cache:
                version_cache[package] = get_latest_version(repository_url, package)
            dependencies = get_direct_dependencies(
                repository_url, package, version_cache[package]
            )
            normal = [
                item["crate_id"] for item in dependencies
                if item.get("kind") in (None, "normal")
            ]
            return list(dict.fromkeys(normal))

    result = {}
    visited = {package_name}
    queue = [(package_name, 0)]

    def bfs():
        if not queue:
            return
        current_package, depth = queue.pop(0)
        if depth >= max_depth:
            result[current_package] = []
            bfs()
            return
        dependencies = get_dependencies(current_package)
        if filter_substring:
            dependencies = [
                dep for dep in dependencies if filter_substring not in dep
            ]
        result[current_package] = dependencies
        for dependency in dependencies:
            if dependency not in visited:
                visited.add(dependency)
                queue.append((dependency, depth + 1))
        bfs()

    bfs()
    return result