"""Tests for the changelog, links, comment reactions, suggest and scroll endpoints.

Also covers the matching `FullIssue` helpers. Payloads are taken from the
official documentation. Masked ids in the docs, e.g.
``"6033f986bd6c4a04********"``, are replaced with plausible concrete
values, following the convention already used by the other test modules:
https://yandex.ru/support/tracker/ru/api/issues/get-changelog
https://yandex.ru/support/tracker/ru/api/issues/link-issue
https://yandex.ru/support/tracker/ru/api/issues/delete-link-issue
https://yandex.ru/support/tracker/ru/api/issues/get-links
https://yandex.ru/support/tracker/ru/api/issues/get-suggest
https://yandex.ru/support/tracker/ru/api/issues/search-release
https://yandex.ru/support/tracker/ru/api/issues/add-reaction-to-comment
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from yatracker import YaTracker
from yatracker.exceptions import ObjectNotFoundError
from yatracker.types import (
    FullIssue,
    Issue,
    LinkRelationship,
)
from yatracker.types.changelog import Changelog
from yatracker.types.issue_link import CreatedIssueLink, IssueLink
from yatracker.types.issue_suggest import IssueSuggest

from tests.conftest import FakeClient, full_issue_body, make_tracker, sent_json

# --------------------------------------------------------------------------
# get-changelog / iter_issue_changelog
# --------------------------------------------------------------------------

CHANGELOG_ISSUE_CREATED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/TEST-27/changelog/6033f986bd6c4a04",
    "id": "6033f986bd6c4a04",
    "issue": {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-27",
        "id": "6033f986bd6c4a04",
        "key": "TEST-27",
        "display": "My issue",
    },
    "updatedAt": "2021-02-22T18:35:50.157+0000",
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "type": "IssueCreated",
    "transport": "front",
    "fields": [
        {
            "field": {
                "self": "https://api.tracker.yandex.net/v3/fields/status",
                "id": "status",
                "display": "Status",
            },
            "from": None,
            "to": {
                "self": "https://api.tracker.yandex.net/v3/statuses/1",
                "id": "1",
                "key": "open",
                "display": "Открыт",
            },
        },
    ],
}

CHANGELOG_ISSUE_UPDATED: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/TEST-27/changelog/6033f98d4417c101",
    "id": "6033f98d4417c101",
    "issue": {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-27",
        "id": "6033f986bd6c4a04",
        "key": "TEST-27",
        "display": "My issue",
    },
    "updatedAt": "2021-02-22T18:35:57.359+0000",
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "type": "IssueUpdated",
    "transport": "front",
    "fields": [
        {
            "field": {
                "self": "https://api.tracker.yandex.net/v3/fields/followers",
                "id": "followers",
                "display": "Followers",
            },
            "from": None,
            "to": [
                {
                    "self": "https://api.tracker.yandex.net/v3/users/1111",
                    "id": "1111",
                    "display": "Имя Фамилия",
                },
            ],
        },
    ],
}

CHANGELOG_COMMENT_ADDED: dict[str, Any] = {
    "id": "62bab52ca16f631e",
    "self": "https://api.tracker.yandex.net/v3/issues/TEST-27/changelog/62bab52ca16f631e",
    "issue": {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-27",
        "id": "5fbc929b5b28572f",
        "key": "TEST-27",
        "display": "My issue",
    },
    "updatedAt": "2022-06-28T08:00:44.155+0000",
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "type": "IssueCommentAdded",
    "transport": "front",
    "comments": {
        "added": [
            {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-27/comments/10",
                "id": "10",
                "display": "My comment",
            },
        ],
    },
    "executedTriggers": [
        {
            "trigger": {
                "self": "https://api.tracker.yandex.net/v3/queues/TEST/triggers/29",
                "id": "29",
                "display": "My trigger",
            },
            "success": True,
            "message": "Success",
        },
    ],
}


class TestGetIssueChangelog:
    async def test_sends_all_query_params_and_decodes_every_field_shape(self) -> None:
        tracker, client = make_tracker(
            [CHANGELOG_ISSUE_CREATED, CHANGELOG_ISSUE_UPDATED, CHANGELOG_COMMENT_ADDED],
        )
        changes = await tracker.get_issue_changelog(
            "TEST-27",
            id_="5b9a1a88f7c60500",
            per_page=50,
            field="status",
            type_="IssueWorkflow",
        )

        assert len(changes) == 3
        assert all(isinstance(c, Changelog) for c in changes)

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/issues/TEST-27/changelog")
        assert call["params"] == {
            "id": "5b9a1a88f7c60500",
            "perPage": "50",
            "field": "status",
            "type": "IssueWorkflow",
        }

        created = changes[0]
        assert created.id == "6033f986bd6c4a04"
        assert created.issue.key == "TEST-27"
        assert created.updated_by.display == "Имя Фамилия"
        assert created.type == "IssueCreated"
        assert created.transport == "front"
        assert created.fields is not None
        field_change = created.fields[0]
        assert field_change.field.id == "status"
        assert field_change.field.display == "Status"
        assert field_change.from_ is None
        assert field_change.to == {
            "self": "https://api.tracker.yandex.net/v3/statuses/1",
            "id": "1",
            "key": "open",
            "display": "Открыт",
        }

        updated = changes[1]
        assert updated.type == "IssueUpdated"
        assert updated.fields is not None
        followers_change = updated.fields[0]
        assert followers_change.field.id == "followers"
        assert followers_change.from_ is None
        assert followers_change.to == [
            {
                "self": "https://api.tracker.yandex.net/v3/users/1111",
                "id": "1111",
                "display": "Имя Фамилия",
            },
        ]

        comment_added = changes[2]
        assert comment_added.type == "IssueCommentAdded"
        assert comment_added.comments is not None
        assert comment_added.comments.added is not None
        assert comment_added.comments.added[0].id == "10"
        assert comment_added.comments.added[0].display == "My comment"
        assert comment_added.executed_triggers is not None
        trigger = comment_added.executed_triggers[0]
        assert trigger.trigger.id == "29"
        assert trigger.trigger.display == "My trigger"
        assert trigger.success is True
        assert trigger.message == "Success"

    async def test_without_optional_params_sends_no_query_string(self) -> None:
        tracker, client = make_tracker([])
        changes = await tracker.get_issue_changelog("TEST-27")
        assert changes == []

        call = client.calls[0]
        assert call["params"] is None


class TestIterIssueChangelog:
    @staticmethod
    def _record(record_id: str, *, type_: str) -> dict[str, Any]:
        return {
            "self": f"https://api.tracker.yandex.net/v3/issues/TEST-27/changelog/{record_id}",
            "id": record_id,
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-27",
                "id": "6033f986bd6c4a04",
                "key": "TEST-27",
                "display": "My issue",
            },
            "updatedAt": "2021-02-22T18:35:50.157+0000",
            "updatedBy": {
                "self": "https://api.tracker.yandex.net/v3/users/1111",
                "id": "1111",
                "display": "Имя Фамилия",
            },
            "type": type_,
        }

    async def test_pages_through_the_cursor_and_dedupes_the_resent_edge(self) -> None:
        page1 = [
            self._record("c1", type_="IssueCreated"),
            self._record("c2", type_="IssueUpdated"),
        ]
        # a server that resends the cursor record as the first item of the
        # next page must not produce a duplicate in the iteration.
        page2 = [
            self._record("c2", type_="IssueUpdated"),
            self._record("c3", type_="IssueWorkflow"),
        ]
        page3: list[dict[str, Any]] = []

        client = FakeClient(
            responses=[
                (200, json.dumps(page1).encode(), {}),
                (200, json.dumps(page2).encode(), {}),
                (200, json.dumps(page3).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)

        seen = [change.id async for change in tracker.iter_issue_changelog("TEST-27")]
        assert seen == ["c1", "c2", "c3"]

        assert len(client.calls) == 3
        assert client.calls[0]["params"] is None
        assert client.calls[1]["params"] == {"id": "c2"}
        assert client.calls[2]["params"] == {"id": "c3"}

    async def test_stops_immediately_on_an_empty_first_page(self) -> None:
        client = FakeClient(responses=[(200, b"[]", {})])
        tracker = YaTracker(client=client)

        seen = [change async for change in tracker.iter_issue_changelog("TEST-27")]
        assert seen == []
        assert len(client.calls) == 1

    async def test_per_page_one_is_sent_unchanged(self) -> None:
        """The changelog cursor is exclusive: a page of one still advances."""
        # `id` is documented as the change the requested ones *follow*,
        # so the fake server never resends the cursor record.
        page1 = [self._record("c1", type_="IssueCreated")]
        page2 = [self._record("c2", type_="IssueUpdated")]
        page3 = [self._record("c3", type_="IssueWorkflow")]
        page4: list[dict[str, Any]] = []

        client = FakeClient(
            responses=[
                (200, json.dumps(page1).encode(), {}),
                (200, json.dumps(page2).encode(), {}),
                (200, json.dumps(page3).encode(), {}),
                (200, json.dumps(page4).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)

        seen = [
            change.id
            async for change in tracker.iter_issue_changelog("TEST-27", per_page=1)
        ]
        assert seen == ["c1", "c2", "c3"]

        assert client.calls[0]["params"] == {"perPage": "1"}
        assert client.calls[1]["params"] == {"perPage": "1", "id": "c1"}
        assert client.calls[2]["params"] == {"perPage": "1", "id": "c2"}
        assert client.calls[3]["params"] == {"perPage": "1", "id": "c3"}


class TestFullIssueGetChangelogDelegation:
    async def test_delegates_to_get_issue_changelog_with_self_id(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, json.dumps([CHANGELOG_ISSUE_CREATED]).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        changes = await issue.get_changelog(field="status", per_page=10)
        assert len(changes) == 1
        assert changes[0].id == "6033f986bd6c4a04"

        call = client.calls[1]
        assert call["method"] == "GET"
        assert call["url"].endswith(f"/issues/{issue.id}/changelog")
        assert call["params"] == {"field": "status", "perPage": "10"}


# --------------------------------------------------------------------------
# get-links / link-issue / delete-link-issue
# --------------------------------------------------------------------------

ISSUE_LINK_WITH_ASSIGNEE_AND_STATUS: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/JUNE-2/links/471234",
    "id": 471234,
    "type": {
        "self": "https://api.tracker.yandex.net/v3/linktypes/subtask",
        "id": "subtask",
        "inward": "Подзадача",
        "outward": "Родительская задача",
    },
    "direction": "outward",
    "object": {
        "self": "https://api.tracker.yandex.net/v3/issues/TREK-9844",
        "id": "593cd211ef7e8a33",
        "key": "TREK-9844",
        "display": "subtask",
    },
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "createdAt": "2017-06-11T05:16:01.421+0000",
    "updatedAt": "2017-06-11T05:16:01.421+0000",
    "assignee": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "status": {
        "self": "https://api.tracker.yandex.net/v3/statuses/1",
        "id": "1",
        "key": "open",
        "display": "Открыт",
    },
}

# `POST .../links` answers without `assignee`/`status` (only `GET .../links`
# carries them), which is why it is decoded as `CreatedIssueLink`, where both
# are optional, and not as `IssueLink`, where `status` is required.
ISSUE_LINK_CREATED_WITHOUT_STATUS: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/TEST-1/links/1012345",
    "id": 1012345,
    "type": {
        "self": "https://api.tracker.yandex.net/v3/linktypes/relates",
        "id": "relates",
        "inward": "relates",
        "outward": "relates",
    },
    "direction": "inward",
    "object": {
        "self": "https://api.tracker.yandex.net/v3/issues/STARTREK-2",
        "id": "4ff3e8dae4b0e2ac",
        "key": "TREK-2",
        "display": "My issue",
    },
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
    },
    "createdAt": "2014-06-18T12:06:02.401+0000",
    "updatedAt": "2014-06-18T12:06:02.401+0000",
}


class TestGetIssueLinks:
    async def test_decodes_full_response_with_assignee_and_status(self) -> None:
        tracker, client = make_tracker([ISSUE_LINK_WITH_ASSIGNEE_AND_STATUS])
        links = await tracker.get_issue_links("JUNE-2")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/issues/JUNE-2/links")

        assert len(links) == 1
        link = links[0]
        assert isinstance(link, IssueLink)
        assert link.id == 471234
        assert link.type.id == "subtask"
        assert link.direction.value == "outward"
        assert link.object.key == "TREK-9844"
        assert link.created_by.display == "Имя Фамилия"
        assert link.assignee is not None
        assert link.assignee.display == "Имя Фамилия"
        assert link.status is not None
        assert link.status.key == "open"
        # `outward`, matching `direction`
        assert link.name == "Родительская задача"


class TestLinkIssues:
    async def test_sends_relationship_enum_and_issue_object_key(self) -> None:
        tracker, client = make_tracker(
            ISSUE_LINK_CREATED_WITHOUT_STATUS,
            status=201,
        )
        link = await tracker.link_issues(
            "TEST-1",
            LinkRelationship.RELATES,
            Issue(self="u", id="9", key="TREK-2", display="d"),
        )

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issues/TEST-1/links")
        assert sent_json(call) == {"relationship": "relates", "issue": "TREK-2"}

        assert link.id == 1012345
        assert link.direction.value == "inward"
        # not sent by `POST .../links`
        assert link.status is None
        assert link.assignee is None

    async def test_accepts_plain_string_relationship_and_issue_key(self) -> None:
        tracker, client = make_tracker(ISSUE_LINK_CREATED_WITHOUT_STATUS, status=201)
        await tracker.link_issues("TEST-1", "is subtask for", "TREK-2")

        call = client.calls[0]
        assert sent_json(call) == {"relationship": "is subtask for", "issue": "TREK-2"}

    async def test_sends_the_key_of_a_full_issue(self) -> None:
        """`FullIssue` is not a subclass of `Issue`, it needs its own branch."""
        client = FakeClient(
            responses=[
                (200, full_issue_body(key="TREK-2"), {}),
                (201, json.dumps(ISSUE_LINK_CREATED_WITHOUT_STATUS).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        linked = await tracker.get_issue("TREK-2")
        assert isinstance(linked, FullIssue)

        await tracker.link_issues("TEST-1", LinkRelationship.RELATES, linked)

        assert sent_json(client.calls[1]) == {
            "relationship": "relates",
            "issue": "TREK-2",
        }

    async def test_returns_a_created_issue_link_without_status(self) -> None:
        tracker, _ = make_tracker(ISSUE_LINK_CREATED_WITHOUT_STATUS, status=201)
        link = await tracker.link_issues("TEST-1", "relates", "TREK-2")

        assert isinstance(link, CreatedIssueLink)
        assert link.status is None
        assert link.assignee is None


class TestUnlinkIssues:
    async def test_deletes_and_returns_true(self) -> None:
        tracker, client = make_tracker(status=204)
        assert await tracker.unlink_issues("TEST-1", 1012345) is True

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/issues/TEST-1/links/1012345")


class TestFullIssueLinkDelegation:
    async def test_link_delegates_to_link_issues(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (201, json.dumps(ISSUE_LINK_CREATED_WITHOUT_STATUS).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        link = await issue.link(LinkRelationship.RELATES, "TREK-2")
        assert link.id == 1012345

        call = client.calls[1]
        assert call["url"].endswith(f"/issues/{issue.id}/links")
        assert sent_json(call) == {"relationship": "relates", "issue": "TREK-2"}

    async def test_link_sends_the_key_of_an_issue_object(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (201, json.dumps(ISSUE_LINK_CREATED_WITHOUT_STATUS).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        await issue.link(
            "relates",
            Issue(self="u", id="9", key="TREK-2", display="d"),
        )

        assert sent_json(client.calls[1]) == {
            "relationship": "relates",
            "issue": "TREK-2",
        }

    async def test_link_sends_the_key_of_a_full_issue(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(key="TREK-2"), {}),
                (201, json.dumps(ISSUE_LINK_CREATED_WITHOUT_STATUS).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")
        linked = await tracker.get_issue("TREK-2")

        await issue.link(LinkRelationship.RELATES, linked)

        assert sent_json(client.calls[2]) == {
            "relationship": "relates",
            "issue": "TREK-2",
        }

    async def test_unlink_delegates_to_unlink_issues(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (204, b"", {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        assert await issue.unlink(1012345) is True

        call = client.calls[1]
        assert call["method"] == "DELETE"
        assert call["url"].endswith(f"/issues/{issue.id}/links/1012345")


# --------------------------------------------------------------------------
# get-suggest
# --------------------------------------------------------------------------


SUGGEST_RESPONSE: list[dict[str, Any]] = [
    {
        "self": "https://api.tracker.yandex.net/v3/issues/TEST-123",
        "id": "11dac333333a",
        "key": "TEST-123",
        "version": 749,
        "summary": "My summary",
        "followers": [
            {
                "self": "https://api.tracker.yandex.net/v3/users/1111",
                "id": "1111",
                "display": "Имя Фамилия",
                "cloudUid": "ajeppa7dgp53",
                "passportUid": 1111,
            },
            {
                "self": "https://api.tracker.yandex.net/v3/users/1112",
                "id": "1112",
                "display": "Имя Фамилия2",
                "cloudUid": "ajeppa7dgp54",
                "passportUid": 1112,
            },
        ],
        "assignee": {
            "self": "https://api.tracker.yandex.net/v3/users/1113",
            "id": "1113",
            "display": "Имя Фамилия3",
            "cloudUid": "ajeppa7dgp55",
            "passportUid": 1113,
        },
        "status": {
            "self": "https://api.tracker.yandex.net/v3/statuses/3",
            "id": "3",
            "key": "open",
            "display": "Открыт",
        },
    },
]


class TestSuggestIssues:
    async def test_default_type_decodes_the_bare_documented_projection(self) -> None:
        """The default `_type` must decode the doc's sample response."""
        tracker, client = make_tracker(SUGGEST_RESPONSE)
        issues = await tracker.suggest_issues("исправить ошибки")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/issues/_suggest")
        assert call["params"] == {"input": "исправить ошибки"}

        assert len(issues) == 1
        issue = issues[0]
        assert isinstance(issue, IssueSuggest)
        assert issue.url == "https://api.tracker.yandex.net/v3/issues/TEST-123"
        assert issue.id == "11dac333333a"
        assert issue.key == "TEST-123"
        assert issue.version == 749
        assert issue.summary == "My summary"
        assert issue.followers is not None
        assert [f.display for f in issue.followers] == [
            "Имя Фамилия",
            "Имя Фамилия2",
        ]
        assert issue.assignee is not None
        assert issue.assignee.display == "Имя Фамилия3"
        assert issue.status is not None
        assert issue.status.key == "open"

    async def test_sends_every_optional_query_param(self) -> None:
        tracker, client = make_tracker(SUGGEST_RESPONSE)
        await tracker.suggest_issues(
            "исправить ошибки",
            queue="TEST",
            full=True,
            fields="summary,status,assignee,followers",
            expand="all",
            embed="comments",
        )

        assert client.calls[0]["params"] == {
            "input": "исправить ошибки",
            "queue": "TEST",
            "full": "true",
            "fields": "summary,status,assignee,followers",
            "expand": "all",
            "embed": "comments",
        }

    async def test_accepts_a_sequence_of_fields(self) -> None:
        tracker, client = make_tracker(SUGGEST_RESPONSE)
        await tracker.suggest_issues(
            "исправить ошибки",
            full=True,
            fields=["summary", "status"],
        )

        assert client.calls[0]["params"] == {
            "input": "исправить ошибки",
            "full": "true",
            "fields": "summary,status",
        }

    async def test_accepts_a_custom_type(self) -> None:
        class MySuggest(IssueSuggest):
            pass

        tracker, client = make_tracker(SUGGEST_RESPONSE)
        issues = await tracker.suggest_issues("текст", MySuggest)

        assert client.calls[0]["params"] == {"input": "текст"}
        assert isinstance(issues[0], MySuggest)

    async def test_accepts_full_issue_for_whole_issues(self) -> None:
        """`_type=FullIssue` + `full=True` (and no `fields`) decodes whole issues."""
        tracker, client = make_tracker([json.loads(full_issue_body())])
        issues = await tracker.suggest_issues("текст", FullIssue, full=True)

        assert client.calls[0]["params"] == {"input": "текст", "full": "true"}
        assert isinstance(issues[0], FullIssue)
        assert issues[0].key == "TEST-1"


# --------------------------------------------------------------------------
# search-release / clear_search_scroll
# --------------------------------------------------------------------------


class TestClearSearchScroll:
    async def test_posts_the_scroll_id_to_token_mapping_and_returns_true(self) -> None:
        tracker, client = make_tracker()
        scroll_ids = {
            "cXVlcnlUaGVuRmV0Y2g7Njsy": "c44356850f446b88e5b5cd65a34a1409:14503",
            "cXVlcnlUaGVuRmV0Y2g7NjsyMDQ0": "b8e1c56966f037d9c4e241af40d31dc:14525",
        }

        assert await tracker.clear_search_scroll(scroll_ids) is True

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/system/search/scroll/_clear")
        assert sent_json(call) == scroll_ids

    async def test_sends_a_single_pair_unchanged(self) -> None:
        tracker, client = make_tracker()
        await tracker.clear_search_scroll({"only-id": "only-token"})

        assert sent_json(client.calls[0]) == {"only-id": "only-token"}


# --------------------------------------------------------------------------
# add-reaction-to-comment
# --------------------------------------------------------------------------

COMMENT_WITH_REACTION: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/issues/TREK-123/comments/626",
    "id": 626,
    "longId": "5fa15a24ac894475b6b21ac0",
    "text": "Comment text",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1111,
    },
    "updatedBy": {
        "self": "https://api.tracker.yandex.net/v3/users/1111",
        "id": "1111",
        "display": "Имя Фамилия",
        "cloudUid": "ajeppa7dgp53",
        "passportUid": 1111,
    },
    "createdAt": "2020-11-03T13:24:52.575+0000",
    "updatedAt": "2020-11-03T13:24:52.575+0000",
    "reactionsCount": {"like": 1},
    "ownReactions": ["like"],
    "version": 1,
    "type": "standard",
    "transport": "internal",
}


class TestAddCommentReaction:
    async def test_sends_reaction_in_the_path_and_decodes_the_comment(self) -> None:
        tracker, client = make_tracker(COMMENT_WITH_REACTION)
        comment = await tracker.add_comment_reaction("TREK-123", 626, "LIKE")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issues/TREK-123/comments/626/reactions/LIKE")
        assert call["data"] is None

        assert comment.id == 626
        assert comment.long_id == "5fa15a24ac894475b6b21ac0"
        assert comment.reactions_count == {"like": 1}
        assert comment.own_reactions == ["like"]
        assert comment.version == 1
        assert comment.type == "standard"
        assert comment.transport == "internal"

    async def test_accepts_the_string_long_id(self) -> None:
        tracker, client = make_tracker(COMMENT_WITH_REACTION)
        long_id = "5fa15a24ac894475b6b21ac0"
        await tracker.add_comment_reaction("TREK-123", long_id, "HEART")

        call = client.calls[0]
        assert call["url"].endswith(
            "/issues/TREK-123/comments/5fa15a24ac894475b6b21ac0/reactions/HEART",
        )


class TestGetIssueChangelogErrorPropagation:
    async def test_404_raises_object_not_found(self) -> None:
        tracker, _ = make_tracker(status=404)
        with pytest.raises(ObjectNotFoundError):
            await tracker.get_issue_changelog("MISSING-1")
