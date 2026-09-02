from __future__ import annotations

__all__ = ["FieldSuggestProvider"]


from .base import Base


class FieldSuggestProvider(Base):
    """Class of the search suggestion shown while filling a field in.

    The docs describe the object as carrying its class name only, and
    note that the class cannot be changed through the API.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/get-global-fields

    Attributes
    ----------
    type - Suggestion class, e.g. `UserSuggestProvider`.

    """

    type: str
