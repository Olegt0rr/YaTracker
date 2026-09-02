from __future__ import annotations

from typing import TYPE_CHECKING

from yatracker.tracker.base import BaseTracker
from yatracker.types.resolution import FullResolution

if TYPE_CHECKING:
    from yatracker.types.localized_name import LocalizedName


class Resolutions(BaseTracker):
    async def get_resolutions(self) -> list[FullResolution]:
        """Get resolutions.

        Use this request to get a list of the resolutions.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/get-resolutions

        :return: list of resolutions.
        """
        data = await self._client.request(
            method="GET",
            uri="/resolutions",
        )
        return self._decode(list[FullResolution], data)

    async def create_resolution(
        self,
        key: str,
        name: LocalizedName | dict[str, str],
    ) -> FullResolution:
        """Create a resolution.

        Admin rights are required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/create-resolution

        :param key: key of the resolution. Latin letters only, must
            start with a lowercase one.
        :param name: name of the resolution in every language, e.g.
            `LocalizedName(ru="Моя резолюция", en="My resolution")` or
            `{"ru": "Моя резолюция", "en": "My resolution"}`.
        :return: created resolution.
        """
        payload = self._prepare_payload(locals())
        data = await self._client.request(
            method="POST",
            uri="/resolutions",
            payload=payload,
        )
        return self._decode(FullResolution, data)

    async def update_resolution(
        self,
        resolution_id: str | int,
        *,
        version: str | int | None = None,
        name: LocalizedName | dict[str, str] | None = None,
        description: str | None = None,
        order: int | None = None,
    ) -> FullResolution:
        """Edit a resolution.

        Admin rights are required.

        Source:
        https://yandex.ru/support/tracker/ru/api/admin/patch-resolution

        :param resolution_id: ID or key of the resolution to edit.
        :param version: current version of the resolution, sent as the
            `version` query parameter: the changes are applied only to
            that version. The API answers 409 when the version is stale
            (:class:`AlreadyExistsError`) and 423 when the maximum
            version number is exceeded.
        :param name: new name of the resolution in every language, e.g.
            `LocalizedName(ru="Не будет исправлено", en="Won't be fixed")`.
        :param description: new description of the resolution.
        :param order: new weight of the resolution; it affects the order
            the resolutions are displayed in the interface.

        Fields left as ``None`` are not sent, i.e. they stay unchanged.

        :return: updated resolution.
        """
        payload = self._prepare_payload(
            locals(),
            exclude=["resolution_id", "version"],
        )
        params = self._prepare_params(version=version)
        data = await self._client.request(
            method="PATCH",
            uri=f"/resolutions/{resolution_id}",
            params=params,
            payload=payload,
        )
        return self._decode(FullResolution, data)
