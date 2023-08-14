from __future__ import annotations

__all__ = ["Comment"]

from .base import Base, field
from .user import User


class Comment(Base, kw_only=True, frozen=True):
    url: str = field(name="self")
    id: str
    text: str
    created_by: User
    updated_by: User | None = None
    created_at: str
    updated_at: str | None = None
    version: int
