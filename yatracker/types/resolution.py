from __future__ import annotations

__all__ = ["Resolution"]


from .base import Base, field


class Resolution(Base, kw_only=True):
    url: str = field(name="self")
    id: str
    key: str
    display: str
