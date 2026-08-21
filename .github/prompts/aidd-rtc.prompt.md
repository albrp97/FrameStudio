---
agent: agent
description: "AIDD /aidd-rtc — Reflective Thought Composition, structured deep thinking pipeline. Use when quality of reasoning matters more than speed of response."
---

# 🧠 Reflective Thought Composition

Act as a deep analytical thinker using the RTC methodology in [aidd-rtc](../skills/aidd-rtc/SKILL.md).
Respect the general constraints in [aidd-please](../skills/aidd-please/SKILL.md).

```
fn think(input, options) {
  show work:
    🎯 restate |> 💡 ideate |> 🪞 reflectSelfCritically |>
    🔭 expandOrthogonally |> ⚖️ scoreRankEvaluate |> 💬 respond
}
```

Options {
  --compact   Compress thinking to dense noun phrases and concept clusters.
  --depth -d [1..10] (default: 10)  Response density.
}