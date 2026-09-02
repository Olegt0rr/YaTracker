"""Tests for the issue reports category (`Reports`, `/entities/report`).

Payloads are taken verbatim from the official documentation:
https://yandex.ru/support/tracker/ru/api/issues/create-report
https://yandex.ru/support/tracker/ru/api/issues/search-reports
"""

from __future__ import annotations

from typing import Any

import pytest
from yatracker.types.report import Report, ReportSearchResult, ReportSort

from tests.conftest import make_tracker, sent_json

# `POST /entities/report/` response sample.
REPORT_RESPONSE: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/entities/report/68f68b553cdc3969e0445570",
    "id": "68f68b553cdc3969e0445570",
    "version": 1,
    "shortId": 142,
    "entityType": "report",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/8000000000000004",
        "id": "8000000000000004",
        "display": "Имя Фамилия",
        "cloudUid": "aje71i6t2tuvanuoimem",
        "passportUid": 1234567890,
    },
    "createdAt": "2025-10-20T19:19:49.120+0000",
    "updatedAt": "2025-10-20T19:19:49.120+0000",
}

# Reports of the `POST /entities/report/_search` response sample.
SEARCH_REPORT_A: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/entities/report/6a0d7cfb81208304d255f618",
    "id": "6a0d7cfb81208304d255f618",
    "version": 5,
    "shortId": 185,
    "entityType": "report",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/8000000000000005",
        "id": "8000000000000005",
        "display": "Имя Фамилия",
        "cloudUid": "ajemqnuerc0d4oaf598d",
        "passportUid": 1987441286,
    },
    "createdAt": "2026-05-20T09:20:59.753+0000",
    "updatedAt": "2026-05-20T09:21:00.085+0000",
}
SEARCH_REPORT_B: dict[str, Any] = {
    "self": "https://api.tracker.yandex.net/v3/entities/report/6a0d7cec7e0f032a528bbcd4",
    "id": "6a0d7cec7e0f032a528bbcd4",
    "version": 27,
    "shortId": 184,
    "entityType": "report",
    "createdBy": {
        "self": "https://api.tracker.yandex.net/v3/users/8000000000000005",
        "id": "8000000000000005",
        "display": "Имя Фамилия",
        "cloudUid": "ajemqnuerc0d4oaf598d",
        "passportUid": 1987441286,
    },
    "createdAt": "2026-05-20T09:20:44.592+0000",
    "updatedAt": "2026-05-20T09:21:07.234+0000",
}

SEARCH_RESPONSE: dict[str, Any] = {
    "hits": 2,
    "pages": 1,
    "values": [SEARCH_REPORT_A, SEARCH_REPORT_B],
}


class TestCreateReport:
    """Doc example 1: report built from a query-language filter."""

    async def test_with_query_and_report_sort_objects_sends_exact_body(self) -> None:
        tracker, client = make_tracker(REPORT_RESPONSE)
        report_fields = [
            "priority",
            "type",
            "key",
            "summary",
            "assignee",
            "status",
            "updated",
        ]
        report = await tracker.create_report(
            "Выгрузка задач очереди SUPPORT",
            fields=report_fields,
            query='Queue: SUPPORT "Sort by": Updated DESC',
            sorts=[ReportSort(order_by="updated", order_asc=False)],
        )
        assert isinstance(report, Report)
        assert report.id == "68f68b553cdc3969e0445570"
        assert report.short_id == 142
        assert report.entity_type == "report"
        assert report.created_by.display == "Имя Фамилия"

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/entities/report/")
        assert sent_json(call) == {
            "fields": {
                "summary": "Выгрузка задач очереди SUPPORT",
                "parameters": {
                    "type": "issueFilterExport",
                    "format": "xlsx",
                    "filter": {
                        "query": 'Queue: SUPPORT "Sort by": Updated DESC',
                        "sorts": [{"orderBy": "updated", "orderAsc": False}],
                    },
                    "fields": [
                        "priority",
                        "type",
                        "key",
                        "summary",
                        "assignee",
                        "status",
                        "updated",
                    ],
                },
            },
        }

    async def test_with_filter_object_and_no_sorts_sends_exact_body(self) -> None:
        """Doc example 2: report built from a field-filter object."""
        tracker, client = make_tracker(REPORT_RESPONSE)
        await tracker.create_report(
            "Задачи без исполнителя",
            fields=["key", "summary", "status", "priority", "created"],
            filter_={"queue": "TREK", "assignee": "empty()"},
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "fields": {
                "summary": "Задачи без исполнителя",
                "parameters": {
                    "type": "issueFilterExport",
                    "format": "xlsx",
                    "filter": {"filter": {"queue": "TREK", "assignee": "empty()"}},
                    "fields": ["key", "summary", "status", "priority", "created"],
                },
            },
        }

    async def test_with_filter_id_dict_sorts_and_custom_format_sends_exact_body(
        self,
    ) -> None:
        """Doc example 3: report built from a saved filter id.

        Also covers `sorts` given as plain dicts instead of `ReportSort`,
        and a non-default `format_`.
        """
        tracker, client = make_tracker(REPORT_RESPONSE)
        await tracker.create_report(
            "Отчет по сохраненному фильтру",
            fields=["key", "summary", "status", "assignee", "priority", "updated"],
            filter_id=12345,
            sorts=[{"orderBy": "updated", "orderAsc": True}],
            format_="csv",
        )

        call = client.calls[0]
        assert sent_json(call) == {
            "fields": {
                "summary": "Отчет по сохраненному фильтру",
                "parameters": {
                    "type": "issueFilterExport",
                    "format": "csv",
                    "filter": {
                        "filterId": 12345,
                        "sorts": [{"orderBy": "updated", "orderAsc": True}],
                    },
                    "fields": [
                        "key",
                        "summary",
                        "status",
                        "assignee",
                        "priority",
                        "updated",
                    ],
                },
            },
        }

    async def test_without_fields_omits_the_fields_key(self) -> None:
        tracker, client = make_tracker(REPORT_RESPONSE)
        await tracker.create_report("No fields", query="Queue: SUPPORT")

        call = client.calls[0]
        parameters = sent_json(call)["fields"]["parameters"]
        assert "fields" not in parameters
        assert parameters["filter"] == {"query": "Queue: SUPPORT"}

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"query": "q", "filter_": {"queue": "TREK"}},
            {"query": "q", "filter_id": 1},
            {"filter_": {"queue": "TREK"}, "filter_id": 1},
            {"query": "q", "filter_": {"queue": "TREK"}, "filter_id": 1},
        ],
    )
    async def test_raises_value_error_when_more_than_one_filter_kind_is_given(
        self,
        kwargs: dict[str, Any],
    ) -> None:
        tracker, client = make_tracker(REPORT_RESPONSE)
        with pytest.raises(ValueError, match="query"):
            await tracker.create_report("name", **kwargs)
        # the request must not have been sent
        assert client.calls == []

    async def test_raises_value_error_when_no_filter_kind_is_given(self) -> None:
        """The reference requires one of `query`, `filter` and `filterId`."""
        tracker, client = make_tracker(REPORT_RESPONSE)
        with pytest.raises(ValueError, match="Pass one of"):
            await tracker.create_report("name")
        # the request must not have been sent
        assert client.calls == []

    async def test_sorts_alone_is_not_a_filter_kind(self) -> None:
        tracker, client = make_tracker(REPORT_RESPONSE)
        with pytest.raises(ValueError, match="Pass one of"):
            await tracker.create_report("name", sorts=[{"orderBy": "key"}])
        assert client.calls == []


class TestSearchReports:
    async def test_sends_filter_body_and_pagination_query_params(self) -> None:
        tracker, client = make_tracker(SEARCH_RESPONSE)
        result = await tracker.search_reports(
            filter_={"author": "1987441286"},
            order_by="createdAt",
            order_asc=False,
            per_page=5,
            page=2,
        )
        assert isinstance(result, ReportSearchResult)
        assert result.hits == 2
        assert result.pages == 1
        assert len(result.values) == 2
        assert result.values[0].short_id == 185
        assert result.values[1].short_id == 184

        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith("/entities/report/_search")
        assert call["params"] == {"perPage": "5", "page": "2"}
        assert sent_json(call) == {
            "filter": {"author": "1987441286"},
            "orderBy": "createdAt",
            "orderAsc": False,
        }

    async def test_with_no_arguments_sends_an_empty_body_and_no_query_string(
        self,
    ) -> None:
        tracker, client = make_tracker(SEARCH_RESPONSE)
        await tracker.search_reports()

        call = client.calls[0]
        assert call["params"] is None
        assert sent_json(call) == {}

    async def test_decodes_the_order_by_field_when_returned(self) -> None:
        tracker, client = make_tracker({**SEARCH_RESPONSE, "orderBy": "author"})
        result = await tracker.search_reports(order_by="createdBy")
        assert result.order_by == "author"

        assert sent_json(client.calls[0]) == {"orderBy": "createdBy"}

    async def test_order_by_defaults_to_none_when_not_returned(self) -> None:
        tracker, _ = make_tracker(SEARCH_RESPONSE)
        result = await tracker.search_reports()
        assert result.order_by is None
