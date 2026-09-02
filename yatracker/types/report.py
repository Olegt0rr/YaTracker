from __future__ import annotations

__all__ = ["Report", "ReportSearchResult", "ReportSort"]

from datetime import datetime

from .base import Base, field, url_field
from .user import User


class ReportSort(Base):
    """Sorting rule of the issues included into a report.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/create-report

    Attributes
    ----------
    order_by - Issue field to sort by.
    order_asc - Sort direction: ascending if `True`, descending if
    `False`.

    """

    order_by: str
    order_asc: bool | None = None


class Report(Base):
    """Issue report entity (`/entities/report`).

    A report is an export of the issues matching a filter. Open it in
    the interface at `https://tracker.yandex.ru/pages/reports/<id>`.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/create-report

    Attributes
    ----------
    url - Reference to the report.
    id - ID of the report.
    version - Version of the report.
    short_id - Short ID of the report.
    entity_type - Type of the entity, always `report`.
    created_by - User who created the report.
    created_at - Date and time the report was created.
    updated_at - Date and time the report was last updated.

    """

    url: str = url_field()
    id: str
    version: int
    short_id: int
    entity_type: str
    created_by: User
    created_at: datetime
    updated_at: datetime | None = None


class ReportSearchResult(Base):
    """Page of reports returned by `POST /entities/report/_search`.

    Source:
    https://yandex.ru/support/tracker/ru/api/issues/search-reports

    Attributes
    ----------
    hits - Total number of the reports found.
    pages - Total number of the result pages.
    values - Reports of the current page.
    order_by - Field the reports are sorted by. Only returned when
    `orderBy` was passed; `createdBy`, `createdAt` and `updatedAt` come
    back as `author`, `created` and `updated`.

    """

    hits: int
    pages: int
    values: list[Report] = field(default_factory=list)
    order_by: str | None = None
