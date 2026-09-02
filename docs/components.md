# Компоненты

Компонент (component) — это способ группировать задачи внутри очереди, например по модулю
или подсистеме. У компонента есть название, очередь, к которой он привязан, необязательный
владелец (`lead`) и флаг `assign_auto` — назначать ли владельца компонента исполнителем
всех новых задач с этим компонентом. `yatracker` предоставляет методы для получения списка
компонентов, их создания и изменения.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с компонентами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

!!! note "Компоненты очереди и задачи"

    Компоненты конкретной очереди можно получить и через `get_queue`
    (см. [«Работа с очередями»](queues.md)) с параметром `expand="components"` — они
    окажутся в поле `queue.components`. Задачи, в свою очередь, хранят свои компоненты в поле
    `issue.components`. Для задач это документированные короткие ссылки `ComponentRef`
    (`url`, `id`, `display`); для очереди формат в документации не описан, и библиотека
    исходит из того же формата по аналогии с `versions`. Полные объекты `Component`
    с версией и владельцем возвращают `get_components` и `get_queue_components`.

## Получение списка компонентов

### get_components

```python
async def get_components(
    self,
    per_page: int | None = None,
    page: int | None = None,
) -> list[Component]: ...
```

Возвращает список компонентов, созданных пользователями организации — сразу по всем
очередям.

```python
components = await tracker.get_components()

for component in components:
    print(component.queue.key, component.name)
```

Как и другие списки, ответ разбивается на страницы по 50 объектов. Если компонентов больше,
используйте `per_page` и `page`:

```python
components = await tracker.get_components(per_page=100, page=2)
```

1. `per_page` — количество компонентов на странице (по умолчанию 50).
2. `page` — номер страницы (по умолчанию 1).

Источник: https://yandex.cloud/ru/docs/tracker/get-components

### get_queue_components

```python
async def get_queue_components(self, queue_id: str | int) -> list[Component]: ...
```

Возвращает полные объекты компонентов одной очереди.

```python
components = await tracker.get_queue_components("WRITERS")

for component in components:
    print(component.name, component.version)
```

1. `queue_id` — ключ или идентификатор очереди.

!!! warning "Недокументированный запрос"

    Запрос `GET /queues/{id}/components` отсутствует в официальном справочнике API, но именно
    его использует официальная библиотека `yandex_tracker_client` для получения компонентов
    очереди. Если Трекер перестанет его поддерживать, используйте `get_components`.

## Создание компонента

### create_component

```python
async def create_component(
    self,
    name: str,
    queue: str,
    *,
    description: str | None = None,
    lead: str | None = None,
    assign_auto: bool | None = None,
) -> Component: ...
```

Создаёт новый компонент в указанной очереди.

```python
component = await tracker.create_component(
    name="Backend",
    queue="WRITERS",
    lead="login",
    assign_auto=True,
)
```

1. `name` — название компонента.
2. `queue` — ключ очереди (строка, например `WRITERS`), а не объект `Queue`.
3. `description` — необязательное описание компонента.
4. `lead` — необязательный логин владельца компонента (строка, а не объект `User`).
5. `assign_auto` — назначать ли `lead` исполнителем новых задач с этим компонентом.

Источник: https://yandex.cloud/ru/docs/tracker/post-component

## Изменение компонента

### update_component

```python
async def update_component(
    self,
    component_id: str | int,
    version: str | int,
    *,
    name: str | None = None,
    description: str | None = None,
    lead: str | None = None,
    assign_auto: bool | None = None,
) -> Component: ...
```

Изменяет существующий компонент. Передаются только те поля, которые нужно обновить.

```python
component = await tracker.update_component(
    component_id=component.id,
    version=component.version,
    description="Серверная часть приложения",
)
```

1. `component_id` — идентификатор компонента.
2. `version` — текущая версия компонента: защита от конфликтов параллельного изменения.
   Если передать неактуальную версию, Трекер ответит `409 Conflict` — см. про
   `AlreadyExistsError` в разделе [«Обработка ошибок»](errors.md).
3. `name`, `description`, `lead`, `assign_auto` — необязательные поля для изменения,
   как в `create_component`. Значение `None` означает «не менять»: такие поля в запрос не
   попадают, поэтому очистить описание или снять владельца через `None` нельзя.

Источник: https://yandex.cloud/ru/docs/tracker/patch-component

## Типичный сценарий

Получить компоненты нужной очереди, найти компонент по имени и изменить его, передав
актуальную версию:

```python
components = await tracker.get_queue_components("WRITERS")
component = next(c for c in components if c.name == "Backend")

component = await tracker.update_component(
    component_id=component.id,
    version=component.version,
    assign_auto=True,
)
```
