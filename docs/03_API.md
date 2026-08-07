# NetMap REST API
**Version:** 1.0
**Status:** Approved
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

/api/v1/sites

/api/v1/networks

/api/v1/devices

/api/v1/interfaces

/api/v1/ip-addresses

/api/v1/services

/api/v1/ports

/api/v1/discovery

/api/v1/monitoring

/api/v1/history

/api/v1/settings

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

GET

/devices

Supports

search

filter

sort

pagination

Example

GET

/devices?page=1

GET

/devices?status=online

GET

/devices?site=1

GET

/devices?type=router

GET

/devices?hostname=proxmox

---

GET

/devices/{id}

---

POST

/devices

---

PUT

/devices/{id}

---

DELETE

/devices/{id}

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

# 16. Discovery

POST

/discovery/start

Start discovery.

---

POST

/discovery/stop

Stop discovery.

---

GET

/discovery/status

Current status.

---

GET

/discovery/results

Latest results.

---

# 17. Monitoring

POST

/monitoring/start

---

POST

/monitoring/stop

---

GET

/monitoring/status

---

GET

/monitoring/history

---

# 18. History

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

# 19. Settings

GET

/settings

PUT

/settings

---

# 20. Search

Universal search.

GET

/search?q=proxmox

Returns

Devices

Networks

Sites

Services

---

# 21. Pagination

Supported by all list endpoints.

Example

?page=1

&page_size=50

Default

50

Maximum

500

---

# 22. Filtering

Examples

?status=online

?type=server

?site=1

?network=2

?vendor=Dell

?hostname=nas

Multiple filters are allowed.

---

# 23. Sorting

Examples

?sort=hostname

?sort=ip

?sort=last_seen

Descending

?sort=-last_seen

---

# 24. API Versioning

Current

/api/v1

Future

/api/v2

Older versions remain supported whenever possible.

---

# 25. Error Codes

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

# 26. Performance

All list endpoints must support

Pagination

Filtering

Sorting

Lazy loading

No endpoint may return unlimited data.

---

# 27. Logging

Every API request is logged.

Log

Timestamp

Endpoint

Method

Status

Execution Time

IP Address

---

# 28. Future API

Reserved for Version 2

/api/v2/assets

/api/v2/snmp

/api/v2/topology

/api/v2/plugins

/api/v2/users

/api/v2/auth

---

# 29. API Philosophy

The API is the public interface of NetMap.

Every feature must be available through the API.

The Web UI is only a client of the REST API.

Business logic belongs to Services.

Database access belongs to Repositories.

The API must remain stable and backward compatible.

---

End of Document