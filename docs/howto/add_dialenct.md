# Adding a new dialect

To add a new executor for a dialect, you need to:

1. Add extras to the project
1. Add an executor
1. Add a config class
1. Add the dialect to the core module
1. Write unit tests
1. Add the dialect to the CI/CD pipeline matrix so it gets built as a docker file

> 💡 Check the [available dialects](https://docs.sqlfluff.com/en/stable/reference/dialects.html) SQLFluff reference to see if your dialect is supported. This is a requirement to be able to parse the backend. Else, you need to implement your own parser.

> 💡 Ensure that the name for the dialect you're using is an **exact match** with the SQLFluff dialect name.

## Add extras to the project

Identify the extras required for your executor.

Add them to the project using the dialect name. For example:

```shell
uv add --optional databricks "databricks-sql-connector[sqlalchemy]>=3.4.0]"
```

## Add your dialect to src/manuel/_executors

To add an executor, you should preferably use a SQLAlchemy-compatible library. Doing so means that you can inherit from the base executor sqlalchemy class and only need to implement the abstract base class to constructing a connection string.

All executors should check for required extras in the executor, but not raise an `ImportError` until that code is actually required to run. You should use the following pattern:

```python
try:
    from databricks import sql  # noqa
except ImportError:
    _has_databricks_sql_connector = False
else:
    _has_databricks_sql_connector = True
```

In your executor, you can add the decorator `manuel._utils.requires_extra` around one of your methods that will raise an import error if the extra is not installed. For example:

```python
class DatabricksSqlAlchemyExecutor(BaseSqlAlchemyExecutor):

    @staticmethod
    @requires_extra(
        library_name="databricks-sql-connector[sqlalchemy]",
        extra_name="databricks",
        extra_installed=_has_databricks_sql_connector,
    )
    def format_connection_string(
        token: pydantic.SecretStr,
        server_hostname: str,
        http_path: str,
        catalog: str,
        schema_: str,
    ) -> str:
        ...
```

Refer to existing implementations in 'src/manuel/_executors' for more examples.

### Executors with a SQLAlchemy backend

To add an executor, you should preferably use a SQLAlchemy-compatible library. Doing so means that you can inherit from the base executor sqlalchemy class and only need to implement the abstract base class for constructing the connection string. For example:

```python
import pydantic

from manuel._executors.base import BaseSqlAlchemyExecutor
from manuel._utils import requires_extra


class DatabricksSqlAlchemyExecutor(BaseSqlAlchemyExecutor):

    @staticmethod
    @requires_extra(
        library_name="databricks-sql-connector[sqlalchemy]",
        extra_name="databricks",
        extra_installed=_has_databricks_sql_connector,
    )
    def format_connection_string(
        token: pydantic.SecretStr,
        server_hostname: str,
        http_path: str,
        catalog: str,
        schema_: str,
    ) -> str:
        return "databricks://token:%s@%s?http_path=%s&catalog=%s&schema=%s" % (
            token.get_secret_value(),
            server_hostname,
            http_path,
            catalog,
            schema_,
        )
```

> 💡 You should use `pydantic.SecretStr` to obfuscate secret values.

Finally, Import your executor in `src/manuel/_executors/__init__.py`

```python
from .databricks import DatabricksSqlAlchemyExecutor  # noqa
```

## Add a config class

In src/manuel/_config.py, create a new class that inherits from `pydantic_settings.BaseSettings` with any configuration options that you need. For example:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostgresSqlConfig(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="POSTGRES_", case_sensitive=False)

    host: str
    port: int
    user: str
    password: pydantic.SecretStr
    database: str
```

> 💡 The `SettingsConfigDict` `env_prefix` allows us to pass inputs as environment variables. In the example above, the input `host` can also be provided by setting the environment variable `POSTGRES_HOST`. This is important because we use a single entrypoint in the Manuel CLI for all dialects, and so we cannot configure the inputs required by different dialects there except through a string input that parses JSON. Additionally, using environment variables simplifies calling the Github Action in a CI/CD pipeline.

## Add the config and executor to the core module

To make your executor and config available to the Manuel CLI, open the 'src/manuel/_core.py' file and add them to the `Enum`, `executor_map`, and `config_map` objects:

```python
class SqlDialect(enum.Enum):
    POSTGRES = "postgres"
    BIGQUERY = "bigquery"
    DATABRICKS = "databricks"
    # Add your own dialect here
    NEWDIALECT = "NEWDIALECT"


executor_map = {
    SqlDialect.POSTGRES: _executors.PostgresSqlAlchemyExecutor,
    SqlDialect.BIGQUERY: _executors.BigQuerySqlAlchemyExecutor,
    SqlDialect.DATABRICKS: _executors.DatabricksSqlAlchemyExecutor,
    SqlDialect.NEWDIALECT: _executors.NewDialectSqlAlchemyExecutor
}


config_map = {
    SqlDialect.POSTGRES: _config.PostgresSqlConfig,
    SqlDialect.BIGQUERY: _config.BigQuerySqlConfig,
    SqlDialect.DATABRICKS: _config.DatabricksSqlConfig,
    SqlDialect.NEWDIALECT: _config.NewDialectSqlAlchemyExecutor
}
```

If you run `uv run manuel run --help`, you can now select your own dialect as an option.

## Write unit tests

### Executor test

You can refer to the available tests for examples. If you need a database to execute a sql statement, you can write the `devtools.run_container` function to spin up a docker container for the duration of your unit tests.

> 💡 The `devtools` library is included in this repository and is available under 'packages/devtools'.

### CLI

In 'tests/test_cli.py', add a dictionary with inputs for the Manuel run CLI command as a JSON input as well as environment variables to the `EXECUTOR_ARGS` dictionary. Add your dialect to the `DIALECTS` list.

### Config

In 'tests/_config.py', add a test to ensure that your configuration can read required environment variables.

### Parser

In 'tests/_parser.py', add a valid and an invalid SQL statement to `DIALECT_STATEMENTS`. Add your dialect to the parametrized test `test_sql_parser_validate`.

## Add the dialect to the CI/CD release pipeline

To build a docker image with all extras required for your dialect, make sure to add it to the matrix of the 'build' step in .github/workflows/release.yaml.

```yaml
    build:
        runs-on: ubuntu-latest
        needs: version
        permissions:
            packages: write
        strategy:
            matrix:
              dialect: ["postgres", "bigquery", "databricks", "NEWDIALECT"]
            fail-fast: false
```
