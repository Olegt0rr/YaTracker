from __future__ import annotations

from yatracker.tracker.base import BaseTracker
from yatracker.types import Component


class Components(BaseTracker):
    async def get_components(
        self,
        per_page: int | None = None,
        page: int | None = None,
    ) -> list[Component]:
        """Get components.

        Use this request to get a list of all components
        of the organization. Like every list request, the response is
        paginated by 50 objects; use `per_page` and `page` to fetch
        the rest.

        Source:
        https://yandex.cloud/en/docs/tracker/get-components

        :param per_page: number of components per page (50 by default).
        :param page: page number (1 by default).
        :return: list of components.
        """
        params = {}
        if per_page is not None:
            params["perPage"] = str(per_page)
        if page is not None:
            params["page"] = str(page)

        data = await self._client.request(
            method="GET",
            uri="/components",
            params=params or None,
        )
        return self._decode(list[Component], data)

    async def get_queue_components(
        self,
        queue_id: str | int,
    ) -> list[Component]:
        """Get components of a queue.

        Attention: this endpoint is not described in the official API
        reference, but it is what the official `yandex_tracker_client`
        uses to list queue components (`GET /queues/{id}/components`).

        :param queue_id: ID or key of the queue.
        :return: list of components of the queue.
        """
        data = await self._client.request(
            method="GET",
            uri=f"/queues/{queue_id}/components",
        )
        return self._decode(list[Component], data)

    async def create_component(
        self,
        name: str,
        queue: str,
        *,
        description: str | None = None,
        lead: str | None = None,
        assign_auto: bool | None = None,
    ) -> Component:
        """Create a component.

        Source:
        https://yandex.cloud/en/docs/tracker/post-component

        :param name: component name.
        :param queue: key of the queue the component belongs to.
        :param description: component description.
        :param lead: login of the component owner.
        :param assign_auto: automatically assign the component owner
            as the assignee of new issues with this component.
        :return: created component.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/components",
            payload=payload,
        )
        return self._decode(Component, data)

    async def update_component(  # noqa: PLR0913
        self,
        component_id: str | int,
        version: str | int,
        *,
        name: str | None = None,
        description: str | None = None,
        lead: str | None = None,
        assign_auto: bool | None = None,
    ) -> Component:
        """Edit a component.

        Source:
        https://yandex.cloud/en/docs/tracker/patch-component

        :param component_id: ID of the component to edit.
        :param version: current version of the component. The request
            fails with a 409 error if the component was changed
            meanwhile.
        :param name: new component name.
        :param description: new component description.
        :param lead: login of the new component owner.
        :param assign_auto: automatically assign the component owner
            as the assignee of new issues with this component.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated component.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["component_id", "version"],
        )
        data = await self._client.request(
            method="PATCH",
            uri=f"/components/{component_id}",
            params={"version": str(version)},
            payload=payload,
        )
        return self._decode(Component, data)
