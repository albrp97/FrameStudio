# PHASE-002 Export Planning Policy

**Status:** confirmed for TICKET-010 implementation  
**Phase:** PHASE-002  
**Feature:** FEAT-005  
**Ticket:** TICKET-010  
**Objective:** OBJ-001  
**Scope:** SCOPE-001  
**Last updated:** 2026-08-21

## Fast stream-copy route

The planner may select `stream-copy` only when all of these conditions hold:

- The edit is non-empty and its source duration matches the project timeline.
- The source container reports one of `mp4`, `mov`, `matroska`, or `mkv`.
- The source video codec is H.264.
- The source audio is absent or AAC.
- Every internal retained-segment boundary is aligned to a probed keyframe.
- The destination is different from the source.

The planner returns the retained segments, expected edited duration, and an
explanation. No output is written by the planner.

## Fallback route

When any fast-route condition fails, the planner returns `fallback` with every
reason. The initial validated output policy is:

- MP4 container.
- H.264 video through `libx264`.
- AAC audio when the source contains audio.
- `yuv420p` video pixel format.
- Source dimensions and the project timebase remain the output target unless
  the execution layer reports an explicit incompatibility.

The fallback route is not a silent success path. Unsupported or ambiguous
project/source state, an empty edit, a destination equal to the source, and
unavailable probing tools remain planning errors before command execution.

## Timing limitations

Keyframe alignment is checked using FFprobe JSON frame data. A stream-copy
plan does not claim frame-accurate cuts for non-keyframe boundaries. Such
edits use the fallback route, which is responsible for validating final
duration and stream presence.

