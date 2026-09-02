# Фильтры

Фильтр (filter) — это сохранённый набор условий отбора задач: кто исполнитель, в каком
статусе, какая очередь и так далее. Фильтр можно построить двумя взаимоисключающими
способами — набором условий по полям (`filter_`) или строкой на языке запросов (`query`);
использовать оба способа одновременно API не позволяет. `yatracker` предоставляет методы
для создания, получения и изменения фильтров.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с фильтрами являются асинхронными. В
    примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:

* [Создать фильтр](https://yandex.ru/support/tracker/ru/api/filters/create-filter)
* [Получить параметры фильтра](https://yandex.ru/support/tracker/ru/api/filters/get-filter)
* [Редактировать фильтр](https://yandex.ru/support/tracker/ru/api/filters/update-filter)

## Создание и получение

### create_filter

```python
async def create_filter(
    self,
    name: str,
    *,
    filter_: dict[str, Any] | None = None,
    query: str | None = None,
    fields: Sequence[str] | None = None,
    sorts: Sequence[FilterSort | dict[str, Any]] | None = None,
    group_by: str | dict[str, Any] | None = None,
    folder: str | dict[str, Any] | None = None,
    **kwargs,
) -> Filter: ...
```

Создаёт новый сохранённый фильтр задач.

```python
filter_ = await tracker.create_filter(
    name="Мои открытые задачи",
    filter_={"status": "open", "assignee": "me()"},
    sorts=[{"field": "created", "isAscending": False}],
    fields=["key", "summary", "status"],
)
```

1. `name` — название фильтра (обязательное поле).
2. `filter_` — условия фильтрации по полям задачи, ключи — имена полей, значения —
   условие: обычное значение (`"assignee": "me()"`), список (`"status": ["open",
   "inProgress"]`) или диапазон дат (`"created": "2024-01-01..2024-12-31"`). Полный
   список полей — на странице `https://tracker.yandex.ru/admin/fields`. Отправляется
   как `filter`.
3. `query` — условия фильтрации на языке запросов. Используйте либо `query`, либо
   `filter_`, не оба одновременно — иначе поведение API не гарантировано.
4. `fields` — список полей задачи, которые будут показаны в интерфейсе Трекера при
   применении фильтра. На результат `/issues/_search` не влияет.
5. `sorts` — правила сортировки результата, см. раздел «Сортировки» ниже.
6. `group_by` — поле, по которому результат группируется в интерфейсе; строка (ключ
   поля) или готовый объект.
7. `folder` — папка, в которую сохраняется фильтр; строка или готовый объект.
8. `kwargs` — любое другое поле фильтра.

Источник: https://yandex.ru/support/tracker/ru/api/filters/create-filter

### get_filter

```python
async def get_filter(self, filter_id: str | int) -> Filter: ...
```

Возвращает фильтр по его идентификатору.

```python
filter_ = await tracker.get_filter(12345)
print(filter_.name, filter_.filter_)
```

1. `filter_id` — идентификатор фильтра.

Источник: https://yandex.ru/support/tracker/ru/api/filters/get-filter

## Изменение

### update_filter

```python
async def update_filter(
    self,
    filter_id: str | int,
    *,
    name: str | None = None,
    filter_: dict[str, Any] | None = None,
    query: str | None = None,
    fields: Sequence[str] | None = None,
    sorts: Sequence[FilterSort | dict[str, Any]] | None = None,
    group_by: str | dict[str, Any] | None = None,
    folder: str | dict[str, Any] | None = None,
    **kwargs,
) -> Filter: ...
```

Изменяет существующий фильтр. Поля, оставленные `None`, не отправляются и остаются
без изменений.

```python
filter_ = await tracker.update_filter(
    filter_.id,
    name="Мои открытые задачи (обновлено)",
    filter_={"status": ["open", "inProgress"], "assignee": "me()"},
)
```

1. `filter_id` — идентификатор изменяемого фильтра.
2. `name` — новое название фильтра.
3. `filter_`, `query`, `fields`, `sorts`, `group_by`, `folder` — новые значения полей,
   формат такой же, как в `create_filter`.
4. `kwargs` — любое другое поле фильтра.

!!! warning "`filter_` заменяется целиком"

    При изменении фильтра параметр `filter_` **заменяется полностью**, а не
    объединяется с уже сохранёнными условиями. Чтобы сохранить старые условия и
    добавить новые, передайте в запросе все условия сразу — и старые, и новые:

    ```python
    updated = await tracker.update_filter(
        filter_.id,
        filter_={**filter_.filter_, "priority": "critical"},
    )
    ```

Источник: https://yandex.ru/support/tracker/ru/api/filters/update-filter

## Сортировки

`sorts` в запросе — список объектов `{"field": "<ключ поля>", "isAscending": <bool>}`.
Метод принимает такую сортировку в одном из двух видов:

* словарь в этом же формате, отправляется как есть;
* объект `FilterSort` — модель, которую Трекер возвращает в `Filter.sorts`. Так можно
  взять сортировку у одного фильтра и передать её другому без ручной сборки словаря:

```python
new_filter = await tracker.create_filter(
    name="Копия сортировки",
    query="Queue: TEST",
    sorts=filter_.sorts,
)
```

`FilterSort.field` — объект `FieldRef` (`url`, `id`, `display`), а в запросе достаточно
`field.id`; поле `is_ascending`, если оно `None`, не отправляется вовсе (Трекер выбирает
направление сортировки сам).

## Модели

### Filter

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на фильтр. |
| `id` | `str` | Идентификатор фильтра. |
| `name` | `str` | Название фильтра. |
| `filter_` | `dict[str, Any] \| None` | Условия фильтрации по полям (JSON-ключ `filter`). |
| `query` | `str \| None` | Условия фильтрации на языке запросов. |
| `fields` | `list[FieldRef] \| None` | Поля задачи, показываемые в интерфейсе. |
| `group_by` | `FieldRef \| None` | Поле группировки результата. |
| `sorts` | `list[FilterSort] \| None` | Правила сортировки. Возвращаются только если сортировка настроена. |
| `favorite` | `bool \| None` | Добавлен ли фильтр в избранное. |
| `permissions` | `FilterPermissions \| None` | Права доступа к фильтру. |
| `owner` | `User \| None` | Владелец фильтра. |

### FilterSort

| Поле | Тип | Описание |
|---|---|---|
| `field` | `FieldRef` | Поле задачи, по которому сортируется результат. |
| `is_ascending` | `bool \| None` | Направление сортировки: `True` — по возрастанию, `False` — по убыванию. |

### FilterPermissions

Права доступа к фильтру, ключи ответа — `READ` и `WRITE` в верхнем регистре (учтено
через `alias` на уровне полей).

| Поле | Тип | Описание |
|---|---|---|
| `read` | `FilterPermission \| None` | Кто может читать фильтр (JSON-ключ `READ`). |
| `write` | `FilterPermission \| None` | Кто может изменять фильтр (JSON-ключ `WRITE`). |

### FilterPermission

| Поле | Тип | Описание |
|---|---|---|
| `users` | `list[User]` | Пользователи, имеющие право. |
| `groups` | `list[Ref]` | Группы, имеющие право. |
| `roles` | `list[dict[str, Any]]` | Роли, имеющие право. В примерах ответа всегда пустой массив, поэтому формат объектов не документирован и хранится как есть. |

## Типичный сценарий

Создать фильтр по условиям, прочитать его, а затем расширить условия и добавить
сортировку, не потеряв уже сохранённые условия:

```python
filter_ = await tracker.create_filter(
    name="Мои открытые задачи",
    filter_={"status": "open", "assignee": "me()"},
)

filter_ = await tracker.get_filter(filter_.id)

filter_ = await tracker.update_filter(
    filter_.id,
    filter_={**filter_.filter_, "priority": "critical"},
    sorts=[{"field": "created", "isAscending": False}],
)
```
