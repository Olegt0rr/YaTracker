"""Tests for response-header plumbing and the scroll pagination helper."""

from __future__ import annotations

import json
from typing import Any

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
            MyIssue,
        )
    ]
    assert isinstance(issues[0], MyIssue)


async def test_iter_issues_folds_queue_into_filter() -> None:
    """Scroll rejects the `queue` search form, so it becomes a filter."""
    client = FakeClient(responses=[(200, b"[]", {})])
    tracker = YaTracker(client=client)

    _ = [
        issue
        async for issue in tracker.iter_issues(
            filter_={"assignee": "me"},
            queue="TEST",
        )
    ]

    body = json.loads(bytes(client.calls[0]["data"]._value))
    assert body == {"filter": {"assignee": "me", "queue": "TEST"}}
    assert "queue" not in body


async def test_iter_issues_releases_the_scroll_on_early_break() -> None:
    """Leaving the loop early must free the server-side snapshots."""
    client = FakeClient(
        responses=[
            (
                200,
                issues_body("TEST-1", "TEST-2"),
                {"X-Scroll-Id": "scroll-1", "X-Scroll-Token": "token-1"},
            ),
            (
                200,
                issues_body("TEST-3"),
                {"X-Scroll-Id": "scroll-2", "X-Scroll-Token": "token-2"},
            ),
            (200, b"{}", {}),
        ],
    )
    tracker = YaTracker(client=client)

    seen = []
    issues = tracker.iter_issues(query="Queue: TEST")
    async for issue in issues:
        seen.append(issue.key)
        if len(seen) == 3:
            break
    # `break` only suspends the generator; the release runs when it is
    # closed (`aclose()`, or the loop's `shutdown_asyncgens`).
    await issues.aclose()

    assert seen == ["TEST-1", "TEST-2", "TEST-3"]

    clear = client.calls[-1]
    assert clear["method"] == "POST"
    assert clear["url"].endswith("/system/search/scroll/_clear")
    assert json.loads(bytes(clear["data"]._value)) == {
        "scroll-1": "token-1",
        "scroll-2": "token-2",
    }
    # exactly one release call
    assert (
        sum(
            call["url"].endswith("/system/search/scroll/_clear")
            for call in client.calls
        )
        == 1
    )


async def test_iter_issues_does_not_release_when_the_scroll_is_exhausted() -> None:
    client = FakeClient(
        responses=[
            (
                200,
                issues_body("TEST-1"),
                {"X-Scroll-Id": "scroll-1", "X-Scroll-Token": "token-1"},
            ),
            (200, b"[]", {}),
        ],
    )
    tracker = YaTracker(client=client)

    _ = [issue async for issue in tracker.iter_issues()]

    assert len(client.calls) == 2
    assert not any(
        call["url"].endswith("/system/search/scroll/_clear") for call in client.calls
    )


async def test_iter_issues_releases_with_an_empty_scroll_token() -> None:
    """`X-Scroll-Token` is unused in API v3, so it is often missing.

    The snapshot still has to be released, with an empty token.
    """
    client = FakeClient(
        responses=[
            (200, issues_body("TEST-1"), {"X-Scroll-Id": "scroll-1"}),
            (200, b"{}", {}),
        ],
    )
    tracker = YaTracker(client=client)

    issues = tracker.iter_issues()
    async for _issue in issues:
        break
    await issues.aclose()

    assert len(client.calls) == 2
    clear = client.calls[1]
    assert clear["url"].endswith("/system/search/scroll/_clear")
    assert json.loads(bytes(clear["data"]._value)) == {"scroll-1": ""}


async def test_iter_issues_drops_first_request_only_params_on_page_two() -> None:
    """`scrollType`/`perScroll` belong to the first request of a series."""
    client = FakeClient(
        responses=[
            (200, issues_body("TEST-1"), {"X-Scroll-Id": "scroll-1"}),
            (200, b"[]", {}),
        ],
    )
    tracker = YaTracker(client=client)

    _ = [
        issue
        async for issue in tracker.iter_issues(
            order="+key",
            expand="attachments",
            scroll_ttl_millis=10000,
            fields="summary",
        )
    ]

    assert client.calls[1]["params"] == {
        "scrollId": "scroll-1",
        "order": "+key",
        "expand": "attachments",
        "scrollTTLMillis": "10000",
        "fields": "summary",
    }


async def test_iter_issues_second_page_without_ttl_sends_only_scroll_id() -> None:
    client = FakeClient(
        responses=[
            (200, issues_body("TEST-1"), {"X-Scroll-Id": "scroll-1"}),
            (200, b"[]", {}),
        ],
    )
    tracker = YaTracker(client=client)

    _ = [issue async for issue in tracker.iter_issues()]

    assert client.calls[1]["params"] == {"scrollId": "scroll-1"}


async def test_iter_issues_swallows_a_failing_release() -> None:
    client = FakeClient(
        responses=[
            (
                200,
                issues_body("TEST-1"),
                {"X-Scroll-Id": "scroll-1", "X-Scroll-Token": "token-1"},
            ),
            (500, b"{}", {}),
        ],
    )
    tracker = YaTracker(client=client)

    issues = tracker.iter_issues()
    async for _issue in issues:
        break
    # a failing release must not surface
    await issues.aclose()

    assert len(client.calls) == 2
    assert client.calls[1]["url"].endswith("/system/search/scroll/_clear")


async def test_iter_issues_swallows_a_transport_error_on_release() -> None:
    """A transport error is not a `YaTrackerError`, and must not escape."""
    released: list[str] = []

    class BoomClient(FakeClient):
        async def _make_request(
            self,
            method: str,
            url: Any,
            **kwargs: Any,
        ) -> tuple[int, bytes, dict[str, str]]:
            if str(url).endswith("/system/search/scroll/_clear"):
                released.append(str(url))
                msg = "connection reset"
                raise RuntimeError(msg)
            return await super()._make_request(method, url, **kwargs)

    client = BoomClient(
        responses=[
            (
                200,
                issues_body("TEST-1"),
                {"X-Scroll-Id": "scroll-1", "X-Scroll-Token": "token-1"},
            ),
        ],
    )
    tracker = YaTracker(client=client)

    issues = tracker.iter_issues()
    async for _issue in issues:
        break
    await issues.aclose()

    # the release was attempted and the transport error stayed inside
    assert len(released) == 1


async def test_iter_issues_skips_the_release_when_the_client_is_closed() -> None:
    """A closed client could not release anything anyway."""
    client = FakeClient(
        responses=[
            (
                200,
                issues_body("TEST-1"),
                {"X-Scroll-Id": "scroll-1", "X-Scroll-Token": "token-1"},
            ),
        ],
    )
    tracker = YaTracker(client=client)

    issues = tracker.iter_issues()
    async for _issue in issues:
        break

    client._closed = True
    await issues.aclose()

    assert len(client.calls) == 1
    assert not any(
        call["url"].endswith("/system/search/scroll/_clear") for call in client.calls
    )


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
