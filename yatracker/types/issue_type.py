from __future__ import annotations

__all__ = ["IssueType"]

from .base import Base, url_field


class IssueType(Base):
    url: str = url_field()
    id: str
    key: str
    display: str
