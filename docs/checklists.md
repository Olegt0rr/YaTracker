# Чек-листы

Чек-лист (checklist) — это список пунктов внутри задачи, каждый из которых можно отмечать
выполненным, назначать на исполнителя и снабжать сроком (`deadline`). `yatracker`
предоставляет методы для получения пунктов чек-листа, добавления и редактирования отдельного
пункта, а также удаления как одного пункта, так и всего чек-листа целиком.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с чек-листами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

!!! note "Что возвращают изменяющие методы"

    В отличие от `get_checklist`, все изменяющие методы (`add_checklist_item`,
    `edit_checklist_item`, `delete_checklist_item`, `delete_checklist`) возвращают не пункт
    чек-листа, а **всю задачу целиком** — объект `FullIssue` (или вашу модель, переданную
    через `_type`, см. [«Работа с пользовательскими полями»](custom_fields.md)). Актуальный
    список пунктов при этом можно найти в поле `issue.checklist_items` возвращённого объекта.

## Получение чек-листа

### get_checklist

```python
async def get_checklist(self, issue_id: str) -> list[ChecklistItem]: ...
```

Возвращает список пунктов чек-листа задачи.

```python
items = await tracker.get_checklist("WRITERS-1")

for item in items:
    print(item.text, item.checked)
```

1. `issue_id` — ID или ключ задачи.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/issues/get-checklist

## Добавление пункта

### add_checklist_item

```python
async def add_checklist_item(
    self,
    issue_id: str,
    text: str,
    *,
    checked: bool | None = None,
    assignee: str | int | None = None,
    deadline: datetime | str | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
) -> IssueT_co | FullIssue: ...
```

Добавляет новый пункт в чек-лист задачи.

```python
issue = await tracker.add_checklist_item("WRITERS-1", "Написать тесты")
```

С дополнительными параметрами:

```python
from datetime import UTC, datetime

issue = await tracker.add_checklist_item(
    issue_id="WRITERS-1",
    text="Написать тесты",
    checked=False,
    assignee="login",
    deadline=datetime(2026, 9, 10, tzinfo=UTC),
)
```

1. `issue_id` — ID или ключ задачи.
2. `text` — текст пункта (обязателен).
3. `checked` — отметить пункт выполненным сразу при создании.
4. `assignee` — логин или числовой ID исполнителя пункта.
5. `deadline` — срок выполнения: timezone-aware `datetime` (рекомендуется) либо готовая
   строка вида `YYYY-MM-DDThh:mm:ss.sss±hhmm`, которую библиотека передаст как есть.
6. `_type` — своя модель задачи вместо `FullIssue`, как и в остальных методах работы с
   задачами (см. [«Работа с пользовательскими полями»](custom_fields.md)).

!!! note "Наивный datetime"

    Если передать в `deadline` "наивный" `datetime` (без часового пояса), библиотека всё
    равно отправит его, но выдаст `UserWarning` — API Трекера может некорректно обработать
    такое значение. Используйте timezone-aware объекты либо готовую строку.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/issues/add-checklist-item

## Редактирование пункта

### edit_checklist_item

```python
async def edit_checklist_item(
    self,
    issue_id: str,
    item_id: str,
    text: str,
    *,
    checked: bool | None = None,
    assignee: str | int | None = None,
    deadline: datetime | str | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
) -> IssueT_co | FullIssue: ...
```

Редактирует существующий пункт чек-листа.

```python
issue = await tracker.edit_checklist_item(
    issue_id="WRITERS-1",
    item_id=item.id,
    text=item.text,
    checked=True,
)
```

1. `issue_id` — ID или ключ задачи.
2. `item_id` — идентификатор пункта чек-листа (`item.id`).
3. `text` — текст пункта. API считает это поле обязательным даже при редактировании, поэтому
   если нужно поменять только `checked` (или другое поле), передавайте прежний текст пункта
   (`item.text`) — иначе Трекер затрёт текст пустым значением.
4. `checked`, `assignee`, `deadline` — необязательные поля, как и в `add_checklist_item`.
5. `_type` — своя модель задачи вместо `FullIssue`.

!!! warning "Расхождение с документацией API"

    Официальная документация метода оборачивает тело запроса в JSON-массив (`[ {...} ]`),
    но фактически (как и официальная библиотека `yandex_tracker_client`) `yatracker`
    отправляет обычный объект — так же, как во всех остальных методах.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/issues/edit-checklist

## Удаление пункта

### delete_checklist_item

```python
async def delete_checklist_item(
    self,
    issue_id: str,
    item_id: str,
    *,
    _type: type[IssueT_co | FullIssue] = FullIssue,
) -> IssueT_co | FullIssue: ...
```

Удаляет один пункт чек-листа.

```python
issue = await tracker.delete_checklist_item("WRITERS-1", item.id)
```

1. `issue_id` — ID или ключ задачи.
2. `item_id` — идентификатор удаляемого пункта.
3. `_type` — своя модель задачи вместо `FullIssue`.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/issues/delete-checklist-item

## Удаление чек-листа

### delete_checklist

```python
async def delete_checklist(
    self,
    issue_id: str,
    *,
    _type: type[IssueT_co | FullIssue] = FullIssue,
) -> IssueT_co | FullIssue: ...
```

Удаляет чек-лист задачи целиком — сразу все пункты.

```python
issue = await tracker.delete_checklist("WRITERS-1")
```

1. `issue_id` — ID или ключ задачи.
2. `_type` — своя модель задачи вместо `FullIssue`.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/issues/delete-checklist

## Методы на объекте задачи

Как и методы работы с комментариями, часть методов продублирована прямо на `FullIssue`,
чтобы не передавать `issue_id` руками — они возвращают ту же задачу (или её подкласс, если
задача изначально была получена с `_type`):

```python
issue = await tracker.get_issue("WRITERS-1")

items = await issue.get_checklist()
issue = await issue.add_checklist_item("Написать тесты")
issue = await issue.edit_checklist_item(item.id, item.text, checked=True)
issue = await issue.delete_checklist_item(item.id)
issue = await issue.delete_checklist()
```

* `issue.get_checklist()` — эквивалент `tracker.get_checklist(issue.id)`.
* `issue.add_checklist_item(text, **kwargs)` — эквивалент `tracker.add_checklist_item(issue.id, text, **kwargs)`.
* `issue.edit_checklist_item(item_id, text, **kwargs)` — эквивалент `tracker.edit_checklist_item(issue.id, item_id, text, **kwargs)`.
* `issue.delete_checklist_item(item_id)` — эквивалент `tracker.delete_checklist_item(issue.id, item_id)`.
* `issue.delete_checklist()` — эквивалент `tracker.delete_checklist(issue.id)`.

`FullIssue` также получает три новых поля, заполняемые чек-листом задачи:

| Поле              | Тип                        | Описание                              |
|-------------------|-----------------------------|----------------------------------------|
| `checklist_items` | `list[ChecklistItem] \| None` | Пункты чек-листа задачи               |
| `checklist_total` | `int \| None`                | Общее количество пунктов чек-листа    |
| `checklist_done`  | `int \| None`                | Количество выполненных пунктов        |

Все три поля не гарантированы в каждом ответе API (например, `get_issue` без чек-листа в
задаче вернёт `None`), но всегда заполняются в ответах методов из этого раздела.

## Модели `ChecklistItem`, `ChecklistAssignee`, `ChecklistDeadline`

### ChecklistItem

Пункт чек-листа — то, что возвращает `get_checklist` и что лежит в
`issue.checklist_items`.

| Поле                  | Тип                        | Описание                                       |
|-----------------------|------------------------------|-------------------------------------------------|
| `id`                  | `str`                        | Идентификатор пункта                            |
| `text`                | `str`                        | Текст пункта                                    |
| `checked`             | `bool`                       | Отмечен ли пункт выполненным                    |
| `text_html`           | `str \| None`                | HTML-версия текста (присутствует не всегда)     |
| `assignee`            | `ChecklistAssignee \| None`  | Исполнитель пункта, если назначен               |
| `deadline`            | `ChecklistDeadline \| None`  | Срок выполнения, если задан                     |
| `checklist_item_type` | `str \| None`                | Тип пункта чек-листа (например, `"standard"`)   |

### ChecklistAssignee

Исполнитель пункта чек-листа.

| Поле           | Тип           | Описание                                    |
|----------------|---------------|-----------------------------------------------|
| `id`           | `str`         | Идентификатор пользователя                    |
| `display`      | `str`         | Отображаемое имя                              |
| `passport_uid` | `int \| None` | Паспортный UID пользователя                   |
| `login`        | `str \| None` | Логин пользователя                            |
| `first_name`   | `str \| None` | Имя                                           |
| `last_name`    | `str \| None` | Фамилия                                       |
| `email`        | `str \| None` | Email                                         |
| `tracker_uid`  | `int \| None` | UID пользователя в Трекере                    |

!!! note "Не то же самое, что `User`"

    В отличие от модели `User`, у `ChecklistAssignee` нет поля `self` (`url`) — Трекер не
    присылает ссылку на пользователя внутри пункта чек-листа, поэтому переиспользовать
    существующую модель `User` для этого поля нельзя.

### ChecklistDeadline

Срок выполнения пункта чек-листа.

| Поле            | Тип           | Описание                                                    |
|-----------------|---------------|----------------------------------------------------------------|
| `date`          | `datetime`    | Дата и время дедлайна                                          |
| `deadline_type` | `str`         | Тип дедлайна (на данный момент API отдаёт только `"date"`)     |
| `is_exceeded`   | `bool \| None`| Просрочен ли срок (заполняется в ответах, полученных из API)   |
