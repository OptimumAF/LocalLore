# Cancellation acknowledgement review, 2026-10-23

Refs #9, M05.04 and supporting M04.04, claim `6376529313`. The frozen nine-method fixture reproduced four failures on baseline B and passed all nine after the coordinator's correction. No remaining concrete source blocker was found in this bounded protocol change. I authored the tests and report and independently reviewed source and retained evidence; the coordinator performed all builds, tests and device actions. This is not independent execution or milestone acceptance.

## Finding and correction

At exact baseline `b90ddc9c0ed955c034a6c1f9e331caf3323e4e9a`, `cancelSaved` and session release cleared pending work for any successful cancel reply whose phase was not `committed`, bypassing the existing turn/scope/expected-revision decoder. Cancelled recovery used that decoder but permitted `ready` to continue into snapshot recovery. An unrelated or unfinished reply cannot establish cancellation disposition.

Production commit `8b30155a2132ef59a4f69d2089e41eb9332475d0` adds one shared cancellation-acknowledgement helper: require `committed`, `cancelled`, `failed` or `stale`, then use the existing complete original-binding/receipt decoder before releasing the recovery key. Invalid acknowledgements throw while retaining the cancelled original key. Explicit UnknownTurn and release-only Closed retain their previous treatment. No native or wire change was introduced.

## Frozen fixture

Test commit `b6e3b0842393c2708b4a41e475bdc0a53b9d7363` adds only `apps/android/app/src/androidTest/java/org/locallore/app/CancelAcknowledgementTest.kt`. Its nine AndroidJUnit4 methods use actual `DurableGateway` and Android JSON through a synthetic `WorkspaceTransport`, without Context, Activity, native workspace, database, file or model access. Ordinary JVM JSON stubs could not establish these behaviors, so the test was reassigned to instrumentation without a shim or dependency. Runner selection is `-e class org.locallore.app.CancelAcknowledgementTest`; no custom arguments.

Four entrypoints exercise the three implementation paths: direct cancel, release before create, release before resume, and already-cancelled recovery. Cases cover foreign or missing identity/head/phase fields, queued/running/ready/unknown phases, malformed committed receipts, matching terminal outcomes, committed races, UnknownTurn and Closed's restricted disposition. A bad acknowledgement must preserve the original request/key, fence an old Prepared handle and permit only cancellation retry for the same session/scope/turn. No new submit, prepare, commit, snapshot or replacement session may conceal the failure. The cancel command itself has no request field; the fixture binds its key to the recorded original submit instead of inventing a new wire requirement.

The test source SHA-256 is `eb84c0a579dcbbf63baca901c318f95baa3c3c7653365a92e5aa9d00ff4053c4`, independently equal in my frozen checkout and the coordinator's candidate checkout.

## Actual evidence readback

| B observation | Passed | Failed | Retained instrumentation stdout SHA-256 |
| --- | ---: | ---: | --- |
| Unchanged baseline gateway | 5 | 4 | `42e8c236658f718b5b9c659d1904ce46e5cf1f8b4d9744ed345d8bd66ff50455` |
| Corrected gateway | 9 | 0 | `66dde76c25e87ebac36726c811e21cd8d608840abfff915d668c23ac52d5293c` |

I inspected both raw transcripts: each has exactly nine paired starts/terminals and the final runner code. Baseline failures were direct cancellation and both release entrypoints accepting a foreign turn, plus cancelled recovery accepting `ready`. Malformed committed receipts already passed baseline. Candidate stdout is 6,479 bytes; its owner completed in 11,016 ms with child exit zero and known cleanup. Across both completed cohorts, all 83 command stdout sizes/hashes matched their records, with completed/zero-exit/known-cleanup metadata throughout. These are 18 JUnit invocations, not separately counted loop subcases.

Baseline app SHA-256 was `c75741d371b39067de2bf1c0ecb290f3d688ace78437183c9771f7c65f1cda6b`; candidate app was `342d71e5d68913af1ec16f3f4789723f082739e4836b101b716d78906f36a1cd`. Test APK remained exactly `43cecd946901b002a9056ec2522d8255ff66f94785660055aa775637ade9c147`. Candidate's initial map equals baseline's final map; candidate installed/final maps match. Only the isolated app hash changed; the test APK and 23 prior B package identities remained equal.

The [safe aggregate](ANDROID_CANCEL_ACK_RESULTS_2026-10-23.json) independently read back as 6,029 bytes, SHA-256 `6a1d6605c76c50b7a6644137946b331828800ea00734bdca39185f861d506e31`; its outcomes, source/test/artifact bindings and B-only limits agree with the inspected records. All 207 entries in the final device seal independently matched their sizes/hashes, totaling 274,928 bytes. Its 35,300-byte index SHA-256 is `7ce760cb00ed570a22298ceabe9c920d08ca03558da607c4b20f565e5432c508`. These readbacks verify retained evidence; they do not rerun its tests or certify every build output.

## Harness findings, retained stops and limits

Before execution I identified a repeated literal `/data` mount-alias refusal and a parser that accepted the final runner marker before the test records. The corrected harness requires fixed-path `stat -L` device agreement for the allowed mount aliases, exact LF/uniform CRLF framing, all nine paired terminals before runner completion, and no later instrumentation records. Its raw-first retention and sticky unknown-ownership fences remain intact; an application process remaining after instrumentation stops collection without force-stop. The final retained private host log records 20 passing mock tests; I reviewed it without running it.

Three earlier cohorts stopped without test invocations: missing selected emulators; A below the unchanged storage floor; and an overly narrow parser rejecting the successful app install's `Performing Push Install` prefix. That last cohort installed only the app. A fresh, reviewed namespace required that exact pinned partial state, installed only the missing test APK for baseline, and retained the earlier failure. No test assertion or storage floor was relaxed. A's observed 1,045,565,440 bytes did not meet the 1,207,959,552-byte floor; qualification is B only.

This exercises Android client protocol handling with synthetic transport. It does not qualify product JNI, SQLite cancellation, native workers, canonical replay, process death, model ownership, ARM execution or physical phones. Build compatibility and source review do not supply those missing observations. Full milestone completion and owner acceptance remain separate.
