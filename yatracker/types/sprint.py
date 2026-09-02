from __future__ import annotations

__all__ = ["Sprint"]
from .base import Base, url_field


class Sprint(Base):
    url: str = url_field()
    id: str
    display: str
