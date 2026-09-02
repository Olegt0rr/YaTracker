from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, overload

from yatracker.tracker.base import (
    BaseTracker,
    IssueT_co,
    SuggestT_co,
    _iter_relative,
    _join_fields,
    _relative_page_size,
)
from yatracker.types import (
    FullIssue,
    Issue,
    IssueType,
    LinkRelationship,
    Priority,
    Transition,
    Transitions,
)
from yatracker.types.changelog import Changelog
from yatracker.types.issue_link import CreatedIssueLink, IssueLink
from yatracker.types.issue_suggest import IssueSuggest

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping, Sequence

logger = logging.getLogger(__name__)

SCROLL_ID_HEADER = "X-Scroll-Id"
SCROLL_TOKEN_HEADER = "X-Scroll-Token"  # noqa: S105 (a header name, not a secret)


def _get_header(headers: Mapping[str, str], name: str) -> str | None:
    """Read a header ignoring case (HTTP headers are case-insensitive)."""
    value = headers.get(name)
    if value is not None:
        return value

    lowered = name.lower()
    for key, header_value in headers.items():
        if key.lower() == lowered:
            return header_value
    return None


def _scroll_params(
    *,
    scroll_type: str,
    per_scroll: int,
    order: str | None,
    expand: str | None,
    scroll_ttl_millis: int | None,
    fields: str | Sequence[str] | None,
) -> dict[str, str]:
    """Build the query params of the FIRST scroll search page.

    `scrollType` and `perScroll` are documented as parameters of the
    first request of a scroll series only; the following ones are built
    by :func:`_next_scroll_params`.
    """
    params: dict[str, str] = {
        "scrollType": scroll_type,
        "perScroll": str(per_scroll),
    }
    if order:
        params["order"] = order
    if expand:
        params["expand"] = expand
    if scroll_ttl_millis is not None:
        params["scrollTTLMillis"] = str(scroll_ttl_millis)
    joined_fields = _join_fields(fields)
    if joined_fields:
        params["fields"] = joined_fields
    return params


def _next_scroll_params(params: dict[str, str], scroll_id: str) -> dict[str, str]:
    """Build the query params of the next page of a scroll search.

    Only `scrollId` identifies the page from the second request on:
    `scrollType` and `perScroll` belong to the first request of the
    series and are dropped here. `scrollTTLMillis` is kept because the
    reference sends it again in its second-request example, and the
    response projection (`order`, `expand`, `fields`) is kept so that
    every page decodes into the same model.
    """
    kept = {
        key: value
        for key, value in params.items()
        if key not in ("scrollType", "perScroll")
    }
    kept["scrollId"] = scroll_id
    return kept


class Issues(BaseTracker):
    @overload
    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        *,
        fields: str | Sequence[str] | None = None,
    ) -> FullIssue: ...

    @overload
    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        _type: type[IssueT_co] = ...,
        *,
        fields: str | Sequence[str] | None = None,
    ) -> IssueT_co: ...

    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        *,
        fields: str | Sequence[str] | None = None,
    ) -> IssueT_co | FullIssue:
        """Get issue parameters.

        Use this request to get information about an issue.

        :param issue_id: ID or key of the current issue.
        :param expand: Additional fields to include in the response:
                        transitions — Workflow transitions between statuses.
                        attachments — Attachments
        :param fields: Response fields to return: a comma-separated
                        string or a sequence of names. Non-listed fields
                        are omitted from the response, so pass a
                        ``_type`` whose required fields match the
                        projection — the default FullIssue needs the
                        full field set.
        :param _type: you can use your own extended FullIssue type
        :return:
        """
        params: dict[str, str] = {}
        if expand:
            params["expand"] = expand
        joined_fields = _join_fields(fields)
        if joined_fields:
            params["fields"] = joined_fields

        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}",
            params=params or None,
        )
        return self._decode(_type, data)

    @overload
    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None = None,
        *,
        _type: type[IssueT_co],
        **kwargs,
    ) -> IssueT_co: ...

    @overload
    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None,
        _type: type[IssueT_co],
        **kwargs,
    ) -> IssueT_co: ...

    @overload
    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None = None,
        **kwargs,
    ) -> FullIssue: ...

    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        **kwargs,
    ) -> IssueT_co | FullIssue:
        """Make changes to an issue.

        Use this request to make changes to an issue.
        The issue is selected by its ID or key.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/issues/patch-issue
        """
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}",
            params={"version": str(version)} if version else None,
            payload=self._prepare_payload(kwargs, type_=_type),
        )
        return self._decode(_type, data)

    @overload
    async def create_issue(
        self,
        summary: str,
        queue: str | int | dict,
        *,
        parent: Issue | str | None = None,
        description: str | None = None,
        sprint: dict[str, str] | None = None,
        type_: IssueType | None = None,
        priority: int | str | Priority | None = None,
        followers: list[str] | None = None,
        assignee: list[str] | None = None,
        unique: str | None = None,
        attachment_ids: list[str] | None = None,
        _type: type[IssueT_co],
        **kwargs,
    ) -> IssueT_co: ...

    @overload
    async def create_issue(
        self,
        summary: str,
        queue: str | int | dict,
        *,
        parent: Issue | str | None = None,
        description: str | None = None,
        sprint: dict[str, str] | None = None,
        type_: IssueType | None = None,
        priority: int | str | Priority | None = None,
        followers: list[str] | None = None,
        assignee: list[str] | None = None,
        unique: str | None = None,
        attachment_ids: list[str] | None = None,
        **kwargs,
    ) -> FullIssue: ...

    # ruff: noqa: PLR0913
    async def create_issue(
        self,
        summary: str,
        queue: str | int | dict,
        *,
        parent: Issue | str | None = None,
        description: str | None = None,
        sprint: dict[str, str] | None = None,
        type_: IssueType | None = None,
        priority: int | str | Priority | None = None,
        followers: list[str] | None = None,
        assignee: list[str] | None = None,
        unique: str | None = None,
        attachment_ids: list[str] | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        **kwargs,
    ) -> IssueT_co | FullIssue:
        """Create an issue.

        Source:
        https://cloud.yandex.ru/docs/tracker/concepts/issues/create-issue
        """
        payload = self._prepare_payload(locals(), type_=_type)
        data = await self._client.request(
            method="POST",
            uri="/issues/",
            payload=payload,
        )
        return self._decode(_type, data)

    @overload
    async def move_issue(
        self,
        issue_id: str,
        queue_key: str,
        *,
        notify: bool = True,
        notify_author: bool = False,
        move_all_fields: bool = False,
        initial_status: bool = False,
        expand: str | None = None,
        _type: type[IssueT_co],
        **kwargs,
    ) -> IssueT_co: ...

    @overload
    async def move_issue(
        self,
        issue_id: str,
        queue_key: str,
        *,
        notify: bool = True,
        notify_author: bool = False,
        move_all_fields: bool = False,
        initial_status: bool = False,
        expand: str | None = None,
        **kwargs,
    ) -> FullIssue: ...

    async def move_issue(
        self,
        issue_id: str,
        queue_key: str,
        *,
        notify: bool = True,
        notify_author: bool = False,
        move_all_fields: bool = False,
        initial_status: bool = False,
        expand: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        **kwargs,
    ) -> IssueT_co | FullIssue:
        """Move an issue to a different queue.

        Before executing the request, make sure the user has permission
        to edit the issues to be moved and is allowed to create them in
        the new queue.

        Warning!
        If an issue you want to move has a type and status that are
        missing in the target queue, no transfer will be made. To reset
        the issue status to the initial value when moving it, use the
        InitialStatus parameter.

        By default, when an issue is moved, the values of its
        components, versions, and projects are cleared. If the new queue
        has the same values of the fields specified, use the
        MoveAllFields parameter to move the components, versions, and
        projects.

        If the issue has the local field values specified, they will be
        reset when moving the issue to a different queue.

        You can use the request body if you need to change the
        parameters of the issue being moved. The request body has the
        same format as when editing issues.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/issues/move-issue
        """
        params: dict[str, Any] = {"queue": queue_key}

        if notify is False:
            params["notify"] = "false"

        if notify_author is True:
            params["notifyAuthor"] = "true"

        if move_all_fields is True:
            params["moveAllFields"] = "true"

        if initial_status is True:
            params["initialStatus"] = "true"

        if expand:
            params["expand"] = expand

        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/_move",
            params=params,
            payload=self._prepare_payload(kwargs, type_=_type),
        )
        return self._decode(_type, data)

    async def count_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
    ) -> int:
        """Get the number of issues.

        Use this request to find out how many issues meet the criteria in your request.
        :return:
        """
        payload: dict[str, Any] = {}
        if filter_ is not None:
            payload["filter"] = filter_
        if query is not None:
            payload["query"] = query

        data = await self._client.request(
            method="POST",
            uri="/issues/_count",
            payload=payload,
        )
        return self._decode(int, data)

    # ruff: noqa: PLR0913
    @overload
    async def find_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        keys: str | None = None,
        queue: str | None = None,
        *,
        per_page: int | None = None,
        page: int | None = None,
        scroll_type: str | None = None,
        per_scroll: int | None = None,
        scroll_ttl_millis: int | None = None,
        scroll_id: str | None = None,
        fields: str | Sequence[str] | None = None,
    ) -> list[FullIssue]: ...

    # ruff: noqa: PLR0913
    @overload
    async def find_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        keys: str | None = None,
        queue: str | None = None,
        _type: type[IssueT_co] = ...,
        *,
        per_page: int | None = None,
        page: int | None = None,
        scroll_type: str | None = None,
        per_scroll: int | None = None,
        scroll_ttl_millis: int | None = None,
        scroll_id: str | None = None,
        fields: str | Sequence[str] | None = None,
    ) -> list[IssueT_co]: ...

    # ruff: noqa: PLR0913
    async def find_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        keys: str | None = None,
        queue: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        *,
        per_page: int | None = None,
        page: int | None = None,
        scroll_type: str | None = None,
        per_scroll: int | None = None,
        scroll_ttl_millis: int | None = None,
        scroll_id: str | None = None,
        fields: str | Sequence[str] | None = None,
    ) -> list[IssueT_co] | list[FullIssue]:
        """Find issues.

        Use this request to get a list of issues that meet specific criteria.
        If there are more than 10,000 issues in the response, use paging.

        Pagination can be done either with ``page``/``per_page``, or with
        the scroll API: pass ``scroll_type`` ("sorted" or "unsorted") and
        ``per_scroll``/``scroll_ttl_millis`` to start a scroll session, then
        pass the ``scroll_id`` returned by the API on subsequent calls to
        continue it. Scroll is not supported together with the ``keys``
        or ``queue`` search forms (the API answers HTTP 400).

        ``fields`` projects the response: non-listed fields are omitted,
        so pass a ``_type`` whose required fields match the projection —
        the default FullIssue needs the full field set. It takes a
        comma-separated string or a sequence of field names.
        :return:
        """
        payload = self._prepare_payload(
            locals(),
            exclude=[
                "expand",
                "order",
                "per_page",
                "page",
                "scroll_type",
                "per_scroll",
                "scroll_ttl_millis",
                "scroll_id",
                "fields",
            ],
            type_=_type,
        )

        params: dict[str, str] = {}
        if order:
            params["order"] = order
        if expand:
            params["expand"] = expand
        if per_page is not None:
            params["perPage"] = str(per_page)
        if page is not None:
            params["page"] = str(page)
        if scroll_type:
            params["scrollType"] = scroll_type
        if per_scroll is not None:
            params["perScroll"] = str(per_scroll)
        if scroll_ttl_millis is not None:
            params["scrollTTLMillis"] = str(scroll_ttl_millis)
        if scroll_id:
            params["scrollId"] = scroll_id
        joined_fields = _join_fields(fields)
        if joined_fields:
            params["fields"] = joined_fields

        data = await self._client.request(
            method="POST",
            uri="/issues/_search",
            params=params,
            payload=payload,
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    # ruff: noqa: PLR0913
    @overload
    def iter_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        queue: str | None = None,
        *,
        scroll_type: str = "sorted",
        per_scroll: int = 100,
        scroll_ttl_millis: int | None = None,
        fields: str | Sequence[str] | None = None,
    ) -> AsyncIterator[FullIssue]: ...

    @overload
    def iter_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        queue: str | None = None,
        _type: type[IssueT_co] = ...,
        *,
        scroll_type: str = "sorted",
        per_scroll: int = 100,
        scroll_ttl_millis: int | None = None,
        fields: str | Sequence[str] | None = None,
    ) -> AsyncIterator[IssueT_co]: ...

    async def iter_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        queue: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        *,
        scroll_type: str = "sorted",
        per_scroll: int = 100,
        scroll_ttl_millis: int | None = None,
        fields: str | Sequence[str] | None = None,
    ) -> AsyncIterator[IssueT_co | FullIssue]:
        """Iterate over all issues matching the criteria via the scroll API.

        This is the supported way to read more than 10,000 issues: the
        scroll session is started with `scrollType`/`perScroll` and then
        continued with the `scrollId` returned in the `X-Scroll-Id`
        response header, which :meth:`find_issues` cannot expose.
        Iteration stops when a page comes back empty or the API stops
        sending the header.

        The API rejects scroll for the `keys`/`queue` search forms with
        HTTP 400, so there is no ``keys`` parameter here and ``queue``
        is folded into the supported ``filter`` form.

        :meth:`find_issues` with an explicit ``scroll_id`` remains
        available when you need to drive the scroll session manually.

        Every page holds a snapshot on the server until the scroll TTL
        expires. When the iteration is left early the accumulated
        `X-Scroll-Id`/`X-Scroll-Token` pairs are released with
        :meth:`clear_search_scroll` on a best-effort basis: errors of
        that call are swallowed (they are only logged), and it is
        skipped altogether once the tracker is closed, because a closed
        client cannot release anything any more.

        The release runs when the generator is *closed*, which a plain
        ``break`` does not do: it only suspends the generator until
        something finalizes it (``asyncio.run`` does, via
        ``shutdown_asyncgens``, but only when the loop shuts down, and
        an unclosed generator keeps the snapshot until its TTL). Close
        it explicitly to release the snapshot at a moment you control,
        and do it before leaving the ``async with`` block of the
        tracker::

            from contextlib import aclosing

            async with aclosing(tracker.iter_issues(query=...)) as issues:
                async for issue in issues:
                    if ...:
                        break

        or, without a context manager, ``gen = tracker.iter_issues(...)``
        and ``await gen.aclose()``.

        :param scroll_type: "sorted" or "unsorted".
        :param per_scroll: number of issues per scroll page.
        :param scroll_ttl_millis: lifetime of the scroll context, in ms.
        :param fields: projection of response fields: a comma-separated
            string or a sequence of names. Non-listed fields are omitted
            from the response, so pass a ``_type`` whose required fields
            match the projection — the default :class:`FullIssue` needs
            the full field set.
        """
        if queue is not None:
            filter_ = {**(filter_ or {}), "queue": queue}
            queue = None

        payload = self._prepare_payload(
            locals(),
            exclude=[
                "expand",
                "order",
                "scroll_type",
                "per_scroll",
                "scroll_ttl_millis",
                "fields",
            ],
            type_=_type,
        )

        params = _scroll_params(
            scroll_type=scroll_type,
            per_scroll=per_scroll,
            order=order,
            expand=expand,
            scroll_ttl_millis=scroll_ttl_millis,
            fields=fields,
        )

        pairs: dict[str, str] = {}
        completed = False
        try:
            while True:
                data, headers = await self._client.request_with_headers(
                    method="POST",
                    uri="/issues/_search",
                    params=params,
                    payload=payload,
                )
                scroll_id = _get_header(headers, SCROLL_ID_HEADER)
                scroll_token = _get_header(headers, SCROLL_TOKEN_HEADER)
                if scroll_id:
                    # `X-Scroll-Token` is documented as unused in the
                    # current v3 API, so it may well be absent: the pair
                    # is still recorded, with an empty token, otherwise
                    # the snapshot would never be released.
                    pairs[scroll_id] = scroll_token or ""

                issues = self._decode(list[_type], data)  # type: ignore[valid-type]
                if not issues:
                    completed = True
                    return

                for issue in issues:
                    yield issue

                if not scroll_id:
                    completed = True
                    return

                params = _next_scroll_params(params, scroll_id)
        finally:
            # Best effort: the caller may have gone away already, and a
            # failing release must not mask the original error. Every
            # exception is swallowed on purpose — the transport is
            # pluggable, so anything from `aiohttp.ClientError` to a
            # `TimeoutError` can come out of it. `CancelledError` is a
            # `BaseException` and still propagates.
            if pairs and not completed and not self._client.closed:
                try:
                    await self.clear_search_scroll(pairs)
                except Exception:
                    logger.warning(
                        "Failed to release the scroll contexts of a search; "
                        "they expire on their own after the scroll TTL.",
                        exc_info=True,
                    )

    async def clear_search_scroll(self, scroll_ids: Mapping[str, str]) -> bool:
        """Release the resources of a scroll search.

        Every page of a scroll search holds a snapshot on the server
        until it expires. Use this request to release them earlier.
        :meth:`iter_issues` calls it on your behalf when the iteration
        is left before the scroll is exhausted; call it yourself when
        you drive the scroll session manually.

        The docs show the request body as `{"srollId": "scrollToken"}`,
        which is a (misspelled) placeholder rather than a literal key:
        the parameter table names the value `scrollId` and the full
        example sends real scroll ids as the keys of the object. So the
        body is a plain mapping of a scroll id to its scroll token, and
        all the pairs of the search have to be sent at once — one pair
        per page of the search results.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/search-release

        :param scroll_ids: mapping of every `X-Scroll-Id` returned by
            the search to the matching `X-Scroll-Token`.
        :return: `True` if the resources were released.
        """
        await self._client.request(
            method="POST",
            uri="/system/search/scroll/_clear",
            payload=dict(scroll_ids),
        )
        return True

    @overload
    async def suggest_issues(
        self,
        input_: str,
        *,
        queue: str | None = None,
        full: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
        embed: str | None = None,
    ) -> list[IssueSuggest]: ...

    @overload
    async def suggest_issues(
        self,
        input_: str,
        _type: type[SuggestT_co] = ...,
        *,
        queue: str | None = None,
        full: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
        embed: str | None = None,
    ) -> list[SuggestT_co]: ...

    async def suggest_issues(
        self,
        input_: str,
        _type: type[SuggestT_co | IssueSuggest] = IssueSuggest,
        *,
        queue: str | None = None,
        full: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
        embed: str | None = None,
    ) -> list[SuggestT_co] | list[IssueSuggest]:
        """Get issue suggestions by a fragment of the issue name.

        Only the issues the user has access to are returned. The
        response is a projection of the issue, not the whole issue: the
        default :class:`IssueSuggest` decodes exactly that bare
        projection. To get whole issues instead, pass
        ``_type=FullIssue`` together with ``full=True`` and *without*
        ``fields`` — a projection narrower than :class:`FullIssue`
        requires fails to validate. With the default type ``full=True``
        still works, the extra fields are simply ignored.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-suggest

        :param input_: fragment of the issue name (query param "input").
            A space between words also matches any text in its place.
        :param _type: model to decode the response with;
            :class:`FullIssue` (with `full=True`) or your own model.
        :param queue: key of the queue to search in.
        :param full: whether to return the detailed information about
            every issue. Required to enable `fields`, `expand` and
            `embed`.
        :param fields: issue fields to return: a comma-separated string
            or a sequence of names.
        :param expand: additional information to include in the
            response: "all", "html", "attachments", "comments", "links",
            "localLinkRefs", "aliases", "transitions", "permissions",
            "sla" or "update_limits".
        :param embed: more details about what was asked in `expand`:
            "attachments", "comments", "transitions" or "sla".
        :return: list of the issues found.
        """
        data = await self._client.request(
            method="GET",
            uri="/issues/_suggest",
            params=self._prepare_params(
                input_=input_,
                queue=queue,
                full=full,
                fields=_join_fields(fields),
                expand=expand,
                embed=embed,
            ),
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    async def get_issue_changelog(
        self,
        issue_id: str,
        *,
        id_: str | None = None,
        per_page: int | None = None,
        field: str | None = None,
        type_: str | None = None,
    ) -> list[Changelog]:
        """Get one page of the change history of an issue.

        The API returns 50 changes per page by default; use `per_page`
        and the `id_` cursor (or :meth:`iter_issue_changelog`) to read
        the rest.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-changelog

        :param issue_id: ID or key of the issue.
        :param id_: id of the change the requested ones follow
            (query param "id"). Omit it to get the first page.
        :param per_page: number of changes per page (50 by default).
        :param field: id of the changed issue field to filter by, e.g.
            "checklistItems" or "status".
        :param type_: key of the change type to filter by, e.g.
            "IssueWorkflow" (query param "type").
        :return: list of the changelog records.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/changelog",
            params=self._prepare_params(
                id_=id_,
                per_page=per_page,
                field=field,
                type_=type_,
            ),
        )
        return self._decode(list[Changelog], data)

    async def iter_issue_changelog(
        self,
        issue_id: str,
        *,
        per_page: int | None = None,
        field: str | None = None,
        type_: str | None = None,
    ) -> AsyncIterator[Changelog]:
        """Iterate over the whole change history of an issue.

        Wraps :meth:`get_issue_changelog`: every page is requested with
        the id of the last change of the previous one (see
        :func:`yatracker.tracker.base._iter_relative`).

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-changelog

        :param issue_id: ID or key of the issue.
        :param per_page: number of changes per page (50 by default).
            `per_page=1` is sent as 2: the cursor change is resent on
            every page, so a page of one could never advance.
        :param field: id of the changed issue field to filter by.
        :param type_: key of the change type to filter by.
        """
        page_size = _relative_page_size(per_page)

        async def fetch_page(id_: str | None) -> list[Changelog]:
            return await self.get_issue_changelog(
                issue_id,
                id_=id_,
                per_page=page_size,
                field=field,
                type_=type_,
            )

        async for change in _iter_relative(
            fetch_page,
            items=lambda page: page,
            key=lambda change: change.id,
        ):
            yield change

    async def get_issue_links(
        self,
        issue_id: str,
    ) -> list[IssueLink]:
        """Get issue links.

        Use this request to get information about links between issues.
        The issue is selected by its ID or key.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-links
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/links",
        )
        return self._decode(list[IssueLink], data)

    async def link_issues(
        self,
        issue_id: str,
        relationship: LinkRelationship | str,
        issue: str | Issue | FullIssue,
    ) -> CreatedIssueLink:
        """Create a link between two issues.

        The link is created between the current issue (`issue_id`) and
        the linked one (`issue`).

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/link-issue

        :param issue_id: ID or key of the current issue.
        :param relationship: type of the link: "relates",
            "is dependent by", "depends on", "is subtask for",
            "is parent task for", "duplicates", "is duplicated by",
            "is epic of" or "has epic" (see :class:`LinkRelationship`).
            The two epic links are only allowed for epics.
        :param issue: ID or key of the issue to link, or an
            :class:`Issue` / :class:`FullIssue` object (its `key` is
            sent).
        :return: the created link. The API answers without `assignee`
            and `status`, hence :class:`CreatedIssueLink` rather than
            :class:`IssueLink`.
        """
        payload = {
            "relationship": relationship.value
            if isinstance(relationship, LinkRelationship)
            else relationship,
            "issue": issue.key if isinstance(issue, (Issue, FullIssue)) else issue,
        }
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/links",
            payload=payload,
        )
        return self._decode(CreatedIssueLink, data)

    async def unlink_issues(self, issue_id: str, link_id: str | int) -> bool:
        """Delete a link between two issues.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/delete-link-issue

        :param issue_id: ID or key of the current issue.
        :param link_id: ID of the link with the other issue.
        :return: `True` if the link was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/links/{link_id}",
        )
        return True

    async def get_transitions(self, issue_id: str) -> Transitions:
        """Get transitions.

        Use this request to get a list of possible transitions for an issue.
        The issue is selected by its ID or key.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/transitions",
        )
        transitions = self._decode(list[Transition], data)
        return Transitions(**{t.id: t for t in transitions})

    async def execute_transition(
        self,
        transition: Transition,
        **kwargs,
    ) -> list[Transition]:
        """Execute transition."""
        payload = self._prepare_payload(kwargs)
        data = await self._client.request(
            method="POST",
            uri=f"{transition.url}/_execute",
            payload=payload,
        )
        return self._decode(list[Transition], data)
