"""Точка входа: python -m depviz [параметры]."""

import sys

from depviz.config import ConfigError, parse_args

EXIT_OK = 0
EXIT_USAGE = 2


def main(argv: list[str] | None = None) -> int:
    """Запустить инструмент и вернуть код завершения."""
    try:
        config = parse_args(argv)
    except ConfigError as error:
        print(f"depviz: ошибка: {error}", file=sys.stderr)
        return EXIT_USAGE
    for line in config.describe():
        print(line)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
