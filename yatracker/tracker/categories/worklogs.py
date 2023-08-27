from __future__ import annotations

from datetime import datetime
from warnings import warn

from yatracker.tracker.base import BaseTracker
from yatracker.types import Worklog
from yatracker.types.duration import Duration


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
        if isinstance(start, datetime):
            start = start.isoformat(timespec="milliseconds")

        if isinstance(duration, Duration):
            duration = duration.to_iso()

        payload = self.clear_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/worklog/",
            payload=payload,
        )
        decoder = self._get_decoder(Worklog)
        return decoder.decode(data)

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

        query_params = ["issue_id", "worklog_id"]
        payload = self.clear_payload(locals(), exclude=query_params)
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}/worklog/{worklog_id}",
            payload=payload,
        )
        decoder = self._get_decoder(Worklog)
        return decoder.decode(data)

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

    async def get_issue_worklog(self, issue_id: str) -> list[Worklog]:
        """Get issue worklog records.

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/issue-worklog
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/worklog",
        )
        decoder = self._get_decoder(list[Worklog])
        return decoder.decode(data)

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
        payload = self.clear_payload(
            locals(),
            exclude=["created_at_from", "created_at_to"],
        )
        data = await self._client.request(
            method="POST",
            uri="/worklog/_search",
            payload=payload,
        )
        decoder = self._get_decoder(list[Worklog])
        return decoder.decode(data)


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

    if isinstance(created_at_from, datetime):
        if created_at_from.tzinfo is None:
            warn(
                "Tracker API may works wrong with naive datetime. "
                "Please, use Timezone-Aware objects.",
                UserWarning,
                stacklevel=2,
            )
        created_at_from = created_at_from.isoformat(timespec="milliseconds")

    if isinstance(created_at_to, datetime):
        created_at_to = created_at_to.isoformat(timespec="milliseconds")

    created_at: dict[str, str] = {
        "from": created_at_from,
        "to": created_at_to,
    }
    return created_at
