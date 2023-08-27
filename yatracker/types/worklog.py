from __future__ import annotations

__all__ = ["Worklog"]

from datetime import datetime

from .base import Base, field
from .issue import Issue
from .user import User


class Worklog(Base, kw_only=True):
    url: str = field(name="self")
    id: int
    version: int
    issue: Issue
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None
    start: datetime
    duration: str
