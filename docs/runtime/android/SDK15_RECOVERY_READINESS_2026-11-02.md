# SDK15 source-bound recovery input inspection

Refs #14 (M10.02), supporting #13 (M09.06). Supporting implementation is in
review; full criteria remain unchecked. This is a working file-only inspection
tool, not guest recovery, an execution grant or Android qualification.

## Fixed scope

`scripts/freeze_library_ui_recovery_inputs.py inspect` uses the operational
checkout `D:/Worktrees/locallore-record-actions-tests-v1`, frozen at PR #352's
`18809566af72530408e2e25007ee4d501e6bf12a`. The tool itself is developed in
`D:/Worktrees/LocalLore-record-query2-tests-v1`; that separate location keeps
the operational source paths/bytes intact. Importing the tool performs no I/O.
Only the literal `inspect` command is accepted; no root, registry, model,
profile, executable or authority can be selected by arguments.

The tool checks the frozen clean Git head before importing its modules, requires
their actual source location, validates all 25 SDK15 source pins and four fixed
selectors, and verifies the existing exact B81 manifest/B80 APK pair. It checks
installed tool-file hashes from preserved metadata; it does not execute those
tools or repeat version/compatibility/performance tests. No dependency changes
or downloads are introduced.

The credential path remains metadata only: its file is never opened, statted,
hashed or copied. The native ADB refuser's source path is rebound to the current
checkout only after its bytes/hash match the preserved compiled-helper source.
No credential permission or global SDK/ADB setting changes.

The current recovery planner reads the unchanged production registry and original
mkdir-failure evidence. Its existing eligibility checks remain authoritative:
same absent root, preparing/full reservation, preserved old proposal/source,
one missing parent, no spent recovery claim. It emits a plan bound to the seven
current operational source files. It does not create a registry lock, migrate
the ledger, reserve another root, establish historical process closure or run
the SDK.

Output is create-only under
`D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1/frozen-inputs-v1`:

- `b80-byte-attestation-v1.json`: verified inspection copy of manifest data.
- `recovery-plan-v1.json`: source-bound file-only plan from the existing planner.
- `static-installed-inputs-v1.json`: installed-file pins and credential path.
- `handoff-inputs-v1.json`: fixed profile, limits, pins and explicit pending gates.
- `result-v1.json`: completed inspection record, always unready for execution.

Each generated record is read back equal to its validated in-memory value and
its pin is rechecked before/after the final result. The tool also rechecks
original ledger/source/tool/artifact/helper pins after planning. A partial or
changed set refuses and remains preserved; no overwrite, rollback or automatic
retry occurs. These are bounded snapshots, not simultaneous filesystem ownership
or protection against an administrator rewriting all evidence. Future execution
must revalidate the records and its independent gates.

## Verification actually performed

Final executable/test source is
`53e30bfd842203676cf7c79fa73edf2c21c50ba7`; later publication changes are docs only.
Windows / installed CPython 3.14.7, with process-local `TEMP`, `TMP`, `TMPDIR`
all `D:/Dev/_Temp`. Project commands ran from their physical D: working directory.
Central jobs use the existing Windows job supervisor, stdin barrier, 300-second
ceiling and bounded binary capture. All observed jobs have known cleanup,
complete capture and unchanged monitored inputs.

Private OUT is `D:/Dev/Experiments/LocalLore/2026-11-02-library-recovery-readiness-v1`.
Commands below use OUT as an abbreviation, not a shell variable:

| Actual command | Recorded outcome |
| --- | --- |
| `python -I -S -B OUT/run-host-v1.py tests host-tests-v1` | Initial 16 tests pass, 26.506 s, at `2379b796` |
| `python -I -S -B OUT/run-host-v1.py inspect frozen-inspection-v1` | Real inspection refuses before output-directory creation, 311 ms |
| `python -I -S -B OUT/diagnose-fixed-pins-v1.py` | Read-only diagnosis: all three real files match expected bytes/hash; path spelling alone differs |
| `python -I -S -B OUT/run-host-v1.py tests host-tests-first-v1` | Same new 17-case suite at `37aca784`: three AssertionError subtest failures, no errors/skips |
| `python -I -S -B OUT/run-host-v1.py tests host-tests-green-v1` | Unchanged 17-case suite at `53e30bfd`: pass, 52.432 s, no failures/errors/skips |
| `python -I -S -B OUT/run-host-v1.py inspect frozen-inspection-v2` | Unmocked file-only inspection passes, 4,098 ms |

The first genuine refusal exposed a gap in the original fixtures: all their
synthetic pins were already canonical Windows strings, while three fixed real
constants used forward slashes. The existing strict binding reader compares
the whole canonical binding, including its path string. The correction applies
`str(Path(...))` only to those three trusted constants. Hashes/byte sizes and
strict rejection of arbitrary noncanonical caller metadata stay unchanged.
The independent regression reproduces all three failures before that fix.

Original refusal stdout: 170 bytes, SHA256
`4ea7d6bd9c4dd3eed2f367b74653540b3605341f55ee1788ab517c4996491de8`.
FIRST stderr: 12,106 bytes, SHA256
`3f43f51e14c8537f8268fe0f6593dd1f34d326301798d082d9c37eae3b543d4e`.
Final GREEN stderr: 4,150 bytes, SHA256
`cfb1963fbfdf967c88917884e56e0c4dbc8fcad242f19312c741b02ab887048e`.
The unchanged test file is 27,791 bytes, SHA256
`7f6920d7a36da6f78c15e4cbf2fb208fb6834d585c557e7c19713e580be8588d`.

The tests use tiny real D: files and the unchanged binding/JSON reader. Frozen
Git/build/planning observations are explicitly simulated; execution, resource,
ledger-write and credential-file operations have tripwires. The genuine
inspection separately uses the actual frozen source, installed file pins,
build byte verifier, production ledger read and recovery planner without mocks.
No earlier B81 host/Android/Rust/Gradle/JVM suite was rerun or promoted.

Python 3.9 grammar checks pass for the two new Python files; whitespace checks
pass. Independent source/file-evidence review found no concrete blocker, while
retaining the original refusal and FIRST failures. This is model-assisted
review, not execution approval or owner acceptance.

Selected evidence is copied additively to
`D:/Dev/Recovery/LocalLore/2026-11-02-library-recovery-readiness-v1`:
37 current source/control pairs, 148,511 bytes, plus the seven original
refusal copies retained separately. The 23,728-byte primary receipt has SHA256
`6dde90180dd55096b623683064041cb260db3dd22ec6f8e8fc461f4cb7d0c509`.
The old failed helper copy intentionally differs from current corrected code;
its historical bytes remain intact. Synthetic fixtures remain in their original
bounded directory and are not claimed as full recovery copies. Final publication
documents/reviews are preserved separately after commit; no private outputs
or credentials are uploaded.

## Actual inspection and remaining execution prerequisites

The new recovery plan is 2,609 bytes, SHA256
`0b4de12259218f1eb735eb366a4ff955b0f2cf6c6481c3143d90f96544a0afd2`.
All seven source paths point to the frozen SDK15 checkout. Its parent mode is
`create_one`; the old entry remains preparing with 42,949,672,960 bytes charged.
The handoff is 8,214 bytes, SHA256
`b94367b9a70e194138a03528e6971c8be1e66d25551021f9140f1fb115a03475`.
Both records retain explicit pending authority and readiness gates.

The original build role stays the B81 30,730-byte manifest, SHA256
`496f6358a860c2f5ff8809610d0d2f83e93dd867fbfdfe5e6c4c551871058ad3`.
The separate compact 25,326-byte inspection copy is not substituted for that
artifact role and does not reseal the original manifest or baseline.

The production ledger remains 41,230 bytes, SHA256
`4917ec696f7c9f9de5917838aafbd9c2d11184e17c8cbecd71f4eb66ae6a58c5`.
Guest, immediate parent, runtime and activation controls remain absent. No
authority, fresh prepare/RUN proposal, admission or activation input was created.
No resource/process observation, SDK/ADB/phone/model action, recovery/migration,
guest boot/stop, image deletion, setting change or merge occurred. Current
Android remains 0/4; B77's earlier grant stays spent. The other emulator is
outside this work's lifecycle actions.

The old B77 direct operator stops after guarded preparation. It cannot create
the current SDK15 run inputs or dispatch this cohort. **Next runnable task:**
implement and test the bounded post-recovery handoff/operator against these
frozen inputs, creating fresh run bindings only after verified successful
recovery. Then freeze/review the exact operation and obtain fresh scope-specific
authority before any migration/SDK preparation/boot. Do not transfer Flow5907's
old plan, infer authority from this inspection, or fabricate preparation results
while the guest is absent. Physical/ARM64/model/accessibility/full milestone
acceptance remain separate gates.
