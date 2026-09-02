from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker, _split_fields
from yatracker.types.report import Report, ReportSearchResult, ReportSort

if TYPE_CHECKING:
    from collections.abc import Sequence

REPORTS_URI = "/entities/report/"


def _dump_sorts(
    sorts: Sequence[ReportSort | dict[str, Any]],
) -> list[dict[str, Any]]:
    """Encode the sorting rules of a report the way the API expects them."""
    return [
        sort.model_dump(mode="json", by_alias=True, exclude_none=True)
        if isinstance(sort, ReportSort)
        else sort
        for sort in sorts
    ]


class Reports(BaseTracker):
    """Issue reports (`/entities/report`)."""

    async def create_report(  # noqa: PLR0913
        self,
        summary: str,
        *,
        fields: str | Sequence[str] | None = None,
        format_: str = "xlsx",
        query: str | None = None,
        filter_: dict[str, Any] | None = None,
        filter_id: str | int | None = None,
        sorts: Sequence[ReportSort | dict[str, Any]] | None = None,
        type_: str = "issueFilterExport",
    ) -> Report:
        """Create an issue report.

        The report exports the issues matching the search criteria.
        Open it in the interface at
        `https://tracker.yandex.ru/pages/reports/<id>`.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/create-report

        :param summary: name of the report.
        :param fields: issue fields to include into the report, e.g.
            `["priority", "type", "key", "summary", "assignee",
            "status", "updated"]`. A comma-separated string
            (`"priority,type,key"`) is accepted too and split into the
            JSON array the API wants.
        :param format_: export format: "xlsx", "xml" or "csv".
        :param query: filter written in the query language. Mutually
            exclusive with `filter_` and `filter_id`.
        :param filter_: field filters, e.g.
            `{"queue": "TREK", "assignee": "empty()"}`. Mutually
            exclusive with `query` and `filter_id`.
        :param filter_id: id of a saved filter. Mutually exclusive with
            `query` and `filter_`.
        :param sorts: sorting rules, e.g.
            `[ReportSort(order_by="updated", order_asc=False)]`.
        :param type_: export type. The only documented value is
            "issueFilterExport".
        :raises ValueError: if none of `query`, `filter_` and
            `filter_id` is given, or if more than one of them is.
        :return: the created report.
        """
        given = [
            name
            for name, value in (
                ("query", query),
                ("filter_", filter_),
                ("filter_id", filter_id),
            )
            if value is not None
        ]
        if not given:
            msg = (
                "Pass one of `query`, `filter_` and `filter_id`: the API "
                "needs to know which issues to export."
            )
            raise ValueError(msg)
        if len(given) > 1:
            msg = (
                f"Pass only one of `query`, `filter_` and `filter_id`, "
                f"got {', '.join(given)}: the API does not support "
                f"several filtering parameters at once."
            )
            raise ValueError(msg)

        report_filter: dict[str, Any] = {}
        if query is not None:
            report_filter["query"] = query
        if filter_ is not None:
            report_filter["filter"] = filter_
        if filter_id is not None:
            report_filter["filterId"] = filter_id
        if sorts is not None:
            report_filter["sorts"] = _dump_sorts(sorts)

        parameters: dict[str, Any] = {
            "type": type_,
            "format": format_,
            "filter": report_filter,
        }
        split_fields = _split_fields(fields)
        if split_fields is not None:
            parameters["fields"] = split_fields

        data = await self._client.request(
            method="POST",
            uri=REPORTS_URI,
            payload={"fields": {"summary": summary, "parameters": parameters}},
        )
        return self._decode(Report, data)

    async def search_reports(
        self,
        *,
        filter_: dict[str, Any] | None = None,
        order_by: str | None = None,
        order_asc: bool | None = None,
        per_page: int | None = None,
        page: int | None = None,
    ) -> ReportSearchResult:
        """Find the issue reports matching the given criteria.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/search-reports

        :param filter_: report filters. Only the `id`, `shortId` and
            `author` keys are supported, e.g. `{"author": "<user id>"}`.
        :param order_by: field to sort the reports by: "id", "shortId",
            "createdBy", "createdAt", "updatedAt" or "self".
        :param order_asc: sort direction: ascending if `True`.
        :param per_page: number of reports per page (50 by default).
        :param page: page number (1 by default).
        :return: page of the reports found.
        """
        payload = self._prepare_payload(locals(), exclude=["per_page", "page"])

        data = await self._client.request(
            method="POST",
            uri=f"{REPORTS_URI}_search",
            params=self._prepare_params(per_page=per_page, page=page),
            payload=payload,
        )
        return self._decode(ReportSearchResult, data)
