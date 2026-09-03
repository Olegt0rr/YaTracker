"""Static typing cases for the element types of the ``iter_*`` helpers.

Each of these wraps a paginated ``get_*`` call in an
``AsyncIterator[<Model>]``; ``assert_type`` pins the element type mypy infers
from the ``async for`` loop. Run by ``tests/test_typing.py`` under mypy; see
``issue_overloads.py``.
"""

from __future__ import annotations

from typing_extensions import assert_type
from yatracker import YaTracker
from yatracker.types import Board, Changelog, FullUser, Trigger


async def iterator_types(tracker: YaTracker) -> None:
    async for board in tracker.iter_boards():
        assert_type(board, Board)

    async for user in tracker.iter_users():
        assert_type(user, FullUser)

    async for trigger in tracker.iter_triggers("K"):
        assert_type(trigger, Trigger)

    async for change in tracker.iter_issue_changelog("K-1"):
        assert_type(change, Changelog)
