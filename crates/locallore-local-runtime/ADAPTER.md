# Optional shared-engine adapter

Refs #25 D04.02/.04 and #9 shared M05. Claim comments6356602412/6356602624.
The `engine-adapter` feature depends on the existing portable `locallore` crate;
the portable engine does not depend on this Windows runtime or on desktop code.
It consumes the coordinator's `Input::Structured` contract from b858923.
Legacy Director/Narrator fake inputs are rejected, without fake fallback.

```rust,ignore
use locallore_local_runtime::adapter::{RuntimeProvider, SharedRuntime};
let shared: SharedRuntime = std::sync::Arc::new(std::sync::Mutex::new(loaded_runtime));
let mut provider = RuntimeProvider::new(shared.clone());
// Supply this provider to the authoritative shared play pipeline on a background worker.
```

Create one provider per turn. It accepts an immutable director request, at most one completed director repair, then one
narrator request for the same story/branch/turn/revision/model profile. Identical
polls return the cached result. A repair may change its bounded prompt while
the same turn identity and schema remain fixed; a second repair is rejected before native work. A changed active prompt, role, schema, budget or
scope is fenced with RetryMismatch and cancellation; another turn needs a new
provider. Public model profile must match the pinned PROFILE constant. Roles are
director/narrator, schema must be an object, output cap is1–350tokens/1–16384
bytes. Role parent deadline is min(request deadline,60000ms); the shared pipeline
separately owns its complete-turn/repair budget.

The first poll starts one named bounded background generation thread and returns
Pending. It uses `try_lock` on the single shared native owner; competing work
returns Provider with private `last_failure() == Busy`, rather than queueing
unbounded model work. Later polls only compile/compare bounded identity and poll
the result channel. Cancellation and mismatched polls signal the local token
promptly. Dropping the provider cancels and joins the generation owner after the
native parent's bounded terminal drain/reap. No thread is detached. The shared
engine should call this adapter from its existing preparation worker, not the
native UI thread. A panic during the owned thread joins as Cleanup and fails/
reaps the exact native runtime before returning an error.

The original Cancellation clone and a provider-local Drop token both reach the
native parent's cancellation callback. The latter does not cancel another turn's
token. The shared engine still rechecks cancellation/revision before committing;
provider output cannot mutate canonical state. Cancelled/lost/late output is
never treated as an accepted receipt by this adapter. Runtime Cancelled/Timeout/
InvalidRequest map to engine Cancelled/Timeout/Rule; other runtime failures map
to Provider while their fixed category remains in `last_failure()`. `metrics()`
retains only bounded aggregate native metrics, no prompts or generated trace.

Verification in this adapter packet used model-free processes only. Commands:

```powershell
$env:CARGO_PROFILE_DEV_DEBUG='0'
$env:CARGO_INCREMENTAL='0'
cargo fmt --manifest-path crates/locallore-local-runtime/Cargo.toml --check
cargo build --manifest-path crates/locallore-local-runtime/Cargo.toml --bins --all-features --locked --offline
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline
cargo clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
```

15 tests passed (seven existing native-owner tests and eight adapter tests).
Adapter cases cover legacy/invalid-role/profile/budget rejection, exact repeat
polls and sequential roles, active scope/prompt/role mismatch poisoning, competing
ownership Busy, post-completion different-turn rejection, one permitted completed director repair,
second-repair/schema/scope rejection, and prompt cancellation
with Drop terminal/reap. Existing hostile frame/pipe/identity/timeout tests remain
enabled. The cancellation test observes poll return under50ms, then confirms
Drop within4s and an exited native fixture child. These are finite local timing
bounds, not device/UI responsiveness qualification. Initial strict Clippy caught
an unnecessary unwrap; it was fixed before the final clean check.

No new model calls, native renders, shared canon/receipt changes, inference
pipeline, database or mobile backend were added. Actual native model lifecycle
evidence remains in the earlier D04_RUNTIME verification. Integrated real scene,
durability, semantic-prose evaluation and app responsiveness remain coordinator
gates; adapter tests alone do not establish them.
