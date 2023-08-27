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
        **kwargs,
    ) -> Worklog:
        """Add worklog to the issue."""
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
