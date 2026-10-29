# Closed validation cost observations

Refs #14 (M10.02), supporting #13 (M09.06). This Windows host diagnostic measures
existing validators against preserved closed restart evidence. It never grants
a live lease or qualifies a model, device, original execution or milestone.
Existing owner/client/contract guards, queries and deadlines are unchanged.

## Fixed actions and inputs

`benchmarks/closed_validation_profile.py` has four fixed phases:

| Phase | Existing operation | What it can establish |
| --- | --- | --- |
| `inputs` | `owned_restart_contract.revalidate_inputs` | Cost of the complete existing file/source/tool checks |
| `proof_before` | `android_process_verification_v5.verify_proof` | Cost of replaying the last command's captured pre-proof |
| `proof_after` | Same fixed reader | Cost of replaying its captured post-proof |
| `controller_refusal` | `verify_controller_result` | Cost of the recorded early `capability` refusal only |

The result phase requires a refused `death`/`resource_uncertain` result before
timing. It does **not** traverse or measure a successful controller's deeper
request, build, restart, model-transfer or prerequisite graph. Completed-result
substitution is refused; no arbitrary operation, provider or reader is selected
by JSON. Expected controller and target workers come from separate bound
external `started-v1.json` records, then agree with session/running/proofs.
Closed-file consistency does not independently authenticate past execution.

The plan has exactly `version=1`, `scope=closed-validation-cost-plan-v1` and nine
file bindings: `admission`, `running`, `session`, `client`, `controller_launch`,
`controller_started`, `target_result`, `target_started`, `controller_result`.
A binding has exact `path`, integer `bytes` and lowercase SHA256 fields.
Metadata is bounded to4MiB; role filenames and canonical paths are checked before
their contents are consumed. The supported case has both last-command proofs;
an incomplete proof is not repaired by later observations.

Only the fixed44 source/tool/metadata pins are admitted for the inputs phase.
This includes the Python executable/DLL, SDK tools, compatibility/capability
records, source files and the65B transfer fixture. It excludes model weights,
APKs, guest images, private keys and the process-probe executable. Proof phases
admit only their proof/query/session files; the refusal phase additionally
admits its result. The unchanged input validator locates its **own already
loaded Python DLL** through `GetModuleFileNameW`; no former target PID is opened.

The executor checks current source/interpreter identities and the exact known
probe/C-source paths before hashing declared assets. It admits both canonical
`command-01.stdout.bin`/`command-02.stdout.bin` capability outputs only after
checking their paths, strict binding fields and bounded bytes. A data inventory
projection by itself is not a read grant; the worker always uses the checked
intake path. This closes a separately preserved preflight alias regression.

## Execution, observations and limits

Run from the physical D checkout. Set `TEMP`, `TMP` and `TMPDIR` to
`D:/Dev/_Temp`; the runner also sets these process-local values. For example:

```text
python -I -S -B benchmarks/closed_validation_profile.py --plan D:/Dev/Experiments/LocalLore/<packet>/closed-case-plan-v1.json --plan-sha256 <exact-sha256> --output D:/Dev/Experiments/LocalLore/<packet>/<fresh-output> --repeat 1
```

Output is create-only, physically D, outside every Git checkout. Parent and
private-worker paths both enforce this. The existing finite supervisor admits
one worker for180 seconds, captures binary streams and records actual worker
identity, known termination and resource closure. Repetitions are explicitly
bounded to1–3; they repeat only closed reads, never an SDK or inference action.
Source/input bindings are checked before and after. Partial/refused runs remain
private evidence and cannot become runtime acceptance.

`validation_profile_stats.ProfileCapture` observes a cooperative action using
standard-library `cProfile`/`pstats`. It rejects preexisting profiling tools,
preserves external legacy callbacks, releases its own collector, propagates the
original action exception and returns independent snapshots after clean closure.
Monitoring tool name/mask checks are cooperative ownership checks: they cannot
authenticate hostile same-name callback replacement. Profiler state and timing
are never authorization or validation verdicts.

Python audit events restrict reads during each fixed action to exact admitted
paths and refuse writes, socket/process-launch events and filesystem mutations.
A denial permanently invalidates that observer. This is **not an OS sandbox**
and cannot observe every native operation or prevent arbitrary hostile Python
code. These restrictions supplement the fixed unchanged readers; no untrusted
module or executable is loaded from the plan.

The read observer records Python read-open calls and the sum of declared file
size per open. That sum is neither actual bytes read nor OS/disk traffic; cache,
partial reads and native loader activity are not inferred. `self_ns` excludes
subcalls, `cumulative_ns` includes them. Nested cumulative times must not be
added as independent wall time. Wall and process CPU counters are different
observations; integer nanosecond representation does not promise nanosecond
accuracy. All costs include instrumentation overhead. Raw function filenames,
captures and case data stay private on D; only reviewed aggregates belong in Git.

## Python compatibility and preserved failures

The installed Python3.14.7 observation shows `cProfile` reserves monitoring tool2
while `sys.getprofile()` stays `None`. The original legacy-only ownership check
therefore failed normal exit and left its monitoring slot occupied. The first
original14-test cohort reports3 failures/9 errors; the later errors include
cascades after that leak. The corrected implementation passes the exact original
four-case smoke. Replaying the original14 after the fix leaves one assertion
whose assumption that active profiling must install a legacy callback is false.
A separate backend-aware14-test revision preserves call/exception/ownership
assertions and strengthens monitoring cleanup. It passes; this is not a claim
that the original14 source is byte-identical to the final fixture.

The implementation follows [pinned CPython3.14.7 source](https://raw.githubusercontent.com/python/cpython/v3.14.7/Modules/_lsprof.c)
and the [monitoring API](https://docs.python.org/3.14/library/sys.monitoring.html).
The consulted rolling documentation identifies itself as3.14.10; exact installed
behavior was separately observed. No tag-to-installed-binary attestation, new
runtime dependency or upstream source vendoring is claimed. The
[official profiler documentation](https://docs.python.org/3.14/library/profile.html)
also distinguishes execution profiling from benchmarking.

## First actual closed observation

At initial profiler source `dad0496bb56384b129af840f4fc4db73a69f338e`, the finite
owner completes in1,878ms, child0, complete capture/cleanup, empty streams and
stable source/input hashes. This reads the actual preserved last command55;
the original model/restart case remains attributed to `f589f270` and refused.

| Phase | Profiled wall ms | Python read opens | Declared size times opens |
| --- | ---: | ---: | ---: |
| Inputs |328.491|102|102,969,064|
| Before proof |23.484|10|443,716|
| After proof |24.108|10|442,954|
| Early controller refusal |88.801|53|8,004,065|

All open counts and declared-size sums match independent source-derived
expectations. In the inputs sample, SHA update self time is130.638ms, buffered
read self time52.856ms, path-existence checks44.227ms and lstat35.641ms. This
identifies repeated hashing and path validation as useful host optimization
targets; it does not establish original Android/model latency or a speedup.
The first raw profile SHA256 is
`18b81a828046eeb727b0156f2a2a76df63188cbf83fead7107338d4381794366`.

Independent boundary tests subsequently identify observer reset, incomplete
event denial, output ancestry and metadata-before-filename-check gaps. The first
25-test cohort preserves12 failing assertions/subcases with zero errors/skips;
its genuine metadata/proof/refusal positive fixtures already pass. Corrections
and final checks are recorded with their distinct source versions in the ticket
and focused PR. These are diagnostic-runner bugs, not changes to gameplay or
the original refused runtime outcome.

## Intermediate integrated checks and hardened observation

Executable source `51b7f5144d73d84f2bf644df3011be1a4f6bbb3b` passes **58 tests**:
14 profiler tests,29 diagnostic-boundary tests,9 unchanged initial guard tests
and6 unchanged controller tests. The finite Root owner completes in72,654ms0,
zero failures/errors/skips, empty stderr, known capture/cleanup and116 stable
source/helper/test hashes. The14 are included in58, not additional tests.

Original boundary evidence is retained separately:25 methods/12 failing
assertions or subcases; three added methods/10 failing subcases for typed
counters and canonical proof/query paths; one added method/five failing
subcases for nested query metadata shape/size. Existing test bodies are not
weakened. The first integrated57-run leaves one error-tag assertion after the
semantic path refusal already succeeds. The implementation restores the
existing `canonical_path` tag; the same57 pass. The later58 add the nested-query
regression. Metadata now hashes and decodes the **same** bounded bytes, reading
at most CAP+1 to detect oversized data; nested and frozen metadata use this
path too. Old streams, source snapshots and refusals remain unchanged.

The hardened actual profile then passes in1,978ms0 with complete capture/cleanup,
empty streams and stable sources/inputs:

| Phase | Profiled wall ms | Python read opens | Declared size times opens |
| --- | ---: | ---: | ---: |
| Inputs |342.267|102|102,969,064|
| Before proof |25.693|10|443,716|
| After proof |25.662|10|442,954|
| Early controller refusal |96.257|53|8,004,065|

The44 unique admitted inputs total70,258,662 declared bytes. Counts and size
sums remain identical to the original independent expectations. The two
single-sample observations do **not** establish a speedup or distribution.
Final raw profile SHA256
`88f97454d3b7d2b231ef58ada31c3d5d7740945db286ba2995156c387ee5c72f`;
parent result `30d2ca8648bfdd963c5d5bdfa8a764231194e8b6c96b7bd7478b5e09281b2985`.

The actual Root commands use the physical D checkout and D temporary settings:

```text
python -I -S -B <packet>/check-host-v1.py stats first
python -I -S -B <packet>/check-host-v1.py combined capped
python -I -S -B benchmarks/closed_validation_profile.py --plan <packet>/closed-case-plan-v1.json --plan-sha256 24d9b8e18c3a39cbc7336c3bb0eb37899b0bd985c925fa8ea174e8228cf1124c --output <packet>/profile-final-v1 --repeat 1
```

Here `<packet>` is the private D folder
`D:/Dev/Experiments/LocalLore/2026-10-29-validation-phase-profile-v1`. Its helpers,
source/input requests, receipts and raw streams are retained locally. The plan
references the original closed case; no model weight, APK, guest image or
credential contents are read by these phases. No Android/Rust production source
changes, new dependency, build or emulator/model acceptance is claimed.

## Final checked intake

At executable source `12b779102b64f48ef63b02e0b4fc71861dc53f75`, **62 tests pass**
in the finite Root owner80,307ms0:14 profiler,33 diagnostic-boundary,9 unchanged
guard and6 unchanged controller tests. Zero failures/errors/skips,116 stable
source/helper/test hashes, known cleanup/capture and empty stderr. The earlier
58 are included in62. The independent final review finds no unresolved concrete
issue and confirms all23 runtime source files and original29 diagnostic test
bodies remain unchanged.

The capability regression is preserved separately. Its first synthetic worker
fixture stops at a mismatched fake SDK hash, before the watched alias; that
attempt is a fixture-precondition error, not a meaningful RED. The corrected
fixture uses the existing matching SDK tool bytes as ordinary read-only inputs,
with no SDK command. Its four worker subcases fail against the unchanged old
runner, then pass against the checked intake. Three additional helper tests
exercise canonical, empty, malformed, changed and oversized output files.
Both capability stdout paths and binding shapes are checked before either
output is consumed; source/interpreter and fixed probe paths are checked before
remaining declared asset hashes. The projection-only inventory fixture is
unchanged and grants no read authority.

One final actual checked profile completes in1,877ms0 with known capture/cleanup,
empty streams and stable source/input hashes:

| Phase | Profiled wall ms | Python read opens | Declared size times opens |
| --- | ---: | ---: | ---: |
| Inputs |326.016|102|102,969,064|
| Before proof |24.637|10|443,716|
| After proof |23.272|10|442,954|
| Early controller refusal |87.856|53|8,004,065|

Counts and size sums still match the independent source expectations. These
separate implementation checkpoints are not a benchmark distribution or a
speedup claim. Raw profile SHA256
`e5ffe2ffcf0daecfc0220f3061b6867d1fa64da6d23f403d5b7846048f1a4c70`;
parent result `14e1cf3dd01b868bf72bcb6cafb38ed1ee3e89fa5f8fccb0631c123b56e40361`;
independent final source review
`aff25d3c223a2248f8191b8fa70552bec8fb3ecba851ecaa6869a26b2972b9bb`.
Final driver entries are `check-host-v1.py combined capability` and the same
profile command above with output `<packet>/profile-checked-v1`.

M10.02 and supporting M09.06 remain **in_review**, with full checkboxes unchanged.
Next work is a justified per-guard hashing/path-work optimization, with explicit
mutation fixtures and fresh complete checks at all three existing trust
positions. No cache across boundaries, missing query, longer deadline or new
guest/model attempt follows from a profile. External restart remains unverified
for the spent case; physical-device, ARM64, quality and performance gates remain
separate.
