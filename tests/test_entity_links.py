"""Tests for the entity links API (projects, portfolios and goals, issue #14).

Payloads are taken from the official documentation:
https://yandex.ru/support/tracker/ru/api/entities/links/get-links
https://yandex.ru/support/tracker/ru/api/entities/links/add-links
https://yandex.ru/support/tracker/ru/api/entities/links/delete-link
"""

from __future__ import annotations

import pytest
from yatracker import YaTracker
from yatracker.types.entity import EntityLinkInfo

from tests.conftest import FakeClient, make_tracker, sent_json

# --- payload builders --------------------------------------------------------

# `GET /entities/project/<id>/links?fields=id,summary` response sample.
LINKS_RESPONSE: list[dict[str, object]] = [
    {
        "type": "is dependent by",
        "linkFieldValues": {
            "summary": "Первый проект",
            "id": "6582874de6db7f5f",
        },
    },
    {
        "type": "relates",
        "linkFieldValues": {
            "summary": "Второй проект",
            "id": "65868f3fe2b9ef74",
        },
    },
]


def links_payload(
    links: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    return links if links is not None else LINKS_RESPONSE


# --- get_entity_links ----------------------------------------------------------


class TestGetEntityLinks:
    async def test_sends_get_with_fields_param(self) -> None:
        tracker, client = make_tracker(links_payload())
        await tracker.get_entity_links(
            "project",
            "6582874de6db7f5f",
            fields=["id", "summary"],
        )

        call = client.calls[0]
        assert call["method"] == "GET"
        assert call["url"].endswith(
            "/v3/entities/project/6582874de6db7f5f/links",
        )
        assert call["params"] == {"fields": "id,summary"}
        assert call["data"] is None

    async def test_no_fields_param_by_default(self) -> None:
        tracker, client = make_tracker(links_payload())
        await tracker.get_entity_links("goal", 42)

        assert client.calls[0]["params"] is None
        assert client.calls[0]["url"].endswith("/v3/entities/goal/42/links")

    async def test_fields_as_comma_separated_string(self) -> None:
        tracker, client = make_tracker(links_payload())
        await tracker.get_entity_links("project", "1", fields="id,summary")

        assert client.calls[0]["params"] == {"fields": "id,summary"}

    async def test_decodes_relationship_from_type_key(self) -> None:
        tracker, _ = make_tracker(links_payload())
        links = await tracker.get_entity_links("project", "1", fields="id,summary")

        assert len(links) == 2
        assert all(isinstance(link, EntityLinkInfo) for link in links)
        assert links[0].relationship == "is dependent by"
        assert links[1].relationship == "relates"

    async def test_decodes_relationship_from_relationship_key_too(self) -> None:
        # the response sample names the key `type`, but the parameter table
        # calls it `relationship`: both must be accepted (issue #15 lesson).
        payload = [
            {
                "relationship": "works towards",
                "linkFieldValues": {"id": "1", "summary": "Goal"},
            },
        ]
        tracker, _ = make_tracker(payload)
        links = await tracker.get_entity_links("goal", "1", fields="id,summary")

        assert links[0].relationship == "works towards"

    async def test_relationship_defaults_to_none_when_absent(self) -> None:
        payload = [{"linkFieldValues": {"id": "1"}}]
        tracker, _ = make_tracker(payload)
        links = await tracker.get_entity_links("project", "1")

        assert links[0].relationship is None

    async def test_link_field_values_decode(self) -> None:
        tracker, _ = make_tracker(links_payload())
        links = await tracker.get_entity_links("project", "1", fields="id,summary")

        assert links[0].link_field_values.id == "6582874de6db7f5f"
        assert links[0].link_field_values.summary == "Первый проект"
        assert links[1].link_field_values.id == "65868f3fe2b9ef74"
        assert links[1].link_field_values.summary == "Второй проект"

    async def test_link_field_values_default_to_empty_when_no_fields(self) -> None:
        payload = [{"type": "depends on"}]
        tracker, _ = make_tracker(payload)
        links = await tracker.get_entity_links("project", "1")

        assert links[0].link_field_values.id is None
        assert links[0].link_field_values.summary is None

    async def test_explicit_null_link_field_values_is_tolerated(self) -> None:
        # the API sends `null` instead of an empty object when the request
        # asked for no fields; it must not raise.
        payload = [{"type": "depends on", "linkFieldValues": None}]
        tracker, _ = make_tracker(payload)
        links = await tracker.get_entity_links("project", "1")

        assert links[0].relationship == "depends on"
        assert links[0].link_field_values.id is None
        assert links[0].link_field_values.summary is None


# --- link_entities ---------------------------------------------------------------


class TestLinkEntities:
    async def test_scalar_entity_sends_object_body(self) -> None:
        tracker, client = make_tracker({})
        result = await tracker.link_entities(
            "project",
            "6582874de6db7f5f",
            "is dependent by",
            "65868f3fe2b9ef74",
        )

        assert result is True
        call = client.calls[0]
        assert call["method"] == "POST"
        assert call["url"].endswith(
            "/v3/entities/project/6582874de6db7f5f/links",
        )
        body = sent_json(call)
        assert isinstance(body, dict)
        assert body == {
            "relationship": "is dependent by",
            "entity": "65868f3fe2b9ef74",
        }

    async def test_scalar_int_entity_is_stringified(self) -> None:
        tracker, client = make_tracker({})
        await tracker.link_entities("goal", "1", "depends on", 42)

        assert sent_json(client.calls[0]) == {
            "relationship": "depends on",
            "entity": "42",
        }

    async def test_sequence_entity_sends_array_body(self) -> None:
        tracker, client = make_tracker({})
        result = await tracker.link_entities(
            "project",
            "1",
            "works towards",
            ["6582874de6db7f5f", "65868f3fe2b9ef74"],
        )

        assert result is True
        body = sent_json(client.calls[0])
        assert isinstance(body, list)
        assert body == [
            {"relationship": "works towards", "entity": "6582874de6db7f5f"},
            {"relationship": "works towards", "entity": "65868f3fe2b9ef74"},
        ]

    async def test_sequence_with_int_ids_is_stringified(self) -> None:
        tracker, client = make_tracker({})
        await tracker.link_entities("goal", "1", "child entity", [1, 2])

        assert sent_json(client.calls[0]) == [
            {"relationship": "child entity", "entity": "1"},
            {"relationship": "child entity", "entity": "2"},
        ]

    async def test_empty_sequence_raises_value_error(self) -> None:
        tracker, _ = make_tracker({})
        with pytest.raises(ValueError, match="At least one entity"):
            await tracker.link_entities("project", "1", "depends on", [])

    async def test_returns_true_regardless_of_response_body(self) -> None:
        # the API documents no response body for this endpoint; the method
        # does not decode it and always answers `True`.
        client = FakeClient(body=b"")
        tracker = YaTracker(client=client)
        result = await tracker.link_entities(
            "project",
            "1",
            "depends on",
            "2",
        )

        assert result is True


# --- delete_entity_link -----------------------------------------------------------


class TestDeleteEntityLink:
    async def test_sends_delete_with_right_param(self) -> None:
        tracker, client = make_tracker({})
        result = await tracker.delete_entity_link(
            "project",
            "6582874de6db7f5f",
            "65868f3fe2b9ef74",
        )

        assert result is True
        call = client.calls[0]
        assert call["method"] == "DELETE"
        assert call["url"].endswith(
            "/v3/entities/project/6582874de6db7f5f/links",
        )
        assert call["params"] == {"right": "65868f3fe2b9ef74"}
        assert call["data"] is None

    async def test_right_id_is_stringified(self) -> None:
        tracker, client = make_tracker({})
        await tracker.delete_entity_link("goal", "1", 42)

        assert client.calls[0]["params"] == {"right": "42"}
