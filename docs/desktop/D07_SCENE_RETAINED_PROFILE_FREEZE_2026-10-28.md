# Retained-review native profile gates: independent first freeze

Refs #29 D07.06, supporting D07.03/.05 and #23. Frozen from exact
`11d82d61226b52c8873ddcd1e902aebdf6466dcb`. **SOURCE ONLY, UNREGISTERED,
UNCOMPILED, UNFORMATTED AND UNRUN.** Missing proposed helper APIs would be a
setup/compilation failure, not behavioral RED. No baseline or pass is claimed.
Root owns helper implementation, Main's early refusal, registration and actual
serialized execution. This author owns only the new test file and this freeze.

The separate retained-review launcher contract at `aa054056` was read through
Git without changing its owner's checkout. The Node/TS author owns that
contract and launcher/journey work. This file does not alter their allocation.

## Proposed exact native seam

In existing `comparison_run_native_harness.rs`, Root implements:

```rust
pub fn review_active() -> bool;
pub fn review_webview_profile(workspace: &Path) -> Result<PathBuf, String>;
```

`review_active()` is exactly existing `scene_active()` plus the closed
`LOCALLORE_TEST_RESTART=review` value. Missing D02/full/native/scene/memory flags
or D04 harness 1 cannot enable review. Old absent/0/1 restart stages retain
their existing meaning and do not activate the new helper. Native/Main must
reject inconsistent requested review before workspace/model setup; testing Main
startup itself belongs to Root's later integration gate.

`review_webview_profile` is read-only path validation. The source argument must
be the existing checked `LOCALLORE_TEST_WORKSPACE`, with absolute ordinary D:
ancestors, lowercase `full-comparison-native-<UUID>` parent and exact absent
`stories-v1.sqlite` leaf under TEST_MEMORY1. No database is created. Retained
comparison Store files remain separate actual sources; synthetic fixture files
are not a completed report, an Engine or a model.

`LOCALLORE_D02_ARTIFACT_DIR` names the absent `review` leaf under an existing
ordinary fresh `full-comparison-native-<different lowercase UUID>` output root.
The return is that output root's **`webview-profile` sibling**, not a profile
under the retained source or under the `review` artifact leaf. The returned
profile must not already exist as either directory or file. Old and new roots
cannot be equal or nested in either direction, including ordinary Windows case
aliases. The helper performs no creation, writes, canonical-state operation,
model action, profile reuse or general path execution. Error spelling is not
frozen; refusal is `Err` rather than a guessed new public error namespace.

## Fixed 24-case oracle

The new module is
`apps/desktop/src-tauri/src/comparison_run_native_harness/review_profile_tests.rs`.
It has one Windows parent matrix and one ignored fixed-child entry. Each case
uses a separate fresh D: synthetic fixture and a fresh copy of the existing
libtest executable, with fixed exact test name and no app arguments. The parent
removes inherited `LOCALLORE_*` keys in the child command only, supplies the
closed flags, and does not mutate its own environment.

| Cases | Required result |
| --- | --- |
| Legacy stage absent, 0, 1; malformed `Review` | `review_active=false`, profile refused |
| Each missing D02/full/native/scene/memory flag; D04 harness 1 | `review_active=false`, profile refused |
| Missing output; relative output; C: output string; wrong artifact leaf | Review flag true, profile refused |
| Same root; output nested in source; source nested in output; actual case-alias same root | Review flag true, profile refused |
| Existing profile directory; existing profile file | Review flag true, profile refused without changing original bytes |
| Existing source database; workspace argument/env mismatch; wrong source leaf | Review flag true, profile refused |
| Safe ordinary fresh D: source/output | Return exact new output-root `webview-profile`; source database, artifact leaf and profile remain absent |

There are 4 legacy-stage cases, 6 flag cases, 4 output-shape cases, 4 overlap
cases, 2 existing-profile cases, 3 source-anchor cases and 1 positive case.
The C: case passes only a newly generated string: fixture setup never creates
or opens a C: directory. The case-alias fixture preserves the valid lowercase
UUID basename and changes only an ancestor's case; it first verifies the alias
resolves to the actual same ordinary D: directory. Refusal cannot pass merely
because a fabricated alias is missing. No 8.3/reparse-race refusal is claimed by
this finite ordinary-fixture set.

Every completed child compares the entire quiescent fixture inventory before
and after two helper invocations; the parent also compares before/after child
execution, including failures. Inventories retain directories and actual file
bytes, including all nested synthetic files, not only sizes/mtime or selected
sentinels. Bounds are depth 8, 128 entries, 4096 bytes per file and 65536 total
file bytes. Existing output/source/profile bytes must not change on refusal.
All fixtures are preserved; no Drop cleanup, deletion, reset or old-packet access
is introduced.

Child pipes are capped at 64 KiB each. A child has 30 seconds, then one kill
attempt and at most five seconds of wait; reader completion has a separate
five-second bound. Timeout or uncertain reader drain fails immediately and
admits no later case. Successful direct-child close is not Windows descendant/
Job containment, native runtime drain or an executed timeout qualification.
No byte-invariance success is invented for an interrupted child.

## Root registration and actual execution remain separate

Root adds only the appropriate test/Windows registration after implementing the
helpers; this author does not edit the parent module. Root should first compile
and distinguish API/setup errors from executed assertions, then run:

```text
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --bin locallore-desktop-spike --jobs 1 --target-dir <owned D: target> comparison_run_native_harness::review_profile_tests::retained_review_profile_matrix_is_pure_and_child_environment_is_isolated -- --nocapture --test-threads=1
```

Run from the physical D: checkout with process-local `TEMP`/`TMP=D:/Dev/_Temp`
and existing owned D: Cargo cache/target. This is an **UNRUN** reproducible
command, not a baseline. The test author ran no Cargo, Node, formatter, build,
app, SDK/model/worker/asset, phone, desktop capture/control or native render.
Source and Git/whitespace inspection are the author's only validation.

These helpers do not establish the later app-owned review journey, exact
bootstrap stage, unchanged actual retained run inventory, read-only source-
mismatch resume behavior, observer isolation, corrected native pixels or zero
model execution. Those remain Root's separately reviewed integration/execution
gates. Both actual human assessments remain needs improvement, and frozen Core
human fields remain unchanged. No task, epic, PR merge or quality gate is
accepted by this source freeze.

## Additive conflict/absence freeze before the production correction

Frozen from exact `db815486f38eb2407a6696be5c2f0ce721ae1c2e`, after source
review identified three gaps outside the original ordinary-fixture set:
conflicting seed harnesses could run during review setup; a present non-Unicode
restart value bypassed Main's string-only early guard; following a dangling leaf
could confuse an existing entry with absence. **This additive source is UNRUN,
UNFORMATTED and UNCOMPILED.** It does not label missing new APIs as behavioral
RED and does not import any later Root execution result.

The original 24 case strings, assertions, inventory mechanism and process
bounds remain intact. A separate 14-case roster extends the same fixed-child
matrix to 38 cases:

- Nonzero M07 memory, D08 timeline/fork, M08 author, D04 scene, M07 legacy and
  D07 reader harnesses each conflict with otherwise valid review flags.
- Unknown nonzero and malformed unrelated harness values also conflict;
  unrelated harness value `0` is a positive disabled control.
- Nonzero storage-failure and unknown `LOCALLORE_TEST_*` flags conflict.
  The intended review whitelist permits only MEMORY, RESTART and WORKSPACE
  test inputs, plus the exact required native/full/scene/D02 flags. Root owns
  the full production configuration predicate and its source review.
- A present Windows restart value made with `OsString::from_wide(&[0xd800])`
  is verified to reach the child as `VarError::NotUnicode`; another case uses
  an ordinary unknown stage. Neither may activate review or yield a profile.

Each added invalid case requires `review_requested() == true`,
`review_active() == false` and refusal by both profile-helper calls. The disabled
unrelated-harness control requires active review and the same absent fresh
profile path as the existing positive case. Whole ordinary fixture directories
and file bytes remain unchanged in child and parent. No parent environment is
mutated; no new C: fixture path is introduced.

Root implements the proposed native-only helper:

```rust
pub fn review_requested() -> bool;
```

Main must use a present OS-string-aware request check before Builder/workspace/
model setup, so invalid Unicode cannot silently choose the initial model
journey. Valid `review` plus conflicting seed/test families must fail before
their seeding paths. Legacy default/0/1 behavior and the old 24 oracles are
preserved. These unit cases test the proposed predicates; actual Main refusal
ordering still requires independent source review and later native integration.

Two additional pure unit tests freeze a private classification seam:

```rust
fn review_absence_from_metadata(result: std::io::Result<()>) -> Result<(), String>;
```

Only `Err(NotFound)` is accepted as absence. `Ok(())` means an entry exists and
must refuse; PermissionDenied, AlreadyExists, NotADirectory, Interrupted,
InvalidInput, InvalidData, TimedOut and Other errors must also refuse. These are
10 finite simulated result classifications across two test functions, with
**no filesystem-link probe**. The actual caller must pass
`std::fs::symlink_metadata(path).map(|_| ())`, not following `metadata` or
`try_exists`; the tests alone cannot prove that wiring. Root owns implementation
and independent source review of those caller sites.

No symlink, junction, reparse canary, dangling-profile object, SDK/profile probe
or real app is created or launched. No executed dangling-link refusal, Windows
link privilege, link race or universal reparse qualification is claimed. The
original ordinary existing-profile file/directory cases remain actual future
filesystem cases; simulated metadata classification does not replace them.

After Root supplies the new helpers and compiles, the documented parent-matrix
command above exercises all 38 fixed cases. A separate exact filter
`comparison_run_native_harness::review_profile_tests::retained_review_absence_`
exercises the two pure tests. These commands remain UNRUN by this author.
No Node/Cargo/formatter, build/app, model/assets, phone or desktop action was
performed. Root must retain setup failures, actual before/after measurements
and all D09 probe restrictions while advancing the narrow production fix.
