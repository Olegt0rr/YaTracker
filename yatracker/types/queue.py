from __future__ import annotations

__all__ = ["Queue"]

from .base import Base, field


class Queue(Base, kw_only=True, frozen=True):
    url: str = field(name="self")
    id: str
    key: str
    display: str
