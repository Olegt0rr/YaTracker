import logging
from typing import Any, Optional, Union

from yatracker.types import (
    Comment,
    FullIssue,
    Issue,
    IssueType,
    Priority,
    Transition,
    Transitions,
    YaTrackerError,
)

from .base import BaseTracker

logger = logging.getLogger(__name__)


class YaTracker(BaseTracker):
    """Represents Yandex Tracker API client.

    API docs: https://cloud.yandex.com/en/docs/tracker/about-api

    Attention!
        All 'self' properties renamed to 'link' because it's incompatible with Python.
        All camelCase properties renamed to pythonic_case.
        Methods named by author, cause Yandex API has no clear method names.
        For help you to recognize method names full description is attached.

    """

    async def get_issue(
        self,
        issue_id: str,
        expand: Optional[str] = None,
    ) -> FullIssue:
        """View issue parameters.
        Use this request to get information about an issue.

        :param issue_id: ID or key of the current issue.
        :param expand: Additional fields to include in the response:
                        transitions — Workflow transitions between statuses.
                        attachments — Attachments

        :return:
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}",
            params={"expand": expand} if expand else None,
        )
        decoder = self._get_decoder(FullIssue)
        return decoder.decode(data)

    async def edit_issue(
        self,
        issue_id: str,
        version: Optional[Union[str, int]] = None,
        **kwargs,
    ) -> FullIssue:
        """Make changes to an issue.

        Use this request to make changes to an issue.
        The issue is selected by its ID or key.

        Source:
        https://yandex.com/dev/connect/tracker/api/concepts/issues/patch-issue.html
        """
        data = await self._client.request(
            method="PATCH",
            uri=f"/issues/{issue_id}",
            params={"version": str(version)} if version else None,
            payload=self.clear_payload(kwargs),
        )
        decoder = self._get_decoder(FullIssue)
        return decoder.decode(data)

    async def create_issue(
        self,
        summary: str,
        queue: str,
        parent: Optional[Issue] = None,
        description: Optional[str] = None,
        sprint: Optional[dict[str, str]] = None,
        type_: Optional[IssueType] = None,
        priority: Optional[Union[int, str, Priority]] = None,
        followers: Optional[list[str]] = None,
        unique: Optional[str] = None,
        **kwargs,
    ) -> FullIssue:
        """Create an issue."""
        payload = self.clear_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/issues/",
            payload=payload,
        )
        decoder = self._get_decoder(FullIssue)
        return decoder.decode(data)

    async def get_comments(self, issue_id: str) -> list[Comment]:
        """Get the comments for an issue.

        Use this request to get a list of comments in the issue.
        :param issue_id:
        :return:
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/comments",
        )
        if not isinstance(data, list):
            msg = "Invalid response"
            raise YaTrackerError(msg)

        decoder = self._get_decoder(Comment)
        return [decoder.decode(item) for item in data]

    async def post_comment(self, issue_id, text, **kwargs) -> Comment:
        payload = self.clear_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/comments/",
            payload=payload,
        )
        decoder = self._get_decoder(Comment)
        return decoder.decode(data)

    async def count_issues(
        self,
        filter_: Optional[dict[str, str]] = None,
        query: Optional[str] = None,
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
        return int(data)

    async def find_issues(
        self,
        filter_: Optional[dict[str, str]] = None,
        query: Optional[str] = None,
        order: Optional[str] = None,
        expand: Optional[str] = None,
        keys: Optional[str] = None,
        queue: Optional[str] = None,
    ) -> list[FullIssue]:
        """Find issues.

        Use this request to get a list of issues that meet specific criteria.
        If there are more than 10,000 issues in the response, use paging.
        :return:
        """
        payload = self.clear_payload(locals(), exclude=["expand", "order"])

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
        decoder = self._get_decoder(FullIssue)
        return [decoder.decode(item) for item in data]

    async def get_priorities(self, localized: bool = True) -> list[Priority]:
        """Get priorities.

        Use this request to get a list of priorities for an issue.
        """
        params = {"localized": str(localized).lower()} if localized else None
        data = await self._client.request(
            method="GET",
            uri="/priorities",
            params=params,
        )

        decoder = self._get_decoder(Priority)
        return [decoder.decode(item) for item in data]

    async def get_issue_links(self, issue_id: str) -> list[FullIssue]:
        """Get issue links.

        Use this request to get information about links between issues.
        The issue is selected by its ID or key.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/links",
        )
        if not isinstance(data, list):
            msg = "Not a list"
            raise YaTrackerError(msg)

        decoder = self._get_decoder(FullIssue)
        return [decoder.decode(item) for item in data]

    async def get_transitions(self, issue_id) -> Transitions:
        """Get transitions.

        Use this request to get a list of possible transitions for an issue.
        The issue is selected by its ID or key.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/transitions",
        )
        decoder = self._get_decoder(Transition)
        transitions = {}

        for item in data:
            transition = decoder.decode(item)
            transitions[transition.id] = transition

        return Transitions(**transitions)

    async def execute_transition(
        self,
        transition: Transition,
        **kwargs,
    ) -> list[Transition]:
        """Execute transition."""
        payload = self.clear_payload(kwargs)
        data = await self._client.request(
            method="POST",
            uri=f"{transition.url}/_execute",
            payload=payload,
        )
        decoder = self._get_decoder(Transition)
        return [decoder.decode(item) for item in data]
