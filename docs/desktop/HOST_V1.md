# Shared host contract v1

Source: `crates/locallore/src/host.rs`; frontend schema:
`apps/desktop/host-v1.schema.json`. Domain request/receipt semantics remain
[domain-v1](../DOMAIN_CONTRACT_V1.md). The provider remains fake. Native
construction selects an ephemeral fixture Host or a Host backed by the shared
SQLite owner. The production desktop and Android apps use the latter; D02
compatibility journeys explicitly use memory fixtures. This is not a general
RPC server or a real inference pipeline. Behavior below describes accepted main
`2612001`, after D01 #33, D02 #36 and shared app integration #42.

## Wire and capabilities

Every input is `{ "version": 1, "command": { "op": "..." } }`.
Unknown fields/operations, malformed JSON/UTF-8, noninteger values and unsupported
versions reject without echoing input. Limits: 24,576 input bytes, 262,144 reply
bytes, four sessions, 64 retained turns per session and four retained generation
workers across session churn. IDs are opaque strings, never pointers or JS numbers.
The 64-turn limit concerns live session retention; reopening durable history does
not reset its canonical revision. Storage separately bounds a root branch to
4,096 persisted turn IDs, 65,536 bytes per receipt and 16 MiB of combined request/
receipt history, and the app library to
256 stories. Full player/history replies can reach the smaller reply limit first
and return `TooLarge`; the UI does not promise unlimited history. Arbitrary
JS-large revisions cannot commit because they fail exact revision checks. The
frontend schema checker additionally requires safe integers.

Replies are `{version:1,status:"ok",data:...}` or
`{version:1,status:"rejected",error:"Category"}`. No exception detail or private
input enters error categories. Tauri transport failures are separate; the UI
resolves an uncertain commit through `turn_status` before deciding its outcome.
An unknown turn is unknown, not evidence of durable rollback after process loss.

| Operation | Input / behavior |
|---|---|
| `capabilities` | Typed actions and trusted Story Lab grant reported; `persistence` reflects native construction. Free text, author actions and snapshot export remain unavailable |
| `workspace` | Metadata only: `persistent`, `location`, `schema_version`, `stories`. Durable entries contain `scope`, `title`, `revision`, `drafts`, sorted by story ID. Fixture Host returns false/null/null/empty list |
| `create` | Allowlisted `seed: "lantern-quay-v1"`; returns fresh session, unique story scope, branch and revision. Durable Host allocates an opaque random story ID and saves the seed; fixture Host uses process-local `quay-N` identities |
| `resume` | Durable only: exact `scope`, returns session/scope/revision after validated replay; refreshes an existing live attachment. Fixture Host reports `Unsupported` |
| `open` | Existing live session + exact scope; returns current revision. Durable Host reloads validated storage first. A closed session must be reattached through `resume`, not reused |
| `close` | Exact session + scope; cancel owned active turns and release the attachment. Durable saves remain; fixture history is discarded. Unknown/closed sessions report `Closed` |
| `submit` | Session, full domain `request`, fake `mode`; explicit scope, turn ID, expected revision and typed intent; validate mechanics before queueing |
| `prepare` | Session + scope + turn; bounded fake pipeline on a captured clone; never canonical mutation |
| `commit` | Session + scope + turn; serialize and recheck cancellation/revision, validate narration and apply once |
| `cancel` | Session + scope + turn; cancel queued/running/ready work; committed outcome stays committed |
| `turn_status` | Session + scope + turn; phase/error and committed receipt. Durable Host looks up the original stored request and outcome across restarts; fixture status exists only while its session is retained |
| `inspect` | Session + scope + observer + expected revision; coherent immutable serialized context or explicitly granted omniscient projection/history |
| `play_snapshot` | Session + scope + expected revision; one coherent player context, player-owned inventory, recorded `rules` profile and finalized player-request receipts; rejects stale revision |
| `model_status` | Honest fixed fake marker; no real model loaded |
| `free_text` | Session + domain request; scope-validated `Unsupported`; no model interpretation of player text |
| `snapshot_export` | Session + scope + expected revision; validated `Unsupported`; no path or file capability |

Phases: `queued → running → ready → committed`, with terminal `cancelled`,
`failed` and `stale`. A queued request can be preflight-rejected before a turn
record exists in the fixture Host. Durable submission records a draft before its
mechanical preview and records failure if that preview rejects. Exact duplicates
return their recorded outcome, including failure; new attempts after a terminal
failure need a new turn ID. An uncertain acknowledgement must retain its original
key. Reusing an ID with a different full request returns `RetryMismatch`. Fake
mode is also checked against a retained live turn; mode is not persisted in the
canonical request or receipt. Across process restart the recorded request/outcome
owns idempotency. Retention limits reject
new turns instead of discarding idempotency history. Sessions must be explicitly
closed; this prototype does not run an eviction policy or unlimited history.

Fake modes are `accepted`, `delayed`, `rejected`, `malformed`, `failed` and
`cancelled`. Delayed mode makes four 50 ms waits on the preparation worker,
checking cancellation between polls; it measures synthetic lifecycle behavior,
not real inference. `live_counts()` is a trusted adapter diagnostic, not a wire
operation or authority to inspect stories.

## Ownership, snapshots and authority

The fixture Host mutex serializes canonical writes. In durable mode the shared
SQLite owner commits canon atomically; Host engines are validated caches, not a
second ledger. Multiple native calls/processes can prepare the same revision;
only a compatible commit wins. Generation uses
`inference::execute` on a clone because that API commits its supplied engine.
No canonical lock/write transaction spans generation. Worker ownership stays
counted until dropped, including after session close. Cancel, close and revision
changes fence even a successful late completion. D02 story switching cancels
and fences pending work while retaining up to four live sessions and separate
session-local composer drafts. In production, New/Reset creates a distinct saved
story and Close retains the save; fixture reset/close discards that attachment's
memory history. A window teardown calls `close_all`, releasing sessions and
signalling owned workers. It performs no database write: interrupted stored
drafts remain uncommitted, visible by count and never automatically adopted.
Process death loses fixture history and unsent composer text, while durable
accepted receipts survive validated resume.

Durable submission, resume and observed terminal outcomes refresh from storage;
worker completion reconciles stored status before publishing. Competing commits
and cancellation are resolved by the existing store transaction. Transient read
or terminal-write failure leaves the original key recoverable. See
[app integration](../storage/APP_INTEGRATION.md) for limits and recovery semantics.

Reads serialize a single revision under the host lock. Future snapshot handles,
pagination and historical revision selection require contract evolution; there
is no live mutable projection handed to JavaScript. Large inspection replies
return `TooLarge`; they do not truncate or fabricate a partial canonical view.
The prospective committed receipt is size-checked before mutation. A failed
transport after accepted commit must use lookup, not resubmit a different turn.

Native construction determines inspection rights (`Host::default()` is
player-only; `Host::new(true)` is the deliberate spoiler-bearing developer app).
Only the native app-owned `main-<epoch>` window has Tauri app-command permission,
and Rust validates its live epoch. Initialization and non-prepare calls share a
control gate; Destroyed invalidates the epoch synchronously and cleanup completes
before a new window lease is granted. Preparation runs outside that gate and
uses Host session/cancellation fences. A wire observer cannot enable Story Lab. Within an authorized
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
