from __future__ import annotations

__all__ = ["QueueFieldOptionsProvider"]


from .base import Base


class QueueFieldOptionsProvider(Base):
    type: str
    # the API returns either a plain array or an object
    # mapping a key to an array, e.g. {"DIRECT": ["First", ...]}
    values: dict[str, list] | list | None = None
    defaults: list | None = None
    # sent back by the `/fields` and `/queues/{id}/localFields` endpoints
    need_validation: bool | None = None
