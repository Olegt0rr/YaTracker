from __future__ import annotations

__all__ = ["FullIssueType", "IssueType"]

from .base import Base, url_field


class IssueType(Base):
    url: str = url_field()
    id: str
    key: str
    display: str


class FullIssueType(Base):
    """Issue type with all its details.

    Unlike :class:`IssueType`, which is the short reference embedded
    into issues and queues, this is the object the issue type endpoints
    return: it carries `name` instead of `display` and has no
    `display` at all.

    Source:
    https://yandex.ru/support/tracker/ru/api/admin/get-issue-types

    Attributes
    ----------
    url - reference to the object.
    id - issue type ID.
    version - issue type version.
    key - issue type key.
    name - name of the issue type displayed in the interface.
    description - description of the issue type.
    deleted - `True` when the issue type is deleted; the API omits the
    field otherwise.

    """

    url: str = url_field()
    id: str
    version: int
    key: str
    name: str
    description: str | None = None
    deleted: bool | None = None
