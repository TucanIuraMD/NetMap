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
- [x] Port Import API endpoint (implemented, not committed)
- [x] Bulk port import service
- [x] Device resolution (ID/IP/name/hostname)
- [x] Duplicate prevention
- [x] Standard service mapping

---

## 🔄 In Progress

### Documentation
- [ ] Commit Monitoring Engine changes
- [ ] Commit Port Import API
- [ ] Commit Device Types updates
- [ ] Commit UI polish changes

---

## 📋 High Priority (Next Iteration)

### Async Discovery
- [ ] Background discovery tasks (non-blocking)
- [ ] Discovery status API (`GET /api/v1/discovery/status`)
- [ ] Discovery progress tracking
- [ ] Discovery results API (`GET /api/v1/discovery/results`)
- [ ] Discovery start/stop/cancel endpoints
- [ ] UI polling for discovery progress
- [ ] Discovery history

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
- [ ] Multiple layout algorithms (hierarchical, circular, grid)
- [ ] Topology filters (by network, device type, status)
- [ ] Topology export (PNG, SVG, PDF)
- [ ] Topology zoom/pan improvements
- [ ] Node grouping by network/site
- [ ] Edge labels (connection type, bandwidth)

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
- Discovery is synchronous and blocks the request until completion
- Large subnets (/16 or larger) may cause timeout issues
- No progress indication during discovery

### UI
- Dashboard stats fetch multiple API endpoints instead of aggregate
- Large device lists may be slow without proper pagination
- No real-time updates (requires manual refresh)

### Monitoring
- No historical monitoring data stored
- No alerting on device status changes
- No latency/packet loss tracking yet

### Topology
- Limited layout options
- No filtering or grouping
- No export functionality

---

## 🎯 Current Focus

**Iteration 4 Target:** Async Discovery + Monitoring History

**Key Goals:**
1. Non-blocking discovery with progress API
2. Store monitoring check results over time
3. Device availability timeline
4. Alert system foundation

**Timeline:** 2-3 weeks

---

## 📝 Notes

- **Port Import API** is implemented but not committed. Needs testing and documentation before merge.
- **Monitoring Engine** is fully functional and running in production.
- **Device Types** (LXC, VM, ZigBee) are implemented but not committed.
- **APScheduler** is integrated and working correctly.

---

**End of TODO**
