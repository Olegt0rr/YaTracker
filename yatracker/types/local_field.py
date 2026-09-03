from __future__ import annotations

__all__ = ["LocalField"]


from .issue_field import IssueField
from .queue import Queue


class LocalField(IssueField):
    """Local issue field bound to a single queue.

    Same shape as a global field plus a reference to the owning queue.
    The `id` of a local field is built from a hexadecimal prefix and the
    field key (`6054ae3a2b6b2c7f********--loc_field_key`) and has to be
    used verbatim when reading or writing the field value of an issue,
    while the `/queues/{id}/localFields/{key}` endpoints address the
    field by its plain `key`.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-local-fields

    Attributes
    ----------
    queue - Reference to the queue the field belongs to. The create
        request answers without it.

    """

    queue: Queue | None = None
