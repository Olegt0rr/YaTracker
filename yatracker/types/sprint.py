from __future__ import annotations

__all__ = ["Sprint"]
from .base import Base, field


class Sprint(Base):
    url: str = field(alias="self")
    id: str
    display: str
