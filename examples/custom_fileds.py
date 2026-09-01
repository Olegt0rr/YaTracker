import asyncio

from yatracker import YaTracker
from yatracker.types import FullIssue, field

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...


# Create your own custom Issue type:
class HelpIssue(FullIssue):
    """Your own FullIssue type.

    For example, you have some fields passed by external system.
    One of them called 'userUsername', second - a queue local field
    with an ugly generated name.

    Local fields are optional: give them a default, so issues without
    the field can still be decoded.
    """

    user_username: str | None = None
    user_id: int | None = field(
        default=None,
        name="64a51c6d866ea82411abe756--userId",
    )


async def main() -> None:
    """Run example."""
    # define tracker (once)
    tracker = YaTracker(ORG_ID, TOKEN)

    # create an issue
    issue = await tracker.create_issue(
        summary="New Issue",
        queue="KEY",
        user_id=1234567890,
        _type=HelpIssue,
    )
    print(issue.user_id)

    # don't forget to close tracker on app shutdown (once)
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
