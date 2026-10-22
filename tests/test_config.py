"""Тесты разбора и проверки параметров командной строки."""

import pytest

from depviz.__main__ import EXIT_USAGE
from depviz.config import (
    DEFAULT_OUTPUT, DEFAULT_REPO, LATEST, ConfigError, parse_args,
)


@pytest.fixture
def repo_file(tmp_path):
    """Вернуть путь к существующему файлу тестового репозитория."""
    path = tmp_path / "repo.txt"
    path.write_text("A: B\n", encoding="utf-8")
    return str(path)


def test_defaults():
    """Без необязательных опций используются значения по умолчанию."""
    config = parse_args(["--package", "requests"])
    assert config.package == "requests"
    assert config.repo == DEFAULT_REPO
    assert not config.test_mode
    assert config.version == LATEST
    assert config.output == DEFAULT_OUTPUT
    assert not config.ascii_tree
    assert config.filter_substring == ""


def test_all_parameters(tmp_path):
    """Все параметры задаются через длинные опции."""
    out = tmp_path / "g.svg"
    config = parse_args([
        "--package", "flask", "--repo", "https://example.org/pypi/",
        "--version", "3.0.0", "--output", str(out), "--ascii-tree",
        "--filter", "click",
    ])
    assert config.repo == "https://example.org/pypi"
    assert config.version == "3.0.0"
    assert config.output == str(out)
    assert config.ascii_tree
    assert config.filter_substring == "click"


def test_short_options(repo_file):
    """Короткие опции работают так же, как длинные."""
    config = parse_args(["-p", "A", "-t", "-r", repo_file, "-a", "-f", "X"])
    assert config.test_mode
    assert config.repo == repo_file
    assert config.ascii_tree
    assert config.filter_substring == "X"


def test_describe_lists_every_parameter():
    """describe выводит каждый параметр в формате ключ=значение."""
    lines = parse_args(["-p", "requests"]).describe()
    keys = [line.split("=", 1)[0] for line in lines]
    assert keys == ["package", "repo", "test_mode", "version", "output",
                    "ascii_tree", "filter_substring"]
    assert "package=requests" in lines


def test_package_is_required(capsys):
    """Без имени пакета программа завершается с кодом 2."""
    with pytest.raises(SystemExit) as error:
        parse_args([])
    assert error.value.code == EXIT_USAGE
    assert "--package" in capsys.readouterr().err


@pytest.mark.parametrize("argv, message", [
    (["-p", "  "], "не может быть пустым"),
    (["-p", "bad name!"], "недопустимое имя пакета"),
    (["-p", "requests-"], "недопустимое имя пакета"),
    (["-p", "requests", "-r", "ftp://host/x"], "некорректный URL"),
    (["-p", "requests", "-r", "pypi.org"], "некорректный URL"),
    (["-p", "requests", "-v", "abc"], "некорректная версия"),
    (["-p", "requests", "-v", ""], "некорректная версия"),
    (["-p", "requests", "-o", "graph.png"], "расширение .svg"),
    (["-p", "requests", "-o", "no/such/dir/g.svg"], "не существует"),
    (["-p", "requests", "-f", ""], "не может быть пустой"),
    (["-p", "requests", "-f", "a b"], "не должна содержать пробелы"),
])
def test_invalid_values(argv, message):
    """Для каждого неверного значения выдаётся понятная ошибка."""
    with pytest.raises(ConfigError, match=message):
        parse_args(argv)


def test_test_mode_requires_repo_path():
    """В тестовом режиме путь к файлу обязателен."""
    with pytest.raises(ConfigError, match="укажите путь"):
        parse_args(["-p", "A", "-t"])


def test_test_mode_missing_file(tmp_path):
    """Несуществующий файл тестового репозитория - ошибка."""
    with pytest.raises(ConfigError, match="не найден"):
        parse_args(["-p", "A", "-t", "-r", str(tmp_path / "nope.txt")])


def test_test_mode_package_must_be_capital_letters(repo_file):
    """В тестовом режиме пакеты называются большими латинскими буквами."""
    with pytest.raises(ConfigError, match="большие латинские буквы"):
        parse_args(["-p", "requests", "-t", "-r", repo_file])


def test_test_mode_rejects_version(repo_file):
    """В тестовом репозитории нет версий пакетов."""
    with pytest.raises(ConfigError, match="версия пакета не задаётся"):
        parse_args(["-p", "A", "-t", "-r", repo_file, "-v", "1.0"])
