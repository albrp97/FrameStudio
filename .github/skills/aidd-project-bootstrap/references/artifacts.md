# Bootstrap artifacts

## Outputs

In `draft` or `status` mode, the skill produces a report only. In `write` mode,
or after the default flow receives explicit approval, it must persist the
approved artifacts with repository file operations and verify each resulting
path. A file body printed in the response is never evidence that an artifact
was created.

The skill may create or update the following durable context:

- **Vision:** `vision.md`, using the `create-vision` contract, for project
  purpose, users, goals, non-goals, durable constraints, principles, and
  success criteria.
- **Agent guidance:** `AGENTS.md` or the configured equivalent, for
  repository-specific setup, commands, architecture boundaries, validation,
  security rules, and agent operating conventions. It must complement rather
  than duplicate `.github/copilot-instructions.md`.
- **Repository map:** the configured map path, using
  `aidd-create-repository-map`, for source, test, documentation, automation,
  infrastructure, ownership, tooling, and unknown surfaces.
- **Scope handoff:** the configured scope artifact, using the
  `aidd-product-manager` discovery contract, for the current horizon,
  exclusions, dependencies, risks, protected behavior, and verification
  intent.
- **Delivery configuration:** an authorized, secret-free update to
  `.github/aidd-config.yml` when project-specific commands, provider, branch,
  artifact settings, or `delivery.development.mode` are confirmed. The
  machine-readable mode is canonical.
- **README:** the configured project README only when it is missing or the
  user explicitly requests it. A README is human-facing onboarding, not a
  substitute for vision or agent guidance.

The selected mode must also be mirrored in `vision.md` and project-specific
`AGENTS.md` (or the configured equivalent), with an explicit reference to
`.github/aidd-config.yml` and `delivery.development.mode` as the source of
truth. When automatic mode is selected, mirror the exact
`delivery.development.automatic_validation` profile:
`rubber-duck`, `gpt-5.6-luna`, high reasoning, and `all-validation`.

The result reports the actual `created`, `updated`, `unchanged`, `skipped`,
`unresolved`, and `blocked` artifacts, including their repository-relative
paths and post-write verification status. It does not create capability,
phase, feature, or ticket children as a side effect.

```sudolang
ArtifactWriteResult {
  path
  operation: created | updated | unchanged | skipped | blocked
  verified
  sourceBasis[]
  reason
}
```
