# aidd-log

Documents completed features in a structured changelog with emoji categorization.
It is intentionally separate from active ticket delivery evidence.

## Why

A consistent changelog format makes it easy to scan project history for
significant user-facing accomplishments. Logging at the feature level keeps the
signal-to-noise ratio high.

## Usage

Invoke `/aidd-log` after completing a significant feature. Record execution
commands and gate results with `/evidence`, then link that record if useful.
Entries
follow this format:

```markdown
## 2026-03-18

- :rocket: - Feature Name - Brief description
```

Log only completed features — not config changes, file moves, minor fixes, or
internal refactoring. Descriptions stay under 50 characters.

## When to use

- After completing a significant feature
- When the user asks to log changes or update the changelog
