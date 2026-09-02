# Работа с задачами

На этой странице собраны все методы `YaTracker`, которые относятся к задачам: получение,
создание, редактирование, перемещение между очередями, подсчёт, поиск и постраничная
итерация, работа со связями между задачами и переходами по workflow.

Официальная документация Yandex Tracker API: https://yandex.cloud/ru/docs/tracker/about-api

!!! note "Обратите внимание"

    Все методы, вызывающие API, — асинхронные, вызывать их нужно внутри корутин. Как и в
    остальной документации, в примерах ниже `await` используется так, будто мы уже находимся
    внутри асинхронной функции.

## Именование полей

Модели библиотеки (`Issue`, `FullIssue`, `IssueLink`, `Transition` и другие) используют
python-имена в стиле `snake_case`, а при обмене данными с Tracker они автоматически
конвертируются в `camelCase`, как принято в самом API. Поле `self`, зарезервированное в
Python, везде переименовано в `url`.

Это касается и именованных параметров (`**kwargs`) методов ниже: `type_` уходит в API как
`type`, `filter_` — как `filter`, `attachment_ids` — как `attachmentIds` и т. д. Обратного
переименования `url` → `self` при этом нет: ключ `self` выставляет сам трекер, поэтому
аргумент `url=` отправляется как `url` (подробнее — в разделе о пользовательских полях).

Если вам нужны собственные поля задачи (например, локальные поля очереди), обратитесь к
разделу [Работа с пользовательскими полями](custom_fields.md) — параметр `_type`,
упоминаемый ниже, работает одинаково для всех методов.

## Получение задачи

```python
issue = await tracker.get_issue("WRITERS-42")
```

Сигнатура:

```python
async def get_issue(
    self,
    issue_id: str,
    expand: str | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
    *,
    fields: str | None = None,
) -> IssueT_co | FullIssue: ...
```

- `issue_id` — ID или ключ задачи (например, `"WRITERS-42"`).
- `expand` — какие дополнительные данные подтянуть вместе с задачей:
  `"transitions"` — доступные переходы по workflow, `"attachments"` — вложения.
- `fields` — список полей ответа через запятую. Поля, не перечисленные здесь, в ответе не
  придут, поэтому если вы используете `fields`, передавайте и `_type` с моделью, у которой
  обязательные поля соответствуют этой проекции (иначе валидация упадёт, т.к. `FullIssue`
  по умолчанию ожидает полный набор полей).
- `_type` — своя модель задачи вместо `FullIssue`, см. [пользовательские поля](custom_fields.md).

```python
issue = await tracker.get_issue("WRITERS-42", expand="transitions")
```

## Создание задачи

```python
issue = await tracker.create_issue("Написать шедевр", "WRITERS")
```

Сигнатура:

```python
async def create_issue(
    self,
    summary: str,
    queue: str | int | dict,
    *,
    parent: Issue | str | None = None,
    description: str | None = None,
    sprint: dict[str, str] | None = None,
    type_: IssueType | None = None,
    priority: int | str | Priority | None = None,
    followers: list[str] | None = None,
    assignee: list[str] | None = None,
    unique: str | None = None,
    attachment_ids: list[str] | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
    **kwargs,
) -> IssueT_co | FullIssue: ...
```

- `summary` — заголовок задачи (обязателен).
- `queue` — ключ очереди (`"WRITERS"`), её числовой ID, либо словарь вида `{"key": "WRITERS"}`.
- `parent` — родительская задача: объект `Issue`, либо строка с ID/ключом.
- `description` — описание задачи.
- `sprint` — привязка к спринту, например `{"id": "123"}`.
- `type_` — тип задачи. Ожидается объект `IssueType` (его удобно взять из уже загруженной
  задачи: `existing_issue.type`).
- `priority` — приоритет: числовой ID, строковый ключ (`"critical"`, `"normal"`, `"minor"`
  и т. п.) или объект `Priority`.
- `followers` — список логинов наблюдателей.
- `assignee` — список логинов исполнителя (принимающая сторона API — строка/логин).
- `unique` — ключ идемпотентности: повторный вызов с тем же значением не создаст дубликат.
- `attachment_ids` — ID заранее загруженных вложений, которые нужно прикрепить к задаче.
- `**kwargs` — любые другие поля задачи, включая пользовательские (локальные) поля очереди.

```python
issue = await tracker.create_issue(
    summary="Починить прод",
    queue="OPS",
    description="Сервис отдаёт 500 на /health",
    priority="critical",
    assignee=["user_login"],
    followers=["another_login"],
    unique="incident-2026-09-01-1",
)
```

## Редактирование задачи

```python
issue = await tracker.edit_issue(
    issue_id="WRITERS-1",
    description="... или нечто ценное",
)
```

Сигнатура:

```python
async def edit_issue(
    self,
    issue_id: str,
    version: str | int | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
    **kwargs,
) -> IssueT_co | FullIssue: ...
```

- `issue_id` — ID или ключ редактируемой задачи.
- `version` — версия задачи для оптимистичной блокировки. Если её передать и она устареет
  (задачу параллельно изменили), Tracker вернёт ошибку конфликта версий.
- `**kwargs` — любые поля задачи, которые нужно изменить (`summary`, `description`,
  `priority`, `assignee`, пользовательские поля и т. д.) — правила именования те же, что и
  при создании.

```python
issue = await tracker.edit_issue("WRITERS-1", version=2, priority="minor")
```

## Перемещение задачи в другую очередь

```python
issue = await tracker.move_issue("WRITERS-1", "ARCHIVE")
```

Сигнатура:

```python
async def move_issue(
    self,
    issue_id: str,
    queue_key: str,
    *,
    notify: bool = True,
    notify_author: bool = False,
    move_all_fields: bool = False,
    initial_status: bool = False,
    expand: str | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
    **kwargs,
) -> IssueT_co | FullIssue: ...
```

- `issue_id` — ID или ключ перемещаемой задачи.
- `queue_key` — ключ очереди назначения.
- `notify` — уведомлять ли участников задачи о перемещении (по умолчанию `True`).
- `notify_author` — уведомлять ли отдельно автора задачи (по умолчанию `False`).
- `move_all_fields` — по умолчанию при переносе компоненты, версии и проекты задачи
  очищаются; если в целевой очереди есть такие же значения, установите `True`, чтобы их
  сохранить.
- `initial_status` — сбросить статус задачи на начальный, если в целевой очереди нет
  статуса/типа исходной задачи (иначе перенос не выполнится).
- `expand` — как и в `get_issue`, что дополнительно подтянуть в ответ.
- `**kwargs` — тело запроса в том же формате, что и при редактировании — можно одновременно
  изменить поля задачи при переносе.

```python
issue = await tracker.move_issue(
    "WRITERS-1",
    "ARCHIVE",
    notify=False,
    move_all_fields=True,
)
```

!!! note "Обратите внимание"

    Пользователь, выполняющий перенос, должен иметь право на редактирование переносимой
    задачи и право на создание задач в целевой очереди.

## Подсчёт задач

```python
total = await tracker.count_issues(filter_={"queue": "WRITERS"})
```

Сигнатура:

```python
async def count_issues(
    self,
    filter_: dict[str, str] | None = None,
    query: str | None = None,
) -> int: ...
```

- `filter_` — фильтр по значениям полей, например `{"queue": "WRITERS", "status": "open"}`.
- `query` — запрос на языке запросов Tracker (см. раздел ниже). `filter_` и `query`
  взаимоисключающие способы задать критерии поиска, как и в самом API.

```python
count = await tracker.count_issues(query="Queue: WRITERS AND Status: Open")
```

## Поиск и фильтрация задач

```python
issues = await tracker.find_issues(filter_={"queue": "WRITERS"})
```

Сигнатура:

```python
async def find_issues(
    self,
    filter_: dict[str, str] | None = None,
    query: str | None = None,
    order: str | None = None,
    expand: str | None = None,
    keys: str | None = None,
    queue: str | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
    *,
    per_page: int | None = None,
    page: int | None = None,
    scroll_type: str | None = None,
    per_scroll: int | None = None,
    scroll_ttl_millis: int | None = None,
    scroll_id: str | None = None,
    fields: str | None = None,
) -> list[IssueT_co] | list[FullIssue]: ...
```

- `filter_` — фильтр по полям (словарь `поле: значение`).
- `query` — запрос на [языке запросов Tracker](https://yandex.cloud/ru/docs/tracker/about-api),
  например `"Queue: WRITERS AND Status: Open ORDER BY Priority DESC"`.
- `order` — сортировка результата, например `"+key"` или `"-priority"`.
- `expand` — дополнительные данные в ответе (`"transitions"`, `"attachments"`).
- `keys` — прямой поиск по ключам задач (через запятую), альтернатива `filter_`/`query`.
- `queue` — ограничить поиск одной очередью (альтернативная форма запроса).
- `fields` — проекция полей ответа, как и в `get_issue`: непойменованные поля не придут, так
  что `_type` должен соответствовать выбранной проекции.
- `_type` — своя модель задачи.

Постраничный вывод (обычная пагинация):

```python
issues = await tracker.find_issues(
    query="Queue: WRITERS",
    per_page=50,
    page=2,
)
```

Если в ответе больше 10 000 задач, обычная пагинация не подойдёт — используйте scroll API:
передайте `scroll_type` (`"sorted"` или `"unsorted"`) и `per_scroll`/`scroll_ttl_millis`,
чтобы начать сессию скроллинга, а затем передавайте `scroll_id`, полученный от API, чтобы
продолжить её на следующих вызовах.

```python
first_page = await tracker.find_issues(
    filter_={"queue": "WRITERS"},
    scroll_type="sorted",
    per_scroll=100,
)
```

!!! note "Обратите внимание"

    Scroll API не поддерживается вместе с формами поиска `keys` и `queue` — API в этом случае
    ответит ошибкой HTTP 400. Кроме того, `find_issues` не может отдать вам `scrollId` для
    продолжения сессии — он приходит в заголовке ответа `X-Scroll-Id`, а не в теле. Чтобы не
    работать со скроллингом вручную, используйте `iter_issues` ниже.

### suggest_issues

Отдельный метод для подсказок по фрагменту названия задачи (то, что показывает интерфейс
Трекера при наборе текста в поиске):

```python
issues = await tracker.suggest_issues("исправить ошибки")

for issue in issues:
    print(issue.key, issue.summary)
```

Сигнатура:

```python
async def suggest_issues(
    self,
    input_: str,
    _type: type[SuggestT_co | IssueSuggest] = IssueSuggest,
    *,
    queue: str | None = None,
    full: bool | None = None,
    fields: str | None = None,
    expand: str | None = None,
    embed: str | None = None,
) -> list[SuggestT_co] | list[IssueSuggest]: ...
```

1. `input_` — фрагмент текста в названии задачи (query-параметр `input`). Пробел между
   словами также совпадает с любым текстом на его месте.
2. `queue` — ограничить поиск одной очередью.
3. `full` — вернуть подробную информацию о каждой задаче вместо краткой проекции; по
   умолчанию `False`. Обязателен, чтобы включить `fields`, `expand` и `embed`.
4. `fields` — список полей задачи через запятую.
5. `expand` — дополнительные данные: `"all"`, `"html"`, `"attachments"`, `"comments"`,
   `"links"`, `"localLinkRefs"`, `"aliases"`, `"transitions"`, `"permissions"`, `"sla"` или
   `"update_limits"`.
6. `embed` — детали по тому, что запрошено в `expand`: `"attachments"`, `"comments"`,
   `"transitions"` или `"sla"`.
7. `_type` — модель, которой декодируется ответ. По умолчанию `IssueSuggest` — узкая
   модель ровно под краткую проекцию ответа.

Модель `IssueSuggest`:

| Поле        | Тип                  | Описание                          |
|-------------|----------------------|-----------------------------------|
| `url`       | `str`                | Ссылка на задачу (`self`)         |
| `id`        | `str`                | Идентификатор задачи              |
| `key`       | `str`                | Ключ задачи                       |
| `version`   | `int`                | Версия задачи                     |
| `summary`   | `str \| None`        | Название задачи                   |
| `followers` | `list[User] \| None` | Наблюдатели задачи                |
| `assignee`  | `User \| None`       | Исполнитель задачи                |
| `status`    | `Status \| None`     | Статус задачи                     |

!!! warning "По умолчанию возвращается краткая проекция, а не `FullIssue`"

    API отдаёт краткую проекцию задачи (`self`, `id`, `key`, `version`, `summary`,
    `followers`, `assignee`, `status`), а не весь набор полей `FullIssue`. Поэтому по
    умолчанию ответ декодируется в `IssueSuggest`. `full=True` с типом по умолчанию тоже
    работает — лишние поля просто игнорируются.

    Если нужны полноценные задачи, передайте `_type=FullIssue` **вместе с `full=True` и
    без `fields`**: `fields` урезает ответ, и `FullIssue` не пройдёт валидацию из-за
    отсутствующих обязательных полей (см. [«Обработка ошибок»](errors.md)).

```python
from yatracker.types import FullIssue

# краткая проекция (по умолчанию)
issues = await tracker.suggest_issues("исправить ошибки", queue="WRITERS")

# полноценные задачи
issues = await tracker.suggest_issues("исправить ошибки", FullIssue, full=True)
```

Источник: https://yandex.ru/support/tracker/ru/api/issues/get-suggest

## Итерация по всем задачам

Чтобы прочитать больше 10 000 задач без ручного управления scroll-сессией, используйте
`iter_issues` — это асинхронный генератор поверх scroll API:

```python
async for issue in tracker.iter_issues(filter_={"queue": "WRITERS"}):
    print(issue.key)
```

Сигнатура:

```python
async def iter_issues(
    self,
    filter_: dict[str, str] | None = None,
    query: str | None = None,
    order: str | None = None,
    expand: str | None = None,
    queue: str | None = None,
    _type: type[IssueT_co | FullIssue] = FullIssue,
    *,
    scroll_type: str = "sorted",
    per_scroll: int = 100,
    scroll_ttl_millis: int | None = None,
    fields: str | None = None,
) -> AsyncIterator[IssueT_co | FullIssue]: ...
```

- `scroll_type` — `"sorted"` или `"unsorted"`, по умолчанию `"sorted"`.
- `per_scroll` — сколько задач запрашивать за одну страницу скролла, по умолчанию `100`.
- `scroll_ttl_millis` — время жизни scroll-сессии в миллисекундах.
- `queue` — здесь нет отдельного параметра `keys`: форма поиска по `keys` не совместима со
  scroll API, а `queue`, если передан, автоматически подмешивается в `filter_` перед
  отправкой запроса.
- Итерация останавливается, когда очередная страница пуста или API перестаёт присылать
  заголовок `X-Scroll-Id`.
- Если выйти из цикла досрочно (`break`, исключение), `iter_issues` сам вызовет
  `clear_search_scroll` для накопленных пар `X-Scroll-Id` / `X-Scroll-Token` — подробнее
  в предупреждении ниже.

Если нужно управлять scroll-сессией вручную (например, встроить в свою пагинацию), можно
по-прежнему пользоваться `find_issues`, передавая `scroll_id` явно.

### clear_search_scroll

Каждая страница scroll-поиска держит на сервере снимок результатов до истечения
`scroll_ttl_millis`. Чтобы освободить ресурсы раньше, используйте `clear_search_scroll`:

```python
async def clear_search_scroll(self, scroll_ids: Mapping[str, str]) -> bool: ...
```

```python
released = await tracker.clear_search_scroll(
    {
        "<X-Scroll-Id страницы 1>": "<X-Scroll-Token страницы 1>",
        "<X-Scroll-Id страницы 2>": "<X-Scroll-Token страницы 2>",
    }
)
```

- `scroll_ids` — отображение `{идентификатор страницы: токен страницы}`. Идентификатор —
  это заголовок ответа `X-Scroll-Id`, токен — `X-Scroll-Token`, которые Трекер присылает на
  каждую страницу поиска с активным scroll (`POST /issues/_search` с `scrollType`). Нужно
  передать пары для **всех** страниц одного поиска разом — по одной паре на каждую
  полученную страницу.

!!! note "Опечатка в официальной документации"

    Страница API показывает тело запроса как `{"srollId": "scrollToken"}` — это
    placeholder с опечаткой (`sroll` вместо `scroll`), а не буквальное имя ключа: в
    описании параметров ключ назван `scrollId`, а полный пример запроса использует в
    качестве ключей реальные scroll id. Поэтому тело запроса — обычное отображение
    `{scroll_id: scroll_token}`, как и реализует `clear_search_scroll`.

!!! warning "Как освобождаются ресурсы scroll-поиска"

    `iter_issues` дочитывает scroll-сессию до конца (пока страница не окажется пустой или
    API не перестанет присылать `X-Scroll-Id`) — в этом случае освобождать ресурсы не
    нужно. Если же выйти из цикла досрочно (`break`, исключение), `iter_issues` вызовет
    `clear_search_scroll` сам: он запоминает пары `X-Scroll-Id` / `X-Scroll-Token` со всех
    прочитанных страниц и отправляет их разом при закрытии генератора. Освобождение
    делается «как получится»: ошибки этого вызова гасятся, чтобы не подменять исходное
    исключение.

    Гарантии, что вызов произойдёт, нет: он привязан к закрытию асинхронного генератора
    (`aclose()` или `shutdown_asyncgens` при завершении цикла событий — это делают за вас
    `async for` вместе с `asyncio.run`). Если генератор так и не будет закрыт, снимок
    результатов провисит на сервере до истечения `scroll_ttl_millis`.

    Ведёте scroll-сессию вручную через `find_issues` — вызывайте `clear_search_scroll`
    сами. Учтите, что `find_issues` не отдаёт заголовки ответа, поэтому получить
    `X-Scroll-Id` и `X-Scroll-Token` через него нельзя: пары приходится собирать своим
    HTTP-клиентом либо пользоваться `iter_issues`.

Источник: https://yandex.ru/support/tracker/ru/api/issues/search-release

## Приоритеты

Приоритет задачи (`priority`) в `create_issue`/`edit_issue` можно передать как:

- числовой ID приоритета;
- строковый ключ приоритета (`"critical"`, `"normal"`, `"minor"` и т. д.);
- объект `Priority`, например взятый из уже загруженной задачи (`issue.priority`).

```python
issue = await tracker.edit_issue("WRITERS-1", priority="critical")
```

Список приоритетов, доступных в вашей организации, можно получить отдельным методом
`get_priorities` (см. соответствующий раздел документации).

## Связи между задачами

```python
links = await tracker.get_issue_links("WRITERS-1")
for link in links:
    print(link.name, link.object.key)
```

Сигнатура:

```python
async def get_issue_links(self, issue_id: str) -> list[IssueLink]: ...
```

`IssueLink` описывает связь одной задачи с другой (ответ `GET /issues/{id}/links`):

| Поле         | Тип              | Описание                                              |
|--------------|------------------|-------------------------------------------------------|
| `url`        | `str`            | Ссылка на связь (`self`)                              |
| `id`         | `int`            | Идентификатор связи                                   |
| `type`       | `LinkType`       | Тип связи, содержит подписи `inward`/`outward`         |
| `direction`  | `LinkDirection`  | Направление связи: `INWARD` или `OUTWARD`              |
| `object`     | `Issue`          | Связанная задача                                       |
| `assignee`   | `User \| None`   | Исполнитель связанной задачи                           |
| `status`     | `Status`         | Текущий статус связанной задачи                        |
| `created_by` | `User`           | Автор связи                                            |
| `updated_by` | `User \| None`   | Кто изменил связь                                      |
| `created_at` | `datetime`       | Дата и время создания связи                            |
| `updated_at` | `datetime \| None` | Дата и время изменения связи                        |

`name` — свойство-хелпер: возвращает подпись связи (`type.inward` или `type.outward` в
зависимости от `direction`) — удобно для вывода вроде «зависит от», «блокирует» и т. п.

Кроме связей между задачами, Трекер поддерживает связи с объектами внешних приложений
(например, коммитами или pull request'ами Bitbucket) — такие связи называются внешними
ссылками. Про них подробно рассказано в разделе [«Внешние приложения»](applications.md).

### link_issues

```python
async def link_issues(
    self,
    issue_id: str,
    relationship: LinkRelationship | str,
    issue: str | Issue | FullIssue,
) -> CreatedIssueLink: ...
```

Создаёт связь между текущей задачей (`issue_id`) и другой (`issue`).

```python
from yatracker.types.issue_link import LinkRelationship

link = await tracker.link_issues("WRITERS-1", LinkRelationship.RELATES, "WRITERS-2")
```

1. `issue_id` — ID или ключ текущей задачи.
2. `relationship` — тип связи: значение `LinkRelationship` либо обычная строка.
   Документированы значения `"relates"`, `"is dependent by"`, `"depends on"`,
   `"is subtask for"`, `"is parent task for"`, `"duplicates"`, `"is duplicated by"`,
   `"is epic of"` и `"has epic"` (два последних — только для задач типа «Эпик»).
   `LinkRelationship` содержит ещё `CLONE` и `ORIGINAL`, но они относятся только к импорту
   задач, см. [«Импорт задач»](import.md).
3. `issue` — ID/ключ связываемой задачи строкой, либо уже загруженный объект `Issue`
   или `FullIssue` (тогда используется `issue.key`).

Возвращается `CreatedIssueLink` — та же связь, что и в `get_issue_links`, но с
необязательными `assignee` и `status`:

| Поле       | Тип              | Описание                                             |
|------------|------------------|------------------------------------------------------|
| `assignee` | `User \| None`   | Исполнитель связанной задачи, в ответе отсутствует   |
| `status`   | `Status \| None` | Статус связанной задачи, в ответе отсутствует        |

Остальные поля совпадают с `IssueLink` (см. таблицу выше).

!!! note "Почему отдельная модель"

    В таблице параметров ответа документация перечисляет `assignee` и `status`, но пример
    ответа `POST /issues/{id}/links` их не содержит. Поэтому у `CreatedIssueLink` оба поля
    необязательны, а у `IssueLink` (ответ `GET /issues/{id}/links`, где они приходят
    всегда) `status` остаётся обязательным — `link.status.key` у прочитанных связей
    по-прежнему проходит проверку типов.

Источник: https://yandex.ru/support/tracker/ru/api/issues/link-issue

### unlink_issues

```python
async def unlink_issues(self, issue_id: str, link_id: str | int) -> bool: ...
```

Удаляет связь. Возвращает `True` при успешном удалении.

```python
await tracker.unlink_issues("WRITERS-1", link.id)
```

1. `issue_id` — ID или ключ текущей задачи.
2. `link_id` — ID связи (поле `IssueLink.id`, полученное из `get_issue_links` или
   `link_issues`).

Источник: https://yandex.ru/support/tracker/ru/api/issues/delete-link-issue

### Методы на объекте задачи

Как и другие методы, работающие с одной задачей, `get_issue_links`, `link_issues` и
`unlink_issues` продублированы на `FullIssue`, чтобы не передавать `issue_id` вручную —
они действуют на ту задачу, у которой были вызваны:

```python
issue = await tracker.get_issue("WRITERS-1")

links = await issue.get_links()
link = await issue.link("relates", "WRITERS-2")
await issue.unlink(link.id)
```

* `issue.get_links()` — эквивалент `tracker.get_issue_links(issue.id)`.
* `issue.link(relationship, issue)` — эквивалент `tracker.link_issues(issue.id, relationship, issue)`
  (возвращает `CreatedIssueLink`; вторым аргументом принимает строку, `Issue` или `FullIssue`).
* `issue.unlink(link_id)` — эквивалент `tracker.unlink_issues(issue.id, link_id)`.

## История изменений

```python
changes = await tracker.get_issue_changelog("WRITERS-1")
for change in changes:
    print(change.type, change.updated_at)
```

Сигнатура:

```python
async def get_issue_changelog(
    self,
    issue_id: str,
    *,
    id_: str | None = None,
    per_page: int | None = None,
    field: str | None = None,
    type_: str | None = None,
) -> list[Changelog]: ...
```

- `issue_id` — ID или ключ задачи.
- `id_` — курсор пагинации: вернуть изменения, идущие после изменения с данным ID
  (query-параметр `id`). Без него возвращается первая страница.
- `per_page` — количество записей на странице (по умолчанию 50).
- `field` — ID изменившегося поля задачи, например `"checklistItems"` или `"status"`, —
  отфильтровать историю только по нему.
- `type_` — ключ типа изменения (query-параметр `type`), например `"IssueWorkflow"`.

Источник: https://yandex.ru/support/tracker/ru/api/issues/get-changelog

Если изменений больше, чем `per_page` (по умолчанию — 50), нужно постранично дочитывать
историю, передавая `id_` последней полученной записи.

### iter_issue_changelog

Чтобы не управлять пагинацией вручную, используйте `iter_issue_changelog` — асинхронный
генератор поверх `get_issue_changelog`:

```python
async def iter_issue_changelog(
    self,
    issue_id: str,
    *,
    per_page: int | None = None,
    field: str | None = None,
    type_: str | None = None,
) -> AsyncIterator[Changelog]: ...
```

```python
async for change in tracker.iter_issue_changelog("WRITERS-1", field="status"):
    print(change.updated_by.display, change.fields)
```

Каждая следующая страница запрашивается с ID последнего изменения предыдущей; итерация
останавливается, как только очередная страница пуста или не продвигается дальше текущего
курсора (защита от зацикливания на случай, если сервер проигнорирует `id`).

!!! note "`per_page=1` отправляется как `perPage=2`"

    Курсор `id` включающий: изменение-курсор возвращается ещё раз в начале следующей
    страницы. Поэтому страница из одной записи могла бы содержать только сам курсор, и
    итерация остановилась бы после первой записи. Чтобы этого не происходило,
    `per_page=1` отправляется в API как `perPage=2`.

Задача, полученная через `get_issue`, тоже умеет отдавать свою историю без явного
`issue_id`:

```python
issue = await tracker.get_issue("WRITERS-1")
changes = await issue.get_changelog()
```

`issue.get_changelog(...)` — эквивалент `tracker.get_issue_changelog(issue.id, ...)`.
Итератора на `FullIssue` нет — для постраничного чтения истории задачи вызывайте
`tracker.iter_issue_changelog(issue.id, ...)` напрямую.

### Модель `Changelog`

| Поле                | Тип                                       | Описание                                |
|---------------------|--------------------------------------------|--------------------------------------------|
| `url`               | `str`                                      | Ссылка на запись изменения (`self`)       |
| `id`                | `str`                                      | ID изменения                              |
| `issue`             | `Issue`                                    | Задача, к которой относится изменение     |
| `updated_at`        | `datetime`                                 | Дата и время изменения                    |
| `updated_by`        | `User`                                     | Пользователь, внёсший изменение           |
| `type`              | `str`                                      | Тип изменения, например `"IssueWorkflow"` или `"IssueCommentAdded"` (полный список — в предупреждении ниже) |
| `transport`         | `str \| None`                              | Служебный параметр                        |
| `fields`            | `list[ChangelogField] \| None`             | Изменённые поля задачи                    |
| `comments`          | `ChangelogComments \| None`                | Комментарии, добавленные изменением       |
| `executed_triggers` | `list[ChangelogExecutedTrigger] \| None`   | Сработавшие триггеры                      |

`ChangelogField` (элемент `fields`):

| Поле    | Тип        | Описание                                                                     |
|---------|------------|---------------------------------------------------------------------------------|
| `field` | `FieldRef` | Ссылка на изменённое поле задачи                                              |
| `from_` | `Any`      | Значение поля до изменения (API-ключ `from`) — не типизировано специально: одиночное поле шлёт строку, многозначное — список объектов, объектное — `{self, id, key, display}`. `None`, если поле было пустым |
| `to`    | `Any`      | Значение поля после изменения, в том же формате, что `from_`                  |

`ChangelogComments` (поле `comments`) хранит только документированный блок `added` — список
`Ref` на добавленные комментарии, где `display` — текст комментария.

`ChangelogExecutedTrigger` (элемент `executed_triggers`) хранит `trigger` (`Ref`), `success`
(`bool | None`) и `message` (`str | None`) — что выполнил сработавший триггер.

!!! note "Список значений `type`"

    `type` — обычная строка, а не enum: набор значений принадлежит серверу и может
    расшириться. На момент написания документированы `IssueCreated`, `IssueUpdated`,
    `IssueMoved`, `IssueCloned`, `IssueCommentAdded`, `IssueCommentUpdated`,
    `IssueCommentRemoved`, `IssueWorklogAdded`, `IssueWorklogUpdated`,
    `IssueWorklogRemoved`, `IssueCommentReactionAdded`, `IssueCommentReactionRemoved`,
    `IssueVoteAdded`, `IssueVoteRemoved`, `IssueLinked`, `IssueLinkChanged`,
    `IssueUnlinked`, `RelatedIssueResolutionChanged`, `IssueAttachmentAdded`,
    `IssueAttachmentRemoved` и `IssueWorkflow`.

## Переходы по workflow (transitions)

Получить список переходов, доступных для задачи в её текущем статусе:

```python
transitions = await tracker.get_transitions("WRITERS-1")
```

Сигнатура:

```python
async def get_transitions(self, issue_id: str) -> Transitions: ...
```

`Transitions` — это словарь `{id перехода: Transition}`, который также можно перебирать как
список:

```python
for transition in transitions:
    print(transition.id, transition.display)

close = transitions.get("close")
```

Выполнить переход:

```python
result = await tracker.execute_transition(transitions["close"], resolution="fixed")
```

Сигнатура:

```python
async def execute_transition(
    self, transition: Transition, **kwargs
) -> list[Transition]: ...
```

- `transition` — объект `Transition`, полученный из `get_transitions` (метод отправляет
  запрос на `transition.url + "/_execute"`, поэтому нельзя просто передать строку с ID).
- `**kwargs` — дополнительные поля перехода, например `resolution` при переводе задачи в
  статус «Закрыт».
- Возвращает список переходов, доступных после выполнения текущего.

Объект `Transition` умеет выполнять себя сам — это удобный шорткат, эквивалентный вызову
`tracker.execute_transition(transition, ...)`:

```python
await transitions["close"].execute()
```

!!! note "Обратите внимание"

    `Transition.execute()` не принимает дополнительные аргументы (например, `resolution`) —
    если переход требует такие поля, вызывайте `tracker.execute_transition(transition, **kwargs)`
    напрямую.

## Кастомные модели задач

Все методы этой страницы принимают параметр `_type`, позволяющий вместо `FullIssue`
использовать вашу собственную модель — например, чтобы получить типизированный доступ к
пользовательским (локальным) полям очереди. Подробнее об этом — в разделе
[Работа с пользовательскими полями](custom_fields.md).
