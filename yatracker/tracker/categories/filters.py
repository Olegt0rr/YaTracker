from __future__ import annotations

from typing import TYPE_CHECKING, Any

from yatracker.tracker.base import BaseTracker
from yatracker.types.filter import Filter, FilterSort

if TYPE_CHECKING:
    from collections.abc import Sequence

# ruff: noqa: PLR0913


def _encode_sorts(
    sorts: Sequence[FilterSort | dict[str, Any]] | None,
) -> list[dict[str, Any]] | None:
    """Bring `sorts` to the request format.

    A request entry is `{"field": "<field key>", "isAscending": <bool>}`,
    while a response entry carries the whole field object; accepting
    :class:`FilterSort` as well lets a filter be re-sent as is. Dicts are
    passed through verbatim, so custom keys keep working.
    """
    if sorts is None:
        return None

    encoded: list[dict[str, Any]] = []
    for sort in sorts:
        if isinstance(sort, FilterSort):
            entry: dict[str, Any] = {"field": sort.field.id}
            if sort.is_ascending is not None:
                entry["isAscending"] = sort.is_ascending
            encoded.append(entry)
        else:
            encoded.append(dict(sort))
    return encoded


class Filters(BaseTracker):
    """Saved issue filters.

    A filter selects issues either by field conditions (`filter_`) or by
    a query-language string (`query`); the API does not support both at
    once.
    """

    async def create_filter(
        self,
        name: str,
        *,
        filter_: dict[str, Any] | None = None,
        query: str | None = None,
        fields: Sequence[str] | None = None,
        sorts: Sequence[FilterSort | dict[str, Any]] | None = None,
        group_by: str | dict[str, Any] | None = None,
        folder: str | dict[str, Any] | None = None,
        **kwargs,
    ) -> Filter:
        """Create an issue filter.

        Source:
        https://yandex.ru/support/tracker/ru/api/filters/create-filter

        :param name: filter name.
        :param filter_: filtering conditions keyed by issue field name,
            e.g. `{"status": "open", "assignee": "me()"}`. A value may
            also be a list (`{"status": ["open", "inProgress"]}`) or a
            date range (`{"created": "2024-01-01..2024-12-31"}`).
            Sent as `filter`.
        :param query: filtering conditions in the query language. Use
            either `query` or `filter_`, not both.
        :param fields: issue fields displayed in the Tracker interface,
            e.g. `["key", "summary", "status"]`. Affects the interface
            only, not the result of `/issues/_search`.
        :param sorts: sorting rules, e.g.
            `[{"field": "created", "isAscending": False}]`. The entries
            of another filter's `sorts` are accepted as well.
        :param group_by: issue field the result is grouped by in the
            interface.
        :param folder: folder to save the filter in.
        :param kwargs: any other filter field.
        :return: created filter.
        """
        sorts = _encode_sorts(sorts)
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/filters/",
            payload=payload,
        )
        return self._decode(Filter, data)

    async def get_filter(self, filter_id: str | int) -> Filter:
        """Get an issue filter.

        Source:
        https://yandex.ru/support/tracker/ru/api/filters/get-filter

        :param filter_id: ID of the filter.
        :return: filter.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/filters/{filter_id}",
        )
        return self._decode(Filter, data)

    async def update_filter(
        self,
        filter_id: str | int,
        *,
        name: str | None = None,
        filter_: dict[str, Any] | None = None,
        query: str | None = None,
        fields: Sequence[str] | None = None,
        sorts: Sequence[FilterSort | dict[str, Any]] | None = None,
        group_by: str | dict[str, Any] | None = None,
        folder: str | dict[str, Any] | None = None,
        **kwargs,
    ) -> Filter:
        """Edit an issue filter.

        `filter_` replaces the conditions completely instead of being
        merged into them: pass every condition you want to keep.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        Source:
        https://yandex.ru/support/tracker/ru/api/filters/update-filter

        :param filter_id: ID of the filter to edit.
        :param name: new filter name.
        :param filter_: new filtering conditions, see `create_filter`.
            Sent as `filter`.
        :param query: new filtering conditions in the query language.
            Use either `query` or `filter_`, not both.
        :param fields: new list of issue fields displayed in the Tracker
            interface.
        :param sorts: new sorting rules, see `create_filter`.
        :param group_by: issue field the result is grouped by in the
            interface.
        :param folder: folder to save the filter in.
        :param kwargs: any other filter field.
        :return: updated filter.
        """
        sorts = _encode_sorts(sorts)
        payload = self._prepare_payload(locals(), exclude=["filter_id"])
        data = await self._client.request(
            method="PATCH",
            uri=f"/filters/{filter_id}",
            payload=payload,
        )
        return self._decode(Filter, data)
