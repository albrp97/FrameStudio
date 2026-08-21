# Editor Foundation Decision

**Decision ID:** DECISION-001
**Objective:** OBJ-001
**Scope:** SCOPE-001
**Phase:** PHASE-001
**Feature:** FEAT-001, FEAT-002, FEAT-003
**Ticket:** TICKET-001
**Status:** confirmed for implementation
**Decision date:** 2026-08-21
**Evidence:** `evidence/selecting-editor-foundation.md`

## Selected foundation

- **Application runtime:** Python 3.14 with PyGObject.
- **GUI toolkit:** GTK 4.
- **Playback engine:** The existing FFmpeg 9.0.1 command through a managed
  subprocess that emits real-time RGBA frames through a pipe.
- **Frame presentation:** RGBA frames pulled from the FFmpeg pipe and
  presented as GTK 4 `Gdk.MemoryTexture` values in a `Gtk.Picture`.
- **Media inspection:** The existing local `ffprobe` command through a
  small, structured Python adapter.
- **Project format:** Versioned UTF-8 JSON stored separately from source
  media, with atomic temporary-file replacement.

This keeps the editor domain in Python, reuses FFmpeg/ffprobe, provides a
GLib-integrated playback loop, and avoids making a second media-processing
implementation in the existing scripts. The FFmpeg pipe is selected because
the target workstation's GStreamer installation lacks the demuxer plugins
needed to open the generated MP4 probe fixture.

## Runtime and setup contract

The target workstation must provide:

- Python 3.14 with `gi` and GTK 4.
- FFmpeg filters and rawvideo pipe support.
- `ffmpeg` and `ffprobe`.

The initial setup is system-package based rather than a Python wheel-only
installation because GTK, GStreamer, and PyGObject are native runtime
dependencies. A future packaging ticket can add a launcher or package once
the editor surface is stable.

## Playback and timing limitations

- The initial presenter is CPU-visible frame transfer through a raw FFmpeg
  pipe, not a zero-copy GPU sink.
- Seeking restarts the decoder at the requested position and is therefore
  approximate for some variable-frame-rate or keyframe-heavy sources.
- The preview drops stale frames when the UI cannot consume them quickly
  enough; project state remains separate from playback state.
- Missing or unavailable FFmpeg capabilities must surface an error rather
  than silently switching to an untested backend.

## One-source project contract

The initial project JSON contains:

- `schema_version` and a stable `project_id`.
- One source record with a stable `source_id`, absolute path, URI, file size,
  modification time, and probed media metadata.
- A foundation timeline with source duration and a current playhead position.
- No destructive media operation or implicit source replacement.

Reopening first checks the stored path and validates the source identity
metadata. A missing or changed source is reported explicitly. The first
version does not silently search for or relink another file; an explicit
future relink operation can be added after source identity and CLI behavior
are approved.

## Atomic persistence contract

Project writes go to a uniquely named sibling temporary file, flush and
close it, then replace the destination atomically. A failed write leaves the
previous project file untouched. Invalid JSON or an unsupported schema version
is rejected before replacing the active in-memory project.

## Manual validation path

Use a small locally generated MP4 fixture or representative local media.
Verify opening, preview playback, pause, seek, duration display, save,
close/reopen, and source preservation on the target workstation. Do not add
private media to the repository or durable evidence.

## Rejected alternatives

- **Tkinter:** the module is discoverable but the target runtime is missing
  `libtk8.6.so`, and it does not provide the required media playback stack.
- **Qt/PySide:** no supported Qt Python binding is installed, so selecting it
  would add an unvalidated dependency and packaging path.
- **Standalone mpv/ffplay process:** useful for probing playback but harder to
  synchronize with an interactive timeline and project state.
- **GStreamer `playbin` plus `appsink`:** the target workstation has the
  Python bindings and `appsink`, but its installation lacks `qtdemux` and
  `matroskademux`; a generated MP4 fails before producing a frame. It remains
  a possible future backend after the system plugin set is made explicit.
- **GTK-native GStreamer sink:** `gtksink`, `gtk4paintablesink`, and
  `gtkglsink` are not installed on the target workstation.
