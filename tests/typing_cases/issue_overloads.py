"""Static typing cases for the ``_type`` overloads of issue methods.

This module is not collected by pytest; ``tests/test_typing.py`` runs mypy
over it. Each ``assert_type`` fails under mypy if overload resolution
regresses, e.g. a bare call resolving to ``Any`` or ``_type=MyIssue`` being
swallowed by ``**kwargs`` and resolving to ``FullIssue``.
"""

from __future__ import annotations

from typing_extensions import assert_type
from yatracker import YaTracker
from yatracker.types import FullIssue


class MyIssue(FullIssue):
    """Custom issue model used to check that ``_type`` narrows the result."""


async def issue_overloads(tracker: YaTracker) -> None:
    assert_type(await tracker.create_issue("s", "Q"), FullIssue)
    assert_type(await tracker.create_issue("s", "Q", custom=1), FullIssue)
    assert_type(await tracker.create_issue("s", "Q", _type=MyIssue), MyIssue)

    assert_type(await tracker.edit_issue("K-1"), FullIssue)
    assert_type(await tracker.edit_issue("K-1", summary="x"), FullIssue)
    assert_type(await tracker.edit_issue("K-1", _type=MyIssue), MyIssue)
    assert_type(await tracker.edit_issue("K-1", None, MyIssue), MyIssue)

    assert_type(await tracker.move_issue("K-1", "Q"), FullIssue)
    assert_type(await tracker.move_issue("K-1", "Q", custom=1), FullIssue)
    assert_type(await tracker.move_issue("K-1", "Q", _type=MyIssue), MyIssue)

    assert_type(await tracker.get_issue("K-1"), FullIssue)
    assert_type(await tracker.get_issue("K-1", None, MyIssue), MyIssue)

    assert_type(await tracker.find_issues(query="x"), list[FullIssue])
    assert_type(await tracker.find_issues(query="x", _type=MyIssue), list[MyIssue])

    async for issue in tracker.iter_issues(query="x"):
        assert_type(issue, FullIssue)
    async for custom in tracker.iter_issues(query="x", _type=MyIssue):
        assert_type(custom, MyIssue)
