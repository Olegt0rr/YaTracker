from __future__ import annotations

__all__ = ["Status"]

from .base import Base, field


class Status(Base):
    url: str = field(alias="self")
    id: str
    key: str
    display: str
