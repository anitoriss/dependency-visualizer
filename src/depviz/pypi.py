"""Получение зависимостей пакета из репозитория формата PyPI.

1. По JSON API репозитория (``<repo>/<пакет>/<версия>/json`` или
   ``<repo>/<пакет>/json`` для последней версии) узнаём список файлов
   версии. Готовый список зависимостей из ответа не используется.
2. Скачиваем файл пакета: wheel без привязки к платформе, иначе любой
   wheel, иначе архив исходников (sdist).
3. Сами распаковываем архив и читаем зависимости из метаданных
   (см. модуль archive).
"""

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from depviz.archive import read_requirements
from depviz.config import LATEST
from depviz.repository import RepositoryError
from depviz.requirements import Requirement, parse_requirement

TIMEOUT_SECONDS = 60
NOT_FOUND = 404
USER_AGENT = "depviz/1.0 (educational project)"
WHEEL_TYPE = "bdist_wheel"
SDIST_TYPE = "sdist"
PURE_WHEEL = "-none-any.whl"


def http_get(url: str) -> bytes:
    """Скачать содержимое по адресу url."""
    request = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            return response.read()
    except HTTPError as error:
        if error.code == NOT_FOUND:
            raise RepositoryError(f"не найдено в репозитории: {url}") \
                from error
        raise RepositoryError(f"ошибка HTTP {error.code}: {url}") from error
    except (URLError, OSError) as error:
        reason = getattr(error, "reason", error)
        raise RepositoryError("не удалось подключиться к репозиторию: "
                              f"{reason}") from error


def fetch_json(url: str) -> dict:
    """Скачать и разобрать JSON по адресу url."""
    try:
        return json.loads(http_get(url))
    except ValueError as error:
        raise RepositoryError(f"некорректный ответ репозитория: {url}") \
            from error


def is_downloadable(file) -> bool:
    """Проверить, что у описания файла есть адрес и имя."""
    if not isinstance(file, dict):
        return False
    return bool(file.get("url")) and bool(file.get("filename"))


def file_size(file: dict) -> int:
    """Размер файла в байтах (0, если размер неизвестен)."""
    return file.get("size") or 0


def file_groups(files: list) -> tuple[list, list, list]:
    """Разбить файлы на группы в порядке предпочтения.

    Сначала wheel без привязки к платформе, затем любые wheel,
    затем архивы исходников (sdist).
    """
    files = list(filter(is_downloadable, files))
    wheels = [f for f in files if f.get("packagetype") == WHEEL_TYPE]
    pure = [f for f in wheels if f["filename"].endswith(PURE_WHEEL)]
    sdists = [f for f in files if f.get("packagetype") == SDIST_TYPE]
    return pure, wheels, sdists


def choose_file(files: list) -> dict:
    """Выбрать файл версии для скачивания (по возможности маленький)."""
    for group in file_groups(files):
        if group:
            return min(group, key=file_size)
    raise RepositoryError("у версии пакета нет файлов для скачивания")


@dataclass(frozen=True)
class PackageInfo:
    """Версия пакета, скачанный файл и зависимости из него."""

    name: str
    version: str
    source: str
    requirements: tuple[Requirement, ...]

    def required(self) -> list[Requirement]:
        """Обязательные зависимости (без доп. возможностей extra)."""
        return [req for req in self.requirements if not req.optional]

    def optional(self) -> list[Requirement]:
        """Зависимости, нужные только для доп. возможностей (extra)."""
        return [req for req in self.requirements if req.optional]


class PypiRepository:
    """Репозиторий пакетов с JSON API в формате PyPI."""

    def __init__(self, base_url: str, fetch=fetch_json, download=http_get):
        """Запомнить адрес репозитория и функции загрузки."""
        self.base_url = base_url.rstrip("/")
        self._fetch = fetch
        self._download = download

    def url(self, name: str, version: str = LATEST) -> str:
        """Вернуть адрес JSON-описания пакета (или его версии)."""
        if version == LATEST:
            return f"{self.base_url}/{name}/json"
        return f"{self.base_url}/{name}/{version}/json"

    def package(self, name: str, version: str = LATEST) -> PackageInfo:
        """Скачать файл пакета заданной версии и прочитать зависимости."""
        data = self._fetch(self.url(name, version))
        info = data.get("info") if isinstance(data, dict) else None
        files = data.get("urls") if isinstance(data, dict) else None
        if not isinstance(info, dict) or not isinstance(files, list):
            raise RepositoryError(f"в ответе нет описания пакета '{name}'")
        chosen = choose_file(files)
        archive = self._download(chosen["url"])
        raw = read_requirements(chosen["filename"], archive)
        return PackageInfo(info.get("name", name),
                           info.get("version", version), chosen["filename"],
                           tuple(parse_requirement(item) for item in raw))
