from __future__ import annotations

from typing import BinaryIO

from aiohttp import FormData

from yatracker.tracker.base import BaseTracker
from yatracker.types import Attachment


class Attachments(BaseTracker):
    async def get_attachments(self, issue_id: str) -> list[Attachment]:
        """Get a list of files attached to an issue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/get-attachments-list
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/attachments",
        )
        return self._decode(list[Attachment], data)

    async def download_attachment(
        self,
        issue_id: str,
        attachment_id: str | int,
        filename: str,
    ) -> bytes:
        """Download file attached to an issue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/get-attachment
        """
        return await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/attachments/{attachment_id}/{filename}",
        )

    async def download_thumbnail(
        self,
        issue_id: str,
        attachment_id: str | int,
    ) -> bytes:
        """Get thumbnails of image files attached to issues.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/get-attachment-preview
        """
        return await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/thumbnails/{attachment_id}",
        )

    async def attach_file(
        self,
        issue_id: str,
        file: BinaryIO,
        filename: str | None = None,
    ) -> Attachment:
        """Attach a file to an issue.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/post-attachment
        """
        form = FormData()
        form.add_field("file_data", file)
        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/attachments",
            params={"filename": filename} if filename else None,
            form=form,
        )
        return self._decode(Attachment, data)

    async def upload_temp_file(
        self,
        file: BinaryIO,
        filename: str | None = None,
    ) -> Attachment:
        """Upload temporary file.

        Use this request to upload a file to Tracker first, and then
        attach it when creating an issue or adding a comment.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/temp-attachment
        """
        form = FormData()
        form.add_field("file_data", file)
        data = await self._client.request(
            method="POST",
            uri="/attachments/",
            params={"filename": filename} if filename else None,
            form=form,
        )
        return self._decode(Attachment, data)

    async def delete_attachment(self, issue_id: str, attachment_id: str | int) -> bool:
        """Delete attached file.

        Source:
        https://cloud.yandex.com/en/docs/tracker/concepts/issues/delete-attachment
        """
        await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/attachments/{attachment_id}/",
        )
        return True
