import pathlib as plb

import duckdb_engine
import pytest

from manuel._config import DuckdbSqlConfig
from manuel._executors import DuckdbSqlAlchemyExecutor


@pytest.fixture(params=[{"database": "test"}, {"database": ":memory:"}])
def config(request, tmp_path: plb.Path) -> DuckdbSqlConfig:
    if request.param["database"] == "test":
        database = str(tmp_path / "test.db")
    else:
        database = request.param["database"]
    return DuckdbSqlConfig(database=database)


def connection_string(config: DuckdbSqlConfig) -> str:
    return f"duckdb://{config.database}"


@pytest.fixture
def duckdb_sql_executor() -> DuckdbSqlAlchemyExecutor:
    return DuckdbSqlAlchemyExecutor()


def test_duckdb_executor(
    duckdb_sql_executor: DuckdbSqlAlchemyExecutor, config: DuckdbSqlConfig
):
    connection_string = duckdb_sql_executor.format_connection_string(
        **config.model_dump()
    )
    with duckdb_sql_executor.get_engine(connection_string=connection_string) as engine:
        assert engine.driver == "duckdb_engine"
        assert isinstance(engine.dialect, duckdb_engine.Dialect)
