"""Tests for payload preparation helpers."""

from __future__ import annotations

from yatracker import YaTracker
from yatracker.tracker.base import BaseTracker, _convert_value, _encode_key
from yatracker.types import FullIssue, Issue, IssueType

from tests.conftest import FakeClient, full_issue_body, json_payload

ISSUE = Issue(url="https://api/issue/1", id="1", key="TEST-1", display="Test")
ISSUE_TYPE = IssueType(url="https://api/type/1", id="1", key="bug", display="Bug")
LOCAL_FIELD = "64a51c6d866ea82411abe756--userId"


class TestEncodeKey:
    def test_identifier_is_camel_cased(self) -> None:
        assert _encode_key("attachment_ids") == "attachmentIds"
        assert _encode_key("filter_") == "filter"
        assert _encode_key("customField") == "customField"

    def test_local_field_id_is_kept_verbatim(self) -> None:
        assert _encode_key(LOCAL_FIELD) == LOCAL_FIELD


class TestConvertValue:
    def test_scalar_passthrough(self) -> None:
        assert _convert_value("text") == "text"
        assert _convert_value(5) == 5

    def test_struct_converted_to_dict(self) -> None:
        assert _convert_value(ISSUE) == {
            "self": "https://api/issue/1",
            "id": "1",
            "key": "TEST-1",
            "display": "Test",
        }

    def test_struct_with_tracker_set(self) -> None:
        issue = Issue(url="u", id="1", key="K-1", display="d")
        issue._tracker = object()
        converted = _convert_value(issue)
        assert "_tracker" not in converted
        assert converted["key"] == "K-1"

    def test_nested_containers(self) -> None:
        assert _convert_value([{"issue": ISSUE}]) == [
            {"issue": _convert_value(ISSUE)},
        ]


class TestPreparePayload:
    def test_create_issue_style_payload(self) -> None:
        payload = {
            "summary": "s",
            "queue": "Q",
            "parent": None,
            "description": "d",
            "type_": ISSUE_TYPE,
            "priority": "minor",
            "unique": "abc",
            "attachment_ids": ["1", "2"],
            "kwargs": {"customField": "x"},
        }
        result = BaseTracker._prepare_payload(payload, type_=FullIssue)
        assert result == {
            "summary": "s",
            "queue": "Q",
            "description": "d",
            "type": _convert_value(ISSUE_TYPE),
            "priority": "minor",
            "unique": "abc",
            "attachmentIds": ["1", "2"],
            "customField": "x",
        }

    def test_find_issues_style_payload(self) -> None:
        payload = {
            "filter_": {"queue": "TEST"},
            "query": "Key: TEST-1",
            "order": "+key",
            "expand": None,
            "keys": "TEST-1",
            "queue": None,
        }
        result = BaseTracker._prepare_payload(
            payload,
            exclude=["expand", "order"],
            type_=FullIssue,
        )
        assert result == {
            "filter": {"queue": "TEST"},
            "query": "Key: TEST-1",
            "keys": "TEST-1",
        }

    def test_without_type(self) -> None:
        result = BaseTracker._prepare_payload(
            {"per_page": 50, "expand": None, "_private": 1},
        )
        assert result == {"perPage": 50}

    def test_excludes_and_private_keys(self) -> None:
        result = BaseTracker._prepare_payload(
            {"self": object(), "_type": FullIssue, "summary": "s"},
            type_=FullIssue,
        )
        assert result == {"summary": "s"}

    def test_local_field_key_kept_verbatim_with_type(self) -> None:
        result = BaseTracker._prepare_payload(
            {"summary": "s", "kwargs": {LOCAL_FIELD: 42}},
            type_=FullIssue,
        )
        assert result == {"summary": "s", LOCAL_FIELD: 42}

    def test_local_field_key_kept_verbatim_without_type(self) -> None:
        result = BaseTracker._prepare_payload({LOCAL_FIELD: 42, "per_page": 1})
        assert result == {LOCAL_FIELD: 42, "perPage": 1}


class TestLocalFieldsOnTheWire:
    async def test_edit_issue_sends_local_field_verbatim(self) -> None:
        client = FakeClient(body=full_issue_body())
        tracker = YaTracker(client=client)
        await tracker.edit_issue("TEST-1", **{LOCAL_FIELD: 42})
        payload = json_payload(client.calls[0])
        assert payload == {LOCAL_FIELD: 42}

    async def test_create_issue_sends_local_field_verbatim(self) -> None:
        client = FakeClient(body=full_issue_body())
        tracker = YaTracker(client=client)
        await tracker.create_issue(
            "summary",
            "TEST",
            attachment_ids=["1"],
            **{LOCAL_FIELD: 42},
        )
        payload = json_payload(client.calls[0])
        assert payload == {
            "summary": "summary",
            "queue": "TEST",
            "attachmentIds": ["1"],
            LOCAL_FIELD: 42,
        }
