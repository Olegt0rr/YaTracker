# Чек-листы сущностей

Чек-лист сущности — это список пунктов внутри проекта или портфеля (`fields.checklistItems`),
устроенный так же, как чек-лист задачи: пункт можно отмечать выполненным, назначать на
исполнителя и снабжать сроком (`deadline`). API документирует чек-листы только для проектов
и портфелей — у целей (`"goal"`) вместо чек-листа есть ключевые результаты, о них ниже.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с чек-листами сущностей являются
    асинхронными. В примерах ниже вызовы показаны так, как будто мы уже находимся внутри
    корутины.

!!! note "Тип сущности — только проект или портфель"

    Все методы этой страницы принимают `entity_type` типа
    `ChecklistEntityType = Literal["project", "portfolio"]` (экспортируется из
    `yatracker.types`), а не более широкий `EntityType`, в который входит ещё и `"goal"`:
    чек-листы задокументированы только для проектов и портфелей. Проверка статическая —
    во время выполнения значение уходит в URL как есть.

!!! note "Чек-лист — это тоже поле сущности"

    Весь чек-лист целиком доступен и через саму сущность: `get_entity(..., fields="checklistItems")`
    (см. [«Проекты, портфели и цели»](entities.md)) читает список пунктов, а
    `update_entity(..., checklist_items=[...])` перезаписывает его целиком. Методы этой
    страницы — это отдельные ручки API для типичных операций (добавить пункт, поменять один
    пункт, переместить, удалить), но ни одна из них не возвращает сам пункт или список
    пунктов — только всю сущность (`Entity`), как и `update_entity`. Актуальный список пунктов
    берите из `entity.fields.checklist_items`.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/entities/checklists/add-checklist

## Получение чек-листа

Отдельного метода для чек-листа сущности нет — используйте `get_entity` с
`fields="checklistItems"` (см. [«Проекты, портфели и цели»](entities.md)):

```python
project = await tracker.get_entity(
    "project",
    "655f3be523db2132",
    fields="checklistItems",
)

for item in project.fields.checklist_items or []:
    print(item.id, item.text, item.checked)
```

## Добавление пункта

### add_entity_checklist_item

```python
async def add_entity_checklist_item(
    self,
    entity_type: ChecklistEntityType,
    entity_id: str | int,
    text: str,
    *,
    checked: bool | None = None,
    assignee: str | int | None = None,
    deadline: EntityDeadline | datetime | date | str | None = None,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Добавляет один пункт в чек-лист сущности; пункт попадает в конец списка, а если у сущности
чек-листа ещё не было — он создаётся.

```python
from datetime import date

entity = await tracker.add_entity_checklist_item(
    "project",
    "655f3be523db2132",
    "Написать тесты",
    checked=False,
    assignee="login",
    deadline=date(2026, 9, 10),
    fields=["checklistItems"],
)

for item in entity.fields.checklist_items or []:
    print(item.id, item.text, item.checked)
```

1. `entity_type` — `"project"` или `"portfolio"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `text` — текст пункта (обязателен).
4. `checked` — отметить пункт выполненным сразу при создании.
5. `assignee` — логин или числовой идентификатор исполнителя пункта.
6. `deadline` — срок выполнения: `EntityDeadline` (например, взятый из другого пункта — тогда
   отправится его собственный `deadline_type`), timezone-aware `datetime` или `date` (оба
   отправляются со значением типа `date`), либо готовая строка API.
7. `notify` — уведомлять ли пользователей, указанных в полях сущности (по умолчанию `True`).
8. `notify_author` — уведомлять ли автора изменения (по умолчанию `False`).
9. `fields`, `expand` — какие поля и доп. информацию вернуть в ответе, как в `get_entity`.

!!! note "Формат даты в `deadline`"

    Все страницы документации по чек-листам показывают дату дедлайна только как полную
    отметку времени `YYYY-MM-DDThh:mm:ss.sss±hhmm`. Поэтому `date(2026, 9, 10)` отправляется
    как полночь UTC — `"2026-09-10T00:00:00.000+0000"`. Если смещение важно (например, срок
    должен наступать в полночь по Москве), передавайте timezone-aware `datetime` или готовую
    строку API — они уходят как есть.

!!! note "Наивный `datetime`"

    Если передать в `deadline` "наивный" `datetime` (без часового пояса), библиотека всё
    равно отправит его, но выдаст `UserWarning` — причём предупреждение указывает на вашу
    строку кода, а не на файл библиотеки. Используйте timezone-aware объекты, `date`
    либо готовую строку.

!!! note "Один пункт за вызов"

    Официальный запрос принимает и один объект, и JSON-массив, то есть умеет добавлять сразу
    несколько пунктов чек-листа за один вызов API. `add_entity_checklist_item` всегда
    отправляет один объект — чтобы добавить несколько пунктов, вызовите метод несколько раз.

Источник: https://yandex.ru/support/tracker/ru/api/entities/checklists/add-checklist

## Изменение чек-листа целиком

### edit_entity_checklist

```python
async def edit_entity_checklist(
    self,
    entity_type: ChecklistEntityType,
    entity_id: str | int,
    items: Sequence[EntityChecklistItem | dict[str, Any]],
    *,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Изменяет сразу несколько пунктов чек-листа одним запросом.

```python
entity = await tracker.edit_entity_checklist(
    "project",
    "655f3be523db2132",
    [
        {"id": "658953a65c0f1b210000000a", "text": "Первый пункт"},
        {"id": "658953a65c0f1b210000000b", "text": "Второй пункт", "checked": True},
    ],
    fields=["checklistItems"],
)
```

1. `entity_type` — `"project"` или `"portfolio"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `items` — пункты для изменения: объекты `EntityChecklistItem` или словари вида
   `{"id": "...", "text": "...", "checked": True}`. Каждый пункт обязан иметь `id` и `text`.
   Одиночный пункт вместо последовательности вызывает `TypeError`, пустая последовательность —
   `ValueError`.
4. `notify`, `notify_author` — уведомления, как в `add_entity_checklist_item`.
5. `fields`, `expand` — какие поля вернуть в ответе.

!!! tip "Пункты, прочитанные из API, можно отправлять обратно"

    `EntityChecklistItem`, полученный из ответа API, содержит поля, которых запрос не
    принимает, поэтому библиотека пересобирает его: `assignee` уходит идентификатором
    пользователя (API ждёт id или логин, а не объект), `deadline` перерисовывается в
    документированный формат, а `text_html`, `checklist_item_type` и `deadline.is_exceeded`
    отбрасываются. Это делает сама модель, а не метод, поэтому тело будет одинаковым и здесь,
    и в `update_entity(values={"checklistItems": [...]})`. Словари отправляются как есть —
    тогда телом запроса управляете вы.

!!! warning "Незаполненные поля сбрасываются, количество пунктов не меняется"

    Это не патч, а полная замена каждого перечисленного пункта: если необязательное поле
    (`checked`, `assignee`, `deadline`) не повторить, оно сбросится к значению по умолчанию
    (пустая строка, `0`, `null` или `false`) — так документирует сам API. Передавайте обратно
    все значения, которые должны остаться прежними. Количество пунктов чек-листа этим методом
    изменить нельзя — для этого используйте `add_entity_checklist_item` и
    `delete_entity_checklist_item`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist

## Изменение одного пункта

### edit_entity_checklist_item

```python
async def edit_entity_checklist_item(
    self,
    entity_type: ChecklistEntityType,
    entity_id: str | int,
    item_id: str,
    *,
    text: str | None = None,
    checked: bool | None = None,
    assignee: str | int | None = None,
    deadline: EntityDeadline | datetime | date | str | None = None,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Изменяет один пункт чек-листа. В отличие от `edit_entity_checklist`, здесь все поля
необязательны — можно поменять, например, только `checked`.

```python
entity = await tracker.edit_entity_checklist_item(
    "project",
    "655f3be523db2132",
    "658953a65c0f1b210000000a",
    checked=True,
)
```

1. `entity_type` — `"project"` или `"portfolio"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `item_id` — идентификатор пункта чек-листа.
4. `text`, `checked`, `assignee`, `deadline` — необязательные поля, как в
   `add_entity_checklist_item`. Поля, оставленные `None`, в запрос не попадают.
5. `notify`, `notify_author`, `fields`, `expand` — как в `add_entity_checklist_item`.
6. Метод бросает `ValueError`, если не передано ни одного поля для изменения.

!!! note "Что происходит с полями, которые не передали"

    В отличие от `edit_entity_checklist`, официальная документация этого запроса не говорит,
    сбрасываются ли непереданные поля или сохраняют прежнее значение — поэтому на сохранение
    прежних значений не полагайтесь и передавайте явно всё, что должно остаться как есть.

Источник: https://yandex.ru/support/tracker/ru/api/entities/checklists/patch-checklist-item

## Перемещение пункта

### move_entity_checklist_item

```python
async def move_entity_checklist_item(
    self,
    entity_type: ChecklistEntityType,
    entity_id: str | int,
    item_id: str,
    before: str,
    *,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Перемещает пункт чек-листа перед другим пунктом.

```python
entity = await tracker.move_entity_checklist_item(
    "project",
    "655f3be523db2132",
    "658953a65c0f1b210000000c",
    before="658953a65c0f1b210000000b",
    fields=["checklistItems"],
)
```

1. `entity_type` — `"project"` или `"portfolio"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `item_id` — идентификатор перемещаемого пункта.
4. `before` — идентификатор пункта, перед которым нужно вставить перемещаемый.
5. `notify`, `notify_author`, `fields`, `expand` — как в `add_entity_checklist_item`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/checklists/move-checklist-item

## Удаление пункта

### delete_entity_checklist_item

```python
async def delete_entity_checklist_item(
    self,
    entity_type: ChecklistEntityType,
    entity_id: str | int,
    item_id: str,
    *,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Удаляет один пункт чек-листа. Действие нельзя отменить. В отличие от задачного
`delete_checklist_item`, запрос отвечает `200 OK` и телом сущности, поэтому метод
возвращает `Entity`, а не признак успеха.

```python
entity = await tracker.delete_entity_checklist_item(
    "project",
    "655f3be523db2132",
    "658953a65c0f1b210000000a",
    fields="checklistItems",
)

for item in entity.fields.checklist_items or []:
    print(item.id, item.text)
```

1. `entity_type` — `"project"` или `"portfolio"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `item_id` — идентификатор удаляемого пункта.
4. `notify`, `notify_author`, `fields`, `expand` — как в `add_entity_checklist_item`.

Возвращает сущность целиком; чтобы увидеть оставшиеся пункты чек-листа, запросите их
через `fields="checklistItems"` — перечитывать сущность отдельным `get_entity` не нужно.

Источник: https://yandex.ru/support/tracker/ru/api/entities/checklists/delete-checklist-item

## Удаление чек-листа целиком

### delete_entity_checklist

```python
async def delete_entity_checklist(
    self,
    entity_type: ChecklistEntityType,
    entity_id: str | int,
    *,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Удаляет чек-лист сущности целиком — сразу все пункты. Действие нельзя отменить. Как и
`delete_entity_checklist_item`, запрос отвечает `200 OK` и телом сущности, поэтому метод
возвращает `Entity`.

```python
entity = await tracker.delete_entity_checklist("project", "655f3be523db2132")
print(entity.version)
```

1. `entity_type` — `"project"` или `"portfolio"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `notify`, `notify_author`, `fields`, `expand` — как в `add_entity_checklist_item`.

Возвращает сущность, из которой удалён чек-лист. Отдельно перечитывать её не нужно: с
`fields="checklistItems"` в ответе будет уже пустой чек-лист.

Источник: https://yandex.ru/support/tracker/ru/api/entities/checklists/delete-checklist

## Модели `EntityChecklistItem`, `EntityDeadline`

### EntityChecklistItem

Пункт чек-листа сущности — то, что лежит в `entity.fields.checklist_items`.

| Поле                  | Тип                       | Описание                                       |
|-----------------------|---------------------------|-------------------------------------------------|
| `id`                  | `str`                     | Идентификатор пункта                            |
| `text`                | `str \| None`             | Текст пункта                                    |
| `text_html`           | `str \| None`             | HTML-версия текста                              |
| `checked`             | `bool \| None`            | Отмечен ли пункт выполненным                    |
| `assignee`            | `ChecklistAssignee \| None` | Исполнитель пункта, если назначен              |
| `deadline`            | `EntityDeadline \| None`  | Срок выполнения, если задан                     |
| `checklist_item_type` | `str \| None`             | Тип пункта чек-листа (например, `"standard"`)   |

!!! note "Исполнитель пункта — не `User`"

    В ответах API исполнитель пункта чек-листа приходит урезанным объектом без ключа
    `self`, поэтому это [`ChecklistAssignee`](checklists.md), а не `User`: у `User` ссылка
    `self` обязательна, и реальный ответ им бы не разобрался. У ключевых результатов
    (`EntityKeyResult.assignee`) `self` есть — там остаётся `User`.

!!! tip "Модель, переданную в запрос, библиотека перерисовывает сама"

    `EntityChecklistItem` и `EntityDeadline` знают, как выглядит их запросная форма, и
    приводятся к ней везде, где попадают в тело запроса — и в `edit_entity_checklist`, и в
    `update_entity(values={"checklistItems": [...]})`, и в `create_entity`. `assignee`
    уходит идентификатором пользователя, `deadline` — полной меткой времени
    `YYYY-MM-DDThh:mm:ss.sss±hhmm`, а read-only поля `text_html`, `checklist_item_type` и
    `deadline.is_exceeded` отбрасываются. Тело получается одинаковым независимо от того,
    каким методом вы отправили пункт. Словари, как и раньше, идут как есть.

### EntityDeadline

Дедлайн пункта чек-листа или ключевого результата цели.

| Поле            | Тип                    | Описание                                                        |
|-----------------|------------------------|-------------------------------------------------------------------|
| `date`          | `date \| datetime \| None` | Дата дедлайна. У пунктов чек-листа API отдаёт полную метку времени, у ключевых результатов — дату; тип выбирается по виду строки в ответе, а не по значению |
| `deadline_type` | `str \| None`          | Тип дедлайна: `"date"` (для ключевых результатов — всегда) или `"quarter"` |
| `is_exceeded`   | `bool \| None`         | Просрочен ли срок (заполняется в ответах, полученных из API)      |

`EntityDeadline`, попавший в тело запроса сам по себе (например, в `values={"deadline": ...}`),
рисуется как `{"date", "deadlineType"}`; голая `date` остаётся в виде `YYYY-MM-DD` — так
документированы дедлайны ключевых результатов. Внутри пункта чек-листа та же `date`
превращается в полночь UTC, потому что чек-листы документированы через полную метку времени.
Передайте `datetime` с таймзоной, если смещение важно.

## Ключевые результаты и метрики

У ключевых результатов (`keyResultItems`, только у целей) и у метрик (`metricItems`, у
проектов, портфелей и целей) нет отдельных методов чтения, добавления и удаления — Трекер
документирует их как обычные поля сущности, и всё изменение идёт через `update_entity` (см.
[«Проекты, портфели и цели»](entities.md)).

### Ключевые результаты (`key_result_items`)

Только у целей (`entity_type="goal"`). Значение — либо список (заменяет весь список целиком),
либо словарь с оператором `add`/`remove`, либо `None` (удаляет все ключевые результаты).

Заменить весь список:

```python
goal = await tracker.update_entity(
    "goal",
    "655f328523db2132",
    key_result_items=[
        {
            "type": "value",
            "text": "Key result 1",
            "assignee": "username1",
            "deadline": {"date": "2025-06-03", "deadlineType": "date"},
            "progress": {"start": 1, "end": 10, "current": 5},
        },
        {
            "type": "binary",
            "text": "Key result 2",
            "assignee": "username2",
            "achieved": False,
        },
    ],
    fields=["keyResultItems"],
)
```

Добавить один ключевой результат к существующим:

```python
goal = await tracker.update_entity(
    "goal",
    "655f328523db2132",
    key_result_items={
        "add": {"type": "binary", "text": "Key result 3", "assignee": "username1"},
    },
)
```

Прочитать список:

```python
goal = await tracker.get_entity("goal", "655f328523db2132", fields="keyResultItems")

for kr in goal.fields.key_result_items or []:
    print(kr.text, kr.type, kr.achieved, kr.progress)
```

Удалить все ключевые результаты — `key_result_items=None`, переданный как обычный именованный
параметр, из запроса просто выпадет, поэтому `None` нужно передать через `values`:

```python
goal = await tracker.update_entity(
    "goal",
    "655f328523db2132",
    values={"key_result_items": None},
)
```

Удалить один ключевой результат — оператором `remove`, которому нужно передать объект пункта
в том же виде, в каком он вернулся от `get_entity` (проще всего — `model_dump`):

!!! warning "`remove` требует объект ровно таким, каким его вернул API"

    В отличие от пунктов чек-листа, `EntityKeyResult` и `EntityMetricItem` не имеют
    собственной запросной формы: оператор `remove` сравнивает объект с тем, что хранится в
    Трекере, поэтому обрезать или переименовывать поля нельзя. Передавайте модель как есть
    (библиотека выгрузит её дословно, вместе со ссылками `self`) или её `model_dump`.

```python
kr = goal.fields.key_result_items[0]

goal = await tracker.update_entity(
    "goal",
    "655f328523db2132",
    key_result_items={
        "remove": kr.model_dump(mode="json", by_alias=True, exclude_none=True)
    },
)
```

* `type` — `"value"` (прогресс по числовому значению, тогда обязателен `progress`) или
  `"binary"` (прогресс по факту выполнения, тогда используется `achieved`).
* `deadline` — объект с обязательными `date` (`YYYY-MM-DD`) и `deadline_type="date"`.

### Метрики (`metric_items`)

У проектов, портфелей и целей. Устроены так же, как ключевые результаты: список — замена
целиком, `{"add": ...}` — добавление одной метрики, `{"remove": ...}` — удаление одной,
`None` (через `values`) — удаление всех.

```python
project = await tracker.update_entity(
    "project",
    "655f8cc523db2132",
    metric_items=[
        {
            "text": "First metric",
            "url": "https://tracker.yandex.ru/dashboard/12/widget/34?_embedded=1&_no_controls=1",
        },
        {
            "text": "Second metric",
            "url": "https://tracker.yandex.ru/dashboard/23/widget/45?_embedded=1&_no_controls=1",
        },
    ],
    fields=["metricItems"],
)

project = await tracker.update_entity(
    "project",
    "655f8cc523db2132",
    metric_items={
        "add": {
            "text": "My metric",
            "url": "https://tracker.yandex.ru/dashboard/12/widget/34?_embedded=1&_no_controls=1",
        },
    },
)

project = await tracker.get_entity("project", "655f8cc523db2132", fields="metricItems")
for metric in project.fields.metric_items or []:
    print(metric.text, metric.link)

# удалить все метрики
project = await tracker.update_entity(
    "project", "655f8cc523db2132", values={"metric_items": None}
)

# удалить одну метрику: объект нужен ровно таким, каким его вернул API
metric = project.fields.metric_items[0]
project = await tracker.update_entity(
    "project",
    "655f8cc523db2132",
    metric_items={
        "remove": metric.model_dump(mode="json", by_alias=True, exclude_none=True)
    },
)
```

Источники:
https://yandex.ru/support/tracker/ru/api/entities/keyresults,
https://yandex.ru/support/tracker/ru/api/entities/metric

### EntityKeyResult

Единственный ключевой результат цели, лежит в `entity.fields.key_result_items`.

| Поле       | Тип                          | Описание                                              |
|------------|-------------------------------|--------------------------------------------------------|
| `id`       | `str`                         | Идентификатор ключевого результата                     |
| `text`     | `str \| None`                 | Текст ключевого результата                             |
| `type`     | `str \| None`                 | Способ измерения прогресса: `"value"` или `"binary"`   |
| `deadline` | `EntityDeadline \| None`      | Дедлайн ключевого результата                           |
| `progress` | `EntityKeyResultProgress \| None` | Числовые показатели прогресса (для `type="value"`) |
| `achieved` | `bool \| None`                | Признак достижения (для `type="binary"`)               |
| `assignee` | `User \| None`                | Исполнитель ключевого результата                       |

### EntityKeyResultProgress

Числовые показатели прогресса ключевого результата (`progress`).

| Поле      | Тип             | Описание               |
|-----------|-----------------|--------------------------|
| `start`   | `float \| None` | Начальное значение показателя |
| `end`     | `float \| None` | Конечное значение показателя  |
| `current` | `float \| None` | Текущее значение показателя   |

### EntityMetricItem

Одна метрика сущности, лежит в `entity.fields.metric_items`.

| Поле   | Тип           | Описание                                                        |
|--------|---------------|--------------------------------------------------------------------|
| `id`   | `str`         | Идентификатор метрики                                              |
| `text` | `str \| None` | Название метрики                                                   |
| `link` | `str \| None` | Ссылка виджета для iframe. API называет это поле `url`, но в библиотеке `url` зарезервировано под `self`-ссылку объекта |
