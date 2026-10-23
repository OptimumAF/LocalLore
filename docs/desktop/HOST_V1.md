# Shared host contract v1

Source: `crates/locallore/src/host.rs`; frontend schema:
`apps/desktop/host-v1.schema.json`. Domain request/receipt semantics remain
[domain-v1](../DOMAIN_CONTRACT_V1.md). This is an in-memory fake-provider
service, not persistence, a general RPC server or a real story pipeline.

## Wire and capabilities

Every input is `{ "version": 1, "command": { "op": "..." } }`.
Unknown fields/operations, malformed JSON/UTF-8, noninteger values and unsupported
versions reject without echoing input. Limits: 24,576 input bytes, 262,144 reply
bytes, four sessions, 64 retained turns per session and four retained generation
workers across session churn. IDs are opaque strings, never pointers or JS numbers.
This bounded seed has at most 512 event revisions per session; arbitrary JS-large
revisions cannot commit because they fail the exact revision check. The frontend
schema checker additionally requires safe integers.

Replies are `{version:1,status:"ok",data:...}` or
`{version:1,status:"rejected",error:"Category"}`. No exception detail or private
input enters error categories. Tauri transport failures are separate; the UI
resolves an uncertain commit through `turn_status` before deciding its outcome.
An unknown turn is unknown, not evidence of durable rollback after process loss.

| Operation | Input / behavior |
|---|---|
| `capabilities` | Typed actions available; free text, durable saves, author actions, snapshot export unavailable; trusted Story Lab grant reported |
| `create` | Allowlisted `seed: "lantern-quay-v1"`; returns fresh session, unique story scope (`quay-N`), branch and current event revision |
| `open` | Session + scope; attach to an existing in-process workspace; cannot reopen after close/process death |
| `close` | Session + scope; invalidate leases/cancel workers and release history; unknown/closed sessions report `Closed` |
| `submit` | Session, full domain `request`, fake `mode`; explicit scope, turn ID, expected revision and typed intent; validate mechanics before queueing |
| `prepare` | Session + scope + turn; bounded fake pipeline on a captured clone; never canonical mutation |
| `commit` | Session + scope + turn; serialize and recheck cancellation/revision, validate narration and apply once |
| `cancel` | Session + scope + turn; cancel queued/running/ready work; committed outcome stays committed |
| `turn_status` | Session + scope + turn; retained phase/error and committed receipt; exact retries return the original outcome |
| `inspect` | Session + scope + observer + expected revision; coherent immutable serialized context or explicitly granted omniscient projection/history |
| `play_snapshot` | Session + scope + expected revision; one coherent player context, player-owned inventory and finalized player-request receipts; rejects stale revision |
| `model_status` | Honest fixed fake marker; no real model loaded |
| `free_text` | Session + domain request; scope-validated `Unsupported`; no model interpretation of player text |
| `snapshot_export` | Session + scope + expected revision; validated `Unsupported`; no path or file capability |

Phases: `queued → running → ready → committed`, with terminal `cancelled`,
`failed` and `stale`. A queued request can be preflight-rejected before a turn
record exists. Exact duplicates return their existing phase, including failure;
new retries after a terminal failure need a new turn ID. Reusing an ID with
different request or fake mode returns `RetryMismatch`. Retention limits reject
new turns instead of discarding idempotency history. Sessions must be explicitly
closed; this prototype does not run an eviction policy or unlimited history.

Fake modes are `accepted`, `delayed`, `rejected`, `malformed`, `failed` and
`cancelled`. Delayed mode makes four 50 ms waits on the preparation worker,
checking cancellation between polls; it measures synthetic lifecycle behavior,
not real inference. `live_counts()` is a trusted adapter diagnostic, not a wire
operation or authority to inspect stories.

## Ownership, snapshots and authority

The host mutex is the sole canonical writer owner. Multiple native calls can
prepare the same revision; only one compatible commit wins. Generation uses
`inference::execute` on a clone because that API commits its supplied engine.
No canonical lock/write transaction spans generation. Worker ownership stays
counted until dropped, including after session close. Cancel, close and revision
changes fence even a successful late completion. D02 story switching cancels
and fences pending work while retaining up to four in-memory sessions and
separate drafts. Reset/close releases the affected session; neither is a save.
A window teardown calls
`close_all`; process death discards this explicitly ephemeral state.
Each creation is a distinct story. Multiple windows opening one existing
session share its canonical owner; creating another session cannot create a
second writer for the same story scope.

Reads serialize a single revision under the host lock. Future snapshot handles,
pagination and historical revision selection require contract evolution; there
is no live mutable projection handed to JavaScript. Large inspection replies
return `TooLarge`; they do not truncate or fabricate a partial canonical view.
The prospective committed receipt is size-checked before mutation. A failed
transport after accepted commit must use lookup, not resubmit a different turn.

Native construction determines inspection rights (`Host::default()` is
player-only; `Host::new(true)` is the deliberate spoiler-bearing developer app).
Only the local main window has Tauri app-command permission, and Rust checks
its native label. A wire observer cannot enable Story Lab. Within an authorized
lab, non-omniscient views use `Engine::character_context`; omniscient reads never
feed back into player/NPC model contexts. Invalid story/branch/observer and stale
revisions reject before returning content. Author mutations remain unsupported.

## Schema maintenance

Generate from Rust, never edit the JSON schema independently:

```powershell
cargo run --locked --offline -p locallore --features host --example host_schema | Set-Content -Encoding utf8 apps/desktop/host-v1.schema.json
cargo test --locked --offline -p locallore --features host
cd apps/desktop
npm ci --ignore-scripts --no-audit --no-fund
npm run check
```

Schemars derives share the existing `Scope`, `Request`, `Intent` and `Command`
definitions. A regression compares the checked schema with fresh Rust output;
Ajv validates frontend action builders and the native smoke fixture against it.
Domain/host semantic validation remains in Rust. `build.mjs` generates request
types in `ui/host.generated.ts` from the same schema. The frontend checks the
coherent player-view/receipt envelope before display; it introduces no gameplay
reducer. Rust remains the semantic authority.
