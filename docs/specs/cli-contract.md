# Deterministic Editor CLI Contract

The editor executable keeps the GTK workflow as its default mode and exposes
deterministic one-source and mixed-source operations as JSON commands:

```sh
resolve-editor inspect PROJECT
resolve-editor import SOURCE [SOURCE ...] --project PROJECT
resolve-editor split PROJECT --at SECONDS
resolve-editor delete PROJECT --segment SEGMENT_ID
resolve-editor restore PROJECT --segment SEGMENT_ID
resolve-editor toggle-delete PROJECT --segment SEGMENT_ID
resolve-editor move PROJECT --segment SEGMENT_ID [--segment SEGMENT_ID ...] \
  --direction {left,right}
resolve-editor copy PROJECT --segment SEGMENT_ID [--segment SEGMENT_ID ...]
resolve-editor paste PROJECT --segment SEGMENT_ID [--segment SEGMENT_ID ...] \
  --at SECONDS
resolve-editor focus PROJECT --segment SEGMENT_ID [--segment SEGMENT_ID ...] \
  [--zoom ZOOM] [--offset-x PIXELS] [--offset-y PIXELS]
resolve-editor copy-focus PROJECT --source-segment SEGMENT_ID \
  --segment SEGMENT_ID [--segment SEGMENT_ID ...]
resolve-editor clean-focus PROJECT --segment SEGMENT_ID [--segment SEGMENT_ID ...]
resolve-editor triplicate-enable PROJECT --segment SEGMENT_ID \
  [--segment SEGMENT_ID ...]
resolve-editor triplicate-disable PROJECT --segment SEGMENT_ID \
  [--segment SEGMENT_ID ...]
resolve-editor relink PROJECT --source SOURCE_ID --path SOURCE
resolve-editor duration PROJECT
resolve-editor save PROJECT [--output PROJECT]
resolve-editor reopen PROJECT
resolve-editor set-fps-policy PROJECT --choice {lowest,highest,custom,60} \
  [--custom-fps FPS] [--enhance-fps|--no-enhance-fps] [--fps-backend BACKEND]
resolve-editor set-upscale-policy PROJECT \
  (--enable-upscale|--disable-upscale) [--upscale-model MODEL] \
  [--upscale-backend BACKEND]
resolve-editor export-plan PROJECT [--output VIDEO] \
  [--fps-choice {lowest,highest,custom,60}] [--custom-fps FPS] \
  [--enhance-fps|--no-enhance-fps] [--fps-backend BACKEND] \
  [--upscale-enhancement|--no-upscale-enhancement] \
  [--upscale-model MODEL] [--upscale-backend BACKEND]
resolve-editor export PROJECT --output VIDEO \
  [--fps-choice {lowest,highest,custom,60}] [--custom-fps FPS] \
  [--enhance-fps|--no-enhance-fps] [--fps-backend BACKEND] \
  [--upscale-enhancement|--no-upscale-enhancement] \
  [--upscale-model MODEL] [--upscale-backend BACKEND]
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
- ordered stable `source_id` values and persisted source metadata;
- ordered stable `segment_id` values with source boundaries, timeline
  placement, block state, deletion state, display color, visual transform, and
  triplicate group state;
- source duration, playhead, edited duration, and active/deleted counts;
- persisted frame-rate and orientation-aware upscale policies, including
  per-source eligibility decisions;
- conservative exportability state.

Repeated inspection of unchanged inputs is byte-equivalent. Explicit delete
and restore operations are idempotent; split creates two new stable segment
identifiers once and rejects invalid or boundary positions without saving a
partial mutation. Project writes use the existing atomic persistence boundary.
Copy and paste on one-source or mixed-source timelines create fresh segment
identities, preserve source coverage and block-owned state, and return the
source and pasted IDs in the operation result. Source relinking requires an
explicit stable `source_id`.

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
be replaced by media output. `export-plan` resolves a collision-safe
destination when no output is supplied and never starts media processing.
Both export commands accept the persisted frame-rate policy choices: lowest
input FPS, highest input FPS, a positive rational custom FPS, or 60 FPS.
Frame-rate enhancement remains disabled by default, while upscale enhancement
is enabled by default for eligible sources. Upscale enhancement can be
disabled per export or persisted with `set-upscale-policy`; eligible
landscape sources have a short side of at most 1000 pixels and
eligible portrait sources have a short side of at most 720 pixels. The default
SuperUltraCompact restoration runs before spatial preparation and never
downscales an eligible source. Export results include the normalized policies,
per-source eligibility decisions, stage estimates, and verified output
metadata.

Export writes structured JSON Lines progress events with
`command: "export.progress"` and `event: "progress"` before the final
`command: "export"` result. Progress events are not success results, so a
failed export cannot be mistaken for a completed command. The final result
reports the selected stream-copy or fallback route, the reason, verified
output metadata, and publication path. Unverified partial files are never
reported as successful output.

Every project export uses the fixed 1920x1080 project canvas. Inputs that do
not match it are contain-scaled and letterboxed through the established
fallback render profile; a one-source input may use stream copy only when it
already matches the project canvas. Source codec/container differences do not
select a different delivery profile.

Focused composition edits use a versioned segment-owned transform on the fixed
1920x1080 canvas. Zoom is bounded to `1.0..8.0`; X and Y offsets use the
zoom-dependent bounds `±(1920 * (zoom - 1) / 2)` and
`±(1080 * (zoom - 1) / 2)` canvas pixels. For example, 2x allows
`±960`/`±540`, while 4x allows `±2880`/`±1620`. Interactive CLI/UI values are
clamped to those bounds. The triplicate renderer also allows `±640` horizontal
X selection at the default `1.0x` zoom because each instance crops a
640-pixel-wide column; Y remains `0` at that zoom. Mismatched sources are
contain-scaled without stretching. Triplicate mode stores one linked group
with exactly `center`, `left`, and `right` instances, renders them in that
order over a black background, and applies one shared transform to all three
while preserving the contain/letterbox source geometry. Focused or triplicate
segments always use the verified fallback render route; they are never
silently stream-copied.

The contract is versioned by `contract_version`. Additive fields preserve the
current version; incompatible changes require a new version and an explicit
migration or compatibility decision. The frame-rate and upscale policies are
persisted in the versioned project JSON by `set-fps-policy` and
`set-upscale-policy`, then reused by GUI, CLI, and export planning; these
additive commands and fields remain within contract version 1.
