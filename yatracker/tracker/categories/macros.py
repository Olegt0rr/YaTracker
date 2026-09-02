from __future__ import annotations

from typing import Any

from yatracker.tracker.base import BaseTracker
from yatracker.types import Macro


class Macros(BaseTracker):
    async def get_macros(self, queue_id: str | int) -> list[Macro]:
        """Get macros of a queue.

        Use this request to get a list of all macros of the queue.

        Source:
        https://yandex.ru/support/tracker/ru/get-macroses

        :param queue_id: ID or key of the queue.
        :return: list of macros of the queue.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/macros",
        )
        return self._decode(list[Macro], data)

    async def get_macro(self, queue_id: str | int, macro_id: str | int) -> Macro:
        """Get a macro.

        Source:
        https://yandex.ru/support/tracker/ru/get-macros

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
        issue_update: dict[str, Any] | None = None,
    ) -> Macro:
        """Create a macro.

        Source:
        https://yandex.ru/support/tracker/ru/post-macros

        :param queue_id: ID or key of the queue.
        :param name: macro name.
        :param body: text of the comment added when the macro runs.
            Supports the `{{currentUser}}`, `{{currentDateTime}}` and
            `{{issue.author}}` placeholders.
        :param issue_update: changes applied to the issue fields, a dict
            keyed by field id. A value is either the new value itself
            (`{"description": "New task"}`) or an operation
            (`{"tags": {"add": "New tag"}}`, also `set` and `remove`);
            `None` clears the field (`{"resolution": None}`).
        :return: created macro.
        """
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
        issue_update: dict[str, Any] | None = None,
    ) -> Macro:
        """Edit a macro.

        Source:
        https://yandex.ru/support/tracker/ru/patch-macros

        :param queue_id: ID or key of the queue.
        :param macro_id: ID of the macro to edit.
        :param name: macro name. The API requires it even when only
            other fields are changed.
        :param body: new text of the comment added when the macro runs.
            Supports the `{{currentUser}}`, `{{currentDateTime}}` and
            `{{issue.author}}` placeholders. Pass `{"unset": 1}` to
            remove the comment text.
        :param issue_update: changes applied to the issue fields, a dict
            keyed by field id. A value is either the new value itself
            (`{"description": "New task"}`) or an operation
            (`{"tags": {"add": "New tag"}}`, also `set` and `remove`);
            `None` clears the field (`{"resolution": None}`).

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated macro.
        """
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
        https://yandex.ru/support/tracker/ru/delete-macros

        :param queue_id: ID or key of the queue.
        :param macro_id: ID of the macro to delete.
        :return: True if the macro was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/queues/{queue_id}/macros/{macro_id}",
        )
        return True
