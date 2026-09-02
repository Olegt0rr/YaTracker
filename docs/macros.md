# Макросы

Макрос (macro) — это именованный набор действий над задачей в очереди: комментарий по
шаблону и/или изменение полей задачи. В отличие от массовых операций и импорта, макрос
не выполняется автоматически — пользователь запускает его вручную из интерфейса задачи,
а `yatracker` предоставляет методы для получения списка макросов очереди, их создания,
изменения и удаления.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с макросами являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Получение макросов

### get_macros

```python
async def get_macros(
    self,
    queue_id: str | int,
    per_page: int | None = None,
    page: int | None = None,
) -> list[Macro]: ...
```

Возвращает список макросов очереди.

```python
macros = await tracker.get_macros("WRITERS")

for macro in macros:
    print(macro.id, macro.name)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `per_page` — количество макросов на странице (по умолчанию 50).
3. `page` — номер страницы (по умолчанию 1).

В справочнике этого запроса параметры пагинации не описаны, но Трекер разбивает на
страницы по 50 объектов любые списки. Если макросов в очереди больше, используйте
`per_page` и `page`.

Источник: https://yandex.ru/support/tracker/ru/get-macroses

### get_macro

```python
async def get_macro(self, queue_id: str | int, macro_id: str | int) -> Macro: ...
```

Возвращает один макрос очереди по его идентификатору.

```python
macro = await tracker.get_macro("WRITERS", 3)

print(macro.name, macro.body)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `macro_id` — идентификатор макроса.

Источник: https://yandex.ru/support/tracker/ru/get-macros

## Создание макроса

### create_macro

```python
async def create_macro(
    self,
    queue_id: str | int,
    name: str,
    *,
    body: str | None = None,
    issue_update: dict[str, Any] | Iterable[MacroFieldChange] | None = None,
) -> Macro: ...
```

Создаёт новый макрос в указанной очереди.

```python
macro = await tracker.create_macro(
    "WRITERS",
    name="Закрыть с тегом",
    body="Готово, {{currentUser}}!\n{{currentDateTime}}",
    issue_update={
        "tags": {"add": "готово"},
        "resolution": None,
    },
)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `name` — название макроса (обязательное поле).
3. `body` — необязательный текст комментария, который будет опубликован при запуске
   макроса. Поддерживает шаблонные плейсхолдеры: `{{currentDateTime}}` (дата и время
   выполнения макроса), `{{issue.author}}` (автор задачи), `{{currentUser}}`
   (пользователь, запустивший макрос).
4. `issue_update` — необязательный словарь с изменениями полей задачи, ключи которого —
   идентификаторы полей. Значением может быть:
      * обычное значение — поле будет установлено (`{"description": "New task"}`);
      * словарь с одним из операторов `set`, `add` или `remove` —
        `{"tags": {"add": "New tag"}}`;
      * `None` — поле будет очищено. `None` внутри `issue_update` не отбрасывается
        библиотекой и уходит в запрос как JSON `null` (в отличие от `None` у именованных
        параметров верхнего уровня, которые в запрос просто не попадают).

    Ключи-идентификаторы приводятся к camelCase так же, как в `bulk_update_issues`
    (`story_points` → `storyPoints`); идентификаторы локальных полей вида
    `64a51c6d866ea82411abe756--userId` отправляются как есть. Вместо словаря можно
    передать `macro.issue_update` другого макроса — список `MacroFieldChange` будет
    преобразован в формат запроса автоматически.

Источник: https://yandex.ru/support/tracker/ru/post-macros

## Изменение и удаление макроса

### update_macro

```python
async def update_macro(
    self,
    queue_id: str | int,
    macro_id: str | int,
    name: str,
    *,
    body: str | dict[str, Any] | None = None,
    issue_update: dict[str, Any] | Iterable[MacroFieldChange] | None = None,
) -> Macro: ...
```

Изменяет существующий макрос.

```python
macro = await tracker.update_macro(
    "WRITERS",
    macro_id=3,
    name="Закрыть с тегом",
    body={"unset": 1},
)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `macro_id` — идентификатор макроса.
3. `name` — название макроса. В отличие от `update_component`, здесь API требует
   передавать `name` при каждом изменении, даже если оно не меняется.
4. `body` — новый текст комментария в том же формате, что и в `create_macro`; либо
   `{"unset": 1}` — специальное значение, которое удаляет текст комментария из макроса.
5. `issue_update` — набор изменений полей, который должен применять макрос, в том же
   формате, что и в `create_macro`. Считайте его полным набором, а не патчем: API не
   описывает слияние с уже сохранёнными изменениями, поэтому, чтобы их сохранить,
   начинайте с `macro.issue_update_payload()` или передайте `macro.issue_update` целиком.

!!! note "У макросов нет версии"

    В отличие от компонентов, у макросов нет параметра `version` — конфликт
    параллельного изменения через `PATCH` не отслеживается.

Источник: https://yandex.ru/support/tracker/ru/patch-macros

### delete_macro

```python
async def delete_macro(self, queue_id: str | int, macro_id: str | int) -> bool: ...
```

Удаляет макрос. Возвращает `True` при успехе.

```python
await tracker.delete_macro("WRITERS", 3)
```

1. `queue_id` — ключ или идентификатор очереди.
2. `macro_id` — идентификатор макроса.

Источник: https://yandex.ru/support/tracker/ru/delete-macros

!!! note "Асимметрия запроса и ответа"

    В запросах `create_macro`/`update_macro` параметр `issue_update` — это словарь,
    ключи которого — идентификаторы полей задачи (как показано выше). В ответе же
    (`Macro.issue_update`) Трекер возвращает список объектов `MacroFieldChange`: у
    каждого есть `field` (`FieldRef` с `url`, `id`, `display` — короткая ссылка на
    изменённое поле) и `update` — как правило, словарь оператора и значения, например
    `{"add": ["tag 1", "tag 2"]}`. Перевести ответ обратно в формат запроса можно
    методом `macro.issue_update_payload()` — он возвращает словарь
    `{field.id: update}`; `create_macro` и `update_macro` также принимают
    `macro.issue_update` напрямую.

## Типичный сценарий

Запустить макрос через API нельзя — его выполняет пользователь из интерфейса Трекера.
Зато можно получить макросы очереди, найти нужный по имени, посмотреть, что он будет
делать, и дописать к его изменениям полей ещё одно, не потеряв существующие:

```python
macros = await tracker.get_macros("WRITERS")
macro = next(m for m in macros if m.name == "Закрыть с тегом")

for change in macro.issue_update:
    print(change.field.id, change.update)

macro = await tracker.update_macro(
    "WRITERS",
    macro_id=macro.id,
    name=macro.name,
    issue_update={
        **macro.issue_update_payload(),
        "tags": {"add": "проверено"},
    },
)
```
