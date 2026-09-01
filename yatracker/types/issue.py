from __future__ import annotations

__all__ = ["Issue"]

from .base import Base, field


class Issue(Base):
    """Represents short view of issue."""

    url: str = field(alias="self")
    id: str
    key: str
    display: str
