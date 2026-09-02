# Поля задач

Yandex Tracker различает два вида полей задач: глобальные поля (`/fields`) — они доступны в
задачах всех очередей организации — и локальные поля очереди (`/queues/{id}/localFields`) —
такое поле видно и доступно для заполнения только в задачах той очереди, к которой оно
привязано. Каждое поле принадлежит категории (`## Категории полей`), которая определяет, в
каком разделе интерфейса настройки полей оно отображается.

Идентификатор локального поля состоит из шестнадцатеричного префикса и ключа поля,
например `603fb94c38bbe658********--myfield`, и его нужно использовать целиком при чтении
или записи значения поля в задаче — так же, как это описано в разделе
[«Работа с пользовательскими полями»](custom_fields.md). А вот методы работы с самим полем
(`get_local_field`, `update_local_field`) адресуют поле по его короткому `key`
(`myfield`), без префикса очереди — префикс возвращает только `LocalField.id`.

Создание и изменение полей и категорий полей — административные операции: они требуют прав
администратора организации в Трекере, точно так же, как аналогичные действия в интерфейсе
Трекера (Настройки → Поля).

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с полями задач являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/issues/fields

## Глобальные поля

### get_global_fields

```python
async def get_global_fields(self) -> list[IssueField]: ...
```

Возвращает список всех глобальных полей организации.

```python
fields = await tracker.get_global_fields()

for field in fields:
    print(field.id, field.name, field.field_schema.type)
```

Источник: https://yandex.ru/support/tracker/ru/api/issues/get-global-fields

### get_field

```python
async def get_field(self, field_id: str | int) -> IssueField: ...
```

Возвращает параметры одного поля задачи — глобального или локального, идентификатор
локального поля указывается с префиксом очереди.

```python
field = await tracker.get_field("ruName")
```

1. `field_id` — идентификатор поля.

Источник: https://yandex.ru/support/tracker/ru/api/issues/get-issue-fields

### create_field

```python
async def create_field(
    self,
    name: LocalizedName | dict[str, str],
    field_id: str,
    category: str,
    type_: str,
    *,
    options_provider: QueueFieldOptionsProvider | dict[str, Any] | None = None,
    order: int | None = None,
    description: str | None = None,
    readonly: bool | None = None,
    visible: bool | None = None,
    hidden: bool | None = None,
    container: bool | None = None,
) -> IssueField: ...
```

Создаёт новое глобальное поле задачи.

```python
from yatracker.types.localized_name import LocalizedName

field = await tracker.create_field(
    name=LocalizedName(en="My field", ru="Моё поле"),
    field_id="myglobalfield",
    category="0000000000000003********",
    type_="ru.yandex.startrek.core.fields.StringFieldType",
    options_provider={
        "type": "FixedListOptionsProvider",
        "values": ["первый элемент", "второй элемент", "третий элемент"],
    },
)
```

1. `name` — локализованное название поля, `LocalizedName(en=..., ru=...)` или обычный
   словарь `{"en": ..., "ru": ...}`.
2. `field_id` — идентификатор нового поля, отправляется как `id`.
3. `category` — идентификатор категории поля; список категорий отдаёт `GET /fields/categories`
   (см. `## Категории полей`).
4. `type_` — тип поля, отправляется как `type`, см. `!!! tip` ниже.
5. `options_provider` — выпадающий список значений поля, см. `!!! tip` ниже.
6. `order` — порядковый номер поля в списке полей организации.
7. `description` — описание поля.
8. `readonly` — `True`, если значение поля нельзя изменить.
9. `visible` — `True`, чтобы всегда показывать поле в интерфейсе.
10. `hidden` — `True`, чтобы скрывать поле даже тогда, когда оно заполнено.
11. `container` — `True`, если в поле можно указать сразу несколько значений (доступно для
    строковых полей, полей с именем пользователя и выпадающих списков).

Поля со значением `None` не отправляются.

Источник: https://yandex.ru/support/tracker/ru/api/issues/create-field

### update_field

```python
async def update_field(
    self,
    field_id: str | int,
    version: str | int,
    *,
    name: LocalizedName | dict[str, str] | None = None,
    category: str | None = None,
    order: int | None = None,
    description: str | None = None,
    readonly: bool | None = None,
    visible: bool | None = None,
    hidden: bool | None = None,
    options_provider: QueueFieldOptionsProvider | dict[str, Any] | None = None,
) -> IssueField: ...
```

Изменяет глобальное поле задачи. В официальной документации это два отдельных запроса —
«Изменить название поля задачи» и «Изменить возможные значения поля задачи», — но у обоих
один и тот же HTTP-эндпоинт (`PATCH /fields/{id}`), поэтому `update_field` объединяет их в
одном методе: передавайте только те параметры, которые нужно изменить.

```python
field = await tracker.update_field(
    field_id="myglobalfield",
    version=field.version,
    name={"en": "Renamed field", "ru": "Переименованное поле"},
    options_provider={
        "type": "FixedListOptionsProvider",
        "values": ["значение 1", "значение 2"],
    },
)
```

1. `field_id` — идентификатор изменяемого поля.
2. `version` — текущая версия поля (`field.version`), отправляется как query-параметр
   `?version=`. Если поле успели изменить параллельно, Трекер отвечает `412 Precondition
   Failed`.
3. `name`, `category`, `order`, `description`, `readonly`, `visible`, `hidden`,
   `options_provider` — новые значения соответствующих параметров, как в `create_field`.

Поля со значением `None` не отправляются, то есть остаются без изменений.

Источник:

* https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-name
* https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-value

!!! warning "`version` — это query-параметр, а не заголовок"

    В отличие от досок и спринтов (см. [«Доски и спринты»](boards.md)), где версия объекта
    уходит в заголовок `If-Match`, здесь версия передаётся как часть URL:
    `PATCH /fields/{id}?version=<версия>`. Библиотека собирает эту строку сама —
    достаточно передать `version` обычным именованным параметром.

## Категории полей

Категория — это группа, к которой относится поле; в интерфейсе Трекера категории образуют
разделы на странице настройки полей. Список существующих категорий возвращает поле
`category` каждого поля (короткая ссылка `Ref`); отдельного метода для получения списка всех
категорий в `yatracker` нет, так как официальный `GET /fields/categories` не задокументирован
как самостоятельный публичный эндпоинт — сравните `category` в ответах `get_global_fields`
или `get_field`.

### create_field_category

```python
async def create_field_category(
    self,
    name: LocalizedName | dict[str, str],
    order: int,
    *,
    description: str | None = None,
) -> FieldCategory: ...
```

Создаёт новую категорию полей.

```python
from yatracker.types.localized_name import LocalizedName

category = await tracker.create_field_category(
    name=LocalizedName(en="My category", ru="Моя категория"),
    order=400,
)
```

1. `name` — локализованное название категории.
2. `order` — вес категории в интерфейсе; категории с меньшим весом отображаются выше.
3. `description` — описание категории.

Источник: https://yandex.ru/support/tracker/ru/api/issues/create-issue-field-category

### update_field_category

```python
async def update_field_category(
    self,
    category_id: str | int,
    *,
    version: str | int | None = None,
    name: LocalizedName | dict[str, str] | None = None,
    order: int | None = None,
    description: str | None = None,
) -> FieldCategory: ...
```

Изменяет существующую категорию полей.

```python
category = await tracker.update_field_category(
    category_id=category.id,
    version=category.version,
    order=100,
)
```

1. `category_id` — идентификатор изменяемой категории.
2. `version` — текущая версия категории (`category.version`), отправляется как
   query-параметр `?version=`. Изменения вносятся только в текущую версию категории.
3. `name`, `order`, `description` — новые значения соответствующих параметров, как в
   `create_field_category`.

Поля со значением `None` не отправляются, то есть остаются без изменений.

Источник: https://yandex.ru/support/tracker/ru/api/issues/patch-issue-field-category

## Локальные поля очереди

### get_local_fields

```python
async def get_local_fields(self, queue_id: str | int) -> list[LocalField]: ...
```

Возвращает список локальных полей очереди.

```python
fields = await tracker.get_local_fields("HELP")

for field in fields:
    print(field.id, field.key, field.name)
```

1. `queue_id` — идентификатор или ключ очереди (ключ чувствителен к регистру символов).

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-local-fields

### get_local_field

```python
async def get_local_field(self, queue_id: str | int, field_key: str) -> LocalField: ...
```

Возвращает одно локальное поле очереди.

```python
field = await tracker.get_local_field("HELP", "userId")
```

1. `queue_id` — идентификатор или ключ очереди.
2. `field_key` — ключ локального поля (значение `key` из объектов, возвращаемых
   `get_local_fields`, а не префиксованный идентификатор `<hex>--key`).

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-info-local-field

### create_local_field

```python
async def create_local_field(
    self,
    queue_id: str | int,
    name: LocalizedName | dict[str, str],
    field_id: str,
    category: str,
    type_: str,
    *,
    options_provider: QueueFieldOptionsProvider | dict[str, Any] | None = None,
    order: int | None = None,
    description: str | None = None,
    readonly: bool | None = None,
    visible: bool | None = None,
    hidden: bool | None = None,
    container: bool | None = None,
) -> LocalField: ...
```

Создаёт локальное поле, привязанное к очереди.

```python
from yatracker.types.localized_name import LocalizedName

field = await tracker.create_local_field(
    "HELP",
    name=LocalizedName(en="User ID", ru="Идентификатор пользователя"),
    field_id="userId",
    category="0000000000000003********",
    type_="ru.yandex.startrek.core.fields.IntegerFieldType",
)
```

1. `queue_id` — идентификатор или ключ очереди.
2. `name` — локализованное название поля.
3. `field_id` — ключ нового локального поля, отправляется как `id`. Созданное поле получит
   префиксованный идентификатор `<hex>--<field_id>` (значение `LocalField.id`), а `field_id`
   останется его коротким `key`.
4. `category` — идентификатор категории поля.
5. `type_` — тип поля, см. `!!! tip` ниже.
6. `options_provider` — выпадающий список значений поля, см. `!!! tip` ниже.
7. `order` — порядковый номер поля в списке полей организации.
8. `description` — описание поля.
9. `readonly` — `True`, если значение поля нельзя изменить.
10. `visible` — `True`, чтобы всегда показывать поле в интерфейсе.
11. `hidden` — `True`, чтобы скрывать поле даже тогда, когда оно заполнено.
12. `container` — `True`, если в поле можно указать сразу несколько значений.

Поля со значением `None` не отправляются.

Источник: https://yandex.ru/support/tracker/ru/api/queues/create-local-field

### update_local_field

```python
async def update_local_field(
    self,
    queue_id: str | int,
    field_key: str,
    *,
    name: LocalizedName | dict[str, str] | None = None,
    category: str | None = None,
    order: int | None = None,
    description: str | None = None,
    options_provider: QueueFieldOptionsProvider | dict[str, Any] | None = None,
    readonly: bool | None = None,
    visible: bool | None = None,
    hidden: bool | None = None,
) -> LocalField: ...
```

Изменяет локальное поле очереди.

```python
field = await tracker.update_local_field(
    "HELP",
    field_key="userId",
    description="Новое описание",
    visible=True,
)
```

1. `queue_id` — идентификатор или ключ очереди.
2. `field_key` — ключ локального поля (как в `get_local_field`, без префикса очереди).
3. `name`, `category`, `order`, `description`, `options_provider`, `readonly`, `visible`,
   `hidden` — новые значения соответствующих параметров, как в `create_local_field`.

Поля со значением `None` не отправляются, то есть остаются без изменений.

Источник: https://yandex.ru/support/tracker/ru/api/queues/edit-local-field

!!! warning "У локальных полей нет `version`"

    В отличие от `update_field`, этот метод не принимает `version` и не отправляет
    `?version=` — официальный запрос на редактирование локального поля версию не
    документирует, а значит и не проверяет конфликт параллельного изменения.

!!! tip "Тип поля, выпадающие списки и поисковые подсказки"

    Параметр `type_` у `create_field` и `create_local_field` — один из классов Трекера:
    `ru.yandex.startrek.core.fields.DateFieldType` (дата),
    `...DateTimeFieldType` (дата/время),
    `...StringFieldType` (текстовое однострочное поле),
    `...TextFieldType` (текстовое многострочное поле),
    `...FloatFieldType` (дробное число),
    `...IntegerFieldType` (целое число),
    `...UserFieldType` (имя пользователя),
    `...UriFieldType` (ссылка),
    `...MoneyFieldType` (деньги),
    `...MoneyWithRateFieldType` (деньги и ставка),
    `...TimeTrackingDurationFieldType` (продолжительность). Клиент не проверяет это
    значение — enum принадлежит серверу, ошибку при недопустимом значении вернёт сам
    Трекер.

    `options_provider` описывает выпадающий список поля: `type` — `FixedListOptionsProvider`
    для строковых или целочисленных полей и `FixedUserListOptionsProvider` для полей с
    именем пользователя, `values` — до 3000 значений списка (в выпадающем меню
    показывается не более 10 элементов сразу). Ответы дополнительно несут `needValidation`
    (`QueueFieldOptionsProvider.need_validation`) — признак, требует ли Трекер валидации
    значений при их вводе; это поле только читается, задать его через API нельзя.

    `suggest_provider` и `query_provider` (класс поисковой подсказки и класс языка запроса
    соответственно) есть только в ответах и не могут быть изменены через API.

## Модели

### `IssueField`

Наследует все поля `QueueField` (таблица ниже) и добавляет:

| Поле | Тип | Описание |
| --- | --- | --- |
| `key` | `str \| None` | Ключ поля. |
| `description` | `str \| None` | Описание поля. |
| `suggest_provider` | `FieldSuggestProvider \| None` | Класс поисковой подсказки. |
| `category` | `Ref \| None` | Ссылка на категорию поля. |
| `type` | `str \| None` | Тип поля, например `standard` или `local`. |

### `LocalField`

Наследует все поля `IssueField` и добавляет:

| Поле | Тип | Описание |
| --- | --- | --- |
| `queue` | `Queue \| None` | Ссылка на очередь, к которой привязано поле. В ответе на создание поля отсутствует. |

### `FieldCategory`

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на категорию (ключ `self`). |
| `id` | `str` | Идентификатор категории. |
| `name` | `str` | Название категории (обычная строка, а не объект локализации, как в теле запроса). |
| `version` | `int` | Версия категории, увеличивается при каждом изменении. |

### `FieldSuggestProvider`

| Поле | Тип | Описание |
| --- | --- | --- |
| `type` | `str` | Класс поисковой подсказки, например `UserSuggestProvider`. |

### `LocalizedName`

Используется только в запросах (`name=`) — ответы возвращают название поля или категории
как обычную строку.

| Поле | Тип | Описание |
| --- | --- | --- |
| `en` | `str \| None` | Название на английском языке. |
| `ru` | `str \| None` | Название на русском языке. |

### `QueueField` и связанные модели

Базовый класс `IssueField`, который также описывает поля, возвращаемые
`GET /queues/{id}/fields`.

| Поле | Тип | Описание |
| --- | --- | --- |
| `url` | `str` | Ссылка на поле (ключ `self`). |
| `id` | `str` | Идентификатор поля. |
| `name` | `str` | Название поля. |
| `version` | `int` | Версия поля, увеличивается при каждом изменении. |
| `field_schema` | `QueueFieldSchema` | Тип данных значения поля (API-ключ `schema`). |
| `readonly` | `bool` | `True`, если значение поля нельзя изменить. |
| `options` | `bool` | `False`, если список значений ограничен настройками организации. |
| `suggest` | `bool` | `True`, если при вводе значения показывается поисковая подсказка. |
| `options_provider` | `QueueFieldOptionsProvider \| None` | Допустимые значения поля. |
| `query_provider` | `QueueFieldQueryProvider \| None` | Класс языка запроса. |
| `order` | `int` | Порядковый номер поля в списке полей организации. |

`QueueFieldSchema`:

| Поле | Тип | Описание |
| --- | --- | --- |
| `type` | `str` | Тип данных значения поля, например `string` или `array`. |
| `required` | `bool \| None` | `True`, если поле обязательно для заполнения. |
| `items` | `str \| None` | Тип элементов, если `type` — `array`. |

`QueueFieldOptionsProvider`:

| Поле | Тип | Описание |
| --- | --- | --- |
| `type` | `str` | Тип поставщика значений, например `FixedListOptionsProvider`. |
| `values` | `dict[str, list] \| list \| None` | Значения поля: либо плоский список, либо объект вида `{"DIRECT": [...]}`. |
| `defaults` | `list \| None` | Значения по умолчанию. |
| `need_validation` | `bool \| None` | Требуется ли валидация вводимых значений (API-ключ `needValidation`). |

`QueueFieldQueryProvider`:

| Поле | Тип | Описание |
| --- | --- | --- |
| `type` | `str` | Класс языка запроса, например `StringOptionalQueryProvider`. |
