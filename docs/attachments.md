# Прикреплённые файлы

К задачам и комментариям в Трекере можно прикреплять файлы. `yatracker` предоставляет методы
для загрузки, получения списка, скачивания и удаления вложений.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с вложениями являются асинхронными.
    В примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

Официальная документация:
https://yandex.cloud/ru/docs/tracker/about-api

## Прикрепление файла к задаче

Чтобы прикрепить файл напрямую к уже существующей задаче, используйте `attach_file`:

```python
from pathlib import Path

with Path(FILE_PATH).open("rb") as file:
    attachment = await tracker.attach_file(
        issue_id="WRITERS-1",
        file=file,
        filename="draft.docx",  # (1)
    )
```

1. `filename` — необязательный параметр: задаёт имя, под которым файл сохранится в Трекере
   (передаётся и в multipart-форме, и как query-параметр). Если не указать, при передаче
   `BytesIO` и подобных объектов без собственного имени файл будет сохранён под именем
   `file`, поэтому для «безымянных» объектов параметр лучше указывать явно.

Сигнатура метода:

```python
async def attach_file(
    issue_id: str,
    file: BinaryIO,
    filename: str | None = None,
) -> Attachment: ...
```

`file` — открытый в бинарном режиме файловый объект (`BinaryIO`), например результат
`Path(...).open('rb')` или `open(..., 'rb')`.

## Загрузка временного файла

Если файл нужно прикрепить не к существующей задаче, а сразу при её создании (или при
создании комментария), сначала загрузите его как временный с помощью `upload_temp_file`:

```python
with Path(FILE_PATH).open("rb") as file:
    attachment = await tracker.upload_temp_file(file, "draft.docx")
```

Сигнатура:

```python
async def upload_temp_file(
    file: BinaryIO,
    filename: str | None = None,
) -> Attachment: ...
```

Полученный `attachment.id` затем можно передать в `attachment_ids` при создании задачи:

```python
issue = await tracker.create_issue(
    summary="New Issue",
    queue="WRITERS",
    attachment_ids=[attachment.id],
)
```

или при добавлении комментария (см. [«Комментарии»](comments.md)):

```python
comment = await tracker.post_comment(
    issue_id=issue.id,
    text="Файл во вложении",
    attachment_ids=[attachment.id],
)
```

## Получение списка вложений

```python
attachments = await tracker.get_attachments("WRITERS-1")
```

Метод возвращает список объектов `Attachment`, прикреплённых к задаче.

## Скачивание файла

```python
content: bytes = await tracker.download_attachment(
    issue_id="WRITERS-1",
    attachment_id=attachment.id,
    filename=attachment.name,
)
```

Метод возвращает содержимое файла в виде `bytes`. Обратите внимание, что помимо
идентификатора вложения (`attachment_id`) требуется его имя (`filename`) — так же, как
это устроено в самом API Трекера.

## Скачивание превью изображения

Для файлов-изображений Трекер умеет строить миниатюры (thumbnails):

```python
thumbnail: bytes = await tracker.download_thumbnail(
    issue_id="WRITERS-1",
    attachment_id=attachment.id,
)
```

## Удаление вложения

```python
await tracker.delete_attachment("WRITERS-1", attachment.id)
```

Метод возвращает `True` при успешном удалении.

## Модель `Attachment`

| Поле         | Тип                | Описание                                          |
|--------------|--------------------|-----------------------------------------------------|
| `url`        | `str`              | Ссылка на вложение (в API — поле `self`)            |
| `id`         | `str`              | Идентификатор вложения                              |
| `name`       | `str`              | Имя файла                                            |
| `content`    | `str`              | Ссылка на содержимое файла                           |
| `thumbnail`  | `str \| None`      | Ссылка на миниатюру (для изображений)                |
| `created_by` | `User`             | Пользователь, загрузивший файл                       |
| `created_at` | `datetime`         | Дата и время загрузки                                |
| `mimetype`   | `str`              | MIME-тип файла                                       |
| `size`       | `int`              | Размер файла в байтах                                |
| `metadata`   | `Metadata \| None` | Дополнительные метаданные (на данный момент — `size`)|
| `comment_id` | `str \| None`      | Идентификатор комментария, к которому привязан файл  |

## Полный пример

```python
import asyncio
from pathlib import Path

from yatracker import YaTracker

ORG_ID = ...
TOKEN = ...
FILE_PATH = ...
FILE_NAME = ...


async def main() -> None:
    tracker = YaTracker(ORG_ID, TOKEN)

    # загружаем временный файл
    with Path(FILE_PATH).open("rb") as file:
        attachment = await tracker.upload_temp_file(file, FILE_NAME)

    # создаём задачу сразу с вложением
    issue = await tracker.create_issue(
        summary="New Issue",
        queue="KEY",
        attachment_ids=[attachment.id],
    )

    # прикрепляем ещё один файл (или тот же) напрямую к задаче
    with Path(FILE_PATH).open("rb") as file:
        await tracker.attach_file(
            issue_id=issue.id,
            file=file,
            filename=FILE_NAME,
        )

    # получаем список вложений
    attachments = await tracker.get_attachments(issue.id)

    # и удаляем их все — запросы независимы, поэтому выполняем их конкурентно
    await asyncio.gather(
        *(tracker.delete_attachment(issue.id, att.id) for att in attachments),
    )

    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
```
