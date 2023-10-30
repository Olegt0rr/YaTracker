from __future__ import annotations

__all__ = ["IssueLink", "LinkType", "LinkDirection"]

from datetime import datetime
from enum import StrEnum, auto

from .base import Base, field
from .issue import Issue
from .status import Status
from .user import User


class LinkDirection(StrEnum):
    """Represents link direction."""

    INWARD = auto()
    OUTWARD = auto()


class LinkType(Base, kw_only=True):
    """Represents issue link type."""

    url: str = field(name="self")
    id: str
    inward: str
    outward: str


class IssueLink(Base, kw_only=True):
    """Represents issue link."""

    url: str = field(name="self")
    id: int
    type: LinkType
    direction: LinkDirection
    object: Issue
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None
    assignee: User | None = None
    status: Status
