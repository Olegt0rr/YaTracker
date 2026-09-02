from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.autoaction import (
    Autoaction,
    AutoactionLaunch,
    AutoactionLaunchResult,
)

if TYPE_CHECKING:
    from yatracker.types.autoaction import AutoactionCalendar
    from yatracker.types.trigger import TriggerAction


class Autoactions(BaseTracker):
    async def get_autoaction(
        self,
        queue_id: str | int,
        autoaction_id: str | int,
    ) -> Autoaction:
        """Get an autoaction.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-autoaction

        :param queue_id: ID or key of the queue.
        :param autoaction_id: ID of the autoaction.
        :return: autoaction.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/autoactions/{autoaction_id}",
        )
        return self._decode(Autoaction, data)

    async def create_autoaction(  # noqa: PLR0913
        self,
        queue_id: str | int,
        name: str,
        actions: list[TriggerAction | dict[str, Any]],
        *,
        filter_: dict[str, Any] | None = None,
        query: str | None = None,
        active: bool | None = None,
        enable_notifications: bool | None = None,
        interval_millis: int | None = None,
        calendar: AutoactionCalendar | dict[str, Any] | None = None,
    ) -> Autoaction:
        """Create an autoaction.

        At least one of `filter_` and `query` has to be given, otherwise
        the API would not know which issues to act on.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/create-autoaction

        :param queue_id: ID or key of the queue.
        :param name: autoaction name.
        :param actions: actions applied to every matched issue, see
            `TriggerAction` and
            https://yandex.ru/support/tracker/ru/api/queues/change-trigger-actions
            Autoactions support the `Transition`, `Update`,
            `CreateComment`, `Webhook` and `CalculateFormula` kinds.
        :param filter_: filter of the issues to act on, a mapping of
            field key to the accepted values, e.g.
            `{"priority": ["critical"], "status": ["inProgress"]}`.
            Sent as `filter`.
        :param query: query-language string filtering the issues, e.g.
            `'"Status": "In progress"'`.
        :param active: whether the autoaction is active.
        :param enable_notifications: whether notifications are sent.
        :param interval_millis: how often the autoaction runs, in
            milliseconds (3600000, i.e. once an hour, by default).
        :param calendar: working schedule during which the autoaction is
            active, an object with the schedule `id`.
        :return: created autoaction.
        """
        if filter_ is None and query is None:
            msg = "Pass at least one of `filter_` and `query`."
            raise ValueError(msg)

        payload = self._prepare_payload(locals(), exclude=["queue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/queues/{queue_id}/autoactions",
            payload=payload,
        )
        return self._decode(Autoaction, data)

    async def get_autoaction_logs(
        self,
        queue_id: str | int,
        autoaction_id: str | int,
    ) -> list[AutoactionLaunch]:
        """Get the launches of an autoaction.

        The endpoint documents neither pagination nor filtering
        parameters.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs

        :param queue_id: ID or key of the queue.
        :param autoaction_id: ID of the autoaction.
        :return: list of autoaction launches.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/autoactions/{autoaction_id}/logs",
        )
        return self._decode(list[AutoactionLaunch], data)

    async def get_autoaction_log(
        self,
        queue_id: str | int,
        autoaction_id: str | int,
        launch_id: str | int,
    ) -> list[AutoactionLaunchResult]:
        """Get the per-issue results of one autoaction launch.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs

        :param queue_id: ID or key of the queue.
        :param autoaction_id: ID of the autoaction.
        :param launch_id: ID of the launch, as returned by
            `get_autoaction_logs`.
        :return: what the autoaction did to every issue of the launch.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/autoactions/{autoaction_id}/logs/{launch_id}",
        )
        return self._decode(list[AutoactionLaunchResult], data)
