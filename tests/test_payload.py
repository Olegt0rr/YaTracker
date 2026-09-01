"""Tests for payload preparation helpers."""

from __future__ import annotations

from yatracker.tracker.base import BaseTracker, _convert_value
from yatracker.types import FullIssue, Issue, IssueType

ISSUE = Issue(url="https://api/issue/1", id="1", key="TEST-1", display="Test")
ISSUE_TYPE = IssueType(url="https://api/type/1", id="1", key="bug", display="Bug")


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
