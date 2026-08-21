---
name: aidd-log
description: Document completed features in a structured changelog with emoji categorization. Use when the user asks to log changes, update the changelog, or after completing a significant feature.
allowed-tools: Bash(git:*)
---

# Changelog Log

Act as a senior software engineer to log completed features using the following
template. This is a global changelog, not an active ticket evidence record:

```
## $date

- $emoji - $featureName - $briefDescription
```

# What to Log

**LOG ONLY COMPLETED FEATURES** - Focus on completed features that represent significant user-facing value:

- ✅ **Feature Completions**: Major feature releases, tool creation, system implementations
- ✅ **User-Impacting Changes**: New capabilities, workflows, or developer experience improvements
- ✅ **Architecture Decisions**: Significant refactoring, new patterns, or system redesigns

**DO NOT LOG**:
- ❌ Config file changes (.json, .config updates)
- ❌ File organization/moves (directory restructuring)
- ❌ Minor bug fixes (unless feature-level)
- ❌ Documentation updates (unless feature-level)
- ❌ Dependency updates
- ❌ Internal refactoring
- ❌ Test additions/changes
- ❌ Meta-work (logging, planning, etc.)

When a feature is complete, link its active ticket evidence record in the
feature-level entry or the surrounding changelog context. Do not copy command
output, credentials, test data, or an execution timeline into this file.

# Emojis

Use the following emoji to represent the feature type:

- 🚀 - new feature
- 🐛 - bug fix
- 📝 - documentation
- 🔄 - refactor
- 📦 - dependency update
- 🎨 - design
- 📱 - UI/UX
- 📊 - analytics
- 🔒 - security

Constraints {
  Always use reverse chronological order.
  Add most recent features to the top.
  Keep descriptions brief (< 50 chars).
  Focus on feature-level accomplishments, not implementation details.
  Never log meta-work or trivial changes.
  Omit the "feature" from the description.
  Keep active execution evidence in `/evidence`, not here.
}

gitChanges() {
  git add .
  git --no-pager diff --cached
}

planChanges() {
  Check the plan diff to detect recently completed plan tickets.
}

detectChanges() {
  gitChanges |> planChanges |> logDetectedChanges
}
