from typing import List, Optional

from pydantic import BaseModel

from .objects import Issue, IssueType, Priority, Queue, Sprint, Status, User


class FullIssue(BaseModel):
    link: str
    id: str
    key: str
    version: int
    last_comment_update_at: Optional[str]
    summary: str
    parent: Optional[Issue]
    aliases: Optional[List[str]]
    updated_by: User
    description: str
    sprint: Optional[List[Sprint]]
    type: IssueType
    priority: Priority
    created_at: str
    followers: List[User]
    created_by: User
    votes: int
    assignee: User
    queue: Queue
    updated_at: str
    status: Status
    previous_status: Optional[Status]
    favorite: bool

    class Config:
        fields = {
            'link': {'alias': '_self'},
            'last_comment_update_at': {'alias': 'lastCommentUpdatedAt'},
            'updated_by': {'alias': 'updatedBy'},
            'created_at': {'alias': 'createdAt'},
            'created_by': {'alias': 'createdBy'},
            'updated_at': {'alias': 'updatedAt'},
            'previous_status': {'alias': 'previousStatus'},
        }
