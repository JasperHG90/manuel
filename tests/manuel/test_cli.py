import os
import pathlib as plb
from unittest import mock

from typer.testing import CliRunner

from manuel.cli import app

runner = CliRunner()


@mock.patch("manuel.cli._core.run_sql")
@mock.patch("manuel.cli._core.parse_sql")
def test_run_cmd_with_dialect_args(
    mock_parse_sql: mock.MagicMock, mock_run_sql: mock.MagicMock, tmp_path: plb.Path
):
    script = tmp_path / "script.sql"
    script.touch()
    result = runner.invoke(
        app,
        [
            "run",
            str(script),
            "postgres",
            "--dialect-args",
            '{"user": "postgres", "password": "password", "host": "localhost", "port": 5432, "database": "test"}',
        ],
    )
    assert result.exit_code == 0
    assert 1 == 1


@mock.patch("manuel.cli._core.run_sql")
@mock.patch("manuel.cli._core.parse_sql")
def test_run_cmd_with_env_vars(
    mock_parse_sql: mock.MagicMock, mock_run_sql: mock.MagicMock, tmp_path: plb.Path
):
    script = tmp_path / "script.sql"
    script.touch()

    os.environ.update(
        {
            "POSTGRES_USER": "postgres",
            "POSTGRES_PASSWORD": "password",
            "POSTGRES_HOST": "localhost",
            "POSTGRES_PORT": "5432",
            "POSTGRES_DATABASE": "test",
        }
    )

    result = runner.invoke(
        app,
        [
            "run",
            str(script),
            "postgres",
        ],
    )
    assert result.exit_code == 0


@mock.patch("manuel.cli._core.run_sql")
@mock.patch("manuel.cli._core.parse_sql")
def test_run_cmd_fails_without_env_vars_or_dialect_args(
    mock_parse_sql: mock.MagicMock, mock_run_sql: mock.MagicMock, tmp_path: plb.Path
):
    script = tmp_path / "script.sql"
    script.touch()
    result = runner.invoke(
        app,
        [
            "run",
            str(script),
            "postgres",
        ],
    )
    assert result.exit_code == 1
