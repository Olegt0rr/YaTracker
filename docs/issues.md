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

Если нужно управлять scroll-сессией вручную (например, встроить в свою пагинацию), можно
по-прежнему пользоваться `find_issues`, передавая `scroll_id` явно.

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

`IssueLink` описывает связь одной задачи с другой:

- `type` — тип связи (`LinkType`, содержит подписи `inward`/`outward`);
- `direction` — направление связи, `LinkDirection.INWARD` или `LinkDirection.OUTWARD`;
- `object` — связанная задача (`Issue`);
- `status` — текущий статус связанной задачи;
- `name` — свойство-хелпер: возвращает подпись связи (`type.inward` или `type.outward` в
  зависимости от `direction`) — удобно для вывода вроде «зависит от», «блокирует» и т. п.

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
