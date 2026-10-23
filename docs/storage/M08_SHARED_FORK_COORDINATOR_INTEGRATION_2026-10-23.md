# Shared native fork packet integration, 2026-10-23

Refs #12 (M08.01/.02 partial), #30 (D08.04 prerequisite). Coordinator-delegated
integrator `/root/desktop_runtime_profile`, `impl/m08-shared-fork-integration`,
reused clean `source-derived-lineage` checkout. Claims
[#12 6373242128](https://github.com/OptimumAF/LocalLore/issues/12#issuecomment-6373242128),
[#30 6373242569](https://github.com/OptimumAF/LocalLore/issues/30#issuecomment-6373242569).
Owner review/merge remains with the coordinator; this packet is not merged by
the integrator and does not complete either milestone.

## Source reconciliation

Fresh `git fetch origin main` confirmed accepted base
`e534f01e107a48642370fa0a976fa25c747baba9`. The reused checkout was clean at
accepted timeline PR106 head `be11f2900148db7573d1fc9e136274026e5a7405`; it was
switched to a new integration branch from current main before imports.

| Reviewed original | Integration cherry-pick | Purpose |
| --- | --- | --- |
| `08c5107d72de242d9c37d541396cf4c523703583` | `4f05e01` | Trusted Host/workspace fork seam and original tests |
| `490972aa6153335644470214aa0fbea4b6a5196d` | `8b66a82` | Opaque-receipt test correction; production unchanged |
| `3ae0acad4d513f4fcbd800562db89f6f4db254d8` | `c09af2d` | Author source/check/limit evidence |
| `5a77ec6e62ce93625654a357532f0c08aacb213c` | `a8a5fdd` | Independent source review and actual seven-case execution |

All four imports applied without conflict. No implementation or original-test
edit was required. Between original base `b2c03d4` and current main `e534f01`,
only `crates/locallore-storage/tests/long_history_stress.rs` and three long-history
evidence documents changed. Both owned production files were unchanged there.

Read-only diff from reviewed `3ae0acad` to integrated `a8a5fdd` is empty for root
Cargo manifests/lock/toolchain, core/storage/workspace source and their manifests,
storage migrations, the Lantern Quay fixture, and `fork_host.rs`. In particular,
the actual tested native seam, Store/Engine source, dependencies and focused test
bytes are identical. The integration retains current main's added long-history
tests/docs. This source comparison is not claimed as a fresh combined full-suite
execution.

## Validation and execution attribution

The integrator previously independently ran the unchanged actual Host/SQLite
target on the original frozen packet and retains its exact evidence in
[the independent review](M08_SHARED_FORK_INTEGRATION_REVIEW_2026-10-23.md):

```powershell
cargo test --offline --locked -p locallore-workspace --test fork_host --jobs 1 -- --test-threads=1
```

Actual **7 passed, 0 failed/ignored, exit0** on `3ae0acad` (production08c5107,
test490972a), fresh own D target/TEMP, debug0/incremental0; compilation39.56s,
tests0.39s. Log SHA256
`66b413df6ff4bbb863797449d66d6492c1891daf582ff598a2ac9184e48e2ddd`.
`fork_host.rs` SHA256
`a42d2ecff9f1388305048520c7d0885b28441056fe792effc5be0e1726c98679`.
No new compile is necessary to re-establish those identical source bytes; the
coordinator explicitly authorized reuse and reserved compilation for other work.

The author's default/all-feature scoped250-test runs, two Host unit cases,
portable no-default158 tests and strict Clippy remain precisely attributed to
the original packet in [the author report](M08_SHARED_FORK_PORT_2026-10-23.md).
They were not re-executed/recounted as tests of this newer combined main. Initial
opaque-receipt compile failure remains preserved there; it is not hidden by the
successful final tests or rewritten as an executed semantic test.

Actually performed after integration on Windows x64 / Rust1.93.1:

```powershell
rustfmt --edition 2021 --check crates/locallore/src/host.rs crates/locallore/src/host/fork_port_tests.rs crates/locallore-workspace/src/lib.rs crates/locallore-workspace/tests/fork_host.rs
git diff --check origin/main
```

Both PASS, exit0. Exact production/dependency/test comparison above is empty.
No redundant heavy test/Clippy, package/native compilation or application launch
occurred in this integration. Only source, tests and these evidence documents
are proposed; no generated artifacts/private data are tracked.

## Scope and next task

This supplies the reviewed trusted Rust fork port only. No Host JSON operation,
desktop/JNI caller, child auto-selection, author grant, observer privilege,
schema4/migration, alternate Store, inference/model/worker/profile change is added.
Fixed child identity retry is immutable parent/fork matching plus current child
head, with expected head guarding new creation only. Cancelled does not prove an
earlier fixed child never committed; native adapters must recover the same ID,
use independent window/activity epoch fences and keep cancellation callbacks
short/non-reentrant under Host/Store locks. Terminal providers may still drain
without authority to commit.

Next: coordinator checks the focused PR/base/head/diff and authorizes any merge,
then separately claims native desktop/JNI fixed-ID recovery and actual UI/platform
verification. No reviewer/integrator merge, release, settings, CUA/desktop/device,
model/worker, dependency download or protected-resource action occurred. Full
M08/D08, physical Android, offline/package and real-model gates remain separate.
