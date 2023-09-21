from __future__ import annotations

__all__ = ["IssueTypeConfig"]


from .base import Base
from .issue_type import IssueType
from .resolution import Resolution
from .workflow import Workflow


class IssueTypeConfig(Base, kw_only=True):
    issue_type: IssueType
    workflow: Workflow
    resolutions: list[Resolution]
