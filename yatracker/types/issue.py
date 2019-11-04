from typing import List, Optional

from pydantic import BaseModel

from .objects import Issue, IssueType, Priority, Queue, Sprint, Status, User


class FullIssue(BaseModel):
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

    @property
    def tracker(self):
        from ..tracker import YaTracker
        return YaTracker.get_current()

    async def get_transitions(self):
        return await self.tracker.get_transitions(self.id)
