import os
import pathlib as plb
from unittest import mock

import pytest
from typer.testing import CliRunner

from manuel.cli import app

runner = CliRunner()

executor_map = {
    "postgres": {
        "args": '{"user": "postgres", "password": "password", "host": "localhost", "port": 5432, "database": "test"}',
        "environ": {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "password",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DATABASE": "test",
        },
    },
    "bigquery": {
        "args": '{"project": "test", "location": "US"}',
        "environ": {
            "BIGQUERY_PROJECT": "test",
            "BIGQUERY_LOCATION": "US",
        },
    },
    "databricks": {
        "args": '{"token": "test", "server_hostname": "test", "http_path": "test", "catalog": "test", "databricks_schema": "test"}',
        "environ": {
            "DATABRICKS_TOKEN": "test",
            "DATABRICKS_SERVER_HOSTNAME": "test",
            "DATABRICKS_HTTP_PATH": "test",
            "DATABRICKS_CATALOG": "test",
            "DATABRICKS_SCHEMA": "test",
        },
    },
    "duckdb": {
        "args": '{"database": "test", "access_mode": "automatic", "s3_access_key_id": "test", "s3_secret_access_key": "test", "s3_endpoint": "test", "s3_region": "test", "s3_use_ssl": true, "allow_community_extensions": true}',
        "environ": {
            "DUCKDB_DATABASE": "test",
            "DUCKDB_ACCESS_MODE": "automatic",
            "DUCKDB_S3_ACCESS_KEY_ID": "test",
            "DUCKDB_S3_SECRET_ACCESS_KEY": "test",
            "DUCKDB_S3_ENDPOINT": "test",
            "DUCKDB_S3_REGION": "test",
            "DUCKDB_S3_USE_SSL": "true",
            "DUCKDB_ALLOW_COMMUNITY_EXTENSIONS": "true",
        },
    },
}


@pytest.mark.parametrize("dialect", ["postgres", "bigquery", "databricks"])
@mock.patch("manuel.cli._core.run_sql")
@mock.patch("manuel.cli._core.parse_sql")
def test_run_cmd_with_dialect_args(
    mock_parse_sql: mock.MagicMock,
    mock_run_sql: mock.MagicMock,
    tmp_path: plb.Path,
    dialect: str,
):
    script = tmp_path / "script.sql"
    script.touch()
    result = runner.invoke(
        app,
        [
            "run",
            str(script),
            dialect,
            "--dialect-args",
            executor_map[dialect]["args"],
        ],
    )
    assert result.exit_code == 0
    assert 1 == 1


@pytest.mark.parametrize("dialect", ["postgres", "bigquery", "databricks"])
@mock.patch("manuel.cli._core.run_sql")
@mock.patch("manuel.cli._core.parse_sql")
def test_run_cmd_with_env_vars(
    mock_parse_sql: mock.MagicMock,
    mock_run_sql: mock.MagicMock,
    tmp_path: plb.Path,
    dialect: str,
):
    script = tmp_path / "script.sql"
    script.touch()

    try:
        orig = os.environ.copy()
        os.environ.update(executor_map[dialect]["environ"])  # type: ignore
        result = runner.invoke(
            app,
            ["run", str(script), dialect],
        )
    finally:
        os.environ.clear()
        os.environ.update(orig)
    assert result.exit_code == 0


@pytest.mark.parametrize("dialect", ["postgres", "bigquery", "databricks"])
@mock.patch("manuel.cli._core.run_sql")
@mock.patch("manuel.cli._core.parse_sql")
def test_run_cmd_fails_without_env_vars_or_dialect_args(
    mock_parse_sql: mock.MagicMock,
    mock_run_sql: mock.MagicMock,
    tmp_path: plb.Path,
    dialect: str,
):
    script = tmp_path / "script.sql"
    script.touch()
    result = runner.invoke(
        app,
        ["run", str(script), dialect],
    )
    assert result.exit_code == 1
