import asyncio as aio
import ssl
from typing import Optional

import certifi
import rapidjson
from aiohttp import ClientSession, TCPConnector

from .types import FullIssue


class YaTracker:
    """
    API docs: https://tech.yandex.com/connect/tracker/api/about-docpage/

    Attention!
        All 'self' properties renamed to 'link' cause it's incompatible with Python.
        All camelCase properties renamed to pythonic_case.
        Methods named by author, cause Yandex API has no clear method names.
        For help you to recognize method names full description is attached.

    """
    host = 'https://api.tracker.yandex.net'
    _session: Optional[ClientSession] = None

    def __init__(self, org_id, token):
        self.__org_id = org_id
        self.__token = token

    async def view_issue(self, issue_id, expand=None):
        """
        View issue parameters.
        Use this request to get information about an issue.

        :type issue_id: str
        :param expand: Additional fields to include in the response:
                        transitions — Lifecycle transitions between statuses.
                        attachments — Attached files

        :return:
        """
        method = 'GET'
        uri = f'{self.host}/v2/issues/{issue_id}'
        params = {'expand': expand} if expand else None
        data = await self._request(method, uri, params)
        return FullIssue(**data)

    async def _request(self, method, uri, params):
        """ Base request method. """

        # let's get new or existing session
        if not isinstance(self._session, ClientSession) or self._session.closed:
            await self._get_session()

        # let's send request and get results
        async with self._session.request(method, uri, params=params) as response:
            text = await response.text()
            return self._get_beauty_json(text)

    @staticmethod
    def _get_beauty_json(text):
        """
        Ugly 'self' param escaping!
        Special thanks for Yandex API namespace incompatible with Python...

        """
        return rapidjson.loads(text.replace('{"self":"', '{"_self":"'))

    async def _get_session(self):
        """ Define aiohttp.ClientSession. """
        # set default headers
        headers = dict()
        headers['Authorization'] = f'OAuth {self.__token}'
        headers['X-Org-Id'] = f'{self.__org_id}'

        # add ssl support
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)

        # define session
        self._session = ClientSession(connector=connector, headers=headers,
                                      json_serialize=rapidjson.dumps)

    async def close(self):
        """ Graceful closing. """
        if isinstance(self._session, ClientSession) and not self._session.closed:
            await self._session.close()
            await aio.sleep(0.250)
