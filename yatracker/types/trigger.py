from __future__ import annotations

__all__ = [
    "Trigger",
    "TriggerAction",
    "TriggerCondition",
    "TriggerWebhookLog",
    "TriggerWebhookLogRequest",
    "TriggerWebhookLogResponse",
]

from datetime import datetime
from typing import Any

from .base import Base, field, url_field
from .queue import Queue
from .status import Status


class TriggerAction(Base):
    """One action performed by a trigger (or by an autoaction).

    The API models every action kind with the same flat object
    discriminated by `type`, so this model keeps a single `type` field
    and the union of the documented keys; anything not listed here is
    ignored on decoding. Only the keys that belong to the action kind
    should be filled in, the rest stay `None` and are not sent.

    Documented `type` values (trigger actions):
    `Transition` (change the issue status), `Update` (change field
    values), `Move` (move the issue to another queue), `CreateComment`
    (add a comment), `CreateChecklist` (create a checklist), `Webhook`
    (send an HTTP request), `CalculateFormula` (calculate a value) and
    `CreateIssue` (create an issue). Autoactions support `Transition`,
    `Update`, `CreateComment`, `Webhook` and `CalculateFormula`. The
    response tables also mention the legacy spellings `Event.create` and
    `Event.comment-create` for the last two; the type is not validated
    client-side.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/change-trigger-actions

    Attributes
    ----------
    type - Action kind, see above.
    id - Action ID (assigned by the API, absent in requests).
    status - `Transition`: the target status. Requests accept a status
    key, id or name (a string) or an object such as `{"key": "open"}`;
    responses carry the full status object.
    formula - `CalculateFormula`: the mathematical expression.
    result_field - `CalculateFormula`: key or name of the field the
    result is written to.
    update - `Update`: mapping of issue field key to its new value.
    `None` clears the field, and the `set` / `add` / `remove` operators
    are accepted as well (`{"tags": {"add": "New tag"}}`).
    queue - `Move` / `CreateIssue`: key of the target queue.
    text - `CreateComment`: text of the comment.
    from_robot - `CreateComment` / `CreateIssue`: whether to act on
    behalf of the robot instead of the user who fired the trigger.
    checklist_items - `CreateChecklist`: the checklist items, each one
    an object with `text` (required), `assignee` and `deadline`
    (`{"date": "YYYY-MM-DD"}`). Kept as plain dicts because the docs
    do not describe how the API echoes them back.
    endpoint - `Webhook`: URL the request is sent to.
    auth_context - `Webhook`: authorization data, one of
    `{"type": "noauth"}`, `{"type": "basic", "login": ..., "password": ...}`
    or `{"type": "oauth", "headerName": ..., "accessToken": ..., "tokenType": ...}`.
    method - `Webhook`: HTTP method (`GET`, `POST`, `PUT` or `DELETE`).
    content_type - `Webhook`: content type of the request body.
    headers - `Webhook`: request headers.
    body - `Webhook`: request body, an object or a string.
    summary - `CreateIssue`: name of the created issue.
    field_templates - `CreateIssue`: fields of the created issue
    (`followers`, `dueDate`, `description`, `assignee`, `priority`,
    `type`, `tags`).
    link_with_initial_issue - `CreateIssue`: whether to link the created
    issue with the one that fired the trigger.

    """

    type: str
    id: str | None = None
    status: Status | str | dict[str, Any] | None = None
    formula: str | None = None
    result_field: str | None = None
    update: dict[str, Any] | None = None
    queue: Queue | str | dict[str, Any] | None = None
    text: str | None = None
    from_robot: bool | None = None
    checklist_items: list[dict[str, Any]] | None = None
    endpoint: str | None = None
    auth_context: dict[str, Any] | None = None
    method: str | None = None
    content_type: str | None = None
    headers: dict[str, str] | None = None
    body: dict[str, Any] | str | None = None
    summary: str | None = None
    field_templates: dict[str, Any] | None = None
    link_with_initial_issue: bool | None = None


class TriggerCondition(Base):
    """One condition that makes a trigger fire.

    Like :class:`TriggerAction` this is a single flat object
    discriminated by `type`. A condition is either a logical group
    (`And` / `Or`, with the nested conditions in `conditions`) or an
    elementary condition, in which case the meaningful keys depend on
    `type`.

    Elementary conditions documented by the API: events
    (`Event.update`, `Event.create`, `Event.comment-create`,
    `CalculationFormulaWatch`), `ChecklistDone`, comment text
    (`CommentFullyMatchCondition`, `CommentStringMatchCondition`,
    `CommentStringNotMatchCondition`, `CommentAnyMatchCondition`,
    `CommentNoneMatchCondition`), comment author (`CommentAuthor`,
    `CommentAuthorNot`), comment kind (`CommentMessageInternal`,
    `CommentMessageExternal`), issue links (`CreatedLinkCondition`,
    `UpdatedLinkCondition`, `RemovedLinkCondition`) and the field
    conditions (`FieldChangedCondition`, `FieldEquals`,
    `FieldBecameEqual`, `FieldIsEmpty`, `FieldIsNotEmpty`,
    `FieldBecameEmpty`, `FieldBecameNotEmpty`, `Date*Condition`,
    `UserInGroups`, `UserNotInGroups`, `Container.Size*`,
    `ContainerContains*`, `GreaterCondition`, `LessCondition`,
    `Became*Condition`, `FieldEqualsString`, `ContainsAnyOfStrings`,
    `ContainsNoneOfStrings`). The type is not validated client-side.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/change-trigger-conditions

    Attributes
    ----------
    type - Condition kind, see above. For a group it is `And` or `Or`
    (the response of `get_triggers` also uses them capitalized).
    conditions - Nested conditions of an `And` / `Or` group.
    field - Key of the issue field the condition is about.
    value - Value the field is compared with: a string, a number or a
    list, depending on the condition kind.
    word - Comment fragment(s) searched for by the `Comment*Condition`
    conditions: a string for `CommentFullyMatchCondition`,
    `CommentStringMatchCondition` and `CommentStringNotMatchCondition`,
    a list of strings for `CommentAnyMatchCondition` and
    `CommentNoneMatchCondition`.
    words - Same as `word`; the reference table names the parameter
    `word` while its example sends `words`, so both are accepted and
    only the one that is set is sent.
    user - Login or ID of the comment author (`CommentAuthor`,
    `CommentAuthorNot`).
    relationship - Issue link types of the `*LinkCondition` conditions,
    e.g. `["is parent task for", "is epic of"]`.
    ignore_case - Whether the text comparison ignores the letter case.
    remove_markup - Whether the text comparison ignores the markup.
    no_match_before - Whether the value is required to have changed
    (i.e. not to have matched before).

    """

    type: str
    conditions: list[TriggerCondition] | None = None
    field: str | None = None
    value: Any = None
    word: str | list[str] | None = None
    words: str | list[str] | None = None
    user: str | None = None
    relationship: str | list[str] | None = None
    ignore_case: bool | None = None
    remove_markup: bool | None = None
    no_match_before: bool | None = None


class Trigger(Base):
    """Represents a queue trigger.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/get-trigger

    Attributes
    ----------
    url - Reference to the trigger.
    id - Trigger ID.
    queue - Queue the trigger belongs to.
    name - Trigger name.
    order - Weight of the trigger; defines its position in the
    interface.
    actions - Actions performed by the trigger.
    conditions - Conditions that make the trigger fire.
    version - Trigger version, incremented by every change. Pass it to
    `update_trigger`.
    active - Whether the trigger is active.

    """

    url: str = url_field()
    id: str
    queue: Queue
    name: str
    order: str
    actions: list[TriggerAction] = field(default_factory=list)
    conditions: list[TriggerCondition] = field(default_factory=list)
    version: int
    active: bool


class TriggerWebhookLogRequest(Base):
    """HTTP request sent by a `Webhook` trigger action.

    Attributes
    ----------
    method - HTTP method of the request.
    endpoint - URL the request was sent to.
    headers - Request headers (values are masked by the API).
    body - Request body.
    webhook_auth_context - Authorization data of the request. Only its
    `type` is documented, the credentials themselves are masked.

    """

    method: str | None = None
    endpoint: str | None = None
    headers: dict[str, str] | None = None
    body: str | None = None
    webhook_auth_context: dict[str, Any] | None = None


class TriggerWebhookLogResponse(Base):
    """HTTP response received by a `Webhook` trigger action.

    Attributes
    ----------
    headers - Response headers (values are masked by the API).
    status_code - HTTP status code of the response.

    """

    headers: dict[str, str] | None = None
    status_code: int | None = None


class TriggerWebhookLog(Base):
    """One log entry of a `Webhook` trigger action.

    Only the HTTP-request action is logged. Every field except `id` is
    optional: the docs show a single successful sample and say nothing
    about what a failed run leaves out.

    Source:
    https://yandex.ru/support/tracker/ru/api/queues/view-trigger-logs

    Attributes
    ----------
    id - ID of the trigger run.
    start_time - When the run started.
    end_time - When the run finished.
    duration - Duration of the run in milliseconds.
    trigger_id - ID of the trigger.
    action_id - ID of the action inside the trigger.
    issue_id - ID of the issue the trigger fired on.
    request - The HTTP request that was sent.
    response - The HTTP response that was received.

    """

    id: str
    start_time: datetime | None = None
    end_time: datetime | None = None
    duration: int | None = None
    trigger_id: str | None = None
    action_id: str | None = None
    issue_id: str | None = None
    request: TriggerWebhookLogRequest | None = None
    response: TriggerWebhookLogResponse | None = None
