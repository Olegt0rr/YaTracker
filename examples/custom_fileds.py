import asyncio

from yatracker import YaTracker
from yatracker.types import FullIssue

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...


# Create your own custom Issue type:
class HelpIssue(FullIssue, kw_only=True):
    """Your own FullIssue type.

    For example, you have some fields passed by external system.
    One of them called 'userUsername', second - 'userId'.
    """

    user_username: str | None
    user_id: int


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
