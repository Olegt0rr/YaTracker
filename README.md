YaTracker
===

Asyncio Yandex Tracker API client

[![Python](https://img.shields.io/badge/python-^3.10-blue)](https://www.python.org/)
[![Code linter: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/charliermarsh/ruff/main/assets/badge/v1.json)](https://github.com/charliermarsh/ruff)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Linters](https://github.com/Olegt0rr/YaTracker/actions/workflows/linters.yml/badge.svg)](https://github.com/Olegt0rr/YaTracker/actions/workflows/linters.yml)
[![Tests](https://github.com/Olegt0rr/YaTracker/actions/workflows/tests.yml/badge.svg)](https://github.com/Olegt0rr/YaTracker/actions/workflows/tests.yml)
[![Coverage](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/Olegt0rr/YaTracker/python-coverage-comment-action-data/endpoint.json)](https://github.com/Olegt0rr/YaTracker/tree/python-coverage-comment-action-data)
---

Documentation: https://olegt0rr.github.io/YaTracker/

API docs: https://yandex.cloud/en/docs/tracker/about-api


## Features
* Fully asynchronous, built on `aiohttp` — no blocking calls, no threads.
* Responses are parsed into `pydantic` v2 models, with `datetime` fields
  already converted.
* Typed end to end: `@overload`s keep your own issue/queue models flowing
  through the return types.
* Supports both Yandex 360 (`X-Org-ID` + OAuth) and Yandex Cloud
  (`X-Cloud-Org-ID` + IAM) organizations.
* Covers issues, queues, comments, worklogs, attachments, priorities and
  bulk changes.
* Local (custom) queue fields are supported via your own model subclasses.
* Pluggable transport: swap `aiohttp` for any client by subclassing
  `BaseClient`.


## Attention!
* All `self` properties are renamed to `url`, because `self` is a reserved
  name in Python.
* All `camelCase` properties are renamed to `pythonic_case`.
* All datetime values are converted to Python `datetime.datetime` objects.
* Methods are named by the author, because the Yandex API has no clear
  method names.


## How to install
```text
pip install yatracker
```


## How to use
```python
from yatracker import YaTracker

tracker = YaTracker(org_id=..., token=...)


async def foo():
    # create an issue
    issue = await tracker.create_issue("New Issue", "KEY")

    # get an issue
    issue = await tracker.get_issue("KEY-1")

    # update an issue (just pass kwargs)
    issue = await tracker.edit_issue("KEY-1", description="Hello World")

    # get transitions (a dict keyed by transition id)
    transitions = await issue.get_transitions()

    # execute a transition
    close = transitions.get("close")
    if close is not None:
        await close.execute()
```
```python
# don't forget to close tracker on app shutdown
async def on_shutdown():
    await tracker.close()
```

`YaTracker` is also an async context manager, which closes the session for you:

```python
async with YaTracker(org_id=..., token=...) as tracker:
    issue = await tracker.get_issue("KEY-1")
```


## Organizations and tokens
Pass exactly one organization id and exactly one token.

```python
# Yandex 360 organization (sends `X-Org-ID`) with an OAuth token
tracker = YaTracker(org_id=..., token=...)

# Yandex Cloud organization (sends `X-Cloud-Org-ID`) with an IAM token
tracker = YaTracker(cloud_org_id=..., iam_token=...)
```

`org_id` and `cloud_org_id` are mutually exclusive, so are `token` and
`iam_token`. API `v3` is used by default, `v2` is still available via
`YaTracker(..., api_version="v2")`.


## Error handling
Every response with a status of 300 or above is raised as a `YaTrackerError`
subclass:

```python
from yatracker.exceptions import ObjectNotFoundError, YaTrackerError

try:
    issue = await tracker.get_issue("KEY-1")
except ObjectNotFoundError:
    ...  # 404: wrong id or key
except YaTrackerError as e:
    ...  # anything else the API rejected
```

`NotAuthorizedError` (401), `SufficientRightsError` (403),
`ObjectNotFoundError` (404) and `AlreadyExistsError` (409) are the
specialised cases; any other status raises the base `YaTrackerError` with
the response body as its message.

See the [error handling guide](https://olegt0rr.github.io/YaTracker/errors/)
for details.


## More
* [Getting started](https://olegt0rr.github.io/YaTracker/howto/)
* [Custom fields](https://olegt0rr.github.io/YaTracker/custom_fields/)
* [Examples](examples)
* [Contributing](CONTRIBUTING.md)
