import pathlib as plb

import pytest

from manuel import _core, _parser

DIALECT_STATEMENTS = {
    "postgres": {
        "valid": """SELECT 1 FROM public.table""",
        "invalid": """SELECT 1 FROM public.table WHERE""",
    },
    "bigquery": {
        "valid": """SELECT 1 FROM `project.dataset.table`""",
        "invalid": """SELECT 1 FROM `project.dataset.table` WHERE""",
    },
    "databricks": {
        "valid": """CREATE TABLE ct.sampleTable (number Int, word String)""",
        "invalid": """CREATE TABLE ct.sampleTable (number Int, word BigString)""",
    },
    "duckdb": {
        "valid": """CREATE TABLE test_table (id INTEGER, age INTEGER)""",
        "invalid": """CREATE TABLE test_table (id SERIAL INTEGER PRIMARY KEY, age INTEGER)""",
    },
}


@pytest.fixture
def sql_statement_from_file(tmp_path: plb.Path) -> plb.Path:
    sql_file = tmp_path / "test.sql"
    sql_file.write_text("SELECT 1 FROM public.table;")
    return sql_file


@pytest.fixture
def sql() -> str:
    return "SELECT 1;"


@pytest.mark.parametrize("dialect", [d.value for d in _core.SqlDialect])
def test_sql_dialect_mapping_valid(dialect: str):
    _parser.SqlParser(sql="SELECT 1;", dialect=dialect)


@pytest.mark.parametrize(
    "dialect,kind",
    [
        ("postgres", "valid"),
        ("postgres", "invalid"),
        ("bigquery", "valid"),
        ("bigquery", "invalid"),
        ("databricks", "valid"),
        ("databricks", "invalid"),
        ("duckdb", "valid"),
        ("duckdb", "invalid"),
    ],
)
def test_sql_parser_validate(dialect: str, kind: str):
    statement = DIALECT_STATEMENTS[dialect][kind]
    if kind == "invalid":
        with pytest.raises(ValueError, match="SQL statement is not valid"):
            _parser.SqlParser(sql=statement, dialect=dialect).validate()
    else:
        _parser.SqlParser(sql=statement, dialect=dialect).validate()


def test_sql_parser_unknown_dialect():
    with pytest.raises(ValueError, match="Unsupported dialect: unknown"):
        _parser.SqlParser(sql="SELECT 1", dialect="unknown").validate()


def test_sql_parser_from_sql_file(sql_statement_from_file: plb.Path):
    _parser.SqlParser.from_file(
        path=sql_statement_from_file, dialect="postgres"
    ).validate()
