# Deterministic Editor CLI Contract

The editor executable keeps the GTK workflow as its default mode and exposes
first-horizon one-source operations as JSON commands:

```sh
resolve-editor inspect PROJECT
resolve-editor import SOURCE --project PROJECT
resolve-editor split PROJECT --at SECONDS
resolve-editor delete PROJECT --segment SEGMENT_ID
resolve-editor restore PROJECT --segment SEGMENT_ID
resolve-editor toggle-delete PROJECT --segment SEGMENT_ID
resolve-editor duration PROJECT
resolve-editor save PROJECT [--output PROJECT]
resolve-editor reopen PROJECT
resolve-editor export PROJECT --output VIDEO
```

The same commands can be run from the repository with
`python3 resolve_editor.py ...` or `make cli ARGS="..."`.

## Success output

Every completed command emits one JSON object with:

```json
{
  "ok": true,
  "contract_version": 1,
  "command": "inspect"
}
```

Inspection and mutation commands include a `project` object containing:

- `project_id` and `schema_version`;
- stable `source_id` and persisted source metadata;
- ordered stable `segment_id` values with source boundaries and deletion
  state;
- source duration, playhead, edited duration, and active/deleted counts;
- conservative exportability state.

Repeated inspection of unchanged inputs is byte-equivalent. Explicit delete
and restore operations are idempotent; split creates two new stable segment
identifiers once and rejects invalid or boundary positions without saving a
partial mutation. Project writes use the existing atomic persistence boundary.

## Errors and exit statuses

Errors are emitted as one JSON object on stderr and never include a successful
result:

```json
{
  "ok": false,
  "contract_version": 1,
  "error": {
    "code": "invalid_operation",
    "message": "Split position must be strictly inside one segment",
    "details": {}
  }
}
```

Exit statuses are:

| Status | Meaning |
| ---: | --- |
| 0 | Completed successfully |
| 2 | Malformed command-line arguments |
| 3 | Invalid project, source, media, or operation |
| 4 | Required FFmpeg/ffprobe dependency is unavailable |
| 5 | Persistence, export, or other operation failure |

## Paths and export progress

Local paths are reduced to basenames by default. `--full-paths` explicitly
opts into absolute project, source, and output paths. Stable IDs and media
metadata are still emitted when paths are redacted. Export rejects a
destination that resolves to the project file so the saved edit state cannot
be replaced by media output.

Export writes structured JSON Lines progress events with
`command: "export.progress"` and `event: "progress"` before the final
`command: "export"` result. Progress events are not success results, so a
failed export cannot be mistaken for a completed command. The final result
reports the selected stream-copy or fallback route, the reason, verified
output metadata, and publication path. Unverified partial files are never
reported as successful output.

The contract is versioned by `contract_version`. Additive fields preserve the
current version; incompatible changes require a new version and an explicit
migration or compatibility decision.
