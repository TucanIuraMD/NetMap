# NetMap TODO

**Last Updated:** 2026-08-17
**Version:** 0.3.0-dev

---

## ✅ Completed

### Iteration 1 — Foundation
- [x] Flask application foundation
- [x] SQLAlchemy ORM + Flask-Migrate
- [x] SQLite database (PostgreSQL-ready)
- [x] REST API (`/api/v1`)
- [x] Basic CRUD for Sites, Networks, Devices
- [x] Web UI with Bootstrap 5 and HTMX
- [x] Dashboard with statistics
- [x] Network Discovery (TCP port scanning)
- [x] Topology visualization (Cytoscape.js)
- [x] Device connections

### Iteration 2 — Interfaces/IP/Ports/Connections
- [x] Interface model with device relationships
- [x] IPAddress model (normalized, 1:N with Interface)
- [x] Port model with Service associations
- [x] Service model
- [x] Connection model (device-to-device links)
- [x] Cascading relationships
- [x] Discovery synchronization improvements
- [x] Port/Service management UI
- [x] Interface and IP inventory UI

### Iteration 3 — Monitoring Engine
- [x] MonitoringService (ICMP ping + TCP fallback)
- [x] APScheduler integration
- [x] Automatic device availability checks (every 5 minutes)
- [x] Auto-update Device.is_active based on reachability
- [x] Configurable monitoring interval and enable/disable
- [x] Primary IP selection logic

### UI/UX Polish
- [x] API-side filtering/sorting/pagination for Devices
- [x] Standard service names and detection
- [x] Web URL generation for services
- [x] Quick web access (Open buttons)
- [x] Services terminology in UI
- [x] Device Types: Router, Switch, Server, NAS, Camera, Printer, AP, ESP32, PC, Laptop, Phone, LXC, VM, ZigBee, Unknown, Other
- [x] Device cards UI polish (3-column grid, full Services list, auto-height)

### Port Import
- [x] Port Import API endpoint (`POST /api/v1/imports/ports`)
- [x] Bulk port import service
- [x] Device resolution (ID/IP/name/hostname)
- [x] Duplicate prevention
- [x] Standard service mapping

### Iteration 4 — Connections and Topology
- [x] Connections API hardening (validation, duplicate protection, filters, pagination)
- [x] Connections duplicate protection (409) with unique endpoint constraint
- [x] Connections API filters (`device_id`, `is_active`, `connection_type`)
- [x] Connections API pagination (`page`, `per_page`)
- [x] Topology API `GET /api/v1/topology` + TopologyService
- [x] Topology filters (`network_id`, `device_type`, `status`)
- [x] Connections UI (device filter, interface+port labels, Open in Topology)
- [x] Topology visualization rebuilt on the topology API (Cytoscape.js)

### Iteration 5 — Async Discovery
- [x] Background discovery tasks (non-blocking)
- [x] Discovery start/status/cancel endpoints
- [x] Discovery progress tracking (monotonic percentage)
- [x] Discovery results API (`GET /api/v1/discovery/results`)
- [x] ICMP probe (raw socket) with automatic TCP fallback
- [x] Discovery range limits (`DISCOVERY_MAX_HOSTS`, default 1024)
- [x] UI polling for discovery progress
- [x] Real-world validation on 192.168.80.0/24 (254 scanned, 12 discovered, repeat run without duplicates, cancel works)

---

## 🔄 In Progress

- None. Iteration 5 is complete; the next iteration is **Monitoring History** (see Current Focus).

---

## 📋 High Priority (Next Iteration)

### Discovery History
- [ ] Persist discovery job runs (history table + API)
- [ ] Re-run discovery from history

### Monitoring Enhancements
- [ ] Monitoring history table (store check results over time)
- [ ] Monitoring history API (`GET /api/v1/monitoring/history`)
- [ ] Device availability timeline
- [ ] Latency measurement and storage
- [ ] Packet loss tracking
- [ ] Response time tracking
- [ ] Monitoring dashboard widget

### Dashboard Improvements
- [ ] Stats API (`GET /api/v1/stats`) — aggregate endpoint
- [ ] Real-time stats updates (WebSocket or polling)
- [ ] Device status overview (online/offline count)
- [ ] Recent monitoring events
- [ ] Network health indicators

---

## 📋 Medium Priority

### Sites CRUD UI
- [ ] Sites list page (`/sites`)
- [ ] Site details page (`/sites/<id>`)
- [ ] Site create/edit/delete forms
- [ ] Site-level statistics
- [ ] Networks list per site

### Alert System
- [ ] Alert configuration model
- [ ] Alert rules (device offline, new device discovered, etc.)
- [ ] Alert notification service
- [ ] Email notifications
- [ ] Webhook notifications
- [ ] Alert history
- [ ] Alert UI

### Service Detection
- [ ] Enhanced automatic service identification
- [ ] Service version detection
- [ ] Banner grabbing for known services
- [ ] Service fingerprinting
- [ ] Custom service definitions

### Topology Enhancements
- [x] Topology filters (by network, device type, status)
- [x] Edge labels (interface, port when available)
- [ ] Multiple layout algorithms (hierarchical, circular, grid)
- [ ] Topology export (PNG, SVG, PDF)
- [ ] Topology zoom/pan improvements
- [ ] Node grouping by network/site

---

## 📋 Low Priority

### Infrastructure Integrations
- [ ] MikroTik API integration
  - [ ] Device discovery
  - [ ] Interface information
  - [ ] ARP table import
  - [ ] DHCP leases import
- [ ] Proxmox API integration
  - [ ] VM discovery
  - [ ] Container (LXC) discovery
  - [ ] Resource usage monitoring
- [ ] Docker API integration
  - [ ] Container discovery
  - [ ] Network inspection
  - [ ] Port mapping import
- [ ] Home Assistant API integration
  - [ ] Device discovery
  - [ ] Entity import
- [ ] VMware integration (future)
- [ ] Kubernetes integration (future)
- [ ] UniFi integration (future)

### Search & Filtering
- [ ] Universal search API (`GET /api/v1/search`)
- [ ] Search across all entities (devices, networks, services)
- [ ] Advanced filtering UI
- [ ] Saved search filters
- [ ] Search history

### Performance
- [ ] Database query optimization
- [ ] Index analysis and optimization
- [ ] Caching layer (Redis)
- [ ] Lazy loading for large datasets
- [ ] Background jobs queue (Celery)

### PostgreSQL Deployment
- [ ] PostgreSQL migration guide
- [ ] Production database configuration
- [ ] Connection pooling
- [ ] Database backup strategy
- [ ] Migration from SQLite to PostgreSQL

### Authentication & Authorization
- [ ] User model
- [ ] Authentication system
- [ ] JWT token support
- [ ] Role-based access control (RBAC)
- [ ] Permission system
- [ ] LDAP integration (future)
- [ ] OAuth integration (future)

---

## 🔮 Future (v2.0+)

### Asset Management
- [ ] Asset tracking
- [ ] Serial numbers
- [ ] Purchase information
- [ ] Warranty tracking
- [ ] Maintenance schedules

### Rack Management
- [ ] Rack model
- [ ] Rack visualization
- [ ] Device placement
- [ ] Rack elevation diagrams
- [ ] Cable management

### Advanced Discovery
- [ ] SNMP support
- [ ] LLDP/CDP discovery
- [ ] ARP table scanning
- [ ] MAC address tracking
- [ ] VLAN discovery

### Logging & Events
- [ ] Syslog server
- [ ] Log aggregation
- [ ] Event correlation
- [ ] Log search and filtering

### Mobile & API
- [ ] Mobile-responsive UI improvements
- [ ] Native mobile app (future)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] API rate limiting
- [ ] API authentication

### Plugins & Extensions
- [ ] Plugin system architecture
- [ ] Plugin marketplace
- [ ] Custom discovery drivers
- [ ] Custom monitoring checks
- [ ] Custom alert handlers

---

## 🐛 Known Issues

### Discovery
- Job state is in-memory only (lost on restart)
- Raw ICMP requires `CAP_NET_RAW`; the scanner falls back to TCP probing otherwise
- No persistent discovery history yet
- Subnets larger than `DISCOVERY_MAX_HOSTS` (default 1024) are rejected by design

### UI
- Dashboard stats fetch multiple API endpoints instead of aggregate
- Large device lists may be slow without proper pagination
- No real-time updates (requires manual refresh)

### Monitoring
- No historical monitoring data stored
- No alerting on device status changes
- No latency/packet loss tracking yet

### Topology
- Limited layout options (single `cose` layout)
- No export functionality
- No grouping by network/site

---

## 🎯 Current Focus

**Iteration 5 (Async Discovery):** Complete — background jobs, progress/results/cancel API, ICMP probe with TCP fallback, range limits, UI progress polling.

**Next Iteration Target:** Monitoring History

**Key Goals:**
1. Store monitoring check results over time
2. Device availability timeline
3. Persist discovery job history
4. Alert system foundation

**Timeline:** 2-3 weeks

---

## 📝 Notes

- **Iteration 5** (Async Discovery) is complete: commits `cdc043c`, `5b36932`, `858747d`, `d4a3588`.
- **Port Import API** is implemented and committed (`358aa40`).
- **Monitoring Engine** is fully functional and running in production.
- **Device Types** (LXC, VM, ZigBee) are implemented and committed.
- **APScheduler** is integrated and working correctly.

---

**End of TODO**
