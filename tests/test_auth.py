"""Tests for authorization/organization headers and API version defaults."""

from __future__ import annotations

from typing import Any

import pytest
from yatracker import YaTracker
from yatracker.tracker.client import (
    AUTH_HEADER,
    CLOUD_ORG_ID_HEADER,
    DEFAULT_API_VERSION,
    ORG_ID_HEADER,
    BaseClient,
)


class FakeClient(BaseClient):
    """In-memory client capturing `_make_request` kwargs.

    Unlike the shared `tests.conftest.FakeClient`, this does NOT default
    `org_id`/`token` — these tests exercise credential validation itself
    (including omitting org/token entirely), so every kwarg must be
    passed through to `BaseClient` untouched.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.calls: list[dict[str, Any]] = []

    async def _make_request(
        self,
        method: str,
        url: Any,
        **kwargs,
    ) -> tuple[int, bytes, dict[str, str]]:
        self.calls.append({"method": method, "url": url, **kwargs})
        return 200, b"{}", {}

    async def close(self) -> None:
        return


def test_default_api_version_is_v3() -> None:
    assert DEFAULT_API_VERSION == "v3"


def test_oauth_token_and_org_id_headers() -> None:
    client = FakeClient(org_id=42, token="token")
    assert client._headers[ORG_ID_HEADER] == "42"
    assert client._headers[AUTH_HEADER] == "OAuth token"
    assert CLOUD_ORG_ID_HEADER not in client._headers


def test_positional_arguments_still_work() -> None:
    client = FakeClient(org_id="org", token="token")
    assert client._headers == {ORG_ID_HEADER: "org", AUTH_HEADER: "OAuth token"}


def test_iam_token_uses_bearer_scheme() -> None:
    client = FakeClient(org_id="org", iam_token="iam")
    assert client._headers[AUTH_HEADER] == "Bearer iam"


def test_cloud_org_id_sets_cloud_header_only() -> None:
    client = FakeClient(cloud_org_id="cloud-org", iam_token="iam")
    assert client._headers[CLOUD_ORG_ID_HEADER] == "cloud-org"
    assert ORG_ID_HEADER not in client._headers


def test_both_org_ids_raise() -> None:
    with pytest.raises(ValueError, match="not both"):
        FakeClient(org_id="org", cloud_org_id="cloud-org", token="token")


def test_both_org_headers_raise() -> None:
    with pytest.raises(ValueError, match="at the same time"):
        FakeClient(
            token="token",
            headers={ORG_ID_HEADER: "org", CLOUD_ORG_ID_HEADER: "cloud-org"},
        )


def test_both_org_headers_raise_case_insensitive() -> None:
    with pytest.raises(ValueError, match="at the same time"):
        FakeClient(
            token="token",
            headers={"x-org-id": "org", "X-CLOUD-ORG-ID": "cloud-org"},
        )


def test_no_org_id_and_no_header_raises() -> None:
    with pytest.raises(ValueError, match="org_id"):
        FakeClient(token="token")


def test_both_tokens_raise() -> None:
    with pytest.raises(ValueError, match="not both"):
        FakeClient(org_id="org", token="token", iam_token="iam")


def test_no_token_and_no_header_raises() -> None:
    with pytest.raises(ValueError, match="iam_token"):
        FakeClient(org_id="org")


def test_custom_headers_are_not_overridden() -> None:
    client = FakeClient(
        org_id="org",
        token="token",
        headers={ORG_ID_HEADER: "custom-org", AUTH_HEADER: "OAuth custom"},
    )
    assert client._headers[ORG_ID_HEADER] == "custom-org"
    assert client._headers[AUTH_HEADER] == "OAuth custom"


def test_custom_headers_satisfy_validation() -> None:
    client = FakeClient(
        headers={CLOUD_ORG_ID_HEADER: "cloud-org", AUTH_HEADER: "Bearer iam"},
    )
    assert client._headers == {
        CLOUD_ORG_ID_HEADER: "cloud-org",
        AUTH_HEADER: "Bearer iam",
    }
    assert ORG_ID_HEADER not in client._headers


def test_custom_headers_are_matched_case_insensitively() -> None:
    client = FakeClient(
        org_id="org",
        token="token",
        headers={"x-org-id": "custom-org", "authorization": "OAuth custom"},
    )
    assert client._headers == {
        "x-org-id": "custom-org",
        "authorization": "OAuth custom",
    }


def test_extra_custom_headers_are_preserved() -> None:
    client = FakeClient(org_id="org", token="token", headers={"X-Trace": "1"})
    assert client._headers["X-Trace"] == "1"
    assert client._headers[ORG_ID_HEADER] == "org"


async def test_request_uses_v3_by_default() -> None:
    client = FakeClient(org_id="org", token="token")
    await client.request(method="GET", uri="/issues/TEST-1")
    assert client.calls[0]["url"] == "https://api.tracker.yandex.net/v3/issues/TEST-1"


async def test_request_respects_explicit_v2() -> None:
    client = FakeClient(org_id="org", token="token", api_version="v2")
    await client.request(method="GET", uri="/issues/TEST-1")
    assert client.calls[0]["url"] == "https://api.tracker.yandex.net/v2/issues/TEST-1"


async def test_request_keeps_absolute_urls() -> None:
    client = FakeClient(org_id="org", token="token")
    await client.request(method="GET", uri="https://example.com/v1/issues")
    assert client.calls[0]["url"] == "https://example.com/v1/issues"


async def test_tracker_accepts_cloud_org_and_iam_token() -> None:
    tracker = YaTracker(cloud_org_id="cloud-org", iam_token="iam")
    headers = tracker._client._headers
    assert headers == {CLOUD_ORG_ID_HEADER: "cloud-org", AUTH_HEADER: "Bearer iam"}
    await tracker.close()


async def test_tracker_positional_arguments_are_backwards_compatible() -> None:
    tracker = YaTracker("org", "token")
    assert tracker._client._headers == {
        ORG_ID_HEADER: "org",
        AUTH_HEADER: "OAuth token",
    }
    await tracker.close()


def test_tracker_without_credentials_raises() -> None:
    with pytest.raises(RuntimeError, match="cloud_org_id"):
        YaTracker()


def test_tracker_with_org_id_but_no_token_raises() -> None:
    with pytest.raises(RuntimeError, match="iam_token"):
        YaTracker(org_id="org")
