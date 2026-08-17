# NetMap Architecture
**Version:** 1.1
**Status:** Current Implementation
**Last Updated:** 2026-08-17
**Project:** NetMap
**License:** MIT

---

# 1. Vision

NetMap is a network inventory and infrastructure access platform.

The primary goal is to maintain a clear, practical inventory of network devices and provide a fast interface for accessing their web services.

NetMap must:

- discover devices
- identify devices and their network information
- allow users to rename devices and ports
- maintain interfaces, IP addresses and ports
- provide clickable access to web services
- monitor device availability
- detect newly appearing devices
- allow connections between devices to be documented
- visualize the infrastructure

NetMap must be lightweight, modular and easy to deploy.

---

# 2. Project Goals

The primary product functions are:

1. Device Inventory

2. Network Discovery

3. Quick Web Service Access

4. Availability Monitoring

5. Device Connections

6. Topology and Visualization

Infrastructure Discovery integrations are an extension of the inventory.

Everything else belongs to Version 2 or later.

---

# 3. Supported Infrastructure

Initially NetMap manages two sites.

## Site 1

Network

192.168.88.0/24

Core Devices

- MikroTik
- Proxmox

---

## Site 2

Network

192.168.80.0/24

Core Devices

- MikroTik
- Proxmox

The architecture must support unlimited future sites.

---

# 4. Architecture Overview

```
                   Web UI

                      │

                 REST API

                      │

              Application Services

                      │

        ┌─────────────┴─────────────┐

        │                           │

 Discovery Engine            Monitoring Engine

        │                           │

        └─────────────┬─────────────┘

                      │

                 Merge Engine

                      │

                 Normalizer

                      │

                 Repository

                      │

                 SQLAlchemy

                      │

                 SQLite / PostgreSQL
```

---

# 5. Main Modules

## 5.1 Device Inventory

The inventory is the core of NetMap.

It stores:

- Sites
- Networks
- Devices
- Interfaces
- IP addresses
- Ports

Users can assign display names to devices and ports without changing discovered technical identifiers.

Ports may contain web access settings and a generated web URL.

---

## 5.2 Network Discovery

Responsible for discovering devices.

**Current Implementation**

- TCP port scanning (NetworkScanner)
- DNS hostname resolution
- Open port detection
- Device synchronization (DiscoveryService)
- Synchronous execution (blocking request)

**Scan Ports:** 22, 23, 53, 80, 81, 443, 445, 554, 8080, 8443

**Architecture:**
- NetworkScanner — TCP scan implementation (does not write to DB)
- DiscoveryService — synchronizes scan results with database
- Creates/updates Device, Interface, IPAddress, Port records
- Marks missing devices as inactive

**Planned Enhancements:**

- Async/background discovery
- Discovery progress API
- Discovery status tracking
- ICMP discovery
- ARP table scanning
- SNMP discovery
- LLDP/CDP discovery

Discovery components NEVER write to the database directly.

Discovery returns only scan results.

Database synchronization is handled by DiscoveryService.

---

## 5.3 Monitoring

**Status:** Implemented

**Current Functions:**

- Online/Offline status
- ICMP Ping (primary method)
- TCP fallback (to known open ports)
- Automatic Device.is_active updates
- Configurable monitoring interval

**Architecture:**
- APScheduler for periodic checks (default: every 5 minutes)
- MonitoringService for device availability checks
- ICMP ping primary, TCP fallback to device's open ports or standard ports
- Update Device.is_active based on reachability results
- Reloader-safe scheduler initialization (Flask debug mode compatible)
- Configurable via MONITORING_ENABLED and MONITORING_INTERVAL_MINUTES

**Planned Enhancements:**
- Latency measurement
- Packet loss tracking
- Response time tracking
- Monitoring history storage
- Availability timeline
- Alert system integration

---

## 5.4 Topology

Responsible for visualization.

Views

Tree

Graph

Table

Dashboard

Topology is automatically rebuilt after infrastructure changes.

---

## 5.5 Infrastructure Discovery

Supported integrations

- MikroTik
- Proxmox
- Docker
- Home Assistant

Future

- VMware
- Kubernetes
- UniFi

---

# 6. Discovery Flow

Drivers never create devices.

Drivers only collect information.

```
ICMP

↓

DiscoveryResult

ARP

↓

DiscoveryResult

Nmap

↓

DiscoveryResult

Docker

↓

DiscoveryResult

Proxmox

↓

DiscoveryResult

↓

Merge Engine

↓

RawDevice

↓

Normalizer

↓

Device

↓

Repository

↓

Database
```

This is one of the most important rules of the project.

---

# 7. Merge Engine

Merge Engine combines information from multiple sources.

Example

ICMP

returns

192.168.88.15

↓

ARP

returns

AA:BB:CC:DD

↓

Nmap

returns

Linux

↓

Docker

returns

18 Containers

↓

Proxmox

returns

Hypervisor

↓

Result

One Device

Never duplicate devices.

Matching priority

1. MAC Address

2. Serial Number

3. UUID

4. IP Address

5. Hostname

---

# 8. Core Entities

## Site

Physical location.

Example

Home

Office

---

## Network

Subnet.

Example

192.168.88.0/24

---

## Device

Physical device.

Examples

Router

Switch

Server

NAS

Camera

Printer

ESP32

PC

Laptop

Phone

---

## Virtual Machine

Virtual machine running on Hypervisor.

---

## Container

Docker or LXC container.

---

## Application

Software running inside VM or Container.

Examples

Immich

Grafana

MQTT

Home Assistant

Ollama

---

## Interface

Physical or virtual network interface.

---

## IP Address

IPv4

IPv6

---

## Port

TCP

UDP

---

## Service

Service records may be associated with ports.

Automatic Service Detection is NOT a required project function.

---

## History

Stores every change.

---

## Monitoring

Stores monitoring data.

---

# 9. Device Hierarchy

```
Site

↓

Network

↓

Router

↓

Switch

↓

Server

↓

Proxmox

↓

VM

↓

Docker Host

↓

Container

↓

Application

↓

Service
```

---

# 10. Repository Pattern

Application never works directly with SQLAlchemy.

```
Service

↓

Repository

↓

SQLAlchemy

↓

Database
```

---

# 11. Discovery Drivers

Every driver implements

```
DiscoveryDriver
```

Functions

discover()

supports()

weight()

name()

Drivers are loaded automatically.

---

# 12. Driver Manager

Drivers are automatically discovered.

```
drivers/

icmp.py

arp.py

nmap.py

dns.py

mdns.py

mikrotik.py

proxmox.py

docker.py

homeassistant.py
```

No manual registration.

---

# 13. Event Bus

Every important action generates an event.

Example

```
Device Offline

↓

History

↓

Dashboard

↓

Notification

↓

Topology Update
```

---

# 14. Scheduler

**Status:** Implemented (APScheduler)

Scheduler runs background periodic tasks.

**Current Implementation:**
- APScheduler (BackgroundScheduler)
- Reloader-safe initialization (Flask debug mode compatible)
- Daemon mode for automatic cleanup
- Job deduplication (coalesce=True, max_instances=1)

**Current Responsibilities:**

- Monitoring — Device availability checks (every 5 minutes)

**Planned Responsibilities:**

- Async Discovery execution
- Cleanup tasks (old logs, inactive devices)
- Scheduled reports
- Alert processing

**Future:**

Redis Queue

Celery (for heavy workloads)

---

# 15. Database

Version 1

SQLite

Future

PostgreSQL

Database must remain portable.

No PostgreSQL specific data types.

---

# 16. REST API

Versioned API.

```
/api/v1/
```

Resources

/sites

/networks

/devices

/discovery

/monitoring

/topology

/history

/settings

---

# 17. Web UI

Pages

Dashboard

Sites

Networks

Devices

Discovery

Monitoring

Topology

Settings

Dark theme is default.

---

# 18. Coding Standards

Python 3.12

PEP8

Type Hints

Docstrings

Logging

Black

Ruff

Pytest

---

# 19. Development Rules

Never generate huge files.

Maximum file size

500 lines

One class per file.

One responsibility per class.

No duplicated code.

No business logic inside Flask routes.

No SQL inside templates.

Drivers never know about SQLAlchemy.

Repositories never know about Flask.

---

# 20. Version 1 Scope

**Completed Functions**

✅ Device inventory

✅ Network discovery (TCP scanning)

✅ Interface and IP inventory

✅ Port and Service inventory

✅ Device and port display names

✅ Quick web-service access (Open buttons)

✅ Device connections

✅ Topology visualization (Cytoscape.js)

✅ Standard service detection

✅ API-side filtering/sorting/pagination

✅ Device Types (including LXC, VM, ZigBee)

✅ Availability monitoring (APScheduler-based, ICMP + TCP fallback)

✅ Port Import API (bulk operations)

**Planned Functions**

⏳ Async discovery (background tasks with progress API)

⏳ Monitoring history (store availability checks over time)

⏳ Alert system (notifications on device status changes)

⏳ Dashboard stats API (aggregate endpoint)

⏳ Infrastructure integrations (MikroTik, Proxmox, Docker)

---

Excluded

❌ Asset Management

❌ Rack Management

❌ LDAP

❌ Active Directory

❌ SNMP Traps

❌ Syslog Server

❌ Kubernetes

❌ Multi-user RBAC

❌ Plugin Marketplace

---

# 21. Roadmap

Phase 1

Foundation

Phase 2

Discovery

Phase 3

Monitoring

Phase 4

Topology

Phase 5

Infrastructure Discovery

Phase 6

Version 1 Release

---

# 22. Project Philosophy

NetMap is **not** an IP scanner.

NetMap is **not** a monitoring-only solution.

NetMap is an Infrastructure Discovery Platform.

The source of truth is the infrastructure inventory maintained by NetMap.

The application continuously discovers, merges, monitors and visualizes the network.

Every architecture decision must preserve:

- simplicity
- modularity
- scalability
- maintainability

No implementation may violate this document without explicit approval.

---
**End of Document**