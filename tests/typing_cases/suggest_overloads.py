"""Static typing cases for the ``_type`` overloads of ``suggest_issues``.

Run by ``tests/test_typing.py`` under mypy; see ``issue_overloads.py``.
"""

from __future__ import annotations

from typing_extensions import assert_type
from yatracker import YaTracker
from yatracker.types import FullIssue, IssueSuggest


class MySuggest(IssueSuggest):
    """Custom suggest model used to check that ``_type`` narrows the result."""


async def suggest_overloads(tracker: YaTracker) -> None:
    assert_type(await tracker.suggest_issues("x"), list[IssueSuggest])
    assert_type(
        await tracker.suggest_issues("x", FullIssue, full=True),
        list[FullIssue],
    )
    assert_type(await tracker.suggest_issues("x", MySuggest), list[MySuggest])
