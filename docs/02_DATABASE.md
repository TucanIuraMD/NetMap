# NetMap Database Design
**Version:** 1.0
**Status:** Approved
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

Supported types

Router

Switch

Access Point

Server

Hypervisor

Virtual Machine

Container

NAS

Desktop

Laptop

Phone

Camera

IoT

Printer

Unknown

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

---

## Port

Represents TCP or UDP port.

Stores

Port Number

Protocol

Status

Description

---

## Service

Examples

SSH

HTTP

HTTPS

MQTT

FTP

DNS

SMB

NTP

Can be linked to multiple Ports.

---

## Monitoring

Stores monitoring samples.

Fields

Timestamp

Online

Latency

Packet Loss

Response Time

---

## History

Stores all important events.

Examples

Device created

Device removed

Status changed

IP changed

Port changed

Service changed

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