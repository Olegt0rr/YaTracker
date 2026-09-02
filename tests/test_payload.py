"""Tests for payload preparation helpers."""

from __future__ import annotations

import importlib
import pkgutil

import pytest
import yatracker.types as types_pkg
from yatracker import YaTracker
from yatracker.tracker.base import (
    BaseTracker,
    _convert_value,
    _encode_key,
    _field_names,
)
from yatracker.types import FullIssue, Issue, IssueType, QueueField, field
from yatracker.types.base import Base

from tests.conftest import FakeClient, full_issue_body, sent_json

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

    def test_struct_dump_round_trips(self) -> None:
        assert Issue.model_validate(_convert_value(ISSUE)) == ISSUE

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

    def test_tuple_is_rendered_as_an_array_of_converted_items(self) -> None:
        # `pydantic_core.to_json` would serialize the tuple without
        # walking into it, dumping the model verbatim
        assert _convert_value((ISSUE,)) == [_convert_value(ISSUE)]

    def test_set_is_rendered_as_a_sorted_array(self) -> None:
        assert _convert_value({"b", "a"}) == ["a", "b"]

    def test_frozenset_is_rendered_as_an_array(self) -> None:
        assert _convert_value(frozenset({2, 1})) == [1, 2]

    def test_set_of_incomparable_items_keeps_the_iteration_order(self) -> None:
        # a `str` cannot be compared to an `int`, so sorting is skipped
        # instead of failing with a `TypeError`
        values = {1, "a"}
        assert _convert_value(values) == list(values)

    async def test_model_inside_a_tuple_reaches_the_wire_as_a_key(self) -> None:
        client = FakeClient(body=full_issue_body())
        tracker = YaTracker(client=client)
        await tracker.edit_issue("TEST-1", sorts=(ISSUE,))
        assert sent_json(client.calls[0])["sorts"] == [_convert_value(ISSUE)]


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


class TestPrepareParams:
    def test_bools_are_lowercased_and_keys_camel_cased(self) -> None:
        result = BaseTracker._prepare_params(backlink=True, notify_author=False)
        assert result == {"backlink": "true", "notifyAuthor": "false"}

    def test_none_values_are_dropped(self) -> None:
        assert BaseTracker._prepare_params(backlink=None, per_page=None) is None

    def test_other_values_are_stringified(self) -> None:
        result = BaseTracker._prepare_params(per_page=50, page=None, expand="all")
        assert result == {"perPage": "50", "expand": "all"}


class TestLocalFieldsOnTheWire:
    async def test_edit_issue_sends_local_field_verbatim(self) -> None:
        client = FakeClient(body=full_issue_body())
        tracker = YaTracker(client=client)
        await tracker.edit_issue("TEST-1", **{LOCAL_FIELD: 42})
        payload = sent_json(client.calls[0])
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
        payload = sent_json(client.calls[0])
        assert payload == {
            "summary": "summary",
            "queue": "TEST",
            "attachmentIds": ["1"],
            LOCAL_FIELD: 42,
        }


def _library_models() -> list[type[Base]]:
    """Every model class defined under ``yatracker.types``."""
    models: list[type[Base]] = []
    for info in pkgutil.iter_modules(types_pkg.__path__):
        module = importlib.import_module(f"yatracker.types.{info.name}")
        models.extend(
            obj
            for obj in vars(module).values()
            if isinstance(obj, type)
            and issubclass(obj, Base)
            and obj is not Base
            and obj.__module__ == module.__name__
        )
    return models


class TestSelfIsDecodeOnly:
    """``self`` is bound through ``url_field``: a kwarg named ``url`` stays ``url``."""

    def test_url_kwarg_is_sent_as_url(self) -> None:
        result = BaseTracker._prepare_payload(
            {"url": "https://old/1", "summary": "s"},
            type_=FullIssue,
        )
        assert result == {"url": "https://old/1", "summary": "s"}

    def test_every_model_binds_url_to_self(self) -> None:
        models = [m for m in _library_models() if "url" in m.model_fields]
        assert len(models) >= 20
        for model in models:
            info = model.model_fields["url"]
            assert info.validation_alias == "self", model
            assert info.serialization_alias == "self", model
            assert _field_names(model)["url"] == "url", model
            assert "self" not in _field_names(model).values(), model

    def test_schema_alias_round_trips(self) -> None:
        assert _field_names(QueueField)["field_schema"] == "schema"
        info = QueueField.model_fields["field_schema"]
        assert info.validation_alias == "schema"
        assert info.serialization_alias == "schema"

    def test_user_subclass_aliases_are_applied(self) -> None:
        class HelpIssue(FullIssue):
            user_id: int | None = field(default=None, alias="64a5--userId")
            source_url: str | None = field(default=None, alias="url")

        result = BaseTracker._prepare_payload(
            {"summary": "s", "user_id": 42, "source_url": "x"},
            type_=HelpIssue,
        )
        assert result == {"summary": "s", "64a5--userId": 42, "url": "x"}

    def test_user_override_of_url_alias_is_applied(self) -> None:
        class LinkIssue(FullIssue):
            url: str | None = field(default=None, alias="link")

        result = BaseTracker._prepare_payload({"url": "x"}, type_=LinkIssue)
        assert result == {"link": "x"}

    def test_self_key_still_decodes_alongside_custom_url(self) -> None:
        class MigratedIssue(FullIssue):
            source_url: str | None = field(default=None, alias="url")

        issue = MigratedIssue.model_validate_json(
            full_issue_body(url="https://old/1"),
        )
        assert issue.url == "https://api/issues/1"
        assert issue.source_url == "https://old/1"

    def test_embedded_model_keeps_self_and_custom_url(self) -> None:
        class MigratedIssue(FullIssue):
            source_url: str | None = field(default=None, alias="url")

        issue = MigratedIssue.model_validate_json(
            full_issue_body(url="https://old/1"),
        )
        dumped = _convert_value(issue)
        assert dumped["self"] == "https://api/issues/1"
        assert dumped["url"] == "https://old/1"

    async def test_create_issue_sends_url_key(self) -> None:
        client = FakeClient(body=full_issue_body())
        tracker = YaTracker(client=client)

        await tracker.create_issue(summary="s", queue="Q", url="https://old/1")

        assert sent_json(client.calls[0]) == {
            "summary": "s",
            "queue": "Q",
            "url": "https://old/1",
        }


class TestWireNameCollisions:
    def test_two_keys_with_same_wire_name_raise(self) -> None:
        class MigratedIssue(FullIssue):
            source_url: str | None = field(default=None, alias="url")

        with pytest.raises(ValueError, match="'url' and 'source_url' both map"):
            BaseTracker._prepare_payload(
                {"url": "A", "source_url": "B"},
                type_=MigratedIssue,
            )

    def test_parameter_and_kwarg_with_same_wire_name_raise(self) -> None:
        with pytest.raises(ValueError, match="'type_' and 'type' both map"):
            BaseTracker._prepare_payload(
                {"type_": ISSUE_TYPE, "kwargs": {"type": "bug"}},
                type_=FullIssue,
            )

    def test_untyped_payload_is_checked_too(self) -> None:
        with pytest.raises(ValueError, match="'attachment_ids' and 'attachmentIds'"):
            BaseTracker._prepare_payload(
                {"attachment_ids": ["1"], "kwargs": {"attachmentIds": ["2"]}},
            )
