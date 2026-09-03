from __future__ import annotations

__all__ = [
    "FullWorkflow",
    "Workflow",
    "WorkflowAction",
    "WorkflowStep",
]

from datetime import datetime

from .base import Base, field, url_field
from .queue import Queue
from .status import Status
from .user import User


class Workflow(Base):
    """Issue type lifecycle.

    Short workflow reference embedded into queue payloads
    (`issueTypesConfig`). Use :class:`FullWorkflow`, returned by the
    `/workflows` endpoints, for the whole object.

    Source:
    https://yandex.ru/support/tracker/ru/concepts/queues/get-queue
    """

    url: str = url_field()
    id: str
    display: str
    # not sent inside `issueTypesConfig` blocks
    key: str | None = None


class WorkflowAction(Base):
    """Action (transition) of a workflow step.

    An action moves an issue from the status of its step to `target`.
    The same shape is used for the workflow's `initialAction`, which
    sets the status an issue gets on creation.

    The request format of an action is richer than the response one:
    `description`, `screen`, `conditions` and `functions` can be sent
    when a workflow is created or edited, but the reference does not
    list them among the response fields, so they are not modelled here.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflow

    Attributes
    ----------
    id - Action ID.
    name - Action name.
    target - Status the action moves the issue to.

    """

    id: str
    name: str
    target: Status


class WorkflowStep(Base):
    """Step of a workflow: a status and the transitions available from it.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflow

    Attributes
    ----------
    status - Status of the step.
    actions - Actions (transitions) available from this status. The API
    omits the key for a terminal step, so it is `None` there.

    """

    status: Status
    actions: list[WorkflowAction] | None = None


class FullWorkflow(Base):
    """Workflow of the organization (`/workflows` API).

    A workflow describes the lifecycle of an issue: the statuses it can
    be in (`steps`) and the transitions between them (`actions`).

    The reference notes that unfilled optional fields are not returned
    at all, naming `queue`, `type`, `createdBy` and `updatedBy` as
    examples, so everything but the identity of the workflow and its
    graph is optional here.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflow

    Attributes
    ----------
    url - Reference to the workflow.
    id - Workflow ID, e.g. `W21`.
    name - Workflow name.
    version - Workflow version. Each change increments it; pass it back
    to `update_workflow` / `update_workflow_action`.
    steps - Steps of the workflow.
    initial_action - Initial action, i.e. the status an issue gets when
    it is created.
    queue - Queue the workflow is bound to. Not sent for a common
    (organization wide) workflow.
    created - Date and time the workflow was created.
    updated - Date and time the workflow was last changed.
    created_by - Author of the workflow.
    updated_by - User who changed the workflow last.
    deleted - Whether the workflow was deleted.
    type - Type of the workflow. The only value is "visual"; workflows
    created earlier may carry no type at all. Requests use the upper
    case name ("VISUAL").

    """

    url: str = url_field()
    id: str
    name: str
    version: int
    steps: list[WorkflowStep] = field(default_factory=list)
    initial_action: WorkflowAction | None = None
    queue: Queue | None = None
    created: datetime | None = None
    updated: datetime | None = None
    created_by: User | None = None
    updated_by: User | None = None
    deleted: bool | None = None
    type: str | None = None
