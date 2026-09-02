from __future__ import annotations

__all__ = ["QueueVersion"]


from datetime import date

from .base import Base, url_field
from .queue import Queue


class QueueVersion(Base):
    url: str = url_field()
    id: int
    version: int
    queue: Queue
    name: str
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    released: bool
    archived: bool
