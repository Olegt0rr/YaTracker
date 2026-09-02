import asyncio

from yatracker import YaTracker

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...


async def main() -> None:
    """Run bulk changes example."""
    # define tracker (once)
    tracker = YaTracker(ORG_ID, TOKEN)

    # create a couple of issues
    first_issue = await tracker.create_issue(
        summary="New Issue 1",
        queue="KEY",
    )
    second_issue = await tracker.create_issue(
        summary="New Issue 2",
        queue="KEY",
    )

    # bulk-add a tag to both issues
    bulk_change = await tracker.bulk_update_issues(
        issues=[first_issue, second_issue],
        values={"tags": {"add": ["reviewed"]}},
    )

    # wait for the operation to finish
    bulk_change = await tracker.wait_bulk_change(
        bulk_change,
        interval=1.0,
        timeout=60.0,
    )
    print(bulk_change.status)

    # if something went wrong, inspect per-issue errors
    if bulk_change.is_failed:
        for result in await tracker.get_bulk_change_issues(bulk_change.id):
            if result.error is not None:
                print(result.issue.key, result.error.errors)

    # bulk-close both issues, using the BulkChange.wait() shortcut this time
    bulk_change = await tracker.bulk_transition_issues(
        issues=[first_issue, second_issue],
        transition="close",
        values={"resolution": "fixed"},
    )
    bulk_change = await bulk_change.wait(interval=1.0, timeout=60.0)
    print(bulk_change.status)

    # don't forget to close tracker on app shutdown (once)
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
