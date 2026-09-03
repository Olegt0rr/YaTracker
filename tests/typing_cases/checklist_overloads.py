"""Static typing cases for the ``_type`` overloads of checklist methods.

Run by ``tests/test_typing.py`` under mypy; see ``issue_overloads.py``.
The ``FullIssue`` helpers default to ``type(self)`` and an explicit
``_type`` must widen the result instead of being reported as ``Self``.
"""

from __future__ import annotations

from datetime import date

from typing_extensions import assert_type
from yatracker import YaTracker
from yatracker.types import ChecklistItem, FullIssue


class MyIssue(FullIssue):
    """Custom issue model used to check that ``_type`` narrows the result."""


async def checklist_overloads(tracker: YaTracker) -> None:
    assert_type(await tracker.get_checklist("K-1"), list[ChecklistItem])

    assert_type(await tracker.add_checklist_item("K-1", "x"), FullIssue)
    # a bare `date` is accepted as a deadline, like a `datetime`
    assert_type(
        await tracker.add_checklist_item("K-1", "x", deadline=date(2024, 3, 1)),
        FullIssue,
    )
    assert_type(
        await tracker.edit_checklist_item(
            "K-1",
            "i",
            "x",
            deadline=date(2024, 3, 1),
        ),
        FullIssue,
    )
    assert_type(await tracker.add_checklist_item("K-1", "x", _type=MyIssue), MyIssue)
    assert_type(await tracker.edit_checklist_item("K-1", "i", "x"), FullIssue)
    assert_type(
        await tracker.edit_checklist_item("K-1", "i", "x", _type=MyIssue),
        MyIssue,
    )
    assert_type(await tracker.delete_checklist_item("K-1", "i"), FullIssue)
    assert_type(await tracker.delete_checklist_item("K-1", "i", _type=MyIssue), MyIssue)
    assert_type(await tracker.delete_checklist("K-1"), FullIssue)
    assert_type(await tracker.delete_checklist("K-1", _type=MyIssue), MyIssue)

    issue = await tracker.get_issue("K-1")
    assert_type(await issue.add_checklist_item("x", checked=True), FullIssue)

    my = await tracker.get_issue("K-1", None, MyIssue)
    assert_type(await my.get_checklist(), list[ChecklistItem])
    assert_type(await my.add_checklist_item("x"), MyIssue)
    assert_type(await my.add_checklist_item("x", _type=FullIssue), FullIssue)
    assert_type(await my.edit_checklist_item("i", "x", checked=True), MyIssue)
    assert_type(await my.edit_checklist_item("i", "x", _type=FullIssue), FullIssue)
    assert_type(await my.delete_checklist_item("i"), MyIssue)
    assert_type(await my.delete_checklist_item("i", _type=FullIssue), FullIssue)
    assert_type(await my.delete_checklist(), MyIssue)
    assert_type(await my.delete_checklist(_type=FullIssue), FullIssue)
