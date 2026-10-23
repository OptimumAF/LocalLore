# Revoke private capture independently of the story head

Refs #28 D06.06/.07 partial. This adds one narrowing Host-v1 command for the
private-capture UI; it does not grant capture/read/generation or character
knowledge privileges.

```json
{"version":1,"command":{"op":"trace_capture_revoke","session":"session-1","scope":{"story":"synthetic","branch":"main"}}}
```

Only a natively constructed Story Lab Host accepts it. The live session must
match the exact scope. Success data is `{version:1,scope,revoked:true}`. There
is deliberately no `expected_head`: accepted progress or an unavailable Store
reader must not prevent deleting optional diagnostics. The operation calls no
persistence method, performs no canonical mutation and leaves the session live.
Existing configure/read commands still require the fresh persisted head and
explicit enable consent. Extra fields are rejected by the strict wire schema.

With a healthy diagnostic ring, revocation clears only the selected owner's
private consent/copies and invalidates their detail epoch. Metadata and other
owners' consent survive. A late artifact callback cannot restore old copies.
A busy ring returns TraceUnavailable; success/erasure is not fabricated. The
existing poisoned-ring recovery policy is different: it clears/disables the
whole untrusted diagnostic ring before returning success, including other
owners' metadata/consent. Poison recovery never makes diagnostics canonical.
This is logical access/copy removal, not forensic erasure, revocation of already
detached copies or deletion of user exports/OS paging.

Production source `81af897` extends the actual production-Play Host wire test:
capture a real candidate, commit it, prove the old-head configure is stale,
revoke without a head, then compare unchanged Play snapshot/receipt and retained
metadata. Unprivileged and closed sessions are refused. A separate Host unit
proves wrong-scope refusal, another owner's retained copies, explicit busy
failure, late-copy fencing and live session ownership. Its deliberately
unreadable persistence stub panics if resume is called; revocation succeeds
without calling it. It is a diagnostic API regression, not a new Store path.

Initial locked/offline checks on that source: **389 workspace tests passed,
four existing qualification ignores**, strict default/all-feature workspace
Clippy, fmt, frontend/schema/controller checks passed. Independent review on
accepted #91 plus this delta actually ran **31 focused Core tests**, strict
default/all-feature Clippy, TypeScript, current contract/Prettier and an Ajv
probe that accepts only the exact new command and rejects head/observer/enable/
consent additions. See `D06_CAPTURE_REVOKE_REVIEW_2026-10-23.md` for its source,
hashes, commands and limits; no fabricated human acceptance is implied.

Final coordinator integration production
`e50f1cb70ce48e930ad7d24ccf1d778d1264c764` includes accepted main
`8e55a98e29235dbc28336022ad3a17f1378747eb` (#92). The unchanged revoke source
passed **407 complete workspace tests**, zero failures, four existing ignores;
frontend verification and native **44 module + 2 harness contract tests**, one
existing ignore, passed. Strict native all-target Clippy passed. Commands:

```powershell
cargo +1.93.1 test --workspace --all-features --locked --offline --target-dir <core-target>
cargo +1.93.1 clippy --workspace --all-targets --locked --offline --target-dir <core-target> -- -D warnings
cargo +1.93.1 clippy --workspace --all-targets --all-features --locked --offline --target-dir <core-target> -- -D warnings
cargo +1.93.1 fmt --all -- --check
node apps/desktop/verify-frontend.mjs
cargo +1.93.1 test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --locked --offline --target-dir <native-target>
cargo +1.93.1 clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --all-targets --locked --offline --target-dir <native-target> -- -D warnings
```

Windows Rust/Cargo1.93.1, Node24.22.1; locked dependencies, development/test
debug=0 and incremental=0, task-owned D targets and UUID TEMP/TMP. Initial core
logs use `capture-revoke-*`; final integration logs use
`capture-revoke-integrated-*` under `m07-derived`/`archive-ui-native`.
Core strict Clippy ran on the earlier identical revoke production files; the
intervening accepted pure coverage module has its separately passing default/
all-feature gates in #92. No source assertion was weakened.

No native capture UI, export, render, actual-model, Android/device or physical
erasure check was executed for this API slice. Native tests establish adapter
compatibility, not that missing UI journeys ran. The separately claimed D06
frontend/private-export adapter consumes this endpoint and must supply its own
actual IPC/render and consent/privacy evidence. Full D06 remains unchecked.
