---
name: aidd-sudolang-syntax
description: Quick cheat sheet for SudoLang syntax. Use when writing or reading SudoLang pseudocode, interfaces, constraints, or function definitions.
---

import ../workflow-interface.md

# SudoLang Syntax

A quick cheat sheet for SudoLang syntax.

## Interfaces

DisplayTheme {
  mode: "light" | "dark"
  name: String
  parameters{} // each theme can have different sets of parameters
  permissions[]
}

UserPreferences {
  displayTheme
}

User {
  id: String
  displayName
  preferences
}

## Constraints

constraint: can be specified inline or in block form

Constraints {
  A constraint
  Another constraint
}


## Syntax reference

Load [syntax reference](./references/syntax-reference.md) for patterns,
functions, objects, templates, arrays, comments, and operators.

## Disallowed Keywords

Should generate a warning for disallowed keywords.

class Foo extends Bar {
  constructor() {
    super()
  }
}
