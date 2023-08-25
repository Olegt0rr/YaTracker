import asyncio

from yatracker import YaTracker

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...


async def main() -> None:
    """Basic example.

    This way you may create, get and edit an issue.
    """
    # define tracker (once)
    tracker = YaTracker(ORG_ID, TOKEN)
    
    # create an issue
    issue = await tracker.create_issue("New Issue", "KEY")
    print(issue)

    # get the issue
    issue = await tracker.get_issue("KEY-1")
    print(issue)

    # update the issue
    issue = await tracker.edit_issue("KEY-1", description="Hello World")
    print(issue)

    # don't forget to close tracker on app shutdown (once)
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main)
