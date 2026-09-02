# Отсутствия

Отсутствие (gap) — это запись об отсутствии сотрудника: отпуск, больничный, командировка,
дежурство и так далее. Отсутствия отображаются на аватарках пользователей и на диаграмме
ресурсов в портфелях и проектах. `yatracker` предоставляет методы для создания, поиска и
удаления записей об отсутствии.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с отсутствиями являются асинхронными. В
    примерах ниже вызовы показаны так, как будто мы уже находимся внутри корутины.

    Все запросы этого раздела может выполнять только **администратор организации** —
    иначе API вернёт `403 Forbidden`, и библиотека выбросит `SufficientRightsError`
    (см. [«Обработка ошибок»](errors.md)).

Официальная документация:

* [Создать отсутствия](https://yandex.ru/support/tracker/ru/api/gaps/post-gaps)
* [Найти отсутствия](https://yandex.ru/support/tracker/ru/api/gaps/search-gaps)
* [Удалить отсутствия](https://yandex.ru/support/tracker/ru/api/gaps/delete-gaps)

## Тип отсутствия

`workflow` — один из `vacation` (отпуск), `paid_day_off` (оплачиваемый выходной),
`illness` (болезнь), `absence` (отсутствие, общий случай), `trip` (командировка),
`conference_trip` (поездка на конференцию), `conference` (конференция), `learning`
(обучение), `maternity` (декрет) или `duty` (дежурство). Библиотека не проверяет
значение на своей стороне — актуальный список отдаёт `GET /v3/gaps/workflows` (пока без
отдельного метода в `yatracker`).

## Создание

### create_gap

```python
async def create_gap(
    self,
    user: str | int,
    workflow: str,
    from_: datetime | str,
    to: datetime | str,
    *,
    id_: str | None = None,
    full_day: bool | None = None,
    work_in_absence: bool | None = None,
) -> Gap: ...
```

Создаёт одну запись об отсутствии.

```python
from datetime import datetime, timezone

gap = await tracker.create_gap(
    user="login",
    workflow="vacation",
    from_=datetime(2026, 7, 1, tzinfo=timezone.utc),
    to=datetime(2026, 7, 15, tzinfo=timezone.utc),
    full_day=True,
)
```

1. `user` — логин или идентификатор сотрудника.
2. `workflow` — тип отсутствия, см. раздел выше.
3. `from_` — начало отсутствия: timezone-aware `datetime` (библиотека сама
   отформатирует его в ISO 8601 с миллисекундами и смещением часового пояса) или
   готовая строка API. Должно быть меньше `to`. Отправляется как `from`.
4. `to` — конец отсутствия, тот же формат. Должно быть больше `from_`.
5. `id_` — идентификатор, который будет присвоен записи (не больше 128 символов).
   Если не передать, Трекер сгенерирует его сам. Отправляется как `id`; хвостовой
   подчёркиванием имя уводится от встроенной функции — так же, как в `create_field`,
   `create_local_field` и `create_workflow`.
6. `full_day` — признак полного дня (по умолчанию `False`).
7. `work_in_absence` — признак того, что сотрудник работает во время отсутствия (по
   умолчанию `False`).

Метод — тонкая обёртка над `create_gaps`: одна запись оборачивается в список и
отправляется тем же запросом. Если API не сохранил ни одной записи (например, она
оказалась устаревшей), метод бросает `ValueError`.

Чтобы создать сразу несколько записей, используйте `create_gaps`.

Источник: https://yandex.ru/support/tracker/ru/api/gaps/post-gaps

### create_gaps

```python
async def create_gaps(
    self,
    gaps: Sequence[Mapping[str, Any]],
) -> list[Gap]: ...
```

Создаёт до 100 записей об отсутствии одним запросом.

```python
gaps = await tracker.create_gaps(
    [
        {
            "user": "login1",
            "workflow": "vacation",
            "from_": datetime(2026, 7, 1, tzinfo=timezone.utc),
            "to": datetime(2026, 7, 15, tzinfo=timezone.utc),
            "full_day": True,
        },
        {
            "user": "login2",
            "workflow": "trip",
            "from_": "2026-07-10T00:00:00.000+0000",
            "to": "2026-07-20T00:00:00.000+0000",
        },
    ],
)
```

1. `gaps` — записи об отсутствии: любая коллекция (список, кортеж, генератор), не пустая
   и не больше 100 элементов. Одиночный словарь вместо коллекции бросает `TypeError`.
   Каждая запись — словарь с ключами
   `user`, `workflow`, `from_` (или `from`) и `to`, а также необязательными `id`,
   `full_day` и `work_in_absence`. Ключи приводятся к camelCase так же, как в остальной
   библиотеке (`full_day` → `fullDay`), а `from_`/`to` принимают и `datetime`, и готовую
   строку API.

Возвращает список **фактически сохранённых** записей: если какая-то запись оказалась
устаревшей (например, дублирующийся `id` или невалидный диапазон дат для конкретной
записи), она в ответ не попадёт.

!!! warning "Лимит в 100 записей"

    Если передать больше 100 записей, `create_gaps` бросит `ValueError`, не обращаясь
    к API — так же поступает и Трекер (`422`), но проверка на стороне библиотеки
    срабатывает раньше и с понятным сообщением. Пустая коллекция тоже бросает
    `ValueError`: запрос без записей бессмысленен.

Источник: https://yandex.ru/support/tracker/ru/api/gaps/post-gaps

## Поиск

### search_gaps

```python
async def search_gaps(
    self,
    users: Sequence[str | int],
    *,
    from_: datetime | str | None = None,
    to: datetime | str | None = None,
    per_page: int | None = None,
    page: int | None = None,
) -> GapsSearchResult: ...
```

Находит записи об отсутствии заданных сотрудников, пересекающиеся с указанным
временным окном.

```python
result = await tracker.search_gaps(
    ["login1", "login2"],
    from_=datetime(2026, 7, 1, tzinfo=timezone.utc),
    to=datetime(2026, 8, 31, 23, 59, 59, tzinfo=timezone.utc),
    per_page=20,
)

for user_gaps in result.user_gaps:
    print(user_gaps.user.login, [gap.workflow for gap in user_gaps.gaps])
```

1. `users` — логины или идентификаторы сотрудников: любая коллекция (список, множество,
   генератор), не пустая и не больше 100 элементов; иначе `ValueError`. Одиночный логин
   вместо коллекции (`users="login1"`) бросает `TypeError`: иначе строка была бы
   разобрана по символам.
2. `from_` — начало окна поиска. Текущий момент по умолчанию.
3. `to` — конец окна поиска. Должно быть строго больше `from_`.
4. `per_page` — количество **сотрудников** на странице (по умолчанию 50).
5. `page` — номер страницы (по умолчанию 1).

!!! warning "Пагинация постранична по сотрудникам, а не по записям"

    Результат группируется по сотруднику: в ответе ровно по одному элементу
    `UserGaps` на каждого запрошенного сотрудника, даже если у него нет отсутствий в
    указанном периоде (тогда `UserGaps.gaps` — пустой список). Параметры `per_page` и
    `page` относятся к числу сотрудников в `users`, а не к числу самих записей об
    отсутствии.

Источник: https://yandex.ru/support/tracker/ru/api/gaps/search-gaps

### iter_gaps

Чтобы не управлять пагинацией вручную, используйте `iter_gaps` — асинхронный генератор
поверх `search_gaps`:

```python
async def iter_gaps(
    self,
    users: Sequence[str | int],
    *,
    from_: datetime | str | None = None,
    to: datetime | str | None = None,
    per_page: int | None = None,
) -> AsyncIterator[UserGaps]: ...
```

```python
async for user_gaps in tracker.iter_gaps(["login1", "login2"], per_page=50):
    print(user_gaps.user.login, len(user_gaps.gaps))
```

1. `users` — логины или идентификаторы сотрудников, не больше 100. Одиночный логин
   вместо последовательности бросает `TypeError` — на первой итерации, как и любая
   другая ошибка в теле генератора.
2. `from_`, `to` — окно поиска, как в `search_gaps`.
3. `per_page` — количество сотрудников, запрашиваемых за один вызов `search_gaps`.

Генератор отдаёт по одному объекту `UserGaps` **на сотрудника** (не на запись об
отсутствии) — так же, как страницы `search_gaps`, включая сотрудников с пустым
`gaps`. Итерация останавливается, когда очередная страница пуста или Трекер сообщает,
что следующей страницы нет (`has_more=False`).

## Удаление

### delete_gap

```python
async def delete_gap(self, gap_id: str) -> bool: ...
```

Удаляет одну запись об отсутствии. Возвращает `True` при успехе.

```python
await tracker.delete_gap(gap.id)
```

1. `gap_id` — идентификатор записи об отсутствии.

Неизвестный идентификатор API игнорирует, а не отвечает ошибкой.

Источник: https://yandex.ru/support/tracker/ru/api/gaps/delete-gaps

### delete_gaps

```python
async def delete_gaps(self, gap_ids: Sequence[str]) -> bool: ...
```

Удаляет до 100 записей об отсутствии одним запросом. Возвращает `True` при успехе.

```python
await tracker.delete_gaps([gap1.id, gap2.id])
```

1. `gap_ids` — идентификаторы записей об отсутствии: любая коллекция (список, множество,
   генератор), не пустая и не больше 100 элементов, каждый идентификатор не длиннее
   128 символов. Отправляются одним query-параметром `gapIds`, через запятую.
   Одиночный идентификатор вместо коллекции (`gap_ids="6834..."`) бросает
   `TypeError`: иначе строка была бы разобрана по символам и лимит в 100 записей
   её бы пропустил.

Неизвестные идентификаторы API игнорирует, а не отвечает ошибкой.

!!! warning "Лимит в 100 записей"

    Если передать больше 100 идентификаторов — или ни одного, — `delete_gaps` бросит
    `ValueError`, не обращаясь к API.

Источник: https://yandex.ru/support/tracker/ru/api/gaps/delete-gaps

## Модели

### Gap

| Поле | Тип | Описание |
|---|---|---|
| `id` | `str` | Идентификатор записи об отсутствии. |
| `workflow` | `str` | Тип отсутствия, см. раздел «Тип отсутствия» выше. |
| `from_` | `datetime` | Начало отсутствия (JSON-ключ `from`). |
| `to` | `datetime` | Конец отсутствия. |
| `full_day` | `bool` | Признак полного дня. |
| `work_in_absence` | `bool` | Признак работы во время отсутствия. |
| `user` | `FullUser \| None` | Сотрудник, которому принадлежит запись. Возвращается `create_gap`/`create_gaps`; `search_gaps`/`iter_gaps` вместо этого группируют записи по сотруднику через `UserGaps` и это поле не заполняют. |

### UserGaps

| Поле | Тип | Описание |
|---|---|---|
| `user` | `FullUser` | Сотрудник. |
| `gaps` | `list[Gap]` | Записи об отсутствии сотрудника в запрошенном периоде. Пустой список, если совпадений нет. |

### GapsSearchResult

Ответ `search_gaps` — одна страница результата.

| Поле | Тип | Описание |
|---|---|---|
| `user_gaps` | `list[UserGaps]` | По одному элементу на каждого запрошенного сотрудника. |
| `has_more` | `bool` | Есть ли следующая страница. |

### GapsResult

Ответ `create_gaps` — техническая модель-обёртка, наружу не всплывает: метод сразу
возвращает `GapsResult.gaps`.

| Поле | Тип | Описание |
|---|---|---|
| `gaps` | `list[Gap]` | Фактически сохранённые записи (устаревшие в ответ не попадают). |

## Типичный сценарий

Создать отпуск и командировку одним запросом, затем перечислить все отсутствия
команды за квартал через `iter_gaps`:

```python
from datetime import datetime, timezone

await tracker.create_gaps(
    [
        {
            "user": "login1",
            "workflow": "vacation",
            "from_": datetime(2026, 7, 1, tzinfo=timezone.utc),
            "to": datetime(2026, 7, 15, tzinfo=timezone.utc),
            "full_day": True,
        },
        {
            "user": "login2",
            "workflow": "trip",
            "from_": datetime(2026, 7, 10, tzinfo=timezone.utc),
            "to": datetime(2026, 7, 20, tzinfo=timezone.utc),
        },
    ],
)

async for user_gaps in tracker.iter_gaps(
    ["login1", "login2"],
    from_=datetime(2026, 7, 1, tzinfo=timezone.utc),
    to=datetime(2026, 9, 30, tzinfo=timezone.utc),
):
    for gap in user_gaps.gaps:
        print(user_gaps.user.login, gap.workflow, gap.from_, gap.to)
```
