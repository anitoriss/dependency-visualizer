"""Тесты точки входа."""

from pathlib import Path

import pytest

import depviz.__main__ as entry
from builders import make_wheel, release
from depviz.__main__ import EXIT_ERROR, EXIT_OK, EXIT_USAGE, main
from depviz.pypi import PypiRepository
from depviz.repository import RepositoryError

EXAMPLES = Path(__file__).parent.parent / "examples" / "repos"
INDEX = {
    "flask/3.1.3": ["click>=8.1.3", "Jinja2>=3.1.2",
                    'asgiref>=3.2; extra == "async"'],
    "click": [],
    "jinja2": ["MarkupSafe>=2.0"],
    "markupsafe": [],
}


def fake_fetch(url):
    """JSON пакета из INDEX по адресу вида .../name[/version]/json."""
    key = url.split("/pypi/", 1)[1].removesuffix("/json")
    if key not in INDEX:
        raise RepositoryError(f"не найдено в репозитории: {url}")
    return release(key.split("/")[0], [(f"{key}.whl", "bdist_wheel")])


def fake_download(url):
    """Wheel пакета: адрес файла - ключ INDEX с суффиксом .whl."""
    key = url.removesuffix(".whl")
    return make_wheel(key.split("/")[0], INDEX[key])


@pytest.fixture
def fake_pypi(monkeypatch):
    """Подменить репозиторий: вместо сети - заготовленные архивы."""
    monkeypatch.setattr(entry, "PypiRepository", lambda url: PypiRepository(
        url, fetch=fake_fetch, download=fake_download))


def test_pypi_graph_uses_given_version_for_root(capsys, fake_pypi):
    """Корень - заданной версии, остальные пакеты - последней."""
    assert main(["-p", "Flask", "-v", "3.1.3"]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "Граф зависимостей пакета flask (версия 3.1.3): " \
                     "пакетов - 4"
    assert "flask -> click, jinja2" in out
    assert "jinja2 -> markupsafe" in out
    assert out[-1] == "Циклические зависимости: нет"


def test_filter_is_reported(capsys, fake_pypi):
    """Исключённые фильтром пакеты перечисляются в отчёте."""
    assert main(["-p", "flask", "-v", "3.1.3", "-f", "jinja"]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert "flask -> click" in out
    assert "Исключены фильтром 'jinja': jinja2" in out


def test_test_mode_reports_cycle(capsys):
    """Тестовый режим: граф из файла и найденный цикл."""
    repo = str(EXAMPLES / "cycle.txt")
    assert main(["-p", "A", "-t", "-r", repo]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert "C -> A, D" in out
    assert out[-1] == "Циклическая зависимость: A -> B -> C -> A"


def test_config_error_has_usage_code(capsys):
    """Ошибка параметра выводится в stderr, код завершения 2."""
    assert main(["-p", "requests", "-o", "x.png"]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("depviz: ошибка:")


def test_repository_error_has_error_code(capsys, fake_pypi):
    """Ошибка репозитория выводится в stderr, код завершения 1."""
    assert main(["-p", "nope"]) == EXIT_ERROR
    assert "не найдено" in capsys.readouterr().err


def test_broken_test_repository(capsys):
    """Ошибка в файле тестового репозитория - код завершения 1."""
    repo = str(EXAMPLES / "broken.txt")
    assert main(["-p", "A", "-t", "-r", repo]) == EXIT_ERROR
    assert "не описана" in capsys.readouterr().err
