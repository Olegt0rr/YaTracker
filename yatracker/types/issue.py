from typing import List, Optional

from .base import BaseObject
from .objects import Issue, IssueType, Priority, Queue, Sprint, Status, User, Transitions


class FullIssue(BaseObject):
    url: str
    id: str
    key: str
    version: int

    summary: str
    parent: Optional[Issue]
    description: Optional[str]
    sprint: Optional[List[Sprint]]
    type: IssueType
    priority: Priority
    followers: Optional[List[User]]
    queue: Queue
    favorite: bool
    assignee: Optional[User]

    last_comment_update_at: Optional[str]
    aliases: Optional[List[str]]
    updated_by: Optional[User]
    created_at: str
    created_by: User
    votes: int
    updated_at: Optional[str]
    status: Status
    previous_status: Optional[Status]
    direction: Optional[str]

    class Config:
        extra = 'allow'
        fields = {
            'url': {'alias': '_self'},
            'last_comment_update_at': {'alias': 'lastCommentUpdatedAt'},
            'updated_by': {'alias': 'updatedBy'},
            'created_at': {'alias': 'createdAt'},
            'created_by': {'alias': 'createdBy'},
            'updated_at': {'alias': 'updatedAt'},
            'previous_status': {'alias': 'previousStatus'},
        }

    async def get_transitions(self) -> Transitions:
        """
        Returns dict and list-like Transitions object.

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

    async def get_comments(self):
        """
        Get comments for self
        :return:
        """
        return await self.tracker.get_comments(self.id)

    async def post_comment(self, text=None, **kwargs):
        """
        Post comment for self
        :param text:
        :param kwargs:
        :return: Comment
        """
        return await self.tracker.post_comment(self.id, text=text, **kwargs)
