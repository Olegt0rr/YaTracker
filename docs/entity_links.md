# Связи сущностей

Связь (link) соединяет проект, портфель или цель с другой сущностью: например, проект может
«зависеть от» другого проекта или «работать над» целью. `yatracker` предоставляет методы для
получения связей сущности, создания одной или сразу нескольких связей и удаления связи.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы со связями сущностей являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

!!! note "Родительская сущность — это не связь"

    Родительский портфель проекта или портфеля и родительская цель цели задаются не здесь, а
    полем `parentEntity` через `update_entity` (см. [«Проекты, портфели и цели»](entities.md)).

Официальная документация:
https://yandex.ru/support/tracker/ru/api/entities/links/get-links

## Получение связей

### get_entity_links

```python
async def get_entity_links(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    fields: str | Sequence[str] | None = None,
) -> list[EntityLinkInfo]: ...
```

Возвращает список связей сущности с другими сущностями.

```python
links = await tracker.get_entity_links(
    "project",
    "655f3be523db2132",
    fields=["id", "summary"],
)

for link in links:
    print(link.relationship, link.link_field_values.id, link.link_field_values.summary)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `fields` — какие поля связанных сущностей вернуть (строка или последовательность имён).
   Без него связи приходят с пустым `link_field_values` — то есть у каждой связи будет виден
   только тип, но не поля связанной сущности.

Источник: https://yandex.ru/support/tracker/ru/api/entities/links/get-links

## Создание связи

### link_entities

```python
async def link_entities(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    relationship: str,
    entity: str | int | Sequence[str | int],
) -> bool: ...
```

Создаёт связь сущности с одной или несколькими другими сущностями. Возвращает `True` — сам
API документов ответа для этого запроса не описывает.

Одна связь:

```python
await tracker.link_entities(
    "project",
    "655f3be523db2132",
    "is dependent by",
    "6582874de6db7f5f00000000",
)
```

Сразу несколько связей одного типа за один вызов:

```python
await tracker.link_entities(
    "project",
    "655f3be523db2132",
    "works towards",
    ["65868f3fe2b9ef7400000000", "65868f3fe2b9ef7400000001"],
)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или `short_id` сущности, от которой создаётся связь.
3. `relationship` — тип связи:
     * для проектов и портфелей — `"depends on"` (зависит от связанной), `"is dependent by"`
       (блокирует связанную) или `"works towards"` (связь проекта с целью);
     * для целей — `"parent entity"` (родительская цель), `"child entity"` (подцель),
       `"depends on"`, `"is dependent by"` или `"is supported by"` (связь с проектом).
4. `entity` — идентификатор связываемой сущности, либо последовательность идентификаторов,
   чтобы создать сразу несколько связей с одним `relationship`. Пустая последовательность
   вызывает `ValueError`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/links/add-links

## Удаление связи

### delete_entity_link

```python
async def delete_entity_link(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    right: str | int,
) -> bool: ...
```

Удаляет связь между двумя сущностями. Возвращает `True` при успехе.

```python
await tracker.delete_entity_link(
    "project",
    "655f3be523db2132",
    "6582874de6db7f5f00000000",
)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или `short_id` сущности, у которой удаляется связь.
3. `right` — идентификатор сущности, с которой удаляется связь.

Источник: https://yandex.ru/support/tracker/ru/api/entities/links/delete-link

## Модель `EntityLinkInfo`

Одна связь сущности, элемент списка, который возвращает `get_entity_links`.

| Поле                | Тип            | Описание                                                              |
|---------------------|-----------------|--------------------------------------------------------------------------|
| `relationship`       | `str \| None`   | Тип связи — те же значения, что и у параметра `relationship` метода `link_entities` |
| `link_field_values`  | `EntityFields`  | Поля связанной сущности — только те, что запрошены через `fields`; при отсутствующем `fields` модель пуста |

!!! note "`type` в ответе, `relationship` в запросе"

    Пример ответа API называет это поле `type`, а таблица параметров запроса — `relationship`.
    `EntityLinkInfo.relationship` принимает оба имени из ответа API, но при сериализации
    (например, `model_dump`) отдаётся уже как `relationship` — так же называется одноимённое
    поле у `EntityLink`, который используют `create_entity`/`update_entity` для связей,
    указанных прямо при создании или изменении сущности.
