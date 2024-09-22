import pathlib as plb

import duckdb_engine
import pytest

from manuel._config import DuckdbSqlConfig
from manuel._executors import DuckdbSqlAlchemyExecutor


@pytest.fixture(
    params=[
        {
            "database": "test",
            "access_mode": "read_only",
            "allow_community_extensions": False,
            "s3_access_key_id": "access_key",
            "s3_secret_access_key": "secret_key",
        },
        {
            "database": ":memory:",
            "access_mode": "automatic",
            "allow_community_extensions": True,
        },
    ]
)
def config(request, tmp_path: plb.Path) -> DuckdbSqlConfig:
    if request.param["database"] == "test":
        database = str(tmp_path / "test.db")
    else:
        database = request.param["database"]
    return DuckdbSqlConfig(database=database)


def connection_string(config: DuckdbSqlConfig) -> str:
    return f"duckdb://{config.database}"


@pytest.fixture(scope="function")
def duckdb_sql_executor() -> DuckdbSqlAlchemyExecutor:
    return DuckdbSqlAlchemyExecutor()


def test_duckdb_sql_executor_format_connection_string(
    duckdb_sql_executor: DuckdbSqlAlchemyExecutor, config: DuckdbSqlConfig
):
    connection_string = duckdb_sql_executor.format_connection_string(
        **config.model_dump()
    )
    assert (
        connection_string == f"duckdb://{config.database}"
        if config.database != ":memory:"
        else f"duckdb:///{config.database}"
    )
    assert (
        duckdb_sql_executor.engine_connect_args["config"]["access_mode"]
        == config.access_mode.value
    )
    assert (
        duckdb_sql_executor.engine_connect_args["config"]["allow_community_extensions"]
        == config.allow_community_extensions
    )
    if config.s3_access_key_id:
        assert (
            duckdb_sql_executor.engine_connect_args["config"]["s3_access_key_id"]
            == config.s3_access_key_id.get_secret_value()
        )
    else:
        assert (
            duckdb_sql_executor.engine_connect_args["config"]["s3_access_key_id"]
            is None
        )


def test_duckdb_executor(
    duckdb_sql_executor: DuckdbSqlAlchemyExecutor, config: DuckdbSqlConfig
):
    connection_string = duckdb_sql_executor.format_connection_string(
        **config.model_dump()
    )  # This method also sets the engine_connect_args attribute of the executor
    with duckdb_sql_executor.get_engine(connection_string=connection_string) as engine:
        assert engine.driver == "duckdb_engine"
        assert isinstance(engine.dialect, duckdb_engine.Dialect)
