from __future__ import annotations

__all__ = ["Issue"]

from .base import Base, url_field


class Issue(Base):
    """Represents short view of issue."""

    url: str = url_field()
    id: str
    key: str
    display: str
