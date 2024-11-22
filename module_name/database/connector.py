from fastapi import Depends
from typing import Sequence, Annotated, Callable
from fastapi.params import Depends as DependsParam
from sqlalchemy import Engine, Table, MetaData, inspect, text
from functools import partial
from sqlmodel import create_engine, SQLModel, Table, Session

from ..shared import config
from .shared import db_logger

__all__ = (
    'connect2database',
    'get_dbsession',
    'get_dbsession_depend',
    'db_logger'
)


def _get_table(table_name: str, metadata: MetaData, engine: Engine) -> Table:
    return Table(table_name, metadata, autoload_with=engine)


def _get_tables(metadata: MetaData, engine: Engine) -> dict[str, Table]:
    return {
        table_name: _get_table(table_name, metadata, engine) for table_name in inspect(engine).get_table_names()
    }


def _merge_table(old: Table, new: Table, engine: Engine):
    old_columns = old.columns

    with engine.connect() as connection:
        for column in new.columns:  # type: ignore
            column_name = column.name
            if column_name in old_columns:
                continue

            connection.execute(  # 手动添加 column
                text(f'ALTER TABLE {new.name} ADD COLUMN {column.name} {column.type}')
            )
            db_logger.success(
                'update database structure succeed for table `{}`: added column `{}`, type `{}`',
                new.name, column.name, column.type
            )


def _merge_tables(engine: Engine, metadata: MetaData | None = None):
    metadata = metadata or MetaData()
    old_tables = _get_tables(metadata, engine)
    for table_name, table in SQLModel.metadata.tables.items():
        if table_name not in old_tables:
            continue

        old_table = old_tables[table_name]
        _merge_table(old_table, table, engine)


def connect2database(tables: Sequence[Table] | None = None, checkfirst: bool = True) -> Engine:
    """
    connect to database

    :param tables: the tables will be created (if not exists), `None` to create all
    :param checkfirst: (from `SQLModel.metadata.create_all`) Defaults to True, don't issue CREATEs for tables already present in the target database.

    NOTE:
    please import SQL models first to let model be added to `SQLModel.metadata`
    """
    if not config.service.database.enable:
        raise RuntimeError('database is not enabled')

    engine = create_engine(
        config.service.database.url,
        **config.service.database.extras
    )

    SQLModel.metadata.create_all(engine, tables=tables, checkfirst=checkfirst)
    _merge_tables(engine)  # 合并 columns
    return engine


def get_dbsession(engine: Engine) -> Session:
    with Session(engine) as session:
        yield session


def get_dbsession_depend(engine: Engine) -> Annotated[Callable[[], Session], DependsParam]:
    return Depends(partial(get_dbsession, engine))
