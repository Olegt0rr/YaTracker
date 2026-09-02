"""Static typing cases for the ``_type`` overloads of queue methods.

Covers ``get_queues``, ``get_queue_versions``, ``create_queue_version`` and
the plain (non-overloaded) ``link_issues``. Run by ``tests/test_typing.py``
under mypy; see ``issue_overloads.py``.
"""

from __future__ import annotations

from typing_extensions import assert_type
from yatracker import YaTracker
from yatracker.types import CreatedIssueLink, FullQueue, QueueVersion


class MyQueue(FullQueue):
    """Custom queue model used to check that ``_type`` narrows the result."""


class MyQueueVersion(QueueVersion):
    """Custom version model used to check that ``_type`` narrows the result."""


async def queue_overloads(tracker: YaTracker) -> None:
    assert_type(await tracker.get_queues(), list[FullQueue])
    assert_type(await tracker.get_queues(_type=MyQueue), list[MyQueue])

    assert_type(await tracker.get_queue_versions("K"), list[QueueVersion])
    assert_type(
        await tracker.get_queue_versions("K", MyQueueVersion),
        list[MyQueueVersion],
    )

    assert_type(await tracker.create_queue_version("K", "v1"), QueueVersion)
    assert_type(
        await tracker.create_queue_version("K", "v1", MyQueueVersion),
        MyQueueVersion,
    )

    assert_type(
        await tracker.link_issues("K-1", "relates", "K-2"),
        CreatedIssueLink,
    )
