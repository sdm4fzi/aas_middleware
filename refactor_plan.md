Perfect—here’s the **adjusted refactor plan** with your constraints:

* **Ports** now expose **one unified Connector protocol** only, with:

  * `receive()` → async iterator (stream)
  * `provide()` → async getter (pull latest / snapshot)
  * `consume(value)` → async setter/post (push)
* **Persistence is just a set of connectors.** No separate persistence port anymore.
* **When a DataModel is loaded**, the system **auto-creates persistence connectors** per model/type/field and keeps them in sync.

I’ll keep the rest of the plan intact (core/adapters/facade/REST/Consul/chains), but update the pieces that touch ports & persistence.

---

# Top-level objectives (unchanged)

1. Repo split: **core**, **adapters**, **facade**, **storage**, **utils**.
2. Everything configurable via Facade **and** Admin REST; saved & restored.
3. **Chained workflows** (Connector→Mapper→Formatter→…): code & REST.
4. **Event Bus** instrumentation by default.
5. **Consul auto-registration** for connectors/mappers/formatters/workflows with capability + I/O schemas.

---

# Phase 1 — Repo skeleton (same as before, trimmed ports)

```
aas_middleware/
  core/
    runtime.py
    events.py
    registries.py
    bindings.py
    sync_engine.py
    chain_runtime.py
    errors.py
    config_model.py
    instrumentation.py
  domain/
    data_model.py
  ports/
    connector.py         # ← only this
    lifecycle.py         # optional connect/disconnect
    discovery.py         # service registry interface
  adapters/
    web/
      rest_adapter.py
      graphql_adapter.py
      admin_adapter.py
      sse_adapter.py
    connectors/
      http_in.py         # implements provide/receive if applicable
      http_out.py        # implements consume/provide
      sql.py             # persistence-as-connector
      redis.py           # persistence-as-connector
      memory.py          # default persistence connector
    mapping/
      basyx_formatter.py
      pydantic_mapper.py
    discovery/
      consul.py
  facade/
    app.py
    builder.py
    chain_compiler.py
  storage/
    repo.py
    models.py
  utils/
    logging.py
    tracing.py
    backoff.py
```

---

# Phase 2 — Ports: single Connector protocol

```python
# ports/connector.py
from typing import Protocol, AsyncIterator, Mapping, Any, TypeVar, Generic

T = TypeVar("T")

class Connector(Protocol, Generic[T]):
    async def provide(self) -> T:
        """Return the latest/current value (snapshot)."""

    async def consume(self, value: T, *, meta: Mapping[str, Any] | None = None) -> None:
        """Accept a value (push/post)."""

    async def receive(self) -> AsyncIterator[T]:
        """Stream values as they arrive (events/changes)."""
```

Optional lifecycle:

```python
# ports/lifecycle.py
class Connectable(Protocol):
    async def connect(self) -> None: ...
    async def disconnect(self) -> None: ...
```

> All adapters (HTTP, SQL, Redis, etc.) just implement this one protocol.

---

# Phase 3 — Core: registries, bindings, sync, chains

### Registries

* `ConnectorRegistry`: `add(id, connector)`, `get(id)`, `list()`.
* `MapperRegistry`, `FormatterRegistry`, `WorkflowRegistry` (unchanged).
* `BindingRegistry` (unchanged signature; now resolves only connectors).

### Binding (unchanged shape; simplified resolution)

```python
# core/bindings.py
from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Address:
    data_model: str
    model_id: Optional[str] = None
    contained_id: Optional[str] = None
    field: Optional[str] = None

@dataclass(frozen=True)
class Binding:
    id: str
    source: str             # e.g., "connector:erp" or "persist:shop/Order.plan"
    target: str
    direction: str          # "push" | "pull" | "bidirectional"
    mapper_id: str | None = None
    formatter_id: str | None = None
```

### SyncEngine (connectors only)

* For **push** bindings, subscribe to `source.receive()` and `target.consume(...)`.
* For **pull** bindings, poll `source.provide()` on interval to `target.consume(...)`.
* For **bidirectional**, install both pumps + conflict policy (last-write-wins or vector clock optional).

---

# Phase 4 — Instrumentation: automatic events

Wrap **connectors** once at registration so authors never touch the bus:

* `connector.provide` → emits `connector.provide`
* `connector.consume` → emits `connector.consume`
* `connector.receive` → emits `connector.receive` per item (with optional batching)
* `connector.connected/disconnected` if lifecycle is implemented
* `connector.error` on exceptions

(Implementation pattern from earlier answer still applies, just targeting the unified protocol.)

---

# Phase 5 — Persistence as connectors (auto-generated)

### Goal

* No “persistence port”. Instead, **persistence backends are just connectors** that implement:

  * `provide()` → read value from store
  * `consume(value)` → write value to store
  * `receive()` → stream change events (DB notifications, polling, or in-memory bus)

### Config

```python
# core/config_model.py (excerpt)
class PersistenceBackendSpec(BaseModel):
    kind: Literal["memory","sql","redis","http"] = "memory"
    options: dict[str, Any] = Field(default_factory=dict)  # dsn, table, keyspace, etc.
```

### Auto-generation of model connectors

When `.models("shop", types=[...])` is called (or via REST):

* For each **top-level model type** `Order`, generate a **virtual connector id**:

  * `persist:shop/Order` (for the whole object collection)
  * `persist:shop/Order.{field}` (for hot fields, optional)
* Build them by **binding** the persistence backend chosen in config to the **data-model address**.
* The builder registers these connectors in `ConnectorRegistry`.

Example pseudo-connector (SQL):

```python
# adapters/connectors/sql.py
class SqlConnector(Connector[Any], Connectable):
    def __init__(self, dsn: str, table: str, key: str | None = None, path: str | None = None):
        ...
    async def connect(self): ...
    async def provide(self): ...                 # SELECT ... (optionally by key)
    async def consume(self, value): ...          # UPSERT ...
    async def receive(self): ...                 # LISTEN/NOTIFY or poll + diff
```

The **auto-generated persistence connectors** wrap an instance of `SqlConnector/RedisConnector/MemoryConnector` preconfigured with the correct table/key/JSON path to the data field. They’re registered under deterministic IDs like `persist:shop/Order.plan`.

### Automatic synchronization

* The builder also **installs bindings** from **external** connectors to **persist:** connectors and vice versa according to configuration (read-only/read-write, directions).
* That gives you instant CRUD + sync without writing glue.

---

# Phase 6 — Facade (DX) with the new assumptions

```python
# facade/app.py (high level)
app = (
  MiddlewareApp()
    .meta(title="RheoNet MW", version="1.0.0")
    .models("shop", types=[Order, Job])                 # triggers auto persist connectors
    .persistence(kind="sql", dsn="postgresql://...")    # sets default backend for auto connectors
    .connector("erp", kind="http_in", path="/erp/orders")
    .connector("scheduler", kind="http_out", url="http://sched:8080/plan")
    .bind("connector:erp", "persist:shop/Order", direction="push", mapper="erp_to_order")
    .bind("persist:shop/Order.plan", "connector:scheduler", direction="push", formatter="json")
    .chain("plan_order")
        .receive("connector:erp")
        .map("erp_to_order")
        .format("json","serialize")
        .consume("connector:scheduler")                 # uses consume under the hood
        .consume("persist:shop/Order.plan")
        .register()
    .discover.consul(url="http://consul:8500")
    .expose.rest("shop")
    .expose.admin()
    .serve()
)
```

Notes:

* Chain step names reflect the unified protocol:

  * `receive(connector_id)` → awaits first item (or streams, depending on option)
  * `provide(connector_id)` → pulls current
  * `consume(connector_id)` → pushes current payload

---

# Phase 7 — Admin REST (create everything externally)

Endpoints (same surface, but wording updated to connectors-only world):

* `POST /admin/connectors` (create/update), with `kind` and `options`
* `POST /admin/mappers`, `POST /admin/formatters`
* `POST /admin/bindings` (source/target/direction/mapper/formatter)
* `POST /admin/chains` (ChainSpec using step types: `receive`, `provide`, `consume`, `map`, `format`, `call_workflow`)
* `POST /admin/models` (define data model, triggers auto persistence connectors)
* `POST /admin/persistence` (set default backend; rewire existing `persist:` connectors if needed)
* `POST /admin/config/save` / `load`

**Example: define persistence + model + auto connectors via REST**

```bash
# 1) set default persistence backend
curl -X POST :8000/admin/persistence -H 'ct: application/json' -d '{
  "kind": "sql",
  "options": {"dsn": "postgresql://mw:mw@db:5432/mw"}
}'

# 2) register data model (pydantic type refs or schema)
curl -X POST :8000/admin/models -d '{
  "name": "shop",
  "types": ["my_models:Order", "my_models:Job"]
}'

# -> system creates connectors:
# persist:shop/Order, persist:shop/Job, (optional fields)
```

**Create a chain that uses only connectors**

```bash
curl -X POST :8000/admin/chains -d '{
  "id": "plan_order",
  "steps": [
    {"type":"receive", "id":"rx:erp", "connector_id":"connector:erp"},
    {"type":"map",     "id":"map:erp2order", "mapper_id":"erp_to_order"},
    {"type":"format",  "id":"fmt:json", "formatter_id":"json", "formatter_mode":"serialize"},
    {"type":"consume", "id":"tx:scheduler", "connector_id":"connector:scheduler"},
    {"type":"consume", "id":"pset:plan", "connector_id":"persist:shop/Order.plan"}
  ]
}'
```

---

# Phase 8 — Chain runtime & compiler (connector-centric)

**StepSpec** adds `provide/consume` (renamed from `persist_*`):

```python
# facade/chain_compiler.py (supported steps)
# - receive(connector_id)
# - provide(connector_id)
# - consume(connector_id)
# - map(mapper_id)
# - format(formatter_id, mode)
# - call_workflow(workflow_id)
```

Adapters:

```python
class ReceiveStep:   async def run(ctx): ctx.payload = await first(conn.receive())
class ProvideStep:   async def run(ctx): ctx.payload = await conn.provide()
class ConsumeStep:   async def run(ctx): await conn.consume(ctx.payload)
```

---

# Phase 9 — Consul registration (capabilities + I/O)

Every **connector**, **mapper**, **formatter**, and **workflow** registers with Consul:

* **Connectors**

  * `tags`: `["mw","kind:connector","dir:receive|provide|consume|duplex", "cap:<name>"]`
  * `meta`:

    * `capability`, `input_mime`, `output_mime`
    * `input_schema` / `output_schema` (JSON-serialized)
  * `address/port`: points to the middleware route that exposes this connector (if any)
* **Mappers/Formatters** (logical services)

  * `tags`: `["mw","kind:mapper"|"kind:formatter"]`
  * `meta`: input/output schema (derive from pydantic type hints if available)
* **Workflows/Chains**

  * `tags`: `["mw","kind:workflow"]`
  * `meta`: `input_schema`, `output_schema`

Auto-register on add\_\* and deregister on shutdown. Keep service IDs deterministic: `mw-connector-{id}`.

---

# Phase 10 — Storage & bootstrapping (persist config)

* `AppSpec` persists:

  * metadata, persistence backend, connectors (user-defined), mappers, formatters, workflows, **chain specs**, **bindings**, **models**.
* On startup:

  * load `AppSpec`
  * register data models → auto-create `persist:*` connectors bound to default backend
  * re-register all connectors/mappers/formatters/workflows
  * re-install bindings & chains
  * re-register in Consul

---

# Phase 11 — Acceptance tests (what to verify)

* **Auto persistence connectors**

  * After `POST /admin/models`, `GET /admin/connectors` includes `persist:shop/Order`.
  * `provide/consume/receive` work (SQL or memory backend).
* **Bindings** work with only connectors.
* **Chains** run via REST and emit `chain.*` events.
* **Consul** shows entries for connectors/mappers/formatters/workflows with correct capability + I/O.
* **Save/Load** rebuilds to the same runtime identity.

---

## Key code snippets

### Connector wrapper (instrumentation)

```python
# core/instrumentation.py (sketch)
class InstrumentedConnector(Connector[T]):
    def __init__(self, inner: Connector[T], id: str, bus: EventBus):
        self._inner, self._id, self._bus = inner, id, bus

    async def provide(self) -> T:
        try:
            val = await self._inner.provide()
            self._bus.publish("connector.provide", id=self._id)
            return val
        except Exception as e:
            self._bus.publish("connector.error", id=self._id, stage="provide", err=str(e))
            raise

    async def consume(self, value: T, *, meta=None) -> None:
        try:
            await self._inner.consume(value, meta=meta or {})
            self._bus.publish("connector.consume", id=self._id)
        except Exception as e:
            self._bus.publish("connector.error", id=self._id, stage="consume", err=str(e))
            raise

    async def receive(self) -> AsyncIterator[T]:
        self._bus.publish("connector.connected", id=self._id)
        try:
            async for item in self._inner.receive():
                self._bus.publish("connector.receive", id=self._id)
                yield item
        except Exception as e:
            self._bus.publish("connector.error", id=self._id, stage="receive", err=str(e))
            raise
        finally:
            self._bus.publish("connector.disconnected", id=self._id)
```

### Auto-create persistence connectors for a DataModel

```python
# facade/builder.py (sketch)
def register_data_model(self, name: str, dm: DataModel):
    self.data_models[name] = dm
    backend = self.default_persistence_backend  # e.g., SqlConnectorFactory
    for type_name, models in dm.get_top_level_models().items():
        conn_id = f"persist:{name}/{type_name}"
        conn = backend.make_connector(model=name, type=type_name)  # implements provide/consume/receive
        self.add_connector(conn_id, conn)
```

---

### REST chain step types (final list)

* `receive` (connector\_id)
* `provide` (connector\_id)
* `consume` (connector\_id)
* `map` (mapper\_id)
* `format` (formatter\_id, mode: serialize|deserialize)
* `call_workflow` (workflow\_id)

---

If you like, I can generate the initial stubs for:

* `ports/connector.py`
* `core/instrumentation.py`
* `facade/builder.py` (auto persistence wrapping)
* `adapters/connectors/memory.py` (default backend)
* `adapters/discovery/consul.py` (register payload with capability + I/O)

…so your agent has concrete files to start from.
