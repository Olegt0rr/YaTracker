from __future__ import annotations

__all__ = ["FieldCategory"]


from .base import Base, url_field


class FieldCategory(Base):
    """Category an issue field belongs to.

    Returned by the create/edit field-category requests and by
    `GET /fields/categories`. Fields embed a shorter reference to their
    category (`self`, `id`, `display`), which is modelled by
    :class:`yatracker.types.ref.Ref`.

    The response sample of the create/edit pages shows only `self`,
    `id`, `name` and `version`; `order` and `description` are documented
    as request parameters and come back from the listing endpoint, which
    has no page of its own, so both are optional here.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/create-issue-field-category

    Attributes
    ----------
    url - Reference to the category.
    id - Category ID.
    name - Category name (a plain string, unlike the request body).
    version - Category version, incremented on every change.
    order - Weight of the category in the interface; lighter categories
    are shown above heavier ones. Not shown in the create/edit response
    samples.
    description - Category description. Not shown in the create/edit
    response samples.

    """

    url: str = url_field()
    id: str
    name: str
    version: int
    order: int | None = None
    description: str | None = None
