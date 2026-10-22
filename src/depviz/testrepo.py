"""Тестовый репозиторий: граф пакетов, описанный в текстовом файле.

Формат файла - по одному пакету в строке::

    # комментарий
    A: B C      # пакет A зависит от B и C
    B: C
    C:          # у C нет зависимостей

Пакеты называются большими латинскими буквами. Каждый пакет, на
который есть ссылка, должен быть описан своей строкой.
"""

from pathlib import Path

from depviz.config import LATEST, TEST_NAME
from depviz.repository import RepositoryError

COMMENT = "#"
NAME_SEP = ":"


def parse_test_repo(text: str) -> dict[str, list[str]]:
    """Разобрать описание репозитория; при ошибке - RepositoryError."""
    packages: dict[str, list[str]] = {}
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split(COMMENT, 1)[0].strip()
        if not line:
            continue
        name, sep, rest = line.partition(NAME_SEP)
        if not sep:
            raise RepositoryError(f"строка {number}: ожидается "
                                  "'ПАКЕТ: ЗАВИСИМОСТИ'")
        name = check_name(name.strip(), number)
        if name in packages:
            raise RepositoryError(f"строка {number}: пакет '{name}' "
                                  "уже описан")
        deps = [check_name(dep, number) for dep in rest.split()]
        packages[name] = list(dict.fromkeys(deps))
    check_references(packages)
    return packages


def check_name(name: str, number: int) -> str:
    """Проверить, что имя пакета состоит из больших латинских букв."""
    if not TEST_NAME.match(name):
        raise RepositoryError(f"строка {number}: недопустимое имя пакета "
                              f"'{name}' (нужны большие латинские буквы)")
    return name


def check_references(packages: dict[str, list[str]]) -> None:
    """Проверить, что все упомянутые зависимости описаны."""
    for name, deps in packages.items():
        for dep in deps:
            if dep not in packages:
                raise RepositoryError(f"зависимость '{dep}' пакета "
                                      f"'{name}' не описана")


class FileRepository:
    """Репозиторий пакетов, загруженный из файла описания графа."""

    def __init__(self, packages: dict[str, list[str]]):
        """Запомнить описание пакетов и их зависимостей."""
        self.packages = packages

    @classmethod
    def load(cls, path: str) -> "FileRepository":
        """Прочитать и разобрать файл тестового репозитория."""
        try:
            text = Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            raise RepositoryError(f"не удалось прочитать '{path}': "
                                  f"{error}") from error
        return cls(parse_test_repo(text))

    def dependencies(self, name: str, version: str = LATEST) -> list[str]:
        """Вернуть прямые зависимости пакета (версии не учитываются)."""
        if name not in self.packages:
            raise RepositoryError(f"пакет '{name}' не найден в тестовом "
                                  "репозитории")
        return list(self.packages[name])
