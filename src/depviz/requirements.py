"""Разбор строк зависимостей формата pip (PEP 508), например
``charset-normalizer (<4,>=2)`` или ``PySocks>=1.5.6; extra == "socks"``.
"""

import re
from dataclasses import dataclass

from depviz.repository import RepositoryError

NAME = re.compile(r"\s*([A-Za-z0-9](?:[A-Za-z0-9._-]*[A-Za-z0-9])?)")
EXTRAS = re.compile(r"^\s*\[[^\]]*\]")
EXTRA_MARKER = re.compile(r"\bextra\s*==")
SEPARATORS = re.compile(r"[-_.]+")
MARKER_SEP = ";"


def normalize_name(name: str) -> str:
    """Привести имя пакета к каноническому виду (PEP 503)."""
    return SEPARATORS.sub("-", name).lower()


@dataclass(frozen=True)
class Requirement:
    """Одна зависимость: имя, ограничение версии и условие установки."""

    name: str
    spec: str = ""
    marker: str = ""

    @property
    def optional(self) -> bool:
        """True, если зависимость нужна только для доп. возможности."""
        return EXTRA_MARKER.search(self.marker) is not None

    def __str__(self) -> str:
        """Вернуть зависимость в виде ``имя спецификатор ; условие``."""
        text = f"{self.name} {self.spec}".strip()
        return f"{text} ; {self.marker}" if self.marker else text


def parse_requirement(text: str) -> Requirement:
    """Разобрать строку зависимости; при ошибке - RepositoryError."""
    body, _, marker = text.partition(MARKER_SEP)
    match = NAME.match(body)
    if match is None:
        raise RepositoryError(f"не удалось разобрать зависимость '{text}'")
    rest = EXTRAS.sub("", body[match.end():])
    spec = rest.strip().strip("()").replace(" ", "")
    return Requirement(normalize_name(match.group(1)), spec, marker.strip())
