import logging
import pathlib as plb

import sqlfluff

from manuel import _utils

logger = logging.getLogger("manuel._parser")


class SqlParser:

    def __init__(self, sql: str, dialect: str) -> None:
        self.sql = sql
        self.dialect = dialect

    @property
    def sql(self) -> str:
        return self._sql

    @sql.setter
    def sql(self, value: str) -> None:
        self._sql = value

    @property
    def dialect(self) -> str:
        return self._dialect

    @dialect.setter
    def dialect(self, value: str) -> None:
        if value not in [dialect.label.lower() for dialect in sqlfluff.list_dialects()]:
            raise ValueError(f"Unsupported dialect: {value}")
        else:
            logger.debug("Using dialect '%s'", value)
            self._dialect = value

    def validate(self):
        """Use SQLFluff to validate the input SQL string

        Args:
            sql (str): SQL string to validate

        Raises:
            ValueError: If the SQL statement is not valid. That is, if there are any Template or Parse errors.
              Other errors are ignored.

        Returns:
            str: The input SQL string
        """
        res = sqlfluff.lint(self.sql, dialect=self.dialect)
        if len(res) == 0:
            return self.sql
        logger.debug("Sqlfluff found %s errors", len(res))
        logger.debug("Will raise errors on TMP (template) and PRS (parse) errors")
        for r in res:
            if r["code"] in ["TMP", "PRS"]:
                raise ValueError(
                    f"SQL statement is not valid. Got error: \n\n{r['description']}"
                )
        return self.sql

    @classmethod
    def from_file(cls, path: plb.Path, dialect: str):
        return cls(_utils.read_sql_file(path.resolve()), dialect)
