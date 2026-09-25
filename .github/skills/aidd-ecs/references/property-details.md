# ECS property details

## Property details

### services

Factory functions creating singleton services. Extended plugin services initialize first, so `db.services` has access to them.

```ts
services: {
  environment: _db => EnvironmentService.create(),
}
```

### components

Schema objects defining ECS component data. Use schema imports from type namespaces or inline schemas. See [data-modeling.md](../data-modeling.md) for a simple example.

```ts
components: {
  layout: Layout.schema,
  layoutElement: { default: null as unknown as HTMLElement, transient: true },
  layoutLayer: F32.schema,
},
```

Non-persistable values (e.g. HTML elements, DOM refs) must use `transient: true` — excluded from serialization.

### resources

Global state not tied to entities. Use `as Type` to provide the compile-time type — without it the value is treated as a const literal. See [data-modeling.md](../data-modeling.md) for patterns.

```ts
resources: {
  themeColor: { default: 'dark' as ThemeColor },
  themeScale: { default: 'medium' as ThemeScale },
},
```

Use `null as unknown as Type` for resources initialized later in a system initializer:

```ts
resources: {
  connection: { default: null as unknown as WebSocket },
},
```

### archetypes

Standard ECS archetypes. Used for querying and inserting related components. See [data-modeling.md](../data-modeling.md) for a simple example.

```ts
archetypes: {
  Layout: ['layout', 'layoutElement', 'layoutLayer'],
},
```

### computed

Factory returning `Observe<T>` or `(...args) => Observe<T>`. Receives full db.

```ts
computed: {
  max: db => Observe.withFilter(
    Observe.fromProperties({
      a: db.observe.resources.a,
      b: db.observe.resources.b,
    }),
    ({ a, b }) => Math.max(a, b)
  ),
},
```

### transactions

Synchronous, deterministic atomic mutations. Receive `store` and a payload. Store allows direct, immediate mutation of all entities, components, and resources.

```ts
transactions: {
  updateLayout: (store, { entity, layout }: { entity: Entity; layout: Layout }) => {
    store.update(entity, { layout });
  },
  setThemeColor: (store, color: ThemeColor) => {
    store.resources.themeColor = color;
  },
},
```

```sudolang
StoreAPI {
  "store.update(entity, data)" = "update entity components"
  "store.resources.x = value" = "mutate resources"
  "store.get(entity, 'component')" = "read component value"
  "store.read(entity)" = "read all entity component values"
  "store.read(entity, archetype)" = "read entity component values in archetype"
  "store.select(archetype.components, { where })" = "query entities"
}
```

### actions

General functions with access to the full db. Can return anything or nothing.
UI components that call actions MUST never consume returned values — call for side effects only. Consuming return values violates unidirectional flow (data down via Observe, actions up as void).
Call at most one transaction per action; multiple transactions corrupt the undo/redo stack.

```ts
actions: {
  generateNewName: async (db) => {
    const generatedName = await db.services.nameGenerator.generateName();
    db.transactions.setName(generatedName);
  },
  getAuth: db => db.services.auth,
},
```

### systems

`create` receives db and may optionally return a per-frame function (60fps) or just initialize values. Always called synchronously when `database.extend(plugin)` runs.

```ts
systems: {
  ui_state_plugin_initialize: {
    create: db => {
      db.transactions.registerViews(views);
    },
  },
  layout_plugin__system: {
    create: db => {
      const observer = new ResizeObserver(/* ... */);
      Database.observeSelectDeep(db, db.archetypes.Layout.components)(entries => {
        // react to entity changes
      });
    },
  },
},
```

**System scheduling** (optional):
```ts
systems: {
  physics: {
    create: db => () => { /* per-tick work */ },
    schedule: {
      before: ['render'],
      after: ['input'],
      during: ['simulation'],
    },
  },
},
```

```sudolang
Schedule {
  before: "hard ordering constraints"
  after: "hard ordering constraints"
  during: "soft preference for same execution tier"
}
```

---
