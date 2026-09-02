"""Base aiohttp client class module."""

from __future__ import annotations

import asyncio
import logging
import ssl
from abc import ABC, abstractmethod
from functools import lru_cache
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

import certifi
from aiohttp import BytesPayload, ClientSession, ClientTimeout, FormData, TCPConnector
from pydantic_core import to_json

from yatracker.exceptions import (
    AlreadyExistsError,
    NotAuthorizedError,
    ObjectNotFoundError,
    PreconditionFailedError,
    PreconditionRequiredError,
    SufficientRightsError,
    YaTrackerError,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from aiohttp.typedefs import StrOrURL

DEFAULT_API_HOST = "https://api.tracker.yandex.net"
DEFAULT_API_VERSION = "v3"

ORG_ID_HEADER = "X-Org-ID"
CLOUD_ORG_ID_HEADER = "X-Cloud-Org-ID"
AUTH_HEADER = "Authorization"

logger = logging.getLogger(__name__)


@lru_cache
def _get_ssl_context() -> ssl.SSLContext:
    """Build the default SSL context once per process.

    Parsing the certifi CA bundle takes a few milliseconds of blocking
    work, so the result is cached instead of being rebuilt inside the
    event loop on every session (re)creation.
    """
    return ssl.create_default_context(cafile=certifi.where())


def _has_header(headers: dict[str, str], name: str) -> bool:
    """Check header presence, ignoring case (HTTP headers are case-insensitive)."""
    lowered = name.lower()
    return any(key.lower() == lowered for key in headers)


def _set_org_header(
    headers: dict[str, str],
    org_id: str | int | None,
    cloud_org_id: str | int | None,
) -> None:
    """Set the organization header in place.

    Exactly one of `X-Org-ID` (Yandex 360 organization) and
    `X-Cloud-Org-ID` (Yandex Cloud organization) may be sent.
    """
    if org_id is not None and cloud_org_id is not None:
        msg = (
            "Provide either `org_id` (Yandex 360 organization) or `cloud_org_id` "
            "(Yandex Cloud organization), not both: the API forbids sending "
            "`X-Org-ID` and `X-Cloud-Org-ID` at the same time."
        )
        raise ValueError(msg)

    has_org_header = _has_header(headers, ORG_ID_HEADER)
    has_cloud_org_header = _has_header(headers, CLOUD_ORG_ID_HEADER)
    if has_org_header and has_cloud_org_header:
        msg = (
            "`headers` contains both `X-Org-ID` and `X-Cloud-Org-ID`: "
            "the API forbids sending them at the same time."
        )
        raise ValueError(msg)

    if has_org_header or has_cloud_org_header:
        return

    if org_id is not None:
        headers[ORG_ID_HEADER] = str(org_id)
        return

    if cloud_org_id is not None:
        headers[CLOUD_ORG_ID_HEADER] = str(cloud_org_id)
        return

    msg = (
        "You must provide `org_id` (Yandex 360 organization) or `cloud_org_id` "
        "(Yandex Cloud organization), or pass the `X-Org-ID` / `X-Cloud-Org-ID` "
        "header via `headers`."
    )
    raise ValueError(msg)


def _set_auth_header(
    headers: dict[str, str],
    token: str | None,
    iam_token: str | None,
) -> None:
    """Set the `Authorization` header in place."""
    if token is not None and iam_token is not None:
        msg = "Provide either `token` (OAuth) or `iam_token` (IAM), not both."
        raise ValueError(msg)

    if _has_header(headers, AUTH_HEADER):
        return

    if token is not None:
        headers[AUTH_HEADER] = f"OAuth {token}"
        return

    if iam_token is not None:
        headers[AUTH_HEADER] = f"Bearer {iam_token}"
        return

    msg = (
        "You must provide `token` (OAuth) or `iam_token` (IAM), "
        "or pass the `Authorization` header via `headers`."
    )
    raise ValueError(msg)


class BaseClient(ABC):
    """Represents abstract base class for tracker client."""

    # ruff: noqa: PLR0913
    def __init__(
        self,
        org_id: str | int | None = None,
        token: str | None = None,
        headers: dict[str, str] | None = None,
        api_host: str | None = None,
        api_version: str | None = None,
        *,
        cloud_org_id: str | int | None = None,
        iam_token: str | None = None,
        # ruff: noqa: ARG002
        **kwargs,
    ) -> None:
        """Set defaults on object init.

        By default, `self._session` is None.
        It will be created on a first API request.
        The second request will use the same `self._session`.

        :param org_id: Yandex 360 organization id (sent as `X-Org-ID`).
        :param cloud_org_id: Yandex Cloud organization id
            (sent as `X-Cloud-Org-ID`). Mutually exclusive with `org_id`.
        :param token: OAuth token (sent as `Authorization: OAuth ...`).
        :param iam_token: IAM token (sent as `Authorization: Bearer ...`).
            Mutually exclusive with `token`.
        """
        self._api_version = api_version or DEFAULT_API_VERSION
        self._base_url = api_host or DEFAULT_API_HOST
        _headers = headers.copy() if headers else {}
        _set_org_header(_headers, org_id, cloud_org_id)
        _set_auth_header(_headers, token, iam_token)
        self._headers: dict[str, str] = _headers
        self._session: ClientSession | None = None

    async def request(
        self,
        method: str,
        uri: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        form: FormData | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> bytes:
        """Make request and return the response body.

        :param headers: extra request headers (e.g. `If-Match`), merged
            with the default ones by the transport.
        """
        body, _ = await self.request_with_headers(
            method=method,
            uri=uri,
            params=params,
            payload=payload,
            form=form,
            headers=headers,
            **kwargs,
        )
        return body

    async def request_with_headers(
        self,
        method: str,
        uri: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | list[Any] | None = None,
        form: FormData | None = None,
        headers: dict[str, str] | None = None,
        **kwargs,
    ) -> tuple[bytes, Mapping[str, str]]:
        """Make request and return both the response body and its headers.

        Some endpoints only expose their pagination state via response
        headers (e.g. `X-Scroll-Id`, `X-Total-Pages`, `X-Total-Count`),
        which are unreachable through :meth:`request`.

        :param headers: extra request headers (e.g. `If-Match`). They are
            forwarded to :meth:`_make_request` as the `headers` kwarg
            only when given, so transports must merge them with the
            default headers.
        """
        bytes_payload: FormData | BytesPayload | None
        if form is not None:
            bytes_payload = form
        elif payload is not None:
            bytes_payload = BytesPayload(
                value=to_json(payload),
                content_type="application/json",
            )
        else:
            bytes_payload = None

        # to support full links (e.g. Transition)
        if not uri.startswith("http"):
            uri = f"{self._base_url}/{self._api_version}{uri}"

        if headers is not None:
            kwargs["headers"] = headers

        status, body, response_headers = await self._make_request(
            method=method,
            url=uri,
            params=params,
            data=bytes_payload,
            **kwargs,
        )
        self._check_status(status, body)
        return body, response_headers

    @abstractmethod
    async def _make_request(
        self,
        method: str,
        url: StrOrURL,
        **kwargs,
    ) -> tuple[int, bytes, Mapping[str, str]]:
        """Get the raw response from the HTTP client.

        Custom transports must forward every kwarg to the underlying
        HTTP call: `params`, `data` (an aiohttp payload or `FormData`)
        and, when present, `headers` — per-request headers such as
        `If-Match`, which have to be merged with the default ones.
        Dropping `headers` silently disables optimistic locking.

        :returns: tuple of (status_code, response_body, response_headers).
        """

    @staticmethod
    def _check_status(status: int, body: bytes) -> None:
        if status < HTTPStatus.MULTIPLE_CHOICES:
            return

        if status == HTTPStatus.UNAUTHORIZED:
            raise NotAuthorizedError

        if status == HTTPStatus.FORBIDDEN:
            raise SufficientRightsError

        if status == HTTPStatus.NOT_FOUND:
            raise ObjectNotFoundError

        if status == HTTPStatus.CONFLICT:
            raise AlreadyExistsError

        if status == HTTPStatus.PRECONDITION_FAILED:
            raise PreconditionFailedError

        if status == HTTPStatus.PRECONDITION_REQUIRED:
            raise PreconditionRequiredError

        raise YaTrackerError(body.decode("utf-8", errors="replace"))

    @abstractmethod
    async def close(self) -> None:
        """Close the session gracefully."""


class AIOHTTPClient(BaseClient):
    """Base aiohttp client.

    Consists of all methods need to make a request to API:
     - session caching
     - request wrapping
     - exceptions wrapping
     - grace session close
     - e.t.c.
    """

    # ruff: noqa: PLR0913
    def __init__(
        self,
        org_id: str | int | None = None,
        token: str | None = None,
        headers: dict[str, str] | None = None,
        api_host: str | None = None,
        api_version: str | None = None,
        *,
        cloud_org_id: str | int | None = None,
        iam_token: str | None = None,
        **kwargs,
    ) -> None:
        """Set defaults on object init.

        By default, `self._session` is None.
        It will be created on a first API request.
        The second request will use the same `self._session`.
        """
        super().__init__(
            org_id=org_id,
            token=token,
            headers=headers,
            api_host=api_host,
            api_version=api_version,
            cloud_org_id=cloud_org_id,
            iam_token=iam_token,
            **kwargs,
        )
        self._timeout: ClientTimeout = kwargs.get("timeout") or ClientTimeout(total=0)

    def get_session(self) -> ClientSession:
        """Get cached session. One session per instance."""
        if isinstance(self._session, ClientSession) and not self._session.closed:
            return self._session

        connector = TCPConnector(ssl=_get_ssl_context())

        self._session = ClientSession(
            connector=connector,
            headers=self._headers,
            json_serialize=lambda obj: to_json(obj).decode(),
            timeout=self._timeout,
        )
        return self._session

    async def _make_request(
        self,
        method: str,
        url: StrOrURL,
        **kwargs,
    ) -> tuple[int, bytes, Mapping[str, str]]:
        """Make a request.

        :param method: HTTP Method
        :param url: endpoint link
        :param kwargs: data, params, json and other...
        :return: status, result and response headers, or exception
        """
        session = self.get_session()

        async with session.request(method, url, **kwargs) as response:
            status = response.status
            body = await response.read()
            headers = response.headers

        if status >= HTTPStatus.BAD_REQUEST:
            logger.warning(
                "Error! Status: %s. Body: %s",
                status,
                body.decode("utf-8", errors="replace"),
            )

        return status, body, headers

    async def close(self) -> None:
        """Close the session gracefully."""
        if not isinstance(self._session, ClientSession):
            return

        if self._session.closed:
            return

        await self._session.close()
        await asyncio.sleep(0.25)
