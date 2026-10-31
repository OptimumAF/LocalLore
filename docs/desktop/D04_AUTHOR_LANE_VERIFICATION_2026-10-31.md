# Author packet A: bounded runtime verification

Refs #25 D04.02, supporting D04.04, #9 and PR301. **The bounded synthetic Author
lane passes the frozen16-case GREEN and full runtime checks; accepted-main
readback remains pending.** Production Author access stays disabled. This is a
bounded synthetic runtime check, not desktop IPC, rendered UI, packaged-worker,
real-model, Android/device, story-quality or release evidence.

## Authority and distinct attempts

The owner approved the [R3 compatibility amendment](D04_AUTHOR_CODE_R3_ADMISSION_2026-10-31.md)
in `call_bc8a3386f5f7418a98b83643ce35129c`, answering
`Approve amended code checks`. Only retained metadata increased1280 to1344KiB;
all other caps and the original target baseline remain unchanged. The actual
decision and immutable R3 Stage were created exclusively before admission.
Their combined4,769B cost brought metadata to1,249,779B. Full prospective
admission/START/child reserve was1,361,395B, below1,376,256B by14,861B.

The [original first baseline](D04_AUTHOR_CODE_CAPTURE_FAILURE_2026-10-31.md)
remains permanently invalid, with incomplete prefixes, unknown ownership history
and no accepted count. The [R2 pre-admission refusal](D04_AUTHOR_CODE_R2_PREFLIGHT_REFUSAL_2026-10-31.md)
launched no test child. Its decision, Stage, source and refusal remain immutable.
R3 reuses original successful format/preparation under their actual old source,
tool, command and raw-log identities. It did not run preparation again.

## Actual corrected baseline

Root ran the reviewed guard from the physical D: source checkout using the
pinned installed64-bit Windows PowerShell5.1.26100.9818. It freshly verified
process ownership/ambiguity, source, tools, retained products/fixtures and storage,
then launched the fixed Node24.22.1 coordinator. No app launched.

```powershell
& 'C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe' -NoProfile -NonInteractive -File '../author-integration-artifacts/d08-fork-native-20261030-v1/author-r3-admit.ps1' -Phase baseline
```

Its exact Cargo child command was:

```powershell
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --lib --features engine-adapter,development-worker --locked --offline author_ -- --test-threads=1 --format terse
```

Source revision `69761326276fad8824a0c0fa7230d8c963c97748`, tree
`fd4ed72b594b348a2845dd09abc028f2ae67231c`, contains the old runtime behavior
and frozen FIRST. The six runtime source hashes match the original prepared
baseline; later documentation did not change that behavior.

Actual result: **16 executed,4 passed,12 failed,0 ignored,48 filtered, exit101**.
The failures directly demonstrate missing Author request admission and the
legacy reply cap. Several lifecycle, singleton and metrics groups stop at that
earlier admission refusal; their later assertions were not fully reached.
No setup failure or compilation error appears. The unused metrics helper emits
a dead-code warning at this old-behavior stage; no strict-Clippy pass is claimed.

The child closed normally with `unknown:false`, no overflow, timeout or kill.
`processTreeContained:false` remains explicit: this is cooperative child/pipe
closure, not OS-enforced descendant containment. Complete stdout6,945B and
stderr708B are retained losslessly. Root read both entire decoded logs and wrote
the actual16-case behavioral-RED review gate.

Cargo reported0.80s test-profile preparation/completion and0.22s test execution;
there is no separate measured compilation time. The child wrapper
recorded1.652s. These are synthetic code-check costs, not inference latency.
The standalone toolchain remains Cargo/rustc1.93.1 with pinned locked offline
dependencies, one job, incremental0/debug0 and TEMP/TMP on D:.

## Local evidence and remaining checks

The ignored retained group contains:

- `author-r3-baseline-1-process.json`, SHA256
  `42c4b299db144e2b846f04e80efc71e203a6e628bb93e36e7abb200aaf883e22`.
- `author-r3-phase-baseline.json`, SHA256
  `2a16bebcb65e3a511f6ef880d611c074486e2b1dfbb511a96e64c9a17848ce4c`.
- Complete raw stdout SHA256
  `915a04e3c3336ce4cda3a31b78e7f281c04f1d8222a26c264972d2cc54556da2`
  and stderr SHA256
  `48e3ae9a5ab2b9b1d8ee1055e1dbdfd893ef29d48cf7b8f916aacb47cfe22e41`.
- The actual Root baseline review, actual owner decision, immutable Stage,
  admission/START and all historical failure/source/product/fixture proofs.

Baseline inventory before its phase receipt: metadata1,264,328B,
target12,287,065,614B unchanged,47 retained empty runtime fixture roots,
old records549,989B physical/570,664B charged logical bytes, fork fixtures671,744B.
No forecast miss occurred. The existing normal desktop binary SHA256
`0482d821a12a92333a9974a43f301d5fe36d5ca08e7c75843c3d04f19b0e6f1f`
was unlaunched and its original retained copy remains unchanged. The later
normal build below replaces the live build artifact without launching it.

## Implementation and independent review

Different-author production commits `fa8cfa64` and `44e54e13` implement the
separate singleton Author lane through existing RuntimeProvider/LocalRuntime,
exact shared schema/identity/budgets, operation-bound replies and unavailable
version2 role metrics. Identity/cache/cross-lane checks precede availability.
Every production constructor remains Disabled; only the test-only helper's two
fixed cases can mint Fixture access. Play retains350/16384 reply ceilings and
the existing60s effective deadline, cancellation/drain and cleanup owner.

Independent review caught the public generation wrapper passing Play bounds to
Author; the separate correction selects request tokens/8192 before the same
native gate. A different author added `0a50b18f`, one actual public-API fixture
regression outside the original Author filter. It checks four valid calls on
one owner, invalid/mismatched budgets send no frames, and positive cleanup.
Its empty fixture proves routing/admission; exact8192/16384 reply payload edges
remain the frozen parser tests' evidence. No additional RED claim is made for
this later review regression.

Both frozen FIRST files and all existing predicates remain unchanged. Production
and regression source received separate independent reviews; these are source
reviews, not human approvals or execution evidence. Root integrated the three
commits, reviewed the actual production-only formatting diff and recorded its
gate. Tested revision is `c35304dcf9a74db82484c929c7bcccfd85fd6f8b`, tree
`3b7d394f70cbf5f285df653a662e2c722ade07e9`.

## Actual GREEN and finish checks

All children below closed code0 with complete logs and no timeout, overflow,
kill, unknown closure or post-child identity error. All used locked offline
packages, the existing target and the same process-local build settings.

| Check | Actual result | Child wrapper time |
| --- | --- | --- |
| Unchanged Author filter |16 passed,0 failed,0 ignored,49 filtered |10.332s |
| Full library, all features |65 listed:64 passed,0 failed,1 ignored |35.692s |
| Explicit five-file formatting check | Exit0, no output |0.408s |
| All-target/all-feature strict Clippy | Exit0, no warnings |2.370s |
| Normal desktop binary build | Exit0; unlaunched |25.215s |

GREEN test execution was7.02s and Cargo test-profile completion2.76s. Full-suite
test execution was29.94s and Cargo test-profile completion5.18s. These are code
test/build costs, not model latency. The sole ignored test is existing
`model_and_worker_reparse_paths_reject`, explicitly requiring Windows symlink
privilege; it was not run, and no privilege/settings change is authorized.

The exact additional commands were:

```powershell
cargo test --manifest-path crates/locallore-local-runtime/Cargo.toml --lib --all-features --locked --offline -- --test-threads=1 --format terse
rustfmt --check --edition 2021 --config skip_children=true crates/locallore-local-runtime/src/lib.rs crates/locallore-local-runtime/src/adapter.rs crates/locallore-local-runtime/src/role_metrics.rs crates/locallore-local-runtime/src/adapter_author_review.rs crates/locallore-local-runtime/src/author_reply_review.rs
cargo clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets --all-features --locked --offline -- -D warnings
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --bin locallore-desktop-spike --locked --offline
```

The local phase records bind the exact argv/source/tools/complete raw logs:
format SHA256 `2948ece87a37bc11c2c8b4c52c92237b59b4495f4810553603e039ff13fd2030`,
GREEN `d4491acdb60481c8fd4b26f3ae5784806fc1dc1a8206bae92800ed249f90651e`,
finish `a8eccf08616d0b7c6c6da09f1efc1b15c344eb3b3d5510bc5f2b4a1222bc67a2`.
The new normal binary is42,246,144B, SHA256
`7a68992bc35d2e778d71e8db80ef4050a281d65d785a054e77abb569aadaf192`.

Finish inventory before its PASS receipt was metadata1,293,710B,
target12,303,887,992B,71 retained runtime fixture roots/210B, no forecast miss.
The later449-byte Root premerge snapshot measures metadata1,298,016B including
itself. Root's exact-main source review/admission/START/full native child reserve
forecasts1,328,224B, below the unchanged1,376,256B cap. Preserving the actual
42,246,144B finish binary would make target12,346,134,136B before the main build,
below both original ceiling and unchanged target-growth forecast. These are
premerge snapshots/forecasts, not future admission or main-build results.

Accepted-main readback is still required. No new frontend, Android/device,
native IPC/render or real-worker/model run was performed. Guarded frontend
source/bundle identities remain unchanged; the library/build checks do not
replace those separate qualification gates. B's worker/profile/pin adoption and
original-story UI remain pending, D04/epic remain open, and no release is claimed.
