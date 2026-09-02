from __future__ import annotations

__all__ = ["BulkChange", "BulkChangeError", "BulkChangeIssue"]

from datetime import datetime
from typing import Any

from .base import Base, field, url_field
from .issue import Issue
from .user import User

BULK_CHANGE_COMPLETE = "COMPLETE"
BULK_CHANGE_FAILED = "FAILED"
TERMINAL_STATUSES: frozenset[str] = frozenset(
    {BULK_CHANGE_COMPLETE, BULK_CHANGE_FAILED},
)


class BulkChangeError(Base):
    """Represents errors occurred while changing a single issue."""

    errors: dict[str, Any] = field(default_factory=dict)
    error_messages: list[str] = field(default_factory=list)


class BulkChangeIssue(Base):
    """Represents a result of a bulk change operation for a single issue."""

    issue: Issue
    status: str
    status_text: str | None = None
    error: BulkChangeError | None = None


class BulkChange(Base):
    """Represents a bulk change (mass edit) operation."""

    url: str = url_field()
    id: str
    created_by: User
    created_at: datetime
    status: str
    status_text: str | None = None
    execution_chunk_percent: float | None = None
    execution_issue_percent: float | None = None
    total_issues: int | None = None
    total_completed_issues: int | None = None

    @property
    def is_complete(self) -> bool:
        """Check whether the operation has been completed successfully."""
        return self.status == BULK_CHANGE_COMPLETE

    @property
    def is_failed(self) -> bool:
        """Check whether the operation has failed."""
        return self.status == BULK_CHANGE_FAILED

    @property
    def is_finished(self) -> bool:
        """Check whether the operation has reached a terminal status."""
        return self.status in TERMINAL_STATUSES

    async def refresh(self) -> BulkChange:
        """Get the current state of the operation."""
        return await self._tracker.get_bulk_change(self)

    async def wait(
        self,
        *,
        interval: float = 1.0,
        timeout: float | None = None,
    ) -> BulkChange:
        """Wait until the operation is finished.

        With the default `timeout=None` the wait is unbounded, so pass an
        explicit `timeout` in unattended code.

        :param interval: Delay between status checks (seconds).
        :param timeout: Maximum time to wait (seconds), `None` for no limit.
        :raises TimeoutError: If the operation is not finished in time.
        """
        return await self._tracker.wait_bulk_change(
            self,
            interval=interval,
            timeout=timeout,
        )

    async def get_issues(self) -> list[BulkChangeIssue]:
        """Get the issues the operation failed to process.

        Only the issues that finished with an error are returned.
        """
        return await self._tracker.get_bulk_change_issues(self)
