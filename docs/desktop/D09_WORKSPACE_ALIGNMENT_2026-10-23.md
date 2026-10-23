# D09 Cargo workspace alignment, 2026-10-23

Refs #31 D09.03/.05/.07 (partial prerequisite), #7 M03.01/.05.
Implementation is **in review**, not acceptance of D09 or application byte
reproducibility. Source frozen at `d76e215f4429811fb87ddd094a9a307dc6874558`;
`5bf654616ea9aaeeb526d57298ba6f403ef10b47` retires the old desktop lock and is
required together with that follow-up. The source parent `d555fd9` combines the
immutable checker handoff `39bd802` with accepted main
`59fa8e898a85bbdae7bbbd3ad34d576bbd8ef4d8`. This separate
`impl/d09-workspace-alignment` checkout preserves both failed historical cohorts.
Claims: [6370272692](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6370272692),
[#7 companion](https://github.com/OptimumAF/LocalLore/issues/7#issuecomment-6370273093),
[harness addendum](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6370357575),
[docs/metadata-test addendum](https://github.com/OptimumAF/LocalLore/issues/31#issuecomment-6370394919).

## Change and authority

The desktop package joins the repository root Cargo workspace. The four existing
portable packages remain `default-members`: `locallore`, `locallore-android`,
`locallore-storage`, `locallore-workspace`. Root `Cargo.lock` now supplies desktop
resolution; the unused desktop lock and desktop's empty `[workspace]` are removed.
`locallore-local-runtime` and `locallore-eval` are explicit exclusions and retain
unchanged standalone manifests/locks.

An explicit Cargo `--workspace` ignores `default-members`. The portable check
runner therefore excludes **only** `locallore-desktop-spike` from test/Clippy;
formatting still checks all workspace members. Direct desktop manifest-path
commands select the desktop package. No compiler metadata override, launcher,
source alias, build-script/product change, dependency update or extra compiler
flag is introduced. The existing approved source remap in the packager remains
unchanged. This is the ordinary Cargo layout suggested by the isolated fixtures
in [the preceding failed-cohort report](D09_APP_REPRODUCIBILITY_2026-10-23.md).
Those fixtures establish a reason to try this layout, not proof that the complete
application will now reproduce.

Nine native harness source inventories replace only their retired lock literal
with `../../Cargo.lock`. All nine already pass their own `--target-dir`; Cargo's
changed default target directory therefore does not redirect their executable
lookup. The actual metadata regression verifies both explicit desktop package
selection and the default/overridden target directory. Harnesses were not run.
No IPC, UI/controller, worker, model, engine, storage/schema, Android or workflow
behavior is edited. The coordinator's independent archive fixture change remains
outside this branch.

## Offline lock provenance

The starting lock contents are tracked Git blob bytes at `d555fd9`, not regenerated
historical reports. Their package sets are:

| Reviewed lock | Packages | SHA-256 |
|---|---:|---|
| Root | 67 | `87d6484fa0d30bf7113c0d17b4a3782b52a91ed8b555c909acdbe20084cb68d8` |
| Prior desktop | 413 | `874d1844ec0508d2c2c6d82bdd40668c74b29e7a8726621bfd1ee9c298237563` |
| Standalone runtime | 41 | `0f0e5aaef2ce12fabdc41c16c2e99ac2984aacf00902802b832b6ce3409a5699` |
| Standalone evaluation | 43 | `f99aca7c5232d3ae430fff37a49055d500a40c678620445ad31f922ca5847753` |

The existing package blocks were unioned by `(name, version, source)`, refusing
checksum disagreement, then ordinary `cargo +1.93.1 metadata --offline
--format-version 1 --filter-platform x86_64-pc-windows-msvc` reconciled resolution.
No package source or version was selected from outside that reviewed union.
Subsequent metadata/build/test commands all used `--locked --offline`.

The result is **414 identities, including 407 registry packages**: exactly the
existing union, zero added/removed identities and zero changed checksums. Relative
to the old root lock, 347 identities move in from the other existing locks.
New root lock SHA-256:
`d6a0fb958805ae4e4271f456ff3bbcbd683e993d25ac9ef35a1122229bcd8950`.
The [sanitized evidence](D09_WORKSPACE_ALIGNMENT_EVIDENCE_2026-10-23.json)
records every identity/checksum, input hashes, union diff, exact Rust argv and log
hashes. Runtime/eval manifests and locks and regenerated Host TypeScript are
byte-unchanged relative to the source parent.

## Actual checks

Windows 11 10.0.26300 x64; Rust 1.93.1 `01f6ddf75`, Cargo 1.93.1 `083ac5135`,
MSVC 19.34.31937 / toolset 14.34.31933, Windows SDK 10.0.19041.0,
Node 24.22.1 / npm 11.19.1, Python 3.14.9. Existing installed tools, registry
sources and locked npm files were reused; no provisioning/download occurred.
All targets, temp and artifacts are task-owned D: directories. Rust used
`CARGO_PROFILE_DEV_DEBUG=0`, `CARGO_PROFILE_TEST_DEBUG=0`, `CARGO_INCREMENTAL=0`.
No existing compiled target was copied. The new target was reused sequentially
for these compatibility checks; these are not independent clean build cohorts.

| Command / selection | Actual result |
|---|---|
| `cargo +1.93.1 fmt --all -- --check` | PASS |
| `cargo +1.93.1 test --workspace --exclude locallore-desktop-spike --locked --offline` | **407 PASS, 0 fail, 4 existing ignored** |
| Same workspace selection, `clippy --all-targets --locked --offline -- -D warnings` | PASS |
| `cargo +1.93.1 run -p locallore --example android_fixtures --locked --offline -- --check` | PASS, 4 contract-v1 fixtures |
| Desktop manifest, `test --locked --offline` | **45 PASS, 0 fail, 1 existing ignored** |
| Desktop manifest, `test --features dev-harness --locked --offline` | **47 native + 2 contract PASS, 0 fail, 1 existing ignored** |
| Desktop manifest, `clippy --all-targets --locked --offline -- -D warnings`, default and dev-harness | Both PASS |
| Runtime manifest, build `protocol-fixture`, then `test --all-targets --features development-worker,engine-adapter --locked --offline` | **40 PASS, 0 fail, 1 existing ignored**; actual synthetic child processes |
| Runtime same features strict all-target Clippy and standalone fmt | PASS |
| Eval manifest `test --all-targets --locked --offline`, default / `--features local-model` | **23 / 24 PASS**, 0 fail/ignored; no actual model |
| Eval strict all-target Clippy, default and local-model; standalone fmt | PASS |
| `python -m unittest discover -s scripts/tests -p 'test_*.py'` | **157 PASS**, 0 fail/skip; includes actual offline metadata regression |
| `python scripts/desktop-reproducible-tests.py` | **20 PASS**, 0 fail/skip |
| `python scripts/desktop-package-tests.py` | **12 PASS**, 0 fail/skip; synthetic package policy |
| `npm --prefix apps/desktop run check` | PASS: normal frontend, schema/types and actual controller/native-double checks |
| `npm --prefix apps/desktop run format:check` | PASS |
| `git diff --check`; unchanged standalone manifests/locks/generated TS | PASS |

Actual Cargo metadata proves five root members, four portable defaults, direct
desktop manifest selecting desktop in the same root, no desktop-local lock, and
two distinct standalone roots. `cargo tree --depth 0 --locked --offline` selects
exactly the four portable members; adding `--workspace --exclude
locallore-desktop-spike` gives the same selection. Direct desktop manifest depth-0
selects only desktop.

Actual graph-only commands:

```powershell
cargo +1.93.1 tree --workspace --exclude locallore-desktop-spike --locked --offline --target x86_64-unknown-linux-gnu -e normal,build --prefix none --format '{p}'
cargo +1.93.1 tree -p locallore-android --locked --offline --target aarch64-linux-android -e normal,build --prefix none --format '{p}'
```

The first has 41 distinct package/version entries, the second 58. Neither
contains desktop, Tauri, GTK, WebKit or GLib. This verifies dependency selection,
not a Linux native or Android cross-ABI build/execution. The unchanged Android
check-runner commands do not select a Cargo workspace. The whole `check.py host`
sequence was not rerun: its Rust, fixture and scripts-test portions above were
run directly; its other benchmark/native-linker portions are not new evidence.

Ignored checks remain explicit: special compiled SQLite page-limit qualifier,
archive IPC-worker entrypoint (not a standalone test), two Store reparse tests,
desktop import reparse test, and runtime model/worker reparse test. No privileges
or system settings were changed to run them.

## Evidence, limits and handoff

Local `workspace-alignment-artifacts/` retains exact stdout/stderr, full Cargo
metadata/trees, pre-merge lock inventory and command/result JSON; sibling
`workspace-alignment-target/` is task-owned. Only sanitized metadata, hashes and
counts are committed. Native results are Rust unit/contract execution, not
WebView rendering. Frontend checks use native doubles; no window, app capture,
desktop input/control, real worker, model, emulator or device was launched.
No new two-path package build occurred, and no prior artifact was rewritten.

The lock audit found no other active reader of the retired desktop lock after
the nine inventory corrections. Historical dated reports retain their original
lock hashes. ADR-0006 keeps the original rationale and adds the superseding
workspace choice; current build instructions name all three consumed locks.
No `.github` edits are needed: its standalone comments describe runtime/eval.

The GLib advisory remains open; graph exclusion is applicability evidence, not
remediation. License/notice gaps, full Unicode clean build, offline traffic and
installation, WebView2 prerequisites, native UI journeys, model quality,
update/uninstall and release gates remain separate. There is no new quality or
release signoff.

Next: coordinator independently reviews the workspace/lock changes and exact
checks, reconciles accepted concurrent changes, and freezes the combined source.
Only then run the existing unchanged two-clean-ASCII-space-path normal packager
checker and compare raw PE/ZIP bytes with no normalization or exclusions.
Successful unit/native compilation cannot replace that gate. Claims transfer
back to the coordinator for review; no task checkbox, PR merge or release action
is performed here.
