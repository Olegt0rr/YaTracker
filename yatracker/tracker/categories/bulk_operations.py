from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from yatracker.exceptions import ObjectNotFoundError
from yatracker.tracker.base import BaseTracker, _convert_value
from yatracker.types import BulkChange, BulkChangeIssue, Queue, Transition

if TYPE_CHECKING:
    from collections.abc import Sequence

    from yatracker.types import FullIssue, Issue

NOT_FOUND_RETRIES = 10


class BulkChanges(BaseTracker):
    async def bulk_update_issues(
        self,
        issues: Sequence[str | Issue | FullIssue] | str,
        values: dict[str, Any] | None = None,
        *,
        notify: bool | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> BulkChange:
        """Edit multiple issues at once.

        :param issues: Sequence of issue keys (or `Issue` objects), or a
                       query-language filter string selecting the issues.
        :param values: Fields to set, in the `edit_issue` format. Supports
                       `{"tags": {"add": [...], "remove": [...]}}` operators.
        :param notify: Whether to notify the issue subscribers.
        :param kwargs: Extra fields merged on top of `values`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-update-issues
        """
        prepared_issues = _prepare_issues(issues)
        prepared_values = self._prepare_values(values, kwargs)
        if not prepared_values:
            msg = "Bulk update requires at least one field in `values`."
            raise ValueError(msg)

        payload: dict[str, Any] = {
            "issues": prepared_issues,
            "values": prepared_values,
        }
        data = await self._client.request(
            method="POST",
            uri="/bulkchange/_update",
            params=_notify_params(notify=notify),
            payload=payload,
        )
        return self._decode(BulkChange, data)

    async def bulk_transition_issues(
        self,
        issues: Sequence[str | Issue | FullIssue],
        transition: str | Transition,
        values: dict[str, Any] | None = None,
        *,
        notify: bool | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> BulkChange:
        """Move multiple issues to a new status at once.

        :param issues: Sequence of issue keys (or `Issue` objects).
        :param transition: Transition id (or a `Transition` object).
        :param values: Fields to set while performing the transition,
                       e.g. `{"resolution": "fixed"}`.
        :param notify: Whether to notify the issue subscribers.
        :param kwargs: Extra fields merged on top of `values`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-transition
        """
        payload: dict[str, Any] = {
            "transition": transition.id
            if isinstance(transition, Transition)
            else transition,
            "issues": _prepare_issue_keys(issues),
        }

        prepared_values = self._prepare_values(values, kwargs)
        if prepared_values:
            payload["values"] = prepared_values

        data = await self._client.request(
            method="POST",
            uri="/bulkchange/_transition",
            params=_notify_params(notify=notify),
            payload=payload,
        )
        return self._decode(BulkChange, data)

    # ruff: noqa: PLR0913
    async def bulk_move_issues(
        self,
        issues: Sequence[str | Issue | FullIssue],
        queue: str | Queue,
        values: dict[str, Any] | None = None,
        *,
        move_all_fields: bool | None = None,
        initial_status: bool | None = None,
        notify: bool | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> BulkChange:
        """Move multiple issues to another queue at once.

        :param issues: Sequence of issue keys (or `Issue` objects).
        :param queue: Target queue key (or a `Queue` object).
        :param values: Fields to set while moving the issues.
        :param move_all_fields: Move components, versions and projects
                                instead of clearing them.
        :param initial_status: Reset the issue status to the initial one.
        :param notify: Whether to notify the issue subscribers.
        :param kwargs: Extra fields merged on top of `values`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-issues
        """
        payload: dict[str, Any] = {
            "queue": queue.key if isinstance(queue, Queue) else queue,
            "issues": _prepare_issue_keys(issues),
        }

        prepared_values = self._prepare_values(values, kwargs)
        if prepared_values:
            payload["values"] = prepared_values

        if move_all_fields is not None:
            payload["moveAllFields"] = move_all_fields

        if initial_status is not None:
            payload["initialStatus"] = initial_status

        data = await self._client.request(
            method="POST",
            uri="/bulkchange/_move",
            params=_notify_params(notify=notify),
            payload=payload,
        )
        return self._decode(BulkChange, data)

    async def get_bulk_change(self, bulk_change_id: str) -> BulkChange:
        """Get the state of a bulk change operation.

        :param bulk_change_id: Id of the bulk change operation.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info
        """
        data = await self._client.request(
            method="GET",
            uri=f"/bulkchange/{bulk_change_id}",
        )
        return self._decode(BulkChange, data)

    async def get_bulk_change_issues(
        self,
        bulk_change_id: str,
    ) -> list[BulkChangeIssue]:
        """Get per-issue results of a bulk change operation.

        :param bulk_change_id: Id of the bulk change operation.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info
        """
        data = await self._client.request(
            method="GET",
            uri=f"/bulkchange/{bulk_change_id}/issues",
        )
        return self._decode(list[BulkChangeIssue], data)

    async def wait_bulk_change(
        self,
        bulk_change: str | BulkChange,
        *,
        interval: float = 1.0,
        timeout: float | None = None,
    ) -> BulkChange:
        """Wait until a bulk change operation reaches a terminal status.

        :param bulk_change: Id of the operation (or a `BulkChange` object).
        :param interval: Delay between status checks (seconds).
        :param timeout: Maximum time to wait (seconds), `None` for no limit.
        :raises TimeoutError: If the operation is not finished in time.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info
        """
        if interval <= 0:
            msg = "`interval` must be greater than zero."
            raise ValueError(msg)

        bulk_change_id = (
            bulk_change.id if isinstance(bulk_change, BulkChange) else bulk_change
        )
        waiter = self._wait_bulk_change(bulk_change_id, interval)
        if timeout is None:
            return await waiter
        return await asyncio.wait_for(waiter, timeout)

    async def _wait_bulk_change(
        self,
        bulk_change_id: str,
        interval: float,
    ) -> BulkChange:
        """Poll the operation until it reaches a terminal status."""
        not_found = 0
        while True:
            try:
                bulk_change = await self.get_bulk_change(bulk_change_id)
            except ObjectNotFoundError:
                # Right after creation the API may not know the operation yet.
                not_found += 1
                if not_found > NOT_FOUND_RETRIES:
                    raise
            else:
                not_found = 0
                if bulk_change.is_finished:
                    return bulk_change

            await asyncio.sleep(interval)

    def _prepare_values(
        self,
        values: dict[str, Any] | None,
        kwargs: dict[str, Any],
    ) -> dict[str, Any]:
        """Merge explicit `values` with the fields passed as keyword arguments."""
        prepared: dict[str, Any] = _convert_value(values or {})
        prepared.update(self._prepare_payload(kwargs))
        return prepared


def _prepare_issue_keys(issues: Sequence[str | Issue | FullIssue]) -> list[str]:
    """Convert a sequence of issues into a list of issue keys."""
    if isinstance(issues, str):
        msg = (
            "This endpoint accepts only a sequence of issue keys. "
            "A query filter string is supported by `bulk_update_issues` only."
        )
        raise TypeError(msg)

    keys = [issue if isinstance(issue, str) else issue.key for issue in issues]
    if not keys:
        msg = "At least one issue is required."
        raise ValueError(msg)
    return keys


def _prepare_issues(
    issues: Sequence[str | Issue | FullIssue] | str,
) -> list[str] | str:
    """Convert issues into a list of keys, passing a query filter through."""
    if isinstance(issues, str):
        return issues
    return _prepare_issue_keys(issues)


def _notify_params(*, notify: bool | None) -> dict[str, str] | None:
    """Build query params for the `notify` flag."""
    if notify is None:
        return None
    return {"notify": str(notify).lower()}
