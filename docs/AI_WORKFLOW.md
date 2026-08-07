# AI Workflow
**Document:** AI_WORKFLOW.md
**Version:** 1.0
**Status:** Approved

---

# Purpose

This document defines how AI assistants participate in the NetMap development process.

The goal is to ensure that multiple AI models work together consistently without changing the approved architecture or duplicating work.

---

# Source of Truth

The GitHub repository is the single source of truth.

Every AI must use the latest version of the repository before starting work.

Repository:

https://github.com/TucanIuraMD/NetMap

---

# Required Reading

Before implementing any code, every AI must read:

1. docs/01_ARCHITECTURE.md
2. docs/02_DATABASE.md
3. docs/03_API.md
4. docs/04_CODING_STANDARDS.md
5. docs/99_AI_RULES.md
6. Current Development Task

No implementation is allowed without reading these documents.

---

# AI Roles

## ChatGPT

Role

Lead Architect

Responsibilities

- Architecture
- Code Review
- Planning
- Documentation
- Project Management
- Integration Review

---

## Claude

Role

Backend Developer

Responsibilities

- Flask
- SQLAlchemy
- Services
- Repositories
- REST API

---

## DeepSeek

Role

System Architect

Responsibilities

- Architecture validation
- Database design
- Performance review
- Refactoring proposals

---

## Kimi

Role

Frontend Developer

Responsibilities

- Bootstrap
- HTMX
- Templates
- UX
- Dashboard

---

## Qwen

Role

Algorithm Engineer

Responsibilities

- Discovery
- Merge Engine
- Network algorithms
- Optimization

---

# Development Process

Every task follows the same workflow.

Read Documentation

↓

Understand Task

↓

Implement Only Assigned Scope

↓

Run Tests

↓

Update Documentation

↓

Commit

↓

Push

↓

Wait for Review

No AI starts the next task without approval.

---

# Branch Strategy

main

Stable releases only.

develop

Current development.

feature/*

One feature per branch.

Examples

feature/foundation

feature/database

feature/discovery

feature/mikrotik

---

# Commit Format

Examples

feat(api): add health endpoint

feat(database): create device model

fix(discovery): correct arp parser

docs(api): update endpoints

refactor(repository): simplify queries

---

# Pull Request Rules

Every Pull Request must include

Purpose

Changes

Testing

Documentation Updated

Checklist

---

# Documentation Rules

Architecture changes require approval.

Database changes require approval.

API changes require approval.

Every completed task updates

CHANGELOG.md

TODO.md

if applicable.

---

# AI Restrictions

AI must never

- redesign architecture
- rename approved modules
- introduce new frameworks
- change the database model
- change REST API contracts
- add dependencies without approval

---

# Allowed Improvements

AI may suggest

- performance improvements
- code simplification
- bug fixes
- documentation improvements
- refactoring

Suggestions must be clearly separated from implementation.

---

# Code Review

Every completed task must be reviewed before merging.

Review includes

- Coding Standards
- Architecture
- API compatibility
- Database compatibility
- Documentation
- Tests

---

# Project Philosophy

The project grows by small iterations.

One task.

One implementation.

One review.

One merge.

No AI develops multiple milestones simultaneously.

---

End of Document