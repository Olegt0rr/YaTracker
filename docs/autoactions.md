# Автодействия

Автодействие (autoaction) — это правило очереди, которое периодически (по умолчанию раз в
час) находит задачи по фильтру или запросу и применяет к каждой из них набор действий:
меняет статус, обновляет поля, добавляет комментарий, отправляет HTTP-запрос или вычисляет
значение. В отличие от триггера (см. [«Триггеры»](triggers.md)), автодействие не реагирует на
события в реальном времени — оно само находит подходящие задачи по расписанию, поэтому у него
нет условий срабатывания, а вместо них — фильтр (`filter_`) или запрос (`query`) задач.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с автодействиями являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Получение автодействия

### get_autoaction

```python
async def get_autoaction(
    self, queue_id: str | int, autoaction_id: str | int
) -> Autoaction: ...
```

Возвращает одно автодействие очереди по его идентификатору.

```python
autoaction = await tracker.get_autoaction("DESIGN", 9)

print(autoaction.name, autoaction.active, autoaction.filter_, autoaction.query)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `autoaction_id` — идентификатор автодействия.

Отдельного метода для получения списка всех автодействий очереди в `yatracker` нет — он не
задокументирован как публичный эндпоинт.

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-autoaction

## Создание автодействия

### create_autoaction

```python
async def create_autoaction(
    self,
    queue_id: str | int,
    name: str,
    actions: list[TriggerAction | dict[str, Any]],
    *,
    filter_: dict[str, Any] | None = None,
    query: str | None = None,
    active: bool | None = None,
    enable_notifications: bool | None = None,
    interval_millis: int | None = None,
    calendar: AutoactionCalendar | dict[str, Any] | None = None,
) -> Autoaction: ...
```

Создаёт новое автодействие в указанной очереди.

```python
from yatracker.types.trigger import TriggerAction

autoaction = await tracker.create_autoaction(
    "DESIGN",
    name="AutoactionName",
    actions=[
        TriggerAction(type="Transition", status={"key": "needInfo"}),
    ],
    filter_={
        "priority": ["critical"],
        "status": ["inProgress"],
    },
    calendar={"id": 2},
)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `name` — название автодействия (обязательное поле).
3. `actions` — действия, применяемые к каждой найденной задаче: список `TriggerAction` (или
   обычных словарей с теми же ключами). Автодействия поддерживают только часть типов
   действий триггера — `Transition`, `Update`, `CreateComment`, `Webhook` и
   `CalculateFormula`, — остальные (`Move`, `CreateChecklist`, `CreateIssue`) в ответе
   `create-autoaction` не упоминаются. Примеры для каждого типа — в разделе «Действия»
   страницы [«Триггеры»](triggers.md).
4. `filter_` — фильтр задач, словарь «идентификатор поля → список принимаемых значений»,
   например `{"priority": ["critical"], "status": ["inProgress"]}`. Отправляется как
   `filter`.
5. `query` — строка на языке запросов, отбирающая задачи вместо (или вместе с) `filter_`,
   например `'"Status": "In progress"'`.
6. `active` — активность автодействия.
7. `enable_notifications` — отправлять ли уведомления о срабатывании.
8. `interval_millis` — периодичность запуска в миллисекундах (по умолчанию `3600000`, то есть
   раз в час).
9. `calendar` — график работы, в рамках которого автодействие активно: `AutoactionCalendar`
   (или словарь) с идентификатором графика `id`.

Поля со значением `None` не отправляются.

!!! warning "Нужен хотя бы один из `filter_` и `query`"

    Если не передать ни `filter_`, ни `query`, метод поднимает `ValueError` ещё до запроса —
    без них API не будет знать, к каким задачам применять действия.

    ```python
    await tracker.create_autoaction("DESIGN", name="Broken", actions=[...])
    # ValueError: Pass at least one of `filter_` and `query`.
    ```

Источник: https://yandex.ru/support/tracker/ru/api/queues/create-autoaction

## Логи автодействия

### get_autoaction_logs

```python
async def get_autoaction_logs(
    self, queue_id: str | int, autoaction_id: str | int
) -> list[AutoactionLaunch]: ...
```

Возвращает список запусков автодействия. Ручка доступна только для автодействий, которые
настраивают автоматическое обновление задач. Пагинация и фильтрация не документированы.

```python
launches = await tracker.get_autoaction_logs("DESIGN", 9)

for launch in launches:
    print(launch.id, launch.launch_time, launch.successes, launch.failures)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `autoaction_id` — идентификатор автодействия.

Источник: https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs

### get_autoaction_log

```python
async def get_autoaction_log(
    self, queue_id: str | int, autoaction_id: str | int, launch_id: str | int
) -> list[AutoactionLaunchResult]: ...
```

Возвращает результат одного запуска автодействия — что оно сделало с каждой найденной
задачей.

```python
results = await tracker.get_autoaction_log("DESIGN", 9, launches[0].id)

for result in results:
    print(result.issue_reference.key, result.status.value)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `autoaction_id` — идентификатор автодействия.
3. `launch_id` — идентификатор запуска (значение `id` из `get_autoaction_logs`).

Источник: https://yandex.ru/support/tracker/ru/api/queues/view-autoaction-logs

## Модели

### `Autoaction`

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на автодействие (ключ `self`). |
| `id` | `str` | Идентификатор автодействия. |
| `queue` | `Queue` | Очередь, в которой создано автодействие. |
| `name` | `str` | Название автодействия. |
| `version` | `int` | Версия автодействия, увеличивается при каждом изменении. |
| `active` | `bool` | Активно ли автодействие. |
| `created` | `datetime` | Дата и время создания. |
| `updated` | `datetime` | Дата и время последнего изменения. |
| `filter_` | `dict[str, Any] \| None` | Фильтр задач (API-ключ `filter`). |
| `query` | `str \| None` | Запрос, отбирающий задачи. |
| `actions` | `list[TriggerAction]` | Действия, применяемые к найденным задачам — модель общая с триггерами, см. [«Триггеры»](triggers.md). |
| `enable_notifications` | `bool \| None` | Отправляются ли уведомления. |
| `last_launch` | `datetime \| None` | Дата и время последнего запуска. |
| `total_issues_processed` | `int \| None` | Число задач, проверенных при последнем запуске. |
| `interval_millis` | `int \| None` | Периодичность запуска в миллисекундах. |
| `calendar` | `AutoactionCalendar \| None` | График работы, в рамках которого автодействие активно. |

### `AutoactionCalendar`

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | `str` | Идентификатор графика работы. |

### `AutoactionLaunch`

Один запуск автодействия, возвращается `get_autoaction_logs`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | `str` | Идентификатор запуска. Передаётся в `get_autoaction_log`. |
| `launch_time` | `datetime \| None` | Время начала запуска. |
| `search_hits` | `int \| None` | Число задач, обработанных автодействием. |
| `successes` | `int \| None` | Число задач, на которых автодействие сработало успешно. |
| `failures` | `int \| None` | Число задач, на которых автодействие завершилось ошибкой. |
| `search_failed` | `bool \| None` | `True`, если ни одна задача не была обработана. |

### `AutoactionIssueRef`

Короткая ссылка на задачу внутри результата запуска (`AutoactionLaunchResult.issue_reference`),
наследует `Ref`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на задачу. |
| `id` | `str` | Идентификатор задачи. |
| `display` | `str \| None` | Название задачи, отображаемое в интерфейсе. |
| `key` | `str \| None` | Ключ задачи. |
| `version` | `int \| None` | Версия задачи, увеличивается при каждом изменении. |

### `AutoactionLaunchResult`

Что автодействие сделало с одной задачей за один запуск, возвращается `get_autoaction_log`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | `int` | Порядковый номер срабатывания автодействия (с нуля). |
| `issue_reference` | `AutoactionIssueRef \| None` | Задача, к которой было применено автодействие. |
| `status` | `AutoactionLaunchStatus \| None` | Результат применения автодействия к этой задаче. |

### `AutoactionLaunchStatus`

| Поле | Тип | Описание |
| --- | --- | --- |
| `value` | `str` | Значение статуса, например `success`. |
| `display` | `str \| None` | Название статуса, отображаемое в интерфейсе. |

## Типичный сценарий

Создать автодействие, которое раз в час переводит просроченные критичные задачи в статус
«Требуется информация», затем проверить результат последнего запуска:

```python
from yatracker.types.trigger import TriggerAction

autoaction = await tracker.create_autoaction(
    "DESIGN",
    name="Escalate critical",
    actions=[TriggerAction(type="Transition", status={"key": "needInfo"})],
    filter_={"priority": ["critical"], "status": ["inProgress"]},
)

launches = await tracker.get_autoaction_logs("DESIGN", autoaction.id)
if launches:
    results = await tracker.get_autoaction_log("DESIGN", autoaction.id, launches[0].id)
    for result in results:
        print(result.issue_reference.key, result.status.value)
```
