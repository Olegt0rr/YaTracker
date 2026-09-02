from __future__ import annotations

from yatracker.tracker.base import BaseTracker
from yatracker.types import RemoteLink


class ExternalLinks(BaseTracker):
    async def get_remote_links(self, issue_id: str) -> list[RemoteLink]:
        """Get links to objects of external applications.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/get-external-links

        :param issue_id: ID or key of the issue.
        :return: list of remote links of the issue.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/issues/{issue_id}/remotelinks",
        )
        return self._decode(list[RemoteLink], data)

    async def add_remote_link(
        self,
        issue_id: str,
        key: str,
        origin: str,
        relationship: str = "RELATES",
        *,
        backlink: bool | None = None,
    ) -> RemoteLink:
        """Link an issue with an object of an external application.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/add-external-link

        :param issue_id: ID or key of the issue.
        :param key: key of the object in the external application.
        :param origin: ID of the external application. Use
            `get_applications` to list the available ones.
        :param relationship: type of the link. The API docs document
            only the uppercase "RELATES" for this endpoint. Do not pass
            `LinkRelationship` here: its lowercase values belong to the
            issue-link and import APIs.
        :param backlink: ask the external application to create
            a mirrored link on its side.
        :return: created remote link.
        """
        payload = self._prepare_payload(locals(), exclude=["issue_id", "backlink"])
        params = self._prepare_params(backlink=backlink)

        data = await self._client.request(
            method="POST",
            uri=f"/issues/{issue_id}/remotelinks",
            params=params,
            payload=payload,
        )
        return self._decode(RemoteLink, data)

    async def delete_remote_link(self, issue_id: str, link_id: str | int) -> bool:
        """Delete a link between an issue and an external application object.

        Source:
        https://yandex.ru/support/tracker/ru/api/issues/delete-external-link

        :param issue_id: ID or key of the issue.
        :param link_id: ID of the remote link.
        :return: True if the link was deleted.
        """
        await self._client.request(
            method="DELETE",
            uri=f"/issues/{issue_id}/remotelinks/{link_id}",
        )
        return True
