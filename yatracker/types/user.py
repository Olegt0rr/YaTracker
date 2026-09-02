from __future__ import annotations

__all__ = ["User"]

from .base import Base, url_field


class User(Base):
    url: str = url_field()
    id: str
    display: str
