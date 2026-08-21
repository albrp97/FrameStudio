# aidd-product-manager

Plans features, user stories, user journeys, and conducts product discovery
using structured personas, pain points, journey maps, and delivery contracts.

## Why

Unstructured feature requests lead to misaligned priorities and wasted effort.
Mapping pain points to personas and scoring by impact and frequency produces a
prioritized backlog grounded in user research.

## Usage

Invoke `/aidd-product-manager` to plan features or conduct discovery. Commands:

`/research`, `/setup`, `/generate [type]`, `/feature`, `/save`, `/cancel [step]`

Artifacts are saved to `plan/story-map/` as YAML files (story map, user
journeys, personas).

Discovery hands an approved delivery contract, including scope, non-goals,
risks, protected behavior, and verification intent, to
`aidd-ticket-creator`, which organizes delivery as phases -> features ->
tickets. Discovery does not create implementation tickets.

## When to use

- Planning features, user stories, or user journeys
- Conducting product discovery
- Building specifications, journey maps, story maps, or personas
