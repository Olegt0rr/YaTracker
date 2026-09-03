from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.workflow import FullWorkflow

if TYPE_CHECKING:
    from collections.abc import Sequence

    from yatracker.types.localized_name import LocalizedNameInput

# ruff: noqa: PLR0913


class Workflows(BaseTracker):
    """Workflows API (`/workflows`).

    A workflow describes the lifecycle of an issue: the statuses it can
    be in (`steps`) and the transitions between them (`actions`). A
    workflow is either bound to a queue or common for the whole
    organization; queues pick the workflow of an issue type in their
    `issueTypesConfig`.

    The endpoints live under `/v3/workflows`, not under `/v3/queues`,
    even though the reference documents them in the queues section.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflows
    """

    async def get_workflows(self) -> list[FullWorkflow]:
        """Get the workflows of the organization.

        Every workflow of the organization is returned, deleted ones
        excluded. The endpoint is organization wide: it takes no queue,
        filter the result by `FullWorkflow.queue` to get the workflows
        of a single queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflows

        :return: list of workflows.
        """
        data = await self._client.request(
            method="GET",
            uri="/workflows",
        )
        return self._decode(list[FullWorkflow], data)

    async def get_workflow(self, workflow_id: str) -> FullWorkflow:
        """Get a workflow.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflow

        :param workflow_id: ID of the workflow, e.g. `W21`.
        :return: workflow.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/workflows/{workflow_id}",
        )
        return self._decode(FullWorkflow, data)

    async def create_workflow(
        self,
        name: str,
        initial_action: dict[str, Any],
        steps: Sequence[dict[str, Any]],
        *,
        id_: str | None = None,
        queue: str | int | dict[str, Any] | None = None,
        type_: str | None = None,
        issue_type_resolutions: Sequence[dict[str, Any]] | None = None,
    ) -> FullWorkflow:
        """Create a workflow.

        The blocks of the request body are passed as plain dicts, keyed
        the way the API expects them (`camelCase`, nested keys are sent
        verbatim).

        A step is `{"status": ..., "description": {...},
        "actions": [...], "metaAction": {...}, "statusType": ...}`,
        where `status` is a status key (string), a status id (number) or
        an object (`{"key": ...}` / `{"id": ...}` / `{"name": ...}`),
        `description` is a localized object (`{"ru": ..., "en": ...}`)
        and `statusType` is one of `NEW`, `IN_PROGRESS`, `PAUSED`,
        `DONE`, `CANCELLED`.

        An action is `{"id": ..., "name": {...}, "description": {...},
        "target": ..., "screen": {...}, "conditions": [...],
        "functions": [...]}`, where `name` is required and localized and
        `target` is a status in the same three forms as `status` above.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/workflows/post-workflow

        :param name: workflow name.
        :param initial_action: initial action — it sets the status an
            issue gets when it is created.
        :param steps: steps of the workflow. Every step is a status with
            the transitions available from it.
        :param id_: ID of the workflow, sent as `id` (the trailing
            underscore keeps the name out of the way of the builtin,
            like `type_`). The API generates one of the `W...` form
            when it is not passed.
        :param queue: queue to bind the workflow to: a queue key
            (string), a queue id (number) or an object (`{"key": ...}` /
            `{"id": ...}` / `{"name": ...}`). A common workflow, which
            can then be assigned to issue types in the settings of a
            queue, is created when it is not passed.
        :param type_: type of the workflow, sent as `type`. The only
            value is `VISUAL` (the API answers with `visual`).
        :param issue_type_resolutions: resolutions available per issue
            type, e.g.
            `[{"issueType": "task", "resolutions": ["fixed"]}]`.
        :return: created workflow.
        """
        payload = self._prepare_payload(locals())

        data = await self._client.request(
            method="POST",
            uri="/workflows",
            payload=payload,
        )
        return self._decode(FullWorkflow, data)

    async def update_workflow(
        self,
        workflow_id: str,
        version: str | int,
        *,
        name: str | None = None,
        type_: str | None = None,
        initial_action: dict[str, Any] | None = None,
        steps: Sequence[dict[str, Any]] | None = None,
        issue_type_resolutions: Sequence[dict[str, Any]] | None = None,
    ) -> FullWorkflow:
        """Edit a workflow.

        The blocks have the same shape as in `create_workflow`. `steps`
        replaces the whole graph, so pass every step of the workflow,
        not only the changed ones; use `update_workflow_action` to
        change a single transition.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/workflows/patch-workflow

        :param workflow_id: ID of the workflow to edit.
        :param version: current version of the workflow, sent as the
            `version` query parameter. The request fails with
            :class:`PreconditionFailedError` (412) if the workflow was
            changed meanwhile.
        :param name: new workflow name.
        :param type_: type of the workflow, sent as `type`. The only
            value is `VISUAL` (the API answers with `visual`).
        :param initial_action: new initial action.
        :param steps: new steps of the workflow.
        :param issue_type_resolutions: resolutions available per issue
            type.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated workflow.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["workflow_id", "version"],
        )

        data = await self._client.request(
            method="PATCH",
            uri=f"/workflows/{workflow_id}",
            params=self._prepare_params(version=version),
            payload=payload,
        )
        return self._decode(FullWorkflow, data)

    async def update_workflow_action(
        self,
        workflow_id: str,
        status: str,
        action_id: str,
        version: str | int,
        *,
        new_id: str | None = None,
        name: LocalizedNameInput | None = None,
        description: LocalizedNameInput | None = None,
        target: str | int | dict[str, Any] | None = None,
        screen: dict[str, Any] | None = None,
        conditions: Sequence[dict[str, Any]] | None = None,
        functions: Sequence[dict[str, Any]] | None = None,
    ) -> FullWorkflow:
        """Edit an action of a workflow step.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/workflows/patch-workflow-action

        :param workflow_id: ID of the workflow.
        :param status: key of the status (step) the action belongs to,
            e.g. `inProgress`.
        :param action_id: ID of the action inside the step, e.g.
            `close`.
        :param version: current version of the workflow, sent as the
            `version` query parameter. Unlike `update_workflow` (412),
            this endpoint reports a stale version as a conflict:
            :class:`AlreadyExistsError` (409).
        :param new_id: new ID of the action, sent as `id`.
        :param name: new action name in every language, e.g.
            `LocalizedName(ru="Завершить", en="Complete")` or
            `{"ru": "Завершить", "en": "Complete"}`.
        :param description: new action description in every language,
            same shape as `name`.
        :param target: new target status: a status key (string), a
            status id (number) or an object (`{"key": ...}` /
            `{"id": ...}` / `{"name": ...}`).
        :param screen: transition screen with the fields that can be
            filled in while the action runs.
        :param conditions: conditions the action runs under.
        :param functions: functions run on the transition.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: the whole updated workflow.
        """
        payload = self._prepare_payload(
            {**locals(), "id_": new_id},
            exclude=["new_id", "workflow_id", "status", "action_id", "version"],
        )

        data = await self._client.request(
            method="PATCH",
            uri=f"/workflows/{workflow_id}/steps/{status}/actions/{action_id}",
            params=self._prepare_params(version=version),
            payload=payload,
        )
        return self._decode(FullWorkflow, data)

    async def delete_workflow(self, workflow_id: str) -> bool:
        """Delete a workflow.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/workflows/delete-workflow

        :param workflow_id: ID of the workflow to delete.
        :return: `True` if the workflow was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/workflows/{workflow_id}",
        )
        return True
