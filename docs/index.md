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
| Задачи | `get_issue`, `create_issue`, `edit_issue`, `move_issue`, `find_issues`, `iter_issues`, `count_issues`, `suggest_issues`, `clear_search_scroll`, `get_issue_links`, `link_issues`, `unlink_issues`, `get_issue_changelog`, `iter_issue_changelog`, `get_transitions`, `execute_transition` | [Задачи](issues.md) |
| Очереди | `get_queue`, `get_queues`, `create_queue`, `delete_queue`, `restore_queue`, `get_queue_tags`, `delete_tag_from_queue`, `get_queue_fields`, `get_queue_versions`, `create_queue_version` | [Очереди](queues.md) |
| Права доступа очередей | `get_queue_user_access`, `get_queue_group_access`, `update_queue_access`, `get_component_user_access`, `get_component_group_access` | [Права доступа очередей](queue_access.md) |
| Поля задач | `get_global_fields`, `get_field`, `create_field`, `update_field`, `get_field_categories`, `create_field_category`, `update_field_category`, `get_local_fields`, `get_local_field`, `create_local_field`, `update_local_field` | [Поля задач](issue_fields.md) |
| Компоненты | `get_components`, `get_queue_components`, `create_component`, `update_component` | [Компоненты](components.md) |
| Рабочие процессы | `get_workflows`, `get_workflow`, `create_workflow`, `update_workflow`, `update_workflow_action`, `delete_workflow` | [Рабочие процессы](workflows.md) |
| Триггеры | `get_triggers`, `iter_triggers`, `get_trigger`, `create_trigger`, `update_trigger`, `get_trigger_logs` | [Триггеры](triggers.md) |
| Автодействия | `get_autoaction`, `create_autoaction`, `get_autoaction_logs`, `get_autoaction_log` | [Автодействия](autoactions.md) |
| Проекты (устаревший API) | `get_projects`, `get_project`, `create_project`, `update_project`, `delete_project`, `get_project_queues` | [Проекты (устаревший API)](projects.md) |
| Проекты, портфели и цели | `create_entity`, `get_entity`, `update_entity`, `delete_entity`, `search_entities`, `iter_entities`, `bulk_update_entities`, `get_entity_events` | [Проекты, портфели и цели](entities.md) |
| Комментарии сущностей | `get_entity_comments`, `get_entity_comments_relative`, `get_entity_comment`, `post_entity_comment`, `edit_entity_comment`, `delete_entity_comment` | [Комментарии сущностей](entity_comments.md) |
| Файлы сущностей | `get_entity_attachments`, `get_entity_attachment`, `attach_file_to_entity`, `delete_entity_attachment` | [Файлы сущностей](entity_attachments.md) |
| Чек-листы сущностей | `add_entity_checklist_item`, `edit_entity_checklist`, `edit_entity_checklist_item`, `move_entity_checklist_item`, `delete_entity_checklist_item`, `delete_entity_checklist` | [Чек-листы сущностей](entity_checklists.md) |
| Связи сущностей | `get_entity_links`, `link_entities`, `delete_entity_link` | [Связи сущностей](entity_links.md) |
| Доступ к сущностям | `get_entity_access`, `update_entity_access` | [Доступ к сущностям](entity_access.md) |
| Макросы | `get_macros`, `get_macro`, `create_macro`, `update_macro`, `delete_macro` | [Макросы](macros.md) |
| Доски | `get_boards`, `get_boards_paginated`, `iter_boards`, `get_board`, `create_board`, `update_board`, `delete_board`, `get_board_columns`, `get_board_column`, `create_board_column`, `update_board_column`, `delete_board_column` | [Доски и спринты](boards.md) |
| Спринты | `get_sprints`, `get_sprint`, `create_sprint`, `update_sprint`, `start_sprint`, `archive_sprint`, `delete_sprint` | [Доски и спринты](boards.md) |
| Комментарии | `get_comments`, `post_comment`, `edit_comment`, `delete_comment`, `add_comment_reaction` | [Комментарии](comments.md) |
| Чек-листы | `get_checklist`, `add_checklist_item`, `edit_checklist_item`, `delete_checklist_item`, `delete_checklist` | [Чек-листы](checklists.md) |
| Учёт времени | `post_worklog`, `edit_worklog`, `delete_worklog`, `get_issue_worklog`, `get_worklog` | [Учёт времени](worklogs.md) |
| Вложения | `get_attachments`, `attach_file`, `upload_temp_file`, `download_attachment`, `download_thumbnail`, `delete_attachment` | [Вложения](attachments.md) |
| Массовые операции | `bulk_update_issues`, `bulk_transition_issues`, `bulk_move_issues`, `get_bulk_change`, `get_bulk_change_issues`, `wait_bulk_change` | [Массовые операции](bulk_changes.md) |
| Импорт | `import_issue`, `import_comment`, `import_link`, `import_attachment`, `import_worklog` | [Импорт](import.md) |
| Внешние приложения | `get_applications`, `get_remote_links`, `add_remote_link`, `delete_remote_link` | [Внешние приложения](applications.md) |
| Пользователи | `get_users`, `get_users_relative`, `iter_users`, `get_user`, `get_myself` | [Пользователи](users.md) |
| Администрирование | `get_issue_types`, `create_issue_type`, `update_issue_type`, `get_statuses`, `create_status`, `update_status`, `get_resolutions`, `create_resolution`, `update_resolution`, `get_priorities`, `create_priority`, `update_priority` | [Администрирование](admin.md) |
| Отчёты по задачам | `create_report`, `search_reports` | [Отчёты по задачам](reports.md) |
| Фильтры | `create_filter`, `get_filter`, `update_filter` | [Фильтры](filters.md) |
| Отсутствия | `create_gap`, `create_gaps`, `search_gaps`, `iter_gaps`, `delete_gap`, `delete_gaps` | [Отсутствия](gaps.md) |
| Дашборды | `create_dashboard`, `create_cycle_time_widget` | [Дашборды](dashboards.md) |

!!! note "Покрытие API"

    Библиотека покрывает все разделы официального справочника API Трекера.
    Если вы нашли метод, которого нет в таблице выше, — его всё ещё можно
    вызвать напрямую через `tracker._client.request(...)`, а лучше
    [завести issue](https://github.com/Olegt0rr/YaTracker/issues) или прислать pull request.

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

!!! warning "Заголовки запроса"

    `_make_request()` получает все параметры запроса именованными аргументами: `params`,
    `data` (тело в виде `aiohttp`-payload или `FormData`) и, когда они нужны, `headers` —
    дополнительные заголовки вроде `If-Match` у досок и спринтов. Свой транспорт обязан
    передавать их в HTTP-вызов и объединять `headers` с заголовками по умолчанию
    (`Authorization`, `X-Org-ID`): если их молча отбросить, оптимистичная блокировка
    перестанет работать без единой ошибки.

### pydantic

В качестве основы для моделирования объектов API используется библиотека `pydantic` (v2),
ядро которой написано на `rust` – она обеспечивает быструю валидацию и сериализацию моделей,
а также прекрасно знакома большинству python-разработчиков.

Ответы Трекера сразу превращаются в модели: `FullIssue`, `FullQueue`, `Project`, `Entity`,
`Comment`, `Worklog`, `Attachment`, `Transition` и другие. Даты приходят готовыми
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
      и конвертируются обратно при отправке запроса. Аргумент `url=` при этом
      уходит в API как `url`, а вложенные в запрос модели сохраняют ключ `self`.
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
