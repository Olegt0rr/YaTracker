from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
from yatracker.types import Worklog
from yatracker.types.duration import Duration
from yatracker.utils.datetime import to_tracker_datetime

if TYPE_CHECKING:
    from datetime import datetime


class Worklogs(BaseTracker):
    async def post_worklog(
        self,
        issue_id: str,
        start: str | datetime,
        duration: str | Duration,
        comment: str | None = None,
    ) -> Worklog:
        """Add worklog to the issue.

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/new-worklog
        """
        start = to_tracker_datetime(start)

        if isinstance(duration, Duration):
            duration = duration.to_iso()

        payload = self._prepare_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/worklog/",
            payload=payload,
        )
        return self._decode(Worklog, data)

    async def edit_worklog(
        self,
        issue_id: str,
        worklog_id: int,
        duration: str | Duration,
        comment: str | None = None,
    ) -> Worklog:
        """Edit worklog.

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/patch-worklog
        """
        if isinstance(duration, Duration):
            duration = duration.to_iso()

        payload = self._prepare_payload(locals(), exclude=("issue_id", "worklog_id"))
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}/worklog/{worklog_id}",
            payload=payload,
        )
        return self._decode(Worklog, data)

    async def delete_worklog(
        self,
        issue_id: str,
        worklog_id: int,
    ) -> bool:
        """Delete worklog.

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/delete-worklog
        """
        await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/worklog/{worklog_id}",
        )
        return True

    async def get_issue_worklog(
        self,
        issue_id: str,
        *,
        per_page: int | None = None,
        id_: str | int | None = None,
    ) -> list[Worklog]:
        """Get issue worklog records.

        :param per_page: Number of entries per page (max 500).
        :param id_: Pagination cursor — return worklogs after this
                    worklog id (query param "id").

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/issue-worklog
        """
        params: dict[str, str] = {}
        if per_page is not None:
            params["perPage"] = str(per_page)
        if id_ is not None:
            params["id"] = str(id_)

        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/worklog",
            params=params or None,
        )
        return self._decode(list[Worklog], data)

    async def get_worklog(
        self,
        created_by: str | None = None,
        created_at_from: datetime | str | None = None,
        created_at_to: datetime | str | None = None,
    ) -> list[Worklog]:
        """Get issue worklog records.

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/get-worklog
        """
        created_at = _process_created_at(created_at_from, created_at_to)
        payload = self._prepare_payload(
            locals(),
            exclude=["created_at_from", "created_at_to"],
        )
        data = await self._client.request(
            method="POST",
            uri="/worklog/_search",
            payload=payload,
        )
        return self._decode(list[Worklog], data)


def _process_created_at(
    created_at_from: datetime | str | None = None,
    created_at_to: datetime | str | None = None,
) -> dict[str, str] | None:
    date_range = [created_at_from, created_at_to]
    if any(date_range) and not all(date_range):
        msg = "Set full range or not set it at all."
        raise ValueError(msg)

    if not created_at_from or not created_at_to:
        return None

    return {
        "from": to_tracker_datetime(created_at_from),
        "to": to_tracker_datetime(created_at_to),
    }
