from __future__ import annotations

__all__ = ["Ref"]

from .base import Base, field


class Ref(Base):
    """Short object reference embedded into other API objects.

    Many payloads carry only `self`, `id` and `display` for a nested
    object (queue versions, components, issue fields, ...). Subclasses
    exist to name the referenced kind and to document where the shape
    comes from; they add no fields.

    Attributes
    ----------
    url - Reference to the object.
    id - Object ID.
    display - Name displayed in the interface (not always sent).

    """

    url: str = field(alias="self")
    id: str
    display: str | None = None
