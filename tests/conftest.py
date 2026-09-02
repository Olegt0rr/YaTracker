"""Shared test fixtures/helpers for the yatracker test suite."""

from __future__ import annotations

import json
from typing import Any

from yatracker import YaTracker
from yatracker.tracker.client import BaseClient


class FakeClient(BaseClient):
    """In-memory client returning canned responses and capturing calls.

    ``org_id``/``token`` default to ``"1"``/``"token"`` so most tests can
    skip credentials entirely, but any keyword (including ``org_id``,
    ``token``, ``cloud_org_id``, ``iam_token``, ...) can still be passed
    through to ``BaseClient`` to override or omit them.
    """

    def __init__(
        self,
        body: bytes = b"{}",
        status: int = 200,
        headers: dict[str, str] | None = None,
        responses: list[tuple[int, bytes, dict[str, str]]] | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("org_id", "1")
        kwargs.setdefault("token", "token")
        super().__init__(**kwargs)
        self.status = status
        self.body = body
        self.headers: dict[str, str] = headers or {}
        # Queue of `(status, body, headers)` triples served one per call;
        # once exhausted (or if never set) the single canned response above
        # is returned for every call.
        self.responses = list(responses or [])
        self.calls: list[dict[str, Any]] = []

    async def _make_request(
        self,
        method: str,
        url: Any,
        **kwargs: Any,
    ) -> tuple[int, bytes, dict[str, str]]:
        self.calls.append({"method": method, "url": url, **kwargs})
        if self.responses:
            return self.responses.pop(0)
        return self.status, self.body, self.headers

    async def close(self) -> None:
        return


def make_tracker(
    payload: Any = None,
    status: int = 200,
) -> tuple[YaTracker, FakeClient]:
    """Build a tracker over a ``FakeClient`` serving one canned JSON payload."""
    body = b"{}" if payload is None else json.dumps(payload).encode()
    client = FakeClient(status=status, body=body)
    return YaTracker(client=client), client


# Sample user from the official docs, embedded into queue/component payloads.
USER: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/users/1111",
    "id": "1111",
    "display": "Имя Фамилия",
    "cloudUid": "ajeppa7dgp53",
    "passportUid": 1111,
}


def full_queue_body(**overrides: Any) -> dict[str, Any]:
    """Build a minimal ``FullQueue`` payload (``GET /queues/{id}`` shape).

    Mirrors ``full_issue_body``; returns a dict so tests can also embed it
    or dump it with ``json.dumps``.
    """
    queue: dict[str, Any] = {
        "self": "https://api.tracker.yandex.net/v3/queues/TEST",
        "id": "3",
        "key": "TEST",
        "version": 5,
        "name": "Test",
        "lead": USER,
        "assignAuto": False,
        "defaultType": {
            "self": "https://api.tracker.yandex.net/v3/issuetypes/1",
            "id": "1",
            "key": "task",
            "display": "Задача",
        },
        "defaultPriority": {
            "self": "https://api.tracker.yandex.net/v3/priorities/3",
            "id": "3",
            "key": "normal",
            "display": "Средний",
        },
    }
    queue.update(overrides)
    return queue


def full_issue_body(**overrides: Any) -> bytes:
    """Build a canned ``FullIssue`` JSON body, with optional field overrides."""
    issue = {
        "self": "https://api/issues/1",
        "id": "1",
        "key": "TEST-1",
        "version": 1,
        "summary": "summary",
        "type": {"self": "t", "id": "1", "key": "bug", "display": "Bug"},
        "priority": {"self": "p", "id": "2", "key": "minor", "display": "Minor"},
        "queue": {"self": "q", "id": "3", "key": "TEST", "display": "Test"},
        "favorite": False,
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "createdBy": {"self": "u", "id": "4", "display": "User"},
        "votes": 0,
        "status": {"self": "s", "id": "5", "key": "open", "display": "Open"},
    }
    issue.update(overrides)
    return json.dumps(issue).encode()


def json_payload(call: dict[str, Any]) -> Any:
    """Decode the JSON body captured in a call.

    Reaches into aiohttp's private ``BytesPayload._value`` in one place so
    tests don't repeat the reach-through.
    """
    return json.loads(bytes(call["data"]._value))


def multipart_dispparams(call: dict[str, Any]) -> Any:
    """Disposition params of the first multipart field captured in a call.

    Reaches into aiohttp's private ``FormData._fields`` in one place so tests
    don't repeat the reach-through.
    """
    return call["data"]._fields[0][0]


def sent_json(call: dict[str, Any]) -> Any:
    """Decode the JSON body of a captured call.

    Reaches into aiohttp's private ``BytesPayload._value`` in one place.
    """
    return json.loads(bytes(call["data"]._value))


def bulk_change_payload(**overrides: Any) -> dict[str, Any]:
    """Build a canned ``BulkChange`` payload, with optional field overrides.

    Shared by the bulk-change and the entities tests: both APIs answer with
    the very same operation object.
    """
    payload: dict[str, Any] = {
        "self": "https://api.tracker.yandex.net/v3/bulkchange/1ab23cd4e5678901abcdef12",
        "id": "1ab23cd4e5678901abcdef12",
        "createdBy": {
            "self": "https://api.tracker.yandex.net/v3/users/1120000000000001",
            "id": "1120000000000001",
            "display": "User Name",
            "passportUid": 12345,
        },
        "createdAt": "2020-12-15T11:52:53.665+0000",
        "status": "CREATED",
        "statusText": "Operation created.",
        "executionChunkPercent": 0,
        "executionIssuePercent": 0,
        "totalIssues": 24,
        "totalCompletedIssues": 0,
    }
    payload.update(overrides)
    return payload


def bulk_change_body(**overrides: Any) -> bytes:
    """Build a canned ``BulkChange`` JSON body, with optional field overrides."""
    return json.dumps(bulk_change_payload(**overrides)).encode()


def comment_body(**overrides: Any) -> bytes:
    """Build a canned ``Comment`` JSON body, with optional field overrides."""
    comment = {
        "self": "https://api/comments/1",
        "id": 1,
        "text": "hello",
        "createdBy": {"self": "u", "id": "1", "display": "User"},
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "version": 1,
    }
    comment.update(overrides)
    return json.dumps(comment).encode()


def attachment_body(**overrides: Any) -> bytes:
    """Build a canned ``Attachment`` JSON body, with optional field overrides."""
    attachment = {
        "self": "https://api/attachments/1",
        "id": "1",
        "name": "a.txt",
        "content": "https://api/attachments/1/a.txt",
        "createdBy": {"self": "u", "id": "1", "display": "User"},
        "createdAt": "2024-01-01T00:00:00.000+0000",
        "mimetype": "text/plain",
        "size": 4,
    }
    attachment.update(overrides)
    return json.dumps(attachment).encode()
