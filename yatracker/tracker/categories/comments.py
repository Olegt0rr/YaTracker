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
        payload = self._prepare_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/comments/",
            payload=payload,
        )
        return self._decode(Comment, data)

    async def edit_comment(
        self,
        issue_id: str,
        comment_id: str | int,
        text: str,
        attachment_ids: list[str] | None = None,
    ) -> Comment:
        """Update issue comment.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/edit-comment
        """
        payload = self._prepare_payload(locals(), exclude=["issue_id", "comment_id"])
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}/comments/{comment_id}",
            payload=payload,
        )
        return self._decode(Comment, data)

    async def delete_comment(self, issue_id: str, comment_id: str | int) -> bool:
        """Delete issue comment.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/delete-comment
        """
        await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/comments/{comment_id}",
        )
        return True
