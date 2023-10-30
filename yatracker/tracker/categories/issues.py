from __future__ import annotations

from typing import Any, TypeVar, overload

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

IssueT_co = TypeVar("IssueT_co", bound=FullIssue, covariant=True)


class Issues(BaseTracker):
    @overload
    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
    ) -> FullIssue:
        ...

    @overload
    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        _type: type[IssueT_co] = ...,
    ) -> IssueT_co:
        ...

    async def get_issue(
        self,
        issue_id: str,
        expand: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
    ) -> IssueT_co | FullIssue:
        """Get issue parameters.

        Use this request to get information about an issue.

        :param issue_id: ID or key of the current issue.
        :param expand: Additional fields to include in the response:
                        transitions — Workflow transitions between statuses.
                        attachments — Attachments
        :param _type: you can use your own extended FullIssue type
        :return:
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}",
            params={"expand": expand} if expand else None,
        )
        return self._decode(_type, data)

    @overload
    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None = None,
        **kwargs,
    ) -> FullIssue:
        ...

    @overload
    async def edit_issue(
        self,
        issue_id: str,
        version: str | int | None = None,
        _type: type[IssueT_co] = ...,
        **kwargs,
    ) -> IssueT_co:
        ...

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
    ) -> IssueT_co:
        ...

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
    ) -> FullIssue:
        ...

    # ruff: noqa: ARG002 PLR0913
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
    ) -> IssueT_co:
        ...

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
    ) -> FullIssue:
        ...

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
            params["notify"] = notify

        if notify_author is True:
            params["notifyAuthor"] = notify_author

        if move_all_fields is True:
            params["moveAllFields"] = move_all_fields

        if initial_status is True:
            params["initialStatus"] = initial_status

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

    @overload
    async def find_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        keys: str | None = None,
        queue: str | None = None,
    ) -> list[FullIssue]:
        ...

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
    ) -> list[IssueT_co]:
        ...

    async def find_issues(
        self,
        filter_: dict[str, str] | None = None,
        query: str | None = None,
        order: str | None = None,
        expand: str | None = None,
        keys: str | None = None,
        queue: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
    ) -> list[IssueT_co] | list[FullIssue]:
        """Find issues.

        Use this request to get a list of issues that meet specific criteria.
        If there are more than 10,000 issues in the response, use paging.
        :return:
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["expand", "order"],
            type_=_type,
        )

        params = {}
        if order:
            params["order"] = order
        if expand:
            params["expand"] = expand

        data = await self._client.request(
            method="POST",
            uri="/issues/_search",
            params=params,
            payload=payload,
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

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
