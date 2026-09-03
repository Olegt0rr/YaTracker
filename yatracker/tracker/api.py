from __future__ import annotations

import logging

from .base import BaseTracker
from .categories import (
    Applications,
    Attachments,
    Autoactions,
    Boards,
    BulkChanges,
    Checklists,
    Comments,
    Components,
    Dashboards,
    Entities,
    EntityAccess,
    EntityAttachments,
    EntityChecklists,
    EntityComments,
    EntityLinks,
    ExternalLinks,
    Filters,
    Gaps,
    Imports,
    IssueFields,
    Issues,
    IssueTypes,
    Macros,
    Priorities,
    Projects,
    QueueAccess,
    Queues,
    Reports,
    Resolutions,
    Sprints,
    Statuses,
    Triggers,
    Users,
    Workflows,
    Worklogs,
)

logger = logging.getLogger(__name__)


class YaTracker(
    Queues,
    QueueAccess,
    Issues,
    Comments,
    Checklists,
    IssueFields,
    IssueTypes,
    Priorities,
    Resolutions,
    Statuses,
    Users,
    Components,
    Projects,
    Entities,
    EntityComments,
    EntityAttachments,
    EntityChecklists,
    EntityLinks,
    EntityAccess,
    Macros,
    Boards,
    Sprints,
    Attachments,
    Worklogs,
    BulkChanges,
    Imports,
    Applications,
    ExternalLinks,
    Reports,
    Filters,
    Gaps,
    Dashboards,
    Triggers,
    Autoactions,
    Workflows,
    BaseTracker,
):
    """Represents Yandex Tracker API client.

    API docs: https://yandex.cloud/en/docs/tracker/about-api

    Attention!
        All 'self' properties renamed to 'url' because it's incompatible with Python.
        All camelCase properties renamed to pythonic_case.
        Methods named by author, cause Yandex API has no clear method names.
        For help you to recognize method names full description is attached.

    """
