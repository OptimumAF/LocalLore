# Native verified-memory inspection adapter

Refs #26 D05.05/.06/.07, #28 D06.04/.07, supporting #11 M07.03/.04.
Status: SOURCE-ONLY, UNCOMPILED/UNRUN at handoff. This packet supplies the native
leaf and test source, not command registration, frontend controls or qualification.
Base: accepted `3f75b5d673512b165e18b2b1e34d3deafc69067a`.
Core dependency: frozen contract `1d644c81` and producer
`37c88c2975566f915f9881e3b23f3f98ccc359d8`,
`locallore::host::memory_inspection`. Root coordinates integration and execution.

## Owned files and authority

The packet owns only new `src-tauri/src/memory_inspection_commands.rs`, its child
`memory_inspection_commands/tests.rs`, and this document. Root separately owns
the module declaration, command registration, build allowlist and permission.
No existing Main, Host, Store, schema, provider, model, dependency or Android file
is changed. No second memory implementation, query backend or reader registry
is introduced.

The adapter calls exactly the existing Host's typed `memory_inspection` method.
Core independently requires its native Story Lab grant and Player observer,
checks selected session/scope/head/seed/history, rechecks coverage and binds the
complete source. Packet bytes, cursor hashes and inspection privilege grant no
execution, author mutation, character knowledge or generation permission.
Domain2 remains explicitly Unsupported. No maintenance admission, rebuild,
repair, status joining, provider construction or canonical/cache write is called.

## Command and closed input

The sole proposed registration is:

```rust
memory_inspection(window, workspace, action: String, request: String)
    -> Result<serde_json::Value, String>
```

`action` is exactly `packets`, `entries` or `source`. The raw request is at most
4096 UTF-8 bytes. Core `engine::parse_unique_json` rejects recursive duplicate
keys, including equivalent escaped keys, before conversion to typed selectors.
The adapter does not deserialize any canonical Engine, receipt or packet.

All requests require these common keys, with no extras or missing keys:

`version,session,scope,expected_head,observer,binding`.

- `version` is integer1. Other integer versions return Version.
- Session/story/branch use1..64 ASCII letters, digits, hyphen or underscore.
  Scope is exactly `{story,branch}`. No renderer path or native owner is selected.
- Head is a JSON integer0..9007199254740991. Numeric strings, booleans,
  fractional/floating representations, negatives and unsafe integers refuse.
- Observer is exactly `{kind:"player"}`. Structurally valid Character/Omniscient
  selectors return Forbidden before Host/workspace IO; malformed/extra observer
  fields return InvalidInput. A Character named player is still forbidden.
- Binding is explicitly null or lowercase64-hex. Entries/source require it.
  It is a read identity, never a signed or persisted capability.

Packets adds exactly `cursor,limit`. Entries adds exactly
`packet_index,cursor,limit`. Source adds exactly `packet_index,source`, where
source is `{scope:{story,branch},sequence}`. Packet index is integer0..31;
limit is integer1..64; source sequence is positive and no greater than head.
An original ancestor source scope is preserved; only Core determines membership.

Cursor is explicitly null or a maximum128-byte canonical
`mp1:<positive decimal offset>:<lowercase64-hex>` string. Leading zeroes and
overflow/unsafe offsets refuse; any cursor requires a nonnull binding. Core
still recomputes the cursor digest against actual binding/view/packet/limit.
This syntax check neither authenticates a cursor nor permits skipping a source
read. Invalid cursor syntax returns InvalidCursor; structural binding errors
and other malformed input return InvalidInput. Oversized raw input is TooLarge.
There are no grant, policy, model, prompt, SQL, search, consent or filesystem keys.

## Admission, cancellation and publication

The command captures the current WindowLease before workspace initialization.
Parsing runs on the UI thread only within the small fixed input bound.
One application-global AtomicBool slot admits a memory inspection nonwaitingly;
a concurrent request returns Busy before workspace initialization/Host IO.
The private non-Clone RAII permit remains owned across asynchronous Host lookup,
the blocking worker, serialization and final publication. Return, initialization
failure and unwind release it. There is no queue, background scheduler, retained
reader, TTL or second application state field. Other native operations do not
acquire this slot; it bounds this command's concurrent snapshot/hash workload,
not the entire app's memory or elapsed time.

Host and Store IO/hash work runs in `spawn_blocking`. Its cancellation callback
is only `!lease.valid(captured_epoch)`; no renderer supplies a cancellation grant
or callable. The worker checks the lease before and after Host execution.
An invalidated window returns Closed even when Core reports Cancelled from the
same invalidation. The final small `lease.dispatch` covers publication only;
it never encloses snapshot reads or the potentially64MiB Core binding stream.
Frontend selection epochs must separately reject late responses in future UI.

The reply is the actual Serialize-only Core DTO, converted to a JSON Value.
Compact UTF-8 serialization is capped at65536 bytes before publication, with
no truncation or synthesized rows. Core owns whole-row paging, JavaScript-safe
integer output and the exact Query2 source page on the same immutable Engine.
No seed, full basis or job/model/path metadata is added by this adapter.

Only the closed Core error enum is mapped to fixed native strings:
Version, Forbidden, Closed, Scope, Stale, Unsupported, InvalidInput,
InvalidCursor, Binding, TooLarge, Cancelled, Integrity, Unavailable, Busy,
Database, Full, Internal. Serialization/join failure is Internal; underlying
panic/path/error text is not returned. This command does not infer cleanup,
generation or durable write success from its slot or window acknowledgement.

## Frozen service/parser test source

The child source uses actual Core-created Wait receipts, ordinary Store APIs and
the actual Workspace Host. It introduces no SQL canonical writer or provider.
The native service tests call the same `read_owned` path as command dispatch.

- Valid action shapes, original ancestor source and exact integer/identifier edges.
- Recursive/escaped duplicate keys, malformed input, trailing JSON and privilege fields.
- Unsafe/coerced numbers, binding/cursor/index/source bounds and unknown action/version.
- Player-only parsing, including refusal of Character{id:player} before Host access.
- Missing cache: actual raw fallback, no implicit job admission or source mutation.
- Explicit test setup rebuild, verified packet/entry reads and exact actual Query2 source.
- Actual Lab/scope/head/binding refusal with source preservation.
- Actual Store author correction: Domain2 Unsupported, parent and child remain intact.
- Nonwaiting slot exclusion plus release on error and fixed caught unwind.
- Window invalidated as an actual Store snapshot returns: no response publication;
  old epoch refuses, source remains intact and the slot is reusable.

Passive invariance compares full canonical-record bytes/opaque valid basis,
actual passive job fields and serialized verified packet bytes through existing
Store APIs. It does not claim forensic SQLite/WAL/SHM byte invariance, a whole
database SQL audit, power-loss behavior or a hard process heap bound. The late
snapshot fixture is a private test Persistence adapter over an actual Store;
it does not change production Host/Persistence behavior.

## Root integration and remaining gate

Root must integrate the Core dependency, declare this module, register only
`memory_inspection`, and add its fixed build/ACL permission using existing
patterns. Root then compiles/runs the parser/service source, Core/Workspace
inspection regressions, normal/dev native Rust suites, strict Clippy/format,
normal-bundle exclusions and compatibility. First compile failures and actual
behavior failures must be retained separately; missing module/API compilation
does not establish behavioral RED.

No checker, Rust test, compiler, formatter, model, worker, application, native
WebView, OS dialog, device or desktop operation was executed by this packet's
source author. There is no frontend/native IPC or render qualification here.
Future UI must bind every page/source response to its current session, scope,
head, Player selection and exact source binding. Semantic summaries, Domain2
maintenance, models, physical-phone/quality/resource qualification and complete
D05/D06/M07 acceptance remain separate.
