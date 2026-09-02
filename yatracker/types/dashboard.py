from __future__ import annotations

__all__ = [
    "CycleTimeWidget",
    "Dashboard",
    "WidgetBucket",
    "WidgetCalendarRef",
    "WidgetDatasetInfo",
    "WidgetLines",
]

from datetime import datetime
from typing import Any

from .base import Base, field, url_field
from .ref import Ref
from .status import Status
from .user import User


class Dashboard(Base):
    """Dashboard holding widgets.

    Attributes
    ----------
    url - Reference to the object.
    id - Dashboard ID.
    version - Dashboard version. Each change increments it.
    name - Dashboard name.
    created_by - User who created the dashboard.
    created_at - Moment the dashboard was created.
    layout - How the widgets are laid out: `one-column`,
    `two-columns`, `three-columns`, `narrow-left-wide-right` or
    `one-top-two-bottom`.
    owner - Owner of the dashboard.

    Source:
    https://yandex.ru/support/tracker/ru/api/dashboards/create-dashboard

    """

    url: str = url_field()
    id: str
    version: int
    name: str
    created_by: User
    created_at: datetime
    layout: str | None = None
    owner: User | None = None


class WidgetBucket(Base):
    """Step size of a cycle time chart.

    The request calls the grouping period `unit` while the response
    calls it `type`; both name the same thing.

    Attributes
    ----------
    type - Grouping period: `days`, `weeks`, `months` or `sprints`.
    count - Number of periods. Always 1 for `sprints`.
    board_id - ID of the board, only for `sprints`.

    Source:
    https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

    """

    type: str | None = None
    count: int | None = None
    board_id: str | None = None


class WidgetLines(Base):
    """Time axis settings of a cycle time chart.

    Attributes
    ----------
    moving_average - Whether the moving average line is shown.
    standard_deviation - Whether the standard deviation band is shown.
    percentile - Percentiles the chart is built for.
    cake_percentile - Percentile used for the per-status chart.

    Source:
    https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

    """

    moving_average: bool | None = None
    standard_deviation: bool | None = None
    percentile: list[float] | None = None
    cake_percentile: float | None = None


class WidgetCalendarRef(Base):
    """Working-time calendar of a cycle time widget.

    Unlike :class:`Ref`, the object carries no `self` link.

    Attributes
    ----------
    id - Calendar ID.
    display - Calendar name displayed in the interface.

    Source:
    https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

    """

    id: str
    display: str | None = None


class WidgetDatasetInfo(Base):
    """State of the widget data computation.

    Attributes
    ----------
    status - Status of the computation.
    build_started_at - Moment the computation started.
    built_by - User the computation runs on behalf of.

    Source:
    https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

    """

    status: str | None = None
    build_started_at: datetime | None = None
    built_by: User | None = None


class CycleTimeWidget(Base):
    """Cycle time chart widget placed on a dashboard.

    Attributes
    ----------
    url - Reference to the object.
    id - Widget ID.
    version - Widget version.
    description - Widget name.
    created_by - User who created the widget.
    color - Service parameter.
    dashboard - Dashboard the widget is placed on.
    from_statuses - Statuses the work on an issue starts from.
    to_statuses - Statuses the work on an issue ends at.
    excluded_statuses - Statuses excluded from the computation. Not
    shown in the response sample of the reference.
    included_statuses - Statuses added to the computation. Not shown in
    the response sample of the reference.
    bucket - Step size of the chart.
    calendar - Working-time calendar used for the computation.
    query - Issue filter in the query language.
    filter_ - Issue filter by fields (sent and returned as `filter`).
    filter_id - ID of the saved filter the widget is built on.
    dataset_info - State of the widget data computation.
    lines - Time axis settings.
    start - Formula for the start of the computed period, e.g.
    `now()-2w`.
    end - Formula for the end of the computed period, e.g. `now()-2d`.
    mode - How the data is displayed: `common-lines`,
    `common-lines-and-points` or `status-lines`.

    Source:
    https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

    """

    url: str = url_field()
    id: str
    version: int
    description: str
    created_by: User | None = None
    color: int | None = None
    dashboard: Ref | None = None
    from_statuses: list[Status] | None = None
    to_statuses: list[Status] | None = None
    excluded_statuses: list[Status] | None = None
    included_statuses: list[Status] | None = None
    bucket: WidgetBucket | None = None
    calendar: WidgetCalendarRef | None = None
    query: str | None = None
    filter_: dict[str, Any] | None = field(default=None, alias="filter")
    filter_id: str | None = None
    dataset_info: WidgetDatasetInfo | None = None
    lines: WidgetLines | None = None
    start: str | None = None
    end: str | None = None
    mode: str | None = None
