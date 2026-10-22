"""Тесты точки входа."""

from depviz.__main__ import EXIT_OK, EXIT_USAGE, main


def test_prints_parameters_as_key_value(capsys):
    """При запуске все параметры выводятся в формате ключ=значение."""
    assert main(["-p", "requests", "-v", "2.31.0"]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert "package=requests" in out
    assert "version=2.31.0" in out
    assert "filter_substring=" in out


def test_error_is_reported_with_usage_code(capsys):
    """Ошибка параметра выводится в stderr, код завершения 2."""
    assert main(["-p", "requests", "-o", "x.png"]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith("depviz: ошибка:")
