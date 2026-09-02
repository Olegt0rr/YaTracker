from __future__ import annotations

__all__ = ["Attachment"]


from datetime import datetime

from .base import Base, url_field
from .user import User


class Attachment(Base):
    """Represents attachment object."""

    url: str = url_field()
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


class Metadata(Base):
    """Represents attachment metadata."""

    size: str | None = None
