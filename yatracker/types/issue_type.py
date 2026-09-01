from __future__ import annotations

__all__ = ["IssueType"]

from .base import Base, field


class IssueType(Base):
    url: str = field(alias="self")
    id: str
    key: str
    display: str
