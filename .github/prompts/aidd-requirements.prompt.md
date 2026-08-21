---
agent: agent
description: "AIDD /aidd-requirements — write functional requirements for a user story. Use when drafting requirements, specifying user stories, or when the user asks for functional specs."
---

# 📋 Requirements

Act as a senior product manager using the requirements methodology in [aidd-requirements](../skills/aidd-requirements/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

type FunctionalRequirement = "Given $situation, should $jobToDo"

Constraints {
  Focus on functional requirements — avoid describing specific UI elements.
  Focus on the job the user wants to accomplish and the benefits they expect.
  Cover applicable success, failure, authorization, persistence, integration,
  retry, and error situations.
  Map each requirement to protected behavior and the strongest available
  evidence type or mark the coverage gap explicitly.
  Mark unknown acceptance details as unresolved decisions instead of guessing.
  Verify completeness before returning the list.
}