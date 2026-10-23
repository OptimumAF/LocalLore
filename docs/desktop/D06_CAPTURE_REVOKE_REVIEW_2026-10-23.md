# Independent review of head-independent private capture revocation

Refs #28 D06.06/.07 partial. Reviewer `/root/resource_metrics_review`,
[claim6369326810](https://github.com/OptimumAF/LocalLore/issues/28#issuecomment-6369326810).
Separate `review/d06-capture-revoke` / `source-capture-revoke-review` worktree from
fresh accepted main `c496eb87147843958653b194aed0ca934fb03923`; unchanged coordinator
source `81af89793bca220ac75a7eb3c7adc732ee58d631` imported as
`e80408f2d4cd8fa3984bcc6309eb81d635cba925`. This review writes only this document.
No production, existing test or author-worktree edit was required.

## Disposition and boundaries

No blocking finding in this finite independent source review and executed checks.
This is agent review, not human approval or completion of D06. The coordinator
retains upstream integration and acceptance; UI/export consumers are separate work.

Read the complete endpoint diff, Host command parsing/dispatch/session checks,
trace control/clear and private consent/epoch recording paths, generated schema
and types, new owner/busy/late-write unit test, production Play wire regression
and existing poison/teardown tests.

`trace_capture_revoke {session, scope}` is native Story Lab only. It validates the
live original session and exact scope before operating on that session's opaque
TraceOwner. It does not accept an expected head or observer, refresh an Engine,
call `Persistence::resume`, assert a current durable revision, grant a read, or
change canonical state. Thus a later unavailable persisted reader cannot stop an
otherwise authorized diagnostic revoke. Configure and read retain their existing
fresh canonical-head, session/scope and privilege checks.

On an ordinary healthy trace ring, revoking the active consenting owner clears
its retained private artifacts/consent and advances the detail epoch. Other
owners' active consent is not revoked by this request. Metadata attempts, trace
enablement, live session and gameplay state survive. Existing RingSink handles
carry their original detail epoch, so late callbacks cannot refill revoked data
or bind themselves to later consent. Revoke is idempotent when the requester has
no active private consent; it does not need an existing selected attempt.

There are two distinct exceptional paths:

- A held trace lock returns `TraceUnavailable`. The endpoint does not claim that
  consent or retained copies were cleared; the caller must report/retry that error.
- A poisoned trace lock enters the **existing global trace-control recovery**:
  `set_enabled(false)` clears the entire window Host ring, including all metadata,
  private details and other owners' diagnostic consent, then clears trace poison.
  The revoke can return success after that broader diagnostic reset. This is not
  owner-only preservation under poison and must not be described that way.

That recovery touches process-local diagnostics only; it does not mutate the
canonical owner. A poisoned Host State is not silently trusted by this endpoint;
normal call failure remains explicit. State-poison teardown retirement is a
separate existing cleanup path. These locks, serialization and cleanup do not
establish a hard latency bound.

`revoked:true` refers to retained private capture state in this Host ring. It does
not erase caller-owned previously returned clones, UI/native export previews,
saved exports, OS paging or forensic copies. Consumers must separately clear and
fence their own presentation/export state. No model input or character knowledge
changes as a consequence of this diagnostic revocation.

## Independently executed verification

Windows x64 OS10.0.26300.0, Rust/Cargo1.93.1, Node24.22.1,
TypeScript7.0.2, Ajv8.20.0 and Prettier3.9.10. Locked offline Rust dependencies;
existing task-owned frontend dependencies reused through a local ignored junction,
without installation/download. New D: target and UUID TEMP/TMP only:

```powershell
$env:TEMP="$reviewRoot/temp-930da5f7"
$env:TMP=$env:TEMP
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_PROFILE_TEST_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo +1.93.1 test -p locallore --all-features --lib --test turn_capture --test turn_capture_host --test turn_capture_review --locked --offline --target-dir "$reviewRoot/target"
cargo +1.93.1 clippy -p locallore --all-targets --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 clippy -p locallore --all-targets --all-features --locked --offline --target-dir "$reviewRoot/target" -- -D warnings
cargo +1.93.1 fmt --all -- --check
git diff --check
# From apps/desktop with the existing pinned Node executable:
node node_modules/typescript/bin/tsc --noEmit
node check-contract.mjs
node node_modules/prettier/bin/prettier.cjs --check host-v1.schema.json ui/host.generated.ts
```

All exited0. **31 Rust tests passed,0failed/ignored**:21lib,5production Play
capture,1Host wire and4existing capture-review integration tests. The lib cohort
includes the new revoke case, existing busy/poison trace recovery, teardown and
actual generated-Rust schema equality. Strict default/all-feature all-target
Clippy, fmt, TypeScript, contract and changed-schema/type formatting checks passed.
Frontend contract execution validated25fixture JSON requests and4action builders;
it did not execute a native application.

The new unit actually replaces the persisted reader with a panic-on-resume port,
then revokes without invoking that reader. It proves foreign session/scope refusal,
preservation of another consenting owner, explicit busy failure, owner revocation,
late RingSink callback rejection, retained metadata and a still-live owner. The
wire test uses a deterministic synthetic provider through actual production Play
and Host JSON: at canonical revision1 the stale configure-disable at head0 fails,
while head-independent revoke succeeds. Its before/after PlaySnapshot is equal,
private bytes disappear from subsequent authorized reads, metadata remains, and
closed sessions refuse. Non-Lab Host refuses the endpoint.

Also executed an Ajv schema probe: the exact version1 session/scope command is
accepted; additions `expected_head`, `observer`, `enabled` and `consent` are each
rejected as extra fields. This is schema validation, not authorization evidence;
the Rust wire checks supply the session/privilege evidence. No new test hook or
general-purpose debug surface was introduced.

Local ignored evidence logs: `capture-revoke-review/tests-capture-allfeatures.log`,
`clippy-default.log`, `clippy-allfeatures.log`, `fmt.log`, `tsc.log`,
`check-contract.log`, `prettier.log` and `revoke-schema.log`. No generated data was
added to Git. Reviewed/tested source file SHA256 values:

| Path | SHA256 |
| --- | --- |
| crates/locallore/src/host.rs | `f8993017b36ec3422dbea01e99e032eb39d2b3d69165359d459a3179db386fb7` |
| crates/locallore/tests/turn_capture_host.rs | `8f1f7aabb0d462c86431b15285f729345b1cfee78203a3a581edb78d8b98b863` |
| apps/desktop/host-v1.schema.json | `7918c1844a3ce955550f7113d976cdaf051abc856fa62d5a3f69f12435d1f48e` |
| apps/desktop/ui/host.generated.ts | `d9517e58de33c292be810c9709b9260a652de0db535325d6ced39134600404ef` |

## Remaining work

This reviewer did not execute a model, native IPC/WebView/rendering, UI consent or
export journey, Android/device, network-block, packaging or erasure experiment.
The poison case above combines executed existing recovery tests with source
inspection of the new endpoint's call into that helper; no separate new
revoke-under-poison injection was added. Broader coordinator checks are not
relabeled reviewer execution. Next runnable task: coordinator integrate this
review with the shared API, then qualify the separately owned capture UI/export
consumer, including busy failure and context-switch revocation presentation.
Full D06 stays unchecked; no merge, release, settings or protected-resource action
was performed by this reviewer.
