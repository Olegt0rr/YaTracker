import logging
from typing import Any, Optional, Union

from yatracker.utils.mixins import ContextInstanceMixin

from .client import AIOHTTPClient, BaseClient

logger = logging.getLogger(__name__)


class BaseTracker(ContextInstanceMixin):
    """Represents technical methods for using YaTracker."""

    def __init__(
        self,
        org_id: Union[str, int, None] = None,
        token: Optional[str] = None,
        client: Optional[BaseClient] = None,
        api_host: Optional[str] = None,
        api_version: Optional[str] = None,
    ) -> None:
        if (org_id is None or token is None) and client is None:
            msg = "You must provide either `org_id` and `token` or `BaseClient` instance with set up headers `X-Org-Id` and `Authorization` and base url."
            raise RuntimeError(
                msg,
            )
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

    @staticmethod
    def clear_payload(payload: dict[str, Any], exclude: Optional[list[str]] = None):
        payload = payload.copy()
        exclude = exclude or []
        kwargs = payload.pop("kwargs", None)
        if kwargs:
            payload.update(kwargs)
        return {
            k: v
            for k, v in payload.items()
            if k not in ["self", "cls", *exclude] and v is not None
        }

    async def close(self):
        """Graceful closing."""
        await self._client.close()
