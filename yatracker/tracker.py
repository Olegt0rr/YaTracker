import asyncio as aio
import ssl
from typing import Optional, List

import certifi
import rapidjson
from aiohttp import ClientSession, TCPConnector

from .types import FullIssue, Transition, Priority, Comment, AlreadyExists
from .types import NotAuthorized, SufficientRights, ObjectNotFound, YaTrackerException
from .utils.mixins import ContextInstanceMixin


class YaTracker(ContextInstanceMixin):
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

    async def get_issue(self, issue_id, expand=None):
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

    async def edit_issue(self, issue_id, version=None, **kwargs):
        """
        Edit an issue.
        Use this request to make changes to an issue.
        The issue is selected by its ID or key.

        :param kwargs:
        :param version:
        :param issue_id:
        :return:
        """
        method = 'PATCH'
        uri = f'{self.host}/v2/issues/{issue_id}'
        params = {'version': version} if version else None
        payload = self.clear_payload(kwargs)
        data = await self._request(method, uri, params, payload)
        return FullIssue(**data)

    async def create_issue(self, summary, queue, parent=None, description=None,
                           sprint=None, type=None, priority=None, followers=None,
                           unique=None, **kwargs):
        """
        Create an issue.
        Use this request to create an issue.

        :return:
        """
        payload = self.clear_payload(locals())
        method = 'POST'
        uri = f'{self.host}/v2/issues/'
        data = await self._request(method, uri, payload=payload)
        return FullIssue(**data)

    async def get_comments(self, issue_id):
        """
        Get the comments for an issue.
        Use this request to get a list of comments in the issue.
        :param issue_id:
        :return:
        """
        method = 'GET'
        uri = f'{self.host}/v2/issues/{issue_id}/comments'
        data = await self._request(method, uri)
        return [Comment(**item) for item in data]

    async def count_issues(self, filter=None, query=None):
        """
        Get the number of issues.
        Use this request to find out how many issues meet the criteria in your request.
        :return:
        """
        method = 'POST'
        uri = f'{self.host}/v2/issues/_count'
        payload = dict()
        if filter:
            payload['filter'] = filter
        if query:
            payload['query'] = query

        data = await self._request(method, uri, payload=payload)
        return data

    async def find_issues(self, filter=None, query=None, order=None, expand=None,
                          keys=None, queue=None):
        """
        Find issues.
        Use this request to get a list of issues that meet specific criteria.
        If there are more than 10,000 issues in the response, use paging.
        :return:
        """
        if (filter or query) and (queue or keys):
            raise YaTrackerException('You can only use keys, queue or search request.')

        payload = self.clear_payload(locals(), exclude=['expand', 'order'])

        method = 'POST'
        uri = f'{self.host}/v2/issues/_search'

        params = dict()
        if order:
            params['order'] = order
        if expand:
            params['expand'] = expand

        data = await self._request(method, uri, params, payload)
        return [FullIssue(**item) for item in data]

    async def get_priorities(self, localized='True'):
        """
        Get priorities.
        Use this request to get a list of priorities for an issue.

        :param localized: 'True' or 'False'.
        :type localized: str
        :return:
        """
        method = 'GET'
        uri = f'{self.host}/v2/priorities'
        params = {'localized': localized} if localized else None
        data = await self._request(method, uri, params)
        return [Priority(**item) for item in data]

    async def get_issue_links(self, issue_id):
        """
        Get issue links.
        Use this request to get information about links between issues.
        The issue is selected by its ID or key.

        :param issue_id:
        :return:
        """
        method = 'GET'
        uri = f'{self.host}/v2/issues/{issue_id}/links'
        data = await self._request(method, uri)
        return [FullIssue(**item) for item in data]

    async def get_transitions(self, issue_id):
        """
        Get transitions.
        Use this request to get a list of possible transitions for an issue.
        The issue is selected by its ID or key.

        :param issue_id:
        :rtype: List[Transition]
        """
        method = 'GET'
        uri = f'{self.host}/v2/issues/{issue_id}/transitions'
        data = await self._request(method, uri)
        return [Transition(**item) for item in data]

    async def execute_transition(self, transition: Transition, **kwargs):
        method = 'POST'
        uri = f'{transition.url}/_execute'
        payload = self.clear_payload(kwargs)
        data = await self._request(method, uri, payload)
        return [Transition(**item) for item in data]

    async def _request(self, method, uri, params=None, payload=None):
        """ Base request method. """

        # let's get new or existing session
        if not isinstance(self._session, ClientSession) or self._session.closed:
            await self._get_session()

        # set context
        YaTracker.set_current(self)

        # let's send request and get results
        async with self._session.request(method=method, url=uri,
                                         params=params, json=payload) as response:
            text = await response.text()
            self._check_status(response.status, text)
            return self._get_beauty_json(text)

    @staticmethod
    def _check_status(status, text):
        if status in (200, 201):
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
    def clear_payload(payload: dict, exclude=None):
        exclude = exclude or []
        kwargs = payload.pop('kwargs', None)
        if kwargs:
            payload.update(kwargs)
        return {k: v for k, v in payload.items()
                if k not in ['self', 'cls'] + exclude and v is not None}

    @staticmethod
    def _get_beauty_json(text):
        """
        Ugly 'self' param escaping!
        Special thanks for Yandex API namespace incompatible with Python...

        """
        return rapidjson.loads(text.replace('"self":"', '"_self":"'))

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
