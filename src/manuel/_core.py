import enum
import pathlib as plb

import pydantic

from manuel import _config, _executors, _parser


class SqlDialect(enum.Enum):
    POSTGRES = "postgres"
    BIGQUERY = "bigquery"
    DATABRICKS = "databricks"
    DUCKDB = "duckdb"


executor_map = {
    SqlDialect.POSTGRES: _executors.PostgresSqlAlchemyExecutor,
    SqlDialect.BIGQUERY: _executors.BigQuerySqlAlchemyExecutor,
    SqlDialect.DATABRICKS: _executors.DatabricksSqlAlchemyExecutor,
    SqlDialect.DUCKDB: _executors.DuckdbSqlAlchemyExecutor,
}


config_map = {
    SqlDialect.POSTGRES: _config.PostgresSqlConfig,
    SqlDialect.BIGQUERY: _config.BigQuerySqlConfig,
    SqlDialect.DATABRICKS: _config.DatabricksSqlConfig,
    SqlDialect.DUCKDB: _config.DuckdbSqlConfig,
}


def parse_sql(path: plb.Path, dialect: SqlDialect):
    return _parser.SqlParser.from_file(path=path, dialect=dialect.value).validate()


def run_sql(
    sql: str, dialect: SqlDialect, engine_config: pydantic.BaseModel, dry_run: bool
):
    executor_map[dialect](dry_run=dry_run).run(sql, **engine_config.model_dump())
