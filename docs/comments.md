# Комментарии

Библиотека позволяет получать, создавать, редактировать и удалять комментарии к задачам.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с комментариями являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация по комментариям:
https://yandex.cloud/ru/docs/tracker/about-api

## Получение списка комментариев

Чтобы получить список комментариев задачи, воспользуйтесь методом `get_comments`:

```python
comments = await tracker.get_comments("WRITERS-1")
```

Метод поддерживает дополнительные параметры:

```python
comments = await tracker.get_comments(
    issue_id="WRITERS-1",
    expand="attachments",  # (1)
    per_page=50,  # (2)
    id_=100500,  # (3)
)
```

1. `expand` — какие дополнительные поля включить в ответ: `attachments`, `html` или `all`.
2. `per_page` — количество записей на странице.
3. `id_` — курсор пагинации: вернуть комментарии, идущие после комментария с данным id
   (соответствует query-параметру `id`).

## Добавление комментария

Чтобы прокомментировать задачу, воспользуйтесь методом `post_comment`:

```python
comment = await tracker.post_comment("WRITERS-1", "Отличная работа!")
```

Есть возможность добавить автора комментария в наблюдатели за задачей:

```python
comment = await tracker.post_comment(
    issue_id="WRITERS-1",
    text="Отличная работа!",
    is_add_to_followers=True,
)
```

!!! note "Дополнительные параметры"

    Метод `post_comment` принимает `**kwargs`, поэтому вы можете передать любые другие
    поля, поддерживаемые API Трекера при создании комментария (например, `attachmentIds`
    или `summonees` — упомянутые пользователи получат уведомление). Имена в `snake_case`
    будут автоматически преобразованы в `camelCase`, как принято в Трекере.

    ```python
    comment = await tracker.post_comment(
        issue_id="WRITERS-1",
        text="Взгляните на файл",
        attachment_ids=["1234"],
        summonees=["login1", "login2"],
    )
    ```

## Редактирование комментария

Для изменения текста существующего комментария используйте `edit_comment`:

```python
comment = await tracker.edit_comment(
    issue_id="WRITERS-1",
    comment_id=comment.id,
    text="Отличная работа, но опечатка в третьем абзаце",
)
```

Метод также принимает необязательные параметры:

```python
comment = await tracker.edit_comment(
    issue_id="WRITERS-1",
    comment_id=comment.id,
    text="Обновлённый текст",
    attachment_ids=["1234"],  # (1)
    summonees=["login1"],  # (2)
    markup_type="md",  # (3)
)
```

1. `attachment_ids` — список идентификаторов вложений, которые нужно связать с комментарием.
2. `summonees` — список логинов пользователей, которых нужно уведомить о комментарии.
3. `markup_type` — тип разметки комментария, например `"md"` для Markdown.

## Реакция на комментарий

Поставить реакцию на комментарий — так же, как в интерфейсе Трекера — можно методом
`add_comment_reaction`:

```python
comment = await tracker.add_comment_reaction("WRITERS-1", comment.id, "LIKE")
```

Сигнатура:

```python
async def add_comment_reaction(
    self,
    issue_id: str,
    comment_id: str | int,
    reaction: str,
) -> Comment: ...
```

1. `issue_id` — ID или ключ задачи.
2. `comment_id` — ID комментария: числовой `id` либо строковый `long_id`.
3. `reaction` — название реакции: `"LIKE"`, `"DISLIKE"`, `"LAUGH"`, `"HOORAY"`,
   `"CONFUSED"`, `"HEART"`, `"ROCKET"`, `"EYES"`, `"FIRE"`, `"OK"`, `"FACEPALM"` или
   `"CHECK"`. Список принадлежит серверу, поэтому в библиотеке не типизирован — обычная
   строка.

Метод возвращает `Comment` с обновлёнными `reactions_count` и `own_reactions` (см. таблицу
полей ниже) — заново загружать комментарий не нужно.

!!! note "Снять реакцию через API нельзя"

    Официальная документация описывает только запрос на добавление реакции — отдельного
    метода для её снятия нет. Отменить реакцию можно через интерфейс Трекера.

Источник: https://yandex.ru/support/tracker/ru/api/issues/add-reaction-to-comment

## Удаление комментария

```python
await tracker.delete_comment("WRITERS-1", comment.id)
```

Метод возвращает `True` при успешном удалении.

## Модель `Comment`

Каждый из методов выше (кроме `delete_comment`) возвращает объект `Comment` со следующими
полями:

| Поле               | Тип                      | Описание                                                          |
|--------------------|---------------------------|----------------------------------------------------------------------|
| `url`              | `str`                    | Ссылка на комментарий (в API — поле `self`)                       |
| `id`               | `int`                    | Идентификатор комментария                                         |
| `text`             | `str`                    | Текст комментария                                                  |
| `created_by`       | `User`                   | Автор комментария                                                  |
| `updated_by`       | `User \| None`           | Последний редактор комментария                                     |
| `created_at`       | `datetime`               | Дата и время создания                                              |
| `updated_at`       | `datetime \| None`       | Дата и время последнего изменения                                  |
| `version`          | `int`                    | Версия комментария                                                  |
| `long_id`          | `str \| None`            | ID комментария в строковом формате                                 |
| `reactions_count`  | `dict[str, int] \| None` | Количество реакций каждого вида; ключ — название реакции в нижнем регистре |
| `own_reactions`    | `list[str] \| None`      | Реакции текущего пользователя на комментарий, в нижнем регистре    |
| `type`             | `str \| None`            | Тип комментария: `standard` (через интерфейс), `incoming`/`outcoming` (из входящего/исходящего письма) |
| `transport`        | `str \| None`            | Способ добавления: `internal` (через интерфейс) или `email`        |

`long_id`, `reactions_count`, `own_reactions`, `type` и `transport` необязательны: они
заполняются не во всех ответах API, поэтому в модели помечены как `| None`.
