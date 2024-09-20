import pytest

from manuel import _utils


class ClassNeedsExtra:

    def __init__(self): ...

    @staticmethod
    @_utils.requires_extra(
        library_name="psycopg2-binary",
        extra_name="postgres",
        extra_installed=False,
    )
    def get_connection_string() -> str:
        return "bigquery://project&location=location"


def test_requires_extra():
    with pytest.raises(ImportError, match="psycopg2-binary is not installed."):
        ClassNeedsExtra().get_connection_string()
