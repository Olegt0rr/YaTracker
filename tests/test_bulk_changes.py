"""Tests for bulk change support (GitHub issue #22).

Covers bulk_operations.BulkChanges: bulk_update_issues,
bulk_transition_issues, bulk_move_issues, get_bulk_change,
get_bulk_change_issues, wait_bulk_change, the BulkChange/BulkChangeIssue/
BulkChangeError types, and the model shortcuts they expose.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any

import pytest
import yatracker.types as types_module
from yatracker import YaTracker
from yatracker.exceptions import ObjectNotFoundError
from yatracker.tracker.categories.bulk_operations import NOT_FOUND_RETRIES
from yatracker.types import (
    BulkChange,
    BulkChangeError,
    BulkChangeIssue,
    FullIssue,
    FullQueue,
    Issue,
    Queue,
    Status,
    Transition,
    User,
)
from yatracker.types.bulk_change import TERMINAL_STATUSES

from tests.conftest import FakeClient, full_issue_body, sent_json

# --- payload builders --------------------------------------------------


def bulk_change_payload(**overrides: Any) -> dict[str, Any]:
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
    return json.dumps(bulk_change_payload(**overrides)).encode()


def bulk_change_issue_payload(**overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "issue": {
            "self": "https://api.tracker.yandex.net/v3/issues/TEST-1",
            "id": "593cd211ef668a33abcdef12",
            "key": "TEST-1",
            "display": "Test",
        },
        "status": "FAILED",
        "statusText": "Edit failed",
        "error": {
            "errors": {
                "resolution": (
                    "You cannot use the selected resolution for this "
                    "type of issue in this queue."
                ),
            },
            "errorMessages": [],
        },
    }
    payload.update(overrides)
    return payload


def patch_sleep(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """Replace ``asyncio.sleep`` with a no-op for the duration of the test.

    The bulk_operations module calls ``asyncio.sleep`` through the ``asyncio``
    module, so the patch is process-wide, not module-scoped.

    Returns the list into which each requested delay is recorded.
    """
    delays: list[float] = []

    async def fake_sleep(seconds: float) -> None:
        delays.append(seconds)

    monkeypatch.setattr(
        "yatracker.tracker.categories.bulk_operations.asyncio.sleep",
        fake_sleep,
    )
    return delays


# --- bulk_update_issues --------------------------------------------------


class TestBulkUpdateIssues:
    async def test_sends_post_to_update_url(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1", "TEST-2"],
            values={"priority": "critical"},
        )

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/bulkchange/_update")

    async def test_body_contains_issues_and_values(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1", "TEST-2"],
            values={"priority": "critical"},
        )

        assert sent_json(client.calls[0]) == {
            "issues": ["TEST-1", "TEST-2"],
            "values": {"priority": "critical"},
        }

    async def test_issues_given_as_models_use_key(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        short_issue = Issue(
            url="https://api/issues/3",
            id="3",
            key="TEST-3",
            display="Test 3",
        )
        full_issue = FullIssue.model_validate(
            json.loads(full_issue_body(key="TEST-4", id="4")),
        )

        await tracker.bulk_update_issues(
            [short_issue, full_issue, "TEST-5"],
            values={"priority": "critical"},
        )

        assert sent_json(client.calls[0])["issues"] == [
            "TEST-3",
            "TEST-4",
            "TEST-5",
        ]

    async def test_issues_given_as_query_filter_string_is_passed_through(
        self,
    ) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        query = "Summary: Test Assignee: username"
        await tracker.bulk_update_issues(query, values={"priority": "critical"})

        assert sent_json(client.calls[0])["issues"] == query

    async def test_values_merged_with_kwargs_and_kwargs_win(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"priority": "critical", "summary": "old"},
            type_={"name": "Task"},
            summary="new",
            attachment_ids=["1", "2"],
        )

        assert sent_json(client.calls[0])["values"] == {
            "priority": "critical",
            "summary": "new",
            "type": {"name": "Task"},
            "attachmentIds": ["1", "2"],
        }

    async def test_none_kwargs_are_dropped_from_values(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"priority": "critical"},
            summary=None,
        )

        assert sent_json(client.calls[0])["values"] == {"priority": "critical"}

    async def test_base_model_inside_values_is_converted_to_dict(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        assignee = User(url="https://api/users/1", id="1", display="User")
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"assignee": assignee},
        )

        assert sent_json(client.calls[0])["values"]["assignee"] == {
            "self": "https://api/users/1",
            "id": "1",
            "display": "User",
        }

    async def test_notify_true_sends_query_param(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"priority": "critical"},
            notify=True,
        )
        assert client.calls[0]["params"] == {"notify": "true"}

    async def test_notify_false_sends_query_param(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"priority": "critical"},
            notify=False,
        )
        assert client.calls[0]["params"] == {"notify": "false"}

    async def test_notify_omitted_sends_no_params(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"priority": "critical"},
        )
        assert client.calls[0]["params"] is None

    async def test_empty_issues_raises_value_error(self) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(ValueError, match="At least one issue"):
            await tracker.bulk_update_issues([], values={"priority": "critical"})

    async def test_empty_values_raises_value_error(self) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(ValueError, match="at least one field"):
            await tracker.bulk_update_issues(["TEST-1"], values={})

    async def test_no_values_and_no_kwargs_raises_value_error(self) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(ValueError, match="at least one field"):
            await tracker.bulk_update_issues(["TEST-1"])

    async def test_snake_case_values_keys_are_camel_cased(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"attachment_ids": ["1"], "storyPoints": 3},
        )

        assert sent_json(client.calls[0])["values"] == {
            "attachmentIds": ["1"],
            "storyPoints": 3,
        }

    async def test_local_field_keys_are_kept_verbatim(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        local_field = "64a51c6d866ea82411abe756--userId"
        await tracker.bulk_update_issues(["TEST-1"], values={local_field: 42})

        assert sent_json(client.calls[0])["values"] == {local_field: 42}

    async def test_kwargs_override_same_field_given_in_snake_case(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"story_points": 1},
            story_points=2,
        )

        assert sent_json(client.calls[0])["values"] == {"storyPoints": 2}

    async def test_local_field_key_in_kwargs_is_kept_verbatim(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        local_field = "64a51c6d866ea82411abe756--userId"
        await tracker.bulk_update_issues(["TEST-1"], **{local_field: 42})

        assert sent_json(client.calls[0])["values"] == {local_field: 42}

    async def test_local_field_key_in_both_sources_is_merged_once(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        local_field = "64a51c6d866ea82411abe756--userId"
        await tracker.bulk_update_issues(
            ["TEST-1"],
            values={local_field: 1},
            **{local_field: 2},
        )

        assert sent_json(client.calls[0])["values"] == {local_field: 2}

    @pytest.mark.parametrize("query", ["", "   "])
    async def test_empty_query_filter_raises_value_error(self, query: str) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(ValueError, match="filter"):
            await tracker.bulk_update_issues(query, values={"priority": "minor"})

    async def test_returns_parsed_bulk_change(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        result = await tracker.bulk_update_issues(
            ["TEST-1"],
            values={"priority": "critical"},
        )

        assert isinstance(result, BulkChange)
        assert result.id == "1ab23cd4e5678901abcdef12"
        assert result.created_at == datetime(
            2020,
            12,
            15,
            11,
            52,
            53,
            665000,
            tzinfo=timezone.utc,
        )
        assert isinstance(result.created_by, User)
        assert result.created_by.display == "User Name"


# --- bulk_transition_issues -----------------------------------------------


class TestBulkTransitionIssues:
    async def test_sends_post_to_transition_url(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_transition_issues(["TEST-1"], "close")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/bulkchange/_transition")

    async def test_body_keys_are_exactly_transition_issues_and_values(
        self,
    ) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_transition_issues(
            ["TEST-1", "TEST-2"],
            "close",
            values={"resolution": "fixed"},
        )

        assert sent_json(client.calls[0]) == {
            "transition": "close",
            "issues": ["TEST-1", "TEST-2"],
            "values": {"resolution": "fixed"},
        }

    async def test_values_key_is_omitted_when_empty(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_transition_issues(["TEST-1"], "close")

        body = sent_json(client.calls[0])
        assert set(body.keys()) == {"transition", "issues"}

    async def test_transition_instance_uses_id(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        status = Status(
            url="https://api/statuses/5",
            id="5",
            key="closed",
            display="Closed",
        )
        transition = Transition(
            id="close",
            url="https://api/issues/1/transitions/close",
            display="Close",
            to=status,
        )
        await tracker.bulk_transition_issues(["TEST-1"], transition)

        assert sent_json(client.calls[0])["transition"] == "close"

    async def test_issue_models_are_normalised_to_keys(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        short_issue = Issue(
            url="https://api/issues/3",
            id="3",
            key="TEST-3",
            display="Test 3",
        )
        await tracker.bulk_transition_issues([short_issue], "close")

        assert sent_json(client.calls[0])["issues"] == ["TEST-3"]

    async def test_bare_str_issues_raises_type_error(self) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(TypeError):
            await tracker.bulk_transition_issues("Summary: Test", "close")

    async def test_notify_true_sends_query_param(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_transition_issues(["TEST-1"], "close", notify=True)
        assert client.calls[0]["params"] == {"notify": "true"}

    async def test_notify_false_sends_query_param(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_transition_issues(["TEST-1"], "close", notify=False)
        assert client.calls[0]["params"] == {"notify": "false"}

    async def test_notify_omitted_sends_no_params(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_transition_issues(["TEST-1"], "close")
        assert client.calls[0]["params"] is None


# --- bulk_move_issues -------------------------------------------------------


class TestBulkMoveIssues:
    async def test_sends_post_to_move_url(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(["TEST-1"], "NEWQUEUE")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/v3/bulkchange/_move")

    async def test_queue_instance_uses_key(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        queue = Queue(
            url="https://api/queues/NEWQ",
            id="1",
            key="NEWQ",
            display="New Q",
        )
        await tracker.bulk_move_issues(["TEST-1"], queue)

        assert sent_json(client.calls[0])["queue"] == "NEWQ"

    async def test_full_queue_instance_uses_key(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        queue = FullQueue.model_validate(
            {
                "self": "https://api.tracker.yandex.net/v3/queues/ARCH",
                "id": "3",
                "key": "ARCH",
                "version": 1,
                "name": "Archive",
                "lead": {"self": "u", "id": "1", "display": "User"},
                "assignAuto": False,
                "defaultType": {"self": "t", "id": "1", "key": "task", "display": "T"},
                "defaultPriority": {
                    "self": "p",
                    "id": "2",
                    "key": "normal",
                    "display": "N",
                },
            },
        )
        await tracker.bulk_move_issues(["TEST-1"], queue)

        assert sent_json(client.calls[0])["queue"] == "ARCH"

    async def test_notify_false_sends_query_param(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(["TEST-1"], "NEWQ", notify=False)

        assert client.calls[0]["params"] == {"notify": "false"}

    async def test_move_all_fields_and_initial_status_omitted_when_none(
        self,
    ) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(["TEST-1"], "NEWQUEUE")

        body = sent_json(client.calls[0])
        assert body == {"queue": "NEWQUEUE", "issues": ["TEST-1"]}
        assert "moveAllFields" not in body
        assert "initialStatus" not in body
        assert "values" not in body

    async def test_move_all_fields_and_initial_status_included_when_set(
        self,
    ) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(
            ["TEST-1"],
            "NEWQUEUE",
            move_all_fields=True,
            initial_status=False,
        )

        body = sent_json(client.calls[0])
        assert body["moveAllFields"] is True
        assert body["initialStatus"] is False

    async def test_values_included_when_non_empty(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(
            ["TEST-1"],
            "NEWQUEUE",
            values={"priority": "minor"},
        )

        assert sent_json(client.calls[0])["values"] == {"priority": "minor"}

    async def test_bare_str_issues_raises_type_error(self) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(TypeError):
            await tracker.bulk_move_issues("Summary: Test", "NEWQUEUE")

    async def test_notify_true_sends_query_param(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(["TEST-1"], "NEWQUEUE", notify=True)
        assert client.calls[0]["params"] == {"notify": "true"}

    async def test_notify_omitted_sends_no_params(self) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        await tracker.bulk_move_issues(["TEST-1"], "NEWQUEUE")
        assert client.calls[0]["params"] is None


# --- get_bulk_change / get_bulk_change_issues ------------------------------


class TestGetBulkChange:
    async def test_accepts_bulk_change_instance(self) -> None:
        client = FakeClient(body=bulk_change_body(id="xyz987", status="COMPLETE"))
        tracker = YaTracker(client=client)
        bulk_change = BulkChange.model_validate(bulk_change_payload(id="xyz987"))
        result = await tracker.get_bulk_change(bulk_change)

        assert result.status == "COMPLETE"
        assert client.calls[0]["url"].endswith("/v3/bulkchange/xyz987")

    async def test_sends_get_to_bulkchange_id(self) -> None:
        client = FakeClient(
            body=bulk_change_body(
                status="RUNNING",
                executionChunkPercent=12.5,
                executionIssuePercent=20.0,
                totalIssues=24,
                totalCompletedIssues=5,
            ),
        )
        tracker = YaTracker(client=client)
        result = await tracker.get_bulk_change("1ab23cd4e5678901abcdef12")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/bulkchange/1ab23cd4e5678901abcdef12")
        assert result.total_issues == 24
        assert result.total_completed_issues == 5
        assert result.execution_chunk_percent == pytest.approx(12.5)
        assert result.execution_issue_percent == pytest.approx(20.0)
        assert isinstance(result.execution_chunk_percent, float)
        assert isinstance(result.execution_issue_percent, float)


class TestGetBulkChangeIssues:
    async def test_accepts_bulk_change_instance(self) -> None:
        client = FakeClient(body=b"[]")
        tracker = YaTracker(client=client)
        bulk_change = BulkChange.model_validate(bulk_change_payload(id="xyz987"))
        result = await tracker.get_bulk_change_issues(bulk_change)

        assert result == []
        assert client.calls[0]["url"].endswith("/v3/bulkchange/xyz987/issues")

    async def test_non_string_error_values_are_decoded(self) -> None:
        item = bulk_change_issue_payload(
            error={"errors": {"tags": ["bad", "worse"]}, "errorMessages": ["x"]},
        )
        client = FakeClient(body=json.dumps([item]).encode())
        tracker = YaTracker(client=client)
        result = await tracker.get_bulk_change_issues("1ab23cd4e5678901abcdef12")

        assert result[0].error is not None
        assert result[0].error.errors == {"tags": ["bad", "worse"]}
        assert result[0].error.error_messages == ["x"]

    async def test_sends_get_to_issues_sub_resource(self) -> None:
        second_item = {
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-2",
                "id": "593cd211ef668a33abcdef13",
                "key": "TEST-2",
                "display": "Test 2",
            },
            "status": "FAILED",
        }
        client = FakeClient(
            body=json.dumps(
                [bulk_change_issue_payload(), second_item],
            ).encode(),
        )
        tracker = YaTracker(client=client)
        result = await tracker.get_bulk_change_issues("1ab23cd4e5678901abcdef12")

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/bulkchange/1ab23cd4e5678901abcdef12/issues",
        )
        assert len(result) == 2
        assert all(isinstance(item, BulkChangeIssue) for item in result)

    async def test_decodes_issue_status_and_error(self) -> None:
        client = FakeClient(
            body=json.dumps([bulk_change_issue_payload()]).encode(),
        )
        tracker = YaTracker(client=client)
        result = await tracker.get_bulk_change_issues("1ab23cd4e5678901abcdef12")

        item = result[0]
        assert item.issue.key == "TEST-1"
        assert item.status == "FAILED"
        assert isinstance(item.error, BulkChangeError)
        assert item.error.errors == {
            "resolution": (
                "You cannot use the selected resolution for this "
                "type of issue in this queue."
            ),
        }
        assert item.error.error_messages == []

    async def test_item_without_error_key_has_none_error(self) -> None:
        item_without_error = {
            "issue": {
                "self": "https://api.tracker.yandex.net/v3/issues/TEST-2",
                "id": "2",
                "key": "TEST-2",
                "display": "Test 2",
            },
            "status": "FAILED",
        }
        client = FakeClient(body=json.dumps([item_without_error]).encode())
        tracker = YaTracker(client=client)
        result = await tracker.get_bulk_change_issues("1ab23cd4e5678901abcdef12")

        assert result[0].error is None


# --- BulkChange status helpers ----------------------------------------------


class TestBulkChangeStatus:
    @pytest.mark.parametrize(
        ("status", "expected"),
        [
            ("CREATED", (False, False, False)),
            ("RUNNING", (False, False, False)),
            ("COMPLETE", (True, False, True)),
            ("FAILED", (False, True, True)),
        ],
    )
    def test_status_properties(
        self,
        status: str,
        expected: tuple[bool, bool, bool],
    ) -> None:
        is_complete, is_failed, is_finished = expected
        bulk_change = BulkChange.model_validate(bulk_change_payload(status=status))
        assert bulk_change.is_complete is is_complete
        assert bulk_change.is_failed is is_failed
        assert bulk_change.is_finished is is_finished

    def test_terminal_statuses_contents(self) -> None:
        assert frozenset({"COMPLETE", "FAILED"}) == TERMINAL_STATUSES


# --- wait_bulk_change --------------------------------------------------------


class TestWaitBulkChange:
    async def test_polls_until_complete(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps = patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[
                (200, bulk_change_body(status="RUNNING"), {}),
                (200, bulk_change_body(status="RUNNING"), {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        result = await tracker.wait_bulk_change(
            "1ab23cd4e5678901abcdef12",
            interval=2.5,
        )

        assert result.status == "COMPLETE"
        assert len(client.calls) == 3
        assert all(
            call["url"].endswith("/v3/bulkchange/1ab23cd4e5678901abcdef12")
            for call in client.calls
        )
        assert sleeps == [2.5, 2.5]

    async def test_accepts_bulk_change_instance(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        patch_sleep(monkeypatch)
        bulk_change = BulkChange.model_validate(
            bulk_change_payload(id="xyz987", status="RUNNING"),
        )
        client = FakeClient(
            responses=[(200, bulk_change_body(id="xyz987", status="COMPLETE"), {})],
        )
        tracker = YaTracker(client=client)
        result = await tracker.wait_bulk_change(bulk_change, interval=1)

        assert result.status == "COMPLETE"
        assert client.calls[0]["url"].endswith("/v3/bulkchange/xyz987")

    async def test_failed_is_terminal(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps = patch_sleep(monkeypatch)
        client = FakeClient(body=bulk_change_body(status="FAILED"))
        tracker = YaTracker(client=client)
        result = await tracker.wait_bulk_change(
            "1ab23cd4e5678901abcdef12",
            interval=1,
        )

        assert result.is_failed is True
        assert len(client.calls) == 1
        assert sleeps == []

    async def test_single_404_before_success_is_retried(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps = patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[
                (404, b"{}", {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        result = await tracker.wait_bulk_change(
            "1ab23cd4e5678901abcdef12",
            interval=0.5,
        )

        assert result.status == "COMPLETE"
        assert len(client.calls) == 2
        assert sleeps == [0.5]

    async def test_more_than_retry_limit_consecutive_404s_reraise(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[(404, b"{}", {})] * (NOT_FOUND_RETRIES + 1),
        )
        tracker = YaTracker(client=client)

        with pytest.raises(ObjectNotFoundError):
            await tracker.wait_bulk_change(
                "1ab23cd4e5678901abcdef12",
                interval=0.1,
            )

        assert len(client.calls) == NOT_FOUND_RETRIES + 1

    async def test_finished_instance_is_returned_without_requests(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps = patch_sleep(monkeypatch)
        client = FakeClient(body=bulk_change_body(status="RUNNING"))
        tracker = YaTracker(client=client)
        bulk_change = BulkChange.model_validate(bulk_change_payload(status="COMPLETE"))

        result = await tracker.wait_bulk_change(bulk_change, interval=1)

        assert result is bulk_change
        assert client.calls == []
        assert sleeps == []

    async def test_404_after_operation_was_seen_uses_the_same_budget(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[
                (200, bulk_change_body(status="RUNNING"), {}),
                (404, b"{}", {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        result = await tracker.wait_bulk_change("1ab23cd4e5678901abcdef12", interval=1)

        assert result.status == "COMPLETE"
        assert len(client.calls) == 3

    async def test_404_budget_is_not_replenished_by_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[
                *[(404, b"{}", {})] * NOT_FOUND_RETRIES,
                (200, bulk_change_body(status="RUNNING"), {}),
                (404, b"{}", {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)

        with pytest.raises(ObjectNotFoundError):
            await tracker.wait_bulk_change("1ab23cd4e5678901abcdef12", interval=1)

        assert len(client.calls) == NOT_FOUND_RETRIES + 2

    async def test_finished_hand_made_model_is_adopted_by_tracker(self) -> None:
        client = FakeClient(body=b"[]")
        tracker = YaTracker(client=client)
        bulk_change = BulkChange.model_validate(bulk_change_payload(status="COMPLETE"))
        assert bulk_change._tracker is None

        result = await tracker.wait_bulk_change(bulk_change)
        issues = await result.get_issues()

        assert result is bulk_change
        assert issues == []
        assert client.calls[0]["url"].endswith(
            "/v3/bulkchange/1ab23cd4e5678901abcdef12/issues"
        )

    async def test_transport_timeout_is_not_masked(self) -> None:
        class TimingOutClient(FakeClient):
            async def _make_request(self, *args: Any, **kwargs: Any) -> Any:  # noqa: ARG002
                msg = "connection timed out"
                raise asyncio.TimeoutError(msg)

        tracker = YaTracker(client=TimingOutClient())

        with pytest.raises(asyncio.TimeoutError, match="connection timed out"):
            await tracker.wait_bulk_change("1ab23cd4e5678901abcdef12", timeout=60)

    async def test_sleep_is_capped_by_the_remaining_time(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps = patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[
                (200, bulk_change_body(status="RUNNING"), {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        await tracker.wait_bulk_change(
            "1ab23cd4e5678901abcdef12", interval=60, timeout=5
        )

        assert len(sleeps) == 1
        assert 0 < sleeps[0] <= 5

    @pytest.mark.parametrize("timeout", [0, -1])
    async def test_timeout_must_be_positive(self, timeout: float) -> None:
        client = FakeClient(body=bulk_change_body())
        tracker = YaTracker(client=client)
        with pytest.raises(ValueError, match="timeout"):
            await tracker.wait_bulk_change(
                "1ab23cd4e5678901abcdef12",
                timeout=timeout,
            )

        assert client.calls == []

    @pytest.mark.parametrize("interval", [0, -1])
    async def test_interval_must_be_positive(self, interval: float) -> None:
        tracker = YaTracker(client=FakeClient(body=bulk_change_body()))
        with pytest.raises(ValueError, match="interval"):
            await tracker.wait_bulk_change(
                "1ab23cd4e5678901abcdef12",
                interval=interval,
            )

    async def test_timeout_raises(self) -> None:
        """A never-finishing operation, awaited with a tiny real timeout."""
        client = FakeClient(body=bulk_change_body(status="RUNNING"))
        tracker = YaTracker(client=client)

        with pytest.raises(TimeoutError):
            await tracker.wait_bulk_change(
                "1ab23cd4e5678901abcdef12",
                interval=0.01,
                timeout=0.05,
            )


# --- BulkChange model shortcuts ----------------------------------------------


class TestModelShortcuts:
    async def test_refresh_delegates_to_tracker(self) -> None:
        client = FakeClient(
            responses=[
                (200, bulk_change_body(status="RUNNING"), {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        bulk_change = await tracker.get_bulk_change("1ab23cd4e5678901abcdef12")

        refreshed = await bulk_change.refresh()

        assert refreshed.status == "COMPLETE"
        call = client.calls[1]
        assert call["method"] == "GET"
        assert call["url"].endswith("/v3/bulkchange/1ab23cd4e5678901abcdef12")

    async def test_wait_delegates_to_tracker(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        sleeps = patch_sleep(monkeypatch)
        client = FakeClient(
            responses=[
                (200, bulk_change_body(status="RUNNING"), {}),
                (200, bulk_change_body(status="RUNNING"), {}),
                (200, bulk_change_body(status="COMPLETE"), {}),
            ],
        )
        tracker = YaTracker(client=client)
        bulk_change = await tracker.get_bulk_change("1ab23cd4e5678901abcdef12")

        result = await bulk_change.wait(interval=3)

        assert result.status == "COMPLETE"
        assert len(client.calls) == 3
        assert sleeps == [3]

    async def test_get_issues_delegates_to_tracker(self) -> None:
        client = FakeClient(
            responses=[
                (200, bulk_change_body(), {}),
                (200, json.dumps([bulk_change_issue_payload()]).encode(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        bulk_change = await tracker.get_bulk_change("1ab23cd4e5678901abcdef12")

        issues = await bulk_change.get_issues()

        assert issues[0].issue.key == "TEST-1"
        call = client.calls[1]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/bulkchange/1ab23cd4e5678901abcdef12/issues",
        )


# --- exports -----------------------------------------------------------------


def test_types_are_exported_from_yatracker_types() -> None:
    assert {"BulkChange", "BulkChangeError", "BulkChangeIssue"} <= set(
        types_module.__all__,
    )


def test_tracker_has_bulk_change_methods() -> None:
    for name in (
        "bulk_update_issues",
        "bulk_transition_issues",
        "bulk_move_issues",
        "get_bulk_change",
        "get_bulk_change_issues",
        "wait_bulk_change",
    ):
        assert callable(getattr(YaTracker, name))
