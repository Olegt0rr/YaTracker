from __future__ import annotations

__all__ = ["FullQueue"]

from .base import Base, field
from .issue_type import IssueType
from .issue_type_config import IssueTypeConfig
from .priority import Priority
from .queue_version import QueueVersion
from .user import User
from .workflow import Workflow


class FullQueue(Base, kw_only=True):
    url: str = field(name="self")
    id: int
    key: str
    version: int

    name: str
    description: str | None = None
    lead: User
    assign_auto: bool
    default_type: IssueType
    default_priority: Priority
    team_users: list[User]
    issue_types: list[IssueType]
    versions: list[QueueVersion]
    workflows: list[Workflow]
    deny_voting: bool
    issue_types_config: list[IssueTypeConfig]
