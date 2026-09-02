# Доски и спринты

Доска (board) — это настраиваемое представление задач в виде канбан- или скрам-доски: у неё
есть название, набор колонок (columns), необязательный бэклог и набор спринтов. Колонка
определяет, какие статусы задач в неё попадают. Спринт (sprint) — это отрезок времени работы
по доске: у него есть даты начала и окончания и статус (`draft`, `in_progress`, `released`,
`archived`). `yatracker` предоставляет методы для получения, создания и изменения досок, их
колонок и спринтов.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с досками и спринтами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

!!! note "Версии и `If-Match`"

    Колонки досок и спринты используют оптимистичную блокировку (optimistic locking): чтобы
    изменить или удалить объект, нужно передать его текущую версию — библиотека кладёт её
    в заголовок `If-Match` в кавычках, как того требует API (`If-Match: "2"`). Если версия
    устарела, то есть кто-то успел изменить объект раньше вас, Трекер отвечает
    `412 Precondition Failed`, и библиотека бросает `PreconditionFailedError` — подробнее
    в разделе [«Обработка ошибок»](errors.md). В этом случае объект нужно перечитать и
    повторить запрос уже с актуальной версией.

    Важно: методы работы с **колонками** (`create_board_column`, `update_board_column`,
    `delete_board_column`) принимают версию **доски** (`Board.version`), а не колонки — у
    самой колонки отдельной версии нет. Методы работы со **спринтами** принимают версию
    спринта (`FullSprint.version`).

!!! warning "`POST /boards/` не используется"

    Официальный запрос на создание доски `POST /boards/` считается устаревшим и игнорирует
    тело запроса. Поэтому `create_board` отправляет `POST /liveBoards/` — то же самое
    действие, но с рабочим телом запроса.

## Доски

### get_boards

```python
async def get_boards(self) -> list[Board]: ...
```

Возвращает список всех досок, доступных пользователю, без пагинации.

```python
boards = await tracker.get_boards()

for board in boards:
    print(board.id, board.name)
```

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards

### get_boards_paginated

```python
async def get_boards_paginated(
    self,
    per_page: int | None = None,
    id_: str | int | None = None,
) -> list[Board]: ...
```

Возвращает одну страницу досок. Пагинация здесь не такая, как у большинства других списков:
она относительная, а не по номеру страницы. Доски отсортированы по возрастанию `id`, и
чтобы получить следующую страницу, нужно передать `id` последней доски предыдущей страницы.

```python
page = await tracker.get_boards_paginated(per_page=50)
next_page = await tracker.get_boards_paginated(per_page=50, id_=page[-1].id)
```

1. `per_page` — количество досок на странице, не больше `500`.
2. `id_` — `id` последней доски предыдущей страницы; для первой страницы не передаётся.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-boards-paginate

### iter_boards

Чтобы не управлять пагинацией вручную, используйте `iter_boards` — асинхронный генератор
поверх `get_boards_paginated`:

```python
async def iter_boards(self, per_page: int | None = None) -> AsyncIterator[Board]: ...
```

```python
async for board in tracker.iter_boards(per_page=50):
    print(board.id, board.name)
```

1. `per_page` — количество досок, запрашиваемых за один вызов `get_boards_paginated`.

Итерация останавливается, когда очередная страница оказывается пустой.

### get_board

```python
async def get_board(self, board_id: str | int) -> Board: ...
```

Возвращает одну доску по идентификатору.

```python
board = await tracker.get_board(1)
```

1. `board_id` — идентификатор доски.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-board

### create_board

```python
async def create_board(
    self,
    name: str,
    *,
    owner: str | int | None = None,
    board_permissions_template: str | None = None,
    backlog_available: bool | None = None,
    sprints_available: bool | None = None,
    columns: list[BoardColumnParams] | None = None,
    backlog_columns: list[BoardColumnParams] | None = None,
    non_parametrized_columns: list[BoardColumnParams] | None = None,
    auto_filters: dict[str, Any] | None = None,
) -> Board: ...
```

Создаёт новую доску.

```python
from yatracker.types import BoardColumnParams

board = await tracker.create_board(
    name="My board",
    owner="login",
    board_permissions_template="private",
    columns=[
        BoardColumnParams(name="To Do", statuses=["new", "open"], limit=10),
    ],
    backlog_columns=[
        BoardColumnParams(name="Later", limit=5),
    ],
)
```

1. `name` — название доски.
2. `owner` — логин или идентификатор владельца доски (строка или число).
3. `board_permissions_template` — `"private"` или `"public"` (по умолчанию у Трекера —
   `"public"`).
4. `backlog_available` — показывать ли на доске бэклог.
5. `sprints_available` — включены ли спринты для доски.
6. `columns`, `backlog_columns`, `non_parametrized_columns` — списки `BoardColumnParams`:
   облегчённого, по сравнению с `BoardColumn` из ответа, описания колонки для запроса —
   `name`, необязательный список ключей статусов `statuses` (для колонок бэклога и
   непараметризованных колонок статусы не указываются) и необязательный `limit` — лимит
   задач в колонке.
7. `auto_filters` — настройки автофильтра доски, отправляются как есть (недокументированная
   внутренняя структура), например:

    ```python
    auto_filters = {
        "addFilter": {
            "liveFilter": {
                "fieldValues": {
                    "queue": [{"fixed": "DEV"}],
                    "assignee": [{"fixed": "login"}],
                },
            },
            "enabled": True,
        },
        "removeFilter": {
            "statuses": ["closed"],
            "checkResolutionPresence": True,
            "maxTimeInToRemoveState": "P6W",
            "enabled": True,
        },
    }
    ```

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/post-board

### update_board

```python
async def update_board(
    self,
    board_id: str | int,
    *,
    version: str | int | None = None,
    name: str | None = None,
    backlog_available: bool | None = None,
    sprints_available: bool | None = None,
    columns: list[BoardColumnParams] | None = None,
    backlog_columns: list[BoardColumnParams] | None = None,
    non_parametrized_columns: list[BoardColumnParams] | None = None,
) -> Board: ...
```

Изменяет существующую доску. Владелец доски (`owner`) через этот метод не меняется — такого
поля в запросе на изменение доски у API нет.

```python
board = await tracker.update_board(
    board_id=board.id,
    version=board.version,
    name="Renamed board",
)
```

1. `board_id` — идентификатор доски.
2. `version` — текущая версия доски (`board.version`). Если передать её, библиотека положит
   значение в заголовок `If-Match`, и Трекер ответит `412 Precondition Failed` (у библиотеки —
   `PreconditionFailedError`) при устаревшей версии. Если не передавать `version`, запрос
   уйдёт без `If-Match`, без защиты от параллельного изменения.
3. `name`, `backlog_available`, `sprints_available`, `columns`, `backlog_columns`,
   `non_parametrized_columns` — необязательные поля для изменения, как в `create_board`.
   Значение `None` означает «не менять».

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-board

### delete_board

```python
async def delete_board(self, board_id: str | int) -> bool: ...
```

Удаляет доску. Возвращает `True` при успехе.

```python
await tracker.delete_board(board.id)
```

1. `board_id` — идентификатор доски.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-board

## Колонки

### get_board_columns

```python
async def get_board_columns(self, board_id: str | int) -> list[BoardColumn]: ...
```

Возвращает список колонок доски.

```python
columns = await tracker.get_board_columns(board.id)

for column in columns:
    print(column.id, column.name)
```

1. `board_id` — идентификатор доски.

Тот же список доступен и на самой модели — см. `Board.get_columns()` ниже.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-columns

### get_board_column

```python
async def get_board_column(
    self,
    board_id: str | int,
    column_id: str | int,
) -> BoardColumn: ...
```

Возвращает одну колонку доски.

```python
column = await tracker.get_board_column(board.id, columns[0].id)
```

1. `board_id` — идентификатор доски.
2. `column_id` — идентификатор колонки.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-column

### create_board_column

```python
async def create_board_column(
    self,
    board_id: str | int,
    version: str | int,
    name: str,
    statuses: list[str],
) -> BoardColumn: ...
```

Создаёт новую колонку на доске.

```python
column = await tracker.create_board_column(
    board_id=board.id,
    version=board.version,
    name="Approve",
    statuses=["needInfo", "adjustment"],
)
```

1. `board_id` — идентификатор доски.
2. `version` — текущая версия **доски** (см. заметку про версии выше), уходит в заголовок
   `If-Match`.
3. `name` — название колонки.
4. `statuses` — ключи статусов, которые попадают в колонку.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/post-column

### update_board_column

```python
async def update_board_column(
    self,
    board_id: str | int,
    column_id: str | int,
    version: str | int,
    *,
    name: str | None = None,
    statuses: list[str] | None = None,
) -> BoardColumn: ...
```

Изменяет колонку доски. Передаются только те поля, которые нужно обновить.

```python
column = await tracker.update_board_column(
    board_id=board.id,
    column_id=column.id,
    version=board.version,
    name="In progress",
)
```

1. `board_id` — идентификатор доски.
2. `column_id` — идентификатор колонки.
3. `version` — текущая версия доски.
4. `name`, `statuses` — необязательные поля для изменения. `None` означает «не менять».

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-column

### delete_board_column

```python
async def delete_board_column(
    self,
    board_id: str | int,
    column_id: str | int,
    version: str | int,
) -> bool: ...
```

Удаляет колонку доски. Возвращает `True` при успехе.

```python
await tracker.delete_board_column(board.id, column.id, board.version)
```

1. `board_id` — идентификатор доски.
2. `column_id` — идентификатор колонки.
3. `version` — текущая версия доски.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-column

## Спринты

В задачах (`FullIssue.sprint`) спринт представлен короткой ссылкой `Sprint` (`url`, `id`,
`display`) — её достаточно, чтобы показать, к какому спринту относится задача. Методы этого
раздела работают с полным объектом `FullSprint`, где есть версия, доска, даты и статус.

### get_sprints

```python
async def get_sprints(self, board_id: str | int) -> list[FullSprint]: ...
```

Возвращает список спринтов доски.

```python
sprints = await tracker.get_sprints(board.id)

for sprint in sprints:
    print(sprint.id, sprint.name, sprint.status)
```

1. `board_id` — идентификатор доски.

Тот же список доступен и на самой модели — см. `Board.get_sprints()` ниже.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprints

### get_sprint

```python
async def get_sprint(self, sprint_id: str | int) -> FullSprint: ...
```

Возвращает один спринт по идентификатору.

```python
sprint = await tracker.get_sprint(4411)
```

1. `sprint_id` — идентификатор спринта.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/get-sprint

### create_sprint

```python
async def create_sprint(
    self,
    name: str,
    board_id: str | int,
    start_date: date | str,
    end_date: date | str,
) -> FullSprint: ...
```

Создаёт новый спринт на доске.

```python
from datetime import date

sprint = await tracker.create_sprint(
    name="Sprint 1",
    board_id=board.id,
    start_date=date(2026, 1, 1),
    end_date=date(2026, 1, 14),
)
```

1. `name` — название спринта.
2. `board_id` — идентификатор доски, на которой создаётся спринт.
3. `start_date`, `end_date` — даты начала и окончания спринта: объект `datetime.date`
   (или `datetime`) или готовая строка `YYYY-MM-DD`.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/post-sprint

### update_sprint

```python
async def update_sprint(
    self,
    sprint_id: str | int,
    version: str | int,
    *,
    name: str | None = None,
    start_date: date | str | None = None,
    end_date: date | str | None = None,
    status: str | None = None,
) -> FullSprint: ...
```

Изменяет спринт. Передаются только те поля, которые нужно обновить.

```python
sprint = await tracker.update_sprint(
    sprint_id=sprint.id,
    version=sprint.version,
    end_date="2026-01-21",
)
```

1. `sprint_id` — идентификатор спринта.
2. `version` — текущая версия спринта (`sprint.version`), уходит в заголовок `If-Match`.
3. `name`, `start_date`, `end_date`, `status` — необязательные поля для изменения.
   `status` — один из `draft`, `in_progress`, `released`, `archived`. `None` означает
   «не менять».

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/patch-sprint

### start_sprint

```python
async def start_sprint(
    self, sprint_id: str | int, version: str | int
) -> FullSprint: ...
```

Переводит спринт в статус `in_progress`.

```python
sprint = await tracker.start_sprint(sprint.id, sprint.version)
```

1. `sprint_id` — идентификатор спринта.
2. `version` — текущая версия спринта, уходит в заголовок `If-Match`.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/start-sprint

### archive_sprint

```python
async def archive_sprint(
    self, sprint_id: str | int, version: str | int
) -> FullSprint: ...
```

Переводит спринт в статус `archived`.

```python
sprint = await tracker.archive_sprint(sprint.id, sprint.version)
```

1. `sprint_id` — идентификатор спринта.
2. `version` — текущая версия спринта, уходит в заголовок `If-Match`.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/archive-sprint

### delete_sprint

```python
async def delete_sprint(self, sprint_id: str | int) -> bool: ...
```

Удаляет спринт. Возвращает `True` при успехе.

```python
await tracker.delete_sprint(sprint.id)
```

1. `sprint_id` — идентификатор спринта.

Источник: https://yandex.cloud/ru/docs/tracker/concepts/boards/delete-sprint

## Типичный сценарий

Создать доску с колонками, прочитать её колонки через удобный метод модели, затем создать
и сразу запустить спринт:

```python
from yatracker.types import BoardColumnParams

board = await tracker.create_board(
    name="Sprint board",
    sprints_available=True,
    columns=[
        BoardColumnParams(name="To Do", statuses=["open"]),
        BoardColumnParams(name="Done", statuses=["closed"]),
    ],
)

columns = await board.get_columns()

sprint = await tracker.create_sprint(
    name="Sprint 1",
    board_id=board.id,
    start_date="2026-01-01",
    end_date="2026-01-14",
)
sprint = await tracker.start_sprint(sprint.id, sprint.version)
```
