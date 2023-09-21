from __future__ import annotations

__all__ = ["QueueField"]


from .base import Base, field
from .queue_field_options_provider import QueueFieldOptionsProvider
from .queue_field_query_provider import QueueFieldQueryProvider
from .queue_field_schema import QueueFieldSchema


class QueueField(Base, kw_only=True):
    url: str = field(name="self")
    id: str
    name: str
    version: int

    field_schema: QueueFieldSchema
    readonly: bool
    options: bool
    suggest: bool
    options_provider: QueueFieldOptionsProvider | None = None
    query_provider: QueueFieldQueryProvider | None = None
    order: int
