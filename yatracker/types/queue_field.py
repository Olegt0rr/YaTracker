from __future__ import annotations

__all__ = ["QueueField"]


from .base import Base, field, url_field
from .queue_field_options_provider import QueueFieldOptionsProvider
from .queue_field_query_provider import QueueFieldQueryProvider
from .queue_field_schema import QueueFieldSchema


class QueueField(Base):
    url: str = url_field()
    id: str
    name: str
    version: int

    # the API sends this one as `schema`, not as the camelized `fieldSchema`
    field_schema: QueueFieldSchema = field(alias="schema")
    readonly: bool
    options: bool
    suggest: bool
    options_provider: QueueFieldOptionsProvider | None = None
    query_provider: QueueFieldQueryProvider | None = None
    order: int
