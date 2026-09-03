"""Tests for the checklists category, `ChecklistItem` and `FullIssue` helpers.

Payloads are taken from the official documentation:
https://yandex.cloud/ru/docs/tracker/concepts/issues/get-checklist
https://yandex.cloud/ru/docs/tracker/concepts/issues/add-checklist-item
https://yandex.cloud/ru/docs/tracker/concepts/issues/edit-checklist
https://yandex.cloud/ru/docs/tracker/concepts/issues/delete-checklist-item
https://yandex.cloud/ru/docs/tracker/concepts/issues/delete-checklist
"""

from __future__ import annotations

import json
import warnings
from datetime import date, datetime, timezone
from typing import Any

import pytest
from pydantic import TypeAdapter
from yatracker import YaTracker
from yatracker.types import ChecklistDeadline, ChecklistItem, FullIssue

from tests.conftest import FakeClient, full_issue_body, make_tracker, sent_json

# `GET /issues/{issue_id}/checklistItems` list item, straight from the docs.
CHECKLIST_ITEM: dict[str, Any] = {
    "id": "5fde5f0a1aee261d12345678",
    "text": "List item text",
    "textHtml": "List item text in HTML",
    "checked": False,
    "assignee": {
        "id": 1111,
        "display": "Имя Фамилия",
        "passportUid": 1111,
        "login": "user_login",
        "firstName": "Имя",
        "lastName": "Фамилия",
        "email": "user_login@example.com",
        "trackerUid": 1111,
    },
    "deadline": {
        "date": "2021-05-09T00:00:00.000+0000",
        "deadlineType": "date",
        "isExceeded": False,
    },
    "checklistItemType": "standard",
}

# A checklist item without the optional assignee/deadline/textHtml.
MINIMAL_CHECKLIST_ITEM: dict[str, Any] = {
    "id": "5fde5f0a1aee261d87654321",
    "text": "Minimal item",
    "checked": True,
}

# The API omits `checked` for items that are not done.
UNCHECKED_CHECKLIST_ITEM: dict[str, Any] = {
    "id": "5fde5f0a1aee261d11223344",
    "text": "Item without the checked flag",
}


def encode(payload: Any) -> bytes:
    return json.dumps(payload).encode()


class TestChecklistItemDecoding:
    def test_full_item_decodes(self) -> None:
        item = TypeAdapter(ChecklistItem).validate_json(json.dumps(CHECKLIST_ITEM))
        assert item.id == "5fde5f0a1aee261d12345678"
        assert item.text == "List item text"
        assert item.text_html == "List item text in HTML"
        assert item.checked is False
        assert item.checklist_item_type == "standard"

        assert item.assignee is not None
        # the API sends a number, `Base` coerces it to a string
        assert item.assignee.id == "1111"
        assert item.assignee.display == "Имя Фамилия"
        assert item.assignee.login == "user_login"

        assert item.deadline is not None
        assert isinstance(item.deadline.date, datetime)
        assert item.deadline.date.tzinfo is not None
        assert item.deadline.deadline_type == "date"
        assert item.deadline.is_exceeded is False

    def test_minimal_item_decodes_with_nones(self) -> None:
        item = TypeAdapter(ChecklistItem).validate_json(
            json.dumps(MINIMAL_CHECKLIST_ITEM),
        )
        assert item.id == "5fde5f0a1aee261d87654321"
        assert item.text == "Minimal item"
        assert item.checked is True
        assert item.text_html is None
        assert item.assignee is None
        assert item.deadline is None
        assert item.checklist_item_type is None

    def test_item_without_checked_decodes_as_not_done(self) -> None:
        item = TypeAdapter(ChecklistItem).validate_json(
            json.dumps(UNCHECKED_CHECKLIST_ITEM),
        )
        assert item.checked is False


class TestGetChecklist:
    async def test_decodes_list_of_items(self) -> None:
        tracker, client = make_tracker([CHECKLIST_ITEM, MINIMAL_CHECKLIST_ITEM])
        items = await tracker.get_checklist("ORG-3")

        assert len(items) == 2
        assert isinstance(items[0], ChecklistItem)
        assert items[0].assignee is not None
        assert items[0].assignee.id == "1111"
        assert items[1].assignee is None

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith("/issues/ORG-3/checklistItems")


class TestAddChecklistItem:
    def _issue_response(self, **overrides: Any) -> bytes:
        return full_issue_body(
            checklistItems=[CHECKLIST_ITEM],
            checklistTotal=2,
            checklistDone="0",
            **overrides,
        )

    async def test_minimal_call_sends_only_text(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        await tracker.add_checklist_item("ORG-3", "List item text")

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issues/ORG-3/checklistItems")
        assert sent_json(call) == {"text": "List item text"}

    async def test_full_call_sends_all_fields(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        await tracker.add_checklist_item(
            "ORG-3",
            "List item text",
            checked=False,
            assignee="login",
            deadline=datetime(2021, 5, 9, tzinfo=timezone.utc),
        )

        assert sent_json(client.calls[0]) == {
            "text": "List item text",
            "checked": False,
            "assignee": "login",
            "deadline": {
                "date": "2021-05-09T00:00:00.000+0000",
                "deadlineType": "date",
            },
        }

    async def test_string_deadline_passes_through_verbatim(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        await tracker.add_checklist_item(
            "ORG-3",
            "List item text",
            deadline="2021-05-09T00:00:00.000+0000",
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T00:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_bare_date_deadline_becomes_midnight_utc(self) -> None:
        # the parameter is documented as a timestamp; a `date` has no
        # time of its own, so it is anchored to midnight UTC instead of
        # reaching the API as an unusable `datetime.date` object
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        with warnings.catch_warnings():
            warnings.simplefilter("error")
            await tracker.add_checklist_item(
                "ORG-3",
                "List item text",
                deadline=date(2021, 5, 9),
            )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T00:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_int_assignee_is_sent_verbatim(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        await tracker.add_checklist_item("ORG-3", "List item text", assignee=1111)

        assert sent_json(client.calls[0])["assignee"] == 1111

    async def test_checklist_deadline_keeps_its_own_type(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        await tracker.add_checklist_item(
            "ORG-3",
            "List item text",
            deadline=ChecklistDeadline(
                date=datetime(2021, 5, 9, tzinfo=timezone.utc),
                deadline_type="absolute",
            ),
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T00:00:00.000+0000",
            "deadlineType": "absolute",
        }

    async def test_decoded_deadline_round_trips(self) -> None:
        item = TypeAdapter(ChecklistItem).validate_json(json.dumps(CHECKLIST_ITEM))
        assert item.deadline is not None

        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        await tracker.add_checklist_item(
            "ORG-3",
            "List item text",
            deadline=item.deadline,
        )

        assert sent_json(client.calls[0])["deadline"] == {
            "date": "2021-05-09T00:00:00.000+0000",
            "deadlineType": "date",
        }

    async def test_naive_deadline_warns(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        with pytest.warns(UserWarning, match="naive datetime") as record:
            await tracker.add_checklist_item(
                "ORG-3",
                "List item text",
                deadline=datetime(2021, 5, 9),  # noqa: DTZ001
            )

        assert record[0].filename == __file__
        assert sent_json(client.calls[0])["deadline"]["date"] == (
            "2021-05-09T00:00:00.000"
        )

    async def test_returns_full_issue_with_checklist_fields_decoded(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = self._issue_response()

        issue = await tracker.add_checklist_item("ORG-3", "List item text")

        assert isinstance(issue, FullIssue)
        assert issue.checklist_items is not None
        assert issue.checklist_items[0].text == "List item text"
        # `checklistDone` is sent as a string in the docs example
        assert issue.checklist_done == 0
        assert isinstance(issue.checklist_done, int)
        assert issue.checklist_total == 2


class TestEditChecklistItem:
    async def test_sends_patch_with_plain_object_body(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = full_issue_body(
            checklistItems=[CHECKLIST_ITEM],
            checklistTotal=1,
            checklistDone="1",
        )

        issue = await tracker.edit_checklist_item(
            "ORG-3",
            "5fde5f0a1aee261d12345678",
            "Updated text",
            checked=True,
        )

        call = client.calls[0]
        assert call["method"] == "PATCH"
        assert call["url"].endswith(
            "/issues/ORG-3/checklistItems/5fde5f0a1aee261d12345678",
        )
        body = sent_json(call)
        assert isinstance(body, dict)  # not the array shown in the docs
        assert body == {"text": "Updated text", "checked": True}
        assert isinstance(issue, FullIssue)


class TestDeleteChecklistItem:
    async def test_sends_delete_with_no_body(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = full_issue_body(
            checklistItems=[],
            checklistTotal=0,
            checklistDone="0",
        )

        issue = await tracker.delete_checklist_item(
            "ORG-3",
            "5fde5f0a1aee261d12345678",
        )

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith(
            "/issues/ORG-3/checklistItems/5fde5f0a1aee261d12345678",
        )
        assert call["data"] is None
        assert isinstance(issue, FullIssue)


class TestDeleteChecklist:
    async def test_sends_delete_and_decodes_issue(self) -> None:
        tracker, client = make_tracker(status=200)
        client.body = full_issue_body(
            lastCommentUpdatedAt="2024-01-01T00:00:00.000+0000",
            checklistDone="0",
            checklistTotal=0,
        )

        issue = await tracker.delete_checklist("ORG-3")

        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/issues/ORG-3/checklistItems")
        assert call["data"] is None
        assert isinstance(issue, FullIssue)
        assert issue.checklist_done == 0
        assert issue.checklist_total == 0


class TestTypeOverride:
    async def test_mutating_methods_return_custom_type(self) -> None:
        class MyIssue(FullIssue):
            pass

        tracker, client = make_tracker(status=200)
        client.body = full_issue_body()

        add_result = await tracker.add_checklist_item(
            "ORG-3",
            "text",
            _type=MyIssue,
        )
        assert isinstance(add_result, MyIssue)

        client.body = full_issue_body()
        edit_result = await tracker.edit_checklist_item(
            "ORG-3",
            "item-1",
            "text",
            _type=MyIssue,
        )
        assert isinstance(edit_result, MyIssue)

        client.body = full_issue_body()
        delete_item_result = await tracker.delete_checklist_item(
            "ORG-3",
            "item-1",
            _type=MyIssue,
        )
        assert isinstance(delete_item_result, MyIssue)

        client.body = full_issue_body()
        delete_checklist_result = await tracker.delete_checklist(
            "ORG-3",
            _type=MyIssue,
        )
        assert isinstance(delete_checklist_result, MyIssue)


class TestFullIssueDecodingWithoutChecklist:
    def test_missing_checklist_fields_decode_as_none(self) -> None:
        issue = TypeAdapter(FullIssue).validate_json(full_issue_body())
        assert issue.checklist_items is None
        assert issue.checklist_total is None
        assert issue.checklist_done is None


class TestFullIssueChecklistHelpers:
    async def test_get_checklist(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, encode([CHECKLIST_ITEM]), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        items = await issue.get_checklist()
        assert [i.text for i in items] == ["List item text"]
        assert client.calls[1]["method"] == "GET"
        assert client.calls[1]["url"].endswith("/issues/1/checklistItems")

    async def test_add_checklist_item(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(checklistItems=[CHECKLIST_ITEM]), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        updated = await issue.add_checklist_item("List item text")
        assert isinstance(updated, FullIssue)
        call = client.calls[1]
        assert call["method"] == "POST"
        assert call["url"].endswith("/issues/1/checklistItems")
        assert sent_json(call) == {"text": "List item text"}

    async def test_edit_checklist_item(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        await issue.edit_checklist_item("item-1", "new text", checked=True)
        call = client.calls[1]
        assert call["method"] == "PATCH"
        assert call["url"].endswith("/issues/1/checklistItems/item-1")
        assert sent_json(call) == {"text": "new text", "checked": True}

    async def test_delete_checklist_item(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        await issue.delete_checklist_item("item-1")
        call = client.calls[1]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/issues/1/checklistItems/item-1")

    async def test_delete_checklist(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        await issue.delete_checklist()
        call = client.calls[1]
        assert call["method"] == "DELETE"
        assert call["url"].endswith("/issues/1/checklistItems")

    async def test_naive_deadline_warning_points_at_the_caller(self) -> None:
        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1")

        with pytest.warns(UserWarning, match="naive datetime") as record:
            await issue.add_checklist_item(
                "List item text",
                deadline=datetime(2021, 5, 9),  # noqa: DTZ001
            )

        assert record[0].filename == __file__
        assert sent_json(client.calls[1])["deadline"] == {
            "date": "2021-05-09T00:00:00.000",
            "deadlineType": "date",
        }

    async def test_explicit_type_overrides_type_of_self(self) -> None:
        class MyIssue(FullIssue):
            pass

        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1", _type=MyIssue)

        added = await issue.add_checklist_item("x", _type=FullIssue)
        assert type(added) is FullIssue

    async def test_explicit_type_saves_a_subclass_with_extra_required_field(
        self,
    ) -> None:
        class IssueWithExtra(FullIssue):
            my_field: str

        client = FakeClient(
            responses=[
                (200, full_issue_body(myField="value"), {}),
                (200, full_issue_body(), {}),  # the response lacks `myField`
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1", _type=IssueWithExtra)
        assert isinstance(issue, IssueWithExtra)

        deleted = await issue.delete_checklist(_type=FullIssue)
        assert type(deleted) is FullIssue

    async def test_helpers_return_subclass_via_type_of_self(self) -> None:
        class MyIssue(FullIssue):
            pass

        client = FakeClient(
            responses=[
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
                (200, full_issue_body(), {}),
            ],
        )
        tracker = YaTracker(client=client)
        issue = await tracker.get_issue("TEST-1", _type=MyIssue)
        assert isinstance(issue, MyIssue)

        added = await issue.add_checklist_item("text")
        assert isinstance(added, MyIssue)

        edited = await issue.edit_checklist_item("item-1", "text")
        assert isinstance(edited, MyIssue)

        deleted_item = await issue.delete_checklist_item("item-1")
        assert isinstance(deleted_item, MyIssue)


class TestYaTrackerExposesChecklistMethods:
    def test_all_five_methods_are_present(self) -> None:
        tracker, _ = make_tracker()
        for name in (
            "get_checklist",
            "add_checklist_item",
            "edit_checklist_item",
            "delete_checklist_item",
            "delete_checklist",
        ):
            assert callable(getattr(tracker, name, None)), name
