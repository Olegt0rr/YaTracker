# Комментарии к проектам, портфелям и целям

Сущности (`project`, `portfolio`, `goal` — см. [«Проекты, портфели и цели»](entities.md)) можно
комментировать так же, как задачи, но через отдельный набор методов и отдельную модель:
комментарий сущности несёт строковый идентификатор `long_id`, HTML-разметку текста, вложения и
реакции прямо в объекте, поэтому он не совпадает с моделью `Comment`, которую возвращают методы
задач (см. [«Комментарии»](comments.md)).

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с комментариями сущностей являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

**Тип сущности идёт первым аргументом**, как и в остальных методах `/entities` — `"project"`,
`"portfolio"` или `"goal"`. Во время выполнения значение не проверяется и подставляется в адрес
запроса как есть.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments

## Получение комментариев

### get_entity_comments

```python
async def get_entity_comments(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    expand: str | None = None,
) -> list[EntityComment]: ...
```

Возвращает список всех комментариев сущности, без пагинации.

```python
from yatracker.types.entity_comment import EntityComment

comments: list[EntityComment] = await tracker.get_entity_comments(
    "project",
    "655f3be523db2132",
    expand="all",
)

for comment in comments:
    print(comment.id, comment.text)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или короткий идентификатор (`short_id`) сущности.
3. `expand` — дополнительная информация в ответе: `"all"` — всё сразу; `"html"` — HTML-разметка
   текста (`EntityComment.text_html`); `"attachments"` — вложения комментария
   (`EntityComment.attachments`); `"reactions"` — реакции пользователей
   (`EntityComment.users_reacted` и `own_reactions`). Без `"reactions"` (и без `"all"`) Трекер
   присылает вместо этого только количество реакций (`EntityComment.reactions_count`).

Источник: https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments

### get_entity_comments_relative

```python
async def get_entity_comments_relative(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    *,
    per_page: int | None = None,
    from_: str | int | None = None,
    selected: str | int | None = None,
    new_comments_on_top: bool | None = None,
    direction: str | None = None,
) -> EntityCommentsPage: ...
```

Возвращает одну страницу комментариев сущности — относительную, как у истории событий сущности
(`get_entity_events`) и у постраничного списка комментариев задачи.

```python
page = await tracker.get_entity_comments_relative(
    "project",
    "655f3be523db2132",
    per_page=3,
)

for comment in page.comments:
    print(comment.id, comment.text)

if page.has_next:
    page = await tracker.get_entity_comments_relative(
        "project",
        "655f3be523db2132",
        per_page=3,
        from_=page.comments[-1].id,
    )
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `per_page` — количество комментариев на странице (по умолчанию 50).
4. `from_` — идентификатор комментария, после которого начинается список (сам он в список не
   включается). Взаимоисключим с `selected`.
5. `selected` — идентификатор комментария, вокруг которого формируется список: сам комментарий,
   предшествующий ему, следующий за ним и так далее. Взаимоисключим с `from_`.
6. `new_comments_on_top` — сортировать ли новые комментарии первыми (по умолчанию `False`).
7. `direction` — `"forward"` (по умолчанию) или `"backward"`, что инвертирует
   `new_comments_on_top`.

!!! warning "`from_` и `selected` взаимоисключимы"

    Если передать оба параметра сразу, метод бросит `ValueError`, не отправляя запрос — так же,
    как это устроено у пагинации истории событий сущности и у пагинации досок.

Источник: https://yandex.ru/support/tracker/ru/api/entities/comments/get-all-comments

## Получение одного комментария

### get_entity_comment

```python
async def get_entity_comment(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    comment_id: str | int,
    *,
    expand: str | None = None,
) -> EntityComment: ...
```

Возвращает один комментарий сущности по его идентификатору.

```python
comment = await tracker.get_entity_comment(
    "project",
    "655f3be523db2132",
    comment_id=15,
    expand="all",
)

print(comment.text_html)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id` сущности.
3. `comment_id` — идентификатор комментария.
4. `expand` — как в `get_entity_comments`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/comments/get-comment

## Добавление комментария

### post_entity_comment

```python
async def post_entity_comment(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    text: str,
    *,
    attachment_ids: list[str | int] | None = None,
    summonees: list[str | int] | None = None,
    maillist_summonees: list[str] | None = None,
    is_add_to_followers: bool | None = None,
    notify: bool | None = None,
    notify_author: bool | None = None,
    expand: str | None = None,
    **kwargs: Any,
) -> EntityComment: ...
```

Добавляет комментарий к сущности.

```python
comment = await tracker.post_entity_comment(
    "project",
    "655f3be523db2132",
    "Отличная работа!",
    summonees=["agent007"],
)
```

Чтобы приложить к комментарию файл, сначала загрузите его как временный (см.
[«Прикреплённые файлы»](attachments.md)) и передайте `id` полученного вложения в
`attachment_ids`:

```python
attachment = await tracker.upload_temp_file(file, "draft.docx")

comment = await tracker.post_entity_comment(
    "project",
    "655f3be523db2132",
    "Файл во вложении",
    attachment_ids=[attachment.id],
)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `text` — текст комментария (обязательное поле).
4. `attachment_ids` — идентификаторы временных файлов, которые будут прикреплены как вложения
   (загрузите их заранее через `upload_temp_file`).
5. `summonees` — идентификаторы или логины призванных пользователей.
6. `maillist_summonees` — список рассылок, призванных в комментарии.
7. `is_add_to_followers` — добавить ли автора комментария в наблюдатели сущности (по умолчанию
   `True`).
8. `notify` — уведомлять ли пользователей, указанных в полях сущности (по умолчанию `True`).
9. `notify_author` — уведомлять ли автора изменения (по умолчанию `False`).
10. `expand` — как в `get_entity_comments`.
11. `**kwargs` — дополнительные поля тела запроса, которые приводятся к `camelCase` и
    отправляются как есть.

Источник: https://yandex.ru/support/tracker/ru/api/entities/comments/add-comment

## Изменение комментария

### edit_entity_comment

```python
async def edit_entity_comment(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    comment_id: str | int,
    *,
    text: str | None = None,
    attachment_ids: list[str | int] | None = None,
    summonees: list[str | int] | None = None,
    maillist_summonees: list[str] | None = None,
    is_add_to_followers: bool | None = None,
    notify: bool | None = None,
    notify_author: bool | None = None,
    expand: str | None = None,
    **kwargs: Any,
) -> EntityComment: ...
```

Изменяет существующий комментарий сущности. Все поля тела запроса необязательны, но хотя бы
одно из них (или именованный аргумент из `**kwargs`) обязательно нужно передать — иначе запрос
ничего бы не поменял.

```python
comment = await tracker.edit_entity_comment(
    "project",
    "655f3be523db2132",
    comment_id=31,
    text="Исправленный текст комментария",
    summonees=["agent007", "agent008"],
)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `comment_id` — идентификатор комментария.
4. `text`, `attachment_ids`, `summonees`, `maillist_summonees` — новые значения полей, как в
   `post_entity_comment`.
5. `is_add_to_followers`, `notify`, `notify_author`, `expand` — параметры запроса, как в
   `post_entity_comment`.
6. `**kwargs` — дополнительные поля тела запроса.

!!! warning "Пустое изменение — `ValueError`"

    Если не передать ни одного поля тела запроса (`text`, `attachment_ids`, `summonees`,
    `maillist_summonees` и `**kwargs` — все `None` или отсутствуют), метод бросит `ValueError` и
    не станет отправлять пустой `PATCH`.

Источник: https://yandex.ru/support/tracker/ru/api/entities/comments/patch-comment

## Удаление комментария

### delete_entity_comment

```python
async def delete_entity_comment(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    comment_id: str | int,
    *,
    notify: bool | None = None,
    notify_author: bool | None = None,
) -> bool: ...
```

Удаляет комментарий сущности. Возвращает `True` при успехе.

```python
await tracker.delete_entity_comment("project", "655f3be523db2132", comment_id=16)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `comment_id` — идентификатор комментария.
4. `notify` — уведомлять ли пользователей, указанных в полях сущности (по умолчанию `True`).
5. `notify_author` — уведомлять ли автора изменения (по умолчанию `False`).

Источник: https://yandex.ru/support/tracker/ru/api/entities/comments/delete-comment

## Модель `EntityComment`

| Поле                  | Тип                            | Описание                                                                                    |
|-----------------------|---------------------------------|----------------------------------------------------------------------------------------------|
| `url`                 | `str`                            | Ссылка на комментарий (в API — поле `self`)                                                 |
| `id`                  | `int`                             | Идентификатор комментария                                                                    |
| `long_id`             | `str \| None`                     | Идентификатор комментария в виде строки                                                      |
| `text`                | `str`                             | Текст комментария                                                                             |
| `text_html`           | `str \| None`                     | HTML-разметка комментария (нужен `expand="html"` или `"all"`)                                |
| `attachments`         | `list[Ref] \| None`               | Вложения комментария (нужен `expand="attachments"` или `"all"`)                              |
| `created_by`          | `User`                            | Автор комментария                                                                             |
| `updated_by`          | `User \| None`                    | Последний редактор комментария                                                               |
| `created_at`          | `datetime`                        | Дата и время создания                                                                        |
| `updated_at`          | `datetime \| None`                | Дата и время последнего изменения                                                            |
| `users_reacted`       | `dict[str, list[User]] \| None`   | Реакции пользователей (нужен `expand="reactions"` или `"all"`), например `{"like": [...]}`  |
| `reactions_count`     | `dict[str, int] \| None`          | Количество реакций (когда `expand` не запрашивал `"reactions"`/`"all"`)                      |
| `own_reactions`       | `list[str] \| None`               | Реакции автора запроса                                                                        |
| `summonees`           | `list[User \| str] \| None`       | Призванные пользователи (объекты или логины/идентификаторы)                                  |
| `maillist_summonees`  | `list[Ref \| str] \| None`        | Призванные рассылки                                                                           |
| `version`             | `int`                              | Версия комментария                                                                            |
| `type`                | `str \| None`                     | `"standard"` (из интерфейса Трекера), `"incoming"` или `"outcoming"` (из письма)             |
| `transport`           | `str \| None`                     | `"internal"` (интерфейс Трекера) или `"email"`                                               |

Названия реакций (`users_reacted`, `own_reactions`) — серверный список: `like`, `dislike`,
`laugh`, `tada`, `hooray`, `confused`, `heart`, `rocket`, `eyes`, `fire`, `ok`, `facepalm`,
`check`.

## Модель `EntityCommentsPage`

Возвращается методом `get_entity_comments_relative`.

| Поле       | Тип                     | Описание                                     |
|------------|--------------------------|-----------------------------------------------|
| `comments` | `list[EntityComment]`    | Комментарии страницы                          |
| `has_next` | `bool`                    | Есть ли следующая страница                    |
| `has_prev` | `bool`                    | Есть ли предыдущая страница                   |

## Типичный сценарий

Получить первую страницу комментариев проекта, дописать к последнему из них ответ и убедиться,
что версия увеличилась:

```python
page = await tracker.get_entity_comments_relative(
    "project", "655f3be523db2132", per_page=5
)
last_comment = page.comments[-1]

updated = await tracker.edit_entity_comment(
    "project",
    "655f3be523db2132",
    comment_id=last_comment.id,
    text=f"{last_comment.text}\n\nUPD: сроки сдвинулись.",
)

print(updated.version > last_comment.version)
```
