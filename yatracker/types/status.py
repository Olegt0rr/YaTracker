from __future__ import annotations

__all__ = ["FullStatus", "Status"]

from .base import Base, url_field


class Status(Base):
    url: str = url_field()
    id: str
    key: str
    display: str


class FullStatus(Base):
    """Issue status with all its details.

    Unlike :class:`Status`, which is the short reference embedded into
    issues, this is the object the status endpoints return: it carries
    `name` instead of `display` and has no `display` at all.

    Source:
    https://yandex.ru/support/tracker/ru/api/admin/get-statuses

    Attributes
    ----------
    url - reference to the object.
    id - status ID.
    version - status version.
    key - status key.
    name - name of the status displayed in the interface.
    description - description of the status.
    order - weight of the status; it affects the order the statuses are
    displayed in the interface.
    type - type of the status: "new", "inProgress", "paused", "done" or
    "cancelled".

    """

    url: str = url_field()
    id: str
    version: int
    key: str
    name: str
    description: str | None = None
    order: int | None = None
    type: str | None = None
