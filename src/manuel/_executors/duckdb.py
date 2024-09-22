import logging
from typing import Optional

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


logger = logging.getLogger("manuel._executors.duckdb")


class DuckdbSqlAlchemyExecutor(BaseSqlAlchemyExecutor):

    @requires_extra(
        library_name="duckdb",
        extra_name="duckdb_engine",
        extra_installed=_has_duckdb_engine,
    )
    def format_connection_string(
        self,
        database: str,
        access_mode: DuckdbAccessMode,
        allow_community_extensions: bool,
        s3_access_key_id: Optional[pydantic.SecretStr],
        s3_secret_access_key: Optional[pydantic.SecretStr],
        s3_endpoint: str,
        s3_region: str,
        s3_use_ssl: bool,
    ) -> str:
        connection_string = "duckdb:///%s" % (database)
        connect_args = {
            "config": {
                "access_mode": access_mode.value,
                "allow_community_extensions": allow_community_extensions,
                "s3_access_key_id": (
                    s3_access_key_id.get_secret_value() if s3_access_key_id else None
                ),
                "s3_secret_access_key": (
                    s3_secret_access_key.get_secret_value()
                    if s3_secret_access_key
                    else None
                ),
                "s3_endpoint": s3_endpoint,
                "s3_region": s3_region,
                "s3_use_ssl": s3_use_ssl,
            }
        }
        self.engine_connect_args = connect_args
        return connection_string
