from __future__ import annotations

__all__ = ["FieldRef"]

from .base import Base, field


class FieldRef(Base):
    """Short issue-field reference embedded into macro payloads.

    Attributes
    ----------
    url - Reference to the object.
    id - Field ID.
    display - Field name displayed in the interface.

    """

    url: str = field(alias="self")
    id: str
    display: str | None = None
