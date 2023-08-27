from __future__ import annotations

from yatracker.tracker.base import BaseTracker
from yatracker.types import (
    Comment,
)


class Comments(BaseTracker):
    async def get_comments(self, issue_id: str) -> list[Comment]:
        """Get the comments for an issue.

        Use this request to get a list of comments in the issue.
        :param issue_id:
        :return:
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/comments",
        )
        return self._decode(list[Comment], data)

    async def post_comment(self, issue_id: str, text: str, **kwargs) -> Comment:
        """Comment the issue."""
        payload = self.clear_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/comments/",
            payload=payload,
        )
        return self._decode(Comment, data)
