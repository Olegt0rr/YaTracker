# Рабочие процессы

Рабочий процесс (workflow) описывает жизненный цикл задачи: набор статусов, в которых она
может находиться (`steps`), и переходов между ними (`actions`). Рабочий процесс либо привязан
к конкретной очереди, либо является общим для всей организации — общий процесс можно назначить
типам задач в настройках `issueTypesConfig` очереди (см. `docs/queues.md`).

Все методы этого раздела работают с эндпоинтом `/v3/workflows`, а не с `/v3/queues/...`, хотя
справочник API документирует их в разделе про очереди. `get_workflows()` не принимает очередь —
запрос всегда организационный и возвращает все рабочие процессы организации; чтобы получить
процессы одной очереди, отфильтруйте результат по `FullWorkflow.queue`.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с рабочими процессами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Получение

### get_workflows

```python
async def get_workflows(self) -> list[FullWorkflow]: ...
```

Возвращает все рабочие процессы организации, кроме удалённых.

```python
workflows = await tracker.get_workflows()

for workflow in workflows:
    print(workflow.id, workflow.name)

# рабочие процессы конкретной очереди
design_workflows = [w for w in workflows if w.queue and w.queue.key == "DESIGN"]
```

Источник: https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflows

### get_workflow

```python
async def get_workflow(self, workflow_id: str) -> FullWorkflow: ...
```

Возвращает один рабочий процесс по идентификатору.

```python
workflow = await tracker.get_workflow("W21")

print(workflow.name, workflow.version)
for step in workflow.steps:
    print(step.status.key, [a.id for a in step.actions or []])
```

1. `workflow_id` — идентификатор рабочего процесса, например `W21`.

Источник: https://yandex.ru/support/tracker/ru/api/queues/workflows/get-workflow

## Создание

### create_workflow

```python
async def create_workflow(
    self,
    name: str,
    initial_action: dict[str, Any],
    steps: Sequence[dict[str, Any]],
    *,
    id_: str | None = None,
    queue: str | int | dict[str, Any] | None = None,
    type_: str | None = None,
    issue_type_resolutions: Sequence[dict[str, Any]] | None = None,
) -> FullWorkflow: ...
```

Создаёт новый рабочий процесс. Блоки `initial_action`, `steps` и `issue_type_resolutions`
передаются как обычные словари в том виде, в каком их ожидает API (`camelCase`, вложенные ключи
уходят в запрос как есть) — `yatracker` не оборачивает их в отдельные модели запроса.

```python
workflow = await tracker.create_workflow(
    name="Design",
    queue="DESIGN",
    type_="VISUAL",
    initial_action={
        "id": "open",
        "name": {"ru": "Открыть", "en": "Open"},
        "target": "open",
    },
    steps=[
        {
            "status": "open",
            "description": {"ru": "Задача открыта", "en": "Issue is open"},
            "actions": [
                {
                    "id": "inProgress",
                    "name": {"ru": "Взять в работу", "en": "Start progress"},
                    "description": {
                        "ru": "Перевести задачу в работу",
                        "en": "Move issue to in progress",
                    },
                    "target": "inProgress",
                },
            ],
        },
        {
            "status": "inProgress",
            "description": {"ru": "Задача в работе", "en": "Issue is in progress"},
            "actions": [
                {
                    "id": "close",
                    "name": {"ru": "Закрыть", "en": "Close"},
                    "description": {"ru": "Закрыть задачу", "en": "Close the issue"},
                    "target": "closed",
                },
            ],
        },
        {
            "status": "closed",
            "description": {"ru": "Задача закрыта", "en": "Issue is closed"},
            "actions": [],
        },
    ],
    issue_type_resolutions=[
        {"issueType": "task", "resolutions": ["wontFix", "fixed"]},
    ],
)
```

1. `name` — название рабочего процесса (обязательное поле).
2. `initial_action` — начальное действие: задаёт статус, в который попадает задача при
   создании (обязательное поле).
3. `steps` — шаги рабочего процесса: каждый шаг соответствует статусу и содержит доступные из
   него переходы (обязательное поле).
4. `id_` — идентификатор рабочего процесса, отправляется как `id`. Завершающее
   подчёркивание нужно, чтобы имя параметра не конфликтовало со встроенным `id`
   (как и у `type_`). Если не передать, API сгенерирует идентификатор вида `W...`.
5. `queue` — очередь, к которой привязывается рабочий процесс. Если не передать, создаётся
   общий (organization-wide) процесс, который затем можно назначить типам задач в настройках
   очереди; создавать общие процессы могут только пользователи с соответствующими правами.
6. `type_` — тип рабочего процесса, отправляется как `type`. Единственное значение —
   `"VISUAL"` (в ответе API возвращает `"visual"`).
7. `issue_type_resolutions` — резолюции, доступные для типов задач, например
   `[{"issueType": "task", "resolutions": ["fixed"]}]`.

#### Ссылка на статус: `status` и `target`

И `status` шага, и `target` действия — это ссылка на статус, которую можно указать тремя
способами:

* ключом статуса — строкой (`"open"`, `"inProgress"`);
* идентификатором статуса — числом;
* объектом с одним из ключей: `{"key": "open"}`, `{"id": 3}` или `{"name": "В работе"}`.

#### Локализованные названия

`name` действия (в `initial_action` и внутри `actions`) и `description` шага/действия — это
объекты с локализациями, например `{"ru": "Открыть", "en": "Open"}`. `name` действия — поле
обязательное, `description` — нет.

#### Поля объекта step

* `status` — статус шага (обязательное поле, см. выше).
* `description` — описание шага, локализованный объект.
* `actions` — переходы, доступные из этого статуса.
* `metaAction` — метадействие шага, которое выполняется автоматически; передаётся как
  `{"metaAction": {...}}`, отдельного параметра метода под него нет — включите его в словарь
  соответствующего элемента `steps`.
* `statusType` — тип статуса: `NEW`, `IN_PROGRESS`, `PAUSED`, `DONE` или `CANCELLED`.

#### Поля объекта action

* `id` — идентификатор действия.
* `name` — название действия, локализованный объект (обязательное поле).
* `description` — описание действия, локализованный объект.
* `target` — целевой статус перехода (обязательное поле, см. выше).
* `screen` — экран перехода с полями, которые можно заполнить при выполнении действия.
* `conditions` — условия выполнения действия.
* `functions` — функции, выполняемые при переходе.

Источник: https://yandex.ru/support/tracker/ru/api/queues/workflows/post-workflow

## Изменение

### update_workflow

```python
async def update_workflow(
    self,
    workflow_id: str,
    version: str | int,
    *,
    name: str | None = None,
    type_: str | None = None,
    initial_action: dict[str, Any] | None = None,
    steps: Sequence[dict[str, Any]] | None = None,
    issue_type_resolutions: Sequence[dict[str, Any]] | None = None,
) -> FullWorkflow: ...
```

Изменяет рабочий процесс. Блоки `initial_action`, `steps` и `issue_type_resolutions` имеют тот
же формат, что и в `create_workflow`.

```python
workflow = await tracker.update_workflow(
    "W21",
    version=workflow.version,
    name="QA process",
    steps=[
        {
            "status": "new",
            "actions": [
                {
                    "id": "needInfo",
                    "name": {
                        "ru": "Отправить на тестирование",
                        "en": "Send to testing",
                    },
                    "target": "testing",
                },
            ],
        },
        {
            "status": "testing",
            "actions": [
                {
                    "id": "resolved",
                    "name": {"ru": "Завершить", "en": "Resolve"},
                    "target": "resolved",
                }
            ],
        },
        {"status": "resolved", "actions": []},
    ],
)
```

1. `workflow_id` — идентификатор рабочего процесса.
2. `version` — текущая версия рабочего процесса (`workflow.version`), уходит в query-параметр
   `version`.
3. `name`, `type_`, `initial_action`, `issue_type_resolutions` — необязательные поля для
   изменения. `None` означает «не менять».
4. `steps` — новый набор шагов. **Важно:** `steps` заменяет весь граф целиком, поэтому передайте
   все шаги рабочего процесса, а не только изменённые — иначе непереданные шаги пропадут. Чтобы
   поменять один переход, не переписывая весь граф, используйте `update_workflow_action`.

!!! warning "Версия обязательна"

    Справочник API допускает передавать версию рабочего процесса как в query-параметре
    `version`, так и в заголовке `If-Match`; `yatracker` всегда использует query-параметр.
    Если версия устарела — рабочий процесс успели изменить параллельно — API отвечает
    `412 Precondition Failed`, и библиотека бросает `PreconditionFailedError` (подробнее в
    разделе [«Обработка ошибок»](errors.md)). В этом случае перечитайте рабочий процесс
    (`get_workflow`) и повторите запрос с актуальной версией.

Источник: https://yandex.ru/support/tracker/ru/api/queues/workflows/patch-workflow

### update_workflow_action

```python
async def update_workflow_action(
    self,
    workflow_id: str,
    status: str,
    action_id: str,
    version: str | int,
    *,
    new_id: str | None = None,
    name: dict[str, str] | None = None,
    description: dict[str, str] | None = None,
    target: str | int | dict[str, Any] | None = None,
    screen: dict[str, Any] | None = None,
    conditions: Sequence[dict[str, Any]] | None = None,
    functions: Sequence[dict[str, Any]] | None = None,
) -> FullWorkflow: ...
```

Изменяет один переход (`action`) внутри шага рабочего процесса — точечная альтернатива
пересылке всего `steps` через `update_workflow`.

```python
workflow = await tracker.update_workflow_action(
    "W21",
    status="inProgress",
    action_id="close",
    version=workflow.version,
    name={"ru": "Завершить", "en": "Complete"},
    description={
        "ru": "Перевести задачу в статус «Закрыт»",
        "en": "Move issue to Closed status",
    },
    target="closed",
)
```

1. `workflow_id` — идентификатор рабочего процесса.
2. `status` — ключ статуса (шага), в котором находится действие, например `inProgress`.
3. `action_id` — идентификатор действия внутри шага, например `close`.
4. `version` — текущая версия рабочего процесса, уходит в query-параметр `version`.
5. `new_id` — новый идентификатор действия, отправляется как `id`.
6. `name` — новое название действия, локализованный объект.
7. `description` — новое описание действия, локализованный объект.
8. `target` — новый целевой статус: ключ (строка), идентификатор (число) или объект
   (`{"key": ...}` / `{"id": ...}` / `{"name": ...}`).
9. `screen`, `conditions`, `functions` — экран перехода, условия и функции, как в
   `create_workflow`.

Поля, оставленные `None`, не отправляются, то есть не меняются. Метод возвращает весь
обновлённый рабочий процесс, а не только изменённое действие.

!!! warning "Версия обязательна"

    Как и `update_workflow`, метод передаёт версию через query-параметр `version` и требует
    актуальную версию рабочего процесса — при конфликте API отвечает ошибкой конфликта, и
    `yatracker` бросает `PreconditionFailedError`. Обратите внимание: справочник этого запроса
    называет код ошибки конфликта `409`, тогда как для `PATCH /workflows/<id>` он же
    задокументирован как `412` — само поведение (нужно перечитать объект и повторить запрос
    с новой версией) одинаковое.

Источник: https://yandex.ru/support/tracker/ru/api/queues/workflows/patch-workflow-action

## Удаление

### delete_workflow

```python
async def delete_workflow(self, workflow_id: str) -> bool: ...
```

Удаляет рабочий процесс. Возвращает `True` при успехе.

```python
await tracker.delete_workflow("W21")
```

1. `workflow_id` — идентификатор рабочего процесса.

Источник: https://yandex.ru/support/tracker/ru/api/queues/workflows/delete-workflow

## Модели

### FullWorkflow

Полный объект рабочего процесса, который возвращают все методы `/workflows`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на рабочий процесс. |
| `id` | `str` | Идентификатор рабочего процесса, например `W21`. |
| `name` | `str` | Название рабочего процесса. |
| `version` | `int` | Версия рабочего процесса. Каждое изменение увеличивает номер версии. |
| `steps` | `list[WorkflowStep]` | Шаги рабочего процесса. |
| `initial_action` | `WorkflowAction \| None` | Начальное действие — статус, который получает задача при создании. |
| `queue` | `Queue \| None` | Очередь, к которой привязан рабочий процесс. Не возвращается для общего процесса. |
| `created` | `datetime \| None` | Дата и время создания. |
| `updated` | `datetime \| None` | Дата и время последнего изменения. |
| `created_by` | `User \| None` | Автор рабочего процесса. |
| `updated_by` | `User \| None` | Пользователь, последним изменивший рабочий процесс. |
| `deleted` | `bool \| None` | Признак удалённого рабочего процесса. |
| `type` | `str \| None` | Тип рабочего процесса. Сейчас единственное значение — `"visual"`; у созданных ранее процессов поле может отсутствовать. |

### WorkflowStep

Шаг рабочего процесса: статус и доступные из него переходы.

| Поле | Тип | Описание |
| --- | --- | --- |
| `status` | `Status` | Статус шага. |
| `actions` | `list[WorkflowAction] \| None` | Переходы, доступные из этого статуса. API не возвращает ключ для терминального шага, поэтому здесь `None`. |

### WorkflowAction

Действие (переход) шага рабочего процесса или начальное действие (`FullWorkflow.initial_action`).

| Поле | Тип | Описание |
| --- | --- | --- |
| `id` | `str` | Идентификатор действия. |
| `name` | `str` | Название действия. |
| `target` | `Status` | Статус, в который переводит действие. |

!!! tip "Формат ответа проще формата запроса"

    В ответе `name` действия — обычная строка, а не локализованный объект: API возвращает
    название на языке интерфейса. `description`, `screen`, `conditions` и `functions`,
    которые можно передать при создании и изменении действия, справочник не включает в
    формат ответа — в модели их поэтому нет.

### Workflow

Короткая ссылка на рабочий процесс, встроенная в `issueTypesConfig` очереди (`docs/queues.md`),
не имеющая отношения к ответам `/workflows`. Импортируется из `yatracker.types.workflow`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на рабочий процесс. |
| `id` | `str` | Идентификатор рабочего процесса. |
| `display` | `str` | Отображаемое название. |
| `key` | `str \| None` | Ключ рабочего процесса. Не возвращается внутри `issueTypesConfig`. |

## Типичный сценарий

Найти общий рабочий процесс по названию, посмотреть его шаги и переходы, затем точечно
поменять один переход, не трогая остальной граф:

```python
workflows = await tracker.get_workflows()
workflow = next(w for w in workflows if w.name == "Design")

for step in workflow.steps:
    print(step.status.key, [action.id for action in step.actions or []])

workflow = await tracker.update_workflow_action(
    workflow.id,
    status="inProgress",
    action_id="close",
    version=workflow.version,
    target="closed",
)
```
