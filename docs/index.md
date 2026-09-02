# О библиотеке

`YaTracker` представляет собой асинхронный клиент на `python`
для удобной работы с API Яндекс Трекера.

```python
from yatracker import YaTracker

tracker = YaTracker(org_id=..., token=...)

issue = await tracker.create_issue("Написать шедевр", "WRITERS")
print(issue.key, issue.status)
```

## Предостережение

Данная библиотека работает **только** с асинхронными приложениями,
и требует наличия базовых навыков работы с python.

## Что умеет библиотека

Клиент `YaTracker` собирается из нескольких категорий методов — все они доступны
напрямую на одном объекте, разделения на под-клиенты нет.

| Категория | Методы | Раздел |
|---|---|---|
| Задачи | `get_issue`, `create_issue`, `edit_issue`, `move_issue`, `find_issues`, `iter_issues`, `count_issues`, `get_issue_links`, `get_transitions`, `execute_transition` | [Задачи](issues.md) |
| Очереди | `get_queue`, `get_queues`, `create_queue`, `delete_queue`, `restore_queue`, `delete_tag_from_queue`, `get_queue_fields`, `get_queue_versions` | [Очереди](queues.md) |
| Компоненты | `get_components`, `get_queue_components`, `create_component`, `update_component` | [Компоненты](components.md) |
| Комментарии | `get_comments`, `post_comment`, `edit_comment`, `delete_comment` | [Комментарии](comments.md) |
| Чек-листы | `get_checklist`, `add_checklist_item`, `edit_checklist_item`, `delete_checklist_item`, `delete_checklist` | [Чек-листы](checklists.md) |
| Учёт времени | `post_worklog`, `edit_worklog`, `delete_worklog`, `get_issue_worklog`, `get_worklog` | [Учёт времени](worklogs.md) |
| Вложения | `get_attachments`, `attach_file`, `upload_temp_file`, `download_attachment`, `download_thumbnail`, `delete_attachment` | [Вложения](attachments.md) |
| Массовые операции | `bulk_update_issues`, `bulk_transition_issues`, `bulk_move_issues`, `get_bulk_change`, `get_bulk_change_issues`, `wait_bulk_change` | [Массовые операции](bulk_changes.md) |
| Импорт | `import_issue`, `import_comment`, `import_link`, `import_attachment` | [Импорт](import.md) |
| Приоритеты | `get_priorities` | — |

!!! note "Покрытие API"

    Библиотека покрывает не весь API Трекера. Разделы, которых нет в таблице выше
    (макросы, доски, проекты и т.д.),
    пока не реализованы. Если вам нужен отсутствующий метод — вы всегда можете
    выполнить запрос напрямую через `tracker._client.request(...)`
    или прислать pull request.

Часть методов продублирована прямо на моделях, чтобы не таскать `issue_id` руками:

```python
issue = await tracker.get_issue("WRITERS-42")

comments = await issue.get_comments()
await issue.post_comment("Готово")

links = await issue.get_links()
transitions = await issue.get_transitions()
```

## Технические особенности

### asyncio

Все методы, обращающиеся к API, — корутины, и вызываются с `await`.
Библиотека не содержит блокирующих вызовов и не создаёт собственных потоков,
поэтому легко встраивается в любое приложение на `asyncio`
(веб-сервис, бот, фоновый воркер).

### aiohttp

Запрос в API реализуются на основе клиентской части `aiohttp`, но если вы хотите использовать
`httpx` или другой асинхронный http-клиент – можете встроить в данную библиотеку свой модуль.

Для этого достаточно унаследоваться от `yatracker.tracker.client.BaseClient`,
реализовать `_make_request()` и `close()`, и передать готовый экземпляр в конструктор:

```python
from yatracker import YaTracker

tracker = YaTracker(client=MyHttpxClient(...))
```

Сессия создаётся лениво — при первом запросе, и переиспользуется до вызова
`close()`.

### pydantic

В качестве основы для моделирования объектов API используется библиотека `pydantic` (v2),
ядро которой написано на `rust` – она обеспечивает быструю валидацию и сериализацию моделей,
а также прекрасно знакома большинству python-разработчиков.

Ответы Трекера сразу превращаются в модели: `FullIssue`, `FullQueue`, `Comment`,
`Worklog`, `Attachment`, `Transition` и другие. Даты приходят готовыми
объектами `datetime.datetime`, а не строками.

### Полная типизация

Весь публичный код аннотирован и проверяется `mypy` и `ruff` в CI.
Перегрузки (`@overload`) расставлены так, что при передаче собственной модели
через `_type` вы получаете корректный тип результата:

```python
issue = await tracker.get_issue("HELP-1", _type=HelpIssue)
reveal_type(issue)  # HelpIssue
```

Подробнее — в разделе [Работа с пользовательскими полями](custom_fields.md).

### Именование

!!! warning "Обратите внимание"

    * Свойство `self` в моделях переименовано в `url`: в python это имя занято
      первым аргументом методов.
    * Все свойства `camelCase` переименованы в `pythonic_case`
      и конвертируются обратно при отправке запроса.
    * Имена методов придуманы автором библиотеки: в API Трекера собственных
      имён у методов нет.

### Версия API

По умолчанию используется API `v3`. Если вам нужна `v2` — передайте её явно:

```python
tracker = YaTracker(org_id=..., token=..., api_version="v2")
```

## С чего начать

* [С чего начать](howto.md) — установка, токены, первый запрос.
* [Обработка ошибок](errors.md) — какие исключения бросает библиотека и когда.
* [Работа с пользовательскими полями](custom_fields.md) — локальные поля очередей.

Официальная документация API: <https://yandex.cloud/ru/docs/tracker/about-api>
