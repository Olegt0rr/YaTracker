from __future__ import annotations

__all__ = ["QueueFieldOptionsProvider"]


from typing import Any

from .base import Base


class QueueFieldOptionsProvider(Base):
    """Drop-down list of an issue field.

    Attributes
    ----------
    type - Kind of the drop-down list: `FixedListOptionsProvider` for
    string or integer fields, `FixedUserListOptionsProvider` for user
    fields.
    values - Values of the drop-down list. The API returns either a
    plain array or an object mapping a key to an array, e.g.
    `{"DIRECT": ["First", ...]}`.
    defaults - Default values. Undocumented: it is sent back by some
    fields but named by no request or response table, so it is read
    only and never written back.
    need_validation - Read-only flag sent back by the `/fields` and
    `/queues/{id}/localFields` endpoints.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/create-field

    """

    type: str
    values: dict[str, list] | list | None = None
    defaults: list | None = None
    need_validation: bool | None = None

    def _to_request(self) -> dict[str, Any]:
        """Render the drop-down list the way a request wants it.

        Only `type` and `values` are documented as request keys of
        `optionsProvider` (see the create-field, create-local-field and
        patch-issue-field-value pages), so a provider read back from a
        field can be modified and passed straight into the next request
        without the read-only `needValidation` (and the undocumented
        `defaults`) leaking into the body. Unset fields are dropped.
        """
        encoded: dict[str, Any] = {"type": self.type}
        if self.values is not None:
            encoded["values"] = self.values
        return encoded
