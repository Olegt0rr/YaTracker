from __future__ import annotations

__all__ = ["User"]

from .base import Base, field


class User(Base):
    url: str = field(alias="self")
    id: str
    display: str
