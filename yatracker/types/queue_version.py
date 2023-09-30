from __future__ import annotations

__all__ = ["QueueVersion"]


from datetime import date

from .base import Base, field
from .queue import Queue


class QueueVersion(Base, kw_only=True):
    url: str = field(name="self")
    id: int
    version: int
    queue: Queue
    name: str
    description: str | None = None
    start_date: date | None = None
    due_date: date | None = None
    released: bool
    archived: bool
