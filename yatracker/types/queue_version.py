from __future__ import annotations

__all__ = ["QueueVersion"]


from datetime import date

from .base import Base, url_field
from .queue import Queue


class QueueVersion(Base):
    """Version of a queue.

    Returned by `GET /queues/{id}/versions` and by
    `create_queue_version`.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/create-version

    Attributes
    ----------
    url - Reference to the version object.
    id - Version ID.
    version - Version number of the object.
    queue - Queue the version belongs to.
    name - Name of the version.
    description - Description of the version.
    start_date - Start date of the version.
    due_date - Due date of the version.
    released - Whether the version is released.
    archived - Whether the version is archived.

    """

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
