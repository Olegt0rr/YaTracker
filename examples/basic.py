import asyncio as aio

from yatracker import YaTracker

# CAUTION! Don't store credentials in your code!
ORG_ID = 123456
TOKEN = 'AgAEA7qidDyAXAnwDvLnsA6Yu6WzFw'

# define tracker
tracker = YaTracker(ORG_ID, TOKEN)


async def foo():
    # create issue
    issue = await tracker.create_issue('New Issue', 'KEY')
    print(issue)

    # get issue
    issue = await tracker.get_issue('KEY-1')
    print(issue)

    # update issue
    issue = await tracker.edit_issue('KEY-1', payload={'description': 'Hello World'})
    print(issue)


# don't forget to close tracker on app shutdown
async def on_shutdown():
    await tracker.close()


if __name__ == '__main__':
    loop = aio.get_event_loop()
    loop.run_until_complete(foo())
    loop.run_until_complete(on_shutdown())
    loop.close()
