# NetMap — UI Status
**Document:** docs/UI_STATUS.md
**Iteration:** 1
**Status:** Draft (implemented, not committed)

---

## 1. Что реализовано

Полноценный server-rendered Web UI (Flask + Jinja2 + Bootstrap 5 + HTMX + Cytoscape.js)
поверх существующего `/api/v1` без изменения backend-логики, моделей или схемы БД.

### Страницы

| Страница | URL | Описание |
|---|---|---|
| Dashboard | `/dashboard` (`/` редиректит сюда) | Счётчики (sites/networks/devices/active/ports/connections), недавно изменённые устройства, inactive-устройства, quick actions |
| Devices List | `/devices` | Таблица с поиском/фильтрами (network, type, status)/сортировкой/пагинацией — всё in-memory на UI-слое |
| Device Details | `/devices/<id>` | Вкладки Overview / Network (Interfaces+IP) / Ports (+Web Access) / Connections |
| Device Create/Edit | `/devices/new`, `/devices/<id>/edit` | Одна переиспользуемая HTMX-модалка |
| Networks List | `/networks` | Таблица с CRUD, счётчиком устройств |
| Network Details | `/networks/<id>` | Инфо о сети, кнопка Discover Network, список устройств сети |
| Discovery | `/discovery` | Список всех сетей с отдельной кнопкой Discover для каждой |
| Connections List | `/connections` | Таблица с CRUD, каскадный выбор портов по выбранному устройству |
| Topology | `/topology` | Cytoscape.js граф: devices = nodes, connections = edges, клик по узлу → Device Details |

### Технические решения

- **Внутренний API-клиент** (`app/web/api_client.py`) — вызывает `/api/v1/...` через `Flask.test_client()`
  внутри процесса, без HTTP round-trip и без новой зависимости (`requests` не добавлялся).
  Это удовлетворяет требованию "UI — только клиент REST API", не обращаясь к SQLAlchemy напрямую.
- **Vendored-библиотеки** (`app/static/vendor/`): Bootstrap 5.3.8, HTMX 1.9.12, Cytoscape.js,
  Bootstrap Icons — скачаны через `npm` и размещены локально, без обращения к CDN на рантайме
  (соответствует self-hosted/приватному характеру инфраструктуры проекта).
- **Dark theme по умолчанию** (`data-bs-theme="dark"` в `base.html`) — согласно `01_ARCHITECTURE.md`, §17.
- **HTMX используется точечно**: partial-обновления таблиц при фильтрации/сортировке/пагинации,
  модалки Create/Edit, Discovery-результат, каскадные `<select>` портов в форме Connection.
  Обычный JS — только там, где HTMX неудобен: удаление устройства со страницы Details (редирект
  после успеха), Cytoscape-граф (`static/js/topology.js`).

---

## 2. Используемые API-эндпоинты

Всё через существующие `/api/v1/*`, ничего не добавлено:

```
GET/POST/PUT/DELETE  /api/v1/devices, /api/v1/devices/<id>
GET/POST/PUT/DELETE  /api/v1/networks, /api/v1/networks/<id>
GET/POST/PUT/DELETE  /api/v1/connections, /api/v1/connections/<id>
GET                  /api/v1/interfaces
GET                  /api/v1/ip-addresses
GET                  /api/v1/ports
GET                  /api/v1/sites
POST                 /api/v1/networks/<id>/discover
```

Topology-граф (`static/js/topology.js`) обращается к `/api/v1/devices` и `/api/v1/connections`
напрямую из браузера (публичный API), без промежуточного UI-эндпоинта.

---

## 3. Backend gaps (обнаружено при исследовании, не исправлялось)

Список подтверждённых расхождений между `docs/03_API.md` и реальным поведением API.
Ничего из этого не было "тихо" реализовано новым API — обходные пути реализованы
на UI-слое и явно задокументированы здесь.

| Заявлено в docs/03_API.md | Реальность в коде | Обходной путь в UI |
|---|---|---|
| `GET /devices` поддерживает search/filter/sort/pagination (`?status=`, `?site=`, `?sort=` и т.д.) | Query-параметры полностью игнорируются, всегда возвращается вся коллекция | Фильтрация/сортировка/пагинация выполняется in-memory в `app/web/helpers.py` и `devices.py` после получения полного списка через API |
| `/api/v1/discovery/start`, `/stop`, `/status`, `/results` | Эти эндпоинты не существуют. Реальный discovery — только `POST /api/v1/networks/<id>/discover`, **синхронный** | UI не поллит статус — делает один блокирующий HTMX-запрос со спиннером (`hx-indicator`) и рендерит финальный результат из тела ответа |
| `GET /monitoring/*` | Не реализовано вообще — нет online/offline статуса устройств, только `is_active` | UI показывает только Active/Inactive (то, что реально есть в модели), не выдумывает "online/offline" |
| Стандартный конверт ответа `{"success": true, "data": {...}}` | API возвращает "голый" JSON (список или объект), ошибки как `{"error": "..."}` | `app/web/api_client.py` разбирает реальный формат, а не документированный |
| `GET /search?q=` (универсальный поиск) | Не реализовано | Поиск по устройствам в UI — локальный, только по полю `search` на странице Devices |
| Aggregate `/stats`-эндпоинт для Dashboard | Не существует | Dashboard считает счётчики на UI-слое из уже загруженных списков `/devices`, `/networks`, `/sites`, `/ports`, `/connections` — приемлемо при текущем масштабе (десятки-сотни записей), но не подойдёт при значительном росте без backend-агрегата |
| `Service` содержит port/protocol/version (как в исходном UI-ТЗ) | Модель `Service` — только `name` + `description`, привязка к порту через `Port.service_id` | Ports/Services в UI не смешивались; отдельной вкладки Services в Iteration 1 нет (не запрашивалась текущим ТЗ) |

---

## 4. Известные ограничения текущей итерации

- **Discovery — синхронный и блокирующий.** На большой подсети (например `/24`) запрос может
  занимать заметное время (`NetworkScanner` сканирует до 254 хостов × 10 портов, `ThreadPoolExecutor`
  с 50 воркерами). UI корректно показывает спиннер на время ожидания, но сам HTTP-запрос
  не прерываем — отмена не реализована ни на backend, ни на UI.
- **Sites не имеют собственной CRUD-страницы** — используются только как select-справочник
  в форме создания/редактирования Network. Явно не требовалось текущим ТЗ.
- **Filtering/sorting/pagination Devices — in-memory на каждый запрос**, т.е. при каждом
  обращении к `/devices/table` UI-слой заново получает **весь** список устройств через
  internal API client. Приемлемо для десятков-сотен записей, станет узким местом при
  значительном росте инвентаря без доработки API.
- **Топология не group-ит узлы по сети** — при одной активной сети (как сейчас) это не критично,
  но при множестве сетей граф может стать плотным. Group-by-network не реализован в Iteration 1.
- **Web Access URL зависит от primary IP устройства** (см. `api/v1/ports.py::get_web_url`) —
  если у устройства нет `IPAddress` с `is_primary=True`, кнопка "Open" не показывается, даже
  если `web_scheme` задан. Это поведение backend, UI просто корректно его отражает (кнопка
  скрывается, а не показывает битую ссылку).

---

## 5. Рекомендации на следующий этап

1. **Реализовать `?search=&status=&sort=&page=` на `GET /api/v1/devices`** — сейчас это
   единственная реальная проблема масштабируемости; при росте инвентаря in-memory-фильтрация
   на UI-слое станет заметно медленнее полного in-DB запроса.
2. **Сделать discovery асинхронным** (фоновая задача + `GET /discovery/status`) — на сетях
   крупнее `/28` синхронный HTTP-запрос рискует упереться в таймаут прокси/браузера.
   Текущий UI спроектирован так, чтобы легко перейти на polling, если появится статус-эндпоинт.
3. **Добавить CRUD для Sites** — простая, но нужная страница, если появятся сайты помимо
   текущего одного из seed-данных.
4. **Добавить `/api/v1/stats`** для Dashboard — уберёт необходимость тянуть 5 полных
   коллекций на каждый заход на Dashboard.
5. **Уточнить Service ↔ Port UX** — сейчас Service существует в модели, но никак не
   отображается и не редактируется в UI; стоит решить, нужна ли отдельная вкладка/страница
   до следующей итерации.

---

End of Document
