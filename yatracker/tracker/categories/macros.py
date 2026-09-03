from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker, _encode_key
from yatracker.types import Macro

if TYPE_CHECKING:
    from collections.abc import Iterable

    from yatracker.types import MacroFieldChange


def _encode_issue_update(
    issue_update: dict[str, Any] | Iterable[MacroFieldChange] | None,
) -> dict[str, Any] | None:
    """Bring `issue_update` to the request format.

    Accepts either the request dict keyed by field id or the response
    entries (`Macro.issue_update`), so a macro can be re-sent as is.
    Identifier keys are camel-cased like in `bulk_update_issues`
    (``story_points`` -> ``storyPoints``); local-field ids such as
    ``<id>--userId`` are kept verbatim. Values, including ``None``
    (which clears the field), are left untouched.
    """
    if issue_update is None:
        return None
    if not isinstance(issue_update, dict):
        issue_update = {change.field.id: change.update for change in issue_update}
    return {_encode_key(key): value for key, value in issue_update.items()}


class Macros(BaseTracker):
    async def get_macros(
        self,
        queue_id: str | int,
        per_page: int | None = None,
        page: int | None = None,
    ) -> list[Macro]:
        """Get macros of a queue.

        Use this request to get a list of all macros of the queue.
        The endpoint reference lists no pagination parameters, but
        Tracker pages every list response by 50 objects; pass
        `per_page` / `page` to fetch the rest.

        Source:
        https://yandex.ru/support/tracker/ru/api/get-macroses

        :param queue_id: ID or key of the queue.
        :param per_page: number of macros per page (50 by default).
        :param page: page number (1 by default).
        :return: list of macros of the queue.
        """
        params = {}
        if per_page is not None:
            params["perPage"] = str(per_page)
        if page is not None:
            params["page"] = str(page)

        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/macros",
            params=params or None,
        )
        return self._decode(list[Macro], data)

    async def get_macro(self, queue_id: str | int, macro_id: str | int) -> Macro:
        """Get a macro.

        Source:
        https://yandex.ru/support/tracker/ru/api/get-macros

        :param queue_id: ID or key of the queue.
        :param macro_id: ID of the macro.
        :return: macro.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/macros/{macro_id}",
        )
        return self._decode(Macro, data)

    async def create_macro(
        self,
        queue_id: str | int,
        name: str,
        *,
        body: str | None = None,
        issue_update: dict[str, Any] | Iterable[MacroFieldChange] | None = None,
    ) -> Macro:
        """Create a macro.

        Source:
        https://yandex.ru/support/tracker/ru/api/post-macros

        :param queue_id: ID or key of the queue.
        :param name: macro name.
        :param body: text of the comment added when the macro runs.
            Supports the `{{currentUser}}`, `{{currentDateTime}}` and
            `{{issue.author}}` placeholders.
        :param issue_update: changes applied to the issue fields, a dict
            keyed by field id. A value is either the new value itself
            (`{"description": "New task"}`) or an operation
            (`{"tags": {"add": "New tag"}}`, also `set` and `remove`);
            `None` clears the field (`{"resolution": None}`). Keys are
            camel-cased like in `bulk_update_issues`. The entries of
            another macro's `issue_update` are accepted as well.
        :return: created macro.
        """
        issue_update = _encode_issue_update(issue_update)
        payload = self._prepare_payload(locals(), exclude=["queue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/queues/{queue_id}/macros",
            payload=payload,
        )
        return self._decode(Macro, data)

    async def update_macro(
        self,
        queue_id: str | int,
        macro_id: str | int,
        name: str,
        *,
        body: str | dict[str, Any] | None = None,
        issue_update: dict[str, Any] | Iterable[MacroFieldChange] | None = None,
    ) -> Macro:
        """Edit a macro.

        Source:
        https://yandex.ru/support/tracker/ru/api/patch-macros

        :param queue_id: ID or key of the queue.
        :param macro_id: ID of the macro to edit.
        :param name: macro name. The API requires it even when only
            other fields are changed.
        :param body: new text of the comment added when the macro runs.
            Supports the `{{currentUser}}`, `{{currentDateTime}}` and
            `{{issue.author}}` placeholders. Pass `{"unset": 1}` to
            remove the comment text.
        :param issue_update: the field changes the macro should apply,
            in the same format as in `create_macro`. Treat it as the
            whole set rather than a patch: the API does not document
            merging with the existing changes, so start from
            `macro.issue_update_payload()` (or pass `macro.issue_update`
            itself) to keep them.

        `body` and `issue_update` left as ``None`` are not sent, i.e.
        they stay unchanged.

        :return: updated macro.
        """
        issue_update = _encode_issue_update(issue_update)
        payload = self._prepare_payload(
            locals(),
            exclude=["queue_id", "macro_id"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/queues/{queue_id}/macros/{macro_id}",
            payload=payload,
        )
        return self._decode(Macro, data)

    async def delete_macro(self, queue_id: str | int, macro_id: str | int) -> bool:
        """Delete a macro.

        Source:
        https://yandex.ru/support/tracker/ru/api/delete-macros

        :param queue_id: ID or key of the queue.
        :param macro_id: ID of the macro to delete.
        :return: True if the macro was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/queues/{queue_id}/macros/{macro_id}",
        )
        return True
