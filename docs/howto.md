# С чего начать

## Установка

Чтобы установить актуальную версию клиента, воспользуйтесь командой:

```text
pip install -U yatracker
```

Требуется Python 3.10 или новее. Вместе с библиотекой ставятся `aiohttp`,
`pydantic` (v2) и `certifi` — больше ничего доустанавливать не нужно.

## Что понадобится

Для работы с API нужны две вещи: **идентификатор организации** и **токен**.
Библиотека поддерживает две пары значений — выбирайте ту, что соответствует
вашей организации.

| Организация | Идентификатор | Токен | Заголовки |
|---|---|---|---|
| Яндекс 360 | `org_id` | `token` (OAuth) | `X-Org-ID`, `Authorization: OAuth ...` |
| Yandex Cloud Organization | `cloud_org_id` | `iam_token` (IAM) | `X-Cloud-Org-ID`, `Authorization: Bearer ...` |

!!! warning "Только одна пара"

    `org_id` и `cloud_org_id` взаимоисключающие, как и `token` с `iam_token`.
    Если передать оба идентификатора или оба токена, конструктор бросит
    `ValueError` — API запрещает отправлять `X-Org-ID` и `X-Cloud-Org-ID`
    одновременно.

Где взять значения — в документации Яндекс Трекера:

* идентификатор организации: <https://yandex.cloud/ru/docs/tracker/enable-tracker>
* OAuth-токен: <https://yandex.cloud/ru/docs/tracker/concepts/access>
* IAM-токен: <https://yandex.cloud/ru/docs/iam/concepts/authorization/iam-token>

## Инициализация

Импортируйте библиотеку

```python
from yatracker import YaTracker
```

Создайте экземпляр, передав в конструктор класса необходимые секреты

```python
import os

from yatracker import YaTracker

tracker = YaTracker(
    org_id=os.environ["TRACKER_ORG_ID"],  # (1)
    token=os.environ["TRACKER_TOKEN"],
)
```

1. Не сохраняйте свои учётные данные прямо в коде. Используйте переменные окружения.

Для организации в Yandex Cloud используйте вторую пару параметров — они
именованные, передать их позиционно нельзя:

```python
tracker = YaTracker(
    cloud_org_id=os.environ["TRACKER_CLOUD_ORG_ID"],
    iam_token=os.environ["TRACKER_IAM_TOKEN"],
)
```

Для работы с одной организацией достаточно одного клиента.
Вы один раз создаёте его и далее повторно используете при необходимости.

!!! tip "Ленивая сессия"

    HTTP-сессия `aiohttp` создаётся не в конструкторе, а при первом запросе.
    Поэтому `YaTracker(...)` можно спокойно вызывать на уровне модуля,
    вне работающего event loop.

## Завершение работы

Сессию нужно закрыть — иначе `aiohttp` пожалуется на незакрытый коннектор.
Есть два способа.

Явный вызов `close()` — подходит для долгоживущего приложения,
где клиент создаётся один раз:

```python
async def on_shutdown():
    await tracker.close()
```

Асинхронный контекстный менеджер — подходит для скриптов и разовых задач:

```python
async with YaTracker(org_id=..., token=...) as tracker:
    issue = await tracker.get_issue("WRITERS-42")
```

При выходе из блока `close()` вызывается автоматически.

!!! note "Повторное использование"

    После `close()` клиент остаётся рабочим: следующий запрос просто создаст
    новую сессию. Но плодить сессии без нужды не стоит — держите один
    экземпляр `YaTracker` на всё приложение.

## Использование

!!! note "Обратите внимание"

    Все методы `YaTracker`, вызывающие API, являются асинхронными.
    Соответственно, вызывать их нужно внутри корутин.
    Но для упрощения примеров они будут использованы напрямую, как будто мы находимся уже внутри функции.

    Т.е. вместо
    ```python
    async def foo(...):
        await method(...)
    ```
    Мы будем писать
    ```python
    await method(...)
    ```

Для начала создадим новую задачу в очереди для писателей

```python
issue = await tracker.create_issue("Написать шедевр", "WRITERS")  # (1)
```

1. `WRITERS` – ключ очереди

Первые два аргумента — `summary` и `queue`, все остальные передаются только
по имени: `description`, `assignee`, `followers`, `priority`, `parent`,
`type_`, `sprint`, `unique`, `attachment_ids`.

Дополним задачу описанием

```python
issue = await tracker.edit_issue(
    issue_id="WRITERS-1",
    description="... или нечто ценное",  # (1)
)
```

1. Описание можно было задать ещё при создании, а здесь это лишь повод для редактирования.

`edit_issue()` принимает произвольные `**kwargs` — любое поле задачи,
которое разрешает менять API.

Если вам известен ключ задачи, то нетрудно её получить

```python
issue = await tracker.get_issue("WRITERS-42")
```

Полученный объект — модель `FullIssue`, у которой есть и данные, и несколько
собственных методов:

```python
issue = await tracker.get_issue("WRITERS-42")

print(issue.key)  # WRITERS-42
print(issue.summary)  # Написать шедевр
print(issue.status)  # Открыт
print(issue.created_at)  # datetime.datetime(...)

comments = await issue.get_comments()
await issue.post_comment("Взял в работу")
```

Переходы по статусам возвращаются словарём, где ключ — идентификатор перехода:

```python
transitions = await issue.get_transitions()

close = transitions.get("close")
if close is not None:
    await close.execute()
```

## Обработка ошибок

Любой ответ с кодом 300 и выше превращается в исключение — наследника
`YaTrackerError`. Минимальная обработка выглядит так:

```python
from yatracker.exceptions import ObjectNotFoundError, YaTrackerError

try:
    issue = await tracker.get_issue("WRITERS-42")
except ObjectNotFoundError:
    print("Такой задачи нет")
except YaTrackerError as e:
    print(f"Трекер вернул ошибку: {e}")
```

Подробный разбор иерархии исключений — в разделе
[Обработка ошибок](errors.md).

## Полный пример

```python
import asyncio
import os

from yatracker import YaTracker
from yatracker.exceptions import YaTrackerError


async def main() -> None:
    async with YaTracker(
        org_id=os.environ["TRACKER_ORG_ID"],
        token=os.environ["TRACKER_TOKEN"],
    ) as tracker:
        try:
            issue = await tracker.create_issue(
                "Написать шедевр",
                "WRITERS",
                description="... или нечто ценное",
            )
        except YaTrackerError as e:
            print(f"Не удалось создать задачу: {e}")
            return

        print(f"Создана задача {issue.key}: {issue.url}")


if __name__ == "__main__":
    asyncio.run(main())
```
