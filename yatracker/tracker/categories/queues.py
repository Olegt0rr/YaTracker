from __future__ import annotations

from typing import TypeVar, overload

from yatracker.tracker.base import BaseTracker
from yatracker.types import (
    FullQueue,
    IssueTypeConfig,
    QueueField,
    QueueVersion,
)

QueueT_co = TypeVar("QueueT_co", bound=FullQueue, covariant=True)
QueueFieldT_co = TypeVar("QueueFieldT_co", bound=QueueField, covariant=True)
QueueVersionT_co = TypeVar("QueueVersionT_co", bound=QueueVersion, covariant=True)


class Queues(BaseTracker):
    @overload
    async def get_queue(
        self,
        queue_id: str | int,
    ) -> FullQueue:
        ...

    @overload
    async def get_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co] = ...,
    ) -> QueueT_co:
        ...

    async def get_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co | FullQueue] = FullQueue,
    ) -> QueueT_co | FullQueue:
        """Get queue parameters.

        Use this request to get information about a queue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/get-queue

        :param queue_id: ID or key of the current queue.
        :param _type: you can use your own extended FullQueue type
        :return:
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}",
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
    ) -> FullQueue:
        ...

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
    ) -> QueueT_co:
        ...

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
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/create-queue
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
    ) -> list[FullQueue]:
        ...

    @overload
    async def get_queues(
        self,
        expand: str | None = None,
        per_page: int | None = None,
        _type: type[QueueT_co] = ...,
    ) -> list[QueueT_co]:
        ...

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
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/get-queues
        """
        params = {}
        if expand is not None:
            params["expand"] = expand
        if per_page is not None:
            params["perPage"] = str(per_page)

        payload = self._prepare_payload(
            locals(),
            exclude=["expand", "perPage"],
            type_=_type,
        )
        data = await self._client.request(
            method="GET",
            uri="/queues",
            params=params,
            payload=payload,
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]

    async def delete_queue(
        self,
        queue_id: str | int,
    ) -> bool:
        """Delete queue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/delete-queue
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
    ) -> FullQueue:
        ...

    @overload
    async def restore_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co] = ...,
    ) -> QueueT_co:
        ...

    async def restore_queue(
        self,
        queue_id: str | int,
        _type: type[QueueT_co | FullQueue] = FullQueue,
    ) -> QueueT_co | FullQueue:
        """Restore queue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/restore-queue
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/_restore",
        )
        return self._decode(_type, data)

    async def delete_tag_from_queue(
        self,
        queue_id: str | int,
        tag_name: str,
    ) -> bool:
        """Remove a tag from a queue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/delete-tag
        """
        await self._client.request(
            method="DELETE",
            uri=f"/queues/{queue_id}/tags/_remove",
            payload={"tag": tag_name},
        )
        return True

    @overload
    async def get_queue_fields(
        self,
        queue_id: str | int,
    ) -> list[QueueField]:
        ...

    @overload
    async def get_queue_fields(
        self,
        queue_id: str | int,
        _type: type[QueueFieldT_co] = ...,
    ) -> list[QueueFieldT_co]:
        ...

    async def get_queue_fields(
        self,
        queue_id: str | int,
        _type: type[QueueField | QueueFieldT_co] = QueueField,
    ) -> list[QueueField] | list[QueueFieldT_co]:
        """Get required fields for the queue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/get-fields
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
    ) -> list[QueueVersion]:
        ...

    @overload
    async def get_queue_versions(
        self,
        queue_id: str | int,
        _type: type[QueueVersionT_co] = ...,
    ) -> list[QueueVersionT_co]:
        ...

    async def get_queue_versions(
        self,
        queue_id: str | int,
        _type: type[QueueVersion | QueueVersionT_co] = QueueVersion,
    ) -> list[QueueVersion] | list[QueueVersionT_co]:
        """Get queue versions.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/queues/get-versions
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/versions",
        )
        return self._decode(list[_type], data)  # type: ignore[valid-type]
