from __future__ import annotations

__all__ = ["FieldCategory"]


from .base import Base, url_field


class FieldCategory(Base):
    """Category an issue field belongs to.

    Returned by the create/edit field-category requests. Fields embed a
    shorter reference to their category (`self`, `id`, `display`), which
    is modelled by :class:`yatracker.types.ref.Ref`.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/create-issue-field-category

    Attributes
    ----------
    url - Reference to the category.
    id - Category ID.
    name - Category name (a plain string, unlike the request body).
    version - Category version, incremented on every change.

    """

    url: str = url_field()
    id: str
    name: str
    version: int
