from __future__ import annotations

__all__ = ["Queue"]

from .base import Base, field


class Queue(Base):
    url: str = field(alias="self")
    id: str
    key: str
    display: str
