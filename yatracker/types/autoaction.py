from __future__ import annotations

__all__ = [
    "Autoaction",
    "AutoactionCalendar",
    "AutoactionIssueRef",
    "AutoactionLaunch",
    "AutoactionLaunchResult",
    "AutoactionLaunchStatus",
]

from datetime import datetime
from typing import Any

from .base import Base, field, url_field
from .queue import Queue
from .ref import Ref
from .trigger import TriggerAction


class AutoactionCalendar(Base):
    """Working schedule during which an autoaction is active.

    Attributes
    ----------
    id - ID of the working schedule.

    """

    id: str


class Autoaction(Base):
    """Represents a queue autoaction.

    An autoaction periodically applies `actions` to every issue matched
    by `filter_` or `query`.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-autoaction

    Attributes
    ----------
    url - Reference to the autoaction.
    id - Autoaction ID.
    queue - Queue the autoaction belongs to.
    name - Autoaction name.
    version - Autoaction version, incremented by every change.
    active - Whether the autoaction is active.
    created - When the autoaction was created.
    updated - When the autoaction was last changed.
    filter_ - Filter of the issues the autoaction is applied to, a
    mapping of field key to the accepted values, e.g.
    `{"priority": ["critical"]}`. Sent and received as `filter`.
    query - Query-language string filtering the issues instead of (or
    together with) `filter_`.
    actions - Actions applied to every matched issue.
    enable_notifications - Whether notifications are sent.
    last_launch - When the autoaction was last launched.
    total_issues_processed - Number of issues checked during the last
    launch.
    interval_millis - How often the autoaction runs, in milliseconds
    (3600000, i.e. once an hour, by default).
    calendar - Working schedule during which the autoaction is active.

    """

    url: str = url_field()
    id: str
    queue: Queue
    name: str
    version: int
    active: bool
    created: datetime
    updated: datetime
    filter_: dict[str, Any] | None = field(default=None, alias="filter")
    query: str | None = None
    actions: list[TriggerAction] = field(default_factory=list)
    enable_notifications: bool | None = None
    last_launch: datetime | None = None
    total_issues_processed: int | None = None
    interval_millis: int | None = None
    calendar: AutoactionCalendar | None = None


class AutoactionLaunch(Base):
    """One launch of an autoaction.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs

    Attributes
    ----------
    id - ID of the launch. Pass it to `get_autoaction_launch` to get the
    per-issue results.
    launch_time - When the launch started.
    search_hits - Number of issues processed by the autoaction.
    successes - Number of issues the autoaction succeeded on.
    failures - Number of issues the autoaction failed on.
    search_failed - `True` when not a single issue was processed.

    """

    id: str
    launch_time: datetime | None = None
    search_hits: int | None = None
    successes: int | None = None
    failures: int | None = None
    search_failed: bool | None = None


class AutoactionIssueRef(Ref):
    """Short issue reference embedded into an autoaction launch result.

    Attributes
    ----------
    url - Reference to the issue.
    id - Issue ID.
    display - Issue name displayed in the interface.
    key - Issue key.
    version - Issue version, incremented by every change.

    """

    key: str | None = None
    version: int | None = None


class AutoactionLaunchStatus(Base):
    """Result of an autoaction on a single issue.

    Attributes
    ----------
    value - Status value, e.g. `success`.
    display - Status name displayed in the interface.

    """

    value: str
    display: str | None = None


class AutoactionLaunchResult(Base):
    """What an autoaction did to one issue during a launch.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs

    Attributes
    ----------
    id - Zero-based ordinal number of the autoaction firing.
    issue_reference - The issue the autoaction was applied to.
    status - Result of the autoaction on that issue.

    """

    id: int
    issue_reference: AutoactionIssueRef | None = None
    status: AutoactionLaunchStatus | None = None
