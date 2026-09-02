"""Tests for the entity comments API (projects, portfolios and goals).

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/comments/add-comment
https://yandex.ru/support/tracker/ru/api/entities/comments/delete-comment
https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments
https://yandex.ru/support/tracker/ru/api/entities/comments/get-comment
https://yandex.ru/support/tracker/ru/api/entities/comments/patch-comment
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

import pytest
from yatracker.types.entity_comment import EntityComment, EntityCommentsPage

from tests.conftest import USER, make_tracker, sent_json

# --- payload builders --------------------------------------------------------


def comment_payload(**overrides: Any) -> dict[str, Any]:
    """Build the `add-comment`/`patch-comment` response shape (no expand)."""
    payload: dict[str, Any] = {
        "self": (
            "https://api.tracker.yandex.net/v3/entities/project/"
            "6586d6fee2b9ef74/comments/22"
        ),
        "id": 22,
        "longId": "65a1ba7b46b9746d00000001",
        "text": "Текст комментария.",
        "createdBy": USER,
        "updatedBy": USER,
        "createdAt": "2024-01-12T22:17:31.176+0000",
        "updatedAt": "2024-01-12T22:17:31.176+0000",
        "summonees": [USER],
        "version": 1,
        "type": "standard",
        "transport": "internal",
    }
    payload.update(overrides)
    return payload


def comment_body(**overrides: Any) -> bytes:
    return json.dumps(comment_payload(**overrides)).encode()


def expanded_comment_payload(**overrides: Any) -> dict[str, Any]:
    """Build the `get-all-comments`/`get-comment` response shape (`expand=all`)."""
    payload: dict[str, Any] = {
        "self": (
            "https://api.tracker.yandex.net/v3/entities/project/"
            "6586d6fee2b9ef74/comments/15"
        ),
        "id": 15,
        "longId": "65a156a29d5d200000000001",
        "text": "Комментарий **номер один.**",
        "textHtml": "<p>Комментарий <strong>номер один.</strong></p>\n",
        "attachments": [
            {
                "self": (
                    "https://api.tracker.yandex.net/v3/entities/project/"
                    "6586d6fee2b9ef74/attachments/25"
                ),
                "id": "25",
                "display": "image.jpg",
            },
        ],
        "createdBy": USER,
        "updatedBy": USER,
        "createdAt": "2024-01-12T15:11:30.278+0000",
        "updatedAt": "2024-01-12T16:33:35.988+0000",
        "usersReacted": {"like": [USER]},
        "ownReactions": ["like"],
        "summonees": [USER],
        "version": 3,
        "type": "standard",
        "transport": "internal",
    }
    payload.update(overrides)
    return payload


PAGE: dict[str, Any] = {
    "comments": [
        comment_payload(id=22, longId="65a1bdb02b780b3100000001", text="Предыдущий."),
        comment_payload(id=23, longId="65a1bdb02b780b3200000002", text="Указанный."),
        comment_payload(id=24, longId="65a1bdb02b780b3300000003", text="Следующий."),
    ],
    "hasNext": True,
    "hasPrev": True,
}


# --- decoding ----------------------------------------------------------------


class TestEntityCommentDecoding:
    async def test_basic_fields_decode(self) -> None:
        tracker, _ = make_tracker(comment_payload())
        comment = await tracker.get_entity_comment("project", "6586d6fee2b9ef74", 22)

        assert isinstance(comment, EntityComment)
        assert comment.id == 22
        assert comment.long_id == "65a1ba7b46b9746d00000001"
        assert comment.text == "Текст комментария."
        assert comment.created_by.display == "Имя Фамилия"
        assert comment.updated_by is not None
        assert comment.created_at == datetime(
            2024,
            1,
            12,
            22,
            17,
            31,
            176000,
            tzinfo=timezone.utc,
        )
        assert comment.summonees is not None
        assert comment.summonees[0].display == "Имя Фамилия"  # type: ignore[union-attr]
        assert comment.version == 1
        assert comment.type == "standard"
        assert comment.transport == "internal"
        assert comment.text_html is None
        assert comment.attachments is None
        assert comment.users_reacted is None
        assert comment.reactions_count is None
        assert comment.own_reactions is None

    async def test_expand_all_fields_decode(self) -> None:
        tracker, _ = make_tracker(expanded_comment_payload())
        comment = await tracker.get_entity_comment(
            "project",
            "6586d6fee2b9ef74",
            15,
            expand="all",
        )

        assert comment.text_html == "<p>Комментарий <strong>номер один.</strong></p>\n"
        assert comment.attachments is not None
        assert comment.attachments[0].id == "25"
        assert comment.attachments[0].display == "image.jpg"
        assert comment.users_reacted is not None
        assert comment.users_reacted["like"][0].display == "Имя Фамилия"
        assert comment.own_reactions == ["like"]

    async def test_reactions_count_without_reactions_expand(self) -> None:
        payload = comment_payload(reactionsCount={"like": 2})
        tracker, _ = make_tracker(payload)
        comment = await tracker.get_entity_comment("project", "1", 22)

        assert comment.reactions_count == {"like": 2}
        assert comment.users_reacted is None

    async def test_summonees_accept_plain_strings(self) -> None:
        payload = comment_payload(summonees=["agent007"])
        tracker, _ = make_tracker(payload)
        comment = await tracker.get_entity_comment("project", "1", 22)

        assert comment.summonees == ["agent007"]

    async def test_maillist_summonees_decode(self) -> None:
        payload = comment_payload(
            maillistSummonees=[
                {
                    "self": "https://api.tracker.yandex.net/v3/maillists/usertest@test.ru",
                    "id": "usertest@test.ru",
                    "display": "My mailist",
                },
            ],
        )
        tracker, _ = make_tracker(payload)
        comment = await tracker.get_entity_comment("project", "1", 22)

        assert comment.maillist_summonees is not None
        maillist = comment.maillist_summonees[0]
        assert maillist.id == "usertest@test.ru"
        assert maillist.display == "My mailist"

    async def test_page_decodes(self) -> None:
        tracker, _ = make_tracker(PAGE)
        page = await tracker.get_entity_comments_relative("project", "1")

        assert isinstance(page, EntityCommentsPage)
        assert page.has_next is True
        assert page.has_prev is True
        assert len(page.comments) == 3
        assert page.comments[1].text == "Указанный."


# --- get_entity_comments ------------------------------------------------------


class TestGetEntityComments:
    async def test_sends_get(self) -> None:
        tracker, client = make_tracker([expanded_comment_payload()])
        await tracker.get_entity_comments("project", "6586d6fee2b9ef74")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/entities/project/6586d6fee2b9ef74/comments")
        assert call["params"] is None

    async def test_expand_param(self) -> None:
        tracker, client = make_tracker([expanded_comment_payload()])
        await tracker.get_entity_comments("project", "1", expand="all")

        assert client.calls[0]["params"] == {"expand": "all"}

    async def test_decodes_list(self) -> None:
        tracker, _ = make_tracker([expanded_comment_payload()])
        comments = await tracker.get_entity_comments("project", "1")

        assert len(comments) == 1
        assert isinstance(comments[0], EntityComment)
        assert comments[0].id == 15


# --- get_entity_comments_relative --------------------------------------------


class TestGetEntityCommentsRelative:
    async def test_sends_get_to_relative_url(self) -> None:
        tracker, client = make_tracker(PAGE)
        await tracker.get_entity_comments_relative("project", "1")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/entities/project/1/comments/_relative")
        assert call["params"] is None

    async def test_all_params_forward(self) -> None:
        tracker, client = make_tracker(PAGE)
        await tracker.get_entity_comments_relative(
            "project",
            "1",
            per_page=3,
            from_="65a1bdb02b780b3100000001",
            new_comments_on_top=False,
            direction="forward",
        )

        assert client.calls[0]["params"] == {
            "perPage": "3",
            "from": "65a1bdb02b780b3100000001",
            "newCommentsOnTop": "false",
            "direction": "forward",
        }

    async def test_selected_param(self) -> None:
        tracker, client = make_tracker(PAGE)
        await tracker.get_entity_comments_relative(
            "project",
            "1",
            selected="65a1bdb02b780b3200000002",
        )

        assert client.calls[0]["params"] == {"selected": "65a1bdb02b780b3200000002"}

    async def test_from_and_selected_are_exclusive(self) -> None:
        tracker, client = make_tracker(PAGE)
        with pytest.raises(ValueError, match="not both"):
            await tracker.get_entity_comments_relative(
                "project",
                "1",
                from_="1",
                selected="2",
            )

        assert client.calls == []


# --- get_entity_comment -------------------------------------------------------


class TestGetEntityComment:
    async def test_sends_get(self) -> None:
        tracker, client = make_tracker(expanded_comment_payload())
        await tracker.get_entity_comment("project", "6586d6fee2b9ef74", 15)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/entities/project/6586d6fee2b9ef74/comments/15",
        )
        assert call["params"] is None

    async def test_expand_param(self) -> None:
        tracker, client = make_tracker(expanded_comment_payload())
        await tracker.get_entity_comment("project", "1", 15, expand="all")

        assert client.calls[0]["params"] == {"expand": "all"}


# --- post_entity_comment -------------------------------------------------------


class TestPostEntityComment:
    async def test_sends_post_with_minimal_body(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.post_entity_comment("project", "1", "Текст комментария.")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/entities/project/1/comments")
        assert call["params"] is None
        assert sent_json(call) == {"text": "Текст комментария."}

    async def test_attachment_ids_and_summonees_in_body(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.post_entity_comment(
            "project",
            "1",
            "Текст",
            attachment_ids=["30"],
            summonees=["1120000000000001"],
            maillist_summonees=["usertest@test.ru"],
        )

        assert sent_json(client.calls[0]) == {
            "text": "Текст",
            "attachmentIds": ["30"],
            "summonees": ["1120000000000001"],
            "maillistSummonees": ["usertest@test.ru"],
        }

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.post_entity_comment(
            "project",
            "1",
            "Текст",
            is_add_to_followers=False,
            notify=False,
            notify_author=True,
            expand="attachments",
        )

        assert client.calls[0]["params"] == {
            "isAddToFollowers": "false",
            "notify": "false",
            "notifyAuthor": "true",
            "expand": "attachments",
        }

    async def test_no_params_when_not_given(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.post_entity_comment("project", "1", "Текст")

        assert client.calls[0]["params"] is None

    async def test_kwargs_are_camel_cased_into_body(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.post_entity_comment("project", "1", "Текст", extra_field="value")

        assert sent_json(client.calls[0]) == {
            "text": "Текст",
            "extraField": "value",
        }

    async def test_returns_decoded_comment(self) -> None:
        tracker, _ = make_tracker(comment_payload())
        comment = await tracker.post_entity_comment("project", "1", "Текст")

        assert isinstance(comment, EntityComment)
        assert comment.id == 22


# --- edit_entity_comment -------------------------------------------------------


class TestEditEntityComment:
    async def test_sends_patch_to_comment_url(self) -> None:
        tracker, client = make_tracker(comment_payload(text="Измененный текст."))
        await tracker.edit_entity_comment(
            "project",
            "1",
            31,
            text="Измененный текст.",
        )

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/v3/entities/project/1/comments/31")
        assert call["params"] is None
        assert sent_json(call) == {"text": "Измененный текст."}

    async def test_body_with_summonees(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.edit_entity_comment(
            "project",
            "1",
            31,
            summonees=["login1", "login2"],
        )

        assert sent_json(client.calls[0]) == {"summonees": ["login1", "login2"]}

    async def test_query_params(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.edit_entity_comment(
            "project",
            "1",
            31,
            text="new",
            is_add_to_followers=True,
            notify=True,
            notify_author=False,
            expand="all",
        )

        assert client.calls[0]["params"] == {
            "isAddToFollowers": "true",
            "notify": "true",
            "notifyAuthor": "false",
            "expand": "all",
        }

    async def test_kwargs_alone_is_enough(self) -> None:
        tracker, client = make_tracker(comment_payload())
        await tracker.edit_entity_comment("project", "1", 31, extra_field="value")

        assert sent_json(client.calls[0]) == {"extraField": "value"}

    async def test_nothing_to_change_raises(self) -> None:
        tracker, client = make_tracker(comment_payload())
        with pytest.raises(ValueError, match="at least one field"):
            await tracker.edit_entity_comment("project", "1", 31)

        assert client.calls == []


# --- delete_entity_comment -----------------------------------------------------


class TestDeleteEntityComment:
    async def test_sends_delete(self) -> None:
        tracker, client = make_tracker()
        result = await tracker.delete_entity_comment("project", "1", 16)

        call = client.calls[0]
        assert result is True
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/v3/entities/project/1/comments/16")
        assert call["params"] is None

    async def test_notify_params(self) -> None:
        tracker, client = make_tracker()
        await tracker.delete_entity_comment(
            "project",
            "1",
            16,
            notify=False,
            notify_author=True,
        )

        assert client.calls[0]["params"] == {
            "notify": "false",
            "notifyAuthor": "true",
        }


# --- unknown entity type ------------------------------------------------------


class TestUnknownEntityType:
    async def test_entity_type_is_sent_as_is(self) -> None:
        # `EntityType` documents the kinds Tracker has today, but a kind
        # added later must not be rejected client-side.
        tracker, client = make_tracker(comment_payload())
        await tracker.get_entity_comment("epic", "1", 22)  # type: ignore[arg-type]

        assert client.calls[0]["url"].endswith("/v3/entities/epic/1/comments/22")
