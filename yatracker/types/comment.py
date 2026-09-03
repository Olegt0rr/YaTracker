from __future__ import annotations

__all__ = ["Comment"]

from datetime import datetime

from .base import Base, url_field
from .user import User


class Comment(Base):
    """Comment of an issue.

    Attributes
    ----------
    url - Reference to the comment.
    id - ID of the comment.
    text - Text of the comment.
    created_by - User who created the comment.
    updated_by - User who last updated the comment.
    created_at - Date and time the comment was created.
    updated_at - Date and time the comment was last updated.
    version - Version of the comment.
    long_id - ID of the comment in the string format.
    reactions_count - Number of the reactions of every kind, keyed by
    the lowercased reaction name.
    own_reactions - Reactions of the current user on this comment,
    lowercased.
    type - Type of the comment: `standard` (sent via the interface),
    `incoming` (created from an incoming email) or `outcoming`
    (created from an outgoing email).
    transport - How the comment was added: `internal` (via the
    interface) or `email`.

    """

    url: str = url_field()
    id: int
    text: str
    created_by: User
    updated_by: User | None = None
    created_at: datetime
    updated_at: datetime | None = None
    version: int

    long_id: str | None = None
    reactions_count: dict[str, int] | None = None
    own_reactions: list[str] | None = None
    type: str | None = None
    transport: str | None = None
