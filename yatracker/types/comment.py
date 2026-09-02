from __future__ import annotations

__all__ = ["Comment"]

from datetime import datetime

from .base import Base, url_field
from .user import User


class Comment(Base):
    url: str = url_field()
    id: int
    text: str
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None
    version: int
