# Административные справочники

Типы задач, статусы, резолюции и приоритеты — общие справочники уровня организации: один
список для всех очередей, а не отдельная настройка каждой из них. Получить содержимое
справочника может любой пользователь с доступом к API, а вот создание новой записи и
изменение существующей требуют **прав администратора** Трекера. `yatracker` предоставляет
методы для получения, создания и изменения всех четырёх справочников.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы со справочниками являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Типы задач

### get_issue_types

```python
async def get_issue_types(self) -> list[FullIssueType]: ...
```

Возвращает список всех типов задач организации.

```python
from yatracker.types import FullIssueType

issue_types: list[FullIssueType] = await tracker.get_issue_types()

for issue_type in issue_types:
    print(issue_type.key, issue_type.name)
```

Источник: https://yandex.ru/support/tracker/ru/api/admin/get-issue-types

### create_issue_type

```python
async def create_issue_type(
    self,
    key: str,
    name: LocalizedName | dict[str, str],
) -> FullIssueType: ...
```

Создаёт новый тип задачи. Требует прав администратора.

```python
from yatracker.types import LocalizedName

issue_type = await tracker.create_issue_type(
    key="client",
    name=LocalizedName(ru="Клиент", en="Customer"),
)
```

1. `key` — ключ типа задачи.
2. `name` — название типа задачи на каждом языке: `LocalizedName(ru="Клиент", en="Customer")`
   или обычный словарь `{"ru": "Клиент", "en": "Customer"}`.

Источник: https://yandex.ru/support/tracker/ru/api/admin/create-issue-type

### update_issue_type

```python
async def update_issue_type(
    self,
    issue_type_id: str | int,
    *,
    version: str | int | None = None,
    name: LocalizedName | dict[str, str] | None = None,
) -> FullIssueType: ...
```

Изменяет название существующего типа задачи. Требует прав администратора.

```python
issue_type = await tracker.update_issue_type(
    issue_type.id,
    version=issue_type.version,
    name={"ru": "Покупатель", "en": "Customer"},
)
```

1. `issue_type_id` — идентификатор или ключ типа задачи.
2. `version` — текущая версия типа задачи (`issue_type.version`).
3. `name` — новое название типа задачи на каждом языке. Поля, оставленные `None`, не
   отправляются и не меняются.

!!! warning "Версия — это query-параметр, а не заголовок"

    В отличие от досок и спринтов (см. [«Доски и спринты»](boards.md)), где версия
    передаётся в заголовке `If-Match`, здесь она уходит в строку запроса как
    `?version=<версия>`. Если версия устарела — кто-то успел изменить тип задачи
    раньше вас, — Трекер отвечает `409 Conflict`, и библиотека бросает
    `AlreadyExistsError` (см. [«Обработка ошибок»](errors.md)): перечитайте объект и
    повторите запрос с его актуальной версией. Отдельно от версии, `423 Locked`
    означает, что превышено максимальное значение самого счётчика версии (`10100`).

Источник: https://yandex.ru/support/tracker/ru/api/admin/patch-issue-type

## Статусы

### get_statuses

```python
async def get_statuses(self) -> list[FullStatus]: ...
```

Возвращает список всех статусов задач организации.

```python
statuses = await tracker.get_statuses()

for status in statuses:
    print(status.key, status.name, status.type)
```

Источник: https://yandex.ru/support/tracker/ru/api/admin/get-statuses

### create_status

```python
async def create_status(
    self,
    key: str,
    name: LocalizedName | dict[str, str],
    type_: str,
) -> FullStatus: ...
```

Создаёт новый статус задачи. Требует прав администратора.

```python
from yatracker.types import LocalizedName

status = await tracker.create_status(
    key="myStatus",
    name=LocalizedName(ru="Мой статус", en="My status"),
    type_="paused",
)
```

1. `key` — ключ статуса. Только латинские буквы, должен начинаться с маленькой буквы.
2. `name` — название статуса на каждом языке.
3. `type_` — тип статуса: `"new"`, `"inProgress"`, `"paused"`, `"done"` или `"cancelled"`.
   Отправляется как `type`.

Источник: https://yandex.ru/support/tracker/ru/api/admin/create-status

### update_status

```python
async def update_status(
    self,
    status_id: str | int,
    *,
    version: str | int | None = None,
    name: LocalizedName | dict[str, str] | None = None,
    description: str | None = None,
    order: int | None = None,
    type_: str | None = None,
) -> FullStatus: ...
```

Изменяет существующий статус задачи. Требует прав администратора.

```python
status = await tracker.update_status(
    status.id,
    version=status.version,
    description="Задача поставлена на паузу",
    order=10,
)
```

1. `status_id` — идентификатор или ключ статуса.
2. `version` — текущая версия статуса (`status.version`).
3. `name` — новое название статуса на каждом языке.
4. `description` — новое описание статуса.
5. `order` — новый вес статуса; влияет на порядок отображения в интерфейсе.
6. `type_` — новый тип статуса: `"new"`, `"inProgress"`, `"paused"`, `"done"` или
   `"cancelled"`. Отправляется как `type`.

    Поля, оставленные `None`, не отправляются и не меняются.

!!! warning "Версия — это query-параметр, код конфликта другой"

    Как и у `update_issue_type`, версия уходит в строку запроса как `?version=<версия>`,
    а не в заголовок `If-Match`. Но для статусов устаревшая версия даёт **другой** код
    ошибки, чем у остальных трёх справочников: `412 Precondition Failed`, и библиотека
    бросает `PreconditionFailedError` (см. [«Обработка ошибок»](errors.md)), а не
    `AlreadyExistsError`. Перечитайте объект и повторите запрос с его актуальной версией.
    `423 Locked` здесь означает то же самое, что и у других справочников: превышено
    максимальное значение счётчика версии (`10100`).

Источник: https://yandex.ru/support/tracker/ru/api/admin/patch-status

## Резолюции

### get_resolutions

```python
async def get_resolutions(self) -> list[FullResolution]: ...
```

Возвращает список всех резолюций организации.

```python
resolutions = await tracker.get_resolutions()

for resolution in resolutions:
    print(resolution.key, resolution.name)
```

Источник: https://yandex.ru/support/tracker/ru/api/admin/get-resolutions

### create_resolution

```python
async def create_resolution(
    self,
    key: str,
    name: LocalizedName | dict[str, str],
) -> FullResolution: ...
```

Создаёт новую резолюцию. Требует прав администратора.

```python
from yatracker.types import LocalizedName

resolution = await tracker.create_resolution(
    key="wontFix",
    name=LocalizedName(ru="Не будет исправлено", en="Won't be fixed"),
)
```

1. `key` — ключ резолюции. Только латинские буквы, должен начинаться с маленькой буквы.
2. `name` — название резолюции на каждом языке.

Источник: https://yandex.ru/support/tracker/ru/api/admin/create-resolution

### update_resolution

```python
async def update_resolution(
    self,
    resolution_id: str | int,
    *,
    version: str | int | None = None,
    name: LocalizedName | dict[str, str] | None = None,
    description: str | None = None,
    order: int | None = None,
) -> FullResolution: ...
```

Изменяет существующую резолюцию. Требует прав администратора.

```python
resolution = await tracker.update_resolution(
    resolution.id,
    version=resolution.version,
    order=5,
)
```

1. `resolution_id` — идентификатор или ключ резолюции.
2. `version` — текущая версия резолюции (`resolution.version`).
3. `name` — новое название резолюции на каждом языке.
4. `description` — новое описание резолюции.
5. `order` — новый вес резолюции; влияет на порядок отображения в интерфейсе.

    Поля, оставленные `None`, не отправляются и не меняются.

!!! warning "Версия — это query-параметр, а не заголовок"

    Версия уходит в строку запроса как `?version=<версия>`, а не в заголовок `If-Match`.
    Если версия устарела, Трекер отвечает `409 Conflict`, и библиотека бросает
    `AlreadyExistsError` (см. [«Обработка ошибок»](errors.md)) — так же, как для типов
    задач и приоритетов. Перечитайте объект и повторите запрос с его актуальной версией.
    `423 Locked` означает, что превышено максимальное значение счётчика версии (`10100`).

Источник: https://yandex.ru/support/tracker/ru/api/admin/patch-resolution

## Приоритеты

### get_priorities

```python
async def get_priorities(self, localized: bool = True) -> list[Priority]: ...
```

Возвращает список приоритетов для задачи.

```python
priorities = await tracker.get_priorities()

for priority in priorities:
    print(priority.key, priority.name)

# названия сразу на всех языках
priorities_all_langs = await tracker.get_priorities(localized=False)
```

1. `localized` — `True` (по умолчанию) — в ответе `name` содержит название только на
   языке пользователя (обычная строка). `False` — `name` содержит названия на всех
   языках сразу (объект, где ключ — код языка).

Источник: https://yandex.ru/support/tracker/ru/api/admin/get-priorities

### create_priority

```python
async def create_priority(
    self,
    key: str,
    name: LocalizedName | dict[str, str],
    order: int,
    description: str,
) -> Priority: ...
```

Создаёт новый приоритет. Требует прав администратора. Справочник документирует все
параметры этого запроса как обязательные.

```python
from yatracker.types import LocalizedName

priority = await tracker.create_priority(
    key="one",
    name=LocalizedName(ru="Название на русском", en="English name"),
    order=60,
    description="Описание",
)
```

1. `key` — ключ приоритета.
2. `name` — название приоритета на каждом языке.
3. `order` — вес приоритета; влияет на порядок отображения в интерфейсе.
4. `description` — описание приоритета.

Источник: https://yandex.ru/support/tracker/ru/api/admin/create-priority

### update_priority

```python
async def update_priority(
    self,
    priority_id: str | int,
    *,
    version: str | int | None = None,
    name: LocalizedName | dict[str, str] | None = None,
    description: str | None = None,
) -> Priority: ...
```

Изменяет существующий приоритет. Требует прав администратора. Запрос не может изменить
значок приоритета, отображаемый в интерфейсе Трекера.

```python
priority = await tracker.update_priority(
    priority.id,
    version=priority.version,
    description="Обновлённое описание",
)
```

1. `priority_id` — идентификатор или ключ приоритета.
2. `version` — текущая версия приоритета (`priority.version`).
3. `name` — новое название приоритета на каждом языке.
4. `description` — новое описание приоритета.

    Поля, оставленные `None`, не отправляются и не меняются.

!!! warning "Версия — это query-параметр, а не заголовок"

    Версия уходит в строку запроса как `?version=<версия>`, а не в заголовок `If-Match`.
    Если версия устарела, Трекер отвечает `409 Conflict`, и библиотека бросает
    `AlreadyExistsError` (см. [«Обработка ошибок»](errors.md)) — так же, как для типов
    задач и резолюций. Перечитайте объект и повторите запрос с его актуальной версией.
    `423 Locked` означает, что превышено максимальное значение счётчика версии (`10100`).

Источник: https://yandex.ru/support/tracker/ru/api/admin/patch-priority

## Модели

### FullIssueType

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на объект. |
| `id` | `str` | Идентификатор типа задачи. |
| `version` | `int` | Версия типа задачи. |
| `key` | `str` | Ключ типа задачи. |
| `name` | `str` | Название типа задачи, отображаемое в интерфейсе. |
| `description` | `str \| None` | Описание типа задачи. |
| `deleted` | `bool \| None` | `True`, если тип задачи удалён; при отсутствии поле не передаётся API. |

### FullStatus

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на объект. |
| `id` | `str` | Идентификатор статуса. |
| `version` | `int` | Версия статуса. |
| `key` | `str` | Ключ статуса. |
| `name` | `str` | Название статуса, отображаемое в интерфейсе. |
| `description` | `str \| None` | Описание статуса. |
| `order` | `int \| None` | Вес статуса; влияет на порядок отображения в интерфейсе. |
| `type` | `str \| None` | Тип статуса: `"new"`, `"inProgress"`, `"paused"`, `"done"` или `"cancelled"`. |

### FullResolution

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на объект. |
| `id` | `str` | Идентификатор резолюции. |
| `version` | `int` | Версия резолюции. |
| `key` | `str` | Ключ резолюции. |
| `name` | `str` | Название резолюции, отображаемое в интерфейсе. |
| `description` | `str \| None` | Описание резолюции. |
| `order` | `int \| None` | Вес резолюции; влияет на порядок отображения в интерфейсе. |

### Priority

| Поле | Тип | Описание |
|---|---|---|
| `url` | `str` | Ссылка на объект. |
| `id` | `str` | Идентификатор приоритета. |
| `key` | `str` | Ключ приоритета. |
| `display` | `str \| None` | Название, отображаемое в интерфейсе. Заполнено только у короткой ссылки, встроенной в задачу. |
| `version` | `int \| None` | Версия приоритета. |
| `name` | `str \| dict \| None` | Название приоритета. При `localized=False` — объект с названиями на всех языках, а не строка. |
| `description` | `str \| None` | Описание приоритета. |
| `order` | `int \| None` | Вес приоритета; влияет на порядок отображения в интерфейсе. |

`Priority` обслуживает сразу два случая ответа API: полный объект из методов этого раздела
и короткую ссылку, встроенную в задачу (`FullIssue.priority`) — поэтому все поля, кроме
`url`, `id` и `key`, необязательны.

### LocalizedName

| Поле | Тип | Описание |
|---|---|---|
| `en` | `str \| None` | Название на английском. |
| `ru` | `str \| None` | Название на русском. |

`LocalizedName` — это формат **запроса** для `name` (`create_issue_type`, `create_status`,
`create_resolution`, `create_priority` и их `update_*`-аналоги). Вместо него можно передать
обычный словарь `{"ru": ..., "en": ...}`: обе формы объединены псевдонимом
`LocalizedNameInput = LocalizedName | dict[str, str]` (`yatracker.types.localized_name`),
который и стоит в аннотациях `name` — в сигнатурах ниже союз для наглядности выписан
целиком. В **ответе** же, наоборот, `name` — просто строка на языке пользователя (кроме
`get_priorities(localized=False)`, см. выше).

!!! note "Короткие ссылки в задачах не меняются"

    Всё, что описано на этой странице, — это полные объекты справочников. Короткие
    ссылки, встроенные в задачу (`FullIssue.type`, `FullIssue.status`,
    `FullIssue.resolution`), остаются моделями `IssueType`, `Status` и `Resolution` —
    у каждой всего четыре поля: `url`, `id`, `key`, `display`. Эта страница их не меняет.
