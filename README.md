# YaTracker
Asyncio Yandex Tracker API client

API docs: https://tech.yandex.com/connect/tracker/api/about-docpage/

## Attention!
* All `self` properties renamed to `url` cause it's incompatible with Python.
* All `camelCase` properties renamed to `pythonic_case`.
* Methods named by author, cause Yandex API has no clear method names.


## How to install
```text
python3.9 -m pip install yatracker
```


## How to use
```python
from yatracker import YaTracker

tracker = YaTracker(org_id=..., token=...)

async def foo():
    # create issue
    issue = await tracker.create_issue('New Issue', 'KEY')

    # get issue
    issue = await tracker.get_issue('KEY-1')

    # update issue (just pass kwargs)
    issue = await tracker.edit_issue('KEY-1', description='Hello World')

    # get transitions:
    transitions = await issue.get_transitions()

    # execute transition
    transition = transitions[0]
    await transition.execute()

```
```python
# don't forget to close tracker on app shutdown
async def on_shutdown():
    await tracker.close()

```
