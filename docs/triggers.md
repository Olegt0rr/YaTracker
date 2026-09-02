# Триггеры

Триггер (trigger) — это правило очереди, которое реагирует на события в задаче (создание
комментария, изменение поля, выполнение всех пунктов чеклиста и так далее) и выполняет над
задачей одно или несколько действий: меняет статус, обновляет поля, создаёт комментарий или
чеклист, отправляет HTTP-запрос, создаёт новую задачу. В отличие от автодействий (см.
[«Автодействия»](autoactions.md)), триггер срабатывает сразу в момент события, а не по
расписанию, и не привязан к фильтру задач — вместо него у триггера есть условия срабатывания
(`conditions`).

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с триггерами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Получение триггеров

### get_triggers

```python
async def get_triggers(
    self,
    queue_id: str | int,
    per_page: int | None = None,
    id_: str | int | None = None,
) -> list[Trigger]: ...
```

Возвращает одну страницу триггеров очереди. Пагинация здесь относительная, а не по номеру
страницы: триггеры отсортированы по возрастанию `id`, и чтобы получить следующую страницу,
нужно передать `id` последнего триггера предыдущей страницы.

```python
page = await tracker.get_triggers("DESIGN", per_page=20)
if page:
    next_page = await tracker.get_triggers("DESIGN", per_page=20, id_=page[-1].id)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `per_page` — количество триггеров на странице.
3. `id_` — идентификатор последнего триггера предыдущей страницы (query-параметр `id`); для
   первой страницы не передаётся.

Пустая страница означает, что триггеры закончились. Документация описывает `id` как триггер,
*с которого начинается* следующая страница, поэтому триггер-курсор может вернуться ещё раз в
начале следующей страницы — `iter_triggers` ниже учитывает это сам.

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-triggers

### iter_triggers

Чтобы не управлять пагинацией вручную, используйте `iter_triggers` — асинхронный генератор
поверх `get_triggers`:

```python
async def iter_triggers(
    self,
    queue_id: str | int,
    per_page: int | None = None,
) -> AsyncIterator[Trigger]: ...
```

```python
async for trigger in tracker.iter_triggers("DESIGN", per_page=20):
    print(trigger.id, trigger.name)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `per_page` — количество триггеров, запрашиваемых за один вызов `get_triggers`.

Итерация останавливается, когда очередная страница оказывается пустой или не продвигается
дальше курсора; если Трекер вернёт триггер-курсор повторно, второй раз он не отдаётся.

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-triggers

### get_trigger

```python
async def get_trigger(self, queue_id: str | int, trigger_id: str | int) -> Trigger: ...
```

Возвращает один триггер очереди по его идентификатору.

```python
trigger = await tracker.get_trigger("DESIGN", 16)

print(trigger.name, trigger.active, trigger.version)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `trigger_id` — идентификатор триггера.

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-trigger

## Создание триггера

### create_trigger

```python
async def create_trigger(
    self,
    queue_id: str | int,
    name: str,
    actions: list[TriggerAction | dict[str, Any]],
    *,
    conditions: list[TriggerCondition | dict[str, Any]] | None = None,
    active: bool | None = None,
) -> Trigger: ...
```

Создаёт новый триггер в указанной очереди.

```python
from yatracker.types.trigger import TriggerAction, TriggerCondition

trigger = await tracker.create_trigger(
    "DESIGN",
    name="TriggerName",
    actions=[
        TriggerAction(type="Transition", status={"key": "open"}),
    ],
    conditions=[
        TriggerCondition(type="CommentFullyMatchCondition", word="Open"),
    ],
)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `name` — название триггера (обязательное поле).
3. `actions` — действия триггера: список `TriggerAction` (или обычных словарей с теми же
   ключами) — см. раздел «Действия» ниже.
4. `conditions` — условия срабатывания триггера: список `TriggerCondition` — см. раздел
   «Условия» ниже. Плоский список означает, что должны выполняться все условия
   (логическое И); чтобы сработать при выполнении хотя бы одного из них, оберните их в
   единственный элемент `TriggerCondition(type="Or", conditions=[...])`.
5. `active` — активность триггера (по умолчанию Трекер создаёт активный триггер).

Поля со значением `None` не отправляются.

Источник: https://yandex.ru/support/tracker/ru/api/queues/create-trigger

## Изменение триггера

### update_trigger

```python
async def update_trigger(
    self,
    queue_id: str | int,
    trigger_id: str | int,
    version: str | int,
    *,
    name: str | None = None,
    actions: list[TriggerAction | dict[str, Any]] | None = None,
    conditions: list[TriggerCondition | dict[str, Any]] | None = None,
    active: bool | None = None,
    before: str | int | None = None,
) -> Trigger: ...
```

Изменяет существующий триггер.

```python
trigger = await tracker.update_trigger(
    "DESIGN",
    trigger_id=16,
    version=trigger.version,
    active=False,
)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `trigger_id` — идентификатор изменяемого триггера.
3. `version` — текущая версия триггера (`trigger.version`).
4. `name` — новое название триггера.
5. `actions` — новые действия триггера. Задаются целиком: `actions` заменяет существующий
   список, а не дополняет его.
6. `conditions` — новые условия срабатывания триггера, тоже целиком.
7. `active` — активность триггера.
8. `before` — идентификатор триггера, перед которым нужно поместить изменяемый (меняет
   порядок отображения триггеров в интерфейсе).

Поля со значением `None` не отправляются и остаются без изменений.

!!! warning "`version` — это query-параметр, а не заголовок"

    В отличие от досок и спринтов (см. [«Доски и спринты»](boards.md)), где версия объекта
    уходит в заголовок `If-Match`, здесь версия передаётся частью URL:
    `PATCH /queues/{id}/triggers/{id}?version=<версия>`. Библиотека собирает эту строку сама
    — достаточно передать `version` обычным именованным параметром. Если версия устарела,
    официальная документация этого метода описывает конфликт как ошибками `409` и `412`
    одновременно; `yatracker` поднимает `AlreadyExistsError` на `409` и
    `PreconditionFailedError` на `412` — в любом случае объект нужно перечитать и повторить
    запрос с актуальной версией.

Источник: https://yandex.ru/support/tracker/ru/api/queues/change-trigger

## Логи триггера

### get_trigger_logs

```python
async def get_trigger_logs(
    self,
    queue_id: str | int,
    trigger_id: str | int,
    *,
    issue_id: str | None = None,
    limit: int | None = None,
    from_: str | datetime | None = None,
    to: str | datetime | None = None,
) -> list[TriggerWebhookLog]: ...
```

Возвращает логи запусков действия `Webhook` триггера — других действий эта ручка не
касается. Пагинации нет: по умолчанию Трекер отдаёт 10 самых новых записей, передайте
`limit` (не больше 100), чтобы получить больше.

```python
logs = await tracker.get_trigger_logs("DESIGN", 6, issue_id="DESIGN-123", limit=100)

for log in logs:
    print(log.request.endpoint, log.response.status_code)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `trigger_id` — идентификатор триггера.
3. `issue_id` — ключ или идентификатор задачи, по которой нужно отфильтровать логи.
4. `limit` — количество записей в ответе (по умолчанию 10, не больше 100).
5. `from_` — начало временного диапазона: `datetime` или готовая строка формата
   `YYYY-MM-DDThh:mm:ss.sss±hhmm` (query-параметр `from`).
6. `to` — конец временного диапазона, в том же формате.

Источник: https://yandex.ru/support/tracker/ru/api/queues/view-trigger-logs

## Действия

Действие триггера (`TriggerAction`) — это плоский объект, вид которого определяет поле
`type`; заполняются только ключи, относящиеся к выбранному типу. Автодействия
(`create_autoaction`) используют ту же модель и поддерживают часть этих типов — см.
[«Автодействия»](autoactions.md). Ниже — по одному примеру на каждый документированный тип.

Источник: https://yandex.ru/support/tracker/ru/api/queues/change-trigger-actions

### Transition — изменить статус задачи

```python
TriggerAction(type="Transition", status="open")
```

`status` — ключ, идентификатор или название статуса (в ответе — полный объект `Status`).

### Update — изменить значения в полях

```python
TriggerAction(
    type="Update",
    update={
        "description": "Новая задача",
        "tags": {"add": "Новый тег"},
        "resolution": None,
    },
)
```

`update` — словарь «ключ поля → новое значение»; `None` очищает поле, операторы `set` /
`add` / `remove` принимаются так же, как в `update_issue`.

### Move — переместить задачу

```python
TriggerAction(type="Move", queue="TESTQUEUE")
```

`queue` — ключ очереди, в которую нужно переместить задачу.

### CreateComment — добавить комментарий

```python
TriggerAction(
    type="CreateComment",
    text="Обращение создано {{currentDateTime.date}}",
    from_robot=False,
)
```

`text` — текст комментария (поддерживает те же шаблонные плейсхолдеры, что и текст макроса).
`from_robot` — `True`, чтобы отправить от имени робота, `False` — от имени пользователя,
запустившего триггер. В таблицах официальной документации это действие также встречается под
именем `Event.comment-create` (см. пример ответа `get_triggers`) — оба значения `type`
описывают одно и то же действие, клиент их не различает.

### CreateChecklist — создать чеклист

```python
TriggerAction(
    type="CreateChecklist",
    checklist_items=[
        {
            "text": "Сделать то",
            "assignee": "username",
            "deadline": {"date": "2025-05-23"},
        },
        {
            "text": "Сделать это",
            "assignee": "username",
            "deadline": {"date": "2025-05-23"},
        },
        {"text": "Отчитаться за все"},
    ],
)
```

`checklist_items` — список пунктов чеклиста, каждый — словарь с `text` (обязательно),
`assignee` и `deadline` (`{"date": "YYYY-MM-DD"}`).

### Webhook — отправить HTTP-запрос

```python
TriggerAction(
    type="Webhook",
    endpoint="https://api.example.com/messenger/sendMessage",
    method="GET",
    content_type="application/json; charset=UTF-8",
    headers={"Content-Language": "ru-RU"},
    auth_context={"type": "basic", "login": "user1", "password": "secret"},
    body={"message": "Успех"},
)
```

`endpoint`, `method` (`GET` / `POST` / `PUT` / `DELETE`), `content_type`, `headers`, `body` —
параметры HTTP-запроса. `auth_context` — один из `{"type": "noauth"}`,
`{"type": "basic", "login": ..., "password": ...}` или
`{"type": "oauth", "headerName": ..., "accessToken": ..., "tokenType": ...}`. Запросы этого
действия можно посмотреть через `get_trigger_logs`.

### CalculateFormula — вычислить значение

```python
TriggerAction(type="CalculateFormula", formula="now()+3M", result_field="start")
```

`formula` — математическое выражение, `result_field` — ключ или название поля, в которое
записывается результат.

### CreateIssue — создать задачу

```python
TriggerAction(
    type="CreateIssue",
    queue="TESTQUEUE",
    summary="Новая задача",
    field_templates={
        "followers": ["user1", "user2"],
        "assignee": "user3",
        "dueDate": "2024-10-31",
        "description": "Создана триггером {{currentDateTime.date}}",
        "priority": "critical",
        "type": "milestone",
        "tags": ["new task", "by trigger"],
    },
    link_with_initial_issue=True,
    from_robot=True,
)
```

`queue` — ключ очереди новой задачи, `summary` — её название, `field_templates` — остальные
поля (`followers`, `dueDate`, `description`, `assignee`, `priority`, `type`, `tags`),
`link_with_initial_issue` — связать ли новую задачу с той, что запустила триггер,
`from_robot` — создавать ли от имени робота. В таблицах официальной документации это действие
также встречается под именем `Event.create` — обе формы описывают одно и то же действие.

## Условия

Условие срабатывания триггера (`TriggerCondition`) — тоже плоский объект, дискриминированный
полем `type`. Условие либо логическая группа (`And` / `Or` с вложенными условиями в
`conditions`), либо элементарное условие; в последнем случае набор значимых полей зависит от
`type`. Ниже — по одному-двум примерам на каждую группу условий, полный список типов и полей,
для которых они применимы, — в docstring `TriggerCondition` и по ссылке источника.

Источник: https://yandex.ru/support/tracker/ru/api/queues/change-trigger-conditions

### Логическая группа

```python
TriggerCondition(
    type="Or",
    conditions=[
        TriggerCondition(type="CommentFullyMatchCondition", word="Need info"),
        TriggerCondition(type="CommentFullyMatchCondition", word="Нужна информация"),
    ],
)
```

Плоский список условий, переданный в `create_trigger(conditions=[...])`, эквивалентен
логическому И — оборачивать его в `And` не нужно. `Or` нужен явно, если сработать должно хотя
бы одно из условий, а группы можно вкладывать друг в друга.

### События

```python
TriggerCondition(type="Event.update")
```

`type` — `Event.update` (задача изменилась), `Event.create` (создана задача),
`Event.comment-create` (создан комментарий) или `CalculationFormulaWatch` (поля формулы
изменились). Без дополнительных параметров.

### Чеклист

```python
TriggerCondition(type="ChecklistDone")
```

Срабатывает, если выполнены все пункты чеклиста задачи.

### Текст комментария

```python
TriggerCondition(
    type="CommentNoneMatchCondition",
    words=["Version 0.1", "Version 0.2"],
    ignore_case=True,
    remove_markup=True,
    no_match_before=False,
)
```

`type` — один из `CommentFullyMatchCondition` / `CommentStringMatchCondition` /
`CommentStringNotMatchCondition` (принимают одну строку в `word`) или
`CommentAnyMatchCondition` / `CommentNoneMatchCondition` (принимают список строк; в примерах
официальной документации ключ называется `words`, в таблице параметров — `word`, поэтому
модель принимает оба и отправляет только заполненный). `ignore_case`, `remove_markup`,
`no_match_before` — необязательные флаги сравнения.

### Автор и тип комментария

```python
TriggerCondition(type="CommentAuthorNot", user="user1")
TriggerCondition(type="CommentMessageExternal")
```

`CommentAuthor` / `CommentAuthorNot` сравнивают `user` (логин или идентификатор) с автором
комментария; `CommentMessageInternal` / `CommentMessageExternal` проверяют, комментарий это в
Трекере или письмо на почту, — без дополнительных параметров.

### Действие со связью

```python
TriggerCondition(
    type="RemovedLinkCondition",
    relationship=["is parent task for", "is epic of"],
)
```

`type` — `CreatedLinkCondition` / `UpdatedLinkCondition` / `RemovedLinkCondition`,
`relationship` — типы связей, например `relates`, `is dependent by`, `depends on`,
`is subtask for`, `is parent task for`, `duplicates`, `is epic of`, `has epic`.

### Значение и состояние поля

```python
TriggerCondition(type="FieldEquals", field="priority", value="blocker")
TriggerCondition(type="FieldIsEmpty", field="assignee")
```

`FieldChangedCondition` (поле изменилось), `FieldEquals` / `FieldBecameEqual` (равно / стало
равно `value`) и `FieldEqualsString` (равно строке, для полей `description`, `emailFrom`,
`emailCreatedBy`) сравнивают значение поля; `FieldIsEmpty` / `FieldIsNotEmpty` /
`FieldBecameEmpty` / `FieldBecameNotEmpty` проверяют, заполнено ли поле. `field` — идентификатор
поля задачи (`status`, `priority`, `assignee`, `tags`, `deadline` и другие — полный список в
источнике).

### Дата

```python
TriggerCondition(
    type="DateGreaterCondition", field="createdAt", value="2023-10-28T09:25:00"
)
```

`type` — один из `DateEqualCondition`, `DateGreaterCondition`, `DateGreaterOrEqualCondition`,
`DateLessCondition`, `DateLessOrEqualCondition`; применимо к полям вроде `createdAt`,
`updatedAt`, `deadline`, `start`, `end`.

### Группы пользователей

```python
TriggerCondition(type="UserNotInGroups", field="createdBy", value=["1", "4"])
```

`UserInGroups` / `UserNotInGroups` сравнивают `field` (`createdBy`, `assignee`, `updatedBy`,
`resolvedBy`, `qaEngineer`) с одной или несколькими группами в `value`.

### Количество элементов

```python
TriggerCondition(type="Container.SizeGreaterOrEquals", field="votedBy", value=5)
TriggerCondition(
    type="ContainerContainsAll",
    field="followers",
    value=["user11", "user22"],
    no_match_before=True,
)
```

`Container.Size*` (`Equals`, `NotEquals`, `Greater`, `GreaterOrEquals`, `Less`,
`LessOrEquals`) сравнивают число элементов контейнерного поля (`tags`, `components`,
`followers`, `boards`, `sprint` и другие) с `value`; `ContainerContainsAll` /
`ContainerContainsAny` / `ContainerContainsNone` проверяют, входят ли элементы `value` в
поле, `no_match_before` — было ли это уже так до изменения.

### Числовые значения

```python
TriggerCondition(type="LessOrEqualCondition", field="storyPoints", value=5)
```

`GreaterCondition`, `GreaterOrEqualCondition`, `LessCondition`, `LessOrEqualCondition` и их
формы «стало …» (`BecameGreaterCondition` и так далее) сравнивают числовые поля (`votes`,
`estimation`, `spent`, `storyPoints` и другие) с `value`.

### Строковые значения

```python
TriggerCondition(
    type="ContainsNoneOfStrings",
    field="description",
    value=["Test task", "12345"],
    ignore_case=True,
)
```

`FieldEqualsString`, `ContainsAnyOfStrings`, `ContainsNoneOfStrings` сравнивают текстовые
поля (`key`, `summary`, `description`, `emailFrom`, `emailCreatedBy`) со строкой или списком
строк в `value`, `ignore_case` — без учёта регистра.

## Модели

### `Trigger`

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на триггер (ключ `self`). |
| `id` | `str` | Идентификатор триггера. |
| `queue` | `Queue` | Очередь, в которой создан триггер. |
| `name` | `str` | Название триггера. |
| `order` | `str` | Вес триггера; влияет на порядок отображения в интерфейсе. |
| `actions` | `list[TriggerAction]` | Действия триггера. |
| `conditions` | `list[TriggerCondition]` | Условия срабатывания триггера. |
| `version` | `int` | Версия триггера, увеличивается при каждом изменении. |
| `active` | `bool` | Активен ли триггер. |

### `TriggerAction`

Плоский объект, набор значимых полей зависит от `type` — см. раздел «Действия» выше.

| Поле | Тип | Описание |
| --- | --- | --- |
| `type` | `str` | Тип действия. |
| `id` | `str \| None` | Идентификатор действия (только в ответе). |
| `status` | `Status \| str \| dict \| None` | `Transition`: статус задачи. |
| `formula` | `str \| None` | `CalculateFormula`: математическое выражение. |
| `result_field` | `str \| None` | `CalculateFormula`: поле для результата. |
| `update` | `dict \| None` | `Update`: изменяемые поля задачи. |
| `queue` | `Queue \| str \| dict \| None` | `Move` / `CreateIssue`: ключ целевой очереди. |
| `text` | `str \| None` | `CreateComment`: текст комментария. |
| `from_robot` | `bool \| None` | `CreateComment` / `CreateIssue`: действовать от имени робота. |
| `checklist_items` | `list[dict] \| None` | `CreateChecklist`: пункты чеклиста. |
| `endpoint` | `str \| None` | `Webhook`: адрес запроса. |
| `auth_context` | `dict \| None` | `Webhook`: данные авторизации. |
| `method` | `str \| None` | `Webhook`: HTTP-метод. |
| `content_type` | `str \| None` | `Webhook`: тип содержимого запроса. |
| `headers` | `dict[str, str] \| None` | `Webhook`: заголовки запроса. |
| `body` | `dict \| str \| None` | `Webhook`: тело запроса. |
| `summary` | `str \| None` | `CreateIssue`: название создаваемой задачи. |
| `field_templates` | `dict \| None` | `CreateIssue`: остальные поля создаваемой задачи. |
| `link_with_initial_issue` | `bool \| None` | `CreateIssue`: связать с задачей, запустившей триггер. |

### `TriggerCondition`

Плоский объект, набор значимых полей зависит от `type` — см. раздел «Условия» выше.

| Поле | Тип | Описание |
| --- | --- | --- |
| `type` | `str` | Тип условия (или `And` / `Or` для логической группы). |
| `conditions` | `list[TriggerCondition] \| None` | Вложенные условия группы `And` / `Or`. |
| `field` | `str \| None` | Идентификатор поля задачи. |
| `value` | `Any` | Сравниваемое значение: строка, число или список. |
| `word` | `str \| list[str] \| None` | Фрагмент(ы) комментария для `Comment*Condition`. |
| `words` | `str \| list[str] \| None` | То же самое, что `word` (см. раздел «Текст комментария»). |
| `user` | `str \| None` | Автор комментария (`CommentAuthor[Not]`). |
| `relationship` | `str \| list[str] \| None` | Типы связей (`*LinkCondition`). |
| `ignore_case` | `bool \| None` | Не учитывать регистр при сравнении текста. |
| `remove_markup` | `bool \| None` | Не учитывать разметку при сравнении текста. |
| `no_match_before` | `bool \| None` | Значение не совпадало до изменения. |

### `TriggerWebhookLog`

Одна запись лога действия `Webhook`, возвращается `get_trigger_logs`. Обязательно только
`id` — остальные поля документация приводит лишь на одном успешном примере, поэтому все они
необязательны.

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | `str` | Идентификатор запуска триггера. |
| `start_time` | `datetime \| None` | Время начала запуска. |
| `end_time` | `datetime \| None` | Время завершения запуска. |
| `duration` | `int \| None` | Длительность запуска в миллисекундах. |
| `trigger_id` | `str \| None` | Идентификатор триггера. |
| `action_id` | `str \| None` | Идентификатор действия внутри триггера. |
| `issue_id` | `str \| None` | Идентификатор задачи, в которой сработал триггер. |
| `request` | `TriggerWebhookLogRequest \| None` | Отправленный HTTP-запрос. |
| `response` | `TriggerWebhookLogResponse \| None` | Полученный HTTP-ответ. |

### `TriggerWebhookLogRequest`

| Поле | Тип | Описание |
| --- | --- | --- |
| `method` | `str \| None` | HTTP-метод запроса. |
| `endpoint` | `str \| None` | Адрес, на который отправлен запрос. |
| `headers` | `dict[str, str] \| None` | Заголовки запроса (значения маскируются API). |
| `body` | `str \| None` | Тело запроса. |
| `webhook_auth_context` | `dict \| None` | Данные авторизации; документирован только `type`, сами учётные данные маскируются. |

### `TriggerWebhookLogResponse`

| Поле | Тип | Описание |
| --- | --- | --- |
| `headers` | `dict[str, str] \| None` | Заголовки ответа (значения маскируются API). |
| `status_code` | `int \| None` | HTTP-код ответа. |

## Типичный сценарий

Найти триггер по названию, посмотреть его условия и действия, затем отключить его:

```python
trigger = None
async for candidate in tracker.iter_triggers("DESIGN", per_page=50):
    if candidate.name == "TriggerName":
        trigger = candidate
        break

if trigger is not None:
    for action in trigger.actions:
        print(action.type, action.status)

    trigger = await tracker.update_trigger(
        "DESIGN",
        trigger_id=trigger.id,
        version=trigger.version,
        active=False,
    )
```
