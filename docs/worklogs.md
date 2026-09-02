# Учёт времени (worklogs)

Трекер позволяет фиксировать время, затраченное на задачу — так называемые worklog-записи.
`yatracker` предоставляет полный набор методов для работы с ними: создание, получение,
редактирование, удаление, а также поиск по всем задачам организации.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с worklog являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Формат длительности

Затраченное время (`duration`) Трекер принимает и возвращает в формате
[ISO 8601 duration](https://ru.wikipedia.org/wiki/ISO_8601#Продолжительности) — строке вида
`P1DT2H30M` (один день, два часа, тридцать минут).

Писать такие строки вручную неудобно, поэтому библиотека предоставляет вспомогательный класс
`Duration` (`yatracker.types.Duration`):

```python
from yatracker.types import Duration

duration = Duration(hours=5)
```

`Duration` — это `dataclass` со следующими полями (все по умолчанию равны `0`):

| Поле      | Значение          |
|-----------|-------------------|
| `years`   | количество лет    |
| `months`  | количество месяцев|
| `weeks`   | количество недель |
| `days`    | количество дней   |
| `hours`   | количество часов  |
| `minutes` | количество минут  |
| `seconds` | количество секунд |

У класса есть два метода преобразования:

```python
duration = Duration(days=1, hours=2, minutes=30)
duration.to_iso()  # 'P1DT2H30M'

Duration.from_iso("P1DT2H30M")  # Duration(days=1, hours=2, minutes=30, ...)
```

Во все методы, принимающие `duration`, можно передать либо готовую строку ISO 8601
(`'P1DT2H30M'`), либо объект `Duration` — библиотека сама вызовет `to_iso()` перед отправкой
запроса.

!!! note "Недели в длительностях"

    Формат ISO 8601 допускает указание длительности в неделях (`P2W`), и `Duration`
    поддерживает его через поле `weeks`. Обратите внимание: Яндекс Трекер считает время
    по рабочему календарю — неделя равна 5 рабочим дням, день — 8 часам. Например,
    `P5D` в ответе API может отображаться как `P1W`.

## Добавление записи о времени

```python
from datetime import datetime
from zoneinfo import ZoneInfo

from yatracker.types import Duration

worklog = await tracker.post_worklog(
    issue_id="WRITERS-1",
    start=datetime.now(ZoneInfo("Europe/Moscow")),
    duration=Duration(hours=5),
    comment="Работа над черновиком",
)
```

Сигнатура метода:

```python
async def post_worklog(
    issue_id: str,
    start: str | datetime,
    duration: str | Duration,
    comment: str | None = None,
) -> Worklog: ...
```

- `start` — момент начала работы. Можно передать `datetime` (рекомендуется использовать
  timezone-aware объекты — то есть созданные с указанием часового пояса) или готовую строку.
- `duration` — длительность работы: строка ISO 8601 или объект `Duration`.
- `comment` — необязательный комментарий к записи.

## Редактирование записи

```python
worklog = await tracker.edit_worklog(
    issue_id="WRITERS-1",
    worklog_id=worklog.id,
    duration=Duration(minutes=5),
)
```

Сигнатура:

```python
async def edit_worklog(
    issue_id: str,
    worklog_id: int,
    duration: str | Duration,
    comment: str | None = None,
) -> Worklog: ...
```

Изменить можно длительность и комментарий; изменить `start` этим методом нельзя.

## Удаление записи

```python
await tracker.delete_worklog("WRITERS-1", worklog.id)
```

Метод возвращает `True` при успешном удалении.

Того же можно добиться через сам объект `Worklog` — у него есть метод-хелпер `delete()`:

```python
await worklog.delete()
```

## Получение worklog-записей задачи

```python
worklogs = await tracker.get_issue_worklog("WRITERS-1")
```

Метод поддерживает пагинацию:

```python
worklogs = await tracker.get_issue_worklog(
    issue_id="WRITERS-1",
    per_page=100,  # (1)
    id_=100500,  # (2)
)
```

1. `per_page` — количество записей на странице (максимум 500).
2. `id_` — курсор пагинации: вернуть записи, идущие после worklog с данным id
   (соответствует query-параметру `id`).

## Поиск worklog-записей по всей организации

Метод `get_worklog` ищет worklog-записи не в одной задаче, а сразу по всей организации,
с фильтрацией по автору и/или диапазону дат создания:

```python
worklogs = await tracker.get_worklog(created_by="login")
```

```python
from datetime import datetime
from zoneinfo import ZoneInfo

worklogs = await tracker.get_worklog(
    created_by="login",
    created_at_from=datetime(2026, 1, 1, tzinfo=ZoneInfo("Europe/Moscow")),
    created_at_to=datetime(2026, 2, 1, tzinfo=ZoneInfo("Europe/Moscow")),
)
```

!!! note "Диапазон дат"

    `created_at_from` и `created_at_to` нужно указывать вместе — если задать только одну
    из границ, метод выбросит `ValueError`. Для `created_at_from` рекомендуется передавать
    timezone-aware `datetime`: при передаче "наивного" (без часового пояса) объекта
    библиотека выдаст `UserWarning`, так как API Трекера может некорректно обработать
    такое значение.

## Модель `Worklog`

| Поле         | Тип                | Описание                                     |
|--------------|--------------------|-----------------------------------------------|
| `url`        | `str`              | Ссылка на запись (в API — поле `self`)        |
| `id`         | `int`              | Идентификатор записи                          |
| `version`    | `int`              | Версия записи                                 |
| `issue`      | `Issue`            | Задача, к которой относится запись            |
| `created_by` | `User`             | Автор записи                                  |
| `updated_by` | `User \| None`     | Последний редактор записи                     |
| `created_at` | `datetime`         | Дата и время создания                         |
| `updated_at` | `datetime \| None` | Дата и время последнего изменения             |
| `start`      | `datetime`         | Момент начала работы                          |
| `duration`   | `str`              | Затраченное время в формате ISO 8601 duration |
| `comment`    | `str \| None`      | Комментарий к записи (если задан)             |
