# Вложения проектов, портфелей и целей

К сущностям (`project`, `portfolio`, `goal` — см. [«Проекты, портфели и цели»](entities.md))
можно прикреплять файлы так же, как к задачам, но через отдельный набор методов `/entities`.
Сама модель файла та же, что и у вложений задачи — `Attachment` (см.
[«Прикреплённые файлы»](attachments.md) — там же описаны все её поля).

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с вложениями сущностей являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

**Тип сущности идёт первым аргументом**, как и в остальных методах `/entities` — `"project"`,
`"portfolio"` или `"goal"`. Во время выполнения значение не проверяется и подставляется в адрес
запроса как есть.

Официальная документация:
https://yandex.ru/support/tracker/ru/api/entities/attachments/get-all-attachments

## Получение вложений

### get_entity_attachments

```python
async def get_entity_attachments(
    self,
    entity_type: EntityType,
    entity_id: str | int,
) -> list[Attachment]: ...
```

Возвращает список файлов, прикреплённых к сущности.

```python
attachments = await tracker.get_entity_attachments("project", "655f3be523db2132")

for attachment in attachments:
    print(attachment.id, attachment.name, attachment.size)
```

1. `entity_type` — `"project"`, `"portfolio"` или `"goal"`.
2. `entity_id` — идентификатор или короткий идентификатор (`short_id`) сущности.

Источник: https://yandex.ru/support/tracker/ru/api/entities/attachments/get-all-attachments

### get_entity_attachment

```python
async def get_entity_attachment(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    attachment_id: str | int,
) -> Attachment: ...
```

Возвращает метаданные одного прикреплённого файла — не его содержимое: чтобы скачать сам файл,
используйте ссылку из `Attachment.content` (как и для вложений задач, у сущностей отдельного
метода скачивания нет).

```python
attachment = await tracker.get_entity_attachment(
    "project",
    "655f3be523db2132",
    attachment_id=5,
)

print(attachment.mimetype, attachment.content)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `attachment_id` — идентификатор файла.

Источник: https://yandex.ru/support/tracker/ru/api/entities/attachments/get-attachment

## Прикрепление файла

### attach_file_to_entity

```python
async def attach_file_to_entity(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    file_id: str | int,
    *,
    notify: bool | None = None,
    notify_author: bool | None = None,
    fields: str | Sequence[str] | None = None,
    expand: str | None = None,
) -> Entity: ...
```

Прикрепляет к сущности уже загруженный временный файл.

!!! warning "Файл нужно загрузить заранее"

    В отличие от `attach_file` у задач, этот метод ничего не загружает сам: сначала отправьте
    файл в Трекер методом `upload_temp_file()` (см. [«Прикреплённые файлы»](attachments.md)) и
    передайте `id` полученного вложения как `file_id`. Метод возвращает не вложение, а
    обновлённый объект `Entity` — сущность, к которой файл был прикреплён.

```python
from yatracker.types import Entity

attachment = await tracker.upload_temp_file(file, "newimage.jpg")

project: Entity = await tracker.attach_file_to_entity(
    "project",
    "655f3be523db2132",
    file_id=attachment.id,
    expand="attachments",
)

for attached in project.attachments or []:
    print(attached.name)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор сущности.
3. `file_id` — идентификатор временного файла (результат `upload_temp_file`).
4. `notify` — уведомлять ли пользователей, указанных в полях сущности (по умолчанию `True`).
5. `notify_author` — уведомлять ли автора изменения (по умолчанию `False`).
6. `fields` — дополнительные поля сущности, которые нужно вернуть в ответе (строка или
   последовательность имён — будет склеена через запятую).
7. `expand` — `"all"` или `"attachments"`, чтобы получить в ответе список вложений
   (`Entity.attachments`) — как в примере выше.

Источник: https://yandex.ru/support/tracker/ru/api/entities/attachments/add-attachment

## Удаление вложения

### delete_entity_attachment

```python
async def delete_entity_attachment(
    self,
    entity_type: EntityType,
    entity_id: str | int,
    attachment_id: str | int,
) -> bool: ...
```

Удаляет файл, прикреплённый к сущности. Возвращает `True` при успехе.

```python
await tracker.delete_entity_attachment("project", "655f3be523db2132", attachment_id=123)
```

1. `entity_type` — тип сущности.
2. `entity_id` — идентификатор или `short_id`.
3. `attachment_id` — идентификатор файла.

Источник: https://yandex.ru/support/tracker/ru/api/entities/attachments/delete-attachment

## Модель `Attachment`

Методы этого раздела возвращают ту же модель `Attachment`, что и вложения задач — со всеми
полями (`url`, `id`, `name`, `content`, `thumbnail`, `created_by`, `created_at`, `mimetype`,
`size`, `metadata`, `comment_id`), см. таблицу в [«Прикреплённые файлы»](attachments.md).
`attach_file_to_entity` — единственное исключение: он возвращает не `Attachment`, а `Entity`
(см. [«Проекты, портфели и цели»](entities.md)), внутри которой список вложений лежит в
`Entity.attachments`.

## Типичный сценарий

Загрузить файл как временный, прикрепить его к проекту и сразу получить список вложений в
ответе, а затем удалить один из них:

```python
with Path(FILE_PATH).open("rb") as file:
    temp_file = await tracker.upload_temp_file(file, "report.pdf")

project = await tracker.attach_file_to_entity(
    "project",
    "655f3be523db2132",
    file_id=temp_file.id,
    expand="attachments",
)

attachments = project.attachments or await tracker.get_entity_attachments(
    "project",
    "655f3be523db2132",
)

for attachment in attachments:
    if attachment.name == "report.pdf":
        await tracker.delete_entity_attachment(
            "project",
            "655f3be523db2132",
            attachment_id=attachment.id,
        )
```
