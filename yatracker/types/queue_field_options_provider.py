from __future__ import annotations

__all__ = ["QueueFieldOptionsProvider"]


from .base import Base


class QueueFieldOptionsProvider(Base, kw_only=True):
    type: str
    values: list
    defaults: list
