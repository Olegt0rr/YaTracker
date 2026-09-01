from __future__ import annotations

from typing import TYPE_CHECKING, Any, TypeVar, overload

from yatracker.tracker.base import BaseTracker
from yatracker.types import (
    FullIssue,
    Issue,
    IssueLink,
    IssueType,
    Priority,
    Transition,
    Transitions,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping

IssueT_co = TypeVar("IssueT_co", bound=FullIssue, covariant=True)

SCROLL_ID_HEADER = "X-Scroll-Id"


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


class Issues(BaseTracker):
    @overload
    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        *,
        fields: str | None = None,
    ) -> FullIssue: ...

    @overload
    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        _type: type[IssueT_co] = ...,
        *,
        fields: str | None = None,
    ) -> IssueT_co: ...

    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        *,
        fields: str | None = None,
    ) -> IssueT_co | FullIssue:
        """Get issue parameters.

        Use this request to get information about an issue.

        :param issue_id: ID or key of the current issue.
        :param expand: Additional fields to include in the response:
                        transitions — Workflow transitions between statuses.
                        attachments — Attachments
        :param fields: Comma-separated list of response fields to
                        return. Non-listed fields are omitted from the
                        response, so pass a ``_type`` whose required
                        fields match the projection — the default
                        FullIssue needs the full field set.
        :param _type: you can use your own extended FullIssue type
        :return:
        """
        params: dict[str, str] = {}
        if expand:
            params["expand"] = expand
        if fields:
            params["fields"] = fields

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
        **kwargs,
    ) -> FullIssue: ...

    @overload
    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None = None,
        _type: type[IssueT_co] = ...,
        **kwargs,
    ) -> IssueT_co: ...

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
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/patch-issue
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
        _type: type[IssueT_co] = ...,
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
        _type: type[IssueT_co] = ...,
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
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/move-issue
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
        fields: str | None = None,
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
        fields: str | None = None,
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
        fields: str | None = None,
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
        the default FullIssue needs the full field set.
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
        if fields:
            params["fields"] = fields

        data = await self._client.request(
            method="POST",
            uri="/issues/_search",
            params=params,
            payload=payload,
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    # ruff: noqa: PLR0913
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
        fields: str | None = None,
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

        :param scroll_type: "sorted" or "unsorted".
        :param per_scroll: number of issues per scroll page.
        :param scroll_ttl_millis: lifetime of the scroll context, in ms.
        :param fields: comma-separated projection of response fields.
            Non-listed fields are omitted from the response, so pass a
            ``_type`` whose required fields match the projection — the
            default :class:`FullIssue` needs the full field set.
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
        if fields:
            params["fields"] = fields

        while True:
            data, headers = await self._client.request_with_headers(
                method="POST",
                uri="/issues/_search",
                params=params,
                payload=payload,
            )
            issues = self._decode(list[_type], data)  # type: ignore[valid-type]
            if not issues:
                return

            for issue in issues:
                yield issue

            scroll_id = _get_header(headers, SCROLL_ID_HEADER)
            if not scroll_id:
                return

            params = {**params, "scrollId": scroll_id}

    async def get_issue_links(
        self,
        issue_id: str,
    ) -> list[IssueLink]:
        """Get issue links.

        Use this request to get information about links between issues.
        The issue is selected by its ID or key.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/links",
        )
        return self._decode(list[IssueLink], data)

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
