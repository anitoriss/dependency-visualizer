"""Точка входа: python -m depviz [параметры]."""

import sys

from depviz.config import LATEST, Config, ConfigError, parse_args
from depviz.graph import build_graph
from depviz.pypi import PypiRepository
from depviz.report import format_graph
from depviz.repository import RepositoryError
from depviz.requirements import normalize_name
from depviz.testrepo import FileRepository

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def open_repository(config: Config):
    """Открыть тестовый репозиторий или репозиторий PyPI."""
    if config.test_mode:
        return FileRepository.load(config.repo)
    return PypiRepository(config.repo)


def describe_root(config: Config, root: str) -> str:
    """Вернуть подпись анализируемого пакета для отчёта."""
    if config.test_mode:
        return f"пакета {root} (тестовый репозиторий {config.repo})"
    version = "последняя версия" if config.version == LATEST \
        else f"версия {config.version}"
    return f"пакета {root} ({version})"


def run(config: Config) -> list[str]:
    """Построить граф зависимостей и вернуть строки отчёта.

    Для анализируемого пакета берётся заданная версия, для остальных
    пакетов графа - последняя.
    """
    repository = open_repository(config)
    root = config.package if config.test_mode \
        else normalize_name(config.package)

    def dependencies(name: str) -> list[str]:
        """Прямые зависимости пакета нужной версии."""
        version = config.version if name == root else LATEST
        return repository.dependencies(name, version)

    graph = build_graph(root, dependencies, config.filter_substring)
    return format_graph(graph, describe_root(config, root),
                        config.filter_substring)


def main(argv: list[str] | None = None) -> int:
    """Запустить инструмент и вернуть код завершения."""
    try:
        config = parse_args(argv)
    except ConfigError as error:
        print(f"depviz: ошибка: {error}", file=sys.stderr)
        return EXIT_USAGE
    try:
        lines = run(config)
    except RepositoryError as error:
        print(f"depviz: ошибка: {error}", file=sys.stderr)
        return EXIT_ERROR
    for line in lines:
        print(line)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
