from __future__ import annotations

__all__ = ["FullQueue", "QueueVersionRef"]

from .base import Base, field
from .component import ComponentRef
from .issue_type import IssueType
from .issue_type_config import IssueTypeConfig
from .priority import Priority
from .ref import Ref
from .user import User
from .workflow import Workflow


class QueueVersionRef(Ref):
    """Short version reference embedded into a queue object.

    The queue payload carries only `self`, `id` and `display` for every
    version, unlike the full objects returned by `/queues/{id}/versions`.

    Source:
    https://yandex.ru/support/tracker/ru/concepts/queues/get-queue

    `display` is not sent by the v2 API.
    """


class FullQueue(Base):
    """Queue with all its details.

    Fields that the API only returns for an explicit `expand` request
    (`team`, `types`, `versions`, `components`, `workflows`,
    `issueTypesConfig`) are optional, so a plain `GET /queues` or
    `GET /queues/{id}` response can be decoded as well.

    Source:
    https://yandex.ru/support/tracker/ru/concepts/queues/get-queue
    """

    url: str = field(alias="self")
    id: str
    key: str
    version: int

    name: str
    description: str | None = None
    lead: User
    assign_auto: bool
    allow_externals: bool | None = None
    default_type: IssueType
    default_priority: Priority
    team_users: list[User] | None = None
    issue_types: list[IssueType] | None = None
    versions: list[QueueVersionRef] | None = None
    components: list[ComponentRef] | None = None
    # v3 returns a `{workflow: [issue type, ...]}` mapping, v2 a plain array
    workflows: dict[str, list[IssueType]] | list[Workflow] | None = None
    deny_voting: bool | None = None
    issue_types_config: list[IssueTypeConfig] | None = None
