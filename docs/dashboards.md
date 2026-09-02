# Дашборды

Дашборд (dashboard) — это страница с виджетами (диаграммами), которые показывают
метрики по задачам. `yatracker` предоставляет метод для создания дашборда и метод для
добавления на него виджета «Время цикла» (cycle time) — диаграммы, которая показывает,
сколько времени задачи проводят между двумя статусами.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с дашбордами являются асинхронными. В
    примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:

* [Создать дашборд](https://yandex.ru/support/tracker/ru/api/dashboards/create-dashboard)
* [Создать виджет «Время цикла»](https://yandex.ru/support/tracker/ru/api/dashboards/create-widget)

## Дашборд

### create_dashboard

```python
async def create_dashboard(
    self,
    name: str,
    *,
    layout: str | None = None,
    owner: str | int | dict[str, Any] | None = None,
) -> Dashboard: ...
```

Создаёт дашборд.

```python
dashboard = await tracker.create_dashboard(
    name="Метрики отдела",
    layout="two-columns",
    owner="login",
)
```

1. `name` — название дашборда (обязательное поле).
2. `layout` — расположение виджетов: `one-column` (по умолчанию), `two-columns`,
   `three-columns`, `narrow-left-wide-right` или `one-top-two-bottom`.
3. `owner` — логин или идентификатор владельца дашборда. Библиотека сама оборачивает
   строку/число в `{"id": ...}`, как того ожидает API; готовый словарь передаётся как
   есть. Если не указан, владельцем становится создатель дашборда.

Источник: https://yandex.ru/support/tracker/ru/api/dashboards/create-dashboard

## Виджет «Время цикла»

### create_cycle_time_widget

```python
async def create_cycle_time_widget(
    self,
    dashboard_id: str | int,
    description: str,
    *,
    query: str | None = None,
    filter_: dict[str, Any] | None = None,
    filter_id: str | int | None = None,
    from_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
    to_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
    excluded_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
    included_statuses: Sequence[str | Status | dict[str, Any]] | None = None,
    bucket: WidgetBucket | dict[str, Any] | None = None,
    calendar: str | int | None = None,
    lines: dict[str, Any] | None = None,
    start: str | None = None,
    end: str | None = None,
    mode: str | None = None,
    auto_updatable: bool | None = None,
    **kwargs,
) -> CycleTimeWidget: ...
```

Добавляет на существующий дашборд виджет с диаграммой «Время цикла».

```python
widget = await tracker.create_cycle_time_widget(
    dashboard.id,
    description="Время цикла разработки",
    query="Queue: TEST Assignee: me()",
    from_statuses=["open"],
    to_statuses=["closed"],
    bucket={"unit": "days", "count": 2},
    lines={
        "movingAverage": True,
        "standardDeviation": True,
        "percentile": [75, 90],
    },
    start="now()-2w",
    end="now()-2d",
    mode="common-lines-and-points",
    auto_updatable=True,
)
```

1. `dashboard_id` — идентификатор дашборда, на который добавляется виджет.
2. `description` — название виджета (обязательное поле).
3. `query` — источник задач на языке запросов.
4. `filter_` — источник задач по полям, например `{"queue": "TEST", "assignee":
   "username"}`. Отправляется как `filter`.
5. `filter_id` — идентификатор сохранённого фильтра (см. [«Фильтры»](filters.md)) как
   источник задач.
6. `from_statuses` — статусы, с которых начинается отсчёт времени работы над задачей;
   время в них не учитывается. По умолчанию — первый статус в истории задачи. Каждый
   элемент — ключ статуса (строка), объект `Status` (из ответа другого запроса, чтобы
   переиспользовать статус как есть) или готовый словарь `{"key": "..."}`. Одиночный
   статус вместо последовательности (`from_statuses="open"`) бросает `TypeError`:
   иначе строка была бы разобрана по символам.
7. `to_statuses` — статусы, на которых отсчёт заканчивается; если задача проходила
   через несколько из них, берётся самый поздний. По умолчанию — последний статус в
   истории задачи. Формат элементов такой же, как у `from_statuses`.
8. `excluded_statuses` — статусы, время в которых вычитается из расчёта.
9. `included_statuses` — статусы, время в которых добавляется к расчёту.
10. `bucket` — величина шага диаграммы, например `{"unit": "days", "count": 1}`, где
    `unit` — `days`, `weeks`, `months` или `sprints`, а `boardId` — идентификатор доски,
    используется только при `unit="sprints"`. По умолчанию — 7 дней. Принимается и
    объект `WidgetBucket` из ответа другого запроса: его поле `type` отправляется как
    `unit`, которого ждёт запрос, а незаполненные поля не отправляются.
11. `calendar` — идентификатор календаря рабочего времени. Если не указан, используется
    обычный календарь.
12. `lines` — настройки отображения оси времени, например `{"movingAverage": True,
    "standardDeviation": True, "percentile": [75, 90], "cakePercentile": 85}`.
13. `start` — формула начала расчётного периода, например `"now()-2w"`. По умолчанию —
    два года.
14. `end` — формула конца расчётного периода, например `"now()-2d"`. По умолчанию —
    `"now()"`.
15. `mode` — режим отображения данных: `common-lines` (только выбранные линии),
    `common-lines-and-points` (линии и точки, соответствующие задачам) или
    `status-lines` (линии по каждому статусу отдельно).
16. `auto_updatable` — обновляется ли диаграмма автоматически.
17. `kwargs` — любое другое поле виджета.

!!! warning "`bucket`, `calendar`, `lines`, `filter_` — сырые структуры"

    В отличие от именованных параметров верхнего уровня (`description`,
    `auto_updatable` и так далее), которые библиотека сама приводит к camelCase,
    словари `bucket`, `lines` и `filter_` отправляются **как есть**, без
    преобразования ключей. Значит, ключи внутри них нужно писать сразу в формате
    API — `movingAverage`, а не `moving_average`. Исключение — списки статусов
    (`from_statuses` и т. д.), которые собираются библиотекой из ключей статусов,
    объектов `Status` или словарей `{"key": "..."}`, и объект `WidgetBucket`,
    переданный в `bucket` вместо словаря.

!!! tip "Порядок источников задач"

    Если передать сразу несколько источников задач, Трекер использует только один —
    в таком порядке приоритета: `filter_id`, затем `query`, затем `filter_`.

Источник: https://yandex.ru/support/tracker/ru/api/dashboards/create-widget

## Модели

### Dashboard

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на дашборд. |
| `id` | `str` | Идентификатор дашборда. |
| `version` | `int` | Версия дашборда; увеличивается при каждом изменении. |
| `name` | `str` | Название дашборда. |
| `created_by` | `User` | Создатель дашборда. |
| `created_at` | `datetime` | Дата и время создания. |
| `layout` | `str \| None` | Расположение виджетов. |
| `owner` | `User \| None` | Владелец дашборда. |

### CycleTimeWidget

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на виджет. |
| `id` | `str` | Идентификатор виджета. |
| `version` | `int` | Версия виджета. |
| `description` | `str` | Название виджета. |
| `created_by` | `User \| None` | Создатель виджета. |
| `color` | `int \| None` | Служебный параметр. |
| `dashboard` | `Ref \| None` | Дашборд, на котором размещён виджет. |
| `from_statuses` | `list[Status] \| None` | Статусы, с которых начинается отсчёт времени работы. |
| `to_statuses` | `list[Status] \| None` | Статусы, на которых отсчёт заканчивается. |
| `excluded_statuses` | `list[Status] \| None` | Статусы, время в которых исключено из расчёта. Не встречается в примерах ответа справочника, но принимается в запросе. |
| `included_statuses` | `list[Status] \| None` | Статусы, время в которых добавлено к расчёту. Не встречается в примерах ответа справочника, но принимается в запросе. |
| `bucket` | `WidgetBucket \| None` | Величина шага диаграммы. |
| `calendar` | `WidgetCalendarRef \| None` | Календарь рабочего времени. |
| `query` | `str \| None` | Источник задач на языке запросов. |
| `filter_` | `dict[str, Any] \| None` | Источник задач по полям (JSON-ключ `filter`). |
| `filter_id` | `str \| None` | Идентификатор сохранённого фильтра-источника. |
| `dataset_info` | `WidgetDatasetInfo \| None` | Состояние расчёта данных виджета. |
| `lines` | `WidgetLines \| None` | Настройки оси времени. |
| `start` | `str \| None` | Формула начала расчётного периода. |
| `end` | `str \| None` | Формула конца расчётного периода. |
| `mode` | `str \| None` | Режим отображения данных. |

### WidgetBucket

Запрос называет период группировки `unit`, ответ — `type`; это одно и то же поле под
разными именами. Если передать объект `WidgetBucket` в `create_cycle_time_widget`,
библиотека переименует поле сама.

| Поле | Тип | Описание |
|---|---|---|
| `type` | `str \| None` | Период группировки: `days`, `weeks`, `months` или `sprints`. |
| `count` | `int \| None` | Количество периодов. Всегда `1` для `sprints`. |
| `board_id` | `str \| None` | Идентификатор доски, только для `sprints`. |

### WidgetCalendarRef

В отличие от `Ref`, объект не содержит ссылки `self`.

| Поле | Тип | Описание |
|---|---|---|
| `id` | `str` | Идентификатор календаря. |
| `display` | `str \| None` | Название календаря, отображаемое в интерфейсе. |

### WidgetDatasetInfo

| Поле | Тип | Описание |
|---|---|---|
| `status` | `str \| None` | Статус расчёта. |
| `build_started_at` | `datetime \| None` | Момент запуска расчёта. |
| `built_by` | `User \| None` | Пользователь, от имени которого выполняется расчёт. |

### WidgetLines

| Поле | Тип | Описание |
|---|---|---|
| `moving_average` | `bool \| None` | Показывать ли линию скользящего среднего. |
| `standard_deviation` | `bool \| None` | Показывать ли полосу стандартного отклонения. |
| `percentile` | `list[float] \| None` | Перцентили, для которых строится диаграмма. |
| `cake_percentile` | `float \| None` | Перцентиль для диаграммы по статусам. |

## Полный пример

```python
import asyncio

from yatracker import YaTracker

ORG_ID = ...
TOKEN = ...


async def main() -> None:
    tracker = YaTracker(ORG_ID, TOKEN)

    dashboard = await tracker.create_dashboard(
        name="Метрики отдела",
        layout="one-column",
    )

    widget = await tracker.create_cycle_time_widget(
        dashboard.id,
        description="Время цикла разработки",
        query="Queue: TEST",
        from_statuses=["open"],
        to_statuses=["closed"],
        bucket={"unit": "weeks", "count": 1},
        lines={"movingAverage": True, "percentile": [75, 90]},
        mode="common-lines",
    )

    print(widget.id, widget.dataset_info.status if widget.dataset_info else None)

    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
```
