from __future__ import annotations

__all__ = ["Sprint"]
from .base import Base, field


class Sprint(Base, kw_only=True, frozen=True):
    url: str = field(name="self")
    id: str
    display: str
