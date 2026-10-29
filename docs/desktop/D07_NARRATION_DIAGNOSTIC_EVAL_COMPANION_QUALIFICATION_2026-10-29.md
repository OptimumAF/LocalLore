# Narration diagnostic Eval companion v1: scoped qualification

2026-10-29. Refs #29 **D07.04**, supporting #9 **M05.03/M05.04**.
**Implemented; focused, full Eval and desktop component checks measured;
independent evidence review pending.**
Current measured source: `272c8bb5d74209d44eb17fcb330e3c59ea9d4f5c`.
This is the bounded full-protocol4 opt-in metadata slice defined by the
[accepted contract](D07_NARRATION_DIAGNOSTIC_EVAL_COMPANION_CONTRACT_2026-10-29.md),
above the [Host-read gate](D07_NARRATION_DIAGNOSTIC_HOST_READ_QUALIFICATION_2026-10-29.md).
It adds no UI/IPC consumer, selected-run/catalog adoption or model-quality claim.

## Implemented interface and evidence boundary

`scene_v4::run_comparison_with_narration_diagnostics_v1` takes the existing
`dir, resume, kind, cancel, max_new_scenes, factory, reference` arguments and
returns `Result<ComparisonReportV4>`. The local-model-only public re-export
`scene_v4::run_native_comparison_with_narration_diagnostics_v1` substitutes the
existing reservation closure for factory, retaining
`NativeResult<ComparisonReportV4, R>` and owner-return semantics.
Old entry points remain opt-out. No new provider, cancel/deadline calls, engine
validator, persistence engine or dependency is introduced by the companion.

`scene_v4::desktop_api::narration_diagnostic_v1(run: &OpenedComparison,
expected_binding: &str, row: &RowId, observer: Observer,
native_inspection_granted: bool) -> Result<Value>` reuses Outputs authorization:
native inspection plus Omniscient access precedes binding, row and companion
probes. This guarantee starts at an already opened capability; existing
`open_read_only` itself is not a permission gate or zero-I/O operation.
Inspection never grants character knowledge or generation access.

The closed result binds version1/protocol4/kind/binding/turn/arm and literal
`generation_grant:false`. `no_declaration` and `no_observation` omit observation;
`recorded`, `host_unavailable` and `host_rejected` contain a validated closed
stored observation. Present malformed, partial, orphan, mismatched, unsupported
or over-budget evidence returns a bounded error, never an absence success.
Recorded describes the finite precommit validator decision: a rejected narrator
can still yield a mechanical fallback commit; an accepted decision can later
cancel. It proves neither final commit nor grounding, privacy or prose quality.

The first exact precommit snapshot latches the actual player attempt once;
one new Host read uses its before-head and immutable base. No after-head/latest
attempt reselection occurs. Publication requires the final checkpoint's exact
trace identity, source/run/arm/index/admission, checkpoint digest and query/reply
binding. Missing identity refuses rather than repairing trace. Digests establish
consistency, not authenticated origin or a restored session capability.

The fixed declaration is created only for a new opt-in run; historical runs are
not retrofitted. Ready-checkpoint recovery never harvests a cause. Actual
checkpoint bytes precede ledger settlement, companion creation and existing
capture revocation/Host close. Companion failures surface after teardown without
canonical rollback, receipt/Report4 rephase, refund, provider retry or deadline
reset. Earlier failure paths retain their existing Drop cleanup. Existing valid
files may be reused byte-for-byte; partial/conflicting files remain refused.
Storage uses existing `create_new`, `write_all`, `sync_all`, not atomic rename.

The declaration cap is 4,096 bytes; each fixed admission record is 7,168 bytes;
32 observations per arm, 64 total, 65 namespace files and 512KiB aggregate include
partial files. Opt-in writes additionally enforce the existing 32MiB/run,
8,192-entry/depth6 boundary. Cold loading enforces the companion namespace,
not the whole-run byte budget. The 256MiB library ceiling remains native-manager
owned; this API does not independently enforce that caller-owned limit.
The extracted existing single-link guard returns a held File through bounded
read/hash/revalidation alongside directory pins/run lock; the old wrapper and
selected roster are unchanged. No new OS race/isolation proof is claimed.

## FIRST provenance, original failures and distinct fixes

Proposal `cecbe972` and precision `2dc511b6` integrate as `8bb9f833` and
`e42cdda9`; formal acceptance is `d6aceb58`. Independent original freeze
`29fe6cbb` integrates as `4f625c89`: 832 lines, 10 groups, SHA256
`7b43bdb623248888fe60c6d800f3fd75606c43ed1d0847aba9cd16359712d03e`.
Root registration/rustfmt `833bbe29` has exact formatted-original equality,
SHA256 `8c1b304611ac72cbf40825a6be2faf24bd29009b88b0e18eb02270962666e249`.
Missing APIs/registration were setup prerequisites, not behavioral RED.
Production `d60e7a1f` integrates as `157ba05a`; rustfmt is `73537f7e`.

The original complete focused run at clean `73537f7e` exited101:
**8 passed, 2 failed, 0 ignored, 139 filtered; 1145.87s test,
1187.4146016s command** (13:55:33.4242589Z–14:15:20.8388605Z).
Its original log remains unchanged, SHA256
`53cdc1040c4cbb12f1849817393b9e8228b09869efe72f856e69fd1f05589fbf`.
Source review established two fixture defects:

- Lifecycle hashed a `json!` Value after map ordering changed, instead of the
  actual typed Receipt serialization used by the stored checkpoint. The corrected
  fixture hashes typed Receipt bytes before converting its summary to Value.
- Authorization inventory tried reading `run.lock` while the opened capability
  held it, producing Windows error33 before permission assertions. The corrected
  inventory is taken before opening, then accounts for the two intentional file
  corruptions. It does not remove the lock or weaken byte/permission assertions.

Independent correction `e98d22e1` integrates as `151de961`. Separate additive
FIRST regression `282b8a22` integrates as `9363c3f4`; rustfmt `ce9bbcae` yields
current 11-group test SHA256
`eaa714033d023d0892602abd668bf08687b97db843ed6410b9b85550cac8788b`.
Original failures remain failures; the corrections have separate measured runs.

The additive byte-reuse test at clean `ce9bbcae` genuinely failed:
**0 passed, 1 failed, 149 filtered; 14.41s test, 62.7678795s command**
(14:15:48.9076045Z–14:16:51.6754840Z). A typed-equivalent but different existing
file was accepted. Production `272c8bb5` changes one condition to require
`existing == encoded` as well as typed equality. It refuses without rewriting
existing bytes. The cold reader still permits valid JSON whitespace within caps;
reader conformance and exact producer file reuse are distinct policies.
Independent source review of exact `272c8bb5` reported no further blocker;
source review is separate from execution and acceptance.

## Completed checks at current source

All following process records report clean, unchanged `272c8bb5`, exit0 and empty
dirty lists. Times are exact differences of original UTC process timestamps;
original local JSON/log records retain command paths and timestamps. Only positive
matched unit results are counted; filtered integration binaries reporting zero
tests are not additional passes.

| Check | Actual result | Command duration |
| --- | --- | --- |
| Strict Eval local-model/all-target Clippy | Passed | 24.0542917s |
| Additive byte-reuse regression | 1 passed, 0 failed; 149 filtered; 17.09s test | 78.8197173s |
| Corrected lifecycle fixture group | 1 passed, 0 failed; 149 filtered; 2.13s test | 3.2114160s |
| Corrected authorization fixture group | 1 passed, 0 failed; 149 filtered; 11.78s test | 12.8672471s |
| Eval without default features | Passed | 4.7399476s |
| Eval formatting | Passed | 0.9800401s |
| Root workspace formatting | Passed | 5.3577130s |
| Android Rust host compilation | Passed | 2.1971959s |
| Full frontend checks/normal build | Passed | 23.8950981s |
| Normal Windows native build | Passed; product unlaunched | 41.6171275s |
| Normal native all-target strict Clippy | Passed | 17.1064233s |

For reproducibility, only private absolute target arguments are normalized to
`<owned-D-target>` and the private Node executable to `node` below. Commands use
existing locked/offline caches, with process-local TEMP/TMP `D:/Dev/_Temp` and
all project sources, targets, caches and outputs on D:.

```text
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <owned-D-target> local_lane::comparison::scene_v4::narration_diagnostic_companion_review_tests:: -- --test-threads=1 --nocapture
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <owned-D-target> local_lane::comparison::scene_v4::narration_diagnostic_companion_review_tests::additive_first_producer_reuse_requires_exact_bytes_while_cold_reader_allows_valid_whitespace -- --test-threads=1 --nocapture
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <owned-D-target> local_lane::comparison::scene_v4::narration_diagnostic_companion_review_tests::finite_failure_controls_preserve_order_exact_checkpoint_canonical_receipt_and_teardown_without_repair -- --test-threads=1 --nocapture
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <owned-D-target> local_lane::comparison::scene_v4::narration_diagnostic_companion_review_tests::outputs_authorization_precedes_binding_unknown_row_and_corrupt_source_probes -- --test-threads=1 --nocapture
cargo clippy --manifest-path crates/locallore-eval/Cargo.toml --features local-model --all-targets --locked --offline --target-dir <owned-D-target> -- -D warnings
cargo check --manifest-path crates/locallore-eval/Cargo.toml --no-default-features --locked --offline --target-dir <owned-D-target>
cargo fmt --manifest-path crates/locallore-eval/Cargo.toml -- --check
cargo fmt --all --manifest-path Cargo.toml -- --check
cargo check -p locallore-android --locked --offline --target-dir <owned-D-target>
node apps/desktop/verify-frontend.mjs
cargo build --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --target-dir <owned-D-target>
cargo clippy --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --all-targets --target-dir <owned-D-target> -- -D warnings
```

The first command is the original failing ten-group run; the second is both the
separate additive RED and GREEN invocation. The next two are corrected-group
runs. The narrow table is separate from the completed full suite below.
The fresh version-only record at exact `272c8bb5`, recorded
2026-10-29T14:29:18.7911899Z, confirms Windows NT10.0.26300.0, PowerShell7.6.5,
rustc1.93.1 (`01f6ddf75`, 2026-02-11), Cargo1.93.1 (`083ac5135`, 2025-12-15),
rustfmt1.8.0-stable (`01f6ddf758`, 2026-02-11) and Node24.22.1. This supersedes
the earlier `2401fcd3` tool-inventory attribution; version reads are not builds
or runtime/UI execution. Root used the existing serialized build setup.
A read-only PowerShell summary-helper parse error was corrected with an array
wrapper; it changed no check/source/artifact and is not a product failure.

## Completed full Eval and desktop component suites

Both completed process records identify clean, unchanged exact `272c8bb5`,
exit0 and empty dirty lists. No result from the later unmerged desktop-read
implementation is attributed to this source.

| Suite | Actual result | Command duration |
| --- | --- | --- |
| Full local-model Eval | 285 passed, 0 failed, 17 ignored; 33 result groups | 6183.3710572s |
| Development desktop component/contract | 282 unit + 2 contract passed, 0 failed, 11 ignored; 699.73s unit-test time | 741.1751851s |

```text
cargo test --manifest-path crates/locallore-eval/Cargo.toml --features local-model --locked --offline --target-dir <owned-D-target> -- --test-threads=1
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --locked --offline --features dev-harness --target-dir <owned-D-target> -- --test-threads=1
```

Full Eval ran 2026-10-29T14:22:38.7036945Z–16:05:42.0747517Z. Its original
log SHA256 is `1fee148648790d84563ed6d2c7b1fc6b3df902fe54092ce544154917306cd1fb`.
All eleven corrected companion groups are explicitly matched passing within its
143-pass/7-ignored unit group. The whole-suite count includes integration
results; zero-test groups add no passes. The earlier original8/2 fixture failure
and additive RED remain separately recorded above, unchanged.

The desktop suite ran 2026-10-29T16:05:42.0896147Z–16:18:03.2647998Z.
Original log SHA256:
`1682b685ceec561dcf5aab0c99d3d17934cb65e9513b19434fd0528dfc9b05ae`.
These are Rust desktop component/contract checks. They do not execute the new
companion operation through desktop IPC, native WebView/UI or a physical SDK
model load. Normal product build/lint above leave the product unlaunched.
Android Rust host compilation is not Android ABI/device qualification.

## Remaining gates and limits

Actual synthetic Host/Engine/Play/RingSink harvest and scripted cold reading are
component evidence. The 25 stored tuple controls, stored unavailable/rejected
envelopes and rehashed tampering are trusted codec/binding controls, not observed
Engine outcomes or authenticated origin. DisableTrace actually harvests
HostUnavailable, then must refuse after teardown when final identity is gone;
it is not a successful stored-unavailable journey. Finite owned-job controls
simulate failures, partial writes and interruption; they are not OS crash tests.
The native entry is checked only for canceled-before-reservation signature/path.

No model execution/assets/runtime qualification, new companion IPC/UI consumer,
new render capture, phone or desktop-control execution is claimed for this slice.
The unchanged broad regression roster includes the existing selected-prefix
hardlink refusal and native archive pinned-ancestor/junction guard fixtures.
Those existing OS-guard regressions are distinct from any **new companion-specific**
link/reparse/case-alias/isolation qualification, which remains unmeasured; no
new standalone OS probe was introduced. No full valid64 boundary, isolated512KiB
overflow, universal race proof, SDK-load measurement or semantic improvement is
established.
No historical30 causes are reconstructed. Old Report4/StoredTurn4/recording/
trace/capture formats, captured model samples and literal-v1 comparator limits
remain unchanged; both original and newer human assessments remain
**needs improvement**. PR#225 remains unaccepted; no merge, dependency/task
completion, D07/D02 acceptance or quality approval follows from this slice.

The documentation author performed source/bounded-record/Git reads and whitespace
checks only. Root owns actual execution, remaining evidence updates and separate
review. The next runnable step is independent evidence review of this bounded
Core companion slice, then a focused reviewable PR. Desktop-reader source on
separate branches still requires its own integration, tests and IPC/render gate;
this document grants no execution promotion or merge authority.

## Normal product restoration

After the development component suite, Root rebuilt the normal Windows product
at clean, unchanged `272c8bb5`, without dev-harness. The existing normal build
command above exited0 in **9.7552782s**,
16:20:11.6568450Z–16:20:21.4121232Z. Its original process/log records are retained;
the normal product remains **unlaunched**. No subsequent source, test, schema or
frontend change is included in this companion branch: the qualification
integration above the tested source changes this document only.
