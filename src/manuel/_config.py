from typing import Optional

import pydantic
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSqlConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", case_sensitive=False)

    host: str
    port: int
    user: str
    password: pydantic.SecretStr
    database: str


class BigQuerySqlConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BIGQUERY_", case_sensitive=False)

    project: str
    location: str
    user_supplied_client: Optional[bool] = False


class DatabricksSqlConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DATABRICKS_", case_sensitive=False)

    token: pydantic.SecretStr
    server_hostname: str
    http_path: str
    catalog: str
    # env_prefix does not apply to aliases, and 'schema' is already an attribute in BaseSettings
    #  so fixing this with the following alias
    #  See: https://docs.pydantic.dev/latest/concepts/pydantic_settings/#validation-of-default-values
    schema_: str = pydantic.Field(alias="databricks_schema")
