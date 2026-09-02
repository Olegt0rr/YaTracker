from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import TypeAdapter
from typing_extensions import Self

from yatracker.types.base import Base
from yatracker.utils.camel_case import camel_case

from .client import AIOHTTPClient

if TYPE_CHECKING:
    from collections.abc import Collection
    from types import TracebackType

    from .client import BaseClient

T = TypeVar("T")
B = TypeVar("B", bound=Base)

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
        *,
        cloud_org_id: str | int | None = None,
        iam_token: str | None = None,
    ) -> None:
        if client is not None:
            self._client = client
            return

        has_org = org_id is not None or cloud_org_id is not None
        has_token = token is not None or iam_token is not None

        if not has_org or not has_token:
            msg = (
                "You must provide either an organization id (`org_id` for "
                "Yandex 360 or `cloud_org_id` for Yandex Cloud) together with "
                "a token (`token` for OAuth or `iam_token` for IAM), or a "
                "`BaseClient` instance with set up headers `X-Org-ID` "
                "(or `X-Cloud-Org-ID`) and `Authorization` and base url."
            )
            raise RuntimeError(msg)

        self._client = AIOHTTPClient(
            org_id=org_id,
            token=token,
            api_host=api_host,
            api_version=api_version,
            cloud_org_id=cloud_org_id,
            iam_token=iam_token,
        )

    def _decode(self, type_: type[T], data: bytes) -> T:
        """Decode bytes object to model.

        Also add producer client object to `_tracker` field.
        """
        adapter = _get_adapter(type_)  # type: ignore[arg-type]
        return adapter.validate_json(data, context={"tracker": self})

    @staticmethod
    def _prepare_payload(
        payload: dict[str, Any],
        exclude: Collection[str] | None = None,
        type_: type[B] | None = None,
    ) -> dict[str, Any]:
        """Remove empty fields from payload."""
        payload = payload.copy()
        exclude = exclude or []

        kwargs: dict | None = payload.pop("kwargs", None)
        if kwargs:
            payload.update(kwargs)

        if type_ is not None:
            return _rename_and_clear(type_, payload, exclude)

        return {
            camel_case(k): _convert_value(v)
            for k, v in payload.items()
            if k not in {"self", "cls", *exclude}
            and not k.startswith("_")
            and v is not None
        }

    async def close(self) -> None:
        """Close gracefully."""
        await self._client.close()

    async def __aenter__(self) -> Self:
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
def _get_adapter(type_: type[T]) -> TypeAdapter[T]:
    """Get cached pydantic type adapter."""
    return TypeAdapter(type_)


@lru_cache
def _field_names(type_: type[Base]) -> dict[str, str]:
    """Map model field names to their encoded (wire) names."""
    return {
        name: field_info.alias or camel_case(name)
        for name, field_info in type_.model_fields.items()
    }


def _convert_value(obj: Any) -> Any:  # noqa: ANN401
    """Convert values to basic types."""
    match obj:
        case Base():
            return obj.model_dump(mode="json", by_alias=True, exclude_none=True)
        case list():
            return [_convert_value(o) for o in obj]
        case dict():
            return {k: _convert_value(v) for k, v in obj.items()}
        case _:
            return obj


def _rename_and_clear(
    type_: type[B],
    payload: dict[str, Any],
    exclude: Collection[str],
) -> dict[str, Any]:
    """Replace kwarg keys with the model's encoded field names.

    Keys that are not fields of `type_` (e.g. `query`, `filter_`,
    custom fields passed via **kwargs) are kept and converted to
    camelCase instead of being dropped.
    """
    renamed: dict[str, Any] = {}
    exclude = {"self", "cls", *exclude}
    encode_names = _field_names(type_)

    for name, raw_value in payload.items():
        if name in exclude or name.startswith("_"):
            continue

        value = _convert_value(raw_value)
        if value is None:
            continue

        renamed[encode_names.get(name) or camel_case(name)] = value

    return renamed
