import os

from manuel import _config


def test_postgres_config_from_env_variables():
    os.environ["POSTGRES_USER"] = "test_user"
    os.environ["POSTGRES_PASSWORD"] = "test_password"
    os.environ["POSTGRES_HOST"] = "test_host"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["POSTGRES_DATABASE"] = "test_db"

    _config.PostgresSqlConfig()


def test_bigquery_config_from_env_variables():
    os.environ["BIGQUERY_PROJECT"] = "test_project"
    os.environ["BIGQUERY_LOCATION"] = "test_location"
    os.environ["BIGQUERY_USER_SUPPLIED_CLIENT"] = "True"

    _config.BigQuerySqlConfig()
