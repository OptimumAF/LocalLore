# Full-comparison window capability backport

2026-10-28 local date. Refs #29 D07.06; supports #23's native window lifetime
checks. **FIRST test/contract freeze on accepted main `d5a6e84c`: source only,
uncompiled and unrun.** The author performs no Cargo, Node, application, model,
phone or desktop-control checks. Root owns baseline execution, integration,
independent review, PRs and acceptance. Claims: #29 comment6487739410 and #23
comment6487739704.

## Existing source and precise problem

Accepted main supports Protocol3 full comparisons through a version1 scripted
wrapper and version2 approved-native wrapper. It has one full-run lifecycle,
one existing token map, the existing 900-second access-time expiry and four-token
per-epoch bound/LRU. It has no scene/Protocol4 API. This backport does not add one
or depend on unaccepted authoring work.

`full_token_lane` currently validates the token's numeric window epoch and the
run's lane. Independent `WindowLease` instances can begin at the same numeric
epoch. `Self::mint` currently reuses a token for an epoch/run pair without knowing
which lease received it. Merely adding an identity check while rebinding that
same token during another lease's explicit lookup would transfer its authority.

The proposed backport reuses reviewed source `35630d3e`'s narrow strategy:

- Give the existing native `WindowLease` an internal allocation identity held by
  an `Arc`; capabilities retain only a `Weak` reference. No serialized identity,
  renderer field, new counter or parallel inference/window manager is added.
- Keep ordinary minting defaults intact. Extract the existing mint algorithm's
  reuse predicate so full comparisons can reuse a token only for its minting
  lease. Preserve TTL, four-token bound and LRU logic.
- Bind both full-run mint sites. Validate lease identity, epoch and lane before
  token expiry is refreshed or a full-run control is performed.
- Keep the full-run identity side map limited by the existing token map, pruning
  on successful mint/check/close and by epoch at retirement. Maintain parent-state
  then full-state lock order; retirement must not invert that order.

No canonical state, storage schema, model ownership, report interpretation,
observer permissions or public command fields change.

## Frozen independent acceptance checks

The new `evaluation/comparison_run/window_identity_review.rs` uses only existing
public manager APIs, the accepted typed `Index` and `current_binding(native)`.
Its tiny synthetic source contains only wrapper metadata. It does not contain a
work directory, report, generated output, accepted receipt, NativeProfile or
canonical Store. Synthetic fixtures and failure evidence stay local; tests do
not delete them. The test commit includes only a cfg(test) module registration
in the production module; production logic is unchanged at this freeze.

Four finite cases are fixed before implementation:

1. Scripted Protocol3: same-owner lookup reuses its token; another authorized
   same-epoch lease receives a distinct token. Each owner can use its own token,
   while stolen status/cancel/resume/close calls return `UnknownEvaluationRun`.
   One close leaves the sibling handle valid; reopening obtains a fresh token.
2. Approved-native Protocol3: the same assertions, with the existing native API
   and a consent callback that must never be reached by a stolen token. This is
   native-service metadata, not approved native inference.
3. Dropping a token's original lease does not let a new same-epoch lease adopt
   the old capability. A new explicit lookup obtains a different token. This
   checks ownership lifetime, not forced allocator address reuse.
4. The existing four-handle limit remains four across same-epoch leases. A fifth
   authorized lookup evicts only the deliberately aged idle LRU entry; the
   other rightful handles remain usable and foreign uses refuse. No sleeping,
   new quota or TTL relaxation is introduced. This case covers both lanes.

Every case checks the entire quiescent source tree's file bytes before/after.
The two main lane cases also compare the application model manager's status.
Those finite observations do not independently measure reserve-and-release
counts; synchronous stolen-token refusal and the source branch establish the
intended before-admission boundary. No completed native run, worker cleanup,
WebView/native IPC, visual, Android or human-quality result is claimed.

Source-only fixture calibration before production: require `retained` on the
initial metadata lookup, not every later lookup. The accepted service keeps a
run's closed presentation phase after closing a handle; minting another valid
handle does not reset that shared run phase. The capability assertions remain
unchanged. No compiler or test result prompted or is claimed by this correction.

## Root verification and handoff

Run project commands from the physical D: checkout. On Windows set process-local
`TEMP` and `TMP` to `D:\Dev\_Temp` before launching tools, and direct Cargo cache
and target outputs to existing owned D: locations. Do not change global SDK or
cache settings. Reuse the pinned offline toolchain and locked dependency graph.

After the test freeze is committed, Root can execute the unchanged baseline:

```powershell
$env:TEMP = 'D:\Dev\_Temp'; $env:TMP = $env:TEMP
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --bin locallore-desktop-spike --jobs 1 --target-dir '<existing owned D: target>' evaluation::comparison_run::window_identity_review:: -- --nocapture --test-threads=1
```

Then apply the separate production backport commit and repeat the unchanged
cases. Preserve actual setup/compiler/test failures and exact source attribution;
source intent alone is not a RED or GREEN result. Run appropriate broader native
and compatibility checks, formatting and strict Clippy on the final integrated
source, obtain independent review and a fresh exact-head GitGuardian result, and
prepare the focused PR against main. This document grants no merge/release or
settings authority; existing owner instructions govern those operations.

All checks remain **UNRUN at author handoff**. A later execution handoff must
record actual commands, source revisions, versions, results and limitations.
