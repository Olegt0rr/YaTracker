from __future__ import annotations

__all__ = ["FullIssue"]

from datetime import datetime
from typing import TYPE_CHECKING

from typing_extensions import Self

from .base import Base, field
from .checklist import ChecklistItem
from .comment import Comment
from .component import ComponentRef
from .issue import Issue
from .issue_type import IssueType
from .priority import Priority
from .queue import Queue
from .sprint import Sprint
from .status import Status
from .transitions import Transitions
from .user import User

if TYPE_CHECKING:
    from .issue_link import IssueLink


class FullIssue(Base):
    url: str = field(alias="self")
    id: str
    key: str
    version: int

    summary: str
    parent: Issue | None = None
    description: str | None = None
    sprint: list[Sprint] | None = None
    components: list[ComponentRef] | None = None
    checklist_items: list[ChecklistItem] | None = None
    checklist_total: int | None = None
    checklist_done: int | None = None
    type: IssueType
    priority: Priority
    followers: list[User] | None = None
    queue: Queue
    previous_queue: Queue | None = None
    favorite: bool
    assignee: User | None = None

    last_comment_update_at: datetime | None = None
    aliases: list[str] | None = None
    updated_by: User | None = None
    created_at: datetime
    created_by: User
    votes: int
    updated_at: datetime | None = None
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
        return await self._tracker.get_transitions(self.id)

    async def get_comments(self) -> list[Comment]:
        """Get comments for self.

        :return:
        """
        return await self._tracker.get_comments(self.id)

    async def post_comment(self, text: str, **kwargs) -> Comment:
        """Post comment for self."""
        return await self._tracker.post_comment(self.id, text=text, **kwargs)

    async def get_checklist(self) -> list[ChecklistItem]:
        """Get the checklist of self."""
        return await self._tracker.get_checklist(self.id)

    async def add_checklist_item(self, text: str, **kwargs) -> Self:
        """Add an item to the checklist of self.

        :return: the updated issue.
        """
        return await self._tracker.add_checklist_item(
            self.id,
            text,
            _type=type(self),
            **kwargs,
        )

    async def edit_checklist_item(self, item_id: str, text: str, **kwargs) -> Self:
        """Edit an item of the checklist of self.

        The API requires `text` even when only `checked` has to be
        toggled, so pass the current text of the item to keep it.

        :return: the updated issue.
        """
        return await self._tracker.edit_checklist_item(
            self.id,
            item_id,
            text,
            _type=type(self),
            **kwargs,
        )

    async def delete_checklist_item(self, item_id: str) -> Self:
        """Delete an item from the checklist of self.

        :return: the updated issue.
        """
        return await self._tracker.delete_checklist_item(
            self.id,
            item_id,
            _type=type(self),
        )

    async def delete_checklist(self) -> Self:
        """Delete the whole checklist of self.

        :return: the updated issue.
        """
        return await self._tracker.delete_checklist(self.id, _type=type(self))

    async def get_links(self) -> list[IssueLink]:
        """Get issue links."""
        return await self._tracker.get_issue_links(self.id)
