from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.trigger import Trigger, TriggerWebhookLog

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from datetime import datetime

    from yatracker.types.trigger import TriggerAction, TriggerCondition


def _format_time(value: str | datetime | None) -> str | None:
    """Render a log time bound the way the API expects it.

    The docs use `YYYY-MM-DDThh:mm:ss.sss±hhmm`, which `datetime.isoformat`
    produces, while `str(datetime)` would send a space instead of `T`.
    Strings are passed through untouched.
    """
    if value is None or isinstance(value, str):
        return value
    return value.isoformat()


class Triggers(BaseTracker):
    async def get_triggers(
        self,
        queue_id: str | int,
        per_page: int | None = None,
        id_: str | int | None = None,
    ) -> list[Trigger]:
        """Get one page of the triggers of a queue.

        The endpoint uses relative pagination: triggers are sorted by id
        in ascending order, so the next page is requested with the id of
        the last trigger of the current one. Use :meth:`iter_triggers`
        to walk over all of them.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-triggers

        :param queue_id: ID or key of the queue.
        :param per_page: number of triggers per page.
        :param id_: id of the last trigger of the previous page
            (query param "id"). Omit it to get the first page.
        :return: list of triggers.
        """
        params = self._prepare_params(per_page=per_page, id=id_)
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/triggers",
            params=params,
        )
        return self._decode(list[Trigger], data)

    async def iter_triggers(
        self,
        queue_id: str | int,
        per_page: int | None = None,
    ) -> AsyncIterator[Trigger]:
        """Iterate over all triggers of a queue, page by page.

        Wraps :meth:`get_triggers`: every page is requested with the id
        of the last trigger of the previous one, and iteration stops as
        soon as a page comes back empty or does not advance past that
        id. The docs describe the `id` cursor as the trigger the next
        page *starts from*, so if the cursor trigger comes back at the
        top of a page it is not yielded twice.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-triggers

        :param queue_id: ID or key of the queue.
        :param per_page: number of triggers per page.
        """
        id_: str | None = None
        while True:
            triggers = await self.get_triggers(queue_id, per_page=per_page, id_=id_)
            # A page that does not advance past the cursor is either the
            # last one (inclusive cursor) or a server ignoring `id`:
            # stop instead of looping forever.
            if not triggers or triggers[-1].id == id_:
                return

            for trigger in triggers:
                if trigger.id != id_:
                    yield trigger

            id_ = triggers[-1].id

    async def get_trigger(
        self,
        queue_id: str | int,
        trigger_id: str | int,
    ) -> Trigger:
        """Get a trigger.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-trigger

        :param queue_id: ID or key of the queue.
        :param trigger_id: ID of the trigger.
        :return: trigger.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/triggers/{trigger_id}",
        )
        return self._decode(Trigger, data)

    async def create_trigger(
        self,
        queue_id: str | int,
        name: str,
        actions: list[TriggerAction | dict[str, Any]],
        *,
        conditions: list[TriggerCondition | dict[str, Any]] | None = None,
        active: bool | None = None,
    ) -> Trigger:
        """Create a trigger.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/create-trigger

        :param queue_id: ID or key of the queue.
        :param name: trigger name.
        :param actions: actions performed by the trigger, see
            `TriggerAction` and
            https://yandex.ru/support/tracker/ru/api/queues/change-trigger-actions
        :param conditions: conditions that make the trigger fire, see
            `TriggerCondition` and
            https://yandex.ru/support/tracker/ru/api/queues/change-trigger-conditions
            A flat list means every condition has to hold (logical AND);
            wrap them into a single `{"type": "Or", "conditions": [...]}`
            group to fire on any of them.
        :param active: whether the trigger is active.
        :return: created trigger.
        """
        payload = self._prepare_payload(locals(), exclude=["queue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/queues/{queue_id}/triggers",
            payload=payload,
        )
        return self._decode(Trigger, data)

    async def update_trigger(  # noqa: PLR0913
        self,
        queue_id: str | int,
        trigger_id: str | int,
        version: str | int,
        *,
        name: str | None = None,
        actions: list[TriggerAction | dict[str, Any]] | None = None,
        conditions: list[TriggerCondition | dict[str, Any]] | None = None,
        active: bool | None = None,
        before: str | int | None = None,
    ) -> Trigger:
        """Edit a trigger.

        Unlike sprints or board columns, a trigger carries its version
        in the `version` query parameter instead of the `If-Match`
        header; the API answers 409 when the version is stale. Fields
        left as `None` are not sent and stay unchanged, but `actions`
        and `conditions` replace the existing ones as a whole.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/change-trigger

        :param queue_id: ID or key of the queue.
        :param trigger_id: ID of the trigger to edit.
        :param version: current version of the trigger.
        :param name: new trigger name.
        :param actions: new actions of the trigger, see `TriggerAction`.
        :param conditions: new conditions of the trigger, see
            `TriggerCondition`.
        :param active: whether the trigger is active.
        :param before: ID of the trigger this one should be placed
            before.
        :return: updated trigger.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["queue_id", "trigger_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/queues/{queue_id}/triggers/{trigger_id}",
            params=self._prepare_params(version=version),
            payload=payload,
        )
        return self._decode(Trigger, data)

    async def get_trigger_logs(  # noqa: PLR0913
        self,
        queue_id: str | int,
        trigger_id: str | int,
        *,
        issue_id: str | None = None,
        limit: int | None = None,
        from_: str | datetime | None = None,
        to: str | datetime | None = None,
    ) -> list[TriggerWebhookLog]:
        """Get the logs of the HTTP-request actions of a trigger.

        Only the `Webhook` action is logged. The endpoint is not
        paginated: it returns the 10 most recent entries by default,
        pass `limit` (100 at most) to get more.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/view-trigger-logs

        :param queue_id: ID or key of the queue.
        :param trigger_id: ID of the trigger.
        :param issue_id: key or ID of the issue to filter the logs by.
        :param limit: number of entries in the response (10 by default,
            100 at most).
        :param from_: start of the time range, a `datetime` or a string
            formatted as `YYYY-MM-DDThh:mm:ss.sss±hhmm` (query param
            "from").
        :param to: end of the time range, in the same format.
        :return: list of log entries, most recent first.
        """
        params = self._prepare_params(
            issue_id=issue_id,
            limit=limit,
            from_=_format_time(from_),
            to=_format_time(to),
        )
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/triggers/{trigger_id}/webhooks/log",
            params=params,
        )
        return self._decode(list[TriggerWebhookLog], data)
