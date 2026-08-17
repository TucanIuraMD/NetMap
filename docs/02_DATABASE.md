# NetMap Database Design
**Version:** 1.1
**Status:** Current Implementation
**Last Updated:** 2026-08-17
**Document:** 02_DATABASE.md

---

# 1. Purpose

This document describes the logical and physical database model of NetMap.

The database is designed to store information about:

- Sites
- Networks
- Devices
- Infrastructure
- Services
- Monitoring
- History

The database must remain portable between SQLite and PostgreSQL.

---

# 2. Design Principles

The database follows these rules:

- Normalize data
- Avoid duplicated information
- No JSON fields for relational data
- Keep relationships explicit
- Every object has a unique identifier
- Every important change is stored in history

---

# 3. Core Objects

NetMap stores infrastructure as interconnected objects.

Main objects:

Site

↓

Network

↓

Device

↓

Interface

↓

IPAddress

↓

Port

↓

Service

↓

Monitoring

↓

History

---

# 4. Entity Overview

## Site

Represents a physical location.

Examples

- Home
- Office
- Data Center

One Site contains multiple Networks.

---

## Network

Represents a subnet.

Examples

192.168.88.0/24

192.168.80.0/24

Contains multiple Devices.

---

## Device

Represents any physical or logical infrastructure object.

**Supported types (current implementation):**

- router
- switch
- server
- nas
- camera
- printer
- ap (Access Point)
- esp32
- pc
- laptop
- phone
- **lxc** (LXC Container)
- **vm** (Virtual Machine)
- **zigbee** (ZigBee Device)
- unknown
- other

**Display labels:**
- lxc → "LXC"
- vm → "VM"
- zigbee → "ZigBee"
- others → capitalize first letter

Every Device belongs to one Network.

---

## Interface

Represents a network interface.

Examples

eth0

ens18

wlan0

docker0

bridge0

Stores

- MAC Address
- Speed
- MTU
- Type

---

## IPAddress

Stores

IPv4

IPv6

One Interface may have multiple IP addresses.

**Additional Fields:**
- is_primary (Boolean) — marks the primary IP address for the device (used by MonitoringService)

---

## Port

Represents TCP or UDP port.

**Fields:**

- port_number (Integer)
- protocol (String: tcp/udp)
- status (String: open/closed/filtered/unknown)
- service_id (Foreign Key to Service, nullable)
- web_scheme (String: http/https, nullable)
- display_name (String, nullable)
- description (Text)
- device_id (Foreign Key to Device)
- created_at, updated_at (DateTime)

**Relationships:**
- Belongs to Device (N:1)
- Belongs to Service (N:1, optional)

---

## Service

**Current Implementation:**

A Service represents a named network service that can be associated with Ports.

**Fields:**
- name (String: SSH, HTTP, DNS, etc.)
- description (Text)
- created_at, updated_at (DateTime)

**Relationships:**
- Has many Ports (1:N)

**Standard Services (auto-detected):**
- SSH (port 22)
- DNS (port 53)
- HTTP (port 80)
- HTTPS (port 443)
- Portainer (ports 3000, 8000, 9443)
- Proxmox (port 8006)
- Qdrant (ports 6333, 6334)
- go2rtc (ports 1984, 8554)
- Custom services (user-defined)

**Web Access:**
Ports with `web_scheme` (http/https) enable "Open" buttons in UI for quick access.

---

## Connection

**Current Implementation:**

Represents a connection/link between two devices.

**Fields:**
- source_device_id (Foreign Key to Device)
- target_device_id (Foreign Key to Device)
- source_port_id (Foreign Key to Port, nullable)
- target_port_id (Foreign Key to Port, nullable)
- source_interface_id (Foreign Key to Interface, nullable)
- target_interface_id (Foreign Key to Interface, nullable)
- connection_type (String: network, physical, logical)
- description (Text)
- is_active (Boolean, default: true)
- created_at, updated_at (DateTime)

**Relationships:**
- Belongs to source Device (N:1)
- Belongs to target Device (N:1)
- Optionally references source Port (N:1)
- Optionally references target Port (N:1)
- Optionally references source Interface (N:1)
- Optionally references target Interface (N:1)

**Notes:**
- Cascading delete: removing a Device removes its Connections
- Port and Interface references are optional (device-level, port-level, or interface-level connections)

---

## Monitoring

**Status:** Not Implemented

**Planned Fields:**

- device_id (Foreign Key to Device)
- timestamp (DateTime)
- is_online (Boolean)
- latency (Float, milliseconds)
- packet_loss (Float, percentage)
- response_time (Float, milliseconds)

---

## History

**Status:** Not Implemented

**Planned Events:**

- Device created
- Device removed
- Status changed (active/inactive)
- IP address changed
- Port changed
- Service changed
- Connection added/removed

---

# 5. Relationships

Site

1:N

Network

Network

1:N

Device

Device

1:N

Interface

Interface

1:N

IPAddress

Device

1:N

Port

Device

1:N

Service

Device

1:N

Monitoring

Device

1:N

History

---

# 6. Device Types

Supported device types

Router

Switch

Firewall

Access Point

Server

Hypervisor

Virtual Machine

Docker Host

Container

NAS

Desktop

Laptop

Phone

Tablet

Camera

Printer

IoT

Unknown

---

# 7. Device Status

Supported states

Discovered

Online

Offline

Monitoring

Disabled

Unknown

---

# 8. Monitoring History

Every monitoring cycle creates a new record.

No monitoring information is overwritten.

Historical information is never lost.

---

# 9. Discovery Rules

Discovery never inserts directly into the database.

Flow

Discovery Driver

↓

Discovery Result

↓

Merge Engine

↓

Repository

↓

Database

---

# 10. Merge Rules

Devices are matched using:

1. MAC Address

2. Serial Number

3. UUID

4. IP Address

5. Hostname

Only one Device may exist for the same physical object.

---

# 11. Database Engine

Current

SQLite

Future

PostgreSQL

No database-specific features may be used.

---

# 12. Naming Convention

Tables

snake_case

Columns

snake_case

Primary Keys

id

Foreign Keys

object_id

Indexes

idx_table_column

---

# 13. Future Tables (Version 2)

Asset

Rack

Cable

Topology Link

SNMP

Syslog

Users

Roles

Permissions

Plugin Registry

---

# 14. Database Philosophy

The database stores infrastructure.

It does not store scanner results.

Scanner results are temporary.

Infrastructure objects are permanent.

Every discovery updates existing infrastructure instead of creating duplicates.

---

End of Document