from __future__ import annotations

__all__ = ["FullIssue"]

from .base import Base, field
from .comment import Comment
from .issue import Issue
from .issue_type import IssueType
from .priority import Priority
from .queue import Queue
from .sprint import Sprint
from .status import Status
from .transitions import Transitions
from .user import User


class FullIssue(Base, kw_only=True, frozen=True):
    url: str = field(name="self")
    id: str
    key: str
    version: int
    summary: str
    parent: Issue | None = None
    description: str | None = None
    sprint: list[Sprint] | None = None
    type: IssueType
    priority: Priority
    followers: list[User] | None = None
    queue: Queue
    favorite: bool
    assignee: User | None = None

    last_comment_update_at: str | None = None
    aliases: list[str] | None = None
    updated_by: User | None = None
    created_at: str
    created_by: User
    votes: int
    updated_at: str | None = None
    status: Status
    previous_status: Status | None = None
    direction: str | None = None

    async def get_transitions(self) -> Transitions:
        """Return dict and list-like Transitions object.

        Iterate Transitions like a list:
        >>> transitions = await self.get_transitions()
        >>> for t in transitions:
        >>>    print(t)

        Use Transitions like a dict with transition names:
        >>> transitions = await self.get_transitions()
        >>> close = transitions.get('close')
        >>> if close:
        >>>    await close.execute()
        """
        return await self.tracker.get_transitions(self.id)

    async def get_comments(self) -> list[Comment]:
        """Get comments for self.

        :return:
        """
        return await self.tracker.get_comments(self.id)

    async def post_comment(self, text: str, **kwargs) -> Comment:
        """Post comment for self."""
        return await self.tracker.post_comment(self.id, text=text, **kwargs)
