# Narration diagnostic Host read v1: partial qualification

2026-10-29. Refs #9 **M05.03/M05.04**, #29 **D07.04**.
**Implemented; focused/schema/frontend compatibility measured; broad gates pending.**
Measured source: `fab59b0761a0585ff57cc8b8e315d7134f8805e2`.
This Host adapter is not UI adoption, Eval persistence, native IPC/WebView,
model/device evidence, human-quality acceptance or full task acceptance.

## Scope and preserved boundaries

The [accepted contract](D07_NARRATION_DIAGNOSTIC_HOST_READ_CONTRACT_2026-10-29.md)
and [HOST_V1 operation](HOST_V1.md#opt-in-narration-validation-read) define the
opt-in `trace_narration_validation_read_v1`. Its required session/scope/current
head/base revision/turn/attempt select the existing owned player attempt.
Native u32 conversion precedes the unchanged shared Core selector preflight;
no JSON observer, owner, handle or privilege is accepted.

A valid non-Story-Lab command is denied after bounded parse/version checks and
before State/session/StoragePort/source access. Existing TooLarge/Malformed/
Version precedence remains. The synthetic Host spy and poisoned-State tests
exercise this **Host-level** zero-probe boundary. Desktop cold
`WorkspaceState::get` can initialize/open storage and reap previews before Host;
these tests do not establish transport-wide zero filesystem activity.
Authorized existing admission can retire/cancel an invalidated attachment on
NotFound. Session/scope/storage/current-head/selector errors remain distinct from
an authorized unavailable diagnostic; whole-Host side-effect freedom is not claimed.

Plain trace `try_lock` returns authorized Unavailable on busy/poison without
recovery, clear, retry or configuration. Reads add no attempt, provider request,
validation/cancellation pass, canonical mutation or knowledge/generation grant.
The separate Serialize-only DTO binds session/scope/head/base/turn/attempt,
literal observer player and `generation_grant:false`. Recorded includes exactly
the four decision fields; Unavailable has no decision key. Fixed actual tuple
projection maps unsupported/inconsistent metadata to Unavailable, never an
invented Unclassified cause. The new operation's **entire envelope**, including
rejected replies, is capped at 4,096 bytes without truncation; old global limits,
trace/capture/PlayRecord/Report4 formats and other operations remain unchanged.
Core changes only the existing selector helper's crate visibility.

## Independent FIRST provenance and preserved source finding

The Phase2 [retention gate](D07_NARRATION_DIAGNOSTIC_RETENTION_QUALIFICATION_2026-10-29.md)
precedes this slice. Formal Host interface acceptance is `27c2607a`.
Independent original six-group test source `a2f5f967` integrates as `0fa0b7cb`;
Root registers/formats it at `8ca5a988`, with module order at `bd4e26d0`.
The original 555-line freeze SHA256 is
`2afb14de702bbcc9ceeeb5519122f6a77750c7324ebb64857b670f4c17a8d94a`;
rustfmt equality proves the registered source SHA256
`e1ae862213cfe1cee595bc7422825d0105975d3ec45bb452fd38b25586ab087e`.
Missing operation/helper/schema were setup prerequisites, not a behavioral RED.

Before production or Rust test execution, Root found that the fixture's global
JSON token replacement renamed the required Seed `player` property key while
changing a nonliteral actor ID. This was local JSON/source inspection, not a
measured Host/Engine failure. Preserve the original freeze and finding.
Independent typed-Seed correction `ea06232a` integrates as `17f447f8`: it changes
only exact actor-ID values/map keys, retaining schema keys, ordinary text,
nonliteral-player coverage and the synthetic privacy sentinel. The correction
proof preserves all six test bodies/helpers after that fixture function.
Corrected immutable SHA256:
`14f4752332fcd5a81ce16fec9f8c3883c7a55543ea4503887d69f3fb396d4aac`.
No runtime failure, repaired capture or weakened oracle is claimed for this fix.

Production `463339c7` integrates as `49ec08de`; rustfmt is `2a977a94`.
Independent source review at `2a977a94` reported no blocker; review is separate
from execution. Production remains unchanged through measured `fab59b07`.

## Actual generation and completed checks

Private absolute target arguments below are normalized to `<owned-D-target>`;
the private absolute Node executable is normalized to `node`. Local records keep
exact paths/arguments/timestamps. No other command argument is normalized.

At clean `2a977a94`, Root ran existing generators, not new generator code:

```text
cargo run --manifest-path Cargo.toml --locked --offline -p locallore --features host --example host_schema --target-dir <owned-D-target>
node apps/desktop/build.mjs
```

Rust JSON stdout was used as `apps/desktop/host-v1.schema.json` before the Node
build; the commands above are the recorded child invocations.
Both exited 0: recorded Rust stage 10.6963861s; combined generation 12.6789727s.
The remaining stage includes Node generation; no isolated Node process duration
is claimed by this record.
The first production compile/generation passed. Source head was unchanged;
only expected tracked schema/type files were dirty, with no unexpected tracked
changes. This generation record is not a test result. `1f8b29bd` commits generated
requests; pinned Prettier3.9.10 restores established JSON formatting at
`fab59b07`. The combined request-only delta is 43 schema lines plus 9 type lines.
The actual Rust/schema semantic equality test below passes. Generated types
describe requests; no new response decoder or frontend consumer exists.

All nine completed check records below report exit 0, clean unchanged
`fab59b07` and empty dirty lists:

| Check | Actual result | Command duration |
| --- | --- | --- |
| Rust/schema equality | 1 passed, 0 failed; 99 filtered | 8.8987370s |
| Frozen Host-read filter | 6 passed, 0 failed, 0 ignored; 94 filtered; 0.23s test | 0.5008883s |
| Existing Host scene recipe suite | 4 passed, 0 failed; 0.09s test | 1.8686413s |
| Existing native retention filter | 11 passed, 0 failed; 89 filtered; 0.27s test | 0.5455744s |
| Strict all-feature/all-target workspace Clippy | Passed | 40.8931979s |
| Workspace formatting | Passed | 2.0324866s |
| Core without default features | Passed | 2.2161284s |
| Android Rust host compilation | Passed | 3.3266871s |
| Full frontend checks/normal build | Passed | 16.1804034s |

```text
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> host::tests::schema_is_generated_from_rust -- --test-threads=1
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> host::narration_diagnostic_read_review_tests:: -- --test-threads=1 --nocapture
cargo test --manifest-path Cargo.toml -p locallore --features host --locked --offline --target-dir <owned-D-target> --test host_scene_recipe_v1 -- --test-threads=1
cargo test --manifest-path Cargo.toml -p locallore --lib --features host --locked --offline --target-dir <owned-D-target> turn_trace::narration_diagnostic_retention_review_tests:: -- --test-threads=1 --nocapture
cargo clippy --workspace --all-features --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo fmt --all --manifest-path Cargo.toml -- --check
cargo check --manifest-path Cargo.toml -p locallore --no-default-features --locked --offline --target-dir <owned-D-target>
cargo check -p locallore-android --locked --offline --target-dir <owned-D-target>
node apps/desktop/verify-frontend.mjs
```

The six functions use actual synthetic Host/Engine/Play/RingSink reads for both
recipes, finite reason order, early denial, admission/selector precedence,
owner/session/head/attempt isolation, lifecycle/lock behavior and unchanged
provider/receipt/replay/knowledge/old-wire results. Separate trusted private
tuple and long-session-alias controls exercise projection and reply limits;
they are not actual Engine failures, public capability issuance or origin proof.
Expected caught synthetic poison panics remain visible in the passing log.
The future-version guard remains source-reviewed: the current getter is
constant 1. No hypothetical runtime version or negative-Serde-trait proof is claimed.

Root's recorded environment is Windows, Rust/Cargo/rustfmt 1.93.1 and
Node 24.22.1, existing locked/offline dependencies, one heavy job, one Cargo build
job, incremental disabled and dev/test debug0. Process-local TEMP/TMP are
`D:/Dev/_Temp`; source, cache, targets and local outputs reside on D:.
The documentation author read source/bounded records and checked Git scope/
whitespace only; no compiler, formatter, Cargo, Node, browser, app, model/assets,
device or desktop execution was performed by this author.

## Pending gates and limitations

The portable-workspace/development-native serialized sequence is running at this
freeze, without completed process records. Both broad results stay pending;
no previous slice's counts are copied. Normal native build/lint and any justified
retained no-inference compatibility read remain Root-owned and unmeasured here.
Independent final evidence review and the focused PR gate remain pending.

Rust synthetic Host/native-component tests and frontend mock/controller/headless
checks/build do not establish native IPC/WebView rendering, new real-model
execution, Android ABI/device behavior or human quality. Earlier Phase1 Eval,
native-render and Native4 report evidence keeps its original source attribution.
Host/schema changes affect Eval fingerprints: preserve historical source-mismatch
refusals and unavailable causes; do not rewrite captures or backfill decisions.
No Eval companion, UI display, Report4 extension or new model cohort is added.
Both original and newer human assessments remain **needs improvement**.

Bounded local `d07-narration-host-read-*` process/log/equality/correction records
retain evidence; private paths/raw material stay outside this public document.
Next: Root records completed broad and appropriate compatibility checks, obtains
independent evidence review and prepares the focused stack above
[PR #253](https://github.com/OptimumAF/LocalLore/pull/253). Full M05.03/M05.04,
D07.04 and dependency acceptance remain unchecked; no merge/release is authorized.
