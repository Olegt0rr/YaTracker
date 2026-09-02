from __future__ import annotations

__all__ = ["IssueField"]


from .field_suggest_provider import FieldSuggestProvider
from .queue_field import QueueField
from .ref import Ref


class IssueField(QueueField):
    """Global issue field of the organization.

    Extends :class:`yatracker.types.queue_field.QueueField` (the shape
    returned by `GET /queues/{id}/fields`) with the keys the `/fields`
    endpoints add: the field key, its description, its category and the
    class of its search suggestion.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/get-global-fields

    Attributes
    ----------
    url - Reference to the field.
    id - Field ID.
    name - Field name.
    key - Field key.
    description - Field description.
    version - Field version, incremented on every change.
    field_schema - Data type of the field value (the API `schema` key).
    readonly - Whether the value cannot be changed.
    options - Whether any value is allowed (`False` means the list of
        values is limited by the organization settings).
    suggest - Whether a search suggestion is shown while filling in.
    suggest_provider - Class of the search suggestion. Cannot be changed
        through the API.
    options_provider - Allowed values of the field.
    query_provider - Class of the query language. Cannot be changed
        through the API.
    order - Position of the field in the organization field list.
    category - Reference to the category of the field.
    type - Field type, e.g. `standard` or `local`.

    """

    key: str | None = None
    description: str | None = None
    suggest_provider: FieldSuggestProvider | None = None
    category: Ref | None = None
    type: str | None = None
