from __future__ import annotations

from datetime import datetime

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
            method="PATCH",
            uri=f"/issues/{issue_id}/worklog",
        )
        decoder = self._get_decoder(list[Worklog])
        return decoder.decode(data)
