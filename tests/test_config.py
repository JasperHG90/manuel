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


def test_databricks_config_from_env_variables():
    os.environ["DATABRICKS_TOKEN"] = "test"
    os.environ["DATABRICKS_SERVER_HOSTNAME"] = "test"
    os.environ["DATABRICKS_HTTP_PATH"] = "test"
    os.environ["DATABRICKS_CATALOG"] = "test"
    os.environ["DATABRICKS_SCHEMA"] = "test"

    _config.DatabricksSqlConfig()


def test_duckdb_config_from_env_variables():
    os.environ["DUCKDB_DATABASE"] = "test"
    os.environ["DUCKDB_ACCESS_MODE"] = "automatic"
    os.environ["DUCKDB_S3_ACCESS_KEY_ID"] = "test"
    os.environ["DUCKDB_S3_SECRET_ACCESS_KEY"] = "test"
    os.environ["DUCKDB_S3_ENDPOINT"] = "test"
    os.environ["DUCKDB_S3_REGION"] = "test"
    os.environ["DUCKDB_S3_USE_SSL"] = "true"
    os.environ["DUCKDB_ALLOW_COMMUNITY_EXTENSIONS"] = "true"

    _config.DuckdbSqlConfig()


def test_motherduck_config_from_env_variables():
    os.environ["MOTHERDUCK_DATABASE"] = "test"
    os.environ["MOTHERDUCK_ACCESS_MODE"] = "automatic"
    os.environ["MOTHERDUCK_ALLOW_COMMUNITY_EXTENSIONS"] = "true"
    os.environ["MOTHERDUCK_TOKEN"] = "test"

    _config.MotherduckSqlConfig()
