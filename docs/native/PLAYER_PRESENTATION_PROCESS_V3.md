# Player presentation process proof V3

B43. Refs #14 (M10.02), #13 (M09.06), #307 (supporting M09.04).
This opt-in model-free debug proof observes the actual Rust-backed app; it
changes no gameplay, canonical storage, inference or cancellation authority.
Implementation/host checks, compilation and actual target execution are separate.

The legacy product probe, controller and host readers retain their bytes and
V1/V2 contracts. `play_presentation_v2` remains unknown (`other`) in that legacy
probe. It is never aliased to `play_snapshot` or ignored as metadata. Old runtime
evidence cannot qualify the new family or arbitrary later source/APKs.

## Installation and observations

`localLorePresentationProcessVerification=true` requires the input-draft flag,
excludes the old input-process flag, uses `.gradle-presentation-process` and
`build-presentation-process`, and refuses release tasks. Product identity is
`org.locallore.app.presentationprocessverify`; the separate controller is
`org.locallore.app.presentationprocesscontroller`. Ordinary, archive and old
process installations remain distinct. No new runtime/library dependency.

The new controller accepts exactly `case=restore_player_presentation`, hex16
`run_id`, and hex64 `product_sha256`. Only a fresh create-only fixture is
permitted: no reuse/cohort, arbitrary package/path/command or helper/retirement
lane. It verifies actual package/UID/signature/APK identity before acting.
The fixed 120-second case and all existing bounded shell/node/save/death fences
apply. A saved acknowledgement after `super.onSaveInstanceState` is required;
STOPPED alone does not establish a saved task. Two known process deaths must
restore the same task into three distinct process identities, each one factory.

The new product writes only `created.json`, `saved.json`, `commands.json` under
`no_backup/process-verify-v3/RUN`. Each is at most4096 UTF-8 bytes, with the exact
14-field legacy record shape, integer `version=3`, and
`scope=locallore_presentation_process_verify_v3`. The operations are the old14
plus a distinct `play_presentation_v2` counter. Counts are attempted dispatches,
not canonical success; unknown names increment only `other`, never leak text.
Run IDs, saved state and observer selection cannot be enabled by story content.
Factory bounds16, operation bounds4096, write sequence bounds65536 and the
fixed hint digest `SHA256(UTF8("1\nSTORY\nBRANCH\n"))` remain. Invalid config
disables routing; one process cannot change runs or reset its lifetime counters.

## Closed controller result and offline reader

The quiet instrumentation result frame is at most32768 bytes, with one
`INSTRUMENTATION_RESULT: proof=JSON` line and `INSTRUMENTATION_CODE: -1`.
Uniform LF or CRLF framing is accepted; chatter and concatenated results refuse.
The JSON has version3,
`scope=locallore_presentation_process_controller_v3`, fixed case above.
It has exactly the old root controller common fields plus `presentation_reads`:
`version, scope, case, run_id, status, stage, reason, checks, process_deaths,
last_workspace_read, last_workspace_utf16_length, controller, observations,
terminal_observations, fixture, presentation_reads`. Success requires
passed/DONE/NONE, two deaths, three distinct PIDs and strictly increasing starts,
same task, factory1, restored false/true/true, and different controller PID/UID.
`checks` is a positive bounded diagnostic count, never an invented gold.

Fixture version3/scope `locallore_presentation_process_fixture_v3` has exactly
`version, scope, case, controller_uid, product_uid, signature_sha256,
origin_run_id, origin_product_sha256, stories`. Two ordered distinct original
root scopes start at head0; the nondefault second story is restored. One
explicit Send commits once there; the first remains unchanged. Native reads
must confirm original input/accepted receipt/head after reopen, with no auto turn.

The six gameplay counters stay `free_text, submit, prepare, commit, cancel,
other`. First terminal vectors are all0; second are `(1,0,1,1,0,0)`.
Creation counters `{create,create_named}` are `{0,2}` then `{0,0}`; final
process counters are all0. Both terminal records contain exact identity,
saved/commands sequence, gameplay, creation and read vectors. Read vectors have
exact `resume, play_presentation_v2, play_snapshot`: terminal/saved/commands
first two positive, last0. The immediate created receipt may precede initial
asynchronous IO and have zero reads; later bound witnesses establish progress.
Saved and commands sequences must differ; a read-only call may finish after
the save. Read vectors must be monotonic in their actual sequence order while
gameplay/creation stay identical.

Two `presentation_reads` witnesses bind the restored process identities and
exact `pid,start,task,before_sequence,after_sequence,resume_before,resume_after,
presentation_before,presentation_after,legacy_before,legacy_after,before_game,
after_game,before_creation,after_creation`. Sequence/resume/presentation each
increase; legacy stays0, gameplay/creation stay0. The second terminal follows
the first witness strictly after the explicit Send, and final third-process
probes bracket/join the second. Counters cannot decrease between a raw probe
and a witness. Equal sequence numbers identify the same write and require
equal read vectors, preventing conflicting snapshots of one observation.

`benchmarks.android_presentation_process_evidence` exposes
`validate_probe(raw,expected,leaf)` and
`validate_result(raw,expected,product_records)`. Expected is exactly
`run_id,product_uid,controller_uid,product_sha256,signature_sha256`.
`product_records` is exactly three original bytes leaves `created,saved,commands`:
third-process created/commands and second-process saved. Strict UTF-8/duplicate
key/schema/types/ranges/run/identity/hint/counter/terminal joins reject mixed
versions, missing/extra fields and booleans disguised as integers. A fixed
`PresentationEvidenceRefused("presentation_evidence_refused")` echoes no input.

These receipts are observations, not independent authentication. A caller must
separately bind source/build/APK, concrete invocation, SDK/ownership and raw
capture, bounded completion and cleanup. Offline synthetic fixtures or a built
controller do not establish actual process death, model/physical/ARM64 support,
privacy/accessibility, storage-loss durability or release acceptance. No target
execution or new boot/retirement authority is granted by this contract.

## Reproducible host and build checks

From the physical D: checkout, with process-local TEMP/TMP on D: and the existing
installed Java/Android/Rust toolchains and D: Gradle cache:

```powershell
python -B -m unittest scripts.tests.test_android_presentation_process_evidence scripts.tests.test_presentation_process_build -v
python -I -S -B scripts/check.py android --presentation-process-verification --offline
```

The public Android command compiles both JNI architectures, the product and
instrumentation APKs, all JVM tests and the separate controller; runs product
and controller lint; then audits product capabilities/alignment, the product/test
pair and signer, and the self-targeted controller's one-package query boundary.
It never installs an APK, discovers a target, starts ADB, boots a guest, or runs
the controller. Ordinary and archive command plans keep their existing defaults.
Record actual results and source/APK hashes separately from this specification.
