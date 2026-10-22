"""Тесты распаковки файлов пакета."""

import io
import zipfile

import pytest

from builders import make_sdist, make_wheel, metadata
from depviz.archive import read_requirements
from depviz.repository import RepositoryError


def test_wheel_metadata():
    """Из wheel читается dist-info/METADATA."""
    data = make_wheel("demo", ["idna>=2", "certifi"])
    assert read_requirements("demo-1.0-py3-none-any.whl", data) == \
        ["idna>=2", "certifi"]


def test_wheel_without_metadata():
    """Wheel без METADATA - ошибка."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("demo/__init__.py", "")
    with pytest.raises(RepositoryError, match="нет файла METADATA"):
        read_requirements("demo-1.0-py3-none-any.whl", buffer.getvalue())


def test_sdist_pkg_info():
    """Из sdist читается PKG-INFO, если в нём есть зависимости."""
    data = make_sdist("demo", {"PKG-INFO": metadata("demo", ["six"])})
    assert read_requirements("demo-1.0.tar.gz", data) == ["six"]


def test_sdist_requires_txt_fallback():
    """Старые sdist: зависимости в egg-info/requires.txt."""
    data = make_sdist("demo", {
        "PKG-INFO": metadata("demo", []),
        "demo.egg-info/requires.txt": "Jinja2>=2.4\n[extra]\nfoo\n",
    })
    assert read_requirements("demo-1.0.tar.gz", data) == \
        ["Jinja2>=2.4", 'foo; extra == "extra"']


def test_sdist_requires_txt_in_src_layout():
    """requires.txt может лежать в src/<пакет>.egg-info."""
    data = make_sdist("demo", {"src/demo.egg-info/requires.txt": "six\n"})
    assert read_requirements("demo-1.0.tar.gz", data) == ["six"]


def test_sdist_without_metadata_has_no_dependencies():
    """Если в sdist нет сведений о зависимостях - список пуст."""
    data = make_sdist("demo", {"setup.py": "print()"})
    assert read_requirements("demo-1.0.tar.gz", data) == []


def test_unknown_format():
    """Неизвестное расширение файла - ошибка."""
    with pytest.raises(RepositoryError, match="неизвестный формат"):
        read_requirements("demo-1.0.exe", b"MZ")


def test_broken_archive():
    """Повреждённый архив - ошибка."""
    with pytest.raises(RepositoryError, match="не удалось распаковать"):
        read_requirements("demo-1.0-py3-none-any.whl", b"not a zip")
