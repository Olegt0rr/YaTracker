from __future__ import annotations

__all__ = ["Comment"]

from datetime import datetime

from .base import Base, field
from .user import User


class Comment(Base, kw_only=True, frozen=True):
    url: str = field(name="self")
    id: str
    text: str
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None
    version: int
