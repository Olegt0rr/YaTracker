from __future__ import annotations

__all__ = ["Attachment"]


from datetime import datetime

from .base import Base, field
from .user import User


class Attachment(Base, kw_only=True):
    """Represents attachment object."""

    url: str = field(name="self")
    id: str
    name: str
    content: str
    thumbnail: str | None = None
    created_by: User
    created_at: datetime
    mimetype: str
    size: int
    metadata: Metadata | None = None
    comment_id: str | None = None


class Metadata(Base, kw_only=True):
    """Represents attachment metadata."""

    size: str | None = None
