from __future__ import annotations

import logging

from .base import BaseTracker
from .categories import (
    Attachments,
    BulkChanges,
    Comments,
    Imports,
    Issues,
    Priorities,
    Queues,
    Worklogs,
)

logger = logging.getLogger(__name__)


class YaTracker(
    Queues,
    Issues,
    Comments,
    Priorities,
    Attachments,
    Worklogs,
    BulkChanges,
    Imports,
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
