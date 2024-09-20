import logging

import pydantic

from manuel._executors.base import BaseSqlExecutor
from manuel._utils import requires_extra

try:
    from databricks import sql  # noqa
except ImportError:
    _has_databricks_sql_connector = False
else:
    _has_databricks_sql_connector = True


logger = logging.getLogger("manuel._executors.databricks")


class DatabricksSqlExecutor(BaseSqlExecutor):

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
