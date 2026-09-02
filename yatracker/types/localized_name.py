from __future__ import annotations

__all__ = ["LocalizedName"]


from .base import Base


class LocalizedName(Base):
    """Localized name sent when creating or editing a field or a category.

    The API expects the name of a global field, a local field or a field
    category as an object with a translation per language, e.g.
    ``{"en": "Sprint", "ru": "Спринт"}``. Responses, in contrast, carry
    the name as a plain string.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/create-field

    Attributes
    ----------
    en - Name in English.
    ru - Name in Russian.

    """

    en: str | None = None
    ru: str | None = None
