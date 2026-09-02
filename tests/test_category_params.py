"""Tests for query/param handling fixes across category modules.

Covers: priorities.get_priorities, issues.get_issue/find_issues,
comments.get_comments/post_comment, and attached_files.attach_file.
"""

from __future__ import annotations

import io
import json
from datetime import datetime, timezone

import pytest
from yatracker import YaTracker
from yatracker.types import Duration, IssueType, IssueTypeConfig, Worklog
from yatracker.types.resolution import Resolution
from yatracker.types.workflow import Workflow

from tests.conftest import (
    FakeClient,
    full_issue_body,
    multipart_dispparams,
    sent_json,
)


def priority_body() -> bytes:
    return json.dumps(
        [
            {
                "self": "https://api/priorities/1",
                "id": "1",
                "key": "normal",
                "display": "Normal",
            },
        ],
    ).encode()


def comment_body() -> bytes:
    return json.dumps(
        {
            "self": "https://api/comments/1",
            "id": 1,
            "text": "hello",
            "createdBy": {"self": "u", "id": "1", "display": "User"},
            "createdAt": "2024-01-01T00:00:00.000+0000",
            "version": 1,
        },
    ).encode()


def worklog_body() -> bytes:
    return json.dumps(
        [
            {
                "self": "https://api/worklog/1",
                "id": 1,
                "version": 1,
                "issue": {
                    "self": "https://api/issue/1",
                    "id": "1",
                    "key": "TEST-1",
                    "display": "Test",
                },
                "createdBy": {"self": "u", "id": "1", "display": "User"},
                "createdAt": "2024-01-01T00:00:00.000+0000",
                "start": "2024-01-01T00:00:00.000+0000",
                "duration": "PT1H",
            },
        ],
    ).encode()


def single_worklog_body() -> bytes:
    return json.dumps(
        {
            "self": "https://api/worklog/1",
            "id": 1,
            "version": 1,
            "issue": {
                "self": "https://api/issue/1",
                "id": "1",
                "key": "TEST-1",
                "display": "Test",
            },
            "createdBy": {"self": "u", "id": "1", "display": "User"},
            "createdAt": "2024-01-01T00:00:00.000+0000",
            "start": "2024-01-01T00:00:00.000+0000",
            "duration": "PT2H",
        },
    ).encode()


def attachment_body() -> bytes:
    return json.dumps(
        {
            "self": "https://api/attachments/1",
            "id": "1",
            "name": "a.txt",
            "content": "https://api/attachments/1/a.txt",
            "createdBy": {"self": "u", "id": "1", "display": "User"},
            "createdAt": "2024-01-01T00:00:00.000+0000",
            "mimetype": "text/plain",
            "size": 4,
        },
    ).encode()


async def test_get_priorities_sends_localized_false() -> None:
    client = FakeClient(body=priority_body())
    tracker = YaTracker(client=client)
    await tracker.get_priorities(localized=False)
    assert client.calls[0]["params"] == {"localized": "false"}


async def test_get_priorities_sends_localized_true_by_default() -> None:
    client = FakeClient(body=priority_body())
    tracker = YaTracker(client=client)
    await tracker.get_priorities()
    assert client.calls[0]["params"] == {"localized": "true"}


async def test_get_issue_sends_fields_param() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.get_issue("TEST-1", expand="transitions", fields="summary,status")
    assert client.calls[0]["params"] == {
        "expand": "transitions",
        "fields": "summary,status",
    }


async def test_get_issue_no_params_when_unset() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.get_issue("TEST-1")
    assert client.calls[0]["params"] is None


async def test_find_issues_sends_paging_and_scroll_params() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.find_issues(
        filter_={"queue": "TEST"},
        per_page=50,
        page=2,
        scroll_type="sorted",
        per_scroll=100,
        scroll_ttl_millis=5000,
        scroll_id="abc123",
        fields="summary",
    )
    call = client.calls[0]
    assert call["params"] == {
        "perPage": "50",
        "page": "2",
        "scrollType": "sorted",
        "perScroll": "100",
        "scrollTTLMillis": "5000",
        "scrollId": "abc123",
        "fields": "summary",
    }
    payload = json.loads(bytes(call["data"]._value))
    assert payload == {"filter": {"queue": "TEST"}}


async def test_find_issues_scroll_params_not_in_body() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.find_issues(query="Key: TEST-1", per_page=10)
    call = client.calls[0]
    payload = json.loads(bytes(call["data"]._value))
    assert "perPage" not in payload
    assert "per_page" not in payload
    assert payload == {"query": "Key: TEST-1"}


async def test_get_comments_sends_expand_perpage_and_id() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.get_comments(
        "TEST-1",
        expand="all",
        per_page=25,
        id_=42,
    )
    assert client.calls[0]["params"] == {
        "expand": "all",
        "perPage": "25",
        "id": "42",
    }


async def test_get_comments_no_params_when_unset() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.get_comments("TEST-1")
    assert client.calls[0]["params"] is None


async def test_post_comment_is_add_to_followers_true_as_string() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    await tracker.post_comment("TEST-1", "hi", is_add_to_followers=True)
    assert client.calls[0]["params"] == {"isAddToFollowers": "true"}


async def test_post_comment_is_add_to_followers_false_as_string() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    await tracker.post_comment("TEST-1", "hi", is_add_to_followers=False)
    assert client.calls[0]["params"] == {"isAddToFollowers": "false"}


async def test_post_comment_no_params_when_unset() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    await tracker.post_comment("TEST-1", "hi")
    assert client.calls[0]["params"] is None


async def test_post_comment_body_excludes_is_add_to_followers() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    await tracker.post_comment("TEST-1", "hi", is_add_to_followers=True)
    payload = json.loads(bytes(client.calls[0]["data"]._value))
    assert "isAddToFollowers" not in payload
    assert payload == {"text": "hi"}


async def test_edit_comment_sends_summonees_and_markup_type() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    await tracker.edit_comment(
        "TEST-1",
        1,
        "updated",
        summonees=["user1", "user2"],
        markup_type="md",
    )
    payload = json.loads(bytes(client.calls[0]["data"]._value))
    assert payload == {
        "text": "updated",
        "summonees": ["user1", "user2"],
        "markupType": "md",
    }


async def test_get_issue_worklog_sends_perpage_and_id() -> None:
    client = FakeClient(body=worklog_body())
    tracker = YaTracker(client=client)
    await tracker.get_issue_worklog("TEST-1", per_page=500, id_=7)
    assert client.calls[0]["params"] == {"perPage": "500", "id": "7"}


async def test_get_issue_worklog_no_params_when_unset() -> None:
    client = FakeClient(body=worklog_body())
    tracker = YaTracker(client=client)
    await tracker.get_issue_worklog("TEST-1")
    assert client.calls[0]["params"] is None


async def test_edit_worklog_body_excludes_query_params() -> None:
    client = FakeClient(body=single_worklog_body())
    tracker = YaTracker(client=client)
    await tracker.edit_worklog("TEST-1", 1, duration="PT2H", comment="updated")
    payload = json.loads(bytes(client.calls[0]["data"]._value))
    assert payload == {"duration": "PT2H", "comment": "updated"}
    assert "queryParams" not in payload


async def test_attach_file_multipart_form() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    await tracker.attach_file("TEST-1", io.BytesIO(b"data"), filename="a.txt")

    dispparams = multipart_dispparams(client.calls[0])
    assert dispparams["name"] == "file"
    assert dispparams["filename"] == "a.txt"
    assert client.calls[0]["params"] == {"filename": "a.txt"}


async def test_attach_file_without_filename_falls_back_to_field_name() -> None:
    """Without explicit filename aiohttp falls back to the field name for BytesIO."""
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    await tracker.attach_file("TEST-1", io.BytesIO(b"data"))

    dispparams = multipart_dispparams(client.calls[0])
    assert dispparams["filename"] == "file"
    assert client.calls[0]["params"] is None


async def test_upload_temp_file_multipart_form() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    await tracker.upload_temp_file(io.BytesIO(b"data"), filename="a.txt")

    dispparams = multipart_dispparams(client.calls[0])
    assert dispparams["name"] == "file"
    assert dispparams["filename"] == "a.txt"
    assert client.calls[0]["params"] == {"filename": "a.txt"}


def issue_link_body() -> bytes:
    return json.dumps(
        [
            {
                "self": "https://api/issues/1/links/2",
                "id": 2,
                "type": {
                    "self": "https://api/linktypes/relates",
                    "id": "relates",
                    "inward": "Relates",
                    "outward": "Relates to",
                },
                "direction": "outward",
                "object": {
                    "self": "https://api/issues/2",
                    "id": "2",
                    "key": "TEST-2",
                    "display": "Other",
                },
                "createdBy": {"self": "u", "id": "1", "display": "User"},
                "createdAt": "2024-01-01T00:00:00.000+0000",
                "status": {"self": "s", "id": "5", "key": "open", "display": "Open"},
            },
        ],
    ).encode()


def transition_body() -> bytes:
    return json.dumps(
        [
            {
                "self": "https://api/issues/1/transitions/close",
                "id": "close",
                "display": "Close",
                "to": {"self": "s", "id": "5", "key": "closed", "display": "Closed"},
            },
        ],
    ).encode()


def queue_version_body() -> bytes:
    return json.dumps(
        [
            {
                "self": "https://api/versions/4",
                "id": 4,
                "version": 1,
                "queue": {
                    "self": "https://api/queues/TEST",
                    "id": "3",
                    "key": "TEST",
                    "display": "Test",
                },
                "name": "First release",
                "startDate": "2024-01-01",
                "dueDate": "2024-02-01",
                "released": False,
                "archived": False,
            },
        ],
    ).encode()


def full_queue_body() -> bytes:
    return json.dumps(
        {
            "self": "https://api/queues/DESIGN",
            "id": "111",
            "key": "DESIGN",
            "version": 1,
            "name": "Design",
            "lead": {"self": "u", "id": "1", "display": "User"},
            "assignAuto": False,
            "defaultType": {"self": "t", "id": "1", "key": "task", "display": "Task"},
            "defaultPriority": {
                "self": "p",
                "id": "3",
                "key": "normal",
                "display": "Normal",
            },
        },
    ).encode()


# --- worklogs ---------------------------------------------------------------


async def test_post_worklog_sends_start_duration_and_comment() -> None:
    client = FakeClient(body=single_worklog_body())
    tracker = YaTracker(client=client)
    worklog = await tracker.post_worklog(
        "TEST-1",
        start=datetime(2024, 1, 1, tzinfo=timezone.utc),
        duration=Duration(hours=2, minutes=30),
        comment="done",
    )

    assert isinstance(worklog, Worklog)
    assert worklog.id == 1
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/issues/TEST-1/worklog/")
    assert sent_json(call) == {
        "start": "2024-01-01T00:00:00.000+00:00",
        "duration": "PT2H30M",
        "comment": "done",
    }


async def test_post_worklog_keeps_plain_strings_as_is() -> None:
    client = FakeClient(body=single_worklog_body())
    tracker = YaTracker(client=client)
    await tracker.post_worklog(
        "TEST-1",
        start="2024-01-01T00:00:00.000+0000",
        duration="PT1H",
    )
    assert sent_json(client.calls[0]) == {
        "start": "2024-01-01T00:00:00.000+0000",
        "duration": "PT1H",
    }


async def test_edit_worklog_converts_duration_object() -> None:
    client = FakeClient(body=single_worklog_body())
    tracker = YaTracker(client=client)
    worklog = await tracker.edit_worklog("TEST-1", 1, duration=Duration(minutes=45))

    assert worklog.duration == "PT2H"
    call = client.calls[0]
    assert call["method"] == "PATCH"
    assert call["url"].endswith("/issues/TEST-1/worklog/1")
    assert sent_json(call) == {"duration": "PT45M"}


async def test_delete_worklog() -> None:
    client = FakeClient(body=b"")
    tracker = YaTracker(client=client)
    assert await tracker.delete_worklog("TEST-1", 1) is True

    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"].endswith("/issues/TEST-1/worklog/1")


async def test_get_issue_worklog_decodes_worklogs() -> None:
    client = FakeClient(body=worklog_body())
    tracker = YaTracker(client=client)
    worklogs = await tracker.get_issue_worklog("TEST-1")

    assert [w.duration for w in worklogs] == ["PT1H"]
    assert worklogs[0].issue.key == "TEST-1"


async def test_get_worklog_search_sends_created_by_and_range() -> None:
    client = FakeClient(body=worklog_body())
    tracker = YaTracker(client=client)
    await tracker.get_worklog(
        created_by="user1",
        created_at_from=datetime(2024, 1, 1, tzinfo=timezone.utc),
        created_at_to=datetime(2024, 2, 1, tzinfo=timezone.utc),
    )

    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/worklog/_search")
    assert sent_json(call) == {
        "createdBy": "user1",
        "createdAt": {
            "from": "2024-01-01T00:00:00.000+00:00",
            "to": "2024-02-01T00:00:00.000+00:00",
        },
    }


async def test_get_worklog_without_range_sends_only_created_by() -> None:
    client = FakeClient(body=worklog_body())
    tracker = YaTracker(client=client)
    await tracker.get_worklog(created_by="user1")
    assert sent_json(client.calls[0]) == {"createdBy": "user1"}


async def test_get_worklog_rejects_half_range() -> None:
    tracker = YaTracker(client=FakeClient(body=worklog_body()))
    with pytest.raises(ValueError, match="full range"):
        await tracker.get_worklog(created_at_from="2024-01-01T00:00:00.000+0000")


async def test_get_worklog_warns_on_naive_datetime() -> None:
    client = FakeClient(body=worklog_body())
    tracker = YaTracker(client=client)
    with pytest.warns(UserWarning, match="Timezone-Aware"):
        await tracker.get_worklog(
            created_at_from=datetime(2024, 1, 1),  # noqa: DTZ001
            created_at_to="2024-02-01T00:00:00.000+0000",
        )
    assert sent_json(client.calls[0])["createdAt"]["to"] == (
        "2024-02-01T00:00:00.000+0000"
    )


# --- issues -----------------------------------------------------------------


async def test_edit_issue_sends_version_param_and_kwargs() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    issue = await tracker.edit_issue("TEST-1", version=3, summary="new")

    assert issue.key == "TEST-1"
    call = client.calls[0]
    assert call["method"] == "PATCH"
    assert call["url"].endswith("/issues/TEST-1")
    assert call["params"] == {"version": "3"}
    assert sent_json(call) == {"summary": "new"}


async def test_edit_issue_without_version_sends_no_params() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.edit_issue("TEST-1", description="text")

    assert client.calls[0]["params"] is None
    assert sent_json(client.calls[0]) == {"description": "text"}


async def test_create_issue_renames_fields_and_extra_kwargs() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    issue = await tracker.create_issue(
        "summary",
        "TEST",
        assignee=["user1"],
        unique="key-1",
        attachment_ids=["1", "2"],
        my_custom_field="value",
    )

    assert issue.id == "1"
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/issues/")
    assert sent_json(call) == {
        "summary": "summary",
        "queue": "TEST",
        "assignee": ["user1"],
        "unique": "key-1",
        "attachmentIds": ["1", "2"],
        "myCustomField": "value",
    }


async def test_move_issue_sends_expand() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.move_issue("TEST-1", "QUEUE", expand="attachments")
    assert client.calls[0]["params"] == {"queue": "QUEUE", "expand": "attachments"}


async def test_find_issues_sends_expand() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.find_issues(query="Key: TEST-1", expand="transitions")
    assert client.calls[0]["params"] == {"expand": "transitions"}


async def test_count_issues_sends_filter_and_query() -> None:
    client = FakeClient(body=b"42")
    tracker = YaTracker(client=client)
    count = await tracker.count_issues(filter_={"queue": "TEST"}, query="Key: TEST-1")

    assert count == 42
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/issues/_count")
    assert sent_json(call) == {"filter": {"queue": "TEST"}, "query": "Key: TEST-1"}


async def test_count_issues_without_arguments_sends_empty_body() -> None:
    client = FakeClient(body=b"0")
    tracker = YaTracker(client=client)
    assert await tracker.count_issues() == 0
    assert sent_json(client.calls[0]) == {}


async def test_get_issue_links_decodes_links() -> None:
    client = FakeClient(body=issue_link_body())
    tracker = YaTracker(client=client)
    links = await tracker.get_issue_links("TEST-1")

    assert links[0].name == "Relates to"
    assert links[0].object.key == "TEST-2"
    call = client.calls[0]
    assert call["method"] == "GET"
    assert call["url"].endswith("/issues/TEST-1/links")


async def test_get_transitions_is_keyed_by_id() -> None:
    client = FakeClient(body=transition_body())
    tracker = YaTracker(client=client)
    transitions = await tracker.get_transitions("TEST-1")

    assert list(transitions.keys()) == ["close"]
    assert transitions["close"].to.key == "closed"
    assert client.calls[0]["url"].endswith("/issues/TEST-1/transitions")


async def test_execute_transition_posts_to_transition_url() -> None:
    client = FakeClient(body=transition_body())
    tracker = YaTracker(client=client)
    transitions = await tracker.get_transitions("TEST-1")

    result = await tracker.execute_transition(
        transitions["close"],
        resolution="fixed",
    )

    assert [t.id for t in result] == ["close"]
    call = client.calls[1]
    assert call["method"] == "POST"
    assert call["url"] == "https://api/issues/1/transitions/close/_execute"
    assert sent_json(call) == {"resolution": "fixed"}


# --- queues -----------------------------------------------------------------


async def test_create_queue_sends_config_payload() -> None:
    client = FakeClient(body=full_queue_body())
    tracker = YaTracker(client=client)
    config = IssueTypeConfig(
        issue_type=IssueType(
            url="https://api/issuetypes/1",
            id="1",
            key="task",
            display="Task",
        ),
        workflow=Workflow(url="https://api/workflows/dev", id="dev", display="dev"),
        resolutions=[
            Resolution(
                url="https://api/resolutions/2",
                id="2",
                key="wontFix",
                display="Won't fix",
            ),
        ],
    )
    queue = await tracker.create_queue(
        key="DESIGN",
        name="Design",
        lead="user1",
        default_type="task",
        default_priority="normal",
        issue_types_config=[config],
    )

    assert queue.key == "DESIGN"
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"].endswith("/queues")
    assert sent_json(call) == {
        "key": "DESIGN",
        "name": "Design",
        "lead": "user1",
        "defaultType": "task",
        "defaultPriority": "normal",
        "issueTypesConfig": [
            {
                "issueType": {
                    "self": "https://api/issuetypes/1",
                    "id": "1",
                    "key": "task",
                    "display": "Task",
                },
                "workflow": {
                    "self": "https://api/workflows/dev",
                    "id": "dev",
                    "display": "dev",
                },
                "resolutions": [
                    {
                        "self": "https://api/resolutions/2",
                        "id": "2",
                        "key": "wontFix",
                        "display": "Won't fix",
                    },
                ],
            },
        ],
    }


async def test_delete_queue() -> None:
    client = FakeClient(body=b"")
    tracker = YaTracker(client=client)
    assert await tracker.delete_queue("TEST") is True

    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"].endswith("/queues/TEST")


async def test_get_queue_versions_decodes_int_ids() -> None:
    client = FakeClient(body=queue_version_body())
    tracker = YaTracker(client=client)
    versions = await tracker.get_queue_versions("TEST")

    assert versions[0].id == 4
    assert versions[0].name == "First release"
    assert versions[0].released is False
    assert client.calls[0]["url"].endswith("/queues/TEST/versions")


# --- attachments ------------------------------------------------------------


async def test_get_attachments_decodes_list() -> None:
    client = FakeClient(body=b"[" + attachment_body() + b"]")
    tracker = YaTracker(client=client)
    attachments = await tracker.get_attachments("TEST-1")

    assert attachments[0].name == "a.txt"
    assert client.calls[0]["url"].endswith("/issues/TEST-1/attachments")


async def test_download_attachment_returns_raw_bytes() -> None:
    client = FakeClient(body=b"raw-bytes")
    tracker = YaTracker(client=client)

    assert await tracker.download_attachment("TEST-1", 1, "a.txt") == b"raw-bytes"
    assert client.calls[0]["url"].endswith("/issues/TEST-1/attachments/1/a.txt")


async def test_download_thumbnail_returns_raw_bytes() -> None:
    client = FakeClient(body=b"png")
    tracker = YaTracker(client=client)

    assert await tracker.download_thumbnail("TEST-1", 1) == b"png"
    assert client.calls[0]["url"].endswith("/issues/TEST-1/thumbnails/1")


async def test_delete_attachment() -> None:
    client = FakeClient(body=b"")
    tracker = YaTracker(client=client)
    assert await tracker.delete_attachment("TEST-1", 1) is True

    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"].endswith("/issues/TEST-1/attachments/1/")


async def test_delete_comment() -> None:
    client = FakeClient(body=b"")
    tracker = YaTracker(client=client)
    assert await tracker.delete_comment("TEST-1", 1) is True

    call = client.calls[0]
    assert call["method"] == "DELETE"
    assert call["url"].endswith("/issues/TEST-1/comments/1")
