# PHASE-002 Cut Semantics

**Status:** confirmed for TICKET-007 implementation  
**Phase:** PHASE-002  
**Feature:** FEAT-004  
**Ticket:** TICKET-007  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Last updated:** 2026-08-21

## Decision

The first cutting implementation uses source-time coordinates and
non-destructive, half-open intervals:

- A source with duration `D` starts as one segment `[0, D)`.
- Each segment has a stable identifier, a start, an end, and a deleted flag.
- A split position must be strictly inside one segment. Positions at a
  segment boundary, at zero, or at the source endpoint are invalid because
  they would create an empty segment.
- Splitting preserves the deleted flag of the segment being split.
- Deleted segments remain in source order and retain their source boundaries.
- The edited timeline initially follows source order and ripples retained
  segments together without preserving gaps created by deletion. Explicit
  block movement may change timeline order while each segment keeps its
  source-time interval.
- Copying a one-source block preserves its source interval while pasting
  creates a fresh timeline block at the selected insertion point. The source
  duration remains unchanged while the composed timeline duration grows.
- Edited duration is the sum of the durations of retained segments. It may be
  zero when every segment is deleted; export must reject an empty edit.
- The source reference and source media are never changed by segment edits.

## Frame and timestamp limitations

The segment model stores requested source-time boundaries and does not claim
that every boundary is frame-accurate or independently decodable. Variable
frame-rate inputs, timestamp discontinuities, and keyframe restrictions are
reported by the playback/export layers. The export planner is responsible for
deciding whether a boundary can use stream copy or requires a validated
fallback.

## Verification

The model must validate that source intervals provide complete coverage,
allowing intentional overlap from pasted blocks, timeline placements are
contiguous when explicit movement or paste has occurred, and segment
identifiers are unique. Invalid operations must fail before mutation so the
last valid timeline remains available.
