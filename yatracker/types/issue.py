from typing import Optional

import msgspec

from .base import BaseObject
from .objects import (
    Comment,
    Issue,
    IssueType,
    Priority,
    Queue,
    Sprint,
    Status,
    Transitions,
    User,
)


class FullIssue(BaseObject, kw_only=True, omit_defaults=True, rename="camel"):
    url: str = msgspec.field(name="self")
    id: str
    key: str
    version: int

    summary: str
    parent: Optional[Issue] = None
    description: Optional[str] = None
    sprint: Optional[list[Sprint]] = None
    type: IssueType
    priority: Priority
    followers: Optional[list[User]] = None
    queue: Queue
    favorite: bool
    assignee: Optional[User] = None

    last_comment_update_at: Optional[str] = None
    aliases: Optional[list[str]] = None
    updated_by: Optional[User] = None
    created_at: str
    created_by: User
    votes: int
    updated_at: Optional[str] = None
    status: Status
    previous_status: Optional[Status] = None
    direction: Optional[str] = None

    async def get_transitions(self) -> Transitions:
        """Returns dict and list-like Transitions object.

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

    async def post_comment(self, text=None, **kwargs):
        """Post comment for self
        :param text:
        :param kwargs:
        :return: Comment.
        """
        return await self.tracker.post_comment(self.id, text=text, **kwargs)
