"""Tests for response-header plumbing and the scroll pagination helper."""

from __future__ import annotations

import json

from yatracker import YaTracker
from yatracker.types import FullIssue

from tests.conftest import FakeClient, full_issue_body


def issues_body(*keys: str) -> bytes:
    issues = [json.loads(full_issue_body(key=key, id=key)) for key in keys]
    return json.dumps(issues).encode()


async def test_request_with_headers_returns_headers() -> None:
    client = FakeClient(body=b"{}", headers={"X-Total-Count": "42"})
    body, headers = await client.request_with_headers(
        method="GET",
        uri="/issues/TEST-1",
    )
    assert body == b"{}"
    assert headers["X-Total-Count"] == "42"


async def test_request_drops_headers() -> None:
    client = FakeClient(body=b"{}", headers={"X-Total-Count": "42"})
    assert await client.request(method="GET", uri="/issues/TEST-1") == b"{}"


async def test_iter_issues_walks_pages_until_empty() -> None:
    client = FakeClient(
        responses=[
            (200, issues_body("TEST-1", "TEST-2"), {"X-Scroll-Id": "scroll-1"}),
            (200, b"[]", {"X-Scroll-Id": "scroll-2"}),
        ],
    )
    tracker = YaTracker(client=client)

    issues = [issue async for issue in tracker.iter_issues(query="Queue: TEST")]

    assert [issue.key for issue in issues] == ["TEST-1", "TEST-2"]
    assert len(client.calls) == 2

    first, second = client.calls
    assert first["method"] == "POST"
    assert first["url"].endswith("/issues/_search")
    assert first["params"] == {"scrollType": "sorted", "perScroll": "100"}
    assert "scrollId" not in first["params"]
    assert second["params"]["scrollId"] == "scroll-1"
    assert json.loads(bytes(second["data"]._value)) == {"query": "Queue: TEST"}


async def test_iter_issues_stops_without_scroll_header() -> None:
    client = FakeClient(
        responses=[
            (200, issues_body("TEST-1"), {}),
            (200, issues_body("TEST-2"), {"X-Scroll-Id": "scroll-2"}),
        ],
    )
    tracker = YaTracker(client=client)

    issues = [issue async for issue in tracker.iter_issues()]

    assert [issue.key for issue in issues] == ["TEST-1"]
    assert len(client.calls) == 1


async def test_iter_issues_reads_scroll_id_case_insensitively() -> None:
    client = FakeClient(
        responses=[
            (200, issues_body("TEST-1"), {"x-scroll-id": "scroll-1"}),
            (200, b"[]", {}),
        ],
    )
    tracker = YaTracker(client=client)

    issues = [issue async for issue in tracker.iter_issues()]

    assert len(issues) == 1
    assert client.calls[1]["params"]["scrollId"] == "scroll-1"


async def test_iter_issues_sends_scroll_options_and_params() -> None:
    client = FakeClient(responses=[(200, b"[]", {})])
    tracker = YaTracker(client=client)

    issues = [
        issue
        async for issue in tracker.iter_issues(
            filter_={"queue": "TEST"},
            order="+key",
            expand="attachments",
            scroll_type="unsorted",
            per_scroll=50,
            scroll_ttl_millis=5000,
            fields="summary",
        )
    ]

    assert issues == []
    call = client.calls[0]
    assert call["params"] == {
        "scrollType": "unsorted",
        "perScroll": "50",
        "order": "+key",
        "expand": "attachments",
        "scrollTTLMillis": "5000",
        "fields": "summary",
    }
    # scroll/paging options must not leak into the request body
    assert json.loads(bytes(call["data"]._value)) == {"filter": {"queue": "TEST"}}


async def test_iter_issues_accepts_positional_type() -> None:
    class MyIssue(FullIssue):
        pass

    client = FakeClient(responses=[(200, issues_body("TEST-1"), {})])
    tracker = YaTracker(client=client)

    issues = [
        issue
        async for issue in tracker.iter_issues(
            None,
            None,
            None,
            None,
            None,
            None,
            MyIssue,
        )
    ]
    assert isinstance(issues[0], MyIssue)


async def test_get_issue_accepts_positional_type() -> None:
    class MyIssue(FullIssue):
        pass

    client = FakeClient(body=full_issue_body())
    tracker = YaTracker(client=client)

    issue = await tracker.get_issue("TEST-1", None, MyIssue)
    assert isinstance(issue, MyIssue)


async def test_find_issues_accepts_positional_type() -> None:
    class MyIssue(FullIssue):
        pass

    client = FakeClient(body=issues_body("TEST-1"))
    tracker = YaTracker(client=client)

    issues = await tracker.find_issues(
        {"queue": "TEST"},
        None,
        None,
        None,
        None,
        None,
        MyIssue,
    )
    assert isinstance(issues[0], MyIssue)
