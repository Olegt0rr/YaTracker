# Обработка ошибок

Все ошибки, которые библиотека формирует сама, живут в модуле
`yatracker.exceptions` и наследуются от общего базового класса.

```python
from yatracker.exceptions import (
    AlreadyExistsError,
    NotAuthorizedError,
    ObjectNotFoundError,
    PreconditionFailedError,
    PreconditionRequiredError,
    SufficientRightsError,
    YaTrackerError,
)
```

!!! note "Импорт"

    Исключения не реэкспортируются из корня пакета — импортируйте их
    именно из `yatracker.exceptions`.

## Иерархия

```text
Exception
└── YaTrackerError            — базовый класс, а также любой неопознанный ответ
    ├── NotAuthorizedError    — 401 Unauthorized
    ├── SufficientRightsError — 403 Forbidden
    ├── ObjectNotFoundError   — 404 Not Found
    ├── AlreadyExistsError    — 409 Conflict
    ├── PreconditionFailedError — 412 Precondition Failed
    └── PreconditionRequiredError — 428 Precondition Required
```

Проверка выполняется в `BaseClient._check_status()` сразу после получения
ответа. Логика простая:

* статус меньше `300` — ошибки нет, тело ответа отдаётся дальше на разбор;
* `401`, `403`, `404`, `409`, `412`, `428` — соответствующее специализированное исключение;
* **любой другой** статус от `300` и выше — базовый `YaTrackerError`,
  в текст которого попадает тело ответа, декодированное как UTF-8.

Это значит, что `400 Bad Request`, `422`, `429 Too Many Requests` и все `5xx`
приходят как «голый» `YaTrackerError` — отличить их можно только по тексту.

!!! warning "Исключения не содержат статус-код"

    Специализированные исключения не принимают аргументов: у каждого свой
    фиксированный текст, а HTTP-статус и тело ответа в объект не попадают.
    Если вам нужен статус — ориентируйтесь на класс исключения.

## Когда что возникает

### `NotAuthorizedError` — 401

Токен не передан, просрочен, отозван или не подходит к указанной организации.
Также возникает, если организация в заголовке не та, к которой привязан токен.

```python
from yatracker.exceptions import NotAuthorizedError

try:
    issue = await tracker.get_issue("WRITERS-42")
except NotAuthorizedError:
    # обновить IAM-токен и повторить запрос
    ...
```

!!! tip

    IAM-токен живёт недолго — его нужно периодически обновлять.
    Пересоздайте клиент с новым `iam_token` (не забыв закрыть старый)
    или подставьте свежий заголовок `Authorization` через собственный
    `BaseClient`.

### `SufficientRightsError` — 403

У пользователя, которому принадлежит токен, недостаточно прав на действие.
Права в API ровно те же, что и в веб-интерфейсе Трекера: если действие
недоступно в интерфейсе, через API оно тоже не пройдёт.

!!! note "О названии"

    Имя класса читается двусмысленно, но означает именно **недостаток** прав.
    Оно сохранено ради обратной совместимости.

### `ObjectNotFoundError` — 404

Объекта не существует, либо указан неверный идентификатор или ключ.
Самый частый случай — опечатка в ключе задачи или очереди, а также
обращение к удалённой сущности.

```python
from yatracker.exceptions import ObjectNotFoundError


async def get_issue_or_none(tracker, key: str):
    try:
        return await tracker.get_issue(key)
    except ObjectNotFoundError:
        return None
```

### `AlreadyExistsError` — 409

Объект с таким значением уникального параметра уже существует.
Практически всегда это `create_issue(..., unique=...)`: Трекер использует
`unique` как ключ идемпотентности и не даёт создать дубль.

Тот же код `409` Трекер возвращает при конфликте версий — когда в `edit_issue`
или `update_component` передана устаревшая `version`. Библиотека и в этом случае
выбрасывает `AlreadyExistsError`, несмотря на текст сообщения про «существующий
объект»: перечитайте объект и повторите запрос с актуальной версией.

```python
from yatracker.exceptions import AlreadyExistsError

try:
    issue = await tracker.create_issue(
        "Заявка из внешней системы",
        "HELP",
        unique="external-id-42",
    )
except AlreadyExistsError:
    # задача уже была создана раньше — просто продолжаем
    ...
```

### `PreconditionFailedError` — 412

Версия, переданная в заголовке `If-Match`, устарела: объект успели изменить параллельно.
Возникает у колонок досок (`create_board_column`, `update_board_column`,
`delete_board_column` — там передаётся версия **доски**), у спринтов
(`update_sprint`, `start_sprint`, `archive_sprint`) и у
`update_board(version=...)`, если версия указана (для этого запроса заголовок `If-Match`
в справочнике не описан, но ответ `412` — описан). Подробнее про версии и `If-Match`
смотрите в разделе [«Доски и спринты»](boards.md).

```python
from yatracker.exceptions import PreconditionFailedError

try:
    sprint = await tracker.start_sprint(sprint.id, sprint.version)
except PreconditionFailedError:
    # версия устарела — перечитываем спринт и повторяем с актуальной версией
    sprint = await tracker.get_sprint(sprint.id)
    sprint = await tracker.start_sprint(sprint.id, sprint.version)
```

### `PreconditionRequiredError` — 428

Запрос требует версию объекта в заголовке `If-Match`, а она не передана. В справочнике
этот ответ описан у запросов на изменение доски и создание/изменение колонки; в библиотеке
до него можно дойти только через `update_board` без параметра `version` — остальные методы
с `If-Match` принимают версию обязательно. Перечитайте объект и повторите запрос
с `version=obj.version`.

### `YaTrackerError` — всё остальное

Базовый класс. Ловите его, если хотите отреагировать на любую ошибку API
одинаково, либо когда статус не входит в четвёрку выше:

```python
from yatracker.exceptions import YaTrackerError

try:
    issues = await tracker.find_issues(query="Queue: WRITERS")
except YaTrackerError as e:
    logger.error("Трекер вернул ошибку: %s", e)
    raise
```

Типичные ситуации:

| Что произошло | Статус | Что делать |
|---|---|---|
| Некорректный запрос или фильтр | `400` | Проверьте `query`, `filter_`, набор параметров |
| Слишком много запросов | `429` | Притормозить и повторить с задержкой |
| Сбой на стороне Трекера | `5xx` | Повторить позже |

Отдельный случай `400` — попытка использовать scroll-пагинацию вместе
с формами поиска `keys` или `queue`: API такое сочетание запрещает.
Для обхода задач пачками используйте `iter_issues()`, который сам
складывает `queue` в `filter`.

## Ошибки до запроса

Часть проверок выполняется ещё в конструкторе, до любого обращения к сети.
Эти ошибки — стандартные python-исключения, а не наследники `YaTrackerError`.

### `RuntimeError`

Не передан идентификатор организации или токен:

```python
YaTracker()  # RuntimeError
YaTracker(org_id="org")  # RuntimeError — нет токена
```

Сообщение подсказывает допустимые комбинации: `org_id` или `cloud_org_id`
вместе с `token` или `iam_token`, либо готовый `BaseClient` с уже
настроенными заголовками.

### `ValueError`

Передана взаимоисключающая пара параметров:

```python
YaTracker(org_id="org", cloud_org_id="cloud", token="t")  # ValueError
YaTracker(org_id="org", token="t", iam_token="iam")  # ValueError
```

API запрещает отправлять `X-Org-ID` и `X-Cloud-Org-ID` одновременно,
а схемы авторизации `OAuth` и `Bearer` тоже не совмещаются.

`ValueError` также бросает `get_worklog()`, если задана только одна граница
диапазона `created_at_from` / `created_at_to` — нужны обе или ни одной.

## Ошибки разбора ответа

Ответ Трекера превращается в модель через `pydantic`. Если структура ответа
не совпала с моделью, вы получите `pydantic.ValidationError` — это не ошибка
API и не наследник `YaTrackerError`.

Самая частая причина — проекция полей. Параметр `fields` заставляет Трекер
вернуть только перечисленные поля, а модель `FullIssue` требует полный набор:

```python
from pydantic import ValidationError

try:
    # FullIssue ждёт status, queue, priority и другие обязательные поля
    issues = await tracker.find_issues(query="Queue: WRITERS", fields="key,summary")
except ValidationError:
    ...
```

Правильное решение — передать через `_type` модель, у которой обязательными
являются только запрошенные поля:

```python
from yatracker.types import Base


class IssueBrief(Base):
    key: str
    summary: str


issues = await tracker.find_issues(
    query="Queue: WRITERS",
    _type=IssueBrief,  # (1)
    fields="key,summary",
)
```

1. Подробнее о собственных моделях — в разделе
   [Работа с пользовательскими полями](custom_fields.md).

!!! note "Замечание для mypy"

    Параметр `_type` объявлен с ограничением `bound=FullIssue`, поэтому на
    модель, унаследованную напрямую от `Base`, mypy выдаст предупреждение.
    В рантайме такой вызов работает: разбор идёт через `pydantic.TypeAdapter`,
    которому подходит любая модель. Если предупреждение мешает, наследуйте
    свою модель от `FullIssue`, сделав ненужные поля необязательными.

## Сетевые ошибки

Библиотека не оборачивает исключения транспорта: всё, что бросает `aiohttp`
(`aiohttp.ClientError` и его наследники), а также `asyncio.TimeoutError`,
поднимается наружу как есть.

!!! warning "Таймаута по умолчанию нет"

    Клиент создаётся с `ClientTimeout(total=0)`, то есть без ограничения
    по времени. Конструктор `YaTracker` собственного параметра для таймаута
    не имеет — задайте его, собрав клиент вручную:

    ```python
    from aiohttp import ClientTimeout

    from yatracker import YaTracker
    from yatracker.tracker.client import AIOHTTPClient

    client = AIOHTTPClient(
        org_id=...,
        token=...,
        timeout=ClientTimeout(total=30),
    )
    tracker = YaTracker(client=client)
    ```

Пример устойчивой обёртки с повтором:

```python
import asyncio

from aiohttp import ClientError

from yatracker.exceptions import YaTrackerError


async def with_retry(coro_factory, attempts: int = 3, delay: float = 1.0):
    for attempt in range(1, attempts + 1):
        try:
            return await coro_factory()
        except (ClientError, asyncio.TimeoutError, YaTrackerError):
            if attempt == attempts:
                raise
            await asyncio.sleep(delay * attempt)
    return None
```

!!! note "Не повторяйте всё подряд"

    `NotAuthorizedError`, `SufficientRightsError`, `ObjectNotFoundError`,
    `AlreadyExistsError`, `PreconditionFailedError` и `PreconditionRequiredError`
    от повтора не исправятся — их лучше исключить из логики ретраев и обработать
    отдельно. Для `PreconditionFailedError` «обработать» означает перечитать объект
    и повторить запрос с его актуальной версией, а не просто повторить тот же
    запрос ещё раз.

## Логирование

Перед тем как бросить исключение, клиент пишет предупреждение в стандартный
`logging` для всех ответов со статусом `400` и выше:

```text
WARNING yatracker.tracker.client Error! Status: 404. Body: {"errors":{},...}
```

Тело ответа видно только в логе — в текст специализированных исключений
оно не попадает. Чтобы эти записи дошли до вывода, настройте логирование:

```python
import logging

logging.basicConfig(level=logging.WARNING)
```

Все логгеры библиотеки начинаются с `yatracker.`, поэтому её вывод можно
настроить отдельно от остального приложения:

```python
logging.getLogger("yatracker").setLevel(logging.DEBUG)
```
