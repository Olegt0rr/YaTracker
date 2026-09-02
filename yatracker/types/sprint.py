from __future__ import annotations

__all__ = ["FullSprint", "Sprint"]

from datetime import date, datetime

from .base import Base, url_field
from .board import BoardRef
from .user import User


class Sprint(Base):
    url: str = url_field()
    id: str
    display: str


class FullSprint(Base):
    """Sprint with all its details.

    Unlike :class:`Sprint`, which is the short reference embedded into
    issues, this is the object the sprint endpoints return.

    `status` is one of `draft`, `in_progress`, `released`, `archived`.

    Source:
    https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprint
    """

    url: str = url_field()
    id: str
    version: int
    name: str
    board: BoardRef
    status: str
    archived: bool
    created_by: User
    created_at: datetime
    start_date: date | None = None
    end_date: date | None = None
    start_date_time: datetime | None = None
    end_date_time: datetime | None = None
