import json
import urllib.error
import urllib.request
from urllib.parse import quote


USER_AGENT = "cargo-dependency-visualizer/1.0"
REQUEST_TIMEOUT_SECONDS = 20


def _get_json(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urllib.request.urlopen(
            request, timeout=REQUEST_TIMEOUT_SECONDS
        ) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise ValueError(
            "Ошибка API: HTTP "
            f"{error.code}. Проверьте имя пакета и версию."
        ) from error
    except urllib.error.URLError as error:
        raise ValueError(
            f"Не удалось подключиться к репозиторию: {error.reason}"
        ) from error
    except json.JSONDecodeError as error:
        raise ValueError("Сервер вернул некорректный JSON") from error


def get_direct_dependencies(repository_url, package_name, package_version):
    package = quote(package_name, safe="")
    version = quote(package_version, safe="")
    url = (
        f"{repository_url.rstrip('/')}/crates/"
        f"{package}/{version}/dependencies"
    )

    data = _get_json(url)
    dependencies = data.get("dependencies")

    if not isinstance(dependencies, list):
        raise ValueError(
            "Некорректный формат ответа API: нет списка dependencies"
        )

    return dependencies


def get_latest_version(repository_url, package_name):
    package = quote(package_name, safe="")
    url = f"{repository_url.rstrip('/')}/crates/{package}"

    data = _get_json(url)

    try:
        return data["crate"]["max_version"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            f"Некорректный ответ API для пакета {package_name}"
        ) from error
