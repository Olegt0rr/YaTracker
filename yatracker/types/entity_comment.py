from __future__ import annotations

__all__ = ["EntityComment", "EntityCommentsPage"]

from datetime import datetime

from .base import Base, field, url_field
from .ref import Ref
from .user import User


class EntityComment(Base):
    """Comment on an entity (a project, a portfolio or a goal).

    Unlike an issue comment (`Comment`), an entity comment carries a
    string id next to the numeric one (`longId`), the rendered HTML of
    the text, the attachments and the reactions, so it is modelled
    separately.

    The fields that depend on the `expand` query parameter are optional:
    `textHtml` needs "html", `attachments` needs "attachments" and
    `usersReacted`/`ownReactions` need "reactions" (or "all" for
    everything). Without "reactions" the API sends `reactionsCount`
    instead of `usersReacted`.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/comments/get-comment
    """

    url: str = url_field()
    id: int
    long_id: str | None = None
    text: str
    text_html: str | None = None
    attachments: list[Ref] | None = None
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None
    # `{"like": [<user>, ...]}`; the reaction names are server-owned
    # ("like", "dislike", "laugh", "tada", "hooray", "confused", "heart",
    # "rocket", "eyes", "fire", "ok", "facepalm", "check").
    users_reacted: dict[str, list[User]] | None = None
    reactions_count: dict[str, int] | None = None
    own_reactions: list[str] | None = None
    # The samples show objects, but the docs describe both `summonees`
    # and `maillistSummonees` as an array of objects *or* of strings
    # (logins / ids), so plain strings are accepted as well.
    summonees: list[User | str] | None = None
    maillist_summonees: list[Ref | str] | None = None
    version: int
    #: "standard" (sent from the Tracker interface), "incoming" or
    #: "outcoming" (created from a mail).
    type: str | None = None
    #: "internal" (the Tracker interface) or "email".
    transport: str | None = None


class EntityCommentsPage(Base):
    """Page of entity comments returned by the `_relative` endpoint.

    Source:
    https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments
    """

    comments: list[EntityComment] = field(default_factory=list)
    has_next: bool = False
    has_prev: bool = False
