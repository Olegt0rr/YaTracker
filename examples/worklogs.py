import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from yatracker import YaTracker
from yatracker.types import Duration

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...


async def main() -> None:
    """Run worklogs example."""
    # define tracker (once)
    tracker = YaTracker(ORG_ID, TOKEN)

    # create an issue
    issue = await tracker.create_issue(
        summary="New Issue",
        queue="KEY",
    )

    # add worklog to issue
    worklog = await tracker.post_worklog(
        issue_id=issue.id,
        start=datetime.now(ZoneInfo("Europe/Moscow")),
        duration=Duration(hours=5),
        comment="Worklog testing",
    )

    # edit worklog
    worklog = await tracker.edit_worklog(
        issue_id=issue.id,
        worklog_id=worklog.id,
        duration=Duration(minutes=5),
    )

    # delete worklog
    await tracker.delete_worklog(issue.id, worklog.id)

    # don't forget to close tracker on app shutdown (once)
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
