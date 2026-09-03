from __future__ import annotations

__all__ = ["Priority"]

from .base import Base, url_field


class Priority(Base):
    """Represents Priority.

    Attributes
    ----------
    url - Reference to the object.
    id - Priority ID.
    key - Priority key.
    version - Priority version.
    display - Name displayed in the interface. Only the short reference
    embedded into issues carries it.
    name - Display name of the priority. When localized=false is passed
    in the request, this parameter contains duplicates of
    the names in other languages.
    description - Priority description.
    order - The weight of the priority. This parameter affects the order
    for displaying the priority in the interface.

    """

    url: str = url_field()
    id: str
    key: str
    display: str | None = None
    version: int | None = None
    name: str | dict | None = None
    description: str | None = None
    order: int | None = None
