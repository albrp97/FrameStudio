# Planning artifact lifecycle

Use this shared contract for phase, feature, and ticket records. Resolve all
paths from `.github/aidd-config.yml`; the configured repository convention
overrides these defaults.

## Required layout

Each planning layer has an index/list file and one Markdown record per stable
ID:

```text
docs/planning/
  phases.md
  phases/
    open/
      PHASE-001-<slug>.md
    closed/
      PHASE-000-<slug>.md
  features.md
  features/
    open/
      FEAT-001-<slug>.md
    closed/
      FEAT-000-<slug>.md
  backlog.md
  tickets/
    open/
      TICKET-001-<slug>.md
    closed/
      TICKET-000-<slug>.md
```

The index files are lists, not substitutes for the individual records. Each
index must contain the stable ID, title, status, parent links, and current
relative path for every record in both `open` and `closed`.

## Directory classification

Unless configuration defines different status lists:

- `open` contains draft, confirmed, needs-review, proposed, planned, active,
  pending, baseline, inProgress, verifying, gated, and blocked records.
- `closed` contains complete, completed, and cancelled records.

Blocked records remain in `open`; they are not archived. A closed record is
not eligible for new child generation or implementation.

## Transition protocol

When an authorized status update changes the directory classification:

1. Read the record by stable ID across both directories.
2. Update its status and lifecycle metadata.
3. Move the same record file from `open` to `closed`, or from `closed` to
   `open`, using the configured filename pattern.
4. Preserve the stable ID, parent/child links, record content, and history.
5. Update the layer index, backlog, and any parent/child path references to the
   new current path.
6. Record the old path, new path, status change, reason, owner, and evidence.

Do not leave a duplicate in both directories. Do not silently move a record
whose status did not change. A title rename may change the slug only when
configured or explicitly approved; the stable ID must remain unchanged.

Statuses that remain in the same classification update the record in place and
still require index synchronization. Reopening a closed record is a real
status transition and moves it back to `open` before it can receive new work.

## Ownership and safety

Creation skills create new phase, feature, and ticket records in `open`.
Planning review is read-only and reports path/status mismatches without moving
files. Grooming may perform only authorized routine status updates. Completion
skills move records only after the configured evidence and approval conditions
pass.

Closing a ticket does not automatically close its feature or phase. A feature
may move to `closed` only when its outcome and all required tickets are
complete or cancelled; a phase may move to `closed` only when its exit
conditions and required child features are satisfied. Material changes use
change control, preserve path history, and move only affected records.
