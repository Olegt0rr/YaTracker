"""Base aiohttp client class module."""

from __future__ import annotations

import asyncio
import io
import logging
import ssl
from abc import ABC, abstractmethod
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any, BinaryIO

import certifi
import msgspec
from aiohttp import BytesPayload, ClientSession, ClientTimeout, FormData, TCPConnector

from yatracker.exceptions import (
    AlreadyExistsError,
    NotAuthorizedError,
    ObjectNotFoundError,
    SufficientRightsError,
    YaTrackerError,
)

if TYPE_CHECKING:
    from aiohttp.typedefs import StrOrURL

DEFAULT_API_HOST = "https://api.tracker.yandex.net"
DEFAULT_API_VERSION = "v2"

logger = logging.getLogger(__name__)


class BaseClient(ABC):
    """Represents abstract base class for tracker client."""

    # ruff: noqa: PLR0913
    def __init__(
        self,
        org_id: str | int,
        token: str,
        headers: dict[str, str] | None = None,
        api_host: str | None = None,
        api_version: str | None = None,
        # ruff: noqa: ARG002
        **kwargs,
    ) -> None:
        """Set defaults on object init.

        By default, `self._session` is None.
        It will be created on a first API request.
        The second request will use the same `self._session`.
        """
        self._api_version = api_version or DEFAULT_API_VERSION
        self._base_url = api_host or DEFAULT_API_HOST
        _headers = headers.copy() if headers else {}
        _headers.setdefault("X-Org-Id", str(org_id))
        _headers.setdefault("Authorization", f"OAuth {token}")
        self._headers: dict[str, str] = _headers
        self._session: ClientSession | None = None
        self._encoder = msgspec.json.Encoder()

    async def request(
        self,
        method: str,
        uri: str,
        params: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
        form: FormData | None = None,
        **kwargs,
    ) -> bytes:
        """Make request."""
        bytes_payload: FormData | BytesPayload
        if form:
            bytes_payload = form
        else:
            bytes_payload = BytesPayload(
                value=self._encoder.encode(payload),
                content_type="application/json",
            )

        # to support full links (e.g. Transition)
        if not uri.startswith("http"):
            uri = f"{self._base_url}/{self._api_version}{uri}"

        status, body = await self._make_request(
            method=method,
            url=uri,
            params=params,
            data=bytes_payload,
            **kwargs,
        )
        self._check_status(status, body)
        return body

    @abstractmethod
    async def _make_request(
        self,
        method: str,
        url: StrOrURL,
        **kwargs,
    ) -> tuple[int, bytes]:
        """Get raw response from via http-client.

        :returns: tuple of (status_code, response_body).
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

        raise YaTrackerError(body)

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
        org_id: str | int,
        token: str,
        headers: dict[str, str] | None = None,
        api_host: str | None = None,
        api_version: str | None = None,
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
            **kwargs,
        )
        self._timeout: ClientTimeout = kwargs.get("timeout") or ClientTimeout(total=0)

    def get_session(self) -> ClientSession:
        """Get cached session. One session per instance."""
        if isinstance(self._session, ClientSession) and not self._session.closed:
            return self._session

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)

        encoder = msgspec.json.Encoder()
        self._session = ClientSession(
            connector=connector,
            headers=self._headers,
            json_serialize=lambda obj: encoder.encode(obj).decode(),
            timeout=self._timeout,
        )
        return self._session

    async def _make_request(
        self,
        method: str,
        url: StrOrURL,
        **kwargs,
    ) -> tuple[int, bytes]:
        """Make a request.

        :param method: HTTP Method
        :param url: endpoint link
        :param kwargs: data, params, json and other...
        :return: status and result or exception
        """
        session = self.get_session()

        async with session.request(method, url, **kwargs) as response:
            status = response.status
            body = await response.read()

        if status >= HTTPStatus.BAD_REQUEST:
            raise self._process_exception(status, body)

        return status, body

    def _prepare_form(self, file: str | Path | io.IOBase) -> FormData:
        """Create form to pass file via multipart/form-data."""
        form = FormData()
        form.add_field("file", self._prepare_file(file))
        return form

    @staticmethod
    def _prepare_file(file: str | Path | io.IOBase) -> io.IOBase | BinaryIO:
        """Prepare accepted types to correct file type."""
        if isinstance(file, str):
            with Path(file).open("rb") as f:
                return f

        if isinstance(file, io.IOBase):
            return file

        if isinstance(file, Path):
            return file.open("rb")

        msg = (  # type: ignore[unreachable]
            f"Not supported file type: `{type(file).__name__}`"
        )
        raise TypeError(msg)

    @staticmethod
    def _process_exception(
        status: int,
        data: bytes,
    ) -> YaTrackerError:
        """Wrap API exceptions.

        :param status: response status
        :param data: response json converted to dict()
        :return: wrapped exception
        """
        text = data.decode("utf-8")
        logger.warning("Error! Status: %s. Body: %s", status, text)
        return YaTrackerError(text)

    async def close(self) -> None:
        """Close the session gracefully."""
        if not isinstance(self._session, ClientSession):
            return

        if self._session.closed:
            return

        await self._session.close()
        await asyncio.sleep(0.25)
