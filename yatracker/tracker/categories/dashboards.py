from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.dashboard import CycleTimeWidget, Dashboard
from yatracker.types.status import Status

if TYPE_CHECKING:
    from collections.abc import Sequence

# ruff: noqa: PLR0913


def _encode_statuses(
    statuses: Sequence[str | Status | dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    """Bring a list of statuses to the request format.

    The API takes `[{"key": "open"}]`; a plain status key and a
    :class:`Status` object (so a widget can be re-sent as is) are
    accepted as well. Dicts are passed through verbatim.
    """
    if statuses is None:
        return None

    encoded: list[dict[str, Any]] = []
    for status in statuses:
        if isinstance(status, Status):
            encoded.append({"key": status.key})
        elif isinstance(status, str):
            encoded.append({"key": status})
        else:
            encoded.append(dict(status))
    return encoded


class Dashboards(BaseTracker):
    """Dashboards and their widgets."""

    async def create_dashboard(
        self,
        name: str,
        *,
        layout: str | None = None,
        owner: str | int | dict[str, Any] | None = None,
    ) -> Dashboard:
        """Create a dashboard.

        Source:
        https://yandex.ru/support/tracker/ru/api/dashboards/create-dashboard

        :param name: dashboard name.
        :param layout: how the widgets are laid out: "one-column"
            (default), "two-columns", "three-columns",
            "narrow-left-wide-right" or "one-top-two-bottom".
        :param owner: login or id of the dashboard owner; it is wrapped
            into `{"id": ...}` the way the reference sample shows, and a
            ready-made dict is sent as is. The creator becomes the owner
            when omitted.
        :return: created dashboard.
        """
        if owner is not None and not isinstance(owner, dict):
            owner = {"id": str(owner)}

        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/dashboards/",
            payload=payload,
        )
        return self._decode(Dashboard, data)

    async def create_cycle_time_widget(
        self,
        dashboard_id: str | int,
        description: str,
        *,
        query: str | None = None,
        filter_: dict[str, Any] | None = None,
        filter_id: str | int | None = None,
        from_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
        to_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
        excluded_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
        included_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
        bucket: dict[str, Any] | None = None,
        calendar: str | int | None = None,
        lines: dict[str, Any] | None = None,
        start: str | None = None,
        end: str | None = None,
        mode: str | None = None,
        auto_updatable: bool | None = None,
        **kwargs,
    ) -> CycleTimeWidget:
        """Add a "cycle time" chart widget to an existing dashboard.

        When several issue sources are given at once, the API picks one
        of them in this order: `filter_id`, `query`, `filter_`.

        Source:
        https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

        :param dashboard_id: ID of the dashboard to add the widget to.
        :param description: widget name.
        :param query: issue filter in the query language.
        :param filter_: issue filter by fields, e.g.
            `{"queue": "TEST", "assignee": "username"}` (sent as
            `filter`).
        :param filter_id: ID of a saved filter.
        :param from_statuses: statuses the work on an issue starts
            from; the time spent in them is not counted. Either status
            keys or `{"key": ...}` dicts. The first status of the issue
            history by default.
        :param to_statuses: statuses the work on an issue ends at; the
            latest one the issue entered is used. The last status of the
            issue history by default.
        :param excluded_statuses: statuses whose time is removed from
            the computation.
        :param included_statuses: statuses whose time is added to the
            computation.
        :param bucket: step size, e.g. `{"unit": "days", "count": 1}`;
            `unit` is "days", "weeks", "months" or "sprints" and
            `boardId` is accepted for "sprints". 7 days by default.
        :param calendar: ID of the working-time calendar. The plain
            calendar is used when omitted.
        :param lines: time axis settings, e.g. `{"movingAverage": True,
            "standardDeviation": True, "percentile": [75, 90],
            "cakePercentile": 85}`.
        :param start: formula for the start of the computed period, e.g.
            "now()-2w". Two years by default.
        :param end: formula for the end of the computed period, e.g.
            "now()-2d". "now()" by default.
        :param mode: how the data is displayed: "common-lines",
            "common-lines-and-points" or "status-lines".
        :param auto_updatable: whether the chart is updated
            automatically.
        :param kwargs: any other widget field.
        :return: created widget.
        """
        from_statuses = _encode_statuses(from_statuses)
        to_statuses = _encode_statuses(to_statuses)
        excluded_statuses = _encode_statuses(excluded_statuses)
        included_statuses = _encode_statuses(included_statuses)

        payload = self._prepare_payload(locals(), exclude=["dashboard_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/dashboards/{dashboard_id}/widgets/cycleTime",
            payload=payload,
        )
        return self._decode(CycleTimeWidget, data)
