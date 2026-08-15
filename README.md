# NetMap

**Network Infrastructure Discovery & Inventory Platform**

> NetMap — веб-платформа для инвентаризации сетевой инфраструктуры, обнаружения устройств, управления сетями и устройствами, фиксации соединений и визуализации топологии.

**Status:** Under Development
**Iteration:** 1 — Foundation / UI
**License:** MIT

## 1. Назначение

NetMap предназначен для ведения актуальной карты сетевой инфраструктуры и быстрого доступа к информации об устройствах.

Основные задачи:

- инвентаризация сетей и устройств;
- обнаружение устройств в подсетях;
- хранение интерфейсов, IP-адресов и портов;
- ручное редактирование имён и описаний;
- фиксация соединений между устройствами;
- отображение Web-сервисов;
- визуализация топологии;
- подготовка основы для мониторинга и инфраструктурных интеграций.

Архитектура рассчитана на несколько независимых площадок (Site) и дальнейшее масштабирование.

## 2. Возможности

### Dashboard

`/dashboard` — счётчики Sites, Networks, Devices, Ports и Connections, недавно изменённые и inactive-устройства, быстрые действия.

`/` перенаправляет на Dashboard.

### Devices

`/devices`

- список устройств;
- поиск, фильтрация, сортировка и пагинация;
- Add / Edit / Delete;
- Active / Inactive.

`/devices/<id>` — Details с Overview, Network, Interfaces/IP, Ports/Web Access и Connections.

### Networks

`/networks`

- Add / Edit / Delete;
- Active / Inactive;
- количество устройств.

`/networks/<id>` — Details сети, устройства и запуск Discovery.

### Discovery

`/discovery` и `/networks/<id>` позволяют запускать обнаружение устройств в сети.

Текущий Discovery синхронный: запрос выполняется до получения результата.

### Connections

`/connections` — CRUD соединений и каскадный выбор портов по выбранному устройству.

### Topology

`/topology` — Cytoscape.js граф, где устройства являются nodes, а connections — edges. Клик по узлу открывает Device Details.

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

- Site;
- Network;
- Device;
- Interface;
- IPAddress;
- Port;
- Service;
- Connection.

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

Текущие компоненты Discovery/сканирования включают ICMP, ARP, Nmap, DNS, mDNS и MAC Vendor.

Основной endpoint:

```http
POST /api/v1/networks/<network_id>/discover
```

Discovery должен собирать информацию, а не напрямую изменять БД. Обработка результатов выполняется сервисным слоем.

Планируемые интеграции: SNMP, LLDP, CDP, MikroTik, Proxmox, Docker, Home Assistant, VMware, Kubernetes, UniFi.

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
/api/v1/discovery
```

CRUD-ресурсы используют GET/POST/PUT/DELETE.

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

Поддерживаемые переменные окружения включают:

```text
SECRET_KEY
DATABASE_URL
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

### Discovery

Discovery синхронный и может занимать заметное время на больших подсетях. Следующий этап — фоновые задачи и статус/polling.

### Devices filtering

Фильтрация, сортировка и пагинация сейчас выполняются на UI-слое после получения полного списка. Для большого инвентаря операции следует перенести в API/БД.

### Sites

Отдельной CRUD-страницы Sites пока нет; Sites используются как справочник.

### Dashboard

Dashboard получает несколько коллекций API вместо отдельного aggregate `/api/v1/stats`.

### Monitoring

Полноценный online/offline monitoring пока не реализован. `Active / Inactive` — это состояние записи, а не результат мониторинга доступности.

## 17. Roadmap

### Iteration 1 — Foundation / UI

- [x] Flask application
- [x] SQLAlchemy
- [x] SQLite
- [x] migrations
- [x] REST API
- [x] Dashboard
- [x] Networks
- [x] Devices
- [x] Connections
- [x] Discovery
- [x] Topology
- [x] HTMX UI
- [x] Bootstrap UI

### Следующие этапы

1. API-side filtering/sorting/pagination для Devices.
2. Асинхронный Discovery.
3. Discovery status API.
4. Monitoring engine.
5. `/api/v1/stats`.
6. Sites CRUD.
7. Улучшение Services/Ports UI.
8. Расширение Topology.
9. Интеграции MikroTik / Proxmox.
10. PostgreSQL deployment.

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

NetMap находится в активной разработке. Текущая версия уже предоставляет рабочий inventory/discovery Web UI для основных объектов инфраструктуры:

```text
Dashboard
   │
   ├── Networks ── Discovery
   │
   ├── Devices
   │      ├── Interfaces
   │      ├── IP addresses
   │      ├── Ports
   │      └── Connections
   │
   ├── Connections
   │
   └── Topology
```

Следующая крупная цель — перейти от inventory/discovery к полноценному мониторингу и автоматическому обновлению карты инфраструктуры.
