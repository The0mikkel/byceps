"""
byceps.database
~~~~~~~~~~~~~~~

Database utilities.

:Copyright: 2014-2024 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from collections.abc import Callable, Iterable
from typing import Any, TypeVar

from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.pagination import Pagination
from sqlalchemy.dialects.postgresql import insert, JSONB
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.sql import Select
from sqlalchemy.sql.dml import Insert
from sqlalchemy.sql.schema import Table


F = TypeVar('F')
T = TypeVar('T')

Mapper = Callable[[F], T]


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


db.JSONB = JSONB


def paginate(
    stmt: Select,
    page: int,
    per_page: int,
    *,
    item_mapper: Mapper | None = None,
) -> Pagination:
    """Return `per_page` items from page `page`."""
    pagination = db.paginate(
        stmt, page=page, per_page=per_page, error_out=False
    )

    if item_mapper is not None:
        pagination.items = [item_mapper(item) for item in pagination.items]

    return pagination


def insert_ignore_on_conflict(table: Table, values: dict[str, Any]) -> None:
    """Insert the record identified by the primary key (specified as
    part of the values), or do nothing on conflict.
    """
    query = (
        insert(table)
        .values(**values)
        .on_conflict_do_nothing(constraint=table.primary_key)
    )

    db.session.execute(query)
    db.session.commit()


def upsert(
    table: Table, identifier: dict[str, Any], replacement: dict[str, Any]
) -> None:
    """Insert or update the record identified by `identifier` with value
    `replacement`.
    """
    execute_upsert(table, identifier, replacement)
    db.session.commit()


def upsert_many(
    table: Table,
    identifiers: Iterable[dict[str, Any]],
    replacement: dict[str, Any],
) -> None:
    """Insert or update the record identified by `identifier` with value
    `replacement`.
    """
    for identifier in identifiers:
        execute_upsert(table, identifier, replacement)

    db.session.commit()


def execute_upsert(
    table: Table, identifier: dict[str, Any], replacement: dict[str, Any]
) -> None:
    """Execute, but do not commit, an UPSERT."""
    query = _build_upsert_query(table, identifier, replacement)
    db.session.execute(query)


def _build_upsert_query(
    table: Table, identifier: dict[str, Any], replacement: dict[str, Any]
) -> Insert:
    values = identifier.copy()
    values.update(replacement)

    return (
        insert(table)
        .values(**values)
        .on_conflict_do_update(constraint=table.primary_key, set_=replacement)
    )
