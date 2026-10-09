# PHASE-010 - Editing Synchronized Tracks and Flexible Outputs

**Phase ID:** PHASE-010
**Parents:** OBJ-001, SCOPE-001, CAP-MAP-001
**Capability links:** CAP-001, CAP-002, CAP-003, CAP-004, CAP-005, CAP-006,
CAP-007, CAP-008, CAP-009, CAP-010, CAP-011, CAP-012, CAP-013
**Sequence:** 10
**Status:** active
**Horizon:** next approved extension
**Approval:** functionality/planning approved 2026-10-09; implementation and
bounded GPT-5.6 Luna max delegation authorized by the subsequent user request.
CHG-014 subsequently authorizes autonomous completion in automatic mode.
Technical-contract, exact-profile automatic-validation and delivery gates remain required.
**Owner:** orchestrator (integration, shared evidence and lifecycle)
**Last updated:** 2026-10-09
**Discovery:** `../../../specs/multi-track-editing-contract.md` (DISC-010)
**Change control:** `../../reviews/CHG-012-synchronized-tracks-and-flexible-delivery.md`
**Export refinement:** `../../reviews/CHG-013-independent-track-source-exports.md`
**Autonomous authorization:** `../../reviews/CHG-014-autonomous-phase010-and-workflow-repair.md`
**Feature links:** FEAT-032, FEAT-033, FEAT-034, FEAT-035, FEAT-036,
FEAT-037, FEAT-038
**Dependencies:** existing single-track model, media identity, visual/audio
policies, migration, verified exports; export consumers require TICKET-104
terminal route-integrity evidence before integration
**Path history:** created at this `phases/open/` path on 2026-10-09

## Outcome and boundaries

Inspect selected media without audio-analysis clutter, remove and undo timeline
blocks, optionally export edited sources independently within each track, and arrange one to four
simultaneous tracks with silent preview, active-only visual layouts, and fixed
stereo export mixing. Preserve fixed 1920x1080 delivery and safe fast rendering.

Separate track/source files fill the full canvas with normal source audio,
never the simultaneous final video's slot crop or stereo pan. The same source
on different tracks produces independent edited files; empty tracks produce
none. Final-only, source-only and combined output modes remain optional.

Exact requirements REQ-010-01 through REQ-010-06 are owned by DISC-010.
No general-purpose undo, fifth track, standalone audio tracks,
transitions, or keyframed effects are included. Other open work is not closed
or reopened by this phase. Silent preview is an intentional approved change.

## Entry conditions

- Scope/capability extension and phase decomposition approved through CHG-012.
- Before each implementation, run readiness and establish its baseline; no
  planned ticket is execution-ready solely from this write.
- Track/persistence compatibility contracts precede dependent domain work.
- Export integration waits for TICKET-104 final route/integrity evidence; do
  not fabricate a pass because the route code exists.
- Confirm GTK/display, generated-media tooling, and enhancement runtime
  availability for applicable tests; missing required functionality gates block.

## Execution authorization and current wave

The user's subsequent 2026-10-09 instruction authorizes orchestrating
implementation, review and actual UI/CLI functionality testing, using bounded
GPT-5.6 Luna agents at maximum reasoning. CHG-014 records the later explicit
authorization to complete this phase autonomously without routine questions.
The configured mode is automatic. Rubber Duck GPT-5.6 Luna, high reasoning,
`all-validation`, owns every validation decision. Routine technical-contract
and delivery approvals are bootstrap-authorized, not invented human results.
Actual tooling, security, provider, branch, remote-check and merge gates remain.

The integration branch is `phase/010-synchronized-tracks`. Initial independent
work is TICKET-109 metadata implementation and TICKET-115 migration work in
isolated worktrees. Read-only migration design identified a timing conflict;
the user subsequently approved DESIGN-010-115 and its explicit conversion
policy before TICKET-115 implementation was dispatched. The orchestrator owns all shared
planning/evidence edits and integration. Subsequent waves wait for their actual
prerequisites and exact-profile automatic validation. TICKET-104 remains
`verifying`; its bounded route-integrity verification runs independently and
unblocks only the export consumers after terminal evidence. TICKET-126 repairs
inherited duplication and broken CI parity independently of the model work.
Neither worker results nor authorization imply publication or closeout.

## Feature dependencies and parallel boundaries

| Feature | Outcome | Hard feature prerequisites | Partial interface available after |
|---|---|---|---|
| FEAT-032 | Selected-video information | None | Existing source metadata |
| FEAT-035 | Collision-safe synchronized track arrangement | None | TICKET-115 model/migration |
| FEAT-033 | Undoable Backspace ripple removal | FEAT-035 interfaces, not whole-feature closure | TICKET-115; UI after TICKET-117 |
| FEAT-034 | Optional independent track/source outputs | FEAT-035 stable track/source identity interface | TICKET-115; render after TICKET-104 |
| FEAT-036 | Matching dynamic preview/render sections | FEAT-035 timing/interaction interface | TICKET-115 and TICKET-117 |
| FEAT-037 | Fixed stereo mix following visual slots | FEAT-036 layout/render interfaces | TICKET-119; integration after TICKET-121 |
| FEAT-038 | Recoverable multi-output delivery and acceptance | Product acceptance consumes FEAT-032 through FEAT-037; maintenance126 independent | TICKET-124 session integration and TICKET-126 quality/CI repair |

These are partial-interface dependencies, not blanket phase-closure gates.
The backlog's ticket graph is the executable ordering authority.

## Dependency waves

| Wave | Candidates after actual prerequisites pass | Merge/write cautions |
|---|---|---|
| A | TICKET-109, TICKET-115, TICKET-126; prerequisite104 verification | Independent metadata/UI, model/migration, workflow/test and read-only export verification ownership |
| B | TICKET-110, TICKET-112, TICKET-116, TICKET-119 | Shared model edits in 110/116 must be serialized or merged through one owner |
| C | TICKET-113, TICKET-117, TICKET-118, TICKET-121, TICKET-122 | Export 113/121 share pipeline helpers; serialize shared writes |
| D | TICKET-111, TICKET-114, TICKET-120, TICKET-123 | 111/114/120 share application wiring; 123 consumes 121+122 |
| E | TICKET-124 | Integrates source/final outputs, stereo, sessions, failure/retry |
| F | TICKET-125 | Integrated acceptance after product predecessors and maintenance126 |

Waves are illustrative, not extra dependencies. A ticket can start as soon as
its actual graph predecessors, local baseline, and exact-profile validation
are satisfied. Delegation is explicitly authorized by CHG-014; parallelizable
alone does not authorize overlapping writes.

## Ownership/conflict rules

Reserve shared `model_*`, `app_*`, `cli*`, `export_*`, and test-module writes
before dispatch. Different ticket IDs are not proof of independent writes.
Use interface contracts and isolated test cases for independent work, one
integration owner for shared seams, and final merged-diff verification.
Existing TICKET-029/105/106/107/108 and TICKET-103/104 are potential shared
surface owners; do not overwrite their work or infer their validation.

## Exit and verification

- Each planned requirement has an executable acceptance test and final
  implementation evidence, not just a unit proxy.
- Migrated projects, gaps, collisions, Backspace/Undo, source-group modes,
  changing active layouts, per-segment transforms/triplicate, silent preview,
  stereo pan, frame counts, source hashes, atomic publication, and resume pass.
- Independent track/source files preserve pair identities, repeated sources,
  cuts, normal source audio and full-canvas modifications; multi-track source
  export does not depend on final-video slot/pan rendering.
- Generated-media preview/render snapshots and decoded audio measurements
  demonstrate actual output behavior at active-set boundaries.
- Required local checks, deterministic review, exact-profile `automaticValidation`, and
  configured delivery policy are terminal before closeout.
- Keep feature/ticket IDs, path histories, and indexes synchronized.

**Evidence plan:** each ticket's `evidence/ticket-NNN-*.md` is a future
implementation record; none is fabricated by this planning write.
