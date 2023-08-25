import asyncio
from pathlib import Path

from yatracker import YaTracker

# CAUTION! Don't store credentials in your code!
ORG_ID = ...
TOKEN = ...
FILE_PATH = ...
FILE_NAME = ...


async def main() -> None:
    """Run basic example.

    This way you may create, get and edit an issue.
    """
    # define tracker (once)
    tracker = YaTracker(ORG_ID, TOKEN)

    # upload temp file
    with Path.open(FILE_PATH, "rb") as file:
        attachment = await tracker.upload_temp_file(file, FILE_NAME)

    # create an issue with attachment
    issue = await tracker.create_issue(
        summary="New Issue",
        queue="KEY",
        attachment_ids=[attachment.id],
    )

    # attach another one... or the same! :)
    with Path.open(FILE_PATH, "rb") as file:
        await tracker.attach_file(
            issue_id=issue.id,
            file=file,
            filename=FILE_NAME,
        )

    # list attachments
    attachments = await tracker.get_attachments(issue.id)

    # and delete them all
    for att in attachments:
        await tracker.delete_attachment(issue.id, att.id)

    # don't forget to close tracker on app shutdown (once)
    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
