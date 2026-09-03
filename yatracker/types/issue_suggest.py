from __future__ import annotations

__all__ = ["IssueSuggest"]

from .base import Base, url_field
from .status import Status
from .user import User


class IssueSuggest(Base):
    """Issue as returned by the suggest endpoint.

    `GET /issues/_suggest` answers with a bare projection of the issue,
    not with the whole issue: only `self`, `id`, `key` and `version` are
    always there, the rest of the documented fields depend on what the
    issue carries. Pass `_type=FullIssue` together with `full=True` to
    `suggest_issues` when you need whole issues instead.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/get-suggest
    """

    url: str = url_field()
    id: str
    key: str
    version: int

    summary: str | None = None
    followers: list[User] | None = None
    assignee: User | None = None
    status: Status | None = None
