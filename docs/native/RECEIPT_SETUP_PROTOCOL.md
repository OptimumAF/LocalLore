# Receipt setup qualification protocol

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). This debug-only experiment
exercises the production setup controller with real receipt transactions and
original 63-byte synthetic content. It does not qualify DocumentsUI, Gemma
provisioning, SDK inference, a reference phone or a production backend.

Build with all four explicit LiteRT, model-setup, model-volume and model-receipt
verification flags. Receipt output belongs to `build-model-receipt`; ordinary
and other SDK profiles must exclude the new fixture classes and activities.
The same isolated `.modelvolumeverify` package is installed only on a separately
admitted fresh target. Existing held installations and data remain untouched.
The APK audit requires four exact nonexported fixed activities, no new service
or provider, unchanged capabilities, and the pinned SDK binaries/notices.

Use the existing create-only [environment helper](../runtime/android/RECEIPT_AVD_ENVIRONMENT.md)
with separate prepare/run admissions, fixed owned ports, installed image/tools,
12 GiB userdata and 8 GiB SD. Keep the original supervisor handle until explicit
stop and known terminal cleanup. No old AVD reuse, resize, clear, model copy,
download, privileged feature change or SDK invocation belongs to this cohort.

`benchmarks/receipt_setup_qualification.py` is disabled until an immutable final
proposal and its exact four-key authorization are supplied. Its fixed APK hash
map must first be frozen from the actual audited receipt build. The proposal
binds final sources, APKs, audit evidence, client binary and the environment's
live descriptor. The live lease checks process identity, start time, deadline,
pinned inputs and stop/result absence before and after every device client.
Serial, open port or a state file alone cannot establish ownership.

The fresh target must boot as API35/x86_64/4096-byte pages with no LocalLore
packages or processes. Require one mounted public volume, actual space above
the unchanged controller/userdata floors, and enough additional staging space
for both exact APK lengths. Install only the app/test pair, without replace,
then pin their actual distinct UIDs and APK hashes. The setup fixture separately
checks trusted Context roots and media admission. No Intent selects inputs.

Run one ordinary three-method instrumentation invocation for
`ReceiptSetupQualificationTest`: accepted import/recheck/recreation; Compose
Cancel before/after acceptance; disposed scope retaining a blocked source until
actual drain. Fixed callbacks use the production picker completion interface;
they do not exercise Android document-picker delivery. Require three exact
passes, six bounded regular proof files, and all 37 closed initial checks true.

Then observe the original APP target absent in the actual process inventory.
Only at this first post-initial observation, after the three exact passes, bind
at most one TEST-main PID/UID/name under the independently pinned TEST UID.
Record it separately as `test_helper`; it is not quiet, passive or an SDK owner.
The strict shared parser still rejects foreign rows, wrong UIDs, APP/service or
provider processes. Before initial instrumentation, both packages must have no
processes. Subsequent observations permit only the same helper row or its
natural disappearance. Disappearance permanently revokes that row; any new,
replaced or observably reappearing helper refuses. An initially absent helper cannot later
appear. Observation order, stage and instrumentation counts are exact, and a
classification failure is sticky. No process is stopped to obtain this result.
Version 2 facts contain separate `target` and `test_helper` rows. Matching the
observed PID/UID/name does not attest continuous liveness or detect unobserved
PID reuse between snapshots. The helper grants no file or runtime authority;
the APP restart proof independently requires its linked changed PID/start pair.

Only afterward run `ReceiptSetupRestartTest` in a separate ordinary
instrumentation invocation. Require one exact pass and two additional proof
files, all seven reopen checks true, unchanged UID/package and an actual new
PID/start pair linked to the original setup proof. Activity recreation alone
cannot satisfy this restart gate. Require source opens/closes 1/1, 2/2, 1/1 and
0/0 by phase; exact fixture identity; true direct-callback and candidate-root
absence flags; false SDK/native-publication flags; and retained capacity floors.

The closed command set permits only bootstrap observations, two exact installs,
two exact class selections and fixed bounded proof reads. No force-stop, clear,
uninstall, arbitrary shell, model transfer, old-root cleanup or AVD lifecycle
command is exposed. Final facts require the same APK hashes/UIDs/volume, no APP
target and the separately tracked TEST-helper row or its absence. Do not claim
all LocalLore processes are absent when that row survives. Real candidate roots
must remain absent throughout. The earlier all-quiet refusal remains recorded
in the [preceding verification](RECEIPT_SETUP_VERIFICATION_2026-10-24.md); this
correction requires another fresh admitted target and new evidence.

The outer owned worker has a 180-second budget; its cohort has 165 seconds,
boot at most 60, initial instrumentation at most 120, restart at most 60,
installs at most 35 each, other clients at most 15. All client budgets are also
capped by remaining cohort time. Raw bounded stdout is forced before parsing;
each command records status, return code, cleanup, byte counts and hashes.
Any unknown cleanup, owner loss or evidence persistence failure stops dispatch.
All namespaces/evidence are create-only. Emergency source/checkpoint timeouts
cannot count as successful cancellation drain. Proof inspection never opens a
live transaction's lock inode.

Pure mocked tests qualify controller rules only. Report actual failures and
all attempts; do not repair or repeat an installation silently. Successful
synthetic UI qualification still leaves real-model/cache/privacy, physical
phone, ARM64/16 KiB, sustained behavior and the existing A/#117/#119 gates open.

## Bounded failure observations

Only the explicit receipt debug fixture contains `ReceiptSetupFailureTrace`
and its related types. The receipt-only JVM source set tests this pure encoder;
APK audits require these classes in that profile and exclude them elsewhere.
No activity, permission, provider or service is added.

On a failed phase wait, the fixture makes at most one diagnostic emission
attempt per app process. It sends status1337 with the sole Bundle field
`locallore_receipt_failure_v1`, then rethrows the identical original failure.
This dedicated record avoids JUnit's repeated exception-message rendering.
Encoding/send failure consumes the sampling attempt and cannot suppress, wrap
or convert the original failure. The10-second wait and original pass gates stay
unchanged. No failure-time filesystem, native or SDK work is introduced.

The complete `INSTRUMENTATION_STATUS: locallore_receipt_failure_v1=` prefix plus
JSON is at most2,048 UTF-8 bytes, excluding the line terminator. Values are
closed ASCII case/phase/error/event enums, version1 and bounded integer/Boolean
observations. No Throwable text/class/stack/cause, path, URI, identity, file/model
or story content enters the payload. Error means the last observed typed
operation error, not the current ViewModel's cause or a diagnosis.

The per-Activity trace owns the newest16 event entries and copies snapshots.
Its total saturates explicitly at1,000,000 with a flag. Selected synthetic-source
opened/closed/active/read/returned-byte counters are independent observations;
read/byte counters saturate with explicit flags at that same bound. They are
not a jointly atomic resource state, accepted/persisted-byte count or runtime
admission. A recreated Activity has a new lifecycle trace while a retained
ViewModel can still invoke its original dependency closure's trace. That new
trace is not a complete retained-ViewModel operation/error history.

Host extraction accepts one adjacent exact status-field/status1337 pair, closed
keys/types/enums/counter bounds and at most16 events. Duplicate, malformed,
oversize, unknown or passing-run diagnostics refuse. Generic instrumentation
framing remains LF or consistent CRLF; the console-name-only CRCRLF exception
does not apply here. A finite trace may be saved before the unchanged strict
runner gate rejects the RAW failed transcript. It never satisfies three initial
passes, helper binding, restart, canonical acceptance or the44 proof checks.
