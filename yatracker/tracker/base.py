from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any

import msgspec.json

from yatracker.utils.mixins import ContextInstanceMixin

from .client import AIOHTTPClient

if TYPE_CHECKING:
    from collections.abc import Collection

    from .client import BaseClient

logger = logging.getLogger(__name__)


class BaseTracker(ContextInstanceMixin):
    """Represents technical methods for using YaTracker."""

    def __init__(
        self,
        org_id: str | int | None = None,
        token: str | None = None,
        client: BaseClient | None = None,
        api_host: str | None = None,
        api_version: str | None = None,
    ) -> None:
        if (org_id is None or token is None) and client is None:
            msg = (
                "You must provide either `org_id` and `token` or `BaseClient` "
                "instance with set up headers `X-Org-Id` and `Authorization` and "
                "base url."
            )
            raise RuntimeError(msg)

        if client is not None:
            self._client = client
        else:
            if token is None or org_id is None:
                msg = "You must provide `org_id` and `token`."
                raise RuntimeError(msg)

            self._client = AIOHTTPClient(
                org_id=org_id,
                token=token,
                api_host=api_host,
                api_version=api_version,
            )

    @lru_cache
    def _get_decoder(self, struct: type[msgspec.Struct]) -> msgspec.json.Decoder:
        """Get cached msgspec encoder."""
        return msgspec.json.Decoder(struct)

    @staticmethod
    def clear_payload(
        payload: dict[str, Any],
        exclude: Collection[str] | None = None,
    ):
        """Remove empty fields from payload."""
        payload = payload.copy()
        exclude = exclude or []
        kwargs = payload.pop("kwargs", None)
        if kwargs:
            payload.update(kwargs)

        return {
            k: v
            for k, v in payload.items()
            if k not in {"self", "cls", *exclude} and v is not None
        }

    async def close(self):
        """Close gracefully."""
        await self._client.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()
