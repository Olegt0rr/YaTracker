from __future__ import annotations

__all__ = ["Resolution"]


from .base import Base, field


class Resolution(Base):
    url: str = field(alias="self")
    id: str
    key: str
    display: str
