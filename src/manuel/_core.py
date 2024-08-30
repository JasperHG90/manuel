import enum
import pathlib as plb

import pydantic
from manuel import _config, _executors, _parser


class SqlDialect(enum.Enum):
    POSTGRES = "postgres"
    BIGQUERY = "bigquery"


executor_map = {
    SqlDialect.POSTGRES: _executors.PostgresSqlExecutor,
    SqlDialect.BIGQUERY: _executors.BigQuerySqlExecutor,
}


config_map = {
    SqlDialect.POSTGRES: _config.PostgresSqlConfig,
    SqlDialect.BIGQUERY: _config.BigQuerySqlConfig,
}


def parse_sql(path: plb.Path, dialect: SqlDialect):
    return _parser.SqlParser.from_file(path=path, dialect=dialect.value).validate()


def run_sql(sql: str, dialect: SqlDialect, engine_config: pydantic.BaseModel):
    executor_map[dialect]().run(sql, **engine_config.model_dump())
