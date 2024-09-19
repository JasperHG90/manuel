import logging

from manuel._executors.base import BaseSqlExecutor
from manuel._utils import requires_extra

try:
    import psycopg2  # noqa
except ImportError:
    _has_psycopg = False
else:
    _has_psycopg = True


logger = logging.getLogger("manuel._executors.postgres")


class PostgresSqlExecutor(BaseSqlExecutor):

    @staticmethod
    @requires_extra(
        library_name="psycopg2-binary",
        extra_name="postgres",
        extra_installed=_has_psycopg,
    )
    def format_connection_string(
        user: str, password: str, host: str, port: int, database: str
    ) -> str:
        return "postgresql+psycopg2://%s:%s@%s:%s/%s" % (
            user,
            password,
            host,
            port,
            database,
        )
