import logging

import pydantic

from manuel._config import DuckdbAccessMode
from manuel._executors.base import BaseSqlAlchemyExecutor
from manuel._utils import requires_extra

try:
    import duckdb_engine  # noqa
except ImportError:
    _has_duckdb_engine = False
else:
    _has_duckdb_engine = True


logger = logging.getLogger("manuel._executors.motherduck")


class MotherduckSqlAlchemyExecutor(BaseSqlAlchemyExecutor):

    @requires_extra(
        library_name="motherduck",
        extra_name="duckdb_engine",
        extra_installed=_has_duckdb_engine,
    )
    def format_connection_string(
        self,
        database: str,
        token: pydantic.SecretStr,
        access_mode: DuckdbAccessMode,
        allow_community_extensions: bool,
    ) -> str:
        connection_string = "duckdb:///md:%s" % (database)
        connect_args = {
            "config": {
                "access_mode": access_mode.value,
                "allow_community_extensions": allow_community_extensions,
                "motherduck_token": token.get_secret_value(),
            }
        }
        self.engine_connect_args = connect_args
        return connection_string
