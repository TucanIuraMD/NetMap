# Changelog

All notable changes to NetMap will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Documentation updates for Monitoring Engine (README, PROJECT_STATUS, CHANGELOG, docs/)
- TODO.md with current project status and roadmap

### Added - Iteration 4: Connections and Topology
- Connections API hardening: validation, duplicate protection, filters, pagination
- Connections duplicate protection (`409 Conflict`) with unique endpoint constraint
- Connections API validation (`400`/`404`) for devices, ports, interfaces and connection types
- Connections API filters (`device_id`, `is_active`, `connection_type`) and pagination (`page`, `per_page`)
- Topology API `GET /api/v1/topology` backed by TopologyService
- Topology nodes (devices with interfaces/IPs/ports) and edges (real connections only)
- Topology filters (`network_id`, `device_type`, `status`)
- Connections UI: device filter, interface+port labels, IP display, Open in Topology
- Topology visualization rebuilt on `GET /api/v1/topology` (Cytoscape.js, directed edges, labels, empty state)
- Documentation: Iteration 4 added to PROJECT_STATUS, TODO, API spec

---

## [0.3.0] - 2026-08-17

### Added - Iteration 3: Monitoring Engine
- MonitoringService for device availability checks
- APScheduler integration for background periodic tasks
- Automatic device reachability monitoring (ICMP ping + TCP fallback)
- Configurable monitoring interval (default: 5 minutes)
- Monitoring enable/disable via `MONITORING_ENABLED` config
- Primary IP selection logic (prefer `is_primary`, fallback to any IP)
- TCP fallback to device's known open ports or standard ports
- Reloader-safe scheduler initialization (Flask debug mode compatible)
- Auto-update `Device.is_active` based on monitoring results

### Added - UI/UX Polish
- Device Types: LXC, VM, ZigBee with custom labels
- Device Type labels mapping (LXC → "LXC", VM → "VM", ZigBee → "ZigBee")
- Port Import API endpoint `POST /api/v1/imports/ports` (implemented, not committed)
- Bulk port import service with duplicate prevention
- Standard service detection and automatic naming
- Auto-marker for imported ports (`description='import:auto'`)

### Changed
- Terminology: "Ports" → "Services" in UI (Device cards, Dashboard, Details page)
- Device cards: Full Services list on separate lines (no truncation, no scrollbar)
- Device cards: Auto-height based on Services count
- Device cards: Removed Interfaces preview block
- Device cards: Horizontal counters layout (Interfaces | IPs | Services | Links)
- Device cards: 3-column grid on desktop (row-cols-xl-3)
- Services display: Service name bold, port/protocol normal, Open button right-aligned
- Services display: Thin dividers between rows
- Device form: Device Type dropdown with display labels
- Config: Added `MONITORING_ENABLED` and `MONITORING_INTERVAL_MINUTES`
- Requirements: Added APScheduler dependency

### Fixed
- Device cards now show all Services without +N more button
- Device cards grid layout consistency (h-100 for equal heights in row)
- Hostname/IP display logic (show both if hostname exists, IP only otherwise)

---

## [0.2.0] - 2026-08-16

### Added
- API-side filtering for `/api/v1/devices` endpoint
- API-side sorting for `/api/v1/devices` endpoint
- API-side pagination for `/api/v1/devices` endpoint
- Query parameters: `search`, `network_id`, `device_type`, `is_active`, `sort`, `page`, `per_page`
- Server-side performance optimization for large device inventories
- Scalable device list operations

### Changed
- Devices endpoint moved filtering/sorting/pagination from UI to API
- Improved performance for device listing with large datasets

---

## [0.1.3] - 2026-08-15

### Added
- Standard service names (SSH, HTTP, HTTPS, DNS, Portainer, Proxmox, Qdrant, etc.)
- Web URL generation for web-accessible services
- `web_scheme` field in Port model (http/https)
- Quick web access via "Open" buttons on service cards
- Service name auto-detection based on port number
- Web service indicators in UI

### Changed
- Port display shows service name if available, otherwise port number
- Device Details: Services section with Web Access column
- Device cards: Open buttons for web-accessible services
- Services terminology in UI components

### Fixed
- Service name display consistency across UI
- Web URL generation logic

---

## [0.1.2] - 2026-08-14

### Added
- UI polish for Ports and Interfaces
- Enhanced Device Details page layout
- Improved visual hierarchy
- Consistent spacing and typography

### Changed
- Device Details tabs styling
- Port/Interface sections visual design
- Connection display improvements

---

## [0.1.1] - 2026-08-13

### Added
- Complete UI design iteration
- Bootstrap 5 theme customization
- Responsive layout improvements
- Enhanced Dashboard statistics
- Improved navigation

### Changed
- Color scheme refinements
- Typography updates
- Card layouts
- Button styles
- Modal designs

---

## [0.1.0] - 2026-08-12

### Added - Iteration 2: Interfaces/IP/Ports/Connections

**Models:**
- Interface model with device relationships
- IPAddress model (normalized, 1:N with Interface)
- Port model with Service associations
- Connection model (device-to-device links)
- Service model for named services

**Database:**
- Database migrations for new models
- Cascading delete relationships
- Foreign key constraints
- Indexes for performance

**API:**
- `/api/v1/interfaces` CRUD endpoints
- `/api/v1/ip-addresses` CRUD endpoints
- `/api/v1/ports` CRUD endpoints
- `/api/v1/services` CRUD endpoints
- `/api/v1/connections` CRUD endpoints

**Discovery:**
- Discovery synchronization with Interfaces
- Automatic Interface creation ("discovered")
- IP address association
- Port detection and syncing
- Inactive device marking

**UI:**
- Device Details: Interfaces/IP section
- Device Details: Ports section
- Device Details: Connections section
- Interface management forms
- IP address management forms
- Port management forms
- Connection management with cascading device/port selection
- Connections list page

**Features:**
- Device-to-device connections
- Multi-interface devices support
- Multiple IP addresses per interface
- Port status tracking (open/closed/filtered)
- Service-to-port associations

---

## [0.0.1] - 2026-08-08

### Added - Iteration 1: Foundation

**Core:**
- Flask application foundation
- SQLAlchemy ORM integration
- Flask-Migrate for database migrations
- SQLite database (development)
- PostgreSQL-ready architecture
- Configuration management
- Environment variables support

**Models:**
- Site model (physical locations)
- Network model (subnets)
- Device model (infrastructure objects)
- Basic relationships and constraints

**API:**
- REST API base path `/api/v1`
- `/api/v1/sites` CRUD endpoints
- `/api/v1/networks` CRUD endpoints
- `/api/v1/devices` CRUD endpoints
- `/api/v1/health` health check endpoint
- JSON request/response handling
- Error handling and validation

**Discovery:**
- NetworkScanner service (TCP port scanning)
- DiscoveryService for database synchronization
- Network discovery endpoint `POST /api/v1/networks/<id>/discover`
- Hostname resolution
- Open port detection
- Device creation from discovery results

**UI:**
- Web UI foundation with Jinja2 templates
- Bootstrap 5 integration
- HTMX for dynamic updates
- Bootstrap Icons
- Dashboard with statistics
- Sites reference
- Networks list and CRUD
- Devices list and CRUD
- Device Details page
- Discovery interface
- Topology visualization (Cytoscape.js)
- Modal forms for Create/Edit
- HTMX-based table updates
- Search functionality
- Active/Inactive status toggle

**Static Assets:**
- Bootstrap 5 (local)
- HTMX (local)
- Bootstrap Icons (local)
- Cytoscape.js (local)
- Custom CSS

**Development:**
- Flask development server
- Gunicorn configuration
- Requirements.txt
- README documentation
- Project structure
- Coding standards document
- Architecture documentation
- Database design document
- API specification document

---

## Initial Commit - 2026-08-01

### Added
- Project repository initialization
- Basic documentation structure
- License (MIT)
- .gitignore

---

## Legend

- **Added:** New features
- **Changed:** Changes to existing functionality
- **Deprecated:** Soon-to-be removed features
- **Removed:** Removed features
- **Fixed:** Bug fixes
- **Security:** Security fixes

---

**End of Changelog**
