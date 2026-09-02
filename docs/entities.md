# Проекты, портфели и цели

Сущности (entities) — это проекты, портфели и цели современного интерфейса Трекера.
У проекта есть статус (`entityStatus`), участники, клиенты, наблюдатели, даты начала и
окончания, чек-лист, метрики, вложения и родительские сущности. Портфель объединяет
проекты, а цель дополнительно хранит ключевые результаты (`keyResultItems`) и прогресс.
Все три вида живут в одном API `/entities/<тип>` и различаются только значением
`entity_type`: `"project"`, `"portfolio"` или `"goal"`.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с сущностями являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

!!! note "Старый API проектов"

    Не путайте эти методы с устаревшим API `/projects` — см.
    [«Проекты (устаревший API)»](projects.md). Проекты, которые вы видите в текущем
    интерфейсе Трекера, — это именно сущности из этого раздела.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/entities/about-entities

## Общие правила

**Тип сущности идёт первым аргументом.** Каждый метод принимает `entity_type` —
`"project"`, `"portfolio"` или `"goal"`. Список нужен прежде всего проверке типов:
во время выполнения значение не проверяется и подставляется в адрес запроса как есть,
поэтому вид сущности, который Трекер добавит позже, тоже будет работать (в том числе
через методы объекта `Entity`, где `entity_type` приходит с сервера обычной строкой).

**Поля передаются через `values` и `**kwargs`.** Оба словаря складываются в тело
запроса под ключом `fields`, ключи из `snake_case` переводятся в `camelCase`
(`entity_status` → `entityStatus`). Ключи, которые не являются идентификаторами Python
(например, идентификаторы локальных полей вида `"<id>--name"`), отправляются как есть.
Значения `date` и `datetime` приводятся к форматам API (`YYYY-MM-DD` и
`YYYY-MM-DDThh:mm:ss.sss±hhmm`). Именованные аргументы со значением `None`
отбрасываются, а `values` отправляется как есть — то есть очистить поле можно только
через `values={"lead": None}`.

**`fields` и `expand` — это параметры запроса, а не тело.** `fields` перечисляет поля,
которые нужно вернуть в ответе (строка или последовательность имён — она будет
склеена через запятую), `expand="attachments"` добавляет в ответ вложения. Ответ
приходит в виде объекта `Entity`, у которого документированные поля лежат в
`entity.fields`, а недокументированные и пользовательские поля сохраняются в той же
модели как дополнительные. Те из них, чьё имя является корректным идентификатором
Python, доступны атрибутом (`entity.fields.customField`), а идентификаторы локальных
полей вида `"<id>--userId"` — только через `model_extra` или `getattr`.

```python
entity = await tracker.get_entity("project", "655f3be523db2132", fields=["summary"])

print(entity.short_id, entity.fields.summary)
print(entity.fields.model_extra["64a51c6d866ea82411abe756--userId"])
```

**Связи.** Параметр `links` принимает последовательность объектов `EntityLink` или
обычных словарей `{"relationship": ..., "entity": ...}`. Одиночная связь (словарь,
`EntityLink` или строка) вызывает `TypeError`: её пришлось бы перебирать по ключам
или по символам. Допустимые значения `relationship`:

* `"depends on"` — зависит от;
* `"is dependent by"` — от неё зависит;
* `"works towards"` — работает над целью;
* `"parent entity"` — родительская сущность;
* `"child entity"` — дочерняя сущность;
* `"is supported by"` — поддерживается.

**Статусы.** Для проектов и портфелей `entityStatus` принимает значения `draft`,
`draft2`, `in_progress`, `according_to_plan`, `postponed`, `at_risk`, `blocked`,
`launched`, `cancelled`. Для целей — `draft`, `according_to_plan`, `at_risk`,
`blocked`, `achieved`, `partially_achieved`, `not_achieved`, `exceeded`, `cancelled`.

!!! warning "Ошибки 412, 423 и 428"

    Конфликт версий (`412`), заблокированная сущность (`423`) и невыполненные
    предусловия (`428`) приходят обычным `YaTrackerError` — отличить их можно только
    по тексту ответа. Подробнее в разделе [«Обработка ошибок»](errors.md).

## Создание сущности

### create_entity

```python
async def create_entity(
    self,
    entity_type: EntityType,
    summary: str,
    *,
    values: dict[str, Any] | None = None,
    links: Sequence[EntityLink | dict[str, Any]] | None = None,
    fields: str | Sequence[str] | None = None,
    **kwargs: Any,
) -> Entity: ...
```

Создаёт проект, портфель или цель.

```python
from datetime import date

from yatracker.types.entity import EntityLink

project = await tracker.create_entity(
    "project",
    "Новый проект",
    entity_status="in_progress",
    start=date(2024, 1, 1),
    team_users=["agent007"],
    links=[EntityLink(relationship="works towards", entity="1234")],
    fields=["summary", "entityStatus"],
)

print(project.id, project.short_id)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `summary` — название сущности (попадёт в `fields.summary`).
3. `values` — словарь полей, как в теле запроса, но с ключами в `snake_case`.
4. `links` — список связей: `EntityLink` или словари.
5. `fields` — какие поля вернуть в ответе.
6. `**kwargs` — дополнительные поля поверх `values`.

!!! note "Ответ без `fields`"

    В ответе на создание Трекер не присылает объект `fields` вовсе. Библиотека
    подставляет пустую модель, поэтому `entity.fields.summary` вернёт `None`, а не
    вызовет ошибку. Чтобы получить поля сразу, перечислите их в `fields`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/create-entity

## Получение сущности

### get_entity

```python
async def get_entity(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Возвращает сущность по идентификатору или короткому идентификатору (`short_id`).

```python
project = await tracker.get_entity(
    "project",
    "655f3be523db2132",
    fields=["summary", "author", "parentEntity", "issueQueues"],
    expand="attachments",
)

print(project.fields.summary)
print(project.fields.parent_entity.primary.display)
print([queue.key for queue in project.fields.issue_queues or []])
print([attachment.name for attachment in project.attachments or []])
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `fields` — какие поля вернуть.
4. `expand` — `"attachments"`, чтобы получить вложения.

!!! note "Даты"

    Поля `start`, `end` и `last_comment_updated_at` API отдаёт либо датой
    (`2023-11-23`), либо меткой времени (`2023-11-23T11:47:49.743+0000`). Тип
    выбирается по виду самой строки, а не по её значению: дата становится `date`,
    метка времени — `datetime` с часовым поясом, даже если время в ней ровно
    полночь (`2023-11-23T00:00:00.000+0000`).

Источник: https://yandex.ru/support/tracker/ru/api/entities/get-entity

## Изменение сущности

### update_entity

```python
async def update_entity(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    values: dict[str, Any] | None = None,
    comment: str | None = None,
    links: Sequence[EntityLink | dict[str, Any]] | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
    **kwargs: Any,
) -> Entity: ...
```

Изменяет сущность: поля, комментарий и связи. Пустые части в тело запроса не
попадают, а если менять нечего вовсе — метод вызовет `ValueError`, не отправляя
запрос.

```python
project = await tracker.update_entity(
    "project",
    "655f3be523db2132",
    entity_status="at_risk",
    comment="Сдвинули сроки",
)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `values` — словарь полей (единственный способ передать `None`, чтобы очистить поле).
4. `comment` — комментарий к изменению.
5. `links` — связи, которые нужно добавить.
6. `fields`, `expand` — как в `get_entity`.
7. `**kwargs` — дополнительные поля поверх `values`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/update-entity

## Удаление сущности

### delete_entity

```python
async def delete_entity(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    with_board: bool | None = None,
) -> bool: ...
```

Удаляет сущность. Метод возвращает `True` при успешном удалении.

```python
await tracker.delete_entity("project", "655f3be523db2132", with_board=True)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `with_board` — удалить ли вместе с доской проекта. Если не передавать, параметр
   `withBoard` в запрос не попадёт.

Источник: https://yandex.ru/support/tracker/ru/api/entities/delete-entity

## Поиск сущностей

### search_entities

```python
async def search_entities(
    self,
    entity_type: EntityType,
    *,
    query: str | None = None,
    filter_: dict[str, Any] | None = None,
    order_by: str | None = None,
    order_asc: bool | None = None,
    root_only: bool | None = None,
    fields: str | Sequence[str] | None = None,
    per_page: int | None = None,
    page: int | None = None,
) -> EntitySearchResult: ...
```

Ищет сущности по подстроке названия и по значениям полей.

```python
result = await tracker.search_entities(
    "project",
    query="Витрина",
    filter_={"entity_status": "in_progress", "followers": "notEmpty()"},
    order_by="entityStatus",
    order_asc=True,
    per_page=50,
)

print(result.hits, result.pages)
for project in result.values:
    print(project.short_id, project.fields.summary)
```

1. `entity_type` — тип сущности.
2. `query` — подстрока названия (уходит в тело как `input`).
3. `filter_` — фильтр по полям. Ключи приводятся к `camelCase`; кроме обычных значений
   поддерживаются `"notEmpty()"` (поле заполнено) и `"empty()"` (поле пустое). Имя
   параметра с подчёркиванием — как и у `find_issues` — чтобы не перекрывать
   встроенную функцию `filter`.
4. `order_by` — поле сортировки, `order_asc` — направление.
5. `root_only` — вернуть только сущности без родителя.
6. `fields` — какие поля вернуть.
7. `per_page`, `page` — постраничная разбивка (по умолчанию 50 объектов на страницу).

Источник: https://yandex.ru/support/tracker/ru/api/entities/search-entities

### iter_entities

```python
async def iter_entities(
    self,
    entity_type: EntityType,
    *,
    query: str | None = None,
    filter_: dict[str, Any] | None = None,
    order_by: str | None = None,
    order_asc: bool | None = None,
    root_only: bool | None = None,
    fields: str | Sequence[str] | None = None,
    per_page: int | None = None,
) -> AsyncIterator[Entity]: ...
```

То же самое, но с автоматическим перебором страниц: итератор запрашивает страницы
одну за другой и останавливается на последней (`page >= pages`) или на первой пустой.

```python
async for goal in tracker.iter_entities("goal", filter_={"entity_status": "at_risk"}):
    print(goal.short_id, goal.fields.summary)
```

Источник: https://yandex.ru/support/tracker/ru/api/entities/search-entities

## Массовое изменение

### bulk_update_entities

```python
async def bulk_update_entities(
    self,
    entity_type: EntityType,
    entities: Sequence[str | Entity],
    *,
    values: dict[str, Any] | None = None,
    comment: str | None = None,
    links: Sequence[EntityLink | dict[str, Any]] | None = None,
    **kwargs: Any,
) -> BulkChange: ...
```

Изменяет сразу несколько сущностей. Операция выполняется в фоне, а метод возвращает
обычный объект `BulkChange` — тот же, что и у массовых операций с задачами
(см. [«Массовые операции»](bulk_changes.md)). Значит, работают и `get_bulk_change`,
и `wait_bulk_change`, и метод `BulkChange.wait()`.

```python
bulk_change = await tracker.bulk_update_entities(
    "project",
    ["655f3be523db2132", project],
    entity_status="at_risk",
    followers="agent007",
    comment="Пересматриваем сроки",
)

bulk_change = await bulk_change.wait(timeout=60)
print(bulk_change.status)
```

1. `entity_type` — тип сущности.
2. `entities` — последовательность идентификаторов сущностей или объектов `Entity`
   (уходят в тело как `metaEntities`). Пустой список вызывает `ValueError`, а одна
   строка вместо списка — `TypeError`: её пришлось бы перебирать по символам.
3. `values`, `**kwargs` — поля, как в `create_entity`. Если менять нечего — `ValueError`.
4. `comment` — комментарий ко всем сущностям.
5. `links` — связи, которые нужно добавить.

Источник: https://yandex.ru/support/tracker/ru/api/entities/bulkchange-entities

## История изменений

### get_entity_events

```python
async def get_entity_events(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    per_page: int | None = None,
    from_: str | None = None,
    selected: str | None = None,
    new_events_on_top: bool | None = None,
    direction: str | None = None,
) -> EntityEvents: ...
```

Возвращает страницу истории изменений сущности: список событий и флаги `has_next`
и `has_prev`, по которым видно, есть ли соседние страницы.

```python
events = await tracker.get_entity_events("project", "655f3be523db2132", per_page=50)

for event in events.events:
    print(event.date, event.display)
    for change in event.changes:
        print(" ", change.field.id if change.field else "?", change.diff)

# следующая страница: считаем от последнего показанного события
if events.has_next:
    events = await tracker.get_entity_events(
        "project",
        "655f3be523db2132",
        per_page=50,
        from_=events.events[-1].id,
        direction="forward",
    )
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `per_page` — количество событий на странице (по умолчанию 50).
4. `from_` — событие, от которого отсчитывается страница (уходит как `from`).
5. `selected` — событие, которое окажется в середине страницы. Передавать `from_` и
   `selected` одновременно нельзя — будет `ValueError`.
6. `new_events_on_top` — показывать ли новые события первыми.
7. `direction` — `"forward"` или `"backward"`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/get-events-relative

## Методы объекта `Entity`

У полученного объекта есть короткие методы, которые обращаются к тому же трекеру и
сами подставляют `entity_type` и `id`:

```python
project = await tracker.get_entity("project", "655f3be523db2132")

project = await project.refresh(fields=["summary", "entityStatus"])
project = await project.update(entity_status="launched", comment="Запустились")
events = await project.get_events(per_page=10, direction="forward")
await project.delete()
```

У `project.get_events()` те же именованные параметры, что и у `get_entity_events`
(`per_page`, `from_`, `selected`, `new_events_on_top`, `direction`), а
`project.delete()` — как и `delete_entity` — возвращает `True` при успешном
удалении.

## Типичный сценарий

Найти проекты в работе, у которых что-то пошло не так, перевести их в статус
«под угрозой» одной массовой операцией и дождаться её завершения:

```python
projects = [
    project
    async for project in tracker.iter_entities(
        "project",
        filter_={"entity_status": "in_progress"},
        fields=["summary", "entityStatus"],
    )
]

bulk_change = await tracker.bulk_update_entities(
    "project",
    projects,
    entity_status="at_risk",
    comment="Пересматриваем сроки",
)

bulk_change = await bulk_change.wait(timeout=300)
print(bulk_change.status, bulk_change.status_text)
```
