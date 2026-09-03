# Импорт

Трекер поддерживает импорт задач, комментариев, связей, записей о затраченном времени
и вложений из внешних систем с сохранением исходных авторов и дат — например, при
переезде истории задач из другого трекера. `yatracker` предоставляет для этого
отдельные методы: `import_issue`, `import_comment`, `import_link`, `import_worklog` и
`import_attachment`.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы импорта являются асинхронными. В примерах ниже
    вызовы показаны так, как будто мы уже находимся внутри корутины.

    Все запросы импорта может выполнять только **администратор организации** — иначе API
    вернёт `403 Forbidden`, и библиотека выбросит `SufficientRightsError`
    (см. [«Обработка ошибок»](errors.md)).

Официальная документация:

* [Импорт задачи](https://yandex.ru/support/tracker/ru/concepts/import/import-ticket)
* [Импорт комментариев](https://yandex.ru/support/tracker/ru/concepts/import/import-comments)
* [Импорт связей](https://yandex.ru/support/tracker/ru/concepts/import/import-links)
* [Импорт записей о затраченном времени](https://yandex.ru/support/tracker/ru/api/import/import-worklogs)
* [Импорт вложений](https://yandex.ru/support/tracker/ru/concepts/import/import-attachments)

## Даты и время

Все методы импорта принимают время создания (`created_at`) и, где применимо, время
изменения (`updated_at`) объекта. Значение можно передать как:

* timezone-aware `datetime` — библиотека сама отформатирует его в ISO 8601 с миллисекундами
  и смещением часового пояса (`2025-01-10T12:00:00.000+0000`);
* готовую строку в формате API Трекера (`YYYY-MM-DDThh:mm:ss.sss±hhmm`) — она
  передаётся как есть.

!!! warning "Наивный datetime"

    Если передать "наивный" `datetime` (без часового пояса), библиотека выдаст
    `UserWarning`, так как API Трекера может некорректно обработать такое значение.
    Используйте `datetime(..., tzinfo=timezone.utc)` или `zoneinfo`.

Ограничения, которые проверяет сам Трекер:

* `created_at` не может быть в будущем;
* для комментария, связи, записи о затраченном времени и вложения `created_at` должен
  попадать в промежуток между созданием и последним изменением задачи (а для вложения
  к комментарию — ещё и между созданием и изменением самого комментария).

Библиотека дополнительно проверяет согласованность параметров ещё до отправки запроса и
бросает `ValueError`, если условие нарушено:

* `updated_at` и `updated_by` должны быть переданы вместе — либо оба, либо ни одного;
* в `import_issue` то же самое верно для тройки `resolved_at`, `resolved_by`, `resolution`.

## Импорт задачи

```python
from datetime import datetime, timezone

issue = await tracker.import_issue(
    queue="WRITERS",
    summary="Перенесённая задача",
    created_at=datetime(2025, 1, 10, 12, 0, tzinfo=timezone.utc),
    created_by="login",
)
```

Сигнатура:

```python
async def import_issue(
    self,
    queue: str,
    summary: str,
    created_at: datetime | str,
    created_by: str | int,
    *,
    key: str | None = None,
    updated_at: datetime | str | None = None,
    updated_by: str | int | None = None,
    resolved_at: datetime | str | None = None,
    resolved_by: str | int | None = None,
    resolution: int | str | None = None,
    status: int | str | None = None,
    type_: int | str | None = None,
    priority: int | str | None = None,
    description: str | None = None,
    assignee: str | int | None = None,
    deadline: date | str | None = None,
    start: date | str | None = None,
    end: date | str | None = None,
    unique: str | None = None,
    _type: type[FullIssue] = FullIssue,
    **kwargs,
) -> FullIssue: ...
```

- `queue` — ключ очереди, в которую импортируется задача.
- `summary` — заголовок задачи.
- `created_at`, `created_by` — дата создания и автор (логин или числовой id) — обязательны.
- `key` — ключ задачи, например `"WRITERS-100"`. Если не указан, Трекер назначит его сам,
  по порядку.
- `updated_at`, `updated_by` — дата и автор последнего изменения (передавать только вместе).
- `resolved_at`, `resolved_by`, `resolution` — дата, автор и id резолюции закрытия задачи
  (передавать только все три вместе).
- `status` — id статуса; должен принадлежать workflow очереди.
- `type_` — id типа задачи.
- `priority` — id приоритета.
- `description`, `assignee`, `deadline`, `start`, `end` — стандартные поля задачи; даты
  `deadline`/`start`/`end` — `date` или строка `YYYY-MM-DD`.
- `unique` — ключ идемпотентности.
- `_type` — своя модель задачи вместо `FullIssue`, как в `create_issue`/`get_issue`
  (см. [пользовательские поля](custom_fields.md)).
- `**kwargs` — любые другие поля API: `affected_versions`, `fix_versions`, `components`,
  `tags`, `sprint`, `followers`, `access`, `following_maillists`, `original_estimation` /
  `estimation` / `spent` (в миллисекундах), `story_points`, `voted_by`, `favorited_by`, а
  также пользовательские (локальные) поля очереди. Имена в `snake_case` конвертируются в
  `camelCase` автоматически.

!!! warning "Импорт с явным ключом"

    Если указать `key` с номером, который больше текущего счётчика очереди (например,
    импортировать `WRITERS-100` в пустую очередь), номера `WRITERS-1`…`WRITERS-99` окажутся
    пропущены и больше не будут использованы — это особенность самого API Трекера.

Метод возвращает `FullIssue` — та же модель, что и `create_issue`/`get_issue`, её поля
описаны в [«Работа с задачами»](issues.md).

## Импорт комментария

```python
comment = await tracker.import_comment(
    issue_id=issue.key,
    text="Перенесённый комментарий",
    created_at=datetime(2025, 1, 11, 9, 30, tzinfo=timezone.utc),
    created_by="login",
)
```

Сигнатура:

```python
async def import_comment(
    self,
    issue_id: str,
    text: str,
    created_at: datetime | str,
    created_by: str | int,
    *,
    updated_at: datetime | str | None = None,
    updated_by: str | int | None = None,
    **kwargs,
) -> Comment: ...
```

- `issue_id` — ID или ключ задачи, в которую импортируется комментарий.
- `text`, `created_at`, `created_by` — текст, дата создания и автор комментария.
- `updated_at`, `updated_by` — дата и автор последнего изменения (передавать только вместе).
- `**kwargs` — прочие поля комментария, поддерживаемые API (например `summonees`), как и в
  `post_comment`.

Метод возвращает `Comment` — модель описана в [«Комментарии»](comments.md).

## Импорт связи

```python
from yatracker.types import LinkRelationship

link = await tracker.import_link(
    issue_id=issue.key,
    relationship=LinkRelationship.RELATES,
    issue="WRITERS-2",
    created_at=datetime(2025, 1, 12, 10, 0, tzinfo=timezone.utc),
    created_by="login",
)
```

Сигнатура:

```python
async def import_link(
    self,
    issue_id: str,
    relationship: str | LinkRelationship,
    issue: str,
    created_at: datetime | str,
    created_by: str | int,
    *,
    updated_at: datetime | str | None = None,
    updated_by: str | int | None = None,
) -> IssueLink: ...
```

- `issue_id` — ID или ключ задачи, от которой создаётся связь.
- `relationship` — тип связи: значение `LinkRelationship` либо обычная строка с тем же
  значением.
- `issue` — ID или ключ связываемой задачи.
- `created_at`, `created_by` — дата создания и автор связи.
- `updated_at`, `updated_by` — дата и автор последнего изменения (передавать только вместе).

`LinkRelationship` (`yatracker.types`) — перечисление (`str`-`Enum`) допустимых значений
связи:

| Значение | Описание |
|---|---|
| `RELATES` | `"relates"` — связана с |
| `IS_DEPENDENT_BY` | `"is dependent by"` — зависит от неё |
| `DEPENDS_ON` | `"depends on"` — зависит от |
| `IS_SUBTASK_FOR` | `"is subtask for"` — подзадача для |
| `IS_PARENT_TASK_FOR` | `"is parent task for"` — родительская для |
| `DUPLICATES` | `"duplicates"` — дублирует |
| `IS_DUPLICATED_BY` | `"is duplicated by"` — дублируется ею |
| `IS_EPIC_OF` | `"is epic of"` — эпик для |
| `HAS_EPIC` | `"has epic"` — относится к эпику |
| `CLONE` | `"clone"` — клон |
| `ORIGINAL` | `"original"` — оригинал |

Метод возвращает `IssueLink` — модель описана в разделе
«Связи между задачами» страницы [«Работа с задачами»](issues.md).

## Импорт записи о затраченном времени

```python
worklog = await tracker.import_worklog(
    issue_id=issue.key,
    duration="PT1H",
    created_at=datetime(2025, 2, 18, 16, 35, tzinfo=timezone.utc),
    created_by="login",
    start=datetime(2025, 2, 18, 16, 35, tzinfo=timezone.utc),
    comment="Перенесённая запись",
)
```

Сигнатура:

```python
async def import_worklog(
    self,
    issue_id: str,
    duration: str,
    created_at: datetime | str,
    created_by: str | int,
    start: datetime | str,
    *,
    comment: str | None = None,
    **kwargs,
) -> Worklog: ...
```

- `issue_id` — ID или ключ задачи, в которую импортируется запись о затраченном
  времени.
- `duration` — затраченное время в формате ISO 8601 (`PnYnMnDTnHnMnS`, `PnW`), например
  `"PT1H"` (час), `"P6W"` (6 недель) или `"P0Y0M30DT2H10M25S"` (30 дней, 2 часа, 10
  минут, 25 секунд).
- `created_at`, `created_by` — дата создания и автор записи. `created_at` должен
  попадать в промежуток между созданием и последним изменением задачи.
- `start` — дата и время начала работы над задачей, датой создания записи не
  ограничено.
- `comment` — необязательный текст комментария к записи; отображается в Отчёте по
  трудозатратам.
- `**kwargs` — прочие поля записи, поддерживаемые API.

Метод возвращает `Worklog` — модель описана в [«Учёт времени»](worklogs.md).

## Импорт вложения

```python
from pathlib import Path

with Path(FILE_PATH).open("rb") as file:
    attachment = await tracker.import_attachment(
        issue_id=issue.key,
        file=file,
        filename="draft.docx",
        created_at=datetime(2025, 1, 13, 8, 0, tzinfo=timezone.utc),
        created_by="login",
    )
```

Сигнатура:

```python
async def import_attachment(
    self,
    issue_id: str,
    file: BinaryIO,
    filename: str,
    created_at: datetime | str,
    created_by: str | int,
    *,
    comment_id: str | int | None = None,
) -> Attachment: ...
```

- `issue_id` — ID или ключ задачи, к которой прикрепляется файл.
- `file` — открытый в бинарном режиме файловый объект (`BinaryIO`).
- `filename` — имя файла. В отличие от `attach_file`, здесь оно **обязательно**.
- `created_at`, `created_by` — дата загрузки и автор вложения.
- `comment_id` — если указан, файл импортируется как вложение к комментарию, а не к самой
  задаче (тогда `created_at` должен попадать в промежуток между созданием и изменением
  этого комментария).

Файл передаётся в теле запроса multipart-полем `file_data`. Максимальный размер файла —
1024 Мбит (значение из официальной документации Трекера).

Метод возвращает `Attachment` — модель описана в [«Прикреплённые файлы»](attachments.md).

## Полный пример

```python
import asyncio
from datetime import datetime, timezone
from pathlib import Path

from yatracker import YaTracker
from yatracker.types import LinkRelationship

ORG_ID = ...
TOKEN = ...
FILE_PATH = ...

AUTHOR = "external_login"


async def main() -> None:
    tracker = YaTracker(ORG_ID, TOKEN)

    # импортируем задачу с заранее известным ключом
    issue = await tracker.import_issue(
        queue="WRITERS",
        key="WRITERS-500",
        summary="Перенос истории из внешней системы",
        description="Импортировано автоматически",
        created_at=datetime(2025, 1, 10, 12, 0, tzinfo=timezone.utc),
        created_by=AUTHOR,
    )

    # импортируем комментарий к ней
    await tracker.import_comment(
        issue_id=issue.key,
        text="Комментарий из старого трекера",
        created_at=datetime(2025, 1, 11, 9, 30, tzinfo=timezone.utc),
        created_by=AUTHOR,
    )

    # импортируем связь с другой задачей
    await tracker.import_link(
        issue_id=issue.key,
        relationship=LinkRelationship.RELATES,
        issue="WRITERS-1",
        created_at=datetime(2025, 1, 12, 10, 0, tzinfo=timezone.utc),
        created_by=AUTHOR,
    )

    # импортируем запись о затраченном времени
    await tracker.import_worklog(
        issue_id=issue.key,
        duration="PT1H",
        created_at=datetime(2025, 1, 12, 11, 0, tzinfo=timezone.utc),
        created_by=AUTHOR,
        start=datetime(2025, 1, 12, 10, 0, tzinfo=timezone.utc),
        comment="Запись из старого трекера",
    )

    # импортируем вложение
    with Path(FILE_PATH).open("rb") as file:
        await tracker.import_attachment(
            issue_id=issue.key,
            file=file,
            filename="draft.docx",
            created_at=datetime(2025, 1, 13, 8, 0, tzinfo=timezone.utc),
            created_by=AUTHOR,
        )

    await tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
```
