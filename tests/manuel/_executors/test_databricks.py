from unittest import mock

import databricks
import pytest

from manuel._config import DatabricksSqlConfig
from manuel._executors import DatabricksSqlExecutor

DATABRICKS_TOKEN = "hgghew78876rtausytfjhvda"
DATABRICKS_SERVER_HOSTNAME = "something.local.databricks.com"
DATABRICKS_HTTP_PATH = "/sql/protocolv1/o/0/0000000000000000"
DATABRICKS_CATALOG = "mycatalog"
DATABRICKS_SCHEMA = "myschema"


@pytest.fixture(scope="module")
def connection_string() -> str:
    return "databricks://token:%s@%s?http_path=%s&catalog=%s&schema=%s" % (
        DATABRICKS_TOKEN,
        DATABRICKS_SERVER_HOSTNAME,
        DATABRICKS_HTTP_PATH,
        DATABRICKS_CATALOG,
        DATABRICKS_SCHEMA,
    )


@pytest.fixture
def databricks_sql_executor() -> DatabricksSqlExecutor:
    return DatabricksSqlExecutor()


@pytest.fixture
def config():
    return DatabricksSqlConfig(
        token=DATABRICKS_TOKEN,
        server_hostname=DATABRICKS_SERVER_HOSTNAME,
        http_path=DATABRICKS_HTTP_PATH,
        catalog=DATABRICKS_CATALOG,
        schema=DATABRICKS_SCHEMA,
    )


@pytest.fixture(scope="session")
def statement() -> str:
    return """
    CREATE DATABASE IF NOT EXISTS ct;
    CREATE TABLE ct.sampleTable (number Int, word String);
    """


def test_databricks_sql_executor_format_connection_string(
    databricks_sql_executor: DatabricksSqlExecutor, config: DatabricksSqlConfig
):
    connection_string = databricks_sql_executor.format_connection_string(
        **config.model_dump()
    )
    assert (
        connection_string
        == "databricks://token:hgghew78876rtausytfjhvda@something.local.databricks.com?http_path=/sql/protocolv1/o/0/0000000000000000&catalog=mycatalog&schema=myschema"
    )


def test_databricks_sql_executor_get_engine(
    databricks_sql_executor: DatabricksSqlExecutor, connection_string: str
):
    with databricks_sql_executor.get_engine(
        connection_string=connection_string
    ) as engine:
        assert engine.driver == "databricks"
        assert isinstance(engine.dialect, databricks.sqlalchemy.base.DatabricksDialect)


@mock.patch("manuel._executors.base.Session")
def test_databricks_sql_executor_run(
    mock_session: mock.MagicMock,
    statement: str,
    databricks_sql_executor: DatabricksSqlExecutor,
    config: DatabricksSqlConfig,
):
    get_engine_mock = mock.MagicMock()
    execute_sql_mock = mock.MagicMock()
    sqlalchemy_session_mock = mock.MagicMock()
    # Add a mock to the return value of the mocked Session context manager return value
    mock_session.return_value.__enter__.return_value = sqlalchemy_session_mock
    databricks_sql_executor.get_engine = get_engine_mock
    databricks_sql_executor.execute_sql = execute_sql_mock
    databricks_sql_executor.run(sql=statement, **config.model_dump())
    get_engine_mock.assert_called_once_with(
        "databricks://token:hgghew78876rtausytfjhvda@something.local.databricks.com?http_path=/sql/protocolv1/o/0/0000000000000000&catalog=mycatalog&schema=myschema"
    )
    execute_sql_mock.assert_called_once_with(statement, sqlalchemy_session_mock)
