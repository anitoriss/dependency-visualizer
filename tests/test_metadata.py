"""Тесты разбора файлов метаданных пакета."""

from depviz.metadata import parse_metadata, parse_requires_txt


def test_requires_dist_headers():
    """Берутся все заголовки Requires-Dist, регистр ключа не важен."""
    text = ("Metadata-Version: 2.1\nName: x\n"
            "Requires-Dist: idna (<4,>=2.5)\n"
            "requires-dist: certifi; extra == 'ssl'\n"
            "Summary: Requires-Dist: nope\n")
    assert parse_metadata(text) == ["idna (<4,>=2.5)",
                                    "certifi; extra == 'ssl'"]


def test_description_body_is_ignored():
    """После пустой строки идёт описание - оно не разбирается."""
    text = "Name: x\nRequires-Dist: a\n\nRequires-Dist: b\n"
    assert parse_metadata(text) == ["a"]


def test_continuation_lines_are_not_headers():
    """Строки-продолжения (с отступом) не считаются заголовками."""
    text = "Name: x\nDescription: text\n        |\n  Requires-Dist: no\n" \
           "Requires-Dist: yes\n"
    assert parse_metadata(text) == ["yes"]


def test_windows_line_endings():
    """Файл с переводами строк Windows разбирается так же."""
    assert parse_metadata("Name: x\r\nRequires-Dist: a\r\n\r\n") == ["a"]


def test_requires_txt_sections():
    """Секции requires.txt превращаются в условия PEP 508."""
    text = ("Werkzeug>=0.7\n# comment\n\n"
            "[:python_version < \"3.8\"]\nimportlib-metadata\n"
            "[socks]\nPySocks>=1.5\n"
            "[tls:sys_platform == \"win32\"]\nwincert\n")
    assert parse_requires_txt(text) == [
        "Werkzeug>=0.7",
        'importlib-metadata; python_version < "3.8"',
        'PySocks>=1.5; extra == "socks"',
        'wincert; extra == "tls" and (sys_platform == "win32")',
    ]
