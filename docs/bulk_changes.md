# Массовые операции (bulk changes)

Трекер умеет выполнять массовые (bulk) операции сразу над большим количеством задач —
до 10 000 штук за один вызов: редактировать поля, переводить по workflow или переносить в
другую очередь. В отличие от обычных методов, такие операции выполняются на сервере
асинхронно: вызов метода лишь ставит операцию в очередь и сразу возвращает объект
`BulkChange` с текущим статусом, а сам ход выполнения нужно затем отслеживать (опрашивать)
отдельно.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с массовыми операциями являются
    асинхронными. В примерах ниже вызовы показаны так, как будто мы уже находимся внутри
    корутины.

Официальная документация:

* <https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-update-issues>
* <https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-transition>
* <https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-issues>
* <https://yandex.ru/support/tracker/ru/concepts/bulkchange/bulk-move-info>

## Как это устроено

Любой из методов, запускающих операцию (`bulk_update_issues`, `bulk_transition_issues`,
`bulk_move_issues`), возвращает объект `BulkChange` практически сразу, не дожидаясь
завершения обработки всех задач. Дальше нужно:

1. дождаться завершения операции — вручную через `get_bulk_change`, либо с помощью
   `wait_bulk_change` (или шортката `bulk_change.wait()`), который сам опрашивает статус
   с заданным интервалом;
2. проверить итоговый статус (`is_complete` / `is_failed`);
3. если статус `FAILED`, разобраться, какие именно задачи не удалось обработать, —
   через `get_bulk_change_issues` (или `bulk_change.get_issues()`).

## Список задач: ключи, объекты или фильтр

Во все методы, запускающие операцию, параметр `issues` можно передать несколькими
способами:

* список ключей задач: `["WRITERS-1", "WRITERS-2"]`;
* список уже загруженных объектов `Issue`/`FullIssue` — библиотека сама возьмёт `.key`
  у каждого элемента;
* смешанный список ключей и объектов;
* **только для `bulk_update_issues`** — строка с фильтром на языке запросов Tracker,
  например `"Queue: WRITERS Assignee: empty()"`. Для `bulk_transition_issues` и
  `bulk_move_issues` фильтр не поддерживается API — передавайте список ключей.

Пустой список задач (или пустая строка-фильтр) приведёт к `ValueError`.

!!! warning "Строка — это фильтр, а не ключ"

    `bulk_update_issues("WRITERS-1", ...)` не обновит задачу `WRITERS-1`: строка без
    указания поля трактуется Трекером как полнотекстовый поиск. Чтобы обновить одну
    задачу, передайте список `["WRITERS-1"]` или фильтр `"Key: WRITERS-1"`.

## Массовое редактирование полей — `bulk_update_issues`

```python
bulk_change = await tracker.bulk_update_issues(
    issues=["WRITERS-1", "WRITERS-2"],
    values={"priority": "critical"},
)
```

Сигнатура:

```python
async def bulk_update_issues(
    self,
    issues: Sequence[str | Issue | FullIssue] | str,
    values: dict[str, Any] | None = None,
    *,
    notify: bool | None = None,
    **kwargs: Any,
) -> BulkChange: ...
```

- `issues` — список ключей/объектов задач либо строка-фильтр (см. выше).
- `values` — словарь полей, которые нужно изменить, в том же формате, что и при обычном
  `edit_issue`. Ключи в `snake_case` автоматически превращаются в `camelCase`
  (`attachment_ids` → `attachmentIds`); ключи локальных полей вида
  `"<id>--userId"` отправляются как есть.
- `notify` — уведомлять ли участников задач об изменении.
- `**kwargs` — то же самое, что и `values`, но именованными параметрами; значения из
  `kwargs` имеют приоритет при пересечении ключей. Значения `None` в `kwargs`
  отбрасываются (как и в `edit_issue`) — чтобы очистить поле, передайте `None` через
  `values`. Итоговый набор полей (`values` + `kwargs`) не может быть пустым — иначе
  `ValueError`.

```python
bulk_change = await tracker.bulk_update_issues(
    issues="Queue: WRITERS Assignee: empty()",
    assignee="new_login",
    notify=False,
)
```

Для полей типа «множество значений» (теги, наблюдатели и т. п.) поддерживаются операторы
`add`/`remove`/`set`:

```python
bulk_change = await tracker.bulk_update_issues(
    issues=["WRITERS-1", "WRITERS-2"],
    values={
        "tags": {"add": ["urgent"], "remove": ["stale"]},
        "followers": {"set": ["login1", "login2"]},
    },
)
```

## Массовый переход по workflow — `bulk_transition_issues`

```python
bulk_change = await tracker.bulk_transition_issues(
    issues=["WRITERS-1", "WRITERS-2"],
    transition="close",
    values={"resolution": "fixed"},
)
```

Сигнатура:

```python
async def bulk_transition_issues(
    self,
    issues: Sequence[str | Issue | FullIssue],
    transition: str | Transition,
    values: dict[str, Any] | None = None,
    *,
    notify: bool | None = None,
    **kwargs: Any,
) -> BulkChange: ...
```

- `issues` — список ключей/объектов задач (строка-фильтр здесь не поддерживается, будет
  выброшен `TypeError`).
- `transition` — переход: строковый id (`"close"`) либо объект `Transition`, полученный,
  например, из `get_transitions` — тогда библиотека сама возьмёт `.id`.
- `values` — дополнительные поля перехода, например `{"resolution": "fixed"}`.
- `notify` — уведомлять ли участников задач.
- `**kwargs` — альтернатива `values` в виде именованных параметров; объединяются так же,
  как в `bulk_update_issues`. Пустой набор `values`/`kwargs` допустим — в этом случае поле
  `values` просто не отправляется в теле запроса.

## Массовый перенос в очередь — `bulk_move_issues`

```python
bulk_change = await tracker.bulk_move_issues(
    issues=["WRITERS-1", "WRITERS-2"],
    queue="ARCHIVE",
)
```

Сигнатура:

```python
async def bulk_move_issues(
    self,
    issues: Sequence[str | Issue | FullIssue],
    queue: str | Queue | FullQueue,
    values: dict[str, Any] | None = None,
    *,
    move_all_fields: bool | None = None,
    initial_status: bool | None = None,
    notify: bool | None = None,
    **kwargs: Any,
) -> BulkChange: ...
```

- `issues` — список ключей/объектов задач (строка-фильтр не поддерживается).
- `queue` — очередь назначения: ключ строкой либо объект `Queue`/`FullQueue` (тогда
  берётся `.key`).
- `values` — дополнительные поля, которые нужно изменить одновременно с переносом.
- `move_all_fields` — сохранить значения компонентов/версий/проектов, если они существуют
  и в целевой очереди (по умолчанию при переносе такие поля очищаются).
- `initial_status` — сбросить статус перенесённых задач в начальный статус целевой
  очереди.
- `notify` — уведомлять ли участников задач.
- `**kwargs` — альтернатива `values` в виде именованных параметров.

```python
bulk_change = await tracker.bulk_move_issues(
    issues=["WRITERS-1", "WRITERS-2"],
    queue="ARCHIVE",
    move_all_fields=True,
    initial_status=True,
)
```

## Статус операции — `get_bulk_change`

```python
bulk_change = await tracker.get_bulk_change(bulk_change.id)
```

Сигнатура:

```python
async def get_bulk_change(self, bulk_change: str | BulkChange) -> BulkChange: ...
```

Возвращает актуальное состояние операции. Принимает как `id` строкой, так и уже
полученный объект `BulkChange`.

## Ошибки по каждой задаче — `get_bulk_change_issues`

API возвращает **только задачи, которые не удалось обработать**, вместе с описанием
ошибок; успешно обработанные задачи в ответ не попадают. Если операция завершилась
статусом `FAILED` (частично или полностью), разобраться в причинах можно так:

```python
results = await tracker.get_bulk_change_issues(bulk_change.id)

for result in results:
    if result.status == "FAILED" and result.error is not None:
        print(result.issue.key, result.error.errors)
```

Сигнатура:

```python
async def get_bulk_change_issues(
    self,
    bulk_change: str | BulkChange,
) -> list[BulkChangeIssue]: ...
```

## Ожидание завершения — `wait_bulk_change`

Вместо ручного опроса `get_bulk_change` в цикле удобнее воспользоваться `wait_bulk_change` —
он сам опрашивает статус операции, пока она не станет финальной (`COMPLETE` или `FAILED`):

```python
bulk_change = await tracker.wait_bulk_change(bulk_change.id, interval=1.0, timeout=60.0)
```

Сигнатура:

```python
async def wait_bulk_change(
    self,
    bulk_change: str | BulkChange,
    *,
    interval: float = 1.0,
    timeout: float | None = None,
) -> BulkChange: ...
```

- `bulk_change` — `id` операции строкой либо уже полученный объект `BulkChange`. Если
  переданный объект уже в финальном статусе, он возвращается сразу, без запросов к API.
- `interval` — пауза между опросами статуса, в секундах (должен быть больше `0`, иначе
  `ValueError`).
- `timeout` — необязательный общий тайм-аут ожидания, в секундах (если задан, должен
  быть больше `0`). Если операция не завершится за это время, будет выброшено
  встроенное исключение `TimeoutError` (на всех поддерживаемых версиях Python, включая
  3.10). По умолчанию тайм-аута нет — в автоматических сценариях лучше задавать его
  явно.

!!! note "Задержка появления операции"

    Сразу после создания операция может ещё не быть доступна по своему `id` — API Трекера
    в первые мгновения может ответить `404`. `wait_bulk_change` учитывает это и в начале
    ожидания несколько раз молча повторяет попытку получить статус, прежде чем считать
    операцию действительно не найденной. Как только операция была получена хотя бы раз,
    последующий `404` сразу приводит к `ObjectNotFoundError`.

## Модель `BulkChange`

| Поле                       | Тип                | Описание                                          |
|-----------------------------|--------------------|-----------------------------------------------------|
| `url`                        | `str`              | Ссылка на операцию (в API — поле `self`)             |
| `id`                          | `str`              | Идентификатор операции                               |
| `created_by`                | `User`             | Пользователь, запустивший операцию                    |
| `created_at`                | `datetime`         | Дата и время создания операции                        |
| `status`                    | `str`              | Текущий статус: `CREATED`, `RUNNING`, `COMPLETE`, `FAILED` |
| `status_text`              | `str \| None`      | Текстовое описание статуса                            |
| `execution_chunk_percent`  | `float \| None`    | Процент выполнения по чанкам                          |
| `execution_issue_percent`  | `float \| None`    | Процент выполнения по задачам                         |
| `total_issues`              | `int \| None`      | Всего задач в операции (доступно не всегда)           |
| `total_completed_issues`   | `int \| None`      | Сколько задач уже обработано (доступно не всегда)     |

У модели есть вспомогательные свойства:

- `is_complete` — `True`, если `status == "COMPLETE"`.
- `is_failed` — `True`, если `status == "FAILED"`.
- `is_finished` — `True`, если операция достигла финального статуса (`COMPLETE` или
  `FAILED`).

А также методы-шорткаты, эквивалентные вызову одноимённых методов `tracker.*` с `id`
операции:

```python
# -> tracker.get_bulk_change(bulk_change.id)
bulk_change = await bulk_change.refresh()

# -> tracker.wait_bulk_change(bulk_change)
bulk_change = await bulk_change.wait()

# -> tracker.get_bulk_change_issues(bulk_change.id)
results = await bulk_change.get_issues()
```

`BulkChangeIssue` (элемент результата `get_bulk_change_issues`) содержит:

| Поле         | Тип                     | Описание                                    |
|--------------|--------------------------|------------------------------------------------|
| `issue`      | `Issue`                  | Задача, к которой относится результат            |
| `status`     | `str`                    | Статус обработки задачи, например `FAILED`      |
| `status_text`| `str \| None`            | Текстовое описание статуса                       |
| `error`      | `BulkChangeError \| None`| Подробности ошибки, если задачу не удалось обработать |

`BulkChangeError` содержит `errors` (словарь `поле: описание ошибки`; обычно это строка,
но тип намеренно не ограничен) и `error_messages` (список общих сообщений об ошибке,
не привязанных к конкретному полю).

## Пример целиком

```python
bulk_change = await tracker.bulk_update_issues(
    issues=["WRITERS-1", "WRITERS-2"],
    values={"tags": {"add": ["reviewed"]}},
)

bulk_change = await tracker.wait_bulk_change(bulk_change, interval=1.0, timeout=60.0)

if bulk_change.is_failed:
    for result in await bulk_change.get_issues():
        if result.error is not None:
            print(result.issue.key, result.error.errors)
else:
    print("Готово:", bulk_change.total_completed_issues, "из", bulk_change.total_issues)
```
