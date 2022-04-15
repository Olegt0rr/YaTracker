import logging
from typing import Any, Dict, List, Optional, Union

from ..utils.mixins import ContextInstanceMixin
from .client import AIOHTTPClient, BaseClient

logger = logging.getLogger(__name__)


class BaseTracker(ContextInstanceMixin):
    def __init__(
        self,
        org_id: Union[str, int, None] = None,
        token: Optional[str] = None,
        client: Optional[BaseClient] = None,
        api_host: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        if (org_id is None or token is None) and client is None:
            raise RuntimeError(
                "You must provide either `org_id` and `token` or `BaseClient` instance "
                "with set up headers `X-Org-Id` and `Authorization` and base url."
            )
        if client is not None:
            self._client = client
        else:
            if token is None or org_id is None:
                raise RuntimeError("You must provide `org_id` and `token`.")
            self._client = AIOHTTPClient(
                org_id=org_id,
                token=token,
                api_host=api_host,
                api_version=api_version,
            )

    @staticmethod
    def clear_payload(payload: Dict[str, Any], exclude: Optional[List[str]] = None):
        payload = payload.copy()
        exclude = exclude or []
        kwargs = payload.pop("kwargs", None)
        if kwargs:
            payload.update(kwargs)
        return {
            k: v
            for k, v in payload.items()
            if k not in ["self", "cls"] + exclude and v is not None
        }

    async def close(self):
        """Graceful closing."""
        await self._client.close()
