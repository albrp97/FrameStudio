# Project Vision

> This document is the source of truth for project direction.
> Revisit when goals, users, or constraints change.

---

## Overview

Brief description of what this project does and who it is for.

## Goals

- Primary goal 1
- Primary goal 2

## Non-Goals (Out of Scope)

Things this project explicitly will NOT do.

## Key Constraints

- Technical constraints (e.g., must use a specific framework or runtime)
- Business or legal constraints (e.g., must be GDPR-compliant)
- Organisational constraints (e.g., must integrate with existing internal tooling)

## Delivery / Operational Readiness

- Supported environments and operational assumptions
- Durable quality, security, and evidence expectations
- Rollback, observability, support, or release-readiness constraints

## Development Mode

- **Selected mode:** `guided` or `automatic`
- **Canonical configuration:** `.github/aidd-config.yml`,
  `delivery.development.mode`
- **Guided:** retain configured approval gates and the functionality-only user
  validation handoff.
- **Automatic:** after the approved and verified project bootstrap, continue
  through mapping, planning, implementation, technical verification,
  automated functionality validation, review/remediation, delivery, and
  remaining phases without asking or waiting for another user response.
- **Automatic validation profile:** `rubber-duck`, model `gpt-5.6-luna`,
  reasoning effort `high`, scope `all-validation`
- **Profile authority:** `.github/aidd-config.yml`,
  `delivery.development.automatic_validation`
- **Mode-policy authority:** `.github/aidd-config.yml`,
  `delivery.mode_overrides.<mode>`; automatic execution additionally requires
  an available matching validator capability from the runtime.

## Architectural Decisions

| Decision | Rationale |
|---|---|
| Example decision | Why this choice was made |

## User Experience Principles

How the product should feel to use or extend. Write from the user's perspective.

## Success Criteria

How we measure whether the project is successful. Prefer measurable outcomes over activities.
