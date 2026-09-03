from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, overload

from yatracker.tracker.base import BaseTracker, QueueT_co
from yatracker.types import (
    FullQueue,
    IssueTypeConfig,
    QueueField,
    QueueVersion,
)
from yatracker.utils.datetime import to_tracker_date

if TYPE_CHECKING:
    from datetime import date

QueueFieldT_co = TypeVar("QueueFieldT_co", bound=QueueField, covariant=True)
QueueVersionT_co = TypeVar("QueueVersionT_co", bound=QueueVersion, covariant=True)


class Queues(BaseTracker):
    @overload
    async def get_queue(
        self,
        queue_id: str | int,
        *,
        expand: str | None = ...,
    ) -> FullQueue: ...

    @overload
    async def get_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co] = ...,
        *,
        expand: str | None = ...,
    ) -> QueueT_co: ...

    async def get_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co | FullQueue] = FullQueue,
        *,
        expand: str | None = None,
    ) -> QueueT_co | FullQueue:
        """Get queue parameters.

        Use this request to get information about a queue.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/get-queue

        :param queue_id: ID or key of the current queue.
        :param _type: you can use your own extended FullQueue type
        :param expand: additional fields to include into the response.
            One of `all`, `projects`, `components`, `versions`, `types`,
            `team`, `workflows`, `fields`, `issueTypesConfig`.
        :return:
        """
        params = {}
        if expand is not None:
            params["expand"] = expand

        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}",
            params=params or None,
        )
        return self._decode(_type, data)

    # ruff: noqa: PLR0913
    @overload
    async def create_queue(
        self,
        key: str,
        name: str,
        lead: str,
        default_type: str,
        default_priority: str,
        issue_types_config: list[IssueTypeConfig],
    ) -> FullQueue: ...

    # ruff: noqa: PLR0913
    @overload
    async def create_queue(
        self,
        key: str,
        name: str,
        lead: str,
        default_type: str,
        default_priority: str,
        issue_types_config: list[IssueTypeConfig],
        _type: type[QueueT_co] = ...,
    ) -> QueueT_co: ...

    # ruff: noqa: PLR0913
    async def create_queue(
        self,
        key: str,
        name: str,
        lead: str,
        default_type: str,
        default_priority: str,
        issue_types_config: list[IssueTypeConfig],
        _type: type[QueueT_co | FullQueue] = FullQueue,
    ) -> QueueT_co | FullQueue:
        """Create a queue.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/create-queue
        """
        payload = self._prepare_payload(locals(), type_=_type)
        data = await self._client.request(
            method="POST",
            uri="/queues",
            payload=payload,
        )
        return self._decode(_type, data)

    @overload
    async def get_queues(
        self,
        expand: str | None = None,
        per_page: int | None = None,
    ) -> list[FullQueue]: ...

    @overload
    async def get_queues(
        self,
        expand: str | None = None,
        per_page: int | None = None,
        _type: type[QueueT_co] = ...,
    ) -> list[QueueT_co]: ...

    async def get_queues(
        self,
        expand: str | None = None,
        per_page: int | None = None,
        _type: type[FullQueue | QueueT_co] = FullQueue,
    ) -> list[FullQueue] | list[QueueT_co]:
        """Get queues.

        Use this request to get a list of available queues.
        If there are more than 50 queues in the response, use pagination.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/get-queues
        """
        params = {}
        if expand is not None:
            params["expand"] = expand
        if per_page is not None:
            params["perPage"] = str(per_page)

        data = await self._client.request(
            method="GET",
            uri="/queues",
            params=params or None,
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    async def delete_queue(
        self,
        queue_id: str | int,
    ) -> bool:
        """Delete queue.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/delete-queue
        """
        await self._client.request(
            method="DELETE",
            uri=f"/queues/{queue_id}",
        )
        return True

    @overload
    async def restore_queue(
        self,
        queue_id: str | int,
    ) -> FullQueue: ...

    @overload
    async def restore_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co] = ...,
    ) -> QueueT_co: ...

    async def restore_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co | FullQueue] = FullQueue,
    ) -> QueueT_co | FullQueue:
        """Restore queue.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/restore-queue
        """
        data = await self._client.request(
            method="POST",
            uri=f"/queues/{queue_id}/_restore",
        )
        return self._decode(_type, data)

    async def get_queue_tags(
        self,
        queue_id: str | int,
    ) -> list[str]:
        """Get the tags of a queue.

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/get-tags

        :param queue_id: ID or key of the queue (the key is
            case-sensitive).
        :return: names of the tags added to the queue.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/tags",
        )
        return self._decode(list[str], data)

    async def delete_tag_from_queue(
        self,
        queue_id: str | int,
        tag_name: str,
    ) -> bool:
        """Remove a tag from a queue.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/delete-tag
        """
        await self._client.request(
            method="POST",
            uri=f"/queues/{queue_id}/tags/_remove",
            payload={"tag": tag_name},
        )
        return True

    @overload
    async def get_queue_fields(
        self,
        queue_id: str | int,
    ) -> list[QueueField]: ...

    @overload
    async def get_queue_fields(
        self,
        queue_id: str | int,
        _type: type[QueueFieldT_co] = ...,
    ) -> list[QueueFieldT_co]: ...

    async def get_queue_fields(
        self,
        queue_id: str | int,
        _type: type[QueueField | QueueFieldT_co] = QueueField,
    ) -> list[QueueField] | list[QueueFieldT_co]:
        """Get required fields for the queue.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/get-fields
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/fields",
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    @overload
    async def get_queue_versions(
        self,
        queue_id: str | int,
    ) -> list[QueueVersion]: ...

    @overload
    async def get_queue_versions(
        self,
        queue_id: str | int,
        _type: type[QueueVersionT_co] = ...,
    ) -> list[QueueVersionT_co]: ...

    async def get_queue_versions(
        self,
        queue_id: str | int,
        _type: type[QueueVersion | QueueVersionT_co] = QueueVersion,
    ) -> list[QueueVersion] | list[QueueVersionT_co]:
        """Get queue versions.

        Source:
        https://yandex.cloud/en/docs/tracker/concepts/queues/get-versions
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/versions",
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    @overload
    async def create_queue_version(
        self,
        queue_id: str | int,
        name: str,
        *,
        description: str | None = ...,
        start_date: date | str | None = ...,
        due_date: date | str | None = ...,
    ) -> QueueVersion: ...

    @overload
    async def create_queue_version(
        self,
        queue_id: str | int,
        name: str,
        _type: type[QueueVersionT_co] = ...,
        *,
        description: str | None = ...,
        start_date: date | str | None = ...,
        due_date: date | str | None = ...,
    ) -> QueueVersionT_co: ...

    async def create_queue_version(
        self,
        queue_id: str | int,
        name: str,
        _type: type[QueueVersion | QueueVersionT_co] = QueueVersion,
        *,
        description: str | None = None,
        start_date: date | str | None = None,
        due_date: date | str | None = None,
    ) -> QueueVersion | QueueVersionT_co:
        """Create a queue version.

        The version is created by `POST /versions`, with the queue
        passed in the request body; the queue is not part of the path
        (unlike `get_queue_versions`).

        Source:
        https://yandex.ru/support/tracker/ru/api/queues/create-version

        :param queue_id: key of the queue the version is created in.
        :param name: name of the version.
        :param _type: you can use your own extended QueueVersion type.
        :param description: description of the version.
        :param start_date: start date, `YYYY-MM-DD` or a `date` object.
        :param due_date: due date, `YYYY-MM-DD` or a `date` object.
        :raises ValueError: if the API answered with an empty array.
        :return: created version.

        The reference shows the created version wrapped into an array,
        while every other single-object endpoint answers with a bare
        object; both shapes are accepted.
        """
        start_date = to_tracker_date(start_date)
        due_date = to_tracker_date(due_date)

        payload = self._prepare_payload(
            locals(),
            exclude=["queue_id"],
            type_=_type,
        )
        payload = {"queue": queue_id, **payload}

        data = await self._client.request(
            method="POST",
            uri="/versions",
            payload=payload,
        )
        return self._decode_single(_type, data)
