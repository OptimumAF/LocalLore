# Record preparation refusal verification — 2026-11-03

M10.02, supporting M09.06. Host implementation in review; Android unrun.

## Problem and change

B119's approved one-use operation failed with EnvironmentRefused during the
broad preparation phase. Its exact original reason/call was discarded. Later
sequential read-only resource observations cannot recover that missing evidence.
The failed/spent operation and all frozen sources remain unchanged.

The inner SDK18 stage runner now emits fixed attempted-step markers and a
closed reason vocabulary for exact trusted exception classes. It never formats
exception payloads or chains. The phase, pass conditions, operation ordering,
source/authority/one-shot/ledger/job/deadline checks remain intact. Unknown
failures remain generic. See RECORD_PREPARATION_REFUSALS_V1.md for the policy.

## Actual host execution

Physical source snapshot: PR392 head
28a633adc27133dca1fd23ed5d020960b0249aac, tree
cdeefefa6f7b0fcd2d39717dc37ba6e0400bbcfa, 2,668 Git files / 38,170,452 bytes.
Only the operator and one new original test file form the code change.
Root used a verified raw Git snapshot and alternate index after the managed
worktree tool rejected the physical repository as outside this chat's attached
workspace roots. Existing separate reviewer worktrees and normal checkout/index
were preserved. New main 11a1e94a independently merged desktop PR395; this
packet remains stacked on open/unmerged PR392, not on that unrelated change.

Windows, installed Python 3.14.7, Git 2.33.0.windows.2; no dependency added.
Process-local TEMP/TMP/TMPDIR were D:/Dev/_Temp. No global settings changed.
The exact central commands, from D:/Dev/Repositories/LocalLore, were:

```text
python D:/Dev/Experiments/LocalLore/2026-11-03-record-preparation-reasons-v1/run_host_owned.py baseline-v1
python D:/Dev/Experiments/LocalLore/2026-11-03-record-preparation-reasons-v1/apply_refusal_fix.py
python D:/Dev/Experiments/LocalLore/2026-11-03-record-preparation-reasons-v1/run_host_owned.py final-v1
```

The checked runtime_spike owner (source SHA256
51e94325ed5e59a31c64fcc274e7a41c40b9dd969b09d39df7be56b0ee941598)
assigned the worker before releasing its stdin barrier. Limits: 180 seconds,
262,144 combined output bytes. Workers used Python -I -S -B and changed to
candidate-source-v1 before unittest loader/runner calls. Complete source hash
catalogs before/after each execution match (2,669 files including the new test).

| Execution | Actual result | Checked owner |
| --- | --- | --- |
| Baseline, original operator + original new tests | 8 methods; 51 assertion failure events across 6 methods, 0 errors/skips; 2 control methods pass | completed, exit1, 12.308s, known cleanup, stderr0 |
| Final, changed operator + unchanged tests | 23 methods / 6 classes, 0 failures/errors/skips | completed, exit0, 7.512s, known cleanup, stderr0 |

Baseline output is 57,741 bytes; final output 5,834 bytes. The first failure
asserts a missing fixed reason, not a loader/API error. Baseline failures and
raw synthetic output remain separately preserved. Raw unittest summaries report 0.021s baseline and 6.554s final. Worker result
durations (0.303s / 6.841s) also include post-run source hashing and record
processing; owners measure their wider checked-job lifetimes. This is one
host cohort, not a performance or repeatability benchmark.

The new eight-method oracle invokes actual _run_stages with memory-only fake
operational ports. It covers 20 trusted literal reason cases; 10 attempted
failure sites and their original broad phases; spoofed names/subclasses;
unknown, multiple and hostile arguments; string subclass/object formatting
traps; exception cause/context; known built-ins, KeyboardInterrupt/SystemExit;
successful full flow and sticky late/publication failure. Formatting counters
are asserted outside swallowed stage exceptions. Positive controls prevent an
all-refuse implementation from passing.

The other 15 selected methods are the unchanged fresh contract, fresh inputs,
fresh stages, parent operation and parent host classes. Their exact module
selection, recorded before execution, is:

```text
scripts.tests.test_record_preparation_refusals
scripts.tests.test_record_cancellation_fresh_contract
scripts.tests.test_record_cancellation_fresh_inputs
scripts.tests.test_record_cancellation_fresh_stages
scripts.tests.test_record_cancellation_operation
scripts.tests.test_record_cancellation_operation_host
```

The last class's three methods exercise four controlled literal Python child
attempts with the real Windows Job/LiveOutput path, including injected job
assignment failure and unknown-close outcomes. Those refused cases do not
qualify successful inner ownership. Other existing
input fixtures use isolated toy storage. Thus the complete 23-method cohort
is not all-fake: only the new eight stage oracles are entirely memory-faked.
There was no operational SDK/ADB/emulator/phone/model/shared-ledger dispatch.
Known owner cleanup is scoped process evidence, not an independent whole-OS audit.

The unchanged regression fixtures retain temporary synthetic outputs outside
the source map. Sixteen D:/Dev/_Temp directories with the exact two fixture
prefixes and creation times inside the recorded final launch/terminal window
were retained: 647 files / 259,483 bytes. Original bytes and verified copies
are preserved; copies join the packet archive and originals count additionally
toward retention. Prefix/time-window selection is not independent cryptographic
process ownership, because tests do not export their generated root names. No
old fixture roots were adopted, removed or executed.

## Byte bindings and limits

Original new test: 15,435 bytes, SHA256
bc3b4a378d4eb1a51af039733aeb30869f5802bd48319fb449942730b98d4d11,
unchanged between baseline/final. Original operator: 29,986 bytes / SHA256
0a1f9feb5276fd96ac691b0757f264fe88f2aee158a91dc907c0d08f2e0fd198.
Changed operator: 31,655 bytes / SHA256
1c7dac9aef00a7cdc0d5cdc49531802da96e61c14c7bff3aa622daa1a1163fbf.
Only this operator changes between the two tested source catalogs.

The old outer FRESH_OPERATOR pin, paths, source catalog and authorities are
unchanged. The changed inner cannot pass old outer admission; it is not a new
runnable SDK18 generation and cannot use B119's spent approval. Before an
actual device attempt, create/review a coherent new freeze and exact proposal,
meet readiness/admission gates, and obtain separate applicable approval.
Never overwrite frozen B116/B119 source or retag old evidence to adopt this fix.

Android0, native app/ARM64/model/story-quality/full-journey/CI gates unqualified.
No boot, phone discovery, model operation, settings change, other-emulator or
shared ADB stop, operational/preserved-data deletion, private diagnostic
upload, release or merge. Toy storage validators may create/remove isolated
lockfiles; that does not mutate the shared ledger or retire preserved data.
Full milestone criteria remain unchecked; owner acceptance remains pending.

The declared ordinary packet source/test/control/recovery retention allowance
is256MiB; final measured accounting includes retained temporary originals.
There is no system-wide quota or automatic aggregate output enforcer;
physical OUT and records-only recovery share basename
2026-11-03-record-preparation-reasons-v1 under D:/Dev/Experiments/LocalLore
and D:/Dev/Recovery/LocalLore. Final private archive/publication audits and
ticket readbacks are recorded separately; public source/test/report bytes
do not include raw diagnostics or private player/model material.
