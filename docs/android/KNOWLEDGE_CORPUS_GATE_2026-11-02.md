# Native Knowledge corpus consistency gate

B87, 2026-11-02. Refs #14 (M10.01), supporting #13 (M09.04/M09.06) and M10.02.
Implemented and locally verified for review; full tasks and milestone gates stay
unchecked pending their broader criteria and owner acceptance. No merge.

This packet stacks on open/unmerged PR #357 at
`0456479a4e128c31516d708f5044a0a18383c075`. It changes no Kotlin, native
production contract, dependency, model or emulator owner. PR #354's separate
frozen recovery/operator/proposal/approval scope remains unchanged.

## Change and reproduced gap

The host gate previously checked the older Android sample but did not regenerate
the new Knowledge corpus. Kotlin could keep validating stale recorded native
pages after Rust changed. The actual Core example now accepts exactly no args
(original JSON stdout) or `--check`. Check mode regenerates the complete corpus,
appends its one LF, then compares every byte against the fixed committed
`-text` resource through `include_bytes!`. It does not normalize JSON/line
endings, rewrite files, take a caller path or accept extra flags. Unknown input
refuses before constructing the fixture and prints only static usage.

`scripts/check.py host` runs this locked/pinned Cargo check immediately after
the existing Android fixture check and before the Python suites. The existing
PR/main host workflow already invokes that entry point. No workflow privileges,
tool provisioning or branch-protection setting changed. Hosted CI execution
and required-status enforcement are not established by this source inspection.

One new orchestration regression fails the actual selected command graph at
the new gate in both online/offline modes, preserves its nonzero status and
proves no later process runs. Existing assertions now require both named native
fixture commands, their order, locked/pinned tools and literal check arguments.

## Native schema discovery and fix

The broader Core run at `468f360c466baa874d383789d1b51b17a0c76466`
actually failed `host::tests::schema_is_generated_from_rust`: 106 passed,
one failed; later cohorts had not run. The original 79,308-byte stdout, raw
stderr, source map and archive remain. This was not a corpus mismatch.

Actual `host_schema` generation plus structural comparison found exactly one
missing pre-existing operation in `apps/desktop/host-v1.schema.json`:
`inspection_relationship_focus`, with `session`, `query` and `target`.
Checked/generated schemas had 42/43 operations. There were no changed common
operations, removals, common-order changes or other definition differences.
The fix adds only that 20-line node, preserving surrounding formatting. The
strict generated-schema test and all native production code remain unchanged.

Final executable/test source is `670fda97f461f00f3febf8d8ccd473ae8b7c308c`.
Only README and this report change after verification.

## Verification actually executed

Commands ran from physical D:, with process-local TEMP/TMP/TMPDIR
`D:\Dev\_Temp`, offline D: Cargo caches and pinned Rust 1.93.1 / installed
CPython 3.14.7. Each of 14 jobs has its own 900-second Windows job owner, binary
capture, known cleanup, and unchanged before/after source map. No SDK/device
process is launched by these checks.

| Check | Actual result | Owned elapsed |
|---|---|---:|
| Workspace Rust format | Pass at `468f360c`; no later Rust edit | 3.492s |
| Core Clippy, all features/all targets, warnings denied | Pass at final `670fda97` | 3.290s |
| Core tests, all features | **620 pass, 6 ignored, zero failures**, 73 cohorts | 41.431s |
| Check orchestration tests | **18 pass**, one new regression | 2.280s |
| Native `--check` | Original corpus matches, at `468f360c` | 12.684s |
| Default stdout at final `670fda97` | Byte-identical original corpus | 2.737s |
| Unknown / extra / repeated argument | Each exit 1, zero stdout, static 59-byte usage stderr | 1.473 / 1.472 / 1.473s |
| Isolated row-text drift | Fresh compile, then expected mismatch exit 1 | 13.595s |
| Isolated CRLF-only drift | Recompile embedded input, then expected mismatch exit 1 | 3.948s |

The Core total includes ten documentation tests. Six existing ignored tests are
historical/one-shot fixture-capture probes; none were newly skipped. The first
failed run and repeated lint/cohorts are not additional distinct passing tests.
The table gives scoped checks, **not** a full workspace host/Python/CI run.

Relevant reproducible commands, after setting the same D: cache/temp locations:

```powershell
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 clippy -p locallore --all-features --all-targets --locked --offline --jobs=2 -- -D warnings
cargo +1.93.1 test -p locallore --all-features --locked --offline --jobs=2
python -I -S -B -m unittest discover -s scripts/tests -p test_check.py
cargo +1.93.1 run -p locallore --example android_knowledge_filter_fixture --locked --offline --jobs=2 -- --check
```

The corpus remains **54,699 bytes**, SHA256
`b224b559410ad3c34a83f71a1f4a097001d94e366d1ad12a59e9a36e80ebe5ab`.
The positive `--check` and final stdout execute the same unchanged Rust example;
the later schema correction touches only the separate generated Host asset.

## Real drift experiments and preservation

One ordinary task-owned source copy is created from the final complete archive
under private OUT's `drift-source-v1/source`, without `.git` or links. Every one
of its 2,607 files is pinned against that archive; only its embedded corpus is
changed. Cargo runs from that physical D: directory with a separate `drift-target`.
No override flag or substitute comparison helper is added to production.

The first mutation changes exactly one original row's text. Its 54,720-byte
resource is `335dd48b1f15a98bb18b1ddbbde89aefb2ea397e330c2307069c7d60776ecfd3`.
The second starts again from the pristine original bytes, changing only the
final LF to CRLF; parsed JSON is identical. Its 54,700-byte resource is
`173feb3e57d3c373763112958f9ef9dc9ca74a56044a14e0f0bf12408ba8b04c`.
Each actual normal `--check` recompiles the include input, reaches the unique
corpus-mismatch error, emits zero stdout and exits 1. The captures show
`Compiling locallore`, successful compilation and the owned example invocation;
these are runtime mismatch refusals, not compiler errors or stale executables.

Primary source/resource/lock bytes stay unchanged across both experiments.
Both mutated full source snapshots remain in separate archives before the next
copy change. Four complete archives each preserve 2,607 entries. No failed
capture, source copy, generated target or earlier recovery evidence is deleted.

Initial primary jobs retain their 3 GiB generated / 64 MiB control caps. Before
creating the isolated copy, the measured retained outputs justified a documented
4 GiB / 96 MiB cap for its separate owner; selected recovery remains 192 MiB.
No failed guard was relaxed or old result relabeled. Final generated logical
bytes were 3,244,170,010, below that adjusted bound. This host-only budget does
not modify the shared emulator ledger or its two-root/64 GiB admission rules.

Private OUT and REC use `2026-11-02-knowledge-corpus-gate-v1` under
`D:\Dev\Experiments\LocalLore` and `D:\Dev\Recovery\LocalLore`.
All original failures, phase captures/maps, four archives, independent source,
closed and negative reviews, and verified copies remain there. Before reuse,
all 147 prior B86 source/control pairs and 74 artifact bindings were verified.
Final canonical preservation receipts and released claims are linked on #14.

No B87 JVM/Android test, APK rebuild, JNI/ARM64 execution, model/phone result,
ledger transition, guest/ADB lifecycle, settings change, other-emulator stop,
private upload or merge is claimed. PR #357's four new Compose journeys remain
unrun. Next runnable preparation is their separately bounded target profile;
actual execution and PR #354 recovery retain their applicable approval gates.
