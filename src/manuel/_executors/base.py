import abc
import contextlib
import logging
from typing import Any, Dict, Iterator, Optional

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session

logger = logging.getLogger("manuel._executors.base")


class BaseSqlExecutor(abc.ABC):

    @abc.abstractmethod
    def run(self, sql: str, **engine_kwargs): ...


class BaseSqlAlchemyExecutor(BaseSqlExecutor):

    def __init__(
        self,
        engine_connect_args: Optional[Dict[str, Any]] = None,
        dry_run: bool = False,
    ):
        self.engine_connect_args = engine_connect_args if engine_connect_args else {}
        self.dry_run = dry_run

    @staticmethod
    @abc.abstractmethod
    def format_connection_string(**kwargs) -> str: ...

    @contextlib.contextmanager
    def get_engine(self, connection_string: str) -> Iterator[Engine]:
        try:
            engine = create_engine(
                connection_string, connect_args=self.engine_connect_args
            )
            yield engine
            engine.dispose()
        finally:
            ...

    def execute_sql(self, sql: str, session: Session):
        logger.debug("Executing statement: \n\n%s", sql)
        session.execute(text(sql))

    def run(self, sql: str, **engine_kwargs):
        with self.get_engine(self.format_connection_string(**engine_kwargs)) as engine:
            with Session(engine) as session:
                self.execute_sql(sql, session)
                if self.dry_run:
                    session.rollback()
                else:
                    session.commit()
