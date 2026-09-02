from __future__ import annotations

__all__ = ["Resolution"]


from .base import Base, url_field


class Resolution(Base):
    url: str = url_field()
    id: str
    key: str
    display: str
