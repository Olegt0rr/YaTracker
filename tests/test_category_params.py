"""Tests for query/param handling fixes across category modules.

Covers: priorities.get_priorities, issues.get_issue/find_issues,
comments.get_comments/post_comment, and attached_files.attach_file.
"""

from __future__ import annotations

import io
import json

from yatracker import YaTracker

from tests.conftest import FakeClient, full_issue_body


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


async def test_attach_file_uses_file_field_name() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    await tracker.attach_file("TEST-1", io.BytesIO(b"data"), filename="a.txt")

    form = client.calls[0]["data"]
    field_names = [f[0]["name"] for f in form._fields]
    assert "file" in field_names
    assert "file_data" not in field_names


async def test_upload_temp_file_uses_file_field_name() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    await tracker.upload_temp_file(io.BytesIO(b"data"), filename="a.txt")

    form = client.calls[0]["data"]
    field_names = [f[0]["name"] for f in form._fields]
    assert "file" in field_names
