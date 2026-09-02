# Права доступа к очереди

Права доступа (permissions) определяют, кто может создавать и читать задачи очереди, кто
может их редактировать, кто может менять настройки самой очереди и кому доступ к очереди
запрещён. Права можно выдавать персонально пользователю, группе целиком или роли
(автору, исполнителю, наблюдателю задачи и любому, у кого уже есть доступ). У компонентов
очереди есть собственный, более узкий набор прав того же вида. `yatracker` предоставляет
методы для просмотра прав пользователя и группы в очереди и в компоненте, а также для
изменения прав доступа к очереди.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с правами доступа являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/queues/manage-access

## Права доступа к очереди

### get_queue_user_access

```python
async def get_queue_user_access(
    self,
    queue_id: str | int,
    user_id: str | int,
) -> QueueUserAccess: ...
```

Возвращает права пользователя в очереди — независимо от того, выданы они лично, через
группу, в которую входит пользователь, или через роль.

```python
access = await tracker.get_queue_user_access("WRITERS", "login")

print(access.user.display)

for permission, grantees in access.permissions.items():
    print(permission, [u.display for u in grantees.users or []])

if access.components:
    print([c.display for c in access.components])
```

1. `queue_id` — ключ или идентификатор очереди (ключ чувствителен к регистру символов).
2. `user_id` — логин или идентификатор пользователя.

`access.permissions` — словарь, ключи которого — `GRANT` (настройки очереди), `CREATE`
(создание задач), `READ` (просмотр задач), `WRITE` (редактирование задач) и `DENY`
(доступ запрещён); значение — `QueueAccessGrantees` с пользователями, группами и ролями,
у которых есть данное разрешение. `access.components` — компоненты очереди, к которым у
пользователя есть доступ (может быть `None`).

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-user-access

### get_queue_group_access

```python
async def get_queue_group_access(
    self,
    queue_id: str | int,
    group_id: str | int,
) -> QueueGroupAccess: ...
```

Возвращает права группы в очереди — то же самое, что `get_queue_user_access`, но для
группы целиком, без объединения с личными разрешениями участников.

```python
access = await tracker.get_queue_group_access("WRITERS", 5)

print(access.group.display)

for permission, grantees in access.permissions.items():
    print(permission, [g.display for g in grantees.groups or []])
```

1. `queue_id` — ключ или идентификатор очереди (ключ чувствителен к регистру символов).
2. `group_id` — идентификатор группы в организации.

`access.permissions` — словарь по тем же ключам, что и у `get_queue_user_access`
(`GRANT`, `CREATE`, `READ`, `WRITE`, `DENY`). `access.components` — компоненты очереди,
доступные группе (может быть `None`).

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-group-access

## Изменение прав доступа

### update_queue_access

```python
async def update_queue_access(
    self,
    queue_id: str | int,
    *,
    create: QueueAccessUpdate | dict[str, Any] | None = None,
    read: QueueAccessUpdate | dict[str, Any] | None = None,
    write: QueueAccessUpdate | dict[str, Any] | None = None,
    grant: QueueAccessUpdate | dict[str, Any] | None = None,
    deny: QueueAccessUpdate | dict[str, Any] | None = None,
) -> QueuePermissions: ...
```

Настраивает права доступа к очереди. Нужно указать хотя бы одно из пяти разрешений:
`create` (создание задач), `read` (просмотр задач), `write` (редактирование задач),
`grant` (изменение настроек очереди) и `deny` (запрет доступа к очереди). Каждое из них
принимает `QueueAccessUpdate` или равносильный словарь с полями `users`, `groups` и
`roles`, а каждое из этих полей — значение в одной из двух форм.

**Список идентификаторов перезаписывает** текущих обладателей разрешения:

```python
permissions = await tracker.update_queue_access(
    "TESTQUEUE",
    create={"users": ["user1"]},
    write={"users": ["user1"]},
)
```

**Объект `{"add": [...], "remove": [...]}` добавляет и отзывает** обладателей
разрешения, не трогая остальных. Его можно передать как обычный словарь либо собрать из
моделей `QueueAccessUpdate`/`QueueAccessChange`:

```python
from yatracker.types.queue_permissions import QueueAccessChange, QueueAccessUpdate

# через модели
permissions = await tracker.update_queue_access(
    "TESTQUEUE",
    grant=QueueAccessUpdate(
        users=QueueAccessChange(add=["user1"], remove=[12345]),
    ),
)

# то же самое через обычные словари, без импорта моделей
permissions = await tracker.update_queue_access(
    "TESTQUEUE",
    grant={"users": {"add": ["user1"], "remove": [12345]}},
)
```

Разные разрешения в одном вызове можно комбинировать, а разные поля одного разрешения —
задавать в разных формах:

```python
permissions = await tracker.update_queue_access(
    "TESTQUEUE",
    write={
        "users": {"remove": ["username1", "username2"]},
        "groups": {"add": [4]},
        "roles": {"add": ["author", "assignee"]},
    },
    read={
        "groups": {"add": [4]},
        "roles": {"add": ["follower"]},
    },
)
```

Запретить доступ к очереди (для `deny` доступны только `users` и `groups` — роли
запретить нельзя):

```python
permissions = await tracker.update_queue_access("TESTQUEUE", deny={"users": ["user1"]})
```

1. `queue_id` — ключ или идентификатор очереди (ключ чувствителен к регистру символов).
2. `create`, `read`, `write`, `grant` — грантополучатели соответствующего разрешения.
3. `deny` — грантополучатели, которым запрещён доступ к очереди; допускаются только
   `users` и `groups`.
4. Разрешения, оставленные `None`, не отправляются и остаются без изменений.

Внутри `QueueAccessUpdate` (и равносильного словаря) поля адресуют грантополучателей
по-разному:

* `users` — по логину, `uid`, `passportUid`, `cloudUid` или `trackerUid`;
* `groups` — по числовому идентификатору группы (см. `GET /groups`);
* `roles` — по одной из строк `author`, `assignee`, `follower`, `access`.

Возвращает `QueuePermissions` — актуальные права доступа очереди после изменения; в
ответе присылаются только те разрешения, у которых есть хотя бы один грантополучатель.

Источник: https://yandex.ru/support/tracker/ru/api/queues/manage-access

## Права доступа к компоненту

У компонента нет разрешения `GRANT` (настройки компонента через права не защищены) —
только `CREATE`, `READ`, `WRITE` и `DENY`.

### get_component_user_access

```python
async def get_component_user_access(
    self,
    component_id: str | int,
    user_id: str | int,
) -> ComponentUserAccess: ...
```

Возвращает права пользователя относительно компонента.

```python
access = await tracker.get_component_user_access(1, "login")

print(access.component.name)

for permission, grantees in access.permissions.items():
    print(permission, [u.display for u in grantees.users or []])
```

1. `component_id` — идентификатор компонента.
2. `user_id` — логин или идентификатор пользователя.

`access.permissions` — словарь по ключам `CREATE`, `READ`, `WRITE`, `DENY`.

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-component-user-access

### get_component_group_access

```python
async def get_component_group_access(
    self,
    component_id: str | int,
    group_id: str | int,
) -> ComponentGroupAccess: ...
```

Возвращает права группы относительно компонента.

```python
access = await tracker.get_component_group_access(1, 5)

print(access.component.name)

for permission, grantees in access.permissions.items():
    print(permission, [g.display for g in grantees.groups or []])
```

1. `component_id` — идентификатор компонента.
2. `group_id` — идентификатор группы в организации.

`access.permissions` — словарь по тем же ключам, что и у `get_component_user_access`
(`CREATE`, `READ`, `WRITE`, `DENY`).

Источник: https://yandex.ru/support/tracker/ru/api/queues/get-component-group-access

!!! tip "Отдельный запрос для каждой пары «пользователь/группа — очередь/компонент»"

    В отличие от `update_queue_access`, который меняет права сразу для многих
    грантополучателей одним запросом, узнать текущие права можно только по одному
    пользователю или группе за раз — массового запроса «права всех пользователей
    очереди» в API нет.

## Модели

### QueueAccessChange

Объектная форма записи `users` / `groups` / `roles` в `update_queue_access`: вместо
перезаписи текущих грантополучателей списком идентификаторов добавляет и отзывает их.

| Поле     | Тип                        | Описание                              |
|----------|-----------------------------|----------------------------------------|
| `add`    | `list[str \| int] \| None` | Идентификаторы, которым выдаётся разрешение |
| `remove` | `list[str \| int] \| None` | Идентификаторы, у которых разрешение отзывается |

### QueueAccessUpdate

Грантополучатели одного разрешения в `update_queue_access`. Каждое поле принимает либо
простой список идентификаторов (текущие грантополучатели перезаписываются), либо
`QueueAccessChange` (грантополучатели добавляются/отзываются). Нужно задать хотя бы одно
поле.

| Поле     | Тип                                              | Описание                                       |
|----------|---------------------------------------------------|-------------------------------------------------|
| `users`  | `list[str \| int] \| QueueAccessChange \| None`  | Пользователи, к которым применяется разрешение |
| `groups` | `list[str \| int] \| QueueAccessChange \| None`  | Группы, к которым применяется разрешение        |
| `roles`  | `list[str] \| QueueAccessChange \| None`         | Роли, к которым применяется разрешение. Недопустимо для `deny` |

### QueueAccessGrantees

Пользователи, группы и роли, у которых есть одно конкретное разрешение. Встречается и в
значениях словаря `permissions` запросов `get_queue_user_access` / `get_queue_group_access`
/ `get_component_user_access` / `get_component_group_access`, и в полях `create` / `read`
/ `write` / `grant` / `deny` ответа `update_queue_access` (`QueuePermissions`) — `url`
приходит только во втором случае.

| Поле     | Тип                | Описание                                    |
|----------|---------------------|-----------------------------------------------|
| `url`    | `str \| None`      | Ссылка на объект разрешения (в API — `self`) |
| `users`  | `list[User] \| None` | Пользователи, обладающие разрешением лично   |
| `groups` | `list[Ref] \| None`  | Группы, обладающие разрешением                |
| `roles`  | `list[Ref] \| None`  | Роли, обладающие разрешением                  |

### QueuePermissions

Результат `update_queue_access`. В ответе присылаются только те разрешения, у которых
есть хотя бы один грантополучатель — остальные поля будут `None`.

| Поле      | Тип                        | Описание                                    |
|-----------|-----------------------------|-----------------------------------------------|
| `url`     | `str`                      | Ссылка на объект прав доступа (в API — `self`) |
| `version` | `int`                      | Версия прав доступа; увеличивается при каждом изменении |
| `create`  | `QueueAccessGrantees \| None` | Право на создание задач в очереди          |
| `read`    | `QueueAccessGrantees \| None` | Право на чтение задач очереди              |
| `write`   | `QueueAccessGrantees \| None` | Право на редактирование задач очереди      |
| `grant`   | `QueueAccessGrantees \| None` | Право на изменение настроек очереди        |
| `deny`    | `QueueAccessGrantees \| None` | Запрещённый доступ к очереди                |

### QueueUserAccess

Результат `get_queue_user_access`.

| Поле          | Тип                                   | Описание                                          |
|---------------|-----------------------------------------|-----------------------------------------------------|
| `user`        | `User`                                 | Пользователь, для которого выполнен запрос          |
| `permissions` | `dict[str, QueueAccessGrantees]`       | Права пользователя, по ключам `GRANT`, `CREATE`, `READ`, `WRITE`, `DENY` |
| `components`  | `list[ComponentRef] \| None`           | Компоненты очереди, доступные пользователю          |

### QueueGroupAccess

Результат `get_queue_group_access`.

| Поле          | Тип                                   | Описание                                          |
|---------------|-----------------------------------------|-----------------------------------------------------|
| `group`       | `Ref`                                  | Группа, для которой выполнен запрос                 |
| `permissions` | `dict[str, QueueAccessGrantees]`       | Права группы, по тем же ключам, что и у `QueueUserAccess` |
| `components`  | `list[ComponentRef] \| None`           | Компоненты очереди, доступные группе                |

### ComponentUserAccess

Результат `get_component_user_access`.

| Поле          | Тип                                   | Описание                                          |
|---------------|-----------------------------------------|-----------------------------------------------------|
| `user`        | `User`                                 | Пользователь, для которого выполнен запрос          |
| `component`   | `Component`                            | Компонент, для которого выполнен запрос             |
| `permissions` | `dict[str, QueueAccessGrantees]`       | Права пользователя для компонента, по ключам `CREATE`, `READ`, `WRITE`, `DENY` |

### ComponentGroupAccess

Результат `get_component_group_access`.

| Поле          | Тип                                   | Описание                                          |
|---------------|-----------------------------------------|-----------------------------------------------------|
| `group`       | `Ref`                                  | Группа, для которой выполнен запрос                 |
| `component`   | `Component`                            | Компонент, для которого выполнен запрос             |
| `permissions` | `dict[str, QueueAccessGrantees]`       | Права группы для компонента, по тем же ключам, что и у `ComponentUserAccess` |

## Типичный сценарий

Выдать пользователю права на создание и редактирование задач, затем убедиться, что
запись действительно применилась:

```python
from yatracker.types.queue_permissions import QueueAccessChange, QueueAccessUpdate

permissions = await tracker.update_queue_access(
    "WRITERS",
    create={"users": ["login"]},
    write=QueueAccessUpdate(users=QueueAccessChange(add=["login"])),
)
print(permissions.version)

access = await tracker.get_queue_user_access("WRITERS", "login")
granted = {
    permission
    for permission, grantees in access.permissions.items()
    if any(u.id == "login" for u in grantees.users or [])
}
print(granted)  # {"CREATE", "WRITE"}
```
