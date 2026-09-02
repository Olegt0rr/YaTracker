from __future__ import annotations

from typing import Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.entity import EntityType
from yatracker.types.entity_comment import EntityComment, EntityCommentsPage


class EntityComments(BaseTracker):
    """Comments of projects, portfolios and goals (`/entities`).

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments
    """

    async def get_entity_comments(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        expand: str | None = None,
    ) -> list[EntityComment]:
        """Get all comments of an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param expand: Additional information to include: "all", "html",
            "attachments" or "reactions".
        :return: List of the comments of the entity.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments
        """
        data = await self._client.request(
            method="GET",
            uri=_comments_uri(entity_type, entity_id),
            params=self._prepare_params(expand=expand),
        )
        return self._decode(list[EntityComment], data)

    async def get_entity_comments_relative(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        entity_id: str | int,
        *,
        per_page: int | None = None,
        from_: str | int | None = None,
        selected: str | int | None = None,
        new_comments_on_top: bool | None = None,
        direction: str | None = None,
    ) -> EntityCommentsPage:
        """Get a page of the comments of an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param per_page: Number of comments per page (50 by default).
        :param from_: Id of the comment to count the page from (it is
            not included). Mutually exclusive with `selected`.
        :param selected: Id of the comment to build the page around.
            Mutually exclusive with `from_`.
        :param new_comments_on_top: Whether to sort the newest comments
            first (`False` by default).
        :param direction: "forward" (default) or "backward", which
            inverts `new_comments_on_top`.
        :raises ValueError: If both `from_` and `selected` are given.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments
        """
        if from_ is not None and selected is not None:
            msg = "Pass either `from_` or `selected`, not both."
            raise ValueError(msg)

        data = await self._client.request(
            method="GET",
            uri=_comments_uri(entity_type, entity_id, "_relative"),
            params=self._prepare_params(
                per_page=per_page,
                from_=from_,
                selected=selected,
                new_comments_on_top=new_comments_on_top,
                direction=direction,
            ),
        )
        return self._decode(EntityCommentsPage, data)

    async def get_entity_comment(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        comment_id: str | int,
        *,
        expand: str | None = None,
    ) -> EntityComment:
        """Get a single comment of an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param comment_id: Id of the comment.
        :param expand: Additional information to include: "all", "html",
            "attachments" or "reactions".

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/comments/get-comment
        """
        data = await self._client.request(
            method="GET",
            uri=_comments_uri(entity_type, entity_id, str(comment_id)),
            params=self._prepare_params(expand=expand),
        )
        return self._decode(EntityComment, data)

    async def post_entity_comment(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        entity_id: str | int,
        text: str,
        *,
        attachment_ids: list[str | int] | None = None,
        summonees: list[str | int] | None = None,
        maillist_summonees: list[str] | None = None,
        is_add_to_followers: bool | None = None,
        notify: bool | None = None,
        notify_author: bool | None = None,
        expand: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> EntityComment:
        """Add a comment to an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param text: Text of the comment.
        :param attachment_ids: Ids of the temporary files to attach
            (upload them with `upload_temp_file` first).
        :param summonees: Ids or logins of the users to summon.
        :param maillist_summonees: Mailing lists to summon.
        :param is_add_to_followers: Whether to add the author of the
            comment to the followers of the entity (`True` by default).
        :param notify: Whether to notify the users mentioned in the
            entity fields (`True` by default).
        :param notify_author: Whether to notify the author of the change
            (`False` by default).
        :param expand: Additional information to include: "all", "html",
            "attachments" or "reactions".
        :param kwargs: Extra body fields, camel-cased and sent as is.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/comments/add-comment
        """
        payload = self._prepare_payload(
            locals(),
            exclude=[
                "entity_type",
                "entity_id",
                "is_add_to_followers",
                "notify",
                "notify_author",
                "expand",
            ],
        )

        data = await self._client.request(
            method="POST",
            uri=_comments_uri(entity_type, entity_id),
            params=self._prepare_params(
                is_add_to_followers=is_add_to_followers,
                notify=notify,
                notify_author=notify_author,
                expand=expand,
            ),
            payload=payload,
        )
        return self._decode(EntityComment, data)

    async def edit_entity_comment(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        entity_id: str | int,
        comment_id: str | int,
        *,
        text: str | None = None,
        attachment_ids: list[str | int] | None = None,
        summonees: list[str | int] | None = None,
        maillist_summonees: list[str] | None = None,
        is_add_to_followers: bool | None = None,
        notify: bool | None = None,
        notify_author: bool | None = None,
        expand: str | None = None,
        **kwargs: Any,  # noqa: ANN401
    ) -> EntityComment:
        """Edit a comment of an entity.

        Every body field is optional, but at least one of them (or a
        keyword argument) is required: an empty request would change
        nothing.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param comment_id: Id of the comment.
        :param text: New text of the comment.
        :param attachment_ids: Ids of the temporary files to attach
            (upload them with `upload_temp_file` first).
        :param summonees: Ids or logins of the users to summon.
        :param maillist_summonees: Mailing lists to summon.
        :param is_add_to_followers: Whether to add the author of the
            comment to the followers of the entity (`True` by default).
        :param notify: Whether to notify the users mentioned in the
            entity fields (`True` by default).
        :param notify_author: Whether to notify the author of the change
            (`False` by default).
        :param expand: Additional information to include: "all", "html",
            "attachments" or "reactions".
        :param kwargs: Extra body fields, camel-cased and sent as is.
        :raises ValueError: If there is nothing to change.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/comments/patch-comment
        """
        payload = self._prepare_payload(
            locals(),
            exclude=[
                "entity_type",
                "entity_id",
                "comment_id",
                "is_add_to_followers",
                "notify",
                "notify_author",
                "expand",
            ],
        )
        if not payload:
            msg = (
                "This operation requires at least one field to change, "
                "e.g. `text` or `summonees`."
            )
            raise ValueError(msg)

        data = await self._client.request(
            method="PATCH",
            uri=_comments_uri(entity_type, entity_id, str(comment_id)),
            params=self._prepare_params(
                is_add_to_followers=is_add_to_followers,
                notify=notify,
                notify_author=notify_author,
                expand=expand,
            ),
            payload=payload,
        )
        return self._decode(EntityComment, data)

    async def delete_entity_comment(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        comment_id: str | int,
        *,
        notify: bool | None = None,
        notify_author: bool | None = None,
    ) -> bool:
        """Delete a comment of an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param comment_id: Id of the comment.
        :param notify: Whether to notify the users mentioned in the
            entity fields (`True` by default).
        :param notify_author: Whether to notify the author of the change
            (`False` by default).
        :return: `True` if the comment was deleted.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/comments/delete-comment
        """
        await self._client.request(
            method="DELETE",
            uri=_comments_uri(entity_type, entity_id, str(comment_id)),
            params=self._prepare_params(notify=notify, notify_author=notify_author),
        )
        return True


def _comments_uri(entity_type: str, entity_id: str | int, *parts: str) -> str:
    """Build the uri of an entity comments endpoint.

    The entity type is not validated at runtime: `EntityType` documents
    the kinds Tracker has today, but a kind added later still works.
    """
    return "/".join(("/entities", entity_type, str(entity_id), "comments", *parts))
