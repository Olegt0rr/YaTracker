from __future__ import annotations

__all__ = ["Application"]

from .base import Base, url_field


class Application(Base):
    """Represents an external application a remote link can point to.

    Attributes
    ----------
    url - Reference to the object.
    id - Application ID.
    type - Application type. Equals the application ID in the
    `/applications` listing, but an application nested into a remote
    link may report a generic type such as "app".
    name - Application name.

    """

    url: str = url_field()
    id: str
    type: str
    name: str
