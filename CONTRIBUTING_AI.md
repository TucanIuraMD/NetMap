# CONTRIBUTING_AI.md

# AI Contribution Guide

Welcome to the NetMap project.

This project is designed for collaborative development between humans and AI assistants.

Every AI participating in development must follow these rules.

---

# Mission

Your task is not to redesign the project.

Your task is to implement approved features safely, consistently and incrementally.

The architecture is considered the source of truth.

---

# Before Writing Code

Read, in this exact order:

1. README.md

2. docs/01_ARCHITECTURE.md

3. docs/02_DATABASE.md

4. docs/03_API.md

5. docs/04_CODING_STANDARDS.md

6. docs/99_AI_RULES.md

7. Current Development Task

Never skip this step.

---

# Source of Truth

The GitHub repository is the only source of truth.

Do not rely on previous conversations.

Do not rely on memory.

Always use the latest repository state.

---

# Development Philosophy

Small iterations.

One task.

One feature.

One commit.

One review.

Never implement multiple milestones simultaneously.

---

# What You MAY Do

Implement approved tasks.

Fix bugs.

Improve readability.

Improve performance.

Refactor without changing behavior.

Improve documentation.

Write tests.

Suggest improvements.

---

# What You MUST NOT Do

Do not redesign architecture.

Do not rename approved modules.

Do not change database schema.

Do not change REST API contracts.

Do not introduce new frameworks.

Do not introduce new dependencies without approval.

Do not remove existing functionality.

Do not implement features outside the current task.

---

# Coding Standards

Follow

docs/04_CODING_STANDARDS.md

at all times.

---

# Documentation

Every completed feature updates documentation if required.

Documentation is as important as source code.

---

# If Something Is Wrong

Do not silently change it.

Explain

why

what

impact

proposed solution

Wait for approval.

---

# AI Roles

ChatGPT

Lead Architect

Claude

Backend

DeepSeek

Architecture

Database

Kimi

Frontend

Qwen

Algorithms

Every AI respects the work of other AI assistants.

---

# Commit Rules

Every commit must implement exactly one logical change.

Commit messages follow

type(scope): description

Examples

feat(api): add health endpoint

fix(database): correct foreign key

docs(api): update endpoint documentation

---

# Pull Requests

Every Pull Request must contain

Purpose

Summary

Testing

Documentation

Known limitations

---

# Goal

The goal is not to generate code.

The goal is to build a maintainable project.

Quality is always more important than quantity.

---

End of Document