from __future__ import annotations

__all__ = ["IssueType"]

from .base import Base, field


class IssueType(Base, kw_only=True):
    url: str = field(name="self")
    id: str
    key: str
    display: str
