from __future__ import annotations

__all__ = ["FullResolution", "Resolution"]


from .base import Base, url_field


class Resolution(Base):
    url: str = url_field()
    id: str
    key: str
    display: str


class FullResolution(Base):
    """Resolution with all its details.

    Unlike :class:`Resolution`, which is the short reference embedded
    into issues, this is the object the resolution endpoints return: it
    carries `name` instead of `display` and has no `display` at all.

    Source:
    https://yandex.ru/support/tracker/ru/api/admin/get-resolutions

    Attributes
    ----------
    url - reference to the object.
    id - resolution ID.
    version - resolution version.
    key - resolution key.
    name - name of the resolution displayed in the interface.
    description - description of the resolution.
    order - weight of the resolution; it affects the order the
    resolutions are displayed in the interface.

    """

    url: str = url_field()
    id: str
    version: int
    key: str
    name: str
    description: str | None = None
    order: int | None = None
