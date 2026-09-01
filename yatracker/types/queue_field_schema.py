from __future__ import annotations

__all__ = ["QueueFieldSchema"]


from .base import Base


class QueueFieldSchema(Base):
    type: str
    required: bool | None = None
    items: str | None = None
