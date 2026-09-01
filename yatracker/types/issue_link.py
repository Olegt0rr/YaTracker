from __future__ import annotations

__all__ = ["IssueLink", "LinkDirection", "LinkType"]

from datetime import datetime
from enum import Enum

from .base import Base, field
from .issue import Issue
from .status import Status
from .user import User


class LinkDirection(str, Enum):
    """Represents link direction."""

    INWARD = "inward"
    OUTWARD = "outward"


class LinkType(Base):
    """Represents issue link type."""

    url: str = field(alias="self")
    id: str
    inward: str
    outward: str


class IssueLink(Base):
    """Represents issue link."""

    url: str = field(alias="self")
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

    @property
    def name(self) -> str:
        """Get link name from links type based on direction."""
        return getattr(self.type, self.direction)
