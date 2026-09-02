from __future__ import annotations

from yatracker.tracker.base import BaseTracker
from yatracker.types import (
    Comment,
)


class Comments(BaseTracker):
    async def get_comments(
        self,
        issue_id: str,
        *,
        expand: str | None = None,
        per_page: int | None = None,
        id_: str | int | None = None,
    ) -> list[Comment]:
        """Get the comments for an issue.

        Use this request to get a list of comments in the issue.
        :param issue_id:
        :param expand: Additional fields to include in the response:
                        attachments, html, all.
        :param per_page: Number of entries per page.
        :param id_: Pagination cursor — return comments after this
                    comment id (query param "id").
        :return:
        """
        params: dict[str, str] = {}
        if expand:
            params["expand"] = expand
        if per_page is not None:
            params["perPage"] = str(per_page)
        if id_ is not None:
            params["id"] = str(id_)

        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/comments",
            params=params or None,
        )
        return self._decode(list[Comment], data)

    async def post_comment(
        self,
        issue_id: str,
        text: str,
        *,
        is_add_to_followers: bool | None = None,
        **kwargs,
    ) -> Comment:
        """Comment the issue.

        :param issue_id:
        :param text:
        :param is_add_to_followers: Whether to add the comment author
                                     to the issue followers.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["issue_id", "is_add_to_followers"],
        )

        params = None
        if is_add_to_followers is not None:
            params = {"isAddToFollowers": str(is_add_to_followers).lower()}

        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/comments/",
            params=params,
            payload=payload,
        )
        return self._decode(Comment, data)

    # ruff: noqa: PLR0913
    async def edit_comment(
        self,
        issue_id: str,
        comment_id: str | int,
        text: str,
        attachment_ids: list[str] | None = None,
        summonees: list[str] | None = None,
        markup_type: str | None = None,
    ) -> Comment:
        """Update issue comment.

        :param summonees: List of user logins to notify about the comment.
        :param markup_type: Comment markup type, e.g. "md" for Markdown.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/issues/edit-comment
        """
        payload = self._prepare_payload(locals(), exclude=["issue_id", "comment_id"])
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}/comments/{comment_id}",
            payload=payload,
        )
        return self._decode(Comment, data)

    async def add_comment_reaction(
        self,
        issue_id: str,
        comment_id: str | int,
        reaction: str,
    ) -> Comment:
        """Add a reaction to an issue comment.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/add-reaction-to-comment

        :param issue_id: ID or key of the issue.
        :param comment_id: ID of the comment, either the numeric `id`
            or the string `longId`.
        :param reaction: name of the reaction: "LIKE", "DISLIKE",
            "LAUGH", "HOORAY", "CONFUSED", "HEART", "ROCKET", "EYES",
            "FIRE", "OK", "FACEPALM" or "CHECK". The list is owned by
            the server, so it is not enforced here.
        :return: the comment with the updated `reactions_count` and
            `own_reactions`.
        """
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/comments/{comment_id}/reactions/{reaction}",
        )
        return self._decode(Comment, data)

    async def delete_comment(self, issue_id: str, comment_id: str | int) -> bool:
        """Delete issue comment.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/issues/delete-comment
        """
        await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/comments/{comment_id}",
        )
        return True
