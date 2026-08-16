# NetMap — Iteration 2: Interfaces, IP Addresses, Ports & Connections

**Document:** docs/02_ITERATION_2.md
**Iteration:** 2
**Status:** Implemented, verified, not committed

---

## 1. Цель

Закрыть "разрыв" между целевой моделью данных (`docs/02_DATABASE.md`) и реальностью
Iteration 1, где `Connection` ссылался на сервисные `Port`, а не на сетевые `Interface`:

- Device → Interface × N → IPAddress × N;
- Device → Service Port × N;
- Connection Interface → Interface;
- полный CRUD для Interfaces / IPAddresses / Ports в UI;
- валидация API;
- Device Cards со статистикой и Device Details с вкладками;
- Network Details со счётчиками;
- Topology с подписями интерфейсов и локальной топологией устройства.

## 2. Изменения в схеме БД

Миграция `backend/migrations/versions/7d2f4c1a9b3e_add_connection_interfaces.py`
(down_revision `c71378a1e1c3`):

- добавлены `connections.source_interface_id` и `connections.target_interface_id`
  (nullable FK → `interfaces.id`, `ondelete=SET NULL`);
- сохранены `source_device_id` / `target_device_id` и `source_port_id` / `target_port_id`
  для обратной совместимости.

Модель `backend/app/models/connection.py`: колонки + отношения `source_interface` / `target_interface`.

Применение:

```bash
cd backend && /path/to/.venv/bin/python -m flask db upgrade
```

Alembic head после применения: `7d2f4c1a9b3e`.

## 3. Изменения в API

### Валидация (`backend/app/api/v1/validation.py`)

Общий модуль валидаторов, подключён к create/update в `interfaces.py`, `ip_addresses.py`, `ports.py`:

- `validate_interface_type` — enum `{unknown, ethernet, wifi, loopback, other, test}`;
- `validate_mac_address` — формат `aa:bb:cc:dd:ee:ff`;
- `validate_positive_int` — для speed/MTU (>0);
- `validate_ip_address` — через `ipaddress.ip_address()`, version должен совпадать с семейством адреса;
- `validate_port_number` — 1..65535;
- `validate_port_protocol` — `tcp`/`udp`;
- `validate_port_status` — `{open, closed, filtered}`.

### Connections (`backend/app/api/v1/connections.py`)

- `connection_to_dict` теперь включает `source_interface_id` / `target_interface_id`;
- create/update валидируют:
  - source/target device существуют и **различаются** (400);
  - при заданном `source_interface_id` интерфейс существует (404) и **принадлежит**
    source-устройству (400); аналогично для target;
  - source и target интерфейсы не совпадают (400);
- legacy `source_port_id`/`target_port_id` по-прежнему принимаются и валидируются.

### IP Addresses (`backend/app/api/v1/ip_addresses.py`)

- валидация адреса и совпадение version с семейством (400);
- дубликат `interface_id + address` → 409.

## 4. Изменения в UI

### Devices List (`/devices`, `backend/app/web/devices.py` + `templates/devices/_table.html`)

Сетка карточек устройств вместо таблицы. Каждая карточка:

- имя/display name, статус Active/Inactive;
- счётчики: interfaces, IP-адреса, service ports, connections;
- первые 3 интерфейса списком;
- ссылка **Show all (N)** → Device Details на вкладку Interfaces;
- dropdown Actions (Details / Edit / Delete);
- пагинация, сортировка и поиск сохранены.

`_filtered_devices` теперь считает `ports_count`, `interfaces_count`, `ip_count`,
`connections_count`, `interfaces_preview`, `primary_ip` на UI-слое из полных коллекций.

### Device Details (`/devices/<id>`)

Вкладки: **Overview / Interfaces / IP Addresses / Services / Connections / Topology**.

- секции-партиалы: `_interfaces_section.html`, `_ip_addresses_section.html`,
  `_ports_section.html`, `_connections_section.html`;
- полный CRUD для интерфейсов, IP-адресов и портов через модальные окна
  (`_interface_form.html`, `_ip_address_form.html`, `_port_form.html`);
- после успешного create/update сервер отдаёт OOB-обновление секции
  (`<div id="device-interfaces-section" hx-swap-oob="true">`) + HX-Trigger
  `interface-saved` / `ip-address-saved` / `port-saved`;
- `netmap.js` закрывает модалку, показывает toast и делает reload, если секция
  отсутствует на странице (детализация вне Device Details);
- удаление устройства — через fetch + редирект (как в Iteration 1);
- вкладка Topology рендерит локальную топологию с focus на текущем устройстве
  (`NM_FOCUS_DEVICE_ID`).

### Network Details (`/networks/<id>`)

Счётчики: Devices (active/total), Interfaces, IP Addresses, Service Ports, Connections.
Расчёт в `web/networks.py::network_details` из коллекций API по `device.network_id`.

### Connections (`/connections`)

- `_connections_with_names` показывает `source_interface_label` / `target_interface_label`
  вместо port-labels; для legacy записей без интерфейсов — `— → —`;
- форма: каскадный выбор интерфейсов по выбранному Source/Target Device
  (`/connections/interface-options?device_id=...`), заменяющий прежний `port-options`;
- старый `_port_options.html` удалён, маршрут `interface_options` добавлен.

### Topology

`static/js/topology.js`:

- edges подписаны интерфейсами (`sourceIface → targetIface`);
- режим focus (`window.NM_FOCUS_DEVICE_ID`): рендерится локальный подграф устройства
  на странице Device Details;
- загружает `/api/v1/interfaces` для подписей edges;
- `topology/index.html` получил `window.NM_INTERFACES_URL`.

## 5. Dashboard

`web/dashboard.py` — добавлены счётчики interfaces и ip_addresses (итого 8 stat-карточек).

## 6. Тесты и проверка

### API

`/home/opencode/.tmp_claude/iter2_api_test.py` — 25 проверок (fixtures изолированные):

- interfaces: создание/валидация name, device (404), MAC, type, speed≤0, MTU=0, PUT;
- ip-addresses: валидация адреса, version mismatch, дубликат 409;
- ports: порт 0 / >65535, протокол, статус;
- connections: с интерфейсом, same device 400, неизвестный интерфейс 404,
  same interface 400, интерфейс чужого устройства 400, очистка интерфейса;
- полная очистка fixture.

Результат: **25/25 PASS**.

### Browser (Playwright)

`/home/opencode/.tmp_claude/iter2_browser_test.py` — 37 проверок:

- Device Cards Grid (карточки, статистика, Show all);
- Device Details вкладки + секции;
- Interface CRUD (create/delete, OOB-обновление секции);
- IP CRUD (create/delete);
- Port CRUD (create/delete);
- Network Counters (5 stat-карточек, соответствие БД);
- Connections List (имена устройств, interface labels);
- Topology (canvas + Cytoscape canvases).

Результат: **37/37 PASS**.

### Regression (Iteration 1 bugfix)

`/home/opencode/.tmp_claude/regression_test.py` — 20 проверок, **19 PASS**.
Единственный FAIL — устаревший сценарий "Devices Edit form (Active toggle)",
который ищет `<tr>` в списке устройств; список переведён на карточки (запрошенное
изменение Iteration 2). Функциональность Edit подтверждена отдельной проверкой
(модалка, is_active checkbox, hx-put) на новой карточной вёрстке.

### Данные после тестов

Тестовые записи (interfaces/IP/ports/connections/devices) удалены. Исходное состояние:

```text
devices 36 | interfaces 36 | ip_addresses 36 | ports 52 | connections 1 | networks 2 | sites 1
alembic_version: 7d2f4c1a9b3e
```

## 7. Известные ограничения

- Соединение Iteration 1 (id=1) связано по `source_port_id=19` / `target_port_id=3`,
  `source_interface_id`/`target_interface_id` = NULL; в UI колонка интерфейсов
  показывает `— → —`. Обновление такой записи через форму позволяет выставить
  интерфейсы, legacy-поля портов сохраняются.
- Фильтрация/сортировка/пагинация Devices остаются in-memory на UI-слое
  (не перенесены в API — вне рамок Iteration 2).
- Discovery остаётся синхронным (не менялся).

## 8. Отличия от Iteration 1 (кратко)

| Аспект | Iteration 1 | Iteration 2 |
|---|---|---|
| Connection ссылки | `source_port_id`/`target_port_id` | `source_interface_id`/`target_interface_id` (+ legacy) |
| Devices List | таблица | карточки со статистикой |
| Device Details | Overview/Network/Ports/Connections | Overview/Interfaces/IP/Services/Connections/Topology + CRUD секций |
| Connections form | каскадный выбор портов | каскадный выбор интерфейсов |
| Network Details | "X active / Y total" | 5 stat-карточек |
| Topology | подписи без интерфейсов | подписи интерфейсов + local topology |
| Валидация API | частичная | централизованная (validation.py) |

---

End of Document