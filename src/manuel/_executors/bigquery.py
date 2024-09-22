import logging

from manuel._executors.base import BaseSqlAlchemyExecutor
from manuel._utils import requires_extra

try:
    import sqlalchemy_bigquery  # noqa
except ImportError:
    _has_bigquery = False
else:
    _has_bigquery = True


logger = logging.getLogger("manuel._executors.bigquery")


class BigQuerySqlAlchemyExecutor(BaseSqlAlchemyExecutor):

    @staticmethod
    @requires_extra(
        library_name="sqlalchemy_bigquery",
        extra_name="bigquery",
        extra_installed=_has_bigquery,
    )
    def format_connection_string(
        project: str, location: str, user_supplied_client: bool = False
    ) -> str:
        # See options: https://github.com/googleapis/python-bigquery-sqlalchemy?tab=readme-ov-file#connection-string-parameters
        connection_string = "bigquery://%s&location=%s" % (project, location)
        if user_supplied_client:
            connection_string += "?user_supplied_client=True"
        return connection_string
