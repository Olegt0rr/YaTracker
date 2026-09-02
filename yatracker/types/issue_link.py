from __future__ import annotations

__all__ = ["BaseLink", "IssueLink", "LinkDirection", "LinkRelationship", "LinkType"]

from datetime import datetime
from enum import Enum

from .base import Base, url_field
from .issue import Issue
from .status import Status
from .user import User


class LinkDirection(str, Enum):
    """Represents link direction."""

    INWARD = "inward"
    OUTWARD = "outward"


class LinkRelationship(str, Enum):
    """Represents a link type as accepted by the import API.

    Source:
    https://yandex.ru/support/tracker/ru/concepts/import/import-links
    """

    RELATES = "relates"
    IS_DEPENDENT_BY = "is dependent by"
    DEPENDS_ON = "depends on"
    IS_SUBTASK_FOR = "is subtask for"
    IS_PARENT_TASK_FOR = "is parent task for"
    DUPLICATES = "duplicates"
    IS_DUPLICATED_BY = "is duplicated by"
    IS_EPIC_OF = "is epic of"
    HAS_EPIC = "has epic"
    CLONE = "clone"
    ORIGINAL = "original"


class LinkType(Base):
    """Represents issue link type."""

    url: str = url_field()
    id: str
    inward: str
    outward: str


class BaseLink(Base):
    """Fields shared by issue links and remote links.

    Subclasses declare the `object` field: the linked entity.
    """

    url: str = url_field()
    id: int
    type: LinkType
    direction: LinkDirection
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @property
    def name(self) -> str:
        """Get link name from links type based on direction."""
        return getattr(self.type, self.direction)


class IssueLink(BaseLink):
    """Represents issue link.

    `assignee` and `status` describe the linked issue (the one in
    `object`). `GET /issues/{id}/links` sends both, while the response
    of `POST /issues/{id}/links` carries neither, so both are optional.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/get-links
    """

    object: Issue
    assignee: User | None = None
    status: Status | None = None
