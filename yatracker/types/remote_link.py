from __future__ import annotations

__all__ = ["RemoteLink", "RemoteLinkObject"]

from .application import Application
from .base import Base, field
from .issue_link import BaseLink


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


class RemoteLink(BaseLink):
    """Represents a link between an issue and an object of an external app.

    Shares `type`, `direction`, the `name` helper and the audit fields
    with `IssueLink`; only `object` differs.
    """

    object: RemoteLinkObject
