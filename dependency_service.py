import json
import urllib.request
import urllib.error
from urllib.parse import quote

def get_direct_dependencies(repository_url, package_name, package_version):
    package = quote(package_name, safe="")
    version = quote(package_version, safe="")
    url = (f"{repository_url.rstrip('/')}/crates/"
           f"{package}/{version}/dependencies")
    request = urllib.request.Request(
        url, headers={"User-Agent": "cargo-dependency-visualizer/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        dependencies = data.get("dependencies")
        if not isinstance(dependencies, list):
            raise ValueError("Некорректный формат ответа API")
        return dependencies
    except urllib.error.HTTPError as error:
        raise ValueError(
            f"Ошибка API: HTTP {error.code}. Проверьте имя пакета и его версию."
        )
    except urllib.error.URLError as error:
        raise ValueError(f"Не удалось подключиться к репозиторию: {error.reason}")
    except json.JSONDecodeError:
        raise ValueError("Сервер вернул некорректный JSON")

def get_latest_version(repository_url, package_name):
    package = quote(package_name, safe="")
    url = f"{repository_url.rstrip('/')}/crates/{package}"
    request = urllib.request.Request(
        url, headers={"User-Agent": "cargo-dependency-visualizer/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data["crate"]["max_version"]
    except (urllib.error.URLError, urllib.error.HTTPError) as error:
        raise ValueError(
            f"Не удалось получить версию пакета {package_name}: {error}"
        )
    except (KeyError, json.JSONDecodeError):
        raise ValueError(
            f"Некорректный ответ API для пакета {package_name}"
        )
