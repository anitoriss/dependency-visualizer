"""Тесты тестового репозитория, описанного в файле."""

from pathlib import Path

import pytest

from depviz.repository import RepositoryError
from depviz.testrepo import FileRepository, parse_test_repo

EXAMPLES = Path(__file__).parent.parent / "examples" / "repos"


def test_parse_with_comments_and_blank_lines():
    """Комментарии и пустые строки пропускаются."""
    text = "# граф\n\nA: B C  # A зависит от B и C\nB:\nC: B\n"
    assert parse_test_repo(text) == {"A": ["B", "C"], "B": [], "C": ["B"]}


def test_duplicate_dependency_is_listed_once():
    """Повтор зависимости в строке не создаёт двух рёбер."""
    assert parse_test_repo("A: B B\nB:\n")["A"] == ["B"]


@pytest.mark.parametrize("text, message", [
    ("A B\n", "ожидается 'ПАКЕТ: ЗАВИСИМОСТИ'"),
    ("a: B\nB:\n", "недопустимое имя пакета 'a'"),
    ("A: B1\n", "недопустимое имя пакета 'B1'"),
    ("A:\nA: B\nB:\n", "строка 2: пакет 'A' уже описан"),
    ("A: B X\nB:\n", "зависимость 'X' пакета 'A' не описана"),
])
def test_invalid_description(text, message):
    """Ошибки в описании репозитория сообщают номер строки или пакет."""
    with pytest.raises(RepositoryError, match=message):
        parse_test_repo(text)


def test_dependencies_of_package():
    """Репозиторий возвращает прямые зависимости пакета."""
    repo = FileRepository({"A": ["B"], "B": []})
    assert repo.dependencies("A") == ["B"]


def test_unknown_package():
    """Неизвестный пакет - ошибка репозитория."""
    with pytest.raises(RepositoryError, match="не найден"):
        FileRepository({"A": []}).dependencies("Q")


def test_load_example_files():
    """Все корректные примеры из examples/repos загружаются."""
    for name in ("simple", "diamond", "cycle", "self_cycle", "complex"):
        repo = FileRepository.load(str(EXAMPLES / f"{name}.txt"))
        assert repo.packages


def test_load_missing_file(tmp_path):
    """Нечитаемый файл - ошибка репозитория."""
    with pytest.raises(RepositoryError, match="не удалось прочитать"):
        FileRepository.load(str(tmp_path / "nope.txt"))
