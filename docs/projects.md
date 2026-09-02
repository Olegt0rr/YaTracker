# Проекты (устаревший API)

Проект (project) в этом API — это набор очередей с владельцем (`lead`), статусом и парой
дат. Такие проекты живут по адресу `/projects`, у них есть версия для защиты от конфликтов
и статусы `DRAFT`, `IN_PROGRESS`, `LAUNCHED` и `POSTPONED`. `yatracker` предоставляет
методы для получения списка проектов, их создания, изменения и удаления, а также для
получения очередей проекта.

!!! warning "Это старый API проектов"

    Проекты, которые вы видите в текущем интерфейсе Трекера (вместе с портфелями и целями),
    — это не эти проекты. Они относятся к API сущностей и описаны на странице
    [«Проекты, портфели и цели»](entities.md). Запросы `/projects` остались от прежней
    версии Трекера: используйте их, если работаете со старыми проектами, привязанными
    к очередям.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с проектами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/projects/get-projects

!!! note "Параметр `queues`"

    В справочнике API параметр `queues` описан как строка (ключ очереди), а официальная
    библиотека `yandex_tracker_client` объявляет его списком. `yatracker` отправляет то,
    что вы передали: строка уходит строкой, любая последовательность строк — JSON-массивом.
    Если сомневаетесь, передавайте список ключей очередей.

## Получение проектов

### get_projects

```python
async def get_projects(
    self,
    *,
    expand: str | None = None,
    per_page: int | None = None,
    page: int | None = None,
) -> list[Project]: ...
```

Возвращает список всех проектов организации.

```python
projects = await tracker.get_projects()

for project in projects:
    print(project.id, project.name, project.status)
```

1. `expand` — дополнительные поля в ответе. Единственное документированное значение —
   `"queues"`: очереди проекта окажутся в поле `project.queues`.
2. `per_page` — количество проектов на странице (по умолчанию 50).
3. `page` — номер страницы (по умолчанию 1).

```python
projects = await tracker.get_projects(expand="queues")
```

Как и все списочные запросы, ответ разбит на страницы по 50 объектов — остальные
страницы забираются через `per_page` и `page`:

```python
projects = await tracker.get_projects(per_page=100, page=2)
```

!!! note "Поле `project.queues`"

    Формат очередей в ответе на `expand="queues"` в документации не описан, поэтому
    `yatracker` декодирует их в «терпимый» объект `ProjectQueueRef`: обязательны только
    `url` (`self`) и `id`, а `key`, `display` и `name` необязательны. Так разберётся и
    короткая ссылка на очередь, и полный объект очереди. Если нужны полные объекты
    `FullQueue`, используйте `get_project_queues`.

Источник: https://yandex.ru/support/tracker/ru/api/projects/get-projects

### get_project

```python
async def get_project(
    self,
    project_id: str | int,
    *,
    expand: str | None = None,
) -> Project: ...
```

Возвращает параметры одного проекта.

```python
project = await tracker.get_project(9)

print(project.name, project.start_date, project.end_date)
```

1. `project_id` — идентификатор проекта.
2. `expand` — дополнительные поля в ответе, например `"queues"`.

Поля `start_date` и `end_date` приходят в виде `datetime.date`, `status` — в нижнем
регистре (`launched`), хотя в запросах статус передаётся в верхнем (`LAUNCHED`).
Поле `description` в интерфейсе Трекера не отображается.

Источник: https://yandex.ru/support/tracker/ru/api/projects/get-project

## Создание проекта

### create_project

```python
async def create_project(
    self,
    name: str,
    queues: str | Sequence[str],
    *,
    description: str | None = None,
    lead: str | int | None = None,
    status: str | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
) -> Project: ...
```

Создаёт новый проект.

```python
from datetime import date

project = await tracker.create_project(
    name="Project",
    queues=["WRITERS"],
    lead="login",
    status="IN_PROGRESS",
    start_date=date(2020, 11, 16),
    end_date="2020-12-16",
)
```

1. `name` — название проекта. Оно же становится ключом проекта (`project.key`).
2. `queues` — очереди проекта: ключ очереди строкой или последовательность ключей.
   Обязательный параметр.
3. `description` — необязательное описание проекта.
4. `lead` — идентификатор или логин владельца проекта (строка или число, а не объект
   `User`).
5. `status` — статус проекта: `DRAFT`, `IN_PROGRESS`, `LAUNCHED` или `POSTPONED`.
6. `start_date` — дата начала: объект `datetime.date` или строка `YYYY-MM-DD`.
7. `end_date` — дата окончания в том же формате.

Источник: https://yandex.ru/support/tracker/ru/api/projects/create-project

## Изменение проекта

### update_project

```python
async def update_project(
    self,
    project_id: str | int,
    version: str | int,
    queues: str | Sequence[str],
    *,
    name: str | None = None,
    description: str | None = None,
    lead: str | int | None = None,
    status: str | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    expand: str | None = None,
) -> Project: ...
```

Изменяет существующий проект запросом `PUT` (не `PATCH`).

```python
project = await tracker.update_project(
    project_id=project.id,
    version=project.version,
    queues=["WRITERS"],
    status="LAUNCHED",
)
```

1. `project_id` — идентификатор проекта.
2. `version` — текущая версия проекта: защита от конфликтов параллельного изменения.
   Если передать неактуальную версию, Трекер ответит `409 Conflict` — см. про
   `AlreadyExistsError` в разделе [«Обработка ошибок»](errors.md).
3. `queues` — очереди проекта. Обязательный параметр **в каждом** запросе на изменение:
   список очередей проекта заменяется переданным, поэтому передавайте текущие очереди,
   даже если меняете только статус или даты.
4. `name`, `description`, `lead`, `status`, `start_date`, `end_date` — необязательные поля
   для изменения, как в `create_project`. Значение `None` означает «не менять»: такие поля
   в запрос не попадают, поэтому очистить описание или снять владельца через `None` нельзя.
5. `expand` — дополнительные поля в ответе, например `"queues"`.

В ответе версия проекта увеличивается на единицу.

Источник: https://yandex.ru/support/tracker/ru/api/projects/update-project

## Удаление проекта

### delete_project

```python
async def delete_project(self, project_id: str | int) -> bool: ...
```

Удаляет проект. Очереди, входившие в проект, при этом не удаляются.

```python
await tracker.delete_project(9)
```

1. `project_id` — идентификатор проекта.

Метод возвращает `True` при успешном удалении: Трекер отвечает пустым телом.

Источник: https://yandex.ru/support/tracker/ru/api/projects/delete-project

## Очереди проекта

### get_project_queues

```python
async def get_project_queues(
    self,
    project_id: str | int,
    _type: type[QueueT_co] = FullQueue,
    *,
    expand: str | None = None,
    per_page: int | None = None,
    page: int | None = None,
) -> list[FullQueue]: ...
```

Возвращает очереди проекта — полные объекты `FullQueue`, как в `get_queue`
(см. [«Работа с очередями»](queues.md)).

```python
queues = await tracker.get_project_queues(9)

for queue in queues:
    print(queue.key, queue.name)
```

1. `project_id` — идентификатор проекта.
2. `_type` — собственный наследник `FullQueue`, если вы расширили модель очереди
   локальными полями (см. [«Работа с пользовательскими полями»](custom_fields.md)).
3. `expand` — дополнительные поля очередей: `all`, `projects`, `components`, `versions`,
   `types`, `team`, `workflows`, `fields`, `notification_fields`, `issue_types_config`,
   `enabled_feaures`, `signature_settings`.
4. `per_page` — количество очередей на странице (по умолчанию 50).
5. `page` — номер страницы (по умолчанию 1).

Как и все списочные запросы, ответ разбит на страницы по 50 объектов:

```python
queues = await tracker.get_project_queues(9, per_page=100, page=2)
```

Свою модель очереди — наследника `FullQueue` с локальными полями — можно передать
вторым позиционным параметром:

```python
from yatracker.types import FullQueue, field


class MyQueue(FullQueue):
    user_id: int | None = field(default=None, name="64a5--userId")


queues = await tracker.get_project_queues(9, MyQueue)
```

!!! note "Значения `expand` записаны в snake_case"

    Это значения с официальной страницы `get-project-queues` (включая опечатку
    `enabled_feaures`). При этом `get_queue` документирует то же самое поле как
    `issueTypesConfig` — если форма в snake_case не даёт эффекта, попробуйте вариант
    в camelCase.

Источник: https://yandex.ru/support/tracker/ru/api/projects/get-project-queues

## Методы объекта `Project`

У полученного из Трекера объекта `Project` есть пара сокращений:

```python
project = await tracker.get_project(9)

queues = await project.get_queues()
await project.delete()
```

1. `get_queues(_type=FullQueue, *, expand=None, per_page=None, page=None)` — то же, что
   `get_project_queues(project.id, ...)`, со всеми теми же параметрами.
2. `delete()` — то же, что `delete_project(project.id)`; возвращает `True`.

## Типичный сценарий

Найти проект по имени, добавить в него очередь и запустить его, передав актуальную версию
и полный список очередей:

```python
projects = await tracker.get_projects(expand="queues")
project = next(p for p in projects if p.name == "Project")

queues = [queue.key for queue in await project.get_queues()]

project = await tracker.update_project(
    project_id=project.id,
    version=project.version,
    queues=[*queues, "WRITERS"],
    status="LAUNCHED",
)
```
