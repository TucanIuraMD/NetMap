# NetMap REST API
**Version:** 1.1
**Status:** Current Implementation
**Last Updated:** 2026-08-17
**Document:** 03_API.md

---

# 1. Purpose

This document defines the REST API specification for NetMap.

The API is the single interface between:

- Web UI
- Mobile clients (future)
- CLI tools
- External integrations
- Automation

All application logic must be exposed through the API.

The frontend never accesses the database directly.

---

# 2. API Principles

REST API

JSON only

UTF-8

Versioned

Stateless

Predictable

---

# 3. Base URL

/api/v1

Example

GET

/api/v1/devices

---

# 4. Content Type

Request

Content-Type:

application/json

Response

Content-Type:

application/json

---

# 5. Standard Response

Successful response

```json
{
    "success": true,
    "data": {},
    "meta": {
        "timestamp": "2026-08-08T10:30:00Z"
    }
}
```

---

Error response

```json
{
    "success": false,
    "error": {
        "code": "DEVICE_NOT_FOUND",
        "message": "Device not found"
    }
}
```

---

# 6. HTTP Status Codes

200 OK

201 Created

204 No Content

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

409 Conflict

422 Validation Error

500 Internal Server Error

---

# 7. Authentication

Version 1

Local authentication only.

Future

JWT

LDAP

OAuth

---

# 8. API Resources

**Implemented:**

/api/v1/sites

/api/v1/networks

/api/v1/devices

/api/v1/interfaces

/api/v1/ip-addresses

/api/v1/services

/api/v1/ports

/api/v1/connections

/api/v1/topology

/api/v1/networks/<id>/discover

/api/v1/imports/ports (port import)

**Planned:**

/api/v1/monitoring/status

/api/v1/monitoring/history

/api/v1/monitoring/check

/api/v1/monitoring/stats

/api/v1/discovery/status

/api/v1/discovery/results

/api/v1/history

/api/v1/settings

/api/v1/stats

---

# 9. Sites

GET

/sites

Return all sites.

---

GET

/sites/{id}

Return one site.

---

POST

/sites

Create site.

---

PUT

/sites/{id}

Update site.

---

DELETE

/sites/{id}

Delete site.

---

# 10. Networks

GET

/networks

GET

/networks/{id}

POST

/networks

PUT

/networks/{id}

DELETE

/networks/{id}

---

# 11. Devices

GET /devices

**Current Implementation — API-side filtering/sorting/pagination:**

**Query Parameters:**

- `search=<term>` — Search by name, hostname, or IP address
- `network_id=<id>` — Filter by network
- `device_type=<type>` — Filter by device type (router, switch, server, lxc, vm, etc.)
- `is_active=<true|false>` — Filter by active status (availability monitoring updates this field)
- `status=<active|inactive>` — Alias for is_active filter
- `links=<with|without>` — Filter by connection presence
- `sort=<field>` — Sort by field: id, name, display_name, hostname, device_type, is_active, created_at, updated_at
- `order=<asc|desc>` — Sort order (default: asc)
- `page=<n>` — Page number (default: 1)
- `per_page=<n>` — Results per page (default: 50, max: 500)

**Examples:**

```
GET /devices?page=1&per_page=50
GET /devices?is_active=true
GET /devices?network_id=2
GET /devices?device_type=server
GET /devices?search=proxmox
GET /devices?sort=hostname&page=2
```

**Response:**

```json
{
  "devices": [...],
  "pagination": {
    "page": 1,
    "per_page": 50,
    "total": 41,
    "pages": 1
  }
}
```

---

GET /devices/{id}

Returns device details with relationships (network, interfaces, ip_addresses, ports, connections).

---

POST /devices

Create a new device.

---

PUT /devices/{id}

Update device.

---

DELETE /devices/{id}

Delete device (cascades to interfaces, ports, connections).

---

# 12. Interfaces

GET

/interfaces

GET

/interfaces/{id}

POST

/interfaces

PUT

/interfaces/{id}

DELETE

/interfaces/{id}

---

# 13. IP Addresses

GET

/ip-addresses

GET

/ip-addresses/{id}

POST

/ip-addresses

PUT

/ip-addresses/{id}

DELETE

/ip-addresses/{id}

---

# 14. Services

GET

/services

GET

/services/{id}

POST

/services

PUT

/services/{id}

DELETE

/services/{id}

---

# 15. Ports

GET

/ports

GET

/ports/{id}

POST

/ports

PUT

/ports/{id}

DELETE

/ports/{id}

---

# 16. Connections

GET

/connections

Return device connections.

**Current Implementation — validation, duplicate protection, filters, pagination:**

**Query Parameters:**

- `device_id=<id>` — Filter by device (connection is returned when the device is the source or the target)
- `is_active=<true|false>` — Filter by active status
- `connection_type=<type>` — Filter by type (network, ethernet, fiber, wifi, virtual, other)
- `page=<n>` — Page number (default: 1)
- `per_page=<n>` — Results per page (default: 50, max: 500; alias `page_size`)

**Backward compatibility:** a request with no query parameters at all returns a bare JSON array of all connections (legacy behavior). Any query parameter switches to the paginated envelope:

```json
{
  "items": [...],
  "page": 1,
  "per_page": 50,
  "total": 12,
  "total_pages": 1
}
```

---

GET

/connections/{id}

Return one connection.

---

POST

/connections

Create a connection between two devices.

Request example

```json
{
  "source_device_id": 1,
  "target_device_id": 3,
  "connection_type": "ethernet",
  "source_interface_id": 5,
  "target_interface_id": 7,
  "source_port_id": 10,
  "target_port_id": 12,
  "description": "Backbone link",
  "is_active": true
}
```

**Validation (400 Bad Request):**

- JSON body is required
- `source_device_id` and `target_device_id` are required
- Source and target devices must differ
- `connection_type` must be one of: network, ethernet, fiber, wifi, virtual, other (default: network)
- Ports and interfaces must belong to their respective device
- Source and target interfaces must differ

**Validation (404 Not Found):**

- Source or target device does not exist
- Referenced port or interface does not exist

**Duplicate protection (409 Conflict):**

A connection is considered a duplicate when the device pair plus the optional interface/port endpoints match an existing connection. `connection_type` is deliberately not part of the identity, so the same physical link cannot be recorded twice under different types. Duplicates are rejected with `409 Conflict` ("Connection already exists"). A database unique constraint on the endpoint pair enforces the same rule at the schema level.

---

PUT

/connections/{id}

Update a connection. Accepts any subset of the connection fields; every referenced device, port and interface is validated and the duplicate check is re-run excluding the updated connection.

---

DELETE

/connections/{id}

Delete a connection.

Connection fields

- `source_device_id` — required
- `target_device_id` — required
- `connection_type` — network, ethernet, fiber, wifi, virtual, other
- `source_interface_id` / `target_interface_id` — optional
- `source_port_id` / `target_port_id` — optional
- `description`
- `is_active`

Deleting a device also removes its associated connections (cascade).

---

# 17. Topology

GET

/topology

Return the device/connection graph consumed by the `/topology` page.

**Current Implementation:**

Response shape:

```json
{
  "nodes": [...],
  "edges": [...]
}
```

**Nodes** are devices. Each node `data` block contains:

- `id` — `"device-{id}"`
- `deviceId` — numeric device id
- `label` — `display_name` or `name`
- `isActive` — boolean
- `linked` — true when the device has at least one connection inside the filtered node set
- `device` — full device record
- `interfaces` — interfaces, each with its nested `ip_addresses`
- `ports` — ports

**Edges** are derived strictly from existing Connection records — no synthetic links are ever fabricated, and every connection maps to exactly one edge. An edge is included only when both endpoints are part of the filtered node set. Each edge `data` block contains:

- `id` — `"conn-{id}"`
- `source` / `target` — `"device-{id}"` node references
- `type` — connection type
- `label` — interface-based label (e.g. `eth0 → eth1`); generic interface names are rendered as `iface {id}`
- `connection` — full connection record (source/target device, interface and port ids)

**Query Parameters:**

- `network_id=<id>` — Include devices of a single network
- `device_type=<type>` — Include devices with the exact device type
- `status=<active|inactive>` — Filter by device active status

**Note:** the server edge `label` is interface-based only. The client (`static/js/topology.js`) builds the final label, adding the port when available (e.g. `eth0 · 80/tcp (HTTP) → eth0 · 80/tcp (HTTP)`).

---

# 18. Discovery

**Current Implementation:**

POST /api/v1/networks/{id}/discover

Start network discovery (synchronous, blocking).

**Request:**
```json
{}
```

**Response:**
```json
{
  "devices": [...],
  "discovered": 5,
  "updated": 3,
  "inactive": 2
}
```

**Discovery Method:**
- TCP port scanning (ports: 22, 23, 53, 80, 81, 443, 445, 554, 8080, 8443)
- DNS hostname resolution
- Open port detection
- Device/Interface/IPAddress/Port creation and synchronization
- Inactive device marking

**Limitations:**
- Synchronous execution (blocks HTTP request until completion)
- No progress indication
- May timeout on large networks

**Planned:**

POST /api/v1/discovery/start — Start async discovery (background task)

POST /api/v1/discovery/stop — Stop running discovery

GET /api/v1/discovery/status — Check discovery status and progress

GET /api/v1/discovery/results — Get latest discovery results

---

# 19. Monitoring

**Status:** Implemented (background service)

**Current Implementation:**

Monitoring runs automatically in the background via APScheduler. Device availability is checked every 5 minutes (configurable) and `Device.is_active` is updated automatically.

**Configuration:**
- `MONITORING_ENABLED` — Enable/disable monitoring (default: true)
- `MONITORING_INTERVAL_MINUTES` — Check interval in minutes (default: 5)

**Monitoring Logic:**
- ICMP ping (primary method)
- TCP probe to known open ports (fallback)
- Updates `Device.is_active` field

**Planned Endpoints:**

GET /monitoring/status — Get monitoring service status

GET /monitoring/history — Get monitoring check history

POST /monitoring/check — Trigger immediate check for specific device

GET /monitoring/stats — Get monitoring statistics

---

# 20. History

GET

/history

Supports

device

date

event

site

Example

/history?device=15

/history?event=offline

---

# 21. Settings

GET

/settings

PUT

/settings

---

# 22. Search

Universal search.

GET

/search?q=proxmox

Returns

Devices

Networks

Sites

Services

---

# 23. Pagination

Supported by all list endpoints.

Example

?page=1

&page_size=50

Default

50

Maximum

500

---

# 24. Filtering

Examples

?status=online

?type=server

?site=1

?network=2

?vendor=Dell

?hostname=nas

Multiple filters are allowed.

---

# 25. Sorting

Examples

?sort=hostname

?sort=ip

?sort=last_seen

Descending

?sort=-last_seen

---

# 26. API Versioning

Current

/api/v1

Future

/api/v2

Older versions remain supported whenever possible.

---

# 27. Error Codes

DEVICE_NOT_FOUND

NETWORK_NOT_FOUND

SITE_NOT_FOUND

INVALID_REQUEST

VALIDATION_ERROR

DISCOVERY_RUNNING

DISCOVERY_STOPPED

MONITORING_RUNNING

MONITORING_STOPPED

INTERNAL_ERROR

---

# 28. Performance

All list endpoints must support

Pagination

Filtering

Sorting

Lazy loading

No endpoint may return unlimited data.

---

# 29. Logging

Every API request is logged.

Log

Timestamp

Endpoint

Method

Status

Execution Time

IP Address

---

# 30. Future API

Reserved for Version 2

/api/v2/assets

/api/v2/snmp

/api/v2/plugins

/api/v2/users

/api/v2/auth

---

# 31. API Philosophy

The API is the public interface of NetMap.

Every feature must be available through the API.

The Web UI is only a client of the REST API.

Business logic belongs to Services.

Database access belongs to Repositories.

The API must remain stable and backward compatible.

---

End of Document