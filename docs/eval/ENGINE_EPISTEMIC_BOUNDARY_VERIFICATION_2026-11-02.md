# Composed engine boundary regressions — 2026-11-02

Refs #14 (M10.01). Two original Rust integration tests add composed invariant
coverage to the real engine. They passed on first execution. No production bug,
functional RED, engine fix or full milestone acceptance is claimed.

## New executable coverage

`m10_staged_epistemic_rejection.rs` stages a claim, a belief in that new claim,
movement, discovery, time advancement and an inventory/relationship transfer,
then fails the eighth command on an unavailable ability. Canonical bytes,
canonical records, warmed receipt cache, revision and turn-key absence must
remain unchanged. Removing only the bad suffix and reusing the same turn key
must accept sequences 1–7 without ghost claim/evidence or sequence gaps. Exact
retry returns the stored receipt, the original failed payload then mismatches,
and provider-free replay/restore preserve the accepted result.

The warmed cache initially contains zero receipts. This case does not qualify
rollback with every possible nonempty cache/history or every invalid suffix.
Existing smaller atomic tests and the seeded suite remain in place.

`m10_query2_observation_chain.rs` composes seed knowledge A, a private correction
to B, a witnessed discovery of B, then a private correction to C. The player must
remember B, Mira must retain seed A, the recorded discovery must remain B with
its original scoped event source, and only a granted omniscient view exposes
canonical C. Parent/sibling future canaries share numeric head 3 with the
selected branch but never enter its public search, counts or pages. Historical
revision 1/2 views retain A/B, the B results span two distinct one-row pages, and
a cursor cannot cross historical request identity even when B rows match.
Queries must not mutate the selected canonical state/records.

These are revision-historical and branch/observer checks, not an elapsed-time
deadline benchmark. No transcript, belief or derived view replaces canonical
world truth. No model/provider is involved.

## Source and execution

Public base is `d3862614cb6654305d88d44901eda36b83f2a4e8`. The tested real crate
was the unchanged frozen operator checkout at
`8924278ce1c877e6d67c90c15a35fb23ca7198dc`, physical
`D:/Dev/Repositories/LocalLore`. Its entire `crates/locallore` Git tree and root
Cargo manifest/lock, pinned toolchain and seed fixture are identical to that
public base; independent review also matched 131 actual source/input blobs.

No operational checkout was switched or edited. The desktop worktree tool
cannot create from this chat's nested repository under its non-Git workspace
parent. An ordinary test-only Cargo package under the private D: experiment
therefore compiled the real crate by path with its existing `host` feature.
It recreated the integration-test/fixture relative layout. It contains no
second engine, production adapter or inference provider. A separate Git index
publishes the two tested files without changing the frozen checkout or its
normal index. This is an independent test PR against main, not a prerequisite
on the unrelated host bridge PR #367.

The proof lock contains 30 packages: 28 registry packages match the existing
415-package public lock by version/source/checksum, plus the actual local
`locallore` dependency and the proof root. No runtime, model, SDK, native or
registry version/dependency/license was introduced. Installed pinned Rust
1.93.1 was used offline, with automatic toolchain installation disabled.

Actual results:

| Selection | Result |
| --- | --- |
| Two new cases, first execution | 2 passed, 0 failed/ignored; initial compile 14.82 s |
| Final exact LF sources, locked/offline | 2 passed, 0 failed/ignored |
| Existing contracts, including 10,000 seeded attempts | 26 passed |
| Existing inspection query | 16 passed |
| Existing Query2 | 10 passed |
| Existing message identity | 6 passed |
| Existing restore | 9 passed |
| Final strict Clippy on proof test targets | exit 0, `-D warnings` |
| Rustfmt check | exit 0 |

**69 distinct tests passed**: two new plus 67 existing. Repeated new-case runs
are not additive; the 10,000 attempts are inside one existing test, not 10,000
new test methods. This is selected real host-engine coverage, not a full
workspace, Android, JNI, physical-device, model-quality or performance gate.

The two initial Clippy findings were unnecessary clones in expected-slice
comparisons. They were corrected to `std::slice::from_ref` with identical
expected values and assertions; no lint suppression or assertion removal.
The first refinement stopped after updating one file because its broad substring
matched two occurrences in the other. The intermediate Clippy failure and all
original/pre-lint sources and logs remain retained. Final exact-statement
correction passes. Both functional cases stayed green throughout; these are
lint/evidence-tool failures, not a fabricated engine defect.

Executed commands used process-local TEMP/TMP/TMPDIR on `D:/Dev/_Temp`, existing
`CARGO_HOME=D:/Dev/Tools/Caches/Cargo-LocalLore-v1`, target under the private OUT,
two jobs, debug info disabled and `CARGO_NET_OFFLINE=true`:

```text
cargo +1.93.1 test --locked --offline --manifest-path Cargo.toml
cargo +1.93.1 clippy --locked --offline --manifest-path Cargo.toml --all-targets -- -D warnings
rustfmt +1.93.1 --edition 2021 --check tests/m10_staged_epistemic_rejection.rs tests/m10_query2_observation_chain.rs
```

Those commands ran from the private proof package. The existing-suite command
ran from the unchanged actual repository:

```text
cargo +1.93.1 test --locked --offline -p locallore --features host --test contracts --test restore --test m08_query_v2 --test m08_query_v2_message_identity_review --test inspection_query
```

When this PR is checked out normally, the reusable new selection is:

```text
cargo +1.93.1 test --locked --offline -p locallore --features host --test m10_staged_epistemic_rejection --test m10_query2_observation_chain
```

That last repository-form command is provided for review; this packet executed
the byte-identical new tests through the external proof package to preserve the
frozen operator checkout. It is not reported as a whole-repository execution.
The Query2 file follows the existing host-feature gate; normal non-host builds
do not gain a new dependency on the inspection API.

## Evidence and remaining gates

Private OUT is `D:/Dev/Experiments/LocalLore/2026-11-02-engine-boundary-review-v1`;
REC is its matching `D:/Dev/Recovery/LocalLore` directory. Original proposal,
source/input, dependency, raw test/lint, review and publication records stay
local. Independent source review verified the assertions and joins; the final
addendum SHA256 is
`eea45ddc4555df167e630676c48a81f83c561a9b5e0e33106dcaed442b7c7568`.
Final test-file SHA256 values are
`931c399fdb7016952cf82c075fce86aa76c4234c9a7c1bc6c7fe4fc60a1b9b13`
and `52d56af6d450c0aa525c2c51c9335e12a6611c6f2190b1cb5aa5087c8a784f9a`.

Declared bounds are 2 GiB build target, 16 MiB controls/source, 8 MiB synthetic
outputs and 128 MiB small-record recovery. Final test observation was
661,106,618 target bytes and 84,921 control/source bytes before report/publication
records. These are file-size observations, not a filesystem quota or complete
TEMP/cache high-water measurement. Build output and failed lint evidence remain;
nothing was deleted to make a test pass.

No private stories, model weights, credentials or raw private diagnostics are
uploaded. No guest/image/model/phone/SDK/ADB/ledger operation, other-emulator stop,
system setting, release or merge occurred. Knowledge Android tests remain 0/4
executed under their separate pending approval/storage gates. M10.01 remains
unchecked until broader criteria and owner acceptance; no whole-app completion
or release readiness follows from these tests.
