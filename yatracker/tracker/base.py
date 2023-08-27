from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any, TypeVar

import msgspec.json

from yatracker.types.base import Base
from yatracker.utils.camel_case import camel_case

from .client import AIOHTTPClient

if TYPE_CHECKING:
    from collections.abc import Collection
    from types import TracebackType

    from .client import BaseClient

T = TypeVar("T")

logger = logging.getLogger(__name__)


class BaseTracker:
    """Represents technical methods for using YaTracker."""

    # ruff: noqa: PLR0913
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

    def _decode(self, type_: type[T], data: bytes) -> T:
        """Decode bytes object to struct.

        Also add producer client object to `_tracker` field.
        """
        decoder = _get_decoder(type_)  # type: ignore[arg-type]
        obj = decoder.decode(data)
        _add_tracker(self, obj)
        return obj

    @staticmethod
    def clear_payload(
        payload: dict[str, Any],
        exclude: Collection[str] | None = None,
    ) -> dict[str, Any]:
        """Remove empty fields from payload."""
        payload = payload.copy()
        exclude = exclude or []
        kwargs = payload.pop("kwargs", None)
        if kwargs:
            payload.update(kwargs)

        return {
            camel_case(k): v
            for k, v in payload.items()
            if k not in {"self", "cls", *exclude} and v is not None
        }

    async def close(self) -> None:
        """Close gracefully."""
        await self._client.close()

    # ruff: noqa: PYI034
    async def __aenter__(self) -> BaseTracker:
        """Return async Tracker with async context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        """Close async context."""
        await self.close()


@lru_cache
def _get_decoder(type_: type[T]) -> msgspec.json.Decoder:
    """Get cached msgspec encoder."""
    return msgspec.json.Decoder(type_)


def _add_tracker(tracker: BaseTracker, obj: Any) -> None:  # noqa: ANN401
    """Add tracker link to the object."""
    match obj:
        case Base():
            obj._tracker = tracker  # noqa: SLF001
        case list():
            for o in obj:
                _add_tracker(tracker, o)
        case dict():
            for v in obj.values():
                _add_tracker(tracker, v)
