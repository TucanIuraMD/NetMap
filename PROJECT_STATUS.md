# NetMap Project Status

**Last Updated:** 2026-08-17
**Version:** 0.3.0-dev
**Status:** Active Development
**License:** MIT

---

## Current State

NetMap has completed **Iteration 1 (Foundation)**, **Iteration 2 (Interfaces/IP/Ports/Connections)**, **Iteration 3 (Monitoring Engine)**, **Iteration 4 (Connections and Topology)**, and **Iteration 5 (Async Discovery)**, and is now a functional network infrastructure inventory, discovery, and monitoring platform with a polished Web UI, automatic availability checks, hardened connections management, a rebuilt topology visualization driven by a dedicated topology API, and non-blocking background discovery with live progress, results and cancel support.

---

## Completed Iterations

### ✅ Iteration 1 — Foundation

**Status:** Complete
**Completed:** 2026-08

Core infrastructure:
- Flask application foundation
- SQLAlchemy ORM with Flask-Migrate
- SQLite database (PostgreSQL-ready architecture)
- REST API (`/api/v1`)
- Basic CRUD for Sites, Networks, Devices
- Web UI with Bootstrap 5 and HTMX
- Dashboard with statistics
- Network Discovery with TCP port scanning
- Topology visualization (Cytoscape.js)
- Connections between devices

### ✅ Iteration 2 — Interfaces/IP/Ports/Connections

**Status:** Complete
**Completed:** 2026-08

Enhanced data model:
- Interface model with device relationships
- IPAddress model (normalized, 1:N with Interface)
- Port model with Service associations
- Connection model (device-to-device links)
- Cascading relationships
- Discovery synchronization improvements
- Port/Service management
- Interface and IP inventory

### ✅ UI Iteration — Polish & UX

**Status:** Complete
**Completed:** 2026-08

UI improvements:
- Services/Ports terminology consistency
- Device cards with full Services list
- Each Service on separate line with Open button
- Standard service names (SSH, HTTP, HTTPS, DNS, etc.)
- Web URL generation and quick access
- Device Types: Router, Switch, Server, NAS, Camera, Printer, AP, ESP32, PC, Laptop, Phone, **LXC**, **VM**, **ZigBee**, Unknown, Other
- Device Type labels (LXC → "LXC", VM → "VM", ZigBee → "ZigBee")
- Horizontal counters (Interfaces | IPs | Services | Links)
- 3-column grid on desktop
- Auto-height cards based on content
- Removed redundant Interfaces preview from cards
- Polished Device Details page

### ✅ API Enhancement — Server-side Operations

**Status:** Complete
**Completed:** 2026-08

API improvements:
- API-side filtering, sorting, pagination for `/devices`
- Query parameters: `search`, `network_id`, `device_type`, `is_active`, `sort`, `page`, `per_page`
- Server-side performance optimization
- Scalable for large inventories

### ✅ Iteration 3 — Monitoring Engine

**Status:** Complete
**Completed:** 2026-08-17

Automatic device availability monitoring:
- MonitoringService with ICMP ping + TCP fallback
- APScheduler integration for background tasks
- Periodic device checks (every 5 minutes, configurable)
- Automatic `is_active` status updates
- Configurable monitoring enable/disable
- Primary IP selection logic (prefer `is_primary`, fallback to any IP)
- TCP fallback to device's known open ports
- Reloader-safe scheduler initialization

**Configuration:**
- `MONITORING_ENABLED` — enable/disable monitoring (default: true)
- `MONITORING_INTERVAL_MINUTES` — check interval in minutes (default: 5)

**Files:**
- `backend/app/services/monitoring_service.py`
- `backend/app/scheduler.py`
- `backend/config.py` (monitoring settings)
- `backend/requirements.txt` (APScheduler added)
- `backend/app/__init__.py` (scheduler initialization)

### ✅ Port Import — Bulk Operations

**Status:** Complete
**Completed:** 2026-08
**Commit:** `358aa40 feat: add port import API`

Bulk port import feature:
- `POST /api/v1/imports/ports` endpoint
- JSON batch import (`{"items": [...]}`)
- Device resolution by ID or IP
- Duplicate prevention (already-existing ports are skipped)
- Automatic service detection
- Standard service mapping
- Auto-marker (`description='import:auto'`)

**Files:**
- `backend/app/api/v1/imports.py`
- `backend/app/services/port_import.py`

---

### ✅ Iteration 4 — Connections and Topology

**Status:** Complete
**Completed:** 2026-08-17
**Commits:**
- `ca5bcb4` feat: validate and harden connections API
- `1230db3` feat: add topology API and service
- `985c8f4` feat: improve connections UI
- `fcd98d3` feat: rebuild topology visualization

**Connections API hardening (`ca5bcb4`):**
- Input validation: required source/target devices, distinct devices, `connection_type` whitelist, port/interface ownership checks
- Validation errors: `400` (bad input, foreign port/interface, same device) and `404` (missing device/port/interface)
- Duplicate protection: `409 Conflict` when the device pair plus optional interface/port endpoints already exist; `connection_type` is not part of the identity
- Database unique constraint on connection endpoints (`unique_connection_endpoints` migration)
- Filters: `device_id` (source or target), `is_active`, `connection_type`
- Pagination: `page`, `per_page` (default 50, max 500, alias `page_size`) with a paginated envelope `{items, page, per_page, total, total_pages}`
- Backward compatibility: a request without query parameters returns a bare JSON array (legacy behavior)

**Topology API + service (`1230db3`):**
- `GET /api/v1/topology` endpoint backed by `TopologyService`
- Nodes = real devices with attached interfaces (and their IP addresses) and ports
- Edges = derived strictly from existing Connection records — no synthetic links, one edge per connection
- Edge only included when both endpoints are part of the filtered node set
- Filters: `network_id`, `device_type`, `status` (`active`/`inactive`)
- Response shape: `{nodes: [...], edges: [...]}` with Cytoscape-ready `data` blocks

**Connections UI (`985c8f4`):**
- Device filter on the connections list page (HTMX-driven table refresh)
- Interface and port shown together on each end of a connection
- Primary IP display per connection end
- "Open in Topology" action linking back to the topology graph
- Updated create/edit forms with cascading interface/port selects

**Topology visualization (`fcd98d3`):**
- Client rebuilt to fetch data **only** from `GET /api/v1/topology` (filters applied as query parameters on that same endpoint)
- Device labels: `display_name` / hostname / name, with primary IP as subtitle
- Edge labels include interface and port when available (e.g. `eth0 · 80/tcp (HTTP) → eth0 · 80/tcp (HTTP)`)
- Directed edges (arrow heads), color/line-style by connection type
- `cose` layout with fit/reload/toggle-unlinked controls and Reset button
- Empty state handled gracefully (no JS errors)
- Tap on node opens details panel with link to the device page

---

### ✅ Iteration 5 — Async Discovery

**Status:** Complete
**Completed:** 2026-08-17
**Commits:**
- `cdc043c` feat: add discovery job manager
- `5b36932` feat: add discovery progress and results API
- `858747d` feat: add ICMP probe and discovery range limits
- `d4a3588` feat: add discovery UI with progress polling

**Discovery job manager (`cdc043c`):**
- `DiscoveryJobManager` bound to the Flask app, one background job per network, single active job process-wide
- Job state kept in memory (running/completed/cancelled/failed; phases scanning/syncing/done)
- Thread-based background execution inside an application context, injectable scanner for tests
- Endpoints: `POST /api/v1/discovery/start`, `GET /api/v1/discovery/status`, `POST /api/v1/discovery/cancel`
- `409 Conflict` when a job is already running; validation for invalid/inactive/missing networks

**Progress and results API (`5b36932`):**
- Live progress via `on_progress` callback in `NetworkScanner`
- Monotonic `progress` percentage (`0..100`) and `scanned_hosts` counters
- `GET /api/v1/discovery/results` returning job state plus discovered hosts (`ip_address`, `hostname`, `open_ports`, `reachable`, `device_id`)

**ICMP probe and range limits (`858747d`):**
- `ICMPProbe` — raw-socket ICMP echo with `ICMPUnavailableError` when raw sockets are not permitted
- ICMP-first reachability with automatic TCP fallback over a fixed port list
- Range validation: `InvalidCIDRError` / `NetworkTooLargeError`, `DISCOVERY_MAX_HOSTS` limit (default 1024)
- Config: `DISCOVERY_MAX_HOSTS`, `DISCOVERY_TCP_TIMEOUT`, `DISCOVERY_ICMP_TIMEOUT`, `DISCOVERY_WORKERS`

**Discovery UI (`d4a3588`):**
- `/discovery` page with start, live progress polling (1s), results table, and cancel
- Polling stops on completion/cancellation/failure; job state restored on reload

**Real-world validation (192.168.80.0/24, network "Work"):**
- **254 hosts** scanned, **12 discovered**, all via TCP fallback (ICMP unavailable without `CAP_NET_RAW`), 242 unreachable, duration ~25s
- **Repeated run:** identical 12 IPs, **no duplicates** (dedup by IP, reuses existing devices)
- **Cancel:** job stopped at scanned=60 with results frozen
- DB after tests: 42 devices, 42 IPs, 72 ports, 2 connections; no duplicates created

**Known limitation:** raw ICMP requires `CAP_NET_RAW` (e.g. `setcap cap_net_raw+ep` or a systemd `AmbientCapabilities=` unit); without it the scanner silently falls back to TCP probing. On the dev sandbox this is expected behaviour.

---

## Current Data State

**Devices:** 42
**Networks:** 2 (Work 192.168.80.0/24, Home 192.168.88.1/24)
**Ports:** 72
**Services:** 8
**Connections:** 2
**Device Types in use:** router, unknown, lxc, test

**Example Device:**
- `docker.local` (192.168.80.16): 12 ports, 9 services
- Services: SSH, go2rtc, Portainer (multiple instances), intercom-bot, Qdrant, Test, border-dashboard, border-analytics

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Backend | Flask | Latest |
| ORM | SQLAlchemy | Latest |
| Migrations | Flask-Migrate / Alembic | Latest |
| Templates | Jinja2 | Latest |
| UI Framework | Bootstrap 5 | 5.x |
| Dynamic UI | HTMX | 1.x |
| Icons | Bootstrap Icons | Latest |
| Topology | Cytoscape.js | Latest |
| Scheduler | APScheduler | Latest |
| Database (dev) | SQLite | 3.x |
| Database (prod) | PostgreSQL | Ready |
| Server | Gunicorn | Latest |
| Python | 3.13 | 3.13+ |

---

## Project Structure

```
NetMap/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API endpoints
│   │   ├── models/          # SQLAlchemy models
│   │   ├── services/        # Business logic (discovery, monitoring, import)
│   │   ├── templates/       # Jinja2 templates
│   │   ├── static/          # CSS, JS, vendor libraries
│   │   ├── web/             # Web UI routes
│   │   ├── extensions.py    # Flask extensions
│   │   └── scheduler.py     # APScheduler configuration
│   ├── migrations/          # Alembic migrations
│   ├── instance/            # SQLite database
│   ├── config.py
│   ├── requirements.txt
│   └── run.py
├── docs/                    # Documentation
├── README.md
├── PROJECT_STATUS.md
├── CHANGELOG.md
└── LICENSE
```

---

## Database Schema

### Core Models

**Site** → **Network** → **Device** → **Interface** → **IPAddress**
**Device** → **Port** → **Service**
**Device** ← **Connection** → **Device**

### Models in Detail

1. **Site** — Physical location (Home, Office)
2. **Network** — Subnet (192.168.x.x/24)
3. **Device** — Any infrastructure object (Router, Server, VM, etc.)
4. **Interface** — Network interface (eth0, ens18)
5. **IPAddress** — IPv4/IPv6 address
6. **Port** — TCP/UDP port with optional Service link
7. **Service** — Named service (SSH, HTTP, DNS, etc.)
8. **Connection** — Device-to-device link

### Key Fields

**Device:**
- `name`, `hostname`, `device_type`, `is_active`
- `created_at`, `updated_at`

**Port:**
- `port_number`, `protocol`, `status`
- `service_id` (FK to Service)
- `web_scheme` (http/https for web access)
- `display_name`, `description`

**Service:**
- `name`, `description`
- Relationship: `ports` (1:N)

---

## REST API

**Base:** `/api/v1`

### Available Endpoints

```
GET    /api/v1/sites
GET    /api/v1/sites/<id>
POST   /api/v1/sites
PUT    /api/v1/sites/<id>
DELETE /api/v1/sites/<id>

GET    /api/v1/networks
GET    /api/v1/networks/<id>
POST   /api/v1/networks
PUT    /api/v1/networks/<id>
DELETE /api/v1/networks/<id>
POST   /api/v1/networks/<id>/discover

POST   /api/v1/discovery/start
GET    /api/v1/discovery/status
GET    /api/v1/discovery/results
POST   /api/v1/discovery/cancel

GET    /api/v1/devices
GET    /api/v1/devices/<id>
POST   /api/v1/devices
PUT    /api/v1/devices/<id>
DELETE /api/v1/devices/<id>

GET    /api/v1/interfaces
GET    /api/v1/interfaces/<id>
POST   /api/v1/interfaces
PUT    /api/v1/interfaces/<id>
DELETE /api/v1/interfaces/<id>

GET    /api/v1/ip-addresses
GET    /api/v1/ip-addresses/<id>
POST   /api/v1/ip-addresses
PUT    /api/v1/ip-addresses/<id>
DELETE /api/v1/ip-addresses/<id>

GET    /api/v1/ports
GET    /api/v1/ports/<id>
POST   /api/v1/ports
PUT    /api/v1/ports/<id>
DELETE /api/v1/ports/<id>

GET    /api/v1/services
GET    /api/v1/services/<id>
POST   /api/v1/services
PUT    /api/v1/services/<id>
DELETE /api/v1/services/<id>

GET    /api/v1/connections
GET    /api/v1/connections/<id>
POST   /api/v1/connections
PUT    /api/v1/connections/<id>
DELETE /api/v1/connections/<id>

GET    /api/v1/topology

POST   /api/v1/imports/ports
```

### API Features

**Devices endpoint** supports:
- `?search=<term>` — Search by name/hostname/IP
- `?network_id=<id>` — Filter by network
- `?device_type=<type>` — Filter by device type
- `?is_active=<true|false>` — Filter by active status
- `?sort=<field>` — Sort by field (`name`, `hostname`, `device_type`, `is_active`, `created_at`, `updated_at`)
- `?page=<n>` — Pagination page number
- `?per_page=<n>` — Results per page (default: 50)

**Connections endpoint** supports:
- `?device_id=<id>` — Filter by device (source or target)
- `?is_active=<true|false>` — Filter by active status
- `?connection_type=<type>` — Filter by type (network, ethernet, fiber, wifi, virtual, other)
- `?page=<n>` — Pagination page number
- `?per_page=<n>` — Results per page (default: 50, max: 500, alias `page_size`)
- Validation: `400` for bad input and foreign ports/interfaces, `404` for missing references
- Duplicate protection: `409 Conflict` when the endpoint pair already exists

**Topology endpoint** (`GET /api/v1/topology`) supports:
- `?network_id=<id>` — Include devices of a single network
- `?device_type=<type>` — Include devices with the exact device type
- `?status=<active|inactive>` — Filter by active status

---

## Web UI

### Pages

- `/` → redirect to Dashboard
- `/dashboard` — Statistics, recent devices, quick actions
- `/devices` — Device list with search/filter/sort/pagination
- `/devices/<id>` — Device details (Overview, Network, Interfaces/IP, Services, Connections)
- `/networks` — Network list with CRUD
- `/networks/<id>` — Network details with Discovery
- `/connections` — Connection list with CRUD, device filter
- `/topology` — Interactive graph visualization with network/type/status filters
- `/discovery` — Discovery interface (redirects to Networks)

### UI Features

- **HTMX** for dynamic updates without page reload
- **Bootstrap 5** for responsive design
- **Modal forms** for Create/Edit operations
- **Cascading selects** for device/port selection
- **Search/filter/sort** on client and server side
- **Pagination** for large datasets
- **Dark theme** support (ready)
- **3-column grid** for device cards on desktop
- **Quick web access** via Open buttons on service cards

---

## Discovery

### Discovery Service

**Current implementation:** asynchronous background jobs.

**Endpoints:**
- `POST /api/v1/discovery/start` — start a background job
- `GET /api/v1/discovery/status?network_id=<id>` — progress and state
- `GET /api/v1/discovery/results?network_id=<id>` — job state plus discovered hosts
- `POST /api/v1/discovery/cancel` — cancel a running job
- `POST /api/v1/networks/<id>/discover` — legacy synchronous discovery (kept for compatibility)

**Components:**
- `DiscoveryJobManager` — background job lifecycle (one active job per process)
- `NetworkScanner` — ICMP-first parallel scanning with TCP fallback
- `ICMPProbe` — raw-socket ICMP echo (falls back gracefully without `CAP_NET_RAW`)
- `DiscoveryService` — database synchronization

**Flow:**
1. Scan network CIDR (host limit: `DISCOVERY_MAX_HOSTS`, default 1024)
2. Probe reachability: ICMP echo, falling back to TCP port probing
3. Resolve hostnames
4. Identify open ports
5. Sync to database (create/update devices)
6. Mark missing devices as inactive

**Port detection:** 22, 23, 53, 80, 81, 443, 445, 554, 8080, 8443 (single source of truth shared with monitoring)

---

## Monitoring

### Monitoring Service

**Status:** Implemented

**Components:**
- `MonitoringService` — Device availability checks
- `APScheduler` — Background task scheduler
- Automatic periodic execution (every 5 minutes by default)

**Flow:**
1. Query all devices with IP addresses
2. Check reachability via ICMP ping
3. Fallback to TCP probe on known open ports
4. Update `Device.is_active` based on results
5. Commit changes to database

**Check Logic:**
- Primary: ICMP ping (system `ping` command)
- Fallback: TCP connection to device's open ports (or default ports)
- Timeout: 1 second (configurable)

**Configuration:**
- `MONITORING_ENABLED` — Enable/disable monitoring (default: true)
- `MONITORING_INTERVAL_MINUTES` — Check interval (default: 5 minutes)

**Current state:** Fully operational, runs in background

---

## Standard Services

NetMap recognizes standard services and generates Web URLs:

| Port | Protocol | Service | web_scheme |
|------|----------|---------|------------|
| 22 | tcp | SSH | — |
| 53 | tcp/udp | DNS | — |
| 80 | tcp | HTTP | http |
| 443 | tcp | HTTPS | https |
| 3000 | tcp | Portainer | http |
| 5000 | tcp | (custom) | http |
| 6333 | tcp | Qdrant | — |
| 6334 | tcp | Qdrant | — |
| 8000 | tcp | Portainer | http |
| 8006 | tcp | Proxmox | https |
| 8080 | tcp | HTTP Alt | http |
| 8088 | tcp | (custom) | http |
| 8443 | tcp | HTTPS Alt | https |
| 8554 | tcp | RTSP | — |
| 9443 | tcp | Portainer | https |

**Web URL format:** `{scheme}://{ip}:{port}`

---

## Known Limitations

1. **Monitoring History** — No historical availability data stored yet
2. **Sites CRUD** — No dedicated UI page
3. **Dashboard stats** — Fetches multiple collections instead of aggregate API
4. **Large datasets** — API filtering helps, but UI can be improved
5. **Alert System** — No notifications on device status changes
6. **ICMP** — Raw ICMP requires `CAP_NET_RAW`; falls back to TCP probing without it

---

## Roadmap

### ✅ Completed

- [x] Iteration 1: Foundation
- [x] Iteration 2: Interfaces/IP/Ports/Connections
- [x] UI Iteration: Polish & UX
- [x] API-side filtering/sorting/pagination for Devices
- [x] Services/Ports UI with Open buttons
- [x] Standard service names and web URLs
- [x] Device Types (LXC, VM, ZigBee)
- [x] Iteration 3: Monitoring Engine (ICMP ping + TCP fallback, APScheduler)
- [x] Port Import API (bulk `POST /api/v1/imports/ports`)
- [x] Iteration 4: Connections API hardening (validation, duplicate protection, filters, pagination)
- [x] Iteration 4: Topology API + TopologyService (`GET /api/v1/topology`)
- [x] Iteration 4: Connections UI (device filter, interface+port labels, Open in Topology)
- [x] Iteration 4: Topology visualization on Cytoscape.js (directed edges, labels, filters, empty state)
- [x] Iteration 5: Async discovery job manager (`POST /api/v1/discovery/start`, status, cancel)
- [x] Iteration 5: Discovery progress and results API (`GET /api/v1/discovery/status`, `/results`)
- [x] Iteration 5: ICMP probe with TCP fallback and discovery range limits (`DISCOVERY_MAX_HOSTS`)
- [x] Iteration 5: Discovery UI with live progress polling

### 📋 Next Steps

1. **Monitoring History** — Store availability check results over time
2. **Dashboard Stats API** — `/api/v1/stats` aggregate endpoint
3. **Alert System** — Notifications on device status changes
4. **Sites CRUD UI** — Dedicated page for Sites management
5. **Service Detection** — Enhanced automatic service identification
6. **Topology Enhancements** — Additional layouts, export (PNG/SVG/PDF), node grouping
7. **Infrastructure Integrations** — MikroTik, Proxmox, Docker APIs
8. **PostgreSQL Deployment** — Production database setup
9. **Multi-user & RBAC** — Authentication and authorization

### 🔮 Future (v2.0+)

- Asset Management
- Rack Management
- SNMP support
- LLDP/CDP discovery
- Syslog server
- Alert system
- Mobile app
- Plugin marketplace

---

## Git Status

**Branch:** `main`

**Last commits (Iteration 5):**
```
d4a3588 feat: add discovery UI with progress polling
858747d feat: add ICMP probe and discovery range limits
5b36932 feat: add discovery progress and results API
cdc043c feat: add discovery job manager
```

**Uncommitted changes:**
- None in tracked files. `opencode.json` is untracked and intentionally not committed.

**Note:** this status document is itself pending commit together with the Iteration 5 documentation update.

---

## Development

### Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask run --host=0.0.0.0 --port=5001
```

### Testing

```bash
python -m compileall -q backend/app
git diff --check
```

### Database

```bash
flask db upgrade        # Apply migrations
flask db migrate -m ""  # Create migration
```

---

## Contact & Support

**Project:** NetMap
**Repository:** (internal)
**Documentation:** `/docs/`
**License:** MIT

---

**End of Status Document**
