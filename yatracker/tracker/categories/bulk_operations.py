from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from yatracker.exceptions import ObjectNotFoundError
from yatracker.tracker.base import BaseTracker, _convert_value
from yatracker.types import BulkChange, BulkChangeIssue
from yatracker.utils.camel_case import camel_case

if TYPE_CHECKING:
    from collections.abc import Sequence

    from yatracker.types import FullIssue, FullQueue, Issue, Queue, Transition

# The API may answer 404 for an existing operation id: right after creation
# for a short while, and occasionally later when a poll lands on a lagging
# replica. This many 404 answers are tolerated over the whole wait; the budget
# is never replenished, so a genuinely missing operation still surfaces.
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
                       Note that a bare key like `"TEST-1"` is a full-text
                       search, not a key match — use `"Key: TEST-1"` or
                       pass a list.
        :param values: Fields to set, in the `edit_issue` format. Supports
                       `{"tags": {"add": [...], "remove": [...]}}` operators.
                       Snake_case keys are converted to camelCase; keys
                       that are not Python identifiers (e.g. local field
                       ids like `"<id>--name"`) are sent as is.
        :param notify: Whether to notify the issue subscribers.
        :param kwargs: Extra fields merged on top of `values`, encoded the
                       same way. `None` values are dropped; to clear a
                       field, pass it via `values`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-update-issues
        """
        if isinstance(issues, str):
            if not issues.strip():
                msg = "The issues filter must not be empty."
                raise ValueError(msg)
            prepared_issues: list[str] | str = issues
        else:
            prepared_issues = _prepare_issue_keys(issues)

        prepared_values = _prepare_values(values, kwargs)
        if not prepared_values:
            msg = (
                "Bulk update requires at least one field, "
                "passed via `values` or as a keyword argument."
            )
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

        :param issues: Sequence of issue keys (or `Issue` objects). Unlike
                       `bulk_update_issues`, a filter string is not
                       supported by this endpoint (`TypeError`).
        :param transition: Transition id (or a `Transition` object).
        :param values: Fields to set while performing the transition,
                       e.g. `{"resolution": "fixed"}`.
        :param notify: Whether to notify the issue subscribers.
        :param kwargs: Extra fields merged on top of `values`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-transition
        """
        payload: dict[str, Any] = {
            "transition": transition if isinstance(transition, str) else transition.id,
            "issues": _prepare_issue_keys(issues),
        }

        prepared_values = _prepare_values(values, kwargs)
        if prepared_values:
            payload["values"] = prepared_values

        data = await self._client.request(
            method="POST",
            uri="/bulkchange/_transition",
            params=_notify_params(notify=notify),
            payload=payload,
        )
        return self._decode(BulkChange, data)

    async def bulk_move_issues(  # noqa: PLR0913
        self,
        issues: Sequence[str | Issue | FullIssue],
        queue: str | Queue | FullQueue,
        values: dict[str, Any] | None = None,
        *,
        move_all_fields: bool | None = None,
        initial_status: bool | None = None,
        notify: bool | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> BulkChange:
        """Move multiple issues to another queue at once.

        :param issues: Sequence of issue keys (or `Issue` objects). Unlike
                       `bulk_update_issues`, a filter string is not
                       supported by this endpoint (`TypeError`).
        :param queue: Target queue key (or a `Queue`/`FullQueue` object).
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
            "queue": queue if isinstance(queue, str) else queue.key,
            "issues": _prepare_issue_keys(issues),
        }

        prepared_values = _prepare_values(values, kwargs)
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

    async def get_bulk_change(self, bulk_change: str | BulkChange) -> BulkChange:
        """Get the current state of a bulk change operation.

        :param bulk_change: Id of the operation (or a `BulkChange` object).

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info
        """
        data = await self._client.request(
            method="GET",
            uri=f"/bulkchange/{_bulk_change_id(bulk_change)}",
        )
        return self._decode(BulkChange, data)

    async def get_bulk_change_issues(
        self,
        bulk_change: str | BulkChange,
    ) -> list[BulkChangeIssue]:
        """Get the issues a bulk change operation failed to process.

        The API returns only the issues for which the operation finished
        with an error, along with the error details. Successfully
        processed issues are not listed.

        :param bulk_change: Id of the operation (or a `BulkChange` object).

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info
        """
        data = await self._client.request(
            method="GET",
            uri=f"/bulkchange/{_bulk_change_id(bulk_change)}/issues",
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

        Only `COMPLETE` and `FAILED` are treated as terminal (the same
        pair the official client relies on). With the default
        `timeout=None` the wait is unbounded, so pass an explicit
        `timeout` in unattended code.

        :param bulk_change: Id of the operation (or a `BulkChange` object).
                            An already finished object is returned as is.
        :param interval: Delay between status checks (seconds).
        :param timeout: Maximum time to wait (seconds), `None` for no limit.
                        The deadline is checked between status requests,
                        so an in-flight request is not interrupted.
        :raises TimeoutError: If the operation is not finished in time.
                              Transport errors of the status requests
                              (including the client's own timeouts)
                              propagate unchanged.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info
        """
        if interval <= 0:
            msg = "`interval` must be greater than zero."
            raise ValueError(msg)

        if timeout is not None and timeout <= 0:
            msg = "`timeout` must be greater than zero."
            raise ValueError(msg)

        if isinstance(bulk_change, BulkChange) and bulk_change.is_finished:
            # A hand-made model (e.g. restored from storage) has no tracker
            # yet; adopt it so the shortcuts keep working.
            if bulk_change._tracker is None:  # noqa: SLF001
                bulk_change._tracker = self  # noqa: SLF001
            return bulk_change

        return await self._wait_bulk_change(
            _bulk_change_id(bulk_change),
            interval,
            timeout,
        )

    async def _wait_bulk_change(
        self,
        bulk_change_id: str,
        interval: float,
        timeout: float | None,
    ) -> BulkChange:
        """Poll the operation until it reaches a terminal status."""
        loop = asyncio.get_running_loop()
        deadline = None if timeout is None else loop.time() + timeout
        not_found_budget = NOT_FOUND_RETRIES

        while True:
            try:
                bulk_change = await self.get_bulk_change(bulk_change_id)
            except ObjectNotFoundError:
                if not_found_budget <= 0:
                    raise
                not_found_budget -= 1
            else:
                if bulk_change.is_finished:
                    return bulk_change

            if deadline is None:
                await asyncio.sleep(interval)
                continue

            remaining = deadline - loop.time()
            if remaining <= 0:
                msg = f"Bulk change operation is not finished in {timeout} seconds."
                raise TimeoutError(msg)
            await asyncio.sleep(min(interval, remaining))


def _prepare_values(
    values: dict[str, Any] | None,
    kwargs: dict[str, Any],
) -> dict[str, Any]:
    """Merge explicit `values` with the fields passed as keyword arguments.

    Top-level keys of both sources are encoded the same way, so a field
    passed twice ends up as a single key with the `kwargs` value winning.
    `None` keyword arguments are dropped, like in `edit_issue`.
    """
    prepared = {
        _encode_key(key): _convert_value(value) for key, value in (values or {}).items()
    }
    prepared.update(
        {
            _encode_key(key): _convert_value(value)
            for key, value in kwargs.items()
            if value is not None
        },
    )
    return prepared


def _encode_key(key: str) -> str:
    """Convert a snake_case field name to camelCase, keeping raw ids intact.

    Local field keys look like `"<id>--name"` and must not be touched;
    the same goes for anything else that is not a plain identifier.
    """
    if key.isidentifier() and not key.startswith("_"):
        return camel_case(key)
    return key


def _prepare_issue_keys(issues: Sequence[str | Issue | FullIssue] | str) -> list[str]:
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


def _bulk_change_id(bulk_change: str | BulkChange) -> str:
    """Extract the operation id from an id string or a `BulkChange` object."""
    return bulk_change if isinstance(bulk_change, str) else bulk_change.id


def _notify_params(*, notify: bool | None) -> dict[str, str] | None:
    """Build query params for the `notify` flag."""
    if notify is None:
        return None
    return {"notify": str(notify).lower()}
