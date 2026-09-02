from __future__ import annotations

__all__ = ["FieldRef", "Ref"]

from .base import Base, url_field


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

    url: str = url_field()
    id: str
    display: str | None = None


class FieldRef(Ref):
    """Short issue-field reference.

    Embedded into macro payloads (`Macro.issue_update`) and used by the
    deprecated `estimateBy` field of a board.

    Attributes
    ----------
    url - Reference to the object.
    id - Field ID.
    display - Field name displayed in the interface.

    """
