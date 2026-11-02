import xml.etree.ElementTree as ET
import os
from graph_service import build_graph

REQUIRED_PARAMETERS = [
    "package_name", "repository_url", "test_repository_path", "test_mode",
    "package_version", "output_file", "max_depth", "filter_substring"
]

def load_config():
    try:
        tree = ET.parse("config.xml")
        root = tree.getroot()
        if root.tag != "configuration":
            raise ValueError("Неверный корневой элемент XML")
        config = {}
        for parameter in REQUIRED_PARAMETERS:
            element = root.find(parameter)
            if element is None:
                raise ValueError(f"Отсутствует параметр: {parameter}")
            config[parameter] = (element.text or "").strip()
        return config
    except ET.ParseError:
        raise ValueError("Ошибка формата XML-файла")
    except FileNotFoundError:
        raise ValueError("Файл config.xml не найден")

def validate_config(config):
    errors = []
    if not config["package_name"]:
        errors.append("Не задано имя пакета")
    if not config["repository_url"].startswith(("http://", "https://")):
        errors.append("Некорректный URL репозитория")
    if config["test_mode"].lower() not in ("true", "false"):
        errors.append("test_mode должен иметь значение true или false")
    if config["test_mode"].lower() == "true":
        if not config["test_repository_path"]:
            errors.append("Не задан путь к тестовому репозиторию")
        elif not os.path.isfile(config["test_repository_path"]):
            errors.append("Файл тестового репозитория не найден")
    if not config["package_version"]:
        errors.append("Не задана версия пакета")
    if not config["output_file"]:
        errors.append("Не задано имя выходного файла")
    try:
        depth = int(config["max_depth"])
        if depth < 0:
            errors.append("Максимальная глубина не может быть отрицательной")
    except ValueError:
        errors.append("Максимальная глубина должна быть целым числом")
    return errors

def main():
    try:
        config = load_config()
        errors = validate_config(config)
        print("Параметры конфигурации:")
        for key, value in config.items():
            print(f"{key}: {value}")
        if errors:
            print("\nОбнаружены ошибки:")
            for error in errors:
                print(f"- {error}")
            return
        graph = build_graph(
            package_name=config["package_name"],
            package_version=config["package_version"],
            repository_url=config["repository_url"],
            max_depth=int(config["max_depth"]),
            filter_substring=config["filter_substring"],
            test_mode=config["test_mode"].lower() == "true",
            test_repository_path=config["test_repository_path"]
        )
        print("\nГраф зависимостей:")
        for package, dependencies in graph.items():
            if dependencies:
                print(f"{package} -> {', '.join(dependencies)}")
            else:
                print(f"{package} -> нет зависимостей")
    except ValueError as error:
        print(f"\nОшибка: {error}")

if __name__ == "__main__":
    main()