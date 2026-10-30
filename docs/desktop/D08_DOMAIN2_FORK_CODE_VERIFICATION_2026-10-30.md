# Domain2 fork code verification

Refs #30 D08.04/.07, #12 M08.04/.06 consumer and PR290. Code checks pass;
native UI/IPC/rendering remains unrun for this fork integration. No application
was launched. The earlier browser run in PR286 is separate evidence.

## Authority and source

The owner answers **Approve bounded code checks** to
`call_0670958c882c495eb37fee072dd43a17`: code checks and normal restoration only,
original target baseline8,259,980,576B with prospective4GiB growth, at most8MiB
new synthetic fixtures and512KiB combined check output, within660MiB joint.
Preserve every earlier output/failure; no app/model/device/SDK/OS/desktop action.
Fresh source/product/process/storage admission precedes execution. The prior
normal binary is preserved as an ordinary42,087,424B copy, SHA`dc2490ab...`.
Pinned environment remains Node24.22.1, Rust/Cargo1.93.1, rustfmt1.8.0,
PowerShell7.6.5, Windows10.0.26300 x64, TS7.0.2, React19.3.1, Prettier3.9.10,
esbuild0.28.2 and Tauri2.12.5. Tools run from physical D; TEMP/TMP=D:/Dev/_Temp.
Cargo uses the existing D cache/target, locked/offline, one job, no incremental
or dev/test debug data. No download or cache reset occurs.

Accepted main is merged into the existing fork branch at3ebcdc7e. Original
FIRST c54e966b runs20 authored groups:9 execute,3PASS/6FAIL,11 UNRUN_SETUP,
exit2,0.1509949s. Missing codec/strict APIs are not behavioral RED. Failures cover
five stale retained-action paths and absent Domain2 fork entry. Current raw21
executes21:20PASS/1FAIL,0.1568571s. A diagnostic-only checker change preserves
every predicate and captures actual established `inspection_query` calls omitted
by the fixture. The diagnostic run remains20/1,0.1629708s.

Independent correction49171e44 validates only that exact session/scope/head/lens
history query and returns a closed typed empty page. All21 groups and the unknown/
mutating-operation refusal remain. This fixes test setup, not product behavior;
neither earlier failure is reclassified. Corrected raw21/21 pass0.157219s;
TypeScript0.4003553s. Inverse source hashes retain the original20, later21,
diagnostic and corrected fixtures in the linked source review.

Rust formatting changes only the adapter and its eight-case file; actual tests
run at ee05b2d0. Build-generated `fork_boundaries.toml` is read back and committed
at8c92ae37: exactly the generated allow/deny entries for `fork_boundaries`.
No fabricated generated output or expanded window/origin/grant is used.
Six frontend files have identical actual esbuild CLI transform hashes before/
after formatting; configuration JSON also compares equal. Successful transform
stdout is retained as hashes/byte counts, not full copies. Actual failures/logs
stay retained. Final frontend/compatibility/restoration source is clean07ad83b0;
its Rust product inputs equal the tested formatted adapter.

## Actual checks

Commands below run from `apps/desktop`; build/test/check/Clippy use
`--locked --offline` and the pinned environment above. Durations include the child.

| Command/scope | Result |
| --- | --- |
| `node check-domain2-fork-review.mjs` after formatting |21/21,0.1839101s|
| `node node_modules/typescript/bin/tsc --noEmit` |Pass,0.2664188s|
| `node check-fork-controller.mjs` |63 assertions,0.1677159s|
| `node check-fork-callback-review.mjs` |6/6,0.1054533s|
| `node check-fork-independent-review.mjs` |9/9,0.1046454s|
| `node check-broker-fork-error-review.mjs` |2/2,0.1066047s|
| Full frontend/config Prettier check |Pass,2.8495928s|
| `cargo fmt --all -- --check` |Pass,2.0009028s|
| `cargo test --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike fork_commands::boundary_catalog_review_tests -- --nocapture --test-threads=1` |8/8,21.8001912s; test body0.13s|
| Same command with `fork_commands::fork_adapter_tests` |6/6,12.320358s; test body0.17s|
| `cargo check --manifest-path ../../Cargo.toml -p locallore-android` |Pass,1.9754651s; Windows host only|
| `cargo clippy --manifest-path src-tauri/Cargo.toml --all-targets -- -D warnings` |Pass,12.2984673s|
| Same Clippy with `--features dev-harness` |Pass,10.1354713s|
| `node build.mjs` |Pass,0.2572663s|
| Existing verifier's actual normal-bundle read/assert block only |70/70 exclusions,0.0781693s; not full77-child suite|
| `cargo build --manifest-path src-tauri/Cargo.toml --bin locallore-desktop-spike` |Pass,9.296509s; unlaunched|

Frontend cases use actual controllers/JSX with disclosed inert effects and
synthetic IPC. They prove no DOM, pixels, mounted effects or native callback.
Rust tests use actual Core/Host/Store and existing broker/lease paths. The4097
entry case is synthetic DTO capacity, not4096 executed turns; pure lease tests
are not actual Tauri window destruction. Android host compilation is not a
device/JVM/SDK check. Neither Clippy nor compiling a qualifier executes it.

All35 recorded direct children close:32 exit0, original baseline exits2, and
two retained fixture failures exit1. No timeout, overflow, kill or new unknown.
Process-tree containment remains unproven. All old fixture paths remain present
with unchanged measured byte totals; that is not a new whole-file hash audit.
New five fixture roots total528,384B; all remain, with no cleanup. Fresh D07/D09/
D05 inventory plus exact eight D07/four D05 source hashes preserve prior costs.
The final restoration checkpoint measures346,653B check output before its last
phase record, joint681,974,588B and target11,741,589,214B, growth3,481,608,638B.
Later small records stay additionally charged under the same limits.

Normal restoration passes without launching. Frontend SHA256
`79e0acd91db0b87ec4486fe34fb00970e05d768c693ab67f4efd552952d0a56c`;
native SHA256`afbe74b0ff8116ced74a351e9cae6596039700f32e8cc661a3e078a4a942bc20`.
Old failed products and the preserved normal copy match throughout. Ignored
local evidence group:`d08-fork-checks-20261030-v1`, with immutable per-child
logs/terminal/source hashes, fixtures baseline, equivalence and restoration.

The independent [native proposal](D08_DOMAIN2_FORK_NATIVE_CONTRACT_2026-10-30.md)
is a separate16,318B source-only phase, not an app admission or actual rendering.
Its seven-success/one-failure ceiling and20MiB packet still need an executable
harness, frozen independent checks, source review and a separate owner resource
decision. All wider D08/desktop/device/model/quality/release gates remain open.
