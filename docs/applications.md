# Внешние приложения

Внешнее приложение (application) — это подключённая к Трекеру внешняя система, например
интеграция с Bitbucket или GitHub. Объекты такой системы (коммит, pull request и т. п.)
можно связать с задачей Трекера — такая связь называется *внешней ссылкой* (remote link).
`yatracker` позволяет получить список доступных внешних приложений, а также получать,
создавать и удалять внешние ссылки задачи.

!!! note "Обратите внимание"

    Как и все методы `YaTracker`, методы работы с внешними приложениями и внешними
    ссылками являются асинхронными. В примерах ниже вызовы показаны так, как будто мы уже
    находимся внутри корутины.

Официальная документация:

* [Список внешних приложений](https://yandex.ru/support/tracker/ru/api/issues/get-applications)
* [Список внешних ссылок задачи](https://yandex.ru/support/tracker/ru/api/issues/get-external-links)
* [Создание внешней ссылки](https://yandex.ru/support/tracker/ru/api/issues/add-external-link)
* [Удаление внешней ссылки](https://yandex.ru/support/tracker/ru/api/issues/delete-external-link)

## Список внешних приложений

### get_applications

```python
async def get_applications(self) -> list[Application]: ...
```

Возвращает список внешних приложений, с объектами которых можно создавать внешние ссылки.

```python
applications = await tracker.get_applications()

for application in applications:
    print(application.id, application.name)
```

`Application` — идентификатор (`id`), тип (`type`, совпадает с `id`) и название (`name`)
приложения. Значение `id` понадобится для `add_remote_link` в качестве `origin`.

Источник: <https://yandex.ru/support/tracker/ru/api/issues/get-applications>

## Внешние ссылки задачи

`RemoteLink` устроен так же, как `IssueLink` (см. [«Связи между задачами»](issues.md)), но
поле `object` в нём — это не задача, а `RemoteLinkObject`: объект внешнего приложения
(`id`, `key` и вложенный `application`). Свойство `name` работает точно так же, как у
`IssueLink`, — возвращает подпись связи (`type.inward` или `type.outward`) в зависимости от
`direction`.

### get_remote_links

```python
async def get_remote_links(self, issue_id: str) -> list[RemoteLink]: ...
```

Возвращает список внешних ссылок задачи.

```python
links = await tracker.get_remote_links("WRITERS-1")

for link in links:
    print(link.name, link.object.key, link.object.application.name)
```

1. `issue_id` — идентификатор или ключ задачи.

Источник: <https://yandex.ru/support/tracker/ru/api/issues/get-external-links>

### add_remote_link

```python
async def add_remote_link(
    self,
    issue_id: str,
    key: str,
    origin: str,
    relationship: str = "RELATES",
    *,
    backlink: bool | None = None,
) -> RemoteLink: ...
```

Создаёт внешнюю ссылку — связывает задачу с объектом внешнего приложения.

```python
link = await tracker.add_remote_link(
    issue_id="WRITERS-1",
    key="1357001000000001",
    origin="ru.yandex.bitbucket",
)
```

1. `issue_id` — идентификатор или ключ задачи.
2. `key` — ключ объекта во внешнем приложении.
3. `origin` — идентификатор внешнего приложения (`Application.id`, см. `get_applications`).
4. `relationship` — тип связи; документация API рекомендует использовать `"RELATES"`,
   поэтому это значение используется по умолчанию.
5. `backlink` — просить ли внешнее приложение создать зеркальную ссылку на своей стороне.
   По умолчанию `None`, и параметр не передаётся в запрос вовсе — поведение остаётся на
   усмотрение Трекера и внешнего приложения. Передайте `True` или `False`, чтобы явно
   запросить или отключить создание зеркальной ссылки.

Источник: <https://yandex.ru/support/tracker/ru/api/issues/add-external-link>

### delete_remote_link

```python
async def delete_remote_link(self, issue_id: str, link_id: str | int) -> bool: ...
```

Удаляет внешнюю ссылку задачи.

```python
await tracker.delete_remote_link("WRITERS-1", link.id)
```

1. `issue_id` — идентификатор или ключ задачи.
2. `link_id` — идентификатор внешней ссылки (`RemoteLink.id`).

Источник: <https://yandex.ru/support/tracker/ru/api/issues/delete-external-link>

## Типичный сценарий

Найти внешнее приложение по имени и связать с ним задачу:

```python
applications = await tracker.get_applications()
bitbucket = next(a for a in applications if a.name == "Bitbucket")

link = await tracker.add_remote_link(
    issue_id="WRITERS-1",
    key="1357001000000001",
    origin=bitbucket.id,
    backlink=True,
)
```
