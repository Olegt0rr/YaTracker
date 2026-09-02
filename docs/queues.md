# Работа с очередями

Очередь (queue) в Яндекс Трекере — это контейнер для задач: у неё есть ключ (например, `WRITERS`),
руководитель, набор допустимых типов задач и их жизненные циклы (workflow). `YaTracker`
предоставляет асинхронные методы для получения, создания, удаления и восстановления очередей,
а также для работы с их версиями, обязательными полями и тегами.

Полное описание сущности «очередь» и её полей смотрите в официальной документации:
https://yandex.cloud/ru/docs/tracker/about-api

!!! note "Обратите внимание"

    Как и в остальных разделах, здесь предполагается, что вызовы происходят внутри корутины —
    примеры для краткости приводятся без обёртки в `async def`.

## Получение очереди

### get_queue

```python
async def get_queue(
    self,
    queue_id: str | int,
    _type: type[QueueT_co | FullQueue] = FullQueue,
    *,
    expand: str | None = None,
) -> QueueT_co | FullQueue: ...
```

Возвращает параметры одной очереди по её ключу или идентификатору.

```python
queue = await tracker.get_queue("WRITERS")

print(queue.key, queue.name, queue.lead.display)
```

Часть полей (`team_users`, `issue_types`, `versions`, `components`, `workflows`,
`issue_types_config`) Трекер возвращает только по запросу — через параметр `expand`:

```python
queue = await tracker.get_queue("WRITERS", expand="all")

print(queue.issue_types_config)
```

1. `expand` — один из `all`, `projects`, `components`, `versions`, `types`, `team`,
   `workflows`, `fields`, `issueTypesConfig`.

!!! note "Собственная модель очереди"

    Как и для задач (см. [«Работа с пользовательскими полями»](custom_fields.md)), можно передать
    параметр `_type` с наследником `FullQueue`, чтобы получить в ответе свою модель с
    дополнительными полями.

    ```python
    from yatracker.types import FullQueue


    class MyQueue(FullQueue):
        my_extra_field: str | None = None


    queue = await tracker.get_queue("WRITERS", MyQueue)
    ```

### get_queues

```python
async def get_queues(
    self,
    expand: str | None = None,
    per_page: int | None = None,
    _type: type[FullQueue | QueueT_co] = FullQueue,
) -> list[FullQueue] | list[QueueT_co]: ...
```

Возвращает список всех доступных очередей.

```python
queues = await tracker.get_queues()

for queue in queues:
    print(queue.key)
```

Если очередей больше 50, используйте пагинацию через `per_page`:

```python
queues = await tracker.get_queues(per_page=100)
```

## Создание, удаление и восстановление очереди

### create_queue

```python
async def create_queue(
    self,
    key: str,
    name: str,
    lead: str,
    default_type: str,
    default_priority: str,
    issue_types_config: list[IssueTypeConfig],
    _type: type[QueueT_co | FullQueue] = FullQueue,
) -> QueueT_co | FullQueue: ...
```

Создаёт новую очередь. Обратите внимание: `lead`, `default_type` и `default_priority`
здесь — это **строки** (логин руководителя и ключи типа задачи/приоритета по умолчанию),
а не объекты `User`, `IssueType` или `Priority`, которые возвращаются в ответе.

```python
from yatracker.types import IssueTypeConfig
from yatracker.types.issue_type import IssueType
from yatracker.types.workflow import Workflow
from yatracker.types.resolution import Resolution

issue_types_config = [
    IssueTypeConfig(
        issue_type=IssueType(
            url="https://api.tracker.yandex.net/v3/issuetypes/1",
            id="1",
            key="task",
            display="Задача",
        ),
        workflow=Workflow(
            url="https://api.tracker.yandex.net/v3/workflows/dev",
            id="dev",
            display="dev",
        ),
        resolutions=[
            Resolution(
                url="https://api.tracker.yandex.net/v3/resolutions/1",
                id="1",
                key="fixed",
                display="Исправлено",
            ),
        ],
    ),
]

queue = await tracker.create_queue(
    key="WRITERS",
    name="Писатели",
    lead="login",
    default_type="task",
    default_priority="normal",
    issue_types_config=issue_types_config,
)
```

!!! note "Несоответствие в текущей реализации"

    `Workflow` и `Resolution` не входят в публичный `yatracker.types.__all__`, поэтому их нужно
    импортировать напрямую из подмодулей (`yatracker.types.workflow`, `yatracker.types.resolution`),
    как показано выше.

    Кроме того, тип параметра `issue_types_config: list[IssueTypeConfig]` требует полностью
    заполненных объектов `IssueTypeConfig` (со вложенными `IssueType`, `Workflow`, `Resolution`,
    у каждого из которых обязательны `url`/`id`/`display`) — то есть повторяет форму *ответа*
    `GET /queues/{id}?expand=issueTypesConfig`, а не минимальный формат тела запроса на создание
    очереди, описанный в официальной документации:
    https://yandex.cloud/ru/docs/tracker/concepts/queues/create-queue

    Перед использованием в проде свяжитесь с реальным API и убедитесь, какая форма
    `issueTypesConfig` ожидается — при необходимости соберите тестовый запрос и проверьте
    фактическое тело, отправленное клиентом.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/queues/create-queue

### delete_queue

```python
async def delete_queue(self, queue_id: str | int) -> bool: ...
```

Удаляет очередь. Возвращает `True` при успехе.

```python
await tracker.delete_queue("WRITERS")
```

Источник: https://yandex.cloud/ru/docs/tracker/concepts/queues/delete-queue

### restore_queue

```python
async def restore_queue(
    self,
    queue_id: str | int,
    _type: type[QueueT_co | FullQueue] = FullQueue,
) -> QueueT_co | FullQueue: ...
```

Восстанавливает ранее удалённую очередь.

```python
queue = await tracker.restore_queue("WRITERS")
```

Источник: https://yandex.cloud/ru/docs/tracker/concepts/queues/restore-queue

## Версии очереди

### get_queue_versions

```python
async def get_queue_versions(
    self,
    queue_id: str | int,
    _type: type[QueueVersion | QueueVersionT_co] = QueueVersion,
) -> list[QueueVersion] | list[QueueVersionT_co]: ...
```

Возвращает список версий (релизов) очереди — например, `1.0`, `1.1` и так далее.

```python
versions = await tracker.get_queue_versions("WRITERS")

for version in versions:
    print(version.name, version.released, version.archived)
```

Источник: https://yandex.cloud/ru/docs/tracker/concepts/queues/get-versions

## Обязательные поля очереди

### get_queue_fields

```python
async def get_queue_fields(
    self,
    queue_id: str | int,
    _type: type[QueueField | QueueFieldT_co] = QueueField,
) -> list[QueueField] | list[QueueFieldT_co]: ...
```

Возвращает список полей, обязательных при создании задачи в данной очереди —
как стандартных, так и локальных.

```python
fields = await tracker.get_queue_fields("WRITERS")

for field in fields:
    print(field.name, field.field_schema.type, field.field_schema.required)
```

`field.field_schema` (в API — `schema`) описывает тип значения поля (`type`), обязательность
(`required`) и, для составных типов, тип элементов коллекции (`items`).

Источник: https://yandex.cloud/ru/docs/tracker/concepts/queues/get-fields

## Теги очереди

### delete_tag_from_queue

```python
async def delete_tag_from_queue(
    self,
    queue_id: str | int,
    tag_name: str,
) -> bool: ...
```

Удаляет тег из очереди. Возвращает `True` при успехе.

```python
await tracker.delete_tag_from_queue("WRITERS", "устаревший-тег")
```

Источник: https://yandex.cloud/ru/docs/tracker/concepts/queues/delete-tag
