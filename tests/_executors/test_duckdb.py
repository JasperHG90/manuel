import pathlib as plb
from typing import Iterator
from unittest import mock

import duckdb_engine
import pytest
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

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
            "s3_endpoint": "endpoint",
            "s3_region": "region",
            "s3_use_ssl": False,
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


@pytest.fixture(scope="module")
def engine(tmp_path_factory) -> Iterator[Engine]:
    path = tmp_path_factory.mktemp("database")
    engine = create_engine(f"duckdb:///{str(path / 'test.db')}")
    yield engine
    engine.dispose()


@pytest.fixture(scope="module", autouse=True)
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="module")
def statement() -> str:
    return """
    CREATE TABLE IF NOT EXISTS test_table (
        id INTEGER,
        age INTEGER,
        category VARCHAR(10)
    );

    INSERT INTO test_table (id, age, category)
    VALUES (1, 25, 'A');
    """


@pytest.fixture(scope="function")
def duckdb_sql_executor() -> DuckdbSqlAlchemyExecutor:
    return DuckdbSqlAlchemyExecutor()


def test_duckdb_sql_executor_format_connection_string(
    duckdb_sql_executor: DuckdbSqlAlchemyExecutor, config: DuckdbSqlConfig
):
    connection_string = duckdb_sql_executor.format_connection_string(
        **config.model_dump()
    )
    assert connection_string == f"duckdb:///{config.database}"
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
    if config.s3_secret_access_key:
        assert (
            duckdb_sql_executor.engine_connect_args["config"]["s3_secret_access_key"]
            == config.s3_secret_access_key.get_secret_value()
        )
    else:
        assert (
            duckdb_sql_executor.engine_connect_args["config"]["s3_secret_access_key"]
            is None
        )
    if config.s3_endpoint:
        assert (
            duckdb_sql_executor.engine_connect_args["config"]["s3_endpoint"]
            == config.s3_endpoint
        )
    else:
        assert duckdb_sql_executor.engine_connect_args["config"]["s3_endpoint"] is None
    if config.s3_region:
        assert (
            duckdb_sql_executor.engine_connect_args["config"]["s3_region"]
            == config.s3_region
        )
    else:
        assert duckdb_sql_executor.engine_connect_args["config"]["s3_region"] is None
    assert (
        duckdb_sql_executor.engine_connect_args["config"]["s3_use_ssl"]
        == config.s3_use_ssl
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


def test_duckdb_sql_executor_execute_sql(
    statement: str, duckdb_sql_executor: DuckdbSqlAlchemyExecutor, session: Session
):
    duckdb_sql_executor.execute_sql(sql=statement, session=session)
    session.rollback()


@mock.patch("manuel._executors.base.Session")
def test_postgres_sql_executor_run(
    mock_session: mock.MagicMock,
    statement: str,
    duckdb_sql_executor: DuckdbSqlAlchemyExecutor,
    config: DuckdbSqlConfig,
):
    get_engine_mock = mock.MagicMock()
    execute_sql_mock = mock.MagicMock()
    sqlalchemy_session_mock = mock.MagicMock()
    # Add a mock to the return value of the mocked Session context manager return value
    mock_session.return_value.__enter__.return_value = sqlalchemy_session_mock
    # Add mocks to these two methods, which are called in the run method
    # We have checked them above, so all we care about is that the arguments are
    # passed correctly.
    duckdb_sql_executor.get_engine = get_engine_mock
    duckdb_sql_executor.execute_sql = execute_sql_mock
    duckdb_sql_executor.run(sql=statement, **config.model_dump())
    get_engine_mock.assert_called_once_with("duckdb:///%s" % config.database)
    execute_sql_mock.assert_called_once_with(statement, sqlalchemy_session_mock)
