# Доступ к сущностям

У проекта, портфеля или цели есть три типа доступа: `READ` (просмотр), `WRITE` (изменение) и
`GRANT` (управление правами доступа). Каждый из них может быть выдан отдельным пользователям,
группам или ролям сущности (`AUTHOR`, `OWNER`, `CLIENT`, `FOLLOWER`, `MEMBER`). `yatracker`
предоставляет методы для чтения текущих настроек доступа и для выдачи/отзыва прав.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с доступом к сущностям являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

!!! note "`extendedPermissions` вместо `permissions`"

    У API есть два семейства запросов: `/extendedPermissions` и более простой `/permissions`.
    Второй отличается только тем, что не отдаёт и не принимает `permissionSources` — сущность,
    от которой наследуются права доступа; в остальном оба совпадают с форматом объекта `acl`.
    `yatracker` оборачивает только `/extendedPermissions` — этого достаточно для обоих
    сценариев, а `permission_sources` можно просто не передавать.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/entities/get-access

## Получение настроек доступа

### get_entity_access

```python
async def get_entity_access(
    self,
    entity_type: EntityType,
    entity_id: str | int,
) -> EntityPermissions: ...
```

Возвращает настройки доступа сущности: кто и как может её видеть, изменять и управлять
доступом к ней, а также сущность, от которой унаследованы эти настройки (если она есть).

```python
access = await tracker.get_entity_access("project", "655f8cc523db2132")

print([user.display for user in access.acl.read.users] if access.acl.read else [])
print([group.display for group in access.acl.write.groups] if access.acl.write else [])
print(access.acl.grant.roles if access.acl.grant else [])
print([source.display for source in access.permission_sources])
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или `short_id` сущности.

!!! note "Пустой `acl`, пока доступ наследуется"

    Пока сущность наследует настройки доступа от родителя (`permission_sources` не пуст), сам
    `acl` пуст: реальные права смотрите у сущности из `permission_sources`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/get-access

## Изменение настроек доступа

### update_entity_access

```python
async def update_entity_access(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    grant: EntityAccessChange | dict[str, Any] | None = None,
    revoke: EntityAccessChange | dict[str, Any] | None = None,
    permission_sources: str | Sequence[str] | None = None,
) -> EntityPermissions: ...
```

Выдаёт или отзывает доступ к сущности, либо включает/отключает наследование прав от
родительской сущности. Метод бросает `ValueError`, если не передано ни `grant`, ни `revoke`,
ни `permission_sources`.

Включить наследование от родительского портфеля (или родительской цели):

```python
access = await tracker.update_entity_access(
    "project",
    "655f8cc523db2132",
    permission_sources="67ffd7e300000000",
)
```

Отключить наследование и сразу выдать права на изменение группе:

```python
from yatracker.types import EntityAccessChange, EntityAccessRule

access = await tracker.update_entity_access(
    "project",
    "655f8cc523db2132",
    permission_sources=[],
    grant=EntityAccessChange(write=EntityAccessRule(groups=2)),
)
```

Выдать доступ на просмотр пользователю (наследование должно быть уже отключено) — через
обычный словарь вместо `EntityAccessChange`/`EntityAccessRule`:

```python
access = await tracker.update_entity_access(
    "project",
    "655f8cc523db2132",
    grant={"READ": {"users": {"login": "username1"}}},
)
```

Отозвать право управления доступом у пользователя:

```python
access = await tracker.update_entity_access(
    "project",
    "655f8cc523db2132",
    revoke={"GRANT": {"users": "username2"}},
)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `grant` — типы доступа, которые нужно выдать: `EntityAccessChange` или эквивалентный
   словарь с ключами `"READ"`/`"WRITE"`/`"GRANT"`, например `{"READ": {"users": ["username"]}}`.
   Пользователь адресуется логином, числовым идентификатором или объектом
   (`{"uid": 123}`, `{"login": "username"}`), группа — числовым идентификатором, роль — именем
   роли; каждое из полей `users`/`groups`/`roles` принимает как одно значение, так и список.
4. `revoke` — типы доступа, которые нужно отозвать, в том же формате, что и `grant`.
5. `permission_sources` — идентификатор сущности, от которой нужно наследовать настройки
   доступа: основной портфель — для проекта или портфеля, родительская цель — для цели.
   Пустая последовательность (`[]`) отключает наследование.

!!! warning "Пока доступ наследуется, `grant`/`revoke` не действуют"

    Пока `permission_sources` не пуст, `grant` и `revoke` не имеют эффекта, а поле сущности
    `teamAccess` игнорируется. Чтобы менять права вручную, сначала передайте
    `permission_sources=[]` — в этом же вызове или заранее.

Источник: https://yandex.ru/support/tracker/ru/api/entities/patch-access

## Модели

### EntityPermissions

Настройки доступа сущности — то, что возвращают оба метода этой страницы.

| Поле                 | Тип                     | Описание                                                                 |
|----------------------|--------------------------|-----------------------------------------------------------------------------|
| `acl`                | `EntityAcl`              | Пользователи, группы и роли, которые держат каждый тип доступа. Пуст, пока `permission_sources` не пуст |
| `permission_sources` | `list[EntityRef]`        | Сущность, от которой унаследованы настройки доступа (основной портфель или родительская цель) |
| `parent_entities`    | `EntityParent \| None`   | Родительские сущности: основная и, для проектов и портфелей, дополнительные портфели |

### EntityAcl

Типы доступа сущности и то, кто ими обладает — поле `acl` объекта `EntityPermissions`.

| Поле    | Тип                         | Описание                                    |
|---------|------------------------------|------------------------------------------------|
| `read`  | `EntityAccessGrantees \| None` | Кто может просматривать сущность (`READ`)    |
| `write` | `EntityAccessGrantees \| None` | Кто может изменять сущность (`WRITE`)        |
| `grant` | `EntityAccessGrantees \| None` | Кто может менять настройки доступа (`GRANT`) |

### EntityAccessGrantees

Пользователи, группы и роли, обладающие одним типом доступа.

| Поле     | Тип           | Описание                                                        |
|----------|---------------|----------------------------------------------------------------------|
| `users`  | `list[User]`  | Пользователи, у которых есть этот тип доступа лично                  |
| `groups` | `list[Ref]`   | Группы, у которых есть этот тип доступа                              |
| `roles`  | `list[str]`   | Роли сущности с этим типом доступа: `AUTHOR`, `OWNER`, `CLIENT`, `FOLLOWER`, `MEMBER` |

### EntityAccessRule

Пользователи, группы и роли, которым нужно выдать (или у которых нужно отозвать) один тип
доступа — значение ключа `READ`/`WRITE`/`GRANT` объекта `grant` или `revoke` метода
`update_entity_access`. Каждое поле принимает как одно значение, так и список; поля,
оставленные `None`, в запрос не попадают.

| Поле     | Тип                                          | Описание                                    |
|----------|-----------------------------------------------|--------------------------------------------------|
| `users`  | `list[login \| id \| dict] \| login \| id \| dict \| None` | Логины или идентификаторы пользователей     |
| `groups` | `list[int \| str] \| int \| str \| None`      | Идентификаторы групп                              |
| `roles`  | `list[str] \| str \| None`                    | Роли: `AUTHOR`, `OWNER`, `CLIENT`, `FOLLOWER`, `MEMBER` |

### EntityAccessChange

Типы доступа, которые нужно выдать (или отозвать) — значение параметра `grant`/`revoke`
метода `update_entity_access`. Типы доступа, оставленные `None`, в запрос не попадают.

| Поле    | Тип                          | Описание                                                |
|---------|-------------------------------|--------------------------------------------------------------|
| `read`  | `EntityAccessRule \| None`    | Кому выдать/у кого отозвать доступ на просмотр (`READ`)      |
| `write` | `EntityAccessRule \| None`    | Кому выдать/у кого отозвать доступ на изменение (`WRITE`)    |
| `grant` | `EntityAccessRule \| None`    | Кому выдать/у кого отозвать право управления доступом (`GRANT`) |

!!! tip "`permission_sources`"

    Показано в отдельном разделе выше — это не часть `acl`/`EntityAccessChange`, а
    самостоятельный параметр `update_entity_access`.
