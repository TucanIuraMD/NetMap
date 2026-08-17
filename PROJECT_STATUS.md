# NetMap Project Status

**Last Updated:** 2026-08-17
**Version:** 0.3.0-dev
**Status:** Active Development
**License:** MIT

---

## Current State

NetMap has completed **Iteration 1 (Foundation)**, **Iteration 2 (Interfaces/IP/Ports/Connections)**, and **Iteration 3 (Monitoring Engine)**, and is now a functional network infrastructure inventory, discovery, and monitoring platform with a polished Web UI and automatic availability checks.

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

**Status:** Implemented (not committed)
**Completed:** 2026-08

Bulk port import feature:
- `POST /api/v1/imports/ports` endpoint
- JSON batch import
- Duplicate prevention
- Automatic service detection
- Standard service mapping
- Auto-marker (`description='import:auto'`)

**Files:**
- `backend/app/api/v1/imports.py` (untracked)
- `backend/app/services/port_import.py` (untracked)
- `backend/app/api/v1/__init__.py` (modified, not committed)

---

## Current Data State

**Devices:** 41
**Networks:** 2 (192.168.88.0/24, 192.168.80.0/24)
**Ports:** 71
**Services:** 8
**Device Types in use:** lxc, router, test, unknown

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
4. **Interface** — Network interface (eth0, ens18, discovered)
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

POST   /api/v1/imports/ports  (not committed)
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

---

## Web UI

### Pages

- `/` → redirect to Dashboard
- `/dashboard` — Statistics, recent devices, quick actions
- `/devices` — Device list with search/filter/sort/pagination
- `/devices/<id>` — Device details (Overview, Network, Interfaces/IP, Services, Connections)
- `/networks` — Network list with CRUD
- `/networks/<id>` — Network details with Discovery
- `/connections` — Connection list with CRUD
- `/topology` — Interactive graph visualization
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

**Endpoint:** `POST /api/v1/networks/<id>/discover`

**Components:**
- `NetworkScanner` — TCP port scanning
- `DiscoveryService` — Database synchronization

**Flow:**
1. Scan network CIDR
2. Detect hosts via TCP port probe
3. Resolve hostnames
4. Identify open ports
5. Sync to database (create/update devices)
6. Mark missing devices as inactive

**Port detection:** 22, 23, 53, 80, 81, 443, 445, 554, 8080, 8443

**Current state:** Synchronous (blocking request)

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

1. **Discovery** — Synchronous; no background tasks or progress API yet
2. **Sites CRUD** — No dedicated UI page
3. **Dashboard stats** — Fetches multiple collections instead of aggregate API
4. **Large datasets** — API filtering helps, but UI can be improved
5. **Monitoring History** — No historical availability data stored yet
6. **Alert System** — No notifications on device status changes

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
- [x] Port Import API (implemented, not committed)

### 📋 Next Steps

1. **Async Discovery** — Background tasks with status API and progress tracking
2. **Monitoring History** — Store availability check results over time
3. **Dashboard Stats API** — `/api/v1/stats` aggregate endpoint
4. **Alert System** — Notifications on device status changes
5. **Sites CRUD UI** — Dedicated page for Sites management
6. **Service Detection** — Enhanced automatic service identification
7. **Topology Enhancements** — Layouts, filters, export
8. **Infrastructure Integrations** — MikroTik, Proxmox, Docker APIs
9. **PostgreSQL Deployment** — Production database setup
10. **Multi-user & RBAC** — Authentication and authorization

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
**Ahead of origin:** 2 commits

**Last commits:**
```
34c5d46 fix: show all device ports in cards
b5d81eb feat: API-side filtering/sorting/pagination for devices
9e27ddd fix: polish NetMap UI ports and interfaces
```

**Uncommitted changes:**
- Modified: 15 files (documentation, templates, web routes, config, scheduler)
- Untracked: 5 files (imports API, port_import service, monitoring_service, scheduler, opencode.json)

**Changes include:**
- Monitoring Engine (MonitoringService, APScheduler)
- Device Types: LXC, VM, ZigBee with labels
- Services terminology (Ports → Services)
- Final device cards UI (3-column grid, full Services list, auto-height)
- Port import API (not committed)
- Documentation updates (README, PROJECT_STATUS, CHANGELOG, TODO, docs/)

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
