from __future__ import annotations

import logging
from functools import lru_cache
from typing import TYPE_CHECKING, Any, TypeVar

from pydantic import TypeAdapter
from typing_extensions import Self

from yatracker.types.base import Base
from yatracker.types.full_issue import FullIssue
from yatracker.utils.camel_case import camel_case

from .client import AIOHTTPClient

if TYPE_CHECKING:
    from collections.abc import Collection
    from types import TracebackType

    from .client import BaseClient

T = TypeVar("T")
B = TypeVar("B", bound=Base)
IssueT_co = TypeVar("IssueT_co", bound=FullIssue, covariant=True)

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

        return _rename_and_clear(type_, payload, exclude)

    @staticmethod
    def _prepare_params(**kwargs: Any) -> dict[str, str] | None:  # noqa: ANN401
        """Build query params from keyword arguments.

        ``None`` values are dropped, booleans are encoded as ``"true"`` /
        ``"false"`` and everything else is stringified, because aiohttp
        (yarl) rejects ``bool`` and ``None`` query values with a
        ``TypeError``. Keys are camel-cased like payload keys. Returns
        ``None`` when nothing is left, so the result can be passed to
        ``request(params=...)`` directly.
        """
        params = {
            _encode_key(key): _encode_param(value)
            for key, value in kwargs.items()
            if value is not None
        }
        return params or None

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
    """Map model field names to their encoded (wire) names.

    Only ``alias`` is consulted. The ``url`` field binds the API's
    ``self`` key through ``validation_alias``/``serialization_alias``
    (see ``yatracker.types.base.url_field``) while its ``alias`` stays
    ``url``, so a ``url`` kwarg is never renamed to ``self`` here.
    """
    return {
        name: field_info.alias or camel_case(name)
        for name, field_info in type_.model_fields.items()
    }


def _encode_key(key: str) -> str:
    """Convert a kwarg name to its wire (camelCase) name.

    Only Python identifiers are converted (``attachment_ids`` ->
    ``attachmentIds``). Keys that are not identifiers, such as Tracker
    local-field ids (``64a51c6d866ea82411abe756--userId``), are sent
    verbatim: running them through ``camel_case`` would mangle them and
    the API would silently ignore the field.
    """
    return camel_case(key) if key.isidentifier() else key


def _encode_param(value: Any) -> str:  # noqa: ANN401
    """Encode a query param value the way the Tracker API expects it."""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


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
    type_: type[Base] | None,
    payload: dict[str, Any],
    exclude: Collection[str],
) -> dict[str, Any]:
    """Replace kwarg keys with the model's encoded field names.

    Keys that are not fields of `type_` (e.g. `query`, `filter_`,
    custom fields passed via **kwargs), or every key when `type_` is
    None, are kept and converted to camelCase instead of being dropped.
    Keys that are not Python identifiers (local-field ids like
    ``<id>--userId``) are kept as is. Two keys that would land on the
    same wire name raise `ValueError` rather than silently overwriting
    each other.
    """
    renamed: dict[str, Any] = {}
    sources: dict[str, str] = {}
    exclude = {"self", "cls", *exclude}
    encode_names = _field_names(type_) if type_ is not None else {}

    for name, raw_value in payload.items():
        if name in exclude or name.startswith("_"):
            continue

        value = _convert_value(raw_value)
        if value is None:
            continue

        wire_name = encode_names.get(name) or _encode_key(name)
        if wire_name in renamed:
            msg = (
                f"Payload keys {sources[wire_name]!r} and {name!r} both map "
                f"to the API field {wire_name!r}; pass only one of them."
            )
            raise ValueError(msg)

        renamed[wire_name] = value
        sources[wire_name] = name

    return renamed
