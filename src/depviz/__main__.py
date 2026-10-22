"""Точка входа: python -m depviz [параметры]."""

import sys

from depviz.config import Config, ConfigError, parse_args
from depviz.pypi import PackageInfo, PypiRepository
from depviz.repository import RepositoryError

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2


def format_direct(info: PackageInfo) -> list[str]:
    """Вернуть строки с прямыми зависимостями пакета."""
    required = info.required()
    lines = [f"{info.name} {info.version} (файл {info.source})",
             f"Прямые зависимости ({len(required)}):"]
    lines += [f"  {req}" for req in required] or ["  (нет)"]
    optional = info.optional()
    if optional:
        names = ", ".join(req.name for req in optional)
        lines.append(f"Не учитываются необязательные (extra): {names}")
    return lines


def run(config: Config) -> list[str]:
    """Выполнить анализ и вернуть строки для вывода."""
    if config.test_mode:
        raise RepositoryError("тестовый режим пока не поддерживается")
    repository = PypiRepository(config.repo)
    return format_direct(repository.package(config.package, config.version))


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
