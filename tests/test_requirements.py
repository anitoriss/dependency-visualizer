"""Тесты разбора строк зависимостей pip."""

import pytest

from depviz.repository import RepositoryError
from depviz.requirements import normalize_name, parse_requirement


@pytest.mark.parametrize("raw, name", [
    ("Jinja2", "jinja2"),
    ("charset_normalizer", "charset-normalizer"),
    ("zope.interface", "zope-interface"),
    ("A__b--C", "a-b-c"),
])
def test_normalize_name(raw, name):
    """Имена сравниваются без учёта регистра и вида разделителей."""
    assert normalize_name(raw) == name


def test_name_only():
    """Зависимость без ограничений версии."""
    req = parse_requirement("certifi")
    assert (req.name, req.spec, req.marker) == ("certifi", "", "")
    assert not req.optional


def test_old_style_parentheses():
    """Старый формат PyPI: спецификатор в скобках."""
    req = parse_requirement("charset-normalizer (<4,>=2)")
    assert req.name == "charset-normalizer"
    assert req.spec == "<4,>=2"


def test_new_style_with_marker():
    """Условие установки отделяется точкой с запятой."""
    req = parse_requirement('importlib-metadata>=3.6.0; python_version < '
                            '"3.10"')
    assert req.name == "importlib-metadata"
    assert req.spec == ">=3.6.0"
    assert req.marker == 'python_version < "3.10"'
    assert not req.optional


def test_extra_marker_is_optional():
    """Зависимость для доп. возможности (extra) - необязательная."""
    req = parse_requirement("PySocks (!=1.5.7,>=1.5.6) ; extra == 'socks'")
    assert req.name == "pysocks"
    assert req.optional


def test_extras_of_dependency_are_dropped():
    """Доп. возможности самой зависимости не входят в спецификатор."""
    req = parse_requirement("requests[security,socks]>=2.0")
    assert req.name == "requests"
    assert req.spec == ">=2.0"


def test_str_shows_spec_and_marker():
    """Строковое представление содержит всё, что известно."""
    req = parse_requirement("idna>=2; python_version >= '3'")
    assert str(req) == "idna >=2 ; python_version >= '3'"


def test_garbage_is_error():
    """Строка без имени пакета - ошибка репозитория."""
    with pytest.raises(RepositoryError, match="не удалось разобрать"):
        parse_requirement(">=1.0")
