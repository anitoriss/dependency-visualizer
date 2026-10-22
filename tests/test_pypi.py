"""Тесты получения зависимостей из репозитория формата PyPI."""

import pytest

from builders import make_sdist, make_wheel, metadata, release
from depviz.pypi import PypiRepository, choose_file
from depviz.repository import RepositoryError

BASE = "https://repo.example/pypi"
WHEEL = "bdist_wheel"
SDIST = "sdist"


class FakeFetch:
    """Подмена загрузки: запоминает адреса и отдаёт заготовки."""

    def __init__(self, data):
        """Запомнить данные, которые будут возвращаться."""
        self.data = data
        self.urls = []

    def __call__(self, url):
        """Вернуть заготовленные данные или выбросить исключение."""
        self.urls.append(url)
        if isinstance(self.data, Exception):
            raise self.data
        return self.data


def file_entry(filename, kind, size=1):
    """Описание файла версии в ответе PyPI."""
    return {"filename": filename, "packagetype": kind, "url": filename,
            "size": size}


def test_url_for_latest_and_given_version():
    """Для последней версии номер в адрес не добавляется."""
    repo = PypiRepository(BASE + "/")
    assert repo.url("requests") == f"{BASE}/requests/json"
    assert repo.url("requests", "2.31.0") == f"{BASE}/requests/2.31.0/json"


def test_choose_pure_wheel_first():
    """Сначала - wheel без привязки к платформе."""
    files = [file_entry("x-1.0.tar.gz", SDIST),
             file_entry("x-1.0-cp312-cp312-win_amd64.whl", WHEEL),
             file_entry("x-1.0-py3-none-any.whl", WHEEL, size=99)]
    assert choose_file(files)["filename"] == "x-1.0-py3-none-any.whl"


def test_choose_smallest_platform_wheel_then_sdist():
    """Иначе - самый маленький wheel, а без wheel - sdist."""
    files = [file_entry("x-1.0-cp312-win.whl", WHEEL, size=50),
             file_entry("x-1.0-cp312-linux.whl", WHEEL, size=10),
             file_entry("x-1.0.tar.gz", SDIST)]
    assert choose_file(files)["filename"] == "x-1.0-cp312-linux.whl"
    assert choose_file(files[2:])["filename"] == "x-1.0.tar.gz"


def test_no_files_is_error():
    """Версия без файлов - ошибка."""
    with pytest.raises(RepositoryError, match="нет файлов"):
        choose_file([{"filename": "x.egg", "packagetype": "bdist_egg"}])


def test_package_downloads_and_unpacks_wheel():
    """Зависимости читаются из скачанного wheel, а не из JSON."""
    fetch = FakeFetch(release("demo", [("demo-1.0-py3-none-any.whl",
                                        WHEEL)]))
    download = FakeFetch(make_wheel("demo", ["idna>=2",
                                             "pysocks; extra == 'socks'"]))
    info = PypiRepository(BASE, fetch, download).package("demo", "1.0")
    assert fetch.urls == [f"{BASE}/demo/1.0/json"]
    assert download.urls == ["demo-1.0-py3-none-any.whl"]
    assert info.source == "demo-1.0-py3-none-any.whl"
    assert [r.name for r in info.required()] == ["idna"]
    assert [r.name for r in info.optional()] == ["pysocks"]


def test_package_from_sdist():
    """Если wheel нет - скачивается и распаковывается sdist."""
    fetch = FakeFetch(release("demo", [("demo-1.0.tar.gz", SDIST)]))
    download = FakeFetch(make_sdist("demo", {
        "PKG-INFO": metadata("demo", ["six"])}))
    info = PypiRepository(BASE, fetch, download).package("demo")
    assert [r.name for r in info.required()] == ["six"]


def test_response_without_files_is_error():
    """Ответ без описания пакета или списка файлов - ошибка."""
    repo = PypiRepository(BASE, FakeFetch({"info": {"name": "x"}}))
    with pytest.raises(RepositoryError, match="нет описания"):
        repo.package("x")


def test_fetch_errors_are_passed_on():
    """Ошибки загрузки передаются вызывающему коду."""
    error = RepositoryError("не найдено в репозитории")
    repo = PypiRepository(BASE, FakeFetch(error))
    with pytest.raises(RepositoryError, match="не найдено"):
        repo.package("x", "1.0")
