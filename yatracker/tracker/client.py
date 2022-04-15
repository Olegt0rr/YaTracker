"""Base aiohttp client class module."""

import asyncio
import io
import ssl
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import certifi
from aiohttp import ClientSession, ClientTimeout, FormData, TCPConnector
from aiohttp.typedefs import StrOrURL

from ..types import (
    AlreadyExists,
    NotAuthorized,
    ObjectNotFound,
    SufficientRights,
    YaTrackerException,
)
from ..utils import json

DEFAULT_API_HOST = "https://api.tracker.yandex.net"
DEFAULT_API_VERSION = "v2"


class BaseClient(ABC):
    """Represents abstract base class for tracker client."""

    def __init__(
        self,
        org_id: Union[str, int],
        token: str,
        headers: Optional[Dict[str, str]] = None,
        api_host: Optional[str] = None,
        api_version: Optional[str] = None,
        **kwargs,
    ):
        """
        Set defaults on object init.

        By default, `self._session` is None.
        It will be created on a first API request.
        The second request will use the same `self._session`.
        """
        api_host = api_host or DEFAULT_API_HOST
        api_version = api_version or DEFAULT_API_VERSION
        self._base_url = f"{api_host}/{api_version}"
        _headers = headers.copy() if headers else {}
        _headers.setdefault("X-Org-Id", str(org_id))
        _headers.setdefault("Authorization", f"OAuth {token}")
        self._headers: Dict[str, str] = _headers
        self._session: Optional[ClientSession] = None

    async def request(
        self,
        method: str,
        uri: str,
        params: Optional[Dict[str, Any]] = None,
        payload: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """Make request."""
        status, body = await self._make_request(
            method=method,
            url=uri,
            params=params,
            json=payload,
            **kwargs,
        )
        self._check_status(status, body)
        return self._get_beauty_json(body)

    @abstractmethod
    async def _make_request(
        self, method: str, url: StrOrURL, **kwargs
    ) -> Tuple[int, str]:
        """Get raw response from via http-client.
        :returns: tuple of (status_code, response_body)
        """

    @staticmethod
    def _check_status(status, text):
        if status < 300:
            return

        if status == 401:
            raise NotAuthorized()

        if status == 403:
            raise SufficientRights()

        if status == 404:
            raise ObjectNotFound()

        if status == 409:
            raise AlreadyExists()

        raise YaTrackerException(text)

    @staticmethod
    def _get_beauty_json(text: str) -> Union[Dict[str, Any], List[Dict[str, Any]], str]:
        """
        Ugly 'self' param escaping!
        Special thanks for Yandex API namespace incompatible with Python

        """
        # noinspection PyBroadException
        try:
            return json.loads(text.replace('"self":"', '"_self":"'))
        except Exception:
            return text

    async def close(self):
        """Close the session gracefully."""


class AIOHTTPClient(BaseClient):
    """
    Base aiohttp client.

    Consists of all methods need to make a request to API:
     - session caching
     - request wrapping
     - exceptions wrapping
     - grace session close
     - e.t.c.
    """

    def __init__(
        self,
        org_id: Union[str, int],
        token: str,
        headers: Optional[Dict[str, str]] = None,
        api_host: Optional[str] = None,
        api_version: Optional[str] = None,
        **kwargs,
    ):
        """
        Set defaults on object init.

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

    def get_session(self):
        """Get cached session. One session per instance."""
        if isinstance(self._session, ClientSession) and not self._session.closed:
            return self._session

        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)

        self._session = ClientSession(
            base_url=self._base_url,
            connector=connector,
            headers=self._headers,
            json_serialize=json.dumps,
            timeout=self._timeout,
        )
        return self._session

    async def _make_request(
        self, method: str, url: StrOrURL, **kwargs
    ) -> Tuple[int, str]:
        """
        Make a request.

        :param method: HTTP Method
        :param url: endpoint link
        :param kwargs: data, params, json and other...
        :return: status and result or exception
        """
        session = self.get_session()

        async with session.request(method, url, **kwargs) as response:
            status = response.status
            text = await response.text()

        if status != 200:
            raise self._process_exception(status, text)

        return status, text

    def _prepare_form(self, file: Union[str, Path, io.IOBase]) -> FormData:
        """Create form to pass file via multipart/form-data."""
        form = FormData()
        form.add_field("file", self._prepare_file(file))
        return form

    @staticmethod
    def _prepare_file(file: Union[str, Path, io.IOBase]):
        """Prepare accepted types to correct file type."""
        if isinstance(file, str):
            return Path(file).open("rb")

        if isinstance(file, io.IOBase):
            return file

        if isinstance(file, Path):
            return file.open("rb")

        raise TypeError(f"Not supported file type: `{type(file).__name__}`")

    @staticmethod
    def _process_exception(
        status: int, data: Union[Dict[str, Any], str]
    ) -> YaTrackerException:
        """
        Wrap API exceptions.

        :param status: response status
        :param data: response json converted to dict()
        :return: wrapped exception
        """
        if isinstance(data, dict):
            text = data.get("message") or data.get("detail")
        else:
            text = data
        return YaTrackerException(text)

    async def close(self):
        """Close the session gracefully."""
        if not isinstance(self._session, ClientSession):
            return

        if self._session.closed:
            return

        await self._session.close()
        await asyncio.sleep(0.25)
