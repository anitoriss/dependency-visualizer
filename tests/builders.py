"""Сборка небольших архивов пакетов в памяти для тестов."""

import io
import tarfile
import zipfile


def metadata(name: str, requires: list[str]) -> str:
    """Вернуть текст METADATA/PKG-INFO с заголовками Requires-Dist."""
    headers = ["Metadata-Version: 2.1", f"Name: {name}", "Version: 1.0"]
    headers += [f"Requires-Dist: {req}" for req in requires]
    return "\n".join(headers) + "\n\nRequires-Dist: not-a-header\n"


def make_wheel(name: str, requires: list[str]) -> bytes:
    """Собрать wheel (zip) с файлом dist-info/METADATA."""
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(f"{name}/__init__.py", "")
        archive.writestr(f"{name}-1.0.dist-info/METADATA",
                         metadata(name, requires))
    return buffer.getvalue()


def make_sdist(name: str, files: dict[str, str]) -> bytes:
    """Собрать sdist (tar.gz) из словаря путь -> содержимое."""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for path, text in files.items():
            data = text.encode("utf-8")
            info = tarfile.TarInfo(f"{name}-1.0/{path}")
            info.size = len(data)
            archive.addfile(info, io.BytesIO(data))
    return buffer.getvalue()


def release(name: str, files: list[tuple[str, str]]) -> dict:
    """Вернуть JSON-ответ PyPI: (filename, packagetype) для каждого
    файла; адрес файла совпадает с его именем.
    """
    urls = [{"filename": filename, "packagetype": kind, "url": filename,
             "size": 1} for filename, kind in files]
    return {"info": {"name": name, "version": "1.0",
                     "requires_dist": ["must-not-be-used"]},
            "urls": urls}
