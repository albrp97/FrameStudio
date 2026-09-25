---
name: aidd-ecs
description: Enforces @adobe/data/ecs best practices. Use this whenever @adobe/data/ecs is imported, when creating or modifying Database.Plugin definitions, or when working with ECS components, resources, transactions, actions, systems, or services.
---

import ../workflow-interface.md

# Database.Plugin authoring

Plugins are created with `Database.Plugin.create()` from `@adobe/data/ecs`.

## Property order (enforced at runtime)

Properties **must** appear in this exact order. All are optional.

```sudolang
PluginPropertyOrder [
  "extends — Plugin, base plugin to extend"
  "services — (db) => ServiceInstance, singleton service factories"
  "components — schema object, ECS component schemas"
  "resources — { default: value as Type }, global resource schemas"
  "archetypes — ['comp1', 'comp2'], standard ECS archetypes; storage tables for efficient insertions"
  "computed — (db) => Observe<T>, computed observables"
  "transactions — (store, payload) => void, synchronous deterministic atomic mutations"
  "actions — (db, payload) => T, general functions"
  "systems — { create: (db) => fn | void }, per-frame (60fps) or init-only"
]

Constraints {
  Properties must appear in this exact order; wrong order throws at runtime
}
```

---

## Composition

**Single extension** — one plugin extends another:
```ts
export const authPlugin = Database.Plugin.create({
  extends: environmentPlugin,
  services: {
    auth: db => AuthService.createLazy({ services: db.services }),
  },
});
```

**Combine** — `extends` accepts only one plugin. To extend from multiple use Database.Plugin.combine:
```ts
export const generationPlugin = Database.Plugin.create({
  extends: Database.Plugin.combine(aPlugin, bPlugin),
  computed: {
    max: db => Observe.withFilter(
        Observe.fromProperties({
            a: db.observe.resources.a,
            b: db.observe.resources.b
        }),
        ({ a, b }) => Math.max(a, b)
    )
  },
});
```

**Final composition** — combine all plugins into the app plugin:
```ts
export const appPlugin = Database.Plugin.combine(
  corePlugin, themePlugin, dataPlugin,
  authPlugin, uiPlugin, featurePlugin
);

export type AppPlugin = typeof appPlugin;
export type AppDatabase = Database.Plugin.ToDatabase<AppPlugin>;
```

---

## Property details

Load [property details](./references/property-details.md) when defining ECS
plugin properties, components, resources, systems, actions, or services.

## Naming conventions

```sudolang
PluginNaming {
  file: "*-plugin.ts (kebab-case) — e.g. layout-plugin.ts"
  export: "*Plugin (camelCase) — e.g. layoutPlugin"
  system: "plugin_name__system (snake_case, double underscore) — e.g. layout_plugin__system"
  initSystem: "plugin_name_initialize — e.g. ui_state_plugin_initialize"
}
```

---

## Type utilities

```ts
export type MyDatabase = Database.Plugin.ToDatabase<typeof myPlugin>;
export type MyStore = Database.Plugin.ToStore<typeof myPlugin>;
```

---

## Execute

```sudolang
fn whenCreatingOrModifyingPlugin() {
  Constraints {
    Verify property order matches (extends, services, components, resources, archetypes, computed, transactions, actions, systems)
    Use extends for single-parent; Database.Plugin.combine() for multiple peers
    Ensure services only access db.services from extended plugins (not forward references)
    Export type *Database = Database.Plugin.ToDatabase<typeof *Plugin> when consumers need typed db access
    Follow naming conventions for files, exports, and systems
  }
}
```

## Additional resources

- [data-modeling.md](data-modeling.md) — Components, resources, and archetypes (particle simulation example)
