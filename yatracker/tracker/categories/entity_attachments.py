from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
from yatracker.types.attachment import Attachment
from yatracker.types.entity import Entity, EntityType

from .entities import _entity_uri

if TYPE_CHECKING:
    from collections.abc import Sequence


class EntityAttachments(BaseTracker):
    """Files attached to projects, portfolios and goals (`/entities`).

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/attachments/get-all-attachments
    """

    async def get_entity_attachments(
        self,
        entity_type: EntityType,
        entity_id: str | int,
    ) -> list[Attachment]:
        """Get the list of files attached to an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :return: List of the attached files.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/attachments/get-all-attachments
        """
        data = await self._client.request(
            method="GET",
            uri=_entity_uri(entity_type, str(entity_id), "attachments"),
        )
        return self._decode(list[Attachment], data)

    async def get_entity_attachment(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        attachment_id: str | int,
    ) -> Attachment:
        """Get the information about a file attached to an entity.

        This endpoint returns the metadata of the file, not its content:
        download the file itself from `Attachment.content`.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param attachment_id: Id of the file.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/attachments/get-attachment
        """
        data = await self._client.request(
            method="GET",
            uri=_entity_uri(
                entity_type, str(entity_id), "attachments", str(attachment_id)
            ),
        )
        return self._decode(Attachment, data)

    async def attach_file_to_entity(  # noqa: PLR0913
        self,
        entity_type: EntityType,
        entity_id: str | int,
        file_id: str | int,
        *,
        notify: bool | None = None,
        notify_author: bool | None = None,
        fields: str | Sequence[str] | None = None,
        expand: str | None = None,
    ) -> Entity:
        """Attach an already uploaded temporary file to an entity.

        Unlike `attach_file` for issues, this endpoint does not upload
        anything: send the file to Tracker with `upload_temp_file()`
        first and pass the id of the temporary file it returns.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id of the entity.
        :param file_id: Id of the temporary file to attach.
        :param notify: Whether to notify the users mentioned in the
            entity fields (`True` by default).
        :param notify_author: Whether to notify the author of the change
            (`False` by default).
        :param fields: Additional entity fields to return in the
            response (a comma-separated string or a sequence of names).
        :param expand: Additional information to include: "all" or
            "attachments".
        :return: The entity the file was attached to.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/attachments/add-attachment
        """
        data = await self._client.request(
            method="POST",
            uri=_entity_uri(entity_type, str(entity_id), "attachments", str(file_id)),
            params=self._prepare_params(
                notify=notify,
                notify_author=notify_author,
                fields=_fields_param(fields),
                expand=expand,
            ),
        )
        return self._decode(Entity, data)

    async def delete_entity_attachment(
        self,
        entity_type: EntityType,
        entity_id: str | int,
        attachment_id: str | int,
    ) -> bool:
        """Delete a file attached to an entity.

        :param entity_type: "project", "portfolio" or "goal".
        :param entity_id: Id (or short id) of the entity.
        :param attachment_id: Id of the file.
        :return: `True` if the file was deleted.

        Source:
        https://yandex.ru/support/tracker/ru/api/entities/attachments/delete-attachment
        """
        await self._client.request(
            method="DELETE",
            uri=_entity_uri(
                entity_type, str(entity_id), "attachments", str(attachment_id)
            ),
        )
        return True


def _fields_param(fields: str | Sequence[str] | None) -> str | None:
    """Render the `fields` query param, which the API takes comma-separated."""
    if fields is None or isinstance(fields, str):
        return fields
    return ",".join(fields)
