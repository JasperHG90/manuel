from unittest import mock

import duckdb_engine
import pytest

from manuel._config import MotherduckSqlConfig
from manuel._executors import MotherduckSqlAlchemyExecutor


@pytest.fixture()
def config() -> MotherduckSqlConfig:
    return MotherduckSqlConfig(
        database="test",
        access_mode="read_only",
        allow_community_extensions=False,
        token="token",
    )


@pytest.fixture(scope="function")
def motherduck_sql_executor() -> MotherduckSqlAlchemyExecutor:
    return MotherduckSqlAlchemyExecutor()


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


def test_motherduck_sql_executor_format_connection_string(
    motherduck_sql_executor: MotherduckSqlAlchemyExecutor, config: MotherduckSqlConfig
):
    connection_string = motherduck_sql_executor.format_connection_string(
        **config.model_dump()
    )
    assert connection_string == f"duckdb:///md:{config.database}"
    assert (
        motherduck_sql_executor.engine_connect_args["config"]["access_mode"]
        == config.access_mode.value
    )
    assert (
        motherduck_sql_executor.engine_connect_args["config"][
            "allow_community_extensions"
        ]
        == config.allow_community_extensions
    )
    assert (
        motherduck_sql_executor.engine_connect_args["config"]["motherduck_token"]
        == "token"
    )


def test_motherduck_executor(
    motherduck_sql_executor: MotherduckSqlAlchemyExecutor, config: MotherduckSqlConfig
):
    connection_string = motherduck_sql_executor.format_connection_string(
        **config.model_dump()
    )  # This method also sets the engine_connect_args attribute of the executor
    with motherduck_sql_executor.get_engine(
        connection_string=connection_string
    ) as engine:
        assert engine.driver == "duckdb_engine"
        assert isinstance(engine.dialect, duckdb_engine.Dialect)


@mock.patch("manuel._executors.base.Session")
def test_motherduck_sql_executor_run(
    mock_session: mock.MagicMock,
    statement: str,
    motherduck_sql_executor: MotherduckSqlAlchemyExecutor,
    config: MotherduckSqlConfig,
):
    get_engine_mock = mock.MagicMock()
    execute_sql_mock = mock.MagicMock()
    sqlalchemy_session_mock = mock.MagicMock()
    # Add a mock to the return value of the mocked Session context manager return value
    mock_session.return_value.__enter__.return_value = sqlalchemy_session_mock
    # Add mocks to these two methods, which are called in the run method
    # We have checked them above, so all we care about is that the arguments are
    # passed correctly.
    motherduck_sql_executor.get_engine = get_engine_mock
    motherduck_sql_executor.execute_sql = execute_sql_mock
    motherduck_sql_executor.run(sql=statement, **config.model_dump())
    get_engine_mock.assert_called_once_with("duckdb:///md:%s" % config.database)
    execute_sql_mock.assert_called_once_with(statement, sqlalchemy_session_mock)
