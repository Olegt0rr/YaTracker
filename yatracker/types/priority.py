from __future__ import annotations

__all__ = ["Priority"]

from .base import Base, field


class Priority(Base, kw_only=True):
    """Represents Priority.

    Attributes
    ----------
    url - Reference to the object.
    id - Priority ID.
    key - Priority key.
    version - Priority version.
    name - Display name of the priority. When localized=false is passed
    in the request, this parameter contains duplicates of
    the names in other languages.
    order - The weight of the priority. This parameter affects the order
    for displaying the priority in the interface.
    """

    url: str = field(name="self")
    id: str
    key: str
    display: str | None = None
    version: int | None = None
    name: str | dict | None = None
    order: int | None = None
