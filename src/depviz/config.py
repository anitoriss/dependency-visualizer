"""Настройки инструмента: разбор и проверка опций командной строки."""

import argparse
import re
from dataclasses import dataclass, fields
from pathlib import Path
from urllib.parse import urlparse

DEFAULT_REPO = "https://pypi.org/pypi"
DEFAULT_OUTPUT = "graph.svg"
LATEST = "latest"
IMAGE_SUFFIX = ".svg"
URL_SCHEMES = ("http", "https")
PIP_NAME = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9._-]*[A-Za-z0-9])?$")
TEST_NAME = re.compile(r"^[A-Z]+$")
VERSION = re.compile(r"^[0-9][0-9A-Za-z.+!-]*$")


class ConfigError(Exception):
    """Ошибка в значении параметра командной строки."""


@dataclass(frozen=True)
class Config:
    """Параметры, настраиваемые пользователем."""

    package: str
    repo: str
    test_mode: bool
    version: str
    output: str
    ascii_tree: bool
    filter_substring: str

    def describe(self) -> list[str]:
        """Вернуть все параметры в формате ключ=значение."""
        return [f"{f.name}={getattr(self, f.name)}" for f in fields(self)]


def build_parser() -> argparse.ArgumentParser:
    """Создать разборщик опций командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Визуализация графа зависимостей пакетов Python (pip).",
    )
    parser.add_argument("-p", "--package", required=True, metavar="NAME",
                        help="имя анализируемого пакета")
    parser.add_argument("-r", "--repo", metavar="URL|PATH",
                        help="URL репозитория (по умолчанию "
                             f"{DEFAULT_REPO}) или путь к файлу "
                             "тестового репозитория")
    parser.add_argument("-t", "--test-mode", action="store_true",
                        help="режим работы с тестовым репозиторием")
    parser.add_argument("-v", "--version", default=LATEST,
                        help="версия пакета (по умолчанию последняя)")
    parser.add_argument("-o", "--output", default=DEFAULT_OUTPUT,
                        metavar="FILE",
                        help="имя файла с изображением графа (.svg)")
    parser.add_argument("-a", "--ascii-tree", action="store_true",
                        help="вывести зависимости в виде ASCII-дерева")
    parser.add_argument("-f", "--filter", metavar="TEXT",
                        help="не учитывать пакеты, имя которых "
                             "содержит эту подстроку")
    return parser


def parse_args(argv: list[str] | None = None) -> Config:
    """Разобрать опции и проверить значения; ошибка - ConfigError."""
    args = build_parser().parse_args(argv)
    test_mode = args.test_mode
    return Config(
        package=check_package(args.package, test_mode),
        repo=check_repo(args.repo, test_mode),
        test_mode=test_mode,
        version=check_version(args.version, test_mode),
        output=check_output(args.output),
        ascii_tree=args.ascii_tree,
        filter_substring=check_filter(args.filter),
    )


def check_package(name: str, test_mode: bool) -> str:
    """Проверить имя пакета (в тестовом режиме - большие буквы)."""
    name = name.strip()
    if not name:
        raise ConfigError("имя пакета не может быть пустым")
    if test_mode and not TEST_NAME.match(name):
        raise ConfigError(f"недопустимое имя пакета '{name}': в тестовом "
                          "режиме разрешены только большие латинские буквы")
    if not test_mode and not PIP_NAME.match(name):
        raise ConfigError(f"недопустимое имя пакета '{name}': разрешены "
                          "латинские буквы, цифры, '.', '_' и '-'")
    return name


def check_repo(repo: str | None, test_mode: bool) -> str:
    """Проверить URL репозитория или путь к тестовому файлу."""
    if test_mode:
        return check_test_file(repo)
    url = DEFAULT_REPO if repo is None else repo.strip()
    parts = urlparse(url)
    if parts.scheme not in URL_SCHEMES or not parts.netloc:
        raise ConfigError(f"некорректный URL репозитория '{url}': "
                          "ожидается адрес вида https://...")
    return url.rstrip("/")


def check_test_file(path: str | None) -> str:
    """Проверить, что путь к файлу тестового репозитория существует."""
    if path is None:
        raise ConfigError("в тестовом режиме укажите путь к файлу "
                          "репозитория через --repo")
    if not Path(path).is_file():
        raise ConfigError(f"файл тестового репозитория '{path}' не найден")
    return path


def check_version(version: str, test_mode: bool) -> str:
    """Проверить версию пакета (в тестовом режиме версий нет)."""
    version = version.strip()
    if test_mode and version != LATEST:
        raise ConfigError("в тестовом режиме версия пакета не задаётся")
    if version != LATEST and not VERSION.match(version):
        raise ConfigError(f"некорректная версия пакета '{version}': "
                          "ожидается, например, 2.31.0")
    return version


def check_output(output: str) -> str:
    """Проверить имя файла изображения: расширение и директорию."""
    path = Path(output)
    if path.suffix.lower() != IMAGE_SUFFIX:
        raise ConfigError(f"файл изображения '{output}' должен иметь "
                          f"расширение {IMAGE_SUFFIX}")
    if not path.parent.is_dir():
        raise ConfigError(f"директория '{path.parent}' для файла "
                          "изображения не существует")
    return output


def check_filter(text: str | None) -> str:
    """Проверить подстроку фильтра; без опции фильтр не применяется."""
    if text is None:
        return ""
    if not text.strip():
        raise ConfigError("подстрока фильтра не может быть пустой")
    if any(char.isspace() for char in text):
        raise ConfigError("подстрока фильтра не должна содержать пробелы")
    return text
