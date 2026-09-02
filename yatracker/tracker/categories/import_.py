from __future__ import annotations

from typing import TYPE_CHECKING, BinaryIO, overload

from aiohttp import FormData

from yatracker.tracker.base import BaseTracker, IssueT_co
from yatracker.types import (
    Attachment,
    Comment,
    FullIssue,
    IssueLink,
    LinkRelationship,
    Worklog,
)
from yatracker.utils.datetime import to_tracker_date, to_tracker_datetime

if TYPE_CHECKING:
    from datetime import date, datetime

# ruff: noqa: PLR0913


class Imports(BaseTracker):
    """Import issues, comments, links and attachments with original metadata.

    Unlike the regular "create" endpoints, the import ones let you set the
    author and the creation/update timestamps explicitly, which is what you
    need when migrating data from another tracker.

    Every request in this category requires organization admin rights.
    Timestamps accept either a (preferably timezone-aware) ``datetime``,
    rendered as ``YYYY-MM-DDThh:mm:ss.sss±hhmm``, or a ready-made string
    in that format, which is passed through verbatim.
    """

    @overload
    async def import_issue(
        self,
        queue: str,
        summary: str,
        created_at: datetime | str,
        created_by: str | int,
        *,
        key: str | None = None,
        updated_at: datetime | str | None = None,
        updated_by: str | int | None = None,
        resolved_at: datetime | str | None = None,
        resolved_by: str | int | None = None,
        resolution: int | str | None = None,
        status: int | str | None = None,
        type_: int | str | None = None,
        priority: int | str | None = None,
        description: str | None = None,
        assignee: str | int | None = None,
        deadline: date | str | None = None,
        start: date | str | None = None,
        end: date | str | None = None,
        unique: str | None = None,
        _type: type[IssueT_co],
        **kwargs,
    ) -> IssueT_co: ...

    @overload
    async def import_issue(
        self,
        queue: str,
        summary: str,
        created_at: datetime | str,
        created_by: str | int,
        *,
        key: str | None = None,
        updated_at: datetime | str | None = None,
        updated_by: str | int | None = None,
        resolved_at: datetime | str | None = None,
        resolved_by: str | int | None = None,
        resolution: int | str | None = None,
        status: int | str | None = None,
        type_: int | str | None = None,
        priority: int | str | None = None,
        description: str | None = None,
        assignee: str | int | None = None,
        deadline: date | str | None = None,
        start: date | str | None = None,
        end: date | str | None = None,
        unique: str | None = None,
        **kwargs,
    ) -> FullIssue: ...

    async def import_issue(
        self,
        queue: str,
        summary: str,
        created_at: datetime | str,
        created_by: str | int,
        *,
        key: str | None = None,
        updated_at: datetime | str | None = None,
        updated_by: str | int | None = None,
        resolved_at: datetime | str | None = None,
        resolved_by: str | int | None = None,
        resolution: int | str | None = None,
        status: int | str | None = None,
        type_: int | str | None = None,
        priority: int | str | None = None,
        description: str | None = None,
        assignee: str | int | None = None,
        deadline: date | str | None = None,
        start: date | str | None = None,
        end: date | str | None = None,
        unique: str | None = None,
        _type: type[IssueT_co | FullIssue] = FullIssue,
        **kwargs,
    ) -> IssueT_co | FullIssue:
        """Import an issue, preserving its original author and timestamps.

        The request requires organization admin rights.

        :param queue: key of the queue to import the issue into.
        :param summary: issue summary.
        :param created_at: creation moment, a datetime or an API string.
        :param created_by: login or id of the issue author.
        :param key: issue key to assign, e.g. "TEST-1".
        :param updated_at: last update moment. Must be passed together
                            with `updated_by`.
        :param updated_by: login or id of the last editor. Must be passed
                            together with `updated_at`.
        :param resolved_at: resolution moment. Must be passed together with
                            `resolved_by` and `resolution`.
        :param resolved_by: login or id of the user who resolved the issue.
        :param resolution: resolution id.
        :param status: status id.
        :param type_: issue type id (sent as `type`).
        :param priority: priority id.
        :param description: issue description.
        :param assignee: login or id of the assignee.
        :param deadline: deadline date (`YYYY-MM-DD`).
        :param start: start date (`YYYY-MM-DD`).
        :param end: end date (`YYYY-MM-DD`).
        :param unique: unique issue marker used for deduplication.
        :param _type: you can use your own extended FullIssue type.
        :param kwargs: any other issue field, including custom ones, e.g.
                        `affected_versions`, `story_points`, `spent`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/import/import-ticket
        """
        _check_all_or_none(updated_at=updated_at, updated_by=updated_by)
        _check_all_or_none(
            resolved_at=resolved_at,
            resolved_by=resolved_by,
            resolution=resolution,
        )

        created_at = to_tracker_datetime(created_at)
        updated_at = to_tracker_datetime(updated_at)
        resolved_at = to_tracker_datetime(resolved_at)
        deadline = to_tracker_date(deadline)
        start = to_tracker_date(start)
        end = to_tracker_date(end)

        payload = self._prepare_payload(locals(), type_=_type)
        data = await self._client.request(
            method="POST",
            uri="/issues/_import",
            payload=payload,
        )
        return self._decode(_type, data)

    async def import_comment(
        self,
        issue_id: str,
        text: str,
        created_at: datetime | str,
        created_by: str | int,
        *,
        updated_at: datetime | str | None = None,
        updated_by: str | int | None = None,
        **kwargs,
    ) -> Comment:
        """Import a comment, preserving its original author and timestamps.

        The request requires organization admin rights.

        :param issue_id: id or key of the issue to import the comment into.
        :param text: comment text.
        :param created_at: creation moment, a datetime or an API string.
        :param created_by: login or id of the comment author.
        :param updated_at: last update moment. Must be passed together
                            with `updated_by`.
        :param updated_by: login or id of the last editor. Must be passed
                            together with `updated_at`.
        :param kwargs: any other comment field.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/import/import-comments
        """
        _check_all_or_none(updated_at=updated_at, updated_by=updated_by)

        created_at = to_tracker_datetime(created_at)
        updated_at = to_tracker_datetime(updated_at)

        payload = self._prepare_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/comments/_import",
            payload=payload,
        )
        return self._decode(Comment, data)

    async def import_link(
        self,
        issue_id: str,
        relationship: str | LinkRelationship,
        issue: str,
        created_at: datetime | str,
        created_by: str | int,
        *,
        updated_at: datetime | str | None = None,
        updated_by: str | int | None = None,
    ) -> IssueLink:
        """Import a link between two issues with its original metadata.

        The request requires organization admin rights.

        :param issue_id: id or key of the issue to import the link into.
        :param relationship: link type, see :class:`LinkRelationship`.
        :param issue: id or key of the linked issue.
        :param created_at: creation moment, a datetime or an API string.
        :param created_by: login or id of the link author.
        :param updated_at: last update moment. Must be passed together
                            with `updated_by`.
        :param updated_by: login or id of the last editor. Must be passed
                            together with `updated_at`.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/import/import-links
        """
        _check_all_or_none(updated_at=updated_at, updated_by=updated_by)

        created_at = to_tracker_datetime(created_at)
        updated_at = to_tracker_datetime(updated_at)

        payload = self._prepare_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/links/_import",
            payload=payload,
        )
        return self._decode(IssueLink, data)

    async def import_worklog(
        self,
        issue_id: str,
        duration: str,
        created_at: datetime | str,
        created_by: str | int,
        start: datetime | str,
        *,
        comment: str | None = None,
        **kwargs,
    ) -> Worklog:
        """Import a worklog, preserving its original author and timestamps.

        The request requires organization admin rights.

        :param issue_id: id or key of the issue to import the worklog into.
        :param duration: time spent, an ISO 8601 duration such as
                            "PT1H", "P6W" or "P0Y0M30DT2H10M25S".
        :param created_at: creation moment, a datetime or an API string.
                            It must lie between the creation and the last
                            update of the issue.
        :param created_by: login or id of the worklog author.
        :param start: moment the work on the issue started, a datetime
                            or an API string.
        :param comment: comment text saved with the worklog. It shows up
                            in the time-tracking report.
        :param kwargs: any other worklog field.

        Source:
        https://yandex.ru/support/tracker/ru/api/import/import-worklogs
        """
        created_at = to_tracker_datetime(created_at)
        start = to_tracker_datetime(start)

        payload = self._prepare_payload(locals(), exclude=["issue_id"])
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/worklogs/_import",
            payload=payload,
        )
        return self._decode(Worklog, data)

    async def import_attachment(
        self,
        issue_id: str,
        file: BinaryIO,
        filename: str,
        created_at: datetime | str,
        created_by: str | int,
        *,
        comment_id: str | int | None = None,
    ) -> Attachment:
        """Import a file attached to an issue or to one of its comments.

        The request requires organization admin rights.

        :param issue_id: id or key of the issue to import the file into.
        :param file: binary file object to upload.
        :param filename: name to store the file under.
        :param created_at: creation moment, a datetime or an API string.
        :param created_by: login or id of the file author.
        :param comment_id: id of the comment to attach the file to. When
                            omitted, the file is attached to the issue itself.

        Source:
        https://yandex.ru/support/tracker/ru/concepts/import/import-attachments
        """
        form = FormData()
        form.add_field("file_data", file, filename=filename)

        uri = f"/issues/{issue_id}/attachments/_import"
        if comment_id is not None:
            uri = f"/issues/{issue_id}/comments/{comment_id}/attachments/_import"

        data = await self._client.request(
            method="POST",
            uri=uri,
            params={
                "filename": filename,
                "createdAt": to_tracker_datetime(created_at),
                "createdBy": str(created_by),
            },
            form=form,
        )
        return self._decode(Attachment, data)


def _check_all_or_none(**fields: object) -> None:
    """Ensure the given fields are either all set or all omitted.

    The API requires e.g. `updatedAt` and `updatedBy` to come together;
    failing early with a clear message beats a bare HTTP 400.
    """
    values = fields.values()
    if any(v is not None for v in values) and not all(v is not None for v in values):
        names = ", ".join(f"`{name}`" for name in fields)
        msg = f"{names} must be passed together: set all of them or none at all."
        raise ValueError(msg)
