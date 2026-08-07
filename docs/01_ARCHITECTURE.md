# NetMap Architecture
**Version:** 1.0  
**Status:** Approved  
**Project:** NetMap  
**License:** MIT

---

# 1. Vision

NetMap is a modern network discovery and infrastructure monitoring platform.

The goal is not simply to scan IP addresses.

The goal is to build a complete model of the infrastructure:

- discover
- identify
- monitor
- visualize
- document

every device inside one or multiple networks.

NetMap must be lightweight, modular and easy to deploy.

---

# 2. Project Goals

Version 1.0 includes only four major modules.

1. Network Discovery

2. Monitoring

3. Topology

4. Infrastructure Discovery

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

## 5.1 Network Discovery

Responsible for discovering devices.

Drivers

- ICMP
- ARP
- Nmap
- DNS
- mDNS
- MAC Vendor

Future

- SNMP
- LLDP
- CDP

Each driver is completely independent.

Drivers NEVER write to the database.

Drivers return only discovery results.

---

## 5.2 Monitoring

Responsible for monitoring devices.

Functions

- Online
- Offline
- Ping
- Latency
- Availability
- Timeline

---

## 5.3 Topology

Responsible for visualization.

Views

Tree

Graph

Table

Dashboard

Topology is automatically rebuilt after infrastructure changes.

---

## 5.4 Infrastructure Discovery

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

HTTP

HTTPS

SSH

MQTT

SMB

FTP

DNS

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

Scheduler is independent from Flask.

Responsibilities

- Discovery
- Monitoring
- Notifications
- Cleanup

Future

Redis Queue

Celery

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

Included

✅ Network Discovery

✅ Monitoring

✅ Dashboard

✅ Device Database

✅ History

✅ Topology

✅ Docker

✅ Proxmox

✅ MikroTik

✅ Home Assistant

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

The source of truth is the infrastructure itself.

The application continuously discovers, merges, monitors and visualizes the network.

Every architecture decision must preserve:

- simplicity
- modularity
- scalability
- maintainability

No implementation may violate this document without explicit approval.

---
**End of Document**