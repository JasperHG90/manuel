from typing import Iterator
from unittest import mock

import pytest
from devtools import run_container
from pytest_postgresql.janitor import DatabaseJanitor
from sqlalchemy import Engine, NullPool, create_engine
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Session

from manuel._config import PostgresSqlConfig
from manuel._executors.postgres import PostgresSqlAlchemyExecutor

IMAGE = "postgres:15.1"
POSTGRES_PASSWORD = "postgres"
POSTGRES_USER = "postgres"
POSTGRES_PORT = 65432
POSTGRES_HOST = "127.0.0.1"
POSTGRES_DATABASE = "test_db"


@pytest.fixture(scope="module")
def connection_string() -> str:
    return "postgresql+psycopg2://%s:%s@%s:%s/%s" % (
        POSTGRES_USER,
        POSTGRES_PASSWORD,
        POSTGRES_HOST,
        POSTGRES_PORT,
        POSTGRES_DATABASE,
    )


@pytest.fixture
def postgres_sql_executor() -> PostgresSqlAlchemyExecutor:
    return PostgresSqlAlchemyExecutor()


@pytest.fixture
def config() -> PostgresSqlConfig:
    return PostgresSqlConfig(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        database=POSTGRES_DATABASE,
    )


@pytest.fixture(scope="module", autouse=True)
def postgres_container():
    with run_container(
        image=IMAGE,
        image_name_prefix="manuel-postgres",
        environment=[f"POSTGRES_PASSWORD={POSTGRES_PASSWORD}"],
        ports={"5432/tcp": (POSTGRES_HOST, POSTGRES_PORT)},
        wait_seconds=1,
    ) as container:
        yield container


@pytest.fixture(scope="module")
def engine(postgres_container, connection_string: str) -> Iterator[Engine]:
    with DatabaseJanitor(
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DATABASE,
        version=15,
    ):
        engine = create_engine(
            connection_string,
            poolclass=NullPool,
        )
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
        id SERIAL PRIMARY KEY,
        age INT,
        category VARCHAR(10)
    );

    INSERT INTO test_table (age, category)
    VALUES (25, 'A');
    """


def test_postgres_sql_executor_format_connection_string(
    postgres_sql_executor: PostgresSqlAlchemyExecutor, config: PostgresSqlConfig
):
    connection_string = postgres_sql_executor.format_connection_string(
        **config.model_dump()
    )
    assert (
        connection_string
        == "postgresql+psycopg2://postgres:postgres@127.0.0.1:65432/test_db"
    )


def test_postgres_sql_executor_get_engine(
    postgres_sql_executor: PostgresSqlAlchemyExecutor, connection_string: str
):
    with postgres_sql_executor.get_engine(
        connection_string=connection_string
    ) as engine:
        assert engine.driver == "psycopg2"
        assert isinstance(engine.dialect, postgresql.psycopg2.PGDialect_psycopg2)


def test_postgres_sql_executor_execute_sql(
    statement: str, postgres_sql_executor: PostgresSqlAlchemyExecutor, session: Session
):
    postgres_sql_executor.execute_sql(sql=statement, session=session)
    session.rollback()


@mock.patch("manuel._executors.base.Session")
def test_postgres_sql_executor_run(
    mock_session: mock.MagicMock,
    statement: str,
    postgres_sql_executor: PostgresSqlAlchemyExecutor,
    config: PostgresSqlConfig,
):
    get_engine_mock = mock.MagicMock()
    execute_sql_mock = mock.MagicMock()
    sqlalchemy_session_mock = mock.MagicMock()
    # Add a mock to the return value of the mocked Session context manager return value
    mock_session.return_value.__enter__.return_value = sqlalchemy_session_mock
    # Add mocks to these two methods, which are called in the run method
    # We have checked them above, so all we care about is that the arguments are
    # passed correctly.
    postgres_sql_executor.get_engine = get_engine_mock
    postgres_sql_executor.execute_sql = execute_sql_mock
    postgres_sql_executor.run(sql=statement, **config.model_dump())
    get_engine_mock.assert_called_once_with(
        "postgresql+psycopg2://postgres:postgres@127.0.0.1:65432/test_db"
    )
    execute_sql_mock.assert_called_once_with(statement, sqlalchemy_session_mock)
