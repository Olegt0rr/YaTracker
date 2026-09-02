from __future__ import annotations

__all__ = ["Status"]

from .base import Base, url_field


class Status(Base):
    url: str = url_field()
    id: str
    key: str
    display: str
