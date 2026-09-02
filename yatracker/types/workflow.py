from __future__ import annotations

__all__ = ["Workflow"]

from .base import Base, url_field


class Workflow(Base):
    """Issue type lifecycle.

    Source:
    https://yandex.ru/support/tracker/ru/concepts/queues/get-queue
    """

    url: str = url_field()
    id: str
    display: str
    # not sent inside `issueTypesConfig` blocks
    key: str | None = None
