from __future__ import annotations

__all__ = ["RemoteLink", "RemoteLinkObject"]

from datetime import datetime

from .application import Application
from .base import Base, field
from .issue_link import LinkDirection, LinkType
from .user import User


class RemoteLinkObject(Base):
    """Object of an external application referenced by a remote link.

    Attributes
    ----------
    url - Reference to the object.
    id - Object ID in the external application.
    key - Object key in the external application.
    application - External application the object belongs to.

    """

    url: str = field(alias="self")
    id: str
    key: str
    application: Application


class RemoteLink(Base):
    """Represents a link between an issue and an object of an external app."""

    url: str = field(alias="self")
    id: int
    type: LinkType
    direction: LinkDirection
    object: RemoteLinkObject
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None

    @property
    def name(self) -> str:
        """Get link name from links type based on direction."""
        return getattr(self.type, self.direction)
