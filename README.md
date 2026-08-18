# NetMap

**Network Infrastructure Discovery & Inventory Platform**

> NetMap — веб-платформа для инвентаризации сетевой инфраструктуры, обнаружения устройств, управления сетями и устройствами, фиксации соединений и визуализации топологии.

**Status:** Active Development
**Version:** 0.3.0-dev
**Iteration:** 3 Complete — Monitoring Engine
**License:** MIT

## 1. Назначение

NetMap предназначен для ведения актуальной карты сетевой инфраструктуры и быстрого доступа к информации об устройствах.

Основные задачи:

- инвентаризация сетей и устройств;
- обнаружение устройств в подсетях (TCP port scanning);
- хранение интерфейсов, IP-адресов и сервисов/портов;
- ручное редактирование имён и описаний;
- фиксация соединений между устройствами;
- автоматическое распознавание стандартных сервисов;
- быстрый доступ к Web-сервисам (кнопки Open);
- визуализация топологии;
- API-side фильтрация, сортировка и пагинация;
- периодический мониторинг доступности устройств (ICMP ping + TCP fallback);
- массовый импорт портов из внешних источников;
- подготовка основы для инфраструктурных интеграций.

Архитектура рассчитана на несколько независимых площадок (Site) и дальнейшее масштабирование.

## 2. Возможности

### Dashboard

`/dashboard` — счётчики Sites, Networks, Devices, Ports и Connections, недавно изменённые и inactive-устройства, быстрые действия.

`/` перенаправляет на Dashboard.

### Devices

`/devices`

- список устройств с карточками (3 колонки на desktop);
- поиск, фильтрация, сортировка и пагинация (API-side);
- Add / Edit / Delete;
- Active / Inactive;
- полный список Services на каждой карточке;
- кнопки Open для быстрого доступа к Web-сервисам.

`/devices/<id>` — Details с Overview, Network, Interfaces/IP, Services/Web Access и Connections.

### Networks

`/networks`

- Add / Edit / Delete;
- Active / Inactive;
- количество устройств.

`/networks/<id>` — Details сети, устройства и запуск Discovery.

### Discovery

`/discovery` и `/networks/<id>` позволяют запускать обнаружение устройств в сети.

**Метод:** TCP port scanning (порты 22, 23, 53, 80, 81, 443, 445, 554, 8080, 8443)

**Возможности:**
- Автоматическое создание/обновление устройств
- Резолвинг hostname
- Обнаружение открытых портов
- Создание интерфейсов и IP-адресов
- Пометка отсутствующих устройств как Inactive

**Статус:** Синхронный (запрос выполняется до получения результата).

### Connections

`/connections` — CRUD соединений и каскадный выбор портов по выбранному устройству.

### Topology

`/topology` — Cytoscape.js граф, где устройства являются nodes, а connections — edges. Клик по узлу открывает Device Details.

### Monitoring

**Статус:** Реализовано

**Компоненты:**
- `MonitoringService` — проверка доступности устройств
- `APScheduler` — фоновый планировщик задач
- Периодические проверки каждые 5 минут (настраивается через `MONITORING_INTERVAL_MINUTES`)

**Метод:** ICMP ping с TCP fallback к известным открытым портам устройства

**Возможности:**
- Автоматическое обновление статуса `is_active` для устройств
- Проверка устройств с известными IP-адресами
- Fallback к стандартным портам при отсутствии записей об открытых портах
- Может быть отключён через `MONITORING_ENABLED=false`

### Port Import

**Статус:** Реализовано (не закоммичено)

**Endpoint:** `POST /api/v1/imports/ports`

**Возможности:**
- Массовый импорт портов из JSON
- Разрешение устройств по ID, IP-адресу, имени или hostname
- Автоматическое создание/обновление портов и сервисов
- Предотвращение дублирования
- Автоопределение `web_scheme` для известных портов
- Маркировка импортированных портов (`description='import:auto'`)

## 3. Архитектура

```text
                    Web UI
                      |
                      v
                 Web Routes
                      |
                      v
                  REST API
                      |
                      v
              Application Services
                      |
             +--------+--------+
             |                 |
             v                 v
        Discovery          Other Services
             |                 |
             +--------+--------+
                      |
                      v
                 SQLAlchemy
                      |
               +------+------+
               |             |
               v             v
             SQLite      PostgreSQL
```

Web UI не должен обращаться к БД напрямую. Основной интерфейс приложения — `/api/v1`.

## 4. Технологический стек

| Компонент | Технология |
|---|---|
| Backend | Flask |
| Templates | Jinja2 |
| UI | Bootstrap 5 |
| Dynamic UI | HTMX |
| Icons | Bootstrap Icons |
| Topology | Cytoscape.js |
| ORM | SQLAlchemy |
| Migrations | Flask-Migrate / Alembic |
| Development DB | SQLite |
| Target DB | PostgreSQL |
| Production server | Gunicorn |
| Scheduler | APScheduler |

Frontend-библиотеки размещены локально в `/backend/app/static/vendor/`.

## 5. Модель данных

```text
Site
 |
 +-- Network
       |
       +-- Device
             |
             +-- Interface -- IPAddress
             |
             +-- Port -- Service

Device ---- Connection ---- Device
```

Основные модели проекта:

- **Site** — физическая площадка (Home, Office);
- **Network** — подсеть (192.168.x.x/24);
- **Device** — любое сетевое устройство;
- **Interface** — сетевой интерфейс (eth0, ens18);
- **IPAddress** — IPv4/IPv6 адрес;
- **Port** — TCP/UDP порт с опциональной привязкой к Service;
- **Service** — именованный сервис (SSH, HTTP, DNS и т.д.);
- **Connection** — связь между двумя устройствами.

**Device Types:** router, switch, server, nas, camera, printer, ap, esp32, pc, laptop, phone, **lxc**, **vm**, **zigbee**, unknown, other.

## 6. Первоначальные сети

Архитектура первоначально рассчитана на две площадки:

### Home

```text
192.168.88.0/24
```

Основные устройства: MikroTik, Proxmox.

### Office

```text
192.168.80.0/24
```

Основные устройства: MikroTik, Proxmox.

Количество Site не ограничено архитектурой.

## 7. Discovery

**Текущая реализация:** TCP port scanning через `NetworkScanner` и синхронизация через `DiscoveryService`.

**Endpoint:**
```http
POST /api/v1/networks/<network_id>/discover
```

**Порты сканирования:** 22, 23, 53, 80, 81, 443, 445, 554, 8080, 8443

**Функции:**
- Обнаружение хостов в подсети
- Резолвинг hostname (DNS reverse lookup)
- Определение открытых портов
- Создание/обновление Device записей
- Создание Interface и IPAddress
- Пометка отсутствующих устройств как Inactive
- Синхронизация портов

**Архитектура:**
- `NetworkScanner` — TCP-сканирование (не пишет в БД)
- `DiscoveryService` — синхронизация результатов с БД
- Результаты Discovery обрабатываются сервисным слоем

**Планируемые интеграции:** SNMP, LLDP, CDP, MikroTik, Proxmox, Docker, Home Assistant, VMware, Kubernetes, UniFi.

## 8. REST API

Base path:

```text
/api/v1
```

Основные ресурсы:

```text
/api/v1/sites
/api/v1/networks
/api/v1/devices
/api/v1/interfaces
/api/v1/ip-addresses
/api/v1/ports
/api/v1/services
/api/v1/connections
/api/v1/imports
```

CRUD-ресурсы используют GET/POST/PUT/DELETE.

**Devices endpoint поддерживает:**
- `?search=<term>` — поиск по name/hostname/IP
- `?network_id=<id>` — фильтр по сети
- `?device_type=<type>` — фильтр по типу устройства
- `?is_active=<true|false>` — фильтр по статусу
- `?sort=<field>` — сортировка (name, hostname, device_type, is_active, created_at, updated_at)
- `?page=<n>` — номер страницы
- `?per_page=<n>` — количество на странице (default: 50)

**Imports endpoint:**
- `POST /api/v1/imports/ports` — массовый импорт портов (реализовано, не закоммичено)

Подробная документация: `/docs/03_API.md`.

> Важно: `/docs/03_API.md` содержит целевую спецификацию, а часть возможностей ещё не полностью реализована в текущем API. Фактическое поведение API должно считаться источником истины при разработке UI.

## 9. HTMX и UI

HTMX используется для частичного обновления таблиц, фильтрации/сортировки/пагинации, Create/Edit modal, Discovery result и каскадных select.

Cytoscape и отдельные специальные действия реализованы обычным JavaScript.

### Edit в модальном окне

Формы Edit должны работать как со страниц List, так и со страниц Details. Для этого форма использует общий контейнер:

```text
#nm-modal-content
```

После успешного сохранения список на List может обновляться через `hx-swap-oob`. На Details, где таблицы нет, UI обновляет данные страницы через reload.

Это исправляет проблему, когда `hx-target` указывал на `#networks-table-wrapper` или `#devices-table-wrapper`, отсутствующий на Details.

## 10. Запуск разработки

```bash
cd /path/to/NetMap/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5001
```

Альтернативно:

```bash
python run.py
```

По умолчанию приложение доступно на:

```text
http://<server-ip>:5001
```

Например:

```text
http://192.168.80.16:5001
```

## 11. Конфигурация

Файл:

```text
/backend/config.py
```

Поддерживаемые переменные окружения:

```text
SECRET_KEY                      — секретный ключ Flask (default: "netmap-dev")
DATABASE_URL                    — URL базы данных (default: "sqlite:///netmap.db")
MONITORING_ENABLED              — включить мониторинг (default: true)
MONITORING_INTERVAL_MINUTES     — интервал проверки устройств в минутах (default: 5)
```

По умолчанию используется SQLite:

```text
sqlite:///netmap.db
```

## 12. Database и migrations

Миграции:

```text
/backend/migrations/
```

Локальная БД разработки:

```text
/backend/instance/netmap.db
```

Изменения схемы должны выполняться через migrations, а не ручным редактированием таблиц.

## 13. Структура проекта

```text
/
├── backend/
│   ├── app/
│   │   ├── api/v1/
│   │   ├── models/
│   │   ├── repositories/
│   │   ├── services/
│   │   ├── web/
│   │   ├── templates/
│   │   └── static/
│   ├── migrations/
│   ├── config.py
│   ├── extensions.py
│   ├── requirements.txt
│   └── run.py
├── docs/
├── frontend/
├── .ai/
├── CONTRIBUTING_AI.md
├── LICENSE
└── README.md
```

## 14. Документация

| Файл | Назначение |
|---|---|
| `/docs/01_ARCHITECTURE.md` | Архитектура |
| `/docs/02_DATABASE.md` | Модель БД |
| `/docs/03_API.md` | REST API |
| `/docs/04_CODING_STANDARDS.md` | Стандарты разработки |
| `/docs/05_DEVELOPMENT_TASK_001.md` | Foundation task |
| `/docs/99_AI_RULES.md` | Правила AI |
| `/docs/AI_WORKFLOW.md` | AI workflow |
| `/docs/PROJECT_STANDARDS.md` | Стандарты проекта |
| `/docs/UI_STATUS.md` | Состояние UI |
| `/CONTRIBUTING_AI.md` | Правила для AI-агентов |

## 15. Проверка проекта

Минимальная проверка Python:

```bash
python -m compileall -q backend/app
```

После изменений UI рекомендуется пройти следующие сценарии.

### Networks

```text
/networks
/networks/<id>
```

Проверить Add, Edit, Delete, Active/Inactive, Cancel и повторный Edit.

### Devices

```text
/devices
/devices/<id>
```

Проверить Add, Edit, Delete, Active/Inactive, фильтрацию, сортировку, пагинацию и Details.

### Connections

```text
/connections
```

Проверить Add, Edit, Delete и каскадный выбор портов.

### Discovery

```text
/discovery
/networks/<id>
```

Проверить запуск, результат, ошибку и повторный запуск.

### Topology

```text
/topology
```

Проверить загрузку nodes/edges и переход в Device Details.

## 16. Известные ограничения



### Sites

Отдельной CRUD-страницы Sites пока нет; Sites используются как справочник.

### Dashboard

Dashboard получает несколько коллекций API вместо отдельного aggregate `/api/v1/stats`.

### Async Discovery

Discovery синхронный и может занимать заметное время на больших подсетях. Следующий этап — фоновые задачи с API статуса и polling.

## 17. Roadmap

### ✅ Iteration 1 — Foundation (Complete)

- [x] Flask application
- [x] SQLAlchemy + Flask-Migrate
- [x] SQLite (PostgreSQL-ready)
- [x] Database migrations
- [x] REST API (`/api/v1`)
- [x] Dashboard with statistics
- [x] Networks CRUD
- [x] Devices CRUD
- [x] Connections CRUD
- [x] Network Discovery (TCP scanning)
- [x] Topology visualization (Cytoscape.js)
- [x] HTMX dynamic UI
- [x] Bootstrap 5 UI

### ✅ Iteration 2 — Interfaces/IP/Ports/Connections (Complete)

- [x] Interface model
- [x] IPAddress model (normalized)
- [x] Port model with Service associations
- [x] Service model
- [x] Connection model
- [x] Cascading relationships
- [x] Discovery synchronization
- [x] Device Details: Interfaces/IP section
- [x] Device Details: Services section
- [x] Device Details: Connections section
- [x] Web UI for all new models

### ✅ Services & API Enhancements (Complete)

- [x] API-side filtering/sorting/pagination для Devices
- [x] Standard service names and detection
- [x] Web URL generation for services
- [x] Quick web access (Open buttons)
- [x] Services terminology in UI
- [x] Device Types: LXC, VM, ZigBee
- [x] Device cards UI polish (3-column grid, full Services list)

### ✅ Iteration 3 — Monitoring Engine (Complete)

- [x] MonitoringService with ICMP ping + TCP fallback
- [x] APScheduler integration (background periodic tasks)
- [x] Automatic device availability checks (every 5 minutes)
- [x] Auto-update Device.is_active based on reachability
- [x] Configurable monitoring interval and enable/disable
- [x] Port Import API (implemented, not committed)

### 📋 Next Steps

1. **Async Discovery** — Background tasks with status API and progress tracking
2. **Dashboard Stats API** — `/api/v1/stats` aggregate endpoint
3. **Sites CRUD UI** — Dedicated page for Sites management
4. **Service Detection** — Enhanced automatic service identification
5. **Topology Enhancements** — Layouts, filters, export
6. **Infrastructure Integrations** — MikroTik, Proxmox, Docker APIs
7. **PostgreSQL Deployment** — Production database setup
8. **Multi-user & RBAC** — Authentication and authorization
9. **Monitoring History** — Store availability checks history
10. **Alert System** — Notifications on device status changes

### 🔮 Future (v2.0+)

- Asset Management
- Rack Management
- SNMP/LLDP/CDP support
- Syslog server
- Alert system
- Mobile app
- Plugin marketplace

## 18. AI-assisted development

NetMap предусматривает работу с AI-агентами.

AI должен:

- изучать реальные исходники перед изменениями;
- не предполагать наличие файлов;
- не менять архитектуру без необходимости;
- сохранять совместимость API;
- запускать доступные проверки после изменений;
- документировать изменения.

Основные правила:

```text
/CONTRIBUTING_AI.md
/docs/99_AI_RULES.md
/docs/AI_WORKFLOW.md
```

Веб-чаты внешних AI-моделей не получают доступ к локальному репозиторию автоматически. Анализ конкретного файла без предоставленных исходников является предположением, а не фактической проверкой.

## 19. Принципы разработки

- UI не обращается к БД напрямую.
- Бизнес-логика не должна дублироваться в Web UI.
- Discovery отделён от хранения данных.
- Не следует выдумывать состояния, которых нет в backend.
- Изменения API должны быть явными и документированными.
- Перед изменением существующего файла необходимо подтвердить его фактическое наличие и содержимое.
- Не следует менять структуру проекта без согласования.

## 20. License

MIT. См. `/LICENSE`.

## 21. Project status

NetMap находится в активной разработке. Текущая версия (**0.3.0-dev**) предоставляет полнофункциональный inventory/discovery/monitoring Web UI для сетевой инфраструктуры:

```text
Dashboard
   │
   ├── Networks ── Discovery (TCP scanning)
   │
   ├── Devices (41 устройств)
   │      ├── Interfaces
   │      ├── IP addresses (71 IP)
   │      ├── Services/Ports (71 портов, 8 сервисов)
   │      └── Connections
   │
   ├── Connections (device-to-device)
   │
   └── Topology (Cytoscape graph)
```

**Завершено:**
- ✅ Iteration 1: Foundation
- ✅ Iteration 2: Interfaces/IP/Ports/Connections
- ✅ Services & API Enhancements
- ✅ Iteration 3: Monitoring Engine

**Следующая крупная цель:** Async Discovery — фоновые задачи с API статуса и прогрессом сканирования.

**Статус git:**
- Branch: `main` (опережает `origin/main` на 2 коммита)
- Uncommitted: 8 modified files, 3 untracked files (Device Types, Services UI, Port Import API)

**Подробнее:** См. `/PROJECT_STATUS.md` и `/CHANGELOG.md`.
