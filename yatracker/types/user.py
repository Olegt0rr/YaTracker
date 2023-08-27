from __future__ import annotations

__all__ = ["User"]

from .base import Base, field


class User(Base, kw_only=True):
    url: str = field(name="self")
    id: str
    display: str
