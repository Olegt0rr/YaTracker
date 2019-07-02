import asyncio as aio

from yatracker import YaTracker
from yatracker.types import FullIssue

# CAUTION! Don't store credentials in your code!
ORG_ID = 123456
TOKEN = 'AgAEA7qidDyAXAnwDvLnsA6Yu6WzFw'

# define tracker
tracker = YaTracker(ORG_ID, TOKEN)


async def main():
    # view issue
    issue: FullIssue = await tracker.view_issue('MAF-1')

    # let's print object to make sure that we get it
    print(issue)


async def on_shutdown():
    # don't forget to close tracker on app shutdown
    await tracker.close()


if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(main())
    loop.run_until_complete(on_shutdown())
    loop.close()
