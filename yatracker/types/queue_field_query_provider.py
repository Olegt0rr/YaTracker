from __future__ import annotations

__all__ = ["QueueFieldQueryProvider"]


from .base import Base


class QueueFieldQueryProvider(Base, kw_only=True):
    type: str
