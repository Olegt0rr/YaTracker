# Отчёты по задачам

Отчёт (report) — это выгрузка задач, подходящих под критерии поиска, в файл (`xlsx`, `xml`
или `csv`). Отчёты живут по адресу `/entities/report` — том же префиксе `/entities`, что и
проекты нового API (см. [«Проекты, портфели и цели»](entities.md)), но со своим типом
сущности `report`. `yatracker` предоставляет методы для создания отчёта и поиска уже
созданных отчётов.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с отчётами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/issues/create-report

!!! note "Открыть отчёт можно только в интерфейсе"

    API создаёт и ищет отчёты, но не отдаёт их содержимое: файл выгрузки открывается в
    интерфейсе Трекера по адресу `https://tracker.yandex.ru/pages/reports/<id>`, где `<id>`
    — поле `Report.id` из ответа.

## Создание отчёта

### create_report

```python
async def create_report(
    self,
    summary: str,
    *,
    fields: str | Sequence[str] | None = None,
    format_: str = "xlsx",
    query: str | None = None,
    filter_: dict[str, Any] | None = None,
    filter_id: str | int | None = None,
    sorts: Sequence[ReportSort | dict[str, Any]] | None = None,
    type_: str = "issueFilterExport",
) -> Report: ...
```

Создаёт отчёт по задачам, найденным на языке запросов:

```python
report = await tracker.create_report(
    summary="Выгрузка задач очереди SUPPORT",
    query='Queue: SUPPORT "Sort by": Updated DESC',
    fields=["priority", "type", "key", "summary", "assignee", "status", "updated"],
)
```

1. `summary` — название отчёта (обязательное поле).
2. `fields` — идентификаторы полей задачи, которые попадут в отчёт: последовательность имён
   (`["priority", "type", "key", "summary", "assignee", "status", "updated"]`) либо строка
   с теми же именами через запятую (`"priority,type,key"`) — её метод сам разобьёт в
   JSON-массив, которого ждёт API.
3. `format_` — формат выгрузки: `"xlsx"`, `"xml"` или `"csv"` (по умолчанию `"xlsx"`).
4. `query`, `filter_`, `filter_id` — три взаимоисключающих способа задать критерии поиска
   задач для отчёта; ровно один из них обязателен (см. предупреждение ниже):
      * `query` — запрос на языке запросов Tracker, как в `find_issues` (см.
        [«Работа с задачами»](issues.md));
      * `filter_` — словарь `поле: значение`, например
        `{"queue": "TREK", "assignee": "empty()"}`;
      * `filter_id` — ID сохранённого фильтра.
5. `sorts` — правила сортировки задач в отчёте: последовательность объектов `ReportSort`
   (или уже готовых словарей `{"orderBy": ..., "orderAsc": ...}`).
6. `type_` — тип экспорта. Единственное документированное значение — `"issueFilterExport"`
   (используется по умолчанию).

!!! warning "`query`, `filter_` и `filter_id` взаимоисключающие, но один обязателен"

    Ровно один из трёх параметров должен быть задан — метод сам это проверяет и бросает
    `ValueError`, если задано больше одного (API не поддерживает одновременное
    использование нескольких способов фильтрации) или если не задано ни одного (API
    требует указать, какие задачи выгружать).

```python
from yatracker.types import ReportSort

report = await tracker.create_report(
    summary="Задачи без исполнителя",
    filter_={"queue": "TREK", "assignee": "empty()"},
    fields=["key", "summary", "status", "priority", "created"],
    sorts=[ReportSort(order_by="updated", order_asc=False)],
)
```

```python
report = await tracker.create_report(
    summary="Отчёт по сохранённому фильтру",
    filter_id=12345,
    fields=["key", "summary", "status", "assignee", "priority", "updated"],
)
```

Источник: https://yandex.ru/support/tracker/ru/api/issues/create-report

## Поиск отчётов

### search_reports

```python
async def search_reports(
    self,
    *,
    filter_: dict[str, Any] | None = None,
    order_by: str | None = None,
    order_asc: bool | None = None,
    per_page: int | None = None,
    page: int | None = None,
) -> ReportSearchResult: ...
```

Ищет уже созданные отчёты:

```python
result = await tracker.search_reports(filter_={"author": "login"})

for report in result.values:
    print(report.id, report.short_id, report.created_at)
```

1. `filter_` — фильтр отчётов. Поддерживаются только ключи `id`, `shortId` и `author` —
   словарь уходит в тело запроса как есть, без переименования `snake_case → camelCase`
   (в отличие от именованных параметров методов), поэтому `shortId` нужно передавать
   именно в этом регистре.
2. `order_by` — поле для сортировки: `"id"`, `"shortId"`, `"createdBy"`, `"createdAt"`,
   `"updatedAt"` или `"self"`.
3. `order_asc` — направление сортировки: по возрастанию, если `True`.
4. `per_page` — количество отчётов на странице (по умолчанию 50).
5. `page` — номер страницы (по умолчанию 1).

```python
result = await tracker.search_reports(
    filter_={"author": "login"},
    order_by="createdAt",
    order_asc=False,
    per_page=10,
)
```

`ReportSearchResult` — страница результатов, а не просто список: `hits` — общее число
найденных отчётов, `pages` — количество страниц, `values` — отчёты текущей страницы,
`order_by` — поле сортировки (заполняется, только если `order_by` передавался в запросе;
значения `createdBy`, `createdAt` и `updatedAt` при этом возвращаются как `author`,
`created` и `updated` соответственно).

Источник: https://yandex.ru/support/tracker/ru/api/issues/search-reports

## Модели

### Report

| Поле          | Тип                | Описание                                                                          |
|---------------|---------------------|----------------------------------------------------------------------------------|
| `url`         | `str`              | Ссылка на отчёт (в API — поле `self`)                                            |
| `id`          | `str`              | ID отчёта — используется в ссылке `https://tracker.yandex.ru/pages/reports/<id>` |
| `version`     | `int`              | Версия отчёта                                                                     |
| `short_id`    | `int`              | Короткий ID отчёта                                                                |
| `entity_type` | `str`              | Тип сущности, всегда `"report"`                                                  |
| `created_by`  | `User`             | Автор отчёта                                                                       |
| `created_at`  | `datetime`         | Дата и время создания                                                             |
| `updated_at`  | `datetime \| None` | Дата и время последнего обновления                                                |

### ReportSort

| Поле        | Тип            | Описание                                             |
|-------------|-----------------|-------------------------------------------------------|
| `order_by`  | `str`          | Поле задачи для сортировки                            |
| `order_asc` | `bool \| None` | Направление сортировки: по возрастанию, если `True`   |

### ReportSearchResult

| Поле       | Тип             | Описание                                                                                                                    |
|------------|------------------|------------------------------------------------------------------------------------------------------------------------------|
| `hits`     | `int`           | Общее количество найденных отчётов                                                                                          |
| `pages`    | `int`           | Общее количество страниц выдачи                                                                                              |
| `values`   | `list[Report]`  | Отчёты текущей страницы                                                                                                      |
| `order_by` | `str \| None`   | Поле сортировки — заполняется только если `order_by` передавался в запросе; `createdBy`/`createdAt`/`updatedAt` возвращаются как `author`/`created`/`updated` |
