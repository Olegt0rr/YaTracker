from __future__ import annotations

__all__ = ["QueueFieldQueryProvider"]


from .base import Base


class QueueFieldQueryProvider(Base):
    type: str
