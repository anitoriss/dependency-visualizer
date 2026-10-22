"""Распаковка скачанного файла пакета и поиск в нём метаданных.

Архив разбирается в памяти, на диск ничего не записывается:

- wheel (``.whl``) - zip-архив, зависимости в
  ``<пакет>-<версия>.dist-info/METADATA``;
- sdist (``.tar.gz``, ``.zip``) - зависимости в ``<папка>/PKG-INFO``,
  а если их там нет - в ``<пакет>.egg-info/requires.txt``.
"""

import io
import re
import tarfile
import zipfile
import zlib

from depviz.metadata import parse_metadata, parse_requires_txt
from depviz.repository import RepositoryError

WHEEL = ".whl"
ZIP = ".zip"
TAR = (".tar.gz", ".tgz", ".tar.bz2", ".tar")
ENCODING = "utf-8"
WHEEL_METADATA = re.compile(r"^[^/]+\.dist-info/METADATA$")
SDIST_PKG_INFO = re.compile(r"^[^/]+/PKG-INFO$")
SDIST_REQUIRES = re.compile(r"^[^/]+/(?:[^/]+/)?[^/]+\.egg-info/"
                            r"requires\.txt$")
ARCHIVE_ERRORS = (KeyError, OSError, EOFError, zlib.error,
                  zipfile.BadZipFile, tarfile.TarError)


class Archive:
    """Список файлов архива и чтение файла по имени."""

    def __init__(self, filename: str, data: bytes):
        """Открыть архив по расширению имени файла."""
        self.filename = filename
        buffer = io.BytesIO(data)
        try:
            if filename.endswith((WHEEL, ZIP)):
                packed = zipfile.ZipFile(buffer)
                self.names = packed.namelist()
                self._read = packed.read
            elif filename.endswith(TAR):
                packed = tarfile.open(fileobj=buffer, mode="r:*")
                self.names = [m.name for m in packed if m.isfile()]
                self._read = lambda name: packed.extractfile(name).read()
            else:
                raise RepositoryError(f"неизвестный формат архива "
                                      f"'{filename}'")
        except ARCHIVE_ERRORS as error:
            raise RepositoryError(f"не удалось распаковать '{filename}': "
                                  f"{error}") from error

    def find(self, pattern: re.Pattern) -> str | None:
        """Вернуть имя первого файла, подходящего под шаблон."""
        return next((n for n in self.names if pattern.match(n)), None)

    def read_text(self, name: str) -> str:
        """Прочитать файл архива как текст UTF-8."""
        try:
            data = self._read(name)
        except ARCHIVE_ERRORS as error:
            raise RepositoryError(f"не удалось прочитать '{name}' из "
                                  f"'{self.filename}': {error}") from error
        return data.decode(ENCODING, errors="replace")


def read_requirements(filename: str, data: bytes) -> list[str]:
    """Распаковать файл пакета и вернуть строки его зависимостей."""
    archive = Archive(filename, data)
    if filename.endswith(WHEEL):
        name = archive.find(WHEEL_METADATA)
        if name is None:
            raise RepositoryError(f"в '{filename}' нет файла METADATA")
        return parse_metadata(archive.read_text(name))
    name = archive.find(SDIST_PKG_INFO)
    requirements = parse_metadata(archive.read_text(name)) if name else []
    if requirements:
        return requirements
    name = archive.find(SDIST_REQUIRES)
    return parse_requires_txt(archive.read_text(name)) if name else []
