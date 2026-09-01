"""Tests for the client request/response pipeline."""

from __future__ import annotations

import json

import pytest
from yatracker import YaTracker
from yatracker.exceptions import (
    AlreadyExistsError,
    NotAuthorizedError,
    ObjectNotFoundError,
    SufficientRightsError,
    YaTrackerError,
)
from yatracker.types import FullIssue

from tests.conftest import FakeClient, full_issue_body


@pytest.mark.parametrize(
    ("status", "error"),
    [
        (401, NotAuthorizedError),
        (403, SufficientRightsError),
        (404, ObjectNotFoundError),
        (409, AlreadyExistsError),
        (500, YaTrackerError),
    ],
)
async def test_error_statuses_raise_typed_exceptions(status, error) -> None:
    client = FakeClient(status=status, body=b'{"errors": {}}')
    with pytest.raises(error):
        await client.request(method="GET", uri="/issues/TEST-1")


async def test_request_without_payload_sends_no_body() -> None:
    client = FakeClient()
    await client.request(method="GET", uri="/issues/TEST-1")
    assert client.calls[0]["data"] is None


async def test_request_with_payload_sends_json_bytes() -> None:
    client = FakeClient()
    await client.request(method="POST", uri="/issues/", payload={"summary": "s"})
    data = client.calls[0]["data"]
    assert bytes(data._value) == b'{"summary":"s"}'


async def test_get_issue_decodes_full_issue() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    issue = await tracker.get_issue("TEST-1")
    assert isinstance(issue, FullIssue)
    assert issue.key == "TEST-1"
    assert issue.status.key == "open"


async def test_move_issue_params_are_strings() -> None:
    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)
    await tracker.move_issue(
        "TEST-1",
        "QUEUE",
        notify=False,
        notify_author=True,
        move_all_fields=True,
        initial_status=True,
    )
    params = client.calls[0]["params"]
    assert params == {
        "queue": "QUEUE",
        "notify": "false",
        "notifyAuthor": "true",
        "moveAllFields": "true",
        "initialStatus": "true",
    }


async def test_find_issues_sends_filters() -> None:
    client = FakeClient(body=b"[]")
    tracker = YaTracker(client=client)
    await tracker.find_issues(
        filter_={"queue": "TEST"},
        query="Key: TEST-1",
        keys="TEST-1",
        order="+key",
    )
    call = client.calls[0]
    payload = json.loads(bytes(call["data"]._value))
    assert payload == {
        "filter": {"queue": "TEST"},
        "query": "Key: TEST-1",
        "keys": "TEST-1",
    }
    assert call["params"] == {"order": "+key"}
