"""Разбор файлов метаданных пакета, извлечённых из архива.

- ``METADATA`` (wheel) и ``PKG-INFO`` (sdist) - заголовки вида
  ``Requires-Dist: idna (<4,>=2.5)``, после пустой строки идёт описание;
- ``*.egg-info/requires.txt`` (старые sdist) - по зависимости в строке,
  секции ``[extra]``, ``[:условие]`` и ``[extra:условие]``.

Результат - строки зависимостей в формате PEP 508.
"""

import re

REQUIRES_DIST = "requires-dist"
HEADER_SEP = ":"
COMMENT = "#"
SECTION = re.compile(r"^\[(?P<extra>[^:\]]*)(?::(?P<marker>[^\]]*))?\]$")


def parse_metadata(text: str) -> list[str]:
    """Вернуть значения заголовков Requires-Dist (до тела описания)."""
    result = []
    for line in text.splitlines():
        if line == "":
            break
        key, sep, value = line.partition(HEADER_SEP)
        if sep and key.lower() == REQUIRES_DIST:
            result.append(value.strip())
    return result


def parse_requires_txt(text: str) -> list[str]:
    """Перевести requires.txt в строки PEP 508 с условиями секций."""
    result = []
    marker = ""
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(COMMENT):
            continue
        section = SECTION.match(line)
        if section:
            marker = section_marker(section.group("extra"),
                                    section.group("marker"))
        else:
            result.append(f"{line}; {marker}" if marker else line)
    return result


def section_marker(extra: str, marker: str | None) -> str:
    """Собрать условие PEP 508 из заголовка секции requires.txt."""
    parts = []
    if extra:
        parts.append(f'extra == "{extra}"')
    if marker:
        parts.append(f"({marker})" if extra else marker)
    return " and ".join(parts)
