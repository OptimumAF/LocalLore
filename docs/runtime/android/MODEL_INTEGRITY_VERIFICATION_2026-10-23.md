# Read-only model integrity and storage investigation, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05),
following [#84](https://github.com/OptimumAF/LocalLore/pull/84).
The bounded investigation and tool are implemented and locally verified;
full-task acceptance remains pending. No inference was admitted. The A cache
is preserved and remains mismatched; B currently matches the approved source.
The cause and timing of A's changes are unresolved.

Base is accepted main `aec8ad02a662b87b960723da8878f4ead4f0a28d`.
Qualified tool/tests are `7278060`; later changes are documentation/evidence.
See the [aggregate](MODEL_INTEGRITY_RESULTS_2026-10-23.json),
[device observations](MODEL_INTEGRITY_DEVICE_2026-10-23.md),
[independent review](MODEL_INTEGRITY_REVIEW_2026-10-23.md) and
[reproduction instructions](README.md#inspect-model-integrity-without-inference).

## Actual complete observations

All three observations cover exactly 2,588,147,712 bytes: 77 full 32MiB intervals
and a final 4,456,448-byte interval, 78 ordered rows. Source inspection makes two
complete same-handle passes, comparing whole/chunk hashes and handle/path
fingerprints. Devices independently hash the whole file before and after their
complete chunk pass, with size checks, regular-file/metadata and benchmark-owner
absence checks. Each device chunk has a separate on-device count read and hash
read. Only hashes/counts/metadata return, never model bytes.

| Observation | Both whole-file reads | Complete comparison to source |
|---|---|---|
| Host source | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` | All 78 intervals match across repeated passes |
| A | `2dde0b287178132dc8b0fdcbd30fba12b087f54993c0e7ee6d135a5394921700` | Intervals 0–71 match; 72–77 differ |
| B | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` | All 78 match the source |

A's six differing intervals cover offsets **2,415,919,104 through
2,588,147,712 (exclusive)**, totaling 172,228,608 covered bytes. This bounds
where differing content was read; it is not the number of changed bytes.
The older #84 A hash `59d70767f8f7a8710fb2d1427e3cf94917ca5b6847fdbfd11f1fcf2617f0eb4d`
remains a distinct earlier observation. The new A reads agree with each other
but differ from both that earlier observation and the approved source. No
continuous observation isolates when or why the difference arose. An interim
progress message mistakenly assumed the older hash; final raw records and this
report correct it. There was no failed scan associated with that message.

Fresh inventory recorded four online emulators and zero physical phones. Only
the two authorized Android 15/API35 x86_64 targets were inspected. The benchmark
APK on both remains SHA256
`715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6`,
from frozen harness `e7beb858b271aa4636f2f5e7b34deedda1fc3f21`.
Its existing LiteRT-LM Android 0.18.1 CPU/Gemma profile is an observational
reference, not a new runtime/backend selection. No dependency changed.
All 21 current LocalLore APK identities per emulator match preflight afterward;
benchmark owners were absent. All 702 recorded transport commands completed with
clean terminal clients, and the final host census found no selected/inventory
client. The initial failed wrapper did not retain its inventory result fields.
This does not audit every save byte or establish historical process continuity.

## Working tool and checks

`benchmarks/model_integrity.py` performs explicit local-file reads and validates
complete hash receipts. It requires exact ordered indices/offsets/lengths,
including the partial tail; strict JSON shapes/digests/types; stable before/after
observations; and the approved source size/hash. Missing/reordered/duplicate
coverage, identity drift and contradictory full/chunk comparisons fail closed.
Receipts contain no paths or model content; inspection/comparison failures print
fixed categories rather than private exception text.
It adds no ADB, inference, copy, repair or app lifecycle operation.

Actually executed on this source:

| Command | Result |
|---|---|
| `python -B -m unittest discover -s scripts/tests -p test_model_integrity.py -v` | 15 adversarial tests pass |
| `python -B -m unittest discover -s scripts/tests -p 'test_*.py'` | 168 pass, including those 15 |
| `python -B -m unittest discover -s benchmarks -p 'test_*.py'` | 140 pass |
| `python -B benchmarks/model_integrity.py compare ...` against actual receipts and pinned identity | Source self-comparison exits 0/match; A exits 2/mismatch; B exits 0/match |
| `git diff --check` and evidence/link/privacy checks | Pass |

The compare invocations used `--reference <source-receipt.json> --observed
<source/A/B-receipt.json> --expected-bytes 2588147712 --expected-sha256
181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`,
with task-private receipt/log paths. These are integrity results, not gameplay
passes. No Rust/JVM/Android build, model load, generation or performance check
was run; only Python tooling and evidence changed. Symlink refusal has a mocked
leaf-link unit test, not an executed Windows adversarial reparse attack.

## Storage failure and preservation

The first private preflight wrapper failed on an unavailable stderr attribute;
it is retained as a setup-only failure. The corrected wrapper completed
preflight. Before any long model scan, host storage then failed the unchanged
1GiB read-only guard. That initial guard was outside its wrapper's catch and
did not persist its exact free-byte value; the subsequent captured value was
655,175,680 bytes. It is a later sample, not a reconstruction of the missing
value. No long model scan launched in that attempt. The wrapper was corrected
to record future storage samples before asserting the gate; no budget relaxed.

Five known inactive compiler `target/debug` trees from earlier work in this chat
were moved intact to task-owned D: storage, with original paths restored as
junctions. They belonged to the durable-turns, desktop shell, durable-replay,
Android warm and storage worktrees. Exact resolved scope, fresh destinations,
no nested links and executable/command-line workspace-prefix checks preceded
native PowerShell moves. Those process-prefix checks are not an exhaustive
audit of every process working directory. No model, save, AVD or user-data path
was in the move allowlist.

**All 12,507 files / 5,144,755,186 logical bytes match their before hashes**;
an independent destination rehash also matched every file. Five original-path
junctions were verified. After relocation, fresh gates admitted the read-only
scans. At B completion C: free was 5,198,635,008 bytes and D: free was
123,806,466,048; those snapshots do not guarantee future headroom or identify
the cause of earlier storage loss/model differences. Pre-existing compiler
outputs exposed as untracked by switching branches remain preserved and are
excluded from this PR.

## Limits and next task

These are trusted read-window observations, not atomic filesystem snapshots,
forced backend writeback, an OS-adversary proof or a historical integrity audit.
Whole-file hashes are separately observed; they cannot be reconstructed from
the list of chunk hashes. Leaf links are refused by the local tool; ancestor
links are not comprehensively audited. Read-only commands do not imply zero
background OS I/O or unchanged access times.

No model copy/repair/eviction, app launch/stop/restart, inference, cache removal,
release, merge or repository-setting action occurred. A's model and its observed
788,412,736-byte XNNPACK cache were preserved, with metadata unchanged during
this window. That observed cache size is not a proven maximum. Raw receipts,
transport journals, compiler ledgers and diagnostics remain private; the public
aggregate binds their lengths/hashes without serials, paths or weight bytes.

M01.01 remains blocked without an authorized physical phone. M01.03/M01.05 and
M01.04/M01.06 acceptance remain partial/unqualified. A is not admitted for
inference. B's identity check passes now, but its guest free space at completion
was **1,800,622,080 bytes**. The earlier controller required 1GiB guest space
before a run; it did not guarantee that reserve after cache creation. Adding
the previously observed cache to that reserve requires **1,862,154,560 bytes**,
already 61,532,480 bytes more than B currently has, without establishing any
upper bound on new cache or OS growth.

The next runnable packet is **M01.05 cache-aware storage admission and preserved
workspace capacity preparation**, then the unchanged-profile B real-model
control only when fresh identity/ownership/storage checks admit it. Keep A
untouched, preserve every failure and compare B's full identity before/after
execution. Current inspection success alone does not authorize that control;
inference remains held through this packet. No phone/ARM64, narrative quality,
latency, supported profile or production-backend gate is satisfied here.
