"""Tests for the import category (issues, comments, links, attachments)."""

from __future__ import annotations

import io
import json
from datetime import date, datetime, timedelta, timezone

import pytest
from yatracker import YaTracker
from yatracker.types import Attachment, Comment, FullIssue, IssueLink, LinkRelationship

from tests.conftest import (
    FakeClient,
    attachment_body,
    comment_body,
    full_issue_body,
    multipart_dispparams,
    sent_json,
)

BASE = "https://api.tracker.yandex.net/v3"

CREATED_AT = datetime(2017, 8, 29, 12, 34, 41, 740000, tzinfo=timezone.utc)
# the API documents `YYYY-MM-DDThh:mm:ss.sss±hhmm` — no colon in the offset
CREATED_AT_ISO = "2017-08-29T12:34:41.740+0000"


def issue_link_body() -> bytes:
    return json.dumps(
        {
            "self": "https://api/issues/TEST-1/links/2",
            "id": 2,
            "type": {
                "self": "https://api/linktypes/relates",
                "id": "relates",
                "inward": "Relates",
                "outward": "Relates",
            },
            "direction": "outward",
            "object": {
                "self": "https://api/issues/TEST-2",
                "id": "2",
                "key": "TEST-2",
                "display": "Test 2",
            },
            "createdBy": {"self": "u", "id": "1", "display": "User"},
            "createdAt": "2017-08-29T12:34:41.740+0000",
            "status": {"self": "s", "id": "5", "key": "open", "display": "Open"},
        },
    ).encode()


# --- import_issue ---------------------------------------------------------


async def test_import_issue_request() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    issue = await tracker.import_issue(
        queue="TEST",
        summary="summary",
        created_at=CREATED_AT,
        created_by="user",
    )

    assert isinstance(issue, FullIssue)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/issues/_import"
    assert sent_json(call) == {
        "queue": "TEST",
        "summary": "summary",
        "createdAt": CREATED_AT_ISO,
        "createdBy": "user",
    }


async def test_import_issue_camel_cases_and_omits_none() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.import_issue(
        queue="TEST",
        summary="summary",
        created_at=CREATED_AT,
        created_by=1234,
        key="TEST-1",
        updated_at=CREATED_AT,
        updated_by="editor",
        resolved_at=CREATED_AT,
        resolved_by="closer",
        resolution=2,
        status=3,
        type_=4,
        priority=5,
        description="text",
        assignee="assignee",
        deadline=date(2017, 8, 30),
        start=date(2017, 8, 29),
        end=date(2017, 8, 31),
        unique="uniq",
        affected_versions=[1],
        story_points=1.0,
        spent=3600000,
    )

    payload = sent_json(client.calls[0])
    assert payload == {
        "queue": "TEST",
        "summary": "summary",
        "createdAt": CREATED_AT_ISO,
        "createdBy": 1234,
        "key": "TEST-1",
        "updatedAt": CREATED_AT_ISO,
        "updatedBy": "editor",
        "resolvedAt": CREATED_AT_ISO,
        "resolvedBy": "closer",
        "resolution": 2,
        "status": 3,
        "type": 4,
        "priority": 5,
        "description": "text",
        "assignee": "assignee",
        "deadline": "2017-08-30",
        "start": "2017-08-29",
        "end": "2017-08-31",
        "unique": "uniq",
        "affectedVersions": [1],
        "storyPoints": 1.0,
        "spent": 3600000,
    }
    assert "issue_id" not in payload
    assert "_type" not in payload
    assert "type_" not in payload


async def test_import_issue_passes_str_timestamps_verbatim() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.import_issue(
        queue="TEST",
        summary="summary",
        created_at="2017-08-29T12:34:41.740+0300",
        created_by="user",
        deadline="2017-08-30",
    )

    payload = sent_json(client.calls[0])
    assert payload["createdAt"] == "2017-08-29T12:34:41.740+0300"
    assert payload["deadline"] == "2017-08-30"


async def test_import_issue_formats_non_utc_offset_and_datetime_dates() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    moscow = timezone(timedelta(hours=3))
    await tracker.import_issue(
        queue="TEST",
        summary="summary",
        created_at=datetime(2017, 8, 29, 15, 34, 41, 7000, tzinfo=moscow),
        created_by="user",
        deadline=CREATED_AT,  # a datetime is truncated to its date part
    )

    payload = sent_json(client.calls[0])
    assert payload["createdAt"] == "2017-08-29T15:34:41.007+0300"
    assert payload["deadline"] == "2017-08-29"


async def test_import_issue_supports_type_override() -> None:
    class MyIssue(FullIssue):
        pass

    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    issue = await tracker.import_issue(
        queue="TEST",
        summary="summary",
        created_at=CREATED_AT,
        created_by="user",
        _type=MyIssue,
    )

    assert isinstance(issue, MyIssue)
    assert "_type" not in sent_json(client.calls[0])


async def test_import_issue_warns_on_naive_datetime() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    with pytest.warns(UserWarning, match="naive datetime") as record:
        await tracker.import_issue(
            queue="TEST",
            summary="summary",
            created_at=datetime(2017, 8, 29, 12, 34, 41, 740000),  # noqa: DTZ001
            created_by="user",
        )

    assert sent_json(client.calls[0])["createdAt"] == "2017-08-29T12:34:41.740"
    # the warning must point at the caller, not at library internals
    assert record[0].filename == __file__


async def test_import_issue_rejects_half_set_updated_pair() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    with pytest.raises(ValueError, match="updated_at"):
        await tracker.import_issue(
            queue="TEST",
            summary="summary",
            created_at=CREATED_AT,
            created_by="user",
            updated_at=CREATED_AT,
        )

    assert client.calls == []


async def test_import_issue_rejects_incomplete_resolved_triple() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    with pytest.raises(ValueError, match="resolved_at"):
        await tracker.import_issue(
            queue="TEST",
            summary="summary",
            created_at=CREATED_AT,
            created_by="user",
            resolved_at=CREATED_AT,
            resolved_by="closer",
        )

    assert client.calls == []


async def test_import_issue_treats_zero_as_set() -> None:
    """`0` is a valid id: the all-or-none check must use `is not None`."""
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.import_issue(
        queue="TEST",
        summary="summary",
        created_at=CREATED_AT,
        created_by="user",
        resolved_at=CREATED_AT,
        resolved_by=0,
        resolution=0,
    )

    payload = sent_json(client.calls[0])
    assert payload["resolvedBy"] == 0
    assert payload["resolution"] == 0


# --- import_comment -------------------------------------------------------


async def test_import_comment_request() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    comment = await tracker.import_comment(
        "TEST-1",
        text="imported",
        created_at=CREATED_AT,
        created_by="user",
    )

    assert isinstance(comment, Comment)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/issues/TEST-1/comments/_import"
    assert sent_json(call) == {
        "text": "imported",
        "createdAt": CREATED_AT_ISO,
        "createdBy": "user",
    }


async def test_import_comment_with_updated_pair() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    await tracker.import_comment(
        "TEST-1",
        text="imported",
        created_at=CREATED_AT,
        created_by=1234,
        updated_at="2017-08-30T12:34:41.740+0000",
        updated_by=5678,
    )

    payload = sent_json(client.calls[0])
    assert payload["updatedAt"] == "2017-08-30T12:34:41.740+0000"
    assert payload["updatedBy"] == 5678
    assert "issue_id" not in payload
    assert "issueId" not in payload


async def test_import_comment_rejects_half_set_updated_pair() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    with pytest.raises(ValueError, match="updated_by"):
        await tracker.import_comment(
            "TEST-1",
            text="imported",
            created_at=CREATED_AT,
            created_by="user",
            updated_by="editor",
        )

    assert client.calls == []


async def test_import_comment_warns_on_naive_datetime() -> None:
    client = FakeClient(body=comment_body())
    tracker = YaTracker(client=client)
    with pytest.warns(UserWarning, match="naive datetime"):
        await tracker.import_comment(
            "TEST-1",
            text="imported",
            created_at=datetime(2017, 8, 29, 12, 34, 41, 740000),  # noqa: DTZ001
            created_by="user",
        )


# --- import_link ----------------------------------------------------------


async def test_import_link_request() -> None:
    client = FakeClient(body=issue_link_body())
    tracker = YaTracker(client=client)
    link = await tracker.import_link(
        "TEST-1",
        relationship=LinkRelationship.RELATES,
        issue="TEST-2",
        created_at=CREATED_AT,
        created_by="user",
    )

    assert isinstance(link, IssueLink)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/issues/TEST-1/links/_import"
    assert sent_json(call) == {
        "relationship": "relates",
        "issue": "TEST-2",
        "createdAt": CREATED_AT_ISO,
        "createdBy": "user",
    }


async def test_import_link_accepts_plain_string_relationship() -> None:
    client = FakeClient(body=issue_link_body())
    tracker = YaTracker(client=client)
    await tracker.import_link(
        "TEST-1",
        relationship="is dependent by",
        issue="TEST-2",
        created_at=CREATED_AT,
        created_by="user",
        updated_at=CREATED_AT,
        updated_by="editor",
    )

    payload = sent_json(client.calls[0])
    assert payload["relationship"] == "is dependent by"
    assert payload["updatedAt"] == CREATED_AT_ISO
    assert payload["updatedBy"] == "editor"


async def test_import_link_rejects_half_set_updated_pair() -> None:
    client = FakeClient(body=issue_link_body())
    tracker = YaTracker(client=client)
    with pytest.raises(ValueError, match="updated_at"):
        await tracker.import_link(
            "TEST-1",
            relationship=LinkRelationship.CLONE,
            issue="TEST-2",
            created_at=CREATED_AT,
            created_by="user",
            updated_at=CREATED_AT,
        )

    assert client.calls == []


# --- import_attachment ----------------------------------------------------


async def test_import_attachment_request() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    attachment = await tracker.import_attachment(
        "TEST-1",
        io.BytesIO(b"data"),
        filename="a.txt",
        created_at=CREATED_AT,
        created_by=1234,
    )

    assert isinstance(attachment, Attachment)
    call = client.calls[0]
    assert call["method"] == "POST"
    assert call["url"] == f"{BASE}/issues/TEST-1/attachments/_import"

    dispparams = multipart_dispparams(call)
    assert dispparams["name"] == "file_data"
    assert dispparams["filename"] == "a.txt"
    assert call["params"] == {
        "filename": "a.txt",
        "createdAt": CREATED_AT_ISO,
        "createdBy": "1234",
    }


async def test_import_attachment_to_comment() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    await tracker.import_attachment(
        "TEST-1",
        io.BytesIO(b"data"),
        filename="a.txt",
        created_at="2017-08-29T12:34:41.740+0000",
        created_by="user",
        comment_id=42,
    )

    call = client.calls[0]
    assert call["url"] == f"{BASE}/issues/TEST-1/comments/42/attachments/_import"
    assert call["params"]["createdAt"] == "2017-08-29T12:34:41.740+0000"
    assert call["params"]["createdBy"] == "user"


async def test_import_attachment_warns_on_naive_datetime() -> None:
    client = FakeClient(body=attachment_body())
    tracker = YaTracker(client=client)
    with pytest.warns(UserWarning, match="naive datetime"):
        await tracker.import_attachment(
            "TEST-1",
            io.BytesIO(b"data"),
            filename="a.txt",
            created_at=datetime(2017, 8, 29, 12, 34, 41, 740000),  # noqa: DTZ001
            created_by="user",
        )
