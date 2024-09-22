from typing import Iterator
from unittest import mock

import pytest
import sqlalchemy_bigquery
from devtools import run_container
from google.api_core.client_options import ClientOptions
from google.auth.credentials import AnonymousCredentials
from google.cloud import bigquery
from sqlalchemy import Engine, NullPool, create_engine
from sqlalchemy.orm import Session

from manuel._config import BigQuerySqlConfig
from manuel._executors import BigQuerySqlAlchemyExecutor

PROJECT_ID = "test-project"
DATASET_NAME = "dataset"
LOCATION = "europe-west4"


@pytest.fixture(scope="module")
def connection_string() -> str:
    return "bigquery://%s&location=%s?user_supplied_client=True" % (
        PROJECT_ID,
        LOCATION,
    )


@pytest.fixture(scope="module")
def client() -> bigquery.Client:
    return bigquery.Client(
        project=PROJECT_ID,
        client_options=ClientOptions(api_endpoint="http://0.0.0.0:9050"),
        credentials=AnonymousCredentials(),
    )


@pytest.fixture
def bigquery_sql_executor(client: bigquery.Client) -> BigQuerySqlAlchemyExecutor:
    return BigQuerySqlAlchemyExecutor(engine_connect_args={"client": client})


@pytest.fixture
def config():
    return BigQuerySqlConfig(
        project=PROJECT_ID, location=LOCATION, user_supplied_client=True
    )


@pytest.fixture(scope="module", autouse=True)
def bigquery_container():
    with run_container(
        image="ghcr.io/goccy/bigquery-emulator:0.6.5",
        command=["--project", PROJECT_ID, "--dataset", DATASET_NAME],
        image_name_prefix="manuel-bigquery",
        platform="linux/amd64",
        ports={
            "9050/tcp": ("127.0.0.1", 9050),  # API
            "9060/tcp": ("127.0.0.1", 9060),  # GRPC
        },
        wait_seconds=1,
    ) as container:
        yield container


@pytest.fixture(scope="module")
def engine(
    bigquery_container, connection_string: str, client: bigquery.Client
) -> Iterator[Engine]:
    engine = create_engine(
        connection_string, poolclass=NullPool, connect_args={"client": client}
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="module", autouse=True)
def session(engine: Engine) -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@pytest.fixture(scope="session")
def statement() -> str:
    return f"""
    CREATE TABLE `{PROJECT_ID}.{DATASET_NAME}.table` (
        `ADDRESS_ID` STRING,
        `INDIVIDUAL_ID` STRING,
        `FIRST_NAME` STRING,
        `LAST_NAME` STRING
    );
    """


@pytest.mark.parametrize(
    "config",
    [
        BigQuerySqlConfig(
            project=PROJECT_ID, location=LOCATION, user_supplied_client=False
        ),
        BigQuerySqlConfig(
            project=PROJECT_ID, location=LOCATION, user_supplied_client=True
        ),
    ],
)
def test_bigquery_sql_executor_format_connection_string(
    bigquery_sql_executor: BigQuerySqlAlchemyExecutor, config: BigQuerySqlConfig
):
    connection_string = bigquery_sql_executor.format_connection_string(
        **config.model_dump()
    )
    assert (
        connection_string
        == "bigquery://test-project&location=europe-west4?user_supplied_client=True"
        if config.user_supplied_client
        else "bigquery://test-project&location=europe-west4"
    )


def test_bigquery_sql_executor_get_engine(
    bigquery_sql_executor: BigQuerySqlAlchemyExecutor,
):
    with bigquery_sql_executor.get_engine(
        connection_string="bigquery://test-project&location=europe-west4?user_supplied_client=True"
    ) as engine:
        assert engine.driver == "bigquery"
        assert isinstance(engine.dialect, sqlalchemy_bigquery.BigQueryDialect)


def test_bigquery_sql_executor_execute_sql(
    statement: str, bigquery_sql_executor: BigQuerySqlAlchemyExecutor, session: Session
):
    bigquery_sql_executor.execute_sql(sql=statement, session=session)
    session.rollback()


@mock.patch("manuel._executors.base.Session")
def test_bigquery_sql_executor_run(
    mock_session: mock.MagicMock,
    statement: str,
    bigquery_sql_executor: BigQuerySqlAlchemyExecutor,
    config: BigQuerySqlConfig,
):
    get_engine_mock = mock.MagicMock()
    execute_sql_mock = mock.MagicMock()
    sqlalchemy_session_mock = mock.MagicMock()
    # Add a mock to the return value of the mocked Session context manager return value
    mock_session.return_value.__enter__.return_value = sqlalchemy_session_mock
    # Add mocks to these two methods, which are called in the run method
    # We have checked them above, so all we care about is that the arguments are
    # passed correctly.
    bigquery_sql_executor.get_engine = get_engine_mock
    bigquery_sql_executor.execute_sql = execute_sql_mock
    bigquery_sql_executor.run(sql=statement, **config.model_dump())
    get_engine_mock.assert_called_once_with(
        "bigquery://test-project&location=europe-west4?user_supplied_client=True"
    )
    execute_sql_mock.assert_called_once_with(statement, sqlalchemy_session_mock)
