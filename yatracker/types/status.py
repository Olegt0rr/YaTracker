from __future__ import annotations

__all__ = ["Status"]

from .base import Base, field


class Status(Base, kw_only=True, frozen=True):
    url: str = field(name="self")
    id: str
    key: str
    display: str
