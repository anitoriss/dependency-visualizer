"""Тесты точки входа."""

import pytest

import depviz.__main__ as entry
from builders import make_wheel, release
from depviz.__main__ import EXIT_ERROR, EXIT_OK, EXIT_USAGE, main
from depviz.pypi import PypiRepository
from depviz.repository import RepositoryError

WHEEL_NAME = "flask-3.1.3-py3-none-any.whl"


@pytest.fixture
def fake_pypi(monkeypatch):
    """Подменить репозиторий: вместо сети - заготовленные ответы."""
    wheel = make_wheel("flask", ["click>=8.1.3",
                                 'asgiref>=3.2; extra == "async"'])

    def make(url):
        """Репозиторий с подменёнными загрузками."""
        return PypiRepository(
            url, fetch=lambda _: release("Flask", [(WHEEL_NAME,
                                                    "bdist_wheel")]),
            download=lambda _: wheel)
    monkeypatch.setattr(entry, "PypiRepository", make)


def test_prints_direct_dependencies(capsys, fake_pypi):
    """Выводятся файл пакета и его прямые зависимости."""
    assert main(["-p", "flask", "-v", "1.0"]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[0] == f"Flask 1.0 (файл {WHEEL_NAME})"
    assert out[1:3] == ["Прямые зависимости (1):", "  click >=8.1.3"]
    assert out[-1] == "Не учитываются необязательные (extra): asgiref"


def test_config_error_has_usage_code(capsys):
    """Ошибка параметра выводится в stderr, код завершения 2."""
    assert main(["-p", "requests", "-o", "x.png"]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("depviz: ошибка:")


def test_repository_error_has_error_code(capsys, monkeypatch):
    """Ошибка репозитория выводится в stderr, код завершения 1."""
    def broken(url):
        """Загрузка, которая всегда завершается ошибкой."""
        raise RepositoryError("не найдено в репозитории: x")
    monkeypatch.setattr(entry, "PypiRepository",
                        lambda url: PypiRepository(url, fetch=broken))
    assert main(["-p", "nope"]) == EXIT_ERROR
    assert "не найдено" in capsys.readouterr().err
