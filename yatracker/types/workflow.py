from __future__ import annotations

__all__ = ["Workflow"]

from .base import Base, field


class Workflow(Base, kw_only=True):
    url: str = field(name="self")
    id: str
    key: str
    display: str
