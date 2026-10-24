# M08 native author preparation port: source freeze

2026-10-23. Future M08.03 / D08.05 / D05 prerequisite, based on
`95db6af97107ba52918885759441a9a4eca953b6`; not part of the first-foundation
PR #131. This packet is source-only: no compilation, tests, provider, application,
device, or desktop execution. Frozen independent tests are commit `d5cd898` in
`crates/locallore-workspace/tests/m08_author_host_port_review.rs` (13 tests).
Missing proposed APIs mean these are not an observed behavioral RED.

## Closed native interface

`host::NativeAuthorPreparation: Any + Send` exposes only `preview() ->
&AuthorCorrectionPreviewV1`, `preview_bytes() -> &[u8]`,
`matches_parent_basis(&AcceptedHistoryBasis) -> bool`, and `as_any() -> &dyn Any`.
Three default-Unsupported `Persistence` methods prepare a boxed native
preparation, apply that preparation, and look up an exact native
`AuthorCorrectionInputV1`. Every method accepts the bounded cancellation callback.
No Core dependency on Store is introduced.

`Host::prepare_author_correction(session, input, cancel)` returns a private-field,
non-Clone, non-Serde `HostAuthorPreparation` with typed/byte preview getters only.
`Host::apply_author_correction(&preparation, cancel)` uses its captured session;
`Host::lookup_author_correction(input, cancel)` is explicit readonly inspection.
All three require the native Story Lab grant. No serialized HostCommand,
capability flag, generated schema, UI control, registry, journal, SQL, or migration
is added.

The native result `WorkspaceAuthorOutcomeV1` has exactly `version: u16` (1),
`scope`, `parent`, `fork_revision`, `author_revision`, `head_revision`, and
`created`. This derived metadata is not canonical authority. The private capsule
holds full exact input, the selected full accepted-history basis, actual boxed
Store preparation, stable typed/byte preview copies, captured session/work-owner,
and a Weak pointer to the existing Host state. Weak pointer identity and the
existing session work-owner fence foreign Host, reopen, close, and explicit
replacement; no extra owner Arc or repository keepalive is added.

## Authority and ordering

Preparation checks cancellation safely (including panic), selected scope, current
parent head, and active work on any same-parent session. It refreshes through the
existing Persistence resume and accepted-prefix guard. After actual Store
preparation, its full parent basis must equal the selected Host basis before any
private preview returns. Typed preview must match exact input; serialized preview
bytes must equal actual Core preview bytes and fit the existing 65,536-byte
receipt cap. Generic Host JSON input/output limits remain unchanged. The Store
getter compares its private captured basis only; it adds no writer or authority.

Apply first checks grant, Host owner, captured session, work-owner, and scope
identity. It then performs actual Store exact lookup with a fixed false
cancellation callback **before** invoking caller cancellation or admitting current
parent work/head/source. An existing exact commit wins: return actual
`created=false`, even for a true or panicking caller callback, without invoking
that callback. This bounded readonly lookup cannot authorize a new write.
Foreign/replaced/closed preparations cannot reach this lookup. If absent, safe
cancellation, pending work, refresh/current-head/full-source guards precede actual
same-port Store apply. No post-commit cancellation check demotes a committed
result. Explicit readonly lookup separately honors caller cancellation and needs
no live parent/session/current H, preserving actual retained-child and tombstone
semantics. Full hint recovery remains a later prerequisite.

The Repository wrapper contains the actual `PreparedStoreAuthorCorrection` and
downcasts only its private native wrapper. It calls the same existing
`Repository.store`; it never opens another Store on confirmation. Store remains
authoritative for owner, exact input collision, IMMEDIATE full-source/preview
checks, atomic child/author row, normalized receipt, retention, and replay.
Callback and faulty-port panics are caught inside the Host lock so they do not
poison it; callback panic closes as Cancelled. Callbacks must be bounded and must
not reenter Host or Store.

## Frozen acceptance oracles

The tests use actual Core author input/history and actual Store APIs. They cover:

- Exact readonly preview, escaped-control capacity above generic input cap, and
  unchanged canonical parent/missing child.
- Same-owner real commit; exact committed apply under true/panicking cancellation
  invokes no callback, adds no rows, and returns actual recorded metadata.
- Grant refusal, absent JSON command, ephemeral Unsupported, foreign/reopened
  owner and closed/replaced session fences.
- Fresh true/panicking cancellation, owner reuse, queued-work Busy/key retention,
  actual changed-parent Stale, and exact retry after parent advances.
- Full-input/kind collision, missing child, actual retained ancestry after parent
  deletion, tombstone nonresurrection, and explicit session replacement.
- Actual Store late commit return wins cancellation; actual same-head/different
  parent source fails before exposing preview. The two test-only Persistence
  wrappers delegate author operations to real Store, not forged receipts or SQL.
- Private preview/native inspection does not teach Mira the replacement; actual
  player re-observation leaves old knower A while world/player can see B.

Actual compile/runtime results, native broker consent, prepared-handle lifecycle
at the application boundary, recovery hints, Android/UI author exposure, and
whole-milestone acceptance are unavailable here. Root owns later execution and
integration. No production behavior is accepted on the strength of these source
oracles alone.

## Source handoff

Frozen tests: `d5cd898`; frozen contract: `ce31946`; production source:
`da94d1856e5c652339f544912ba09027dd2179fa`. The production commit changes only
the five allocated port/wiring/getter paths. Storage changes are exactly the
readonly `matches_parent_basis` getter; there are no writer/DDL changes. Existing
tests and generated schemas are unchanged. The separate thin-snapshot/Query2
future stacks are not prerequisites for this native-only source packet.

Static commands actually run (Rustfmt 1.8.0-stable, Rust 1.93.1):

```text
rustfmt --edition 2021 --check --config skip_children=true crates/locallore/src/host.rs crates/locallore/src/host/author_port.rs crates/locallore-workspace/src/lib.rs crates/locallore-workspace/src/author_port.rs crates/locallore-storage/src/author_correction.rs crates/locallore-workspace/tests/m08_author_host_port_review.rs
git diff --check
```

Both exited 0. Rustfmt is a source parser/format check, not a compiler or test.
No heavy qualification was authorized or run. SHA-256:

| Source | SHA-256 |
| --- | --- |
| Frozen 13-test source | `92962c0ad9515f3d7269d51e7cf873ac8bb59a51af8cc457ac67a016b01734b2` |
| Core Host native port | `e6ba269db36ad64561965744992ed2d0fdbfb62f915cb36d3cc7111b6b4e1224` |
| Repository native wrapper | `0ba8a20851952f6446e9ccf9b147f0869e5f41015305f99e2a56f8973e713d51` |

Next runnable task belongs to the coordinator: compile and execute the frozen
workspace integration test in an authorized heavy slot, preserve any first
compile failure separately from behavioral RED, then qualify compatible Core,
Store, workspace, and native consumers. Later application broker consent must
bind the full current UI/session/window/root context before consuming a capsule;
this native port does not implement that broker or make UI acceptance claims.
