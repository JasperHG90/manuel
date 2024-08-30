import json
import logging
import pathlib as plb
from typing import Optional

import typer
from manuel import _core
from typing_extensions import Annotated

logger = logging.getLogger("manuel")
handler = logging.StreamHandler()
format = logging.Formatter("%(name)s - %(levelname)s - %(message)s")
handler.setFormatter(format)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


app = typer.Typer(
    name="manuel",
    help="A tool to run one-off SQL scripts",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=True,
    pretty_exceptions_short=True,
)


@app.callback()
def main(debug: bool = typer.Option(False, help="Enable debug logging.")):
    if debug:
        logger.setLevel(logging.DEBUG)


@app.command(
    name="validate",
    help="Validate a SQL file using SQLFluff",
)
def _validate(
    path: Annotated[plb.Path, typer.Argument(help="Path to the SQL file to validate")],
    dialect: Annotated[
        _core.SqlDialect, typer.Option(help="SQL dialect to use", case_sensitive=False)
    ] = "postgres",
):
    logger.info("Validating SQL file: %s", path)
    _core.parse_sql(path=path, dialect=dialect)
    logger.info("Validation successful")


@app.command(
    name="run",
    help="Execute a SQL file",
)
def _run(
    path: Annotated[plb.Path, typer.Argument(help="Path to the SQL file to validate")],
    dialect: Annotated[_core.SqlDialect, typer.Argument(help="SQL dialect to use")],
    dialect_args: Annotated[
        Optional[str],
        typer.Option(
            help="""Dialect-specific arguments passed as JSON (e.g. '{"user": "postgres", ...}').
            These may also be passed using environment variables prefixed with the dialect name in
            uppercase and an underscore (e.g. 'POSTGRES_USER')"""
        ),
    ] = None,
):
    logger.info("Executing SQL file: %s", path)
    _core.run_sql(
        sql=_core.parse_sql(path=path, dialect=dialect),
        dialect=dialect,
        engine_config=_core.config_map[dialect](
            **json.loads(dialect_args) if dialect_args else {}
        ),
    )
    logger.info("Execution successful")


def entrypoint():
    app()
