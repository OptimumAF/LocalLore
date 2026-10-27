# Windows phone discovery — 2026-10-26

Refs #5 (M01.01/M01.05 supporting), #9 (M05.05 prerequisite), PR #186.
Host corrections are implemented and locally verified; physical-model admission
remains blocked. No milestone acceptance, installation or model result follows.

## Corrections

The previously authorized Samsung reappeared, but the controller refused before
any device query. This Windows ADB reports product, model, device and transport
ID without a USB path. A missing optional path now remains explicit `None`.
USB selection requires an independent, standalone host-server query:

```text
adb -H 127.0.0.1 -P 5037 -d get-serialno
```

Its serial must equal the prior authorized identity. The pinned server must
remain unchanged, and device enumeration before and after must contain the same
unique row and transport ID. No `-s` or `-t` may override this USB selector.
Subsequent device queries retain the exact transport ID; there is no automatic
rebinding or default-device fallback. USB battery power is a separate observation.

A second actual refusal exposed legitimate whitespace in unrelated process
names. Process rows now parse exactly two leading numeric columns and preserve
the remaining name. LocalLore's exact process names, UID association and colon
prefix refusals remain unchanged. No private process names were added to tests.

Official AOSP documents the [host USB selector](https://android.googlesource.com/platform/packages/modules/adb/+/HEAD/docs/dev/services.md),
[host-side serial query and transport binding](https://android.googlesource.com/platform/packages/modules/adb/+/HEAD/adb.cpp),
[optional device-path output](https://android.googlesource.com/platform/packages/modules/adb/+/HEAD/transport.cpp),
and [Windows USB registration without a path](https://android.googlesource.com/platform/packages/modules/adb/+/51ed3f3f38d8a48554587849dbac2c896d3f37db/client/usb_windows.cpp).
The actual installed-tool control below verifies this path; source inspection
alone does not establish behavior of every ADB version.

## Verification actually performed

With Python 3.14, from the phone-host worktree:

```text
python -B -m unittest scripts.tests.test_physical_model_probe scripts.tests.test_physical_model_contract -v
python -B -m unittest discover -s scripts/tests -p test_*.py
```

- Focused gate: **67 tests pass**, 2.864 seconds; owned 3,814 ms/0 with known
  cleanup and complete capture. Earlier USB-only correction passed 63 tests.
- Full gate: **1,191 tests pass**, 90.248 seconds; owned 92,079 ms/0, known
  cleanup/capture. The four changed input files and unchanged physical contract
  match before/after hashes. Production capacity checks are unchanged.
- The first full attempt ran 1,191 tests with one error: an existing consumed-
  claim unit test called real host-capacity admission before reaching its claim
  refusal. Its setup now mocks that observation and asserts admission precedes
  the actual create-only claim attempt; the consumed record stays unchanged and
  both SDK launch paths remain unused. Separate existing tests retain actual
  resource-refusal ordering coverage. This fixes test isolation, not capacity.
- An actual standalone USB control matched the prior authorized identity:
  six clean host clients, zero device calls, owned 10,883 ms/0 and unchanged
  source/identity bindings. No USB path was reported.
- Corrected actual discovery completed 74 bounded clients with known cleanup,
  owned 151,634 ms/worker 2, complete capture and unchanged sources. Readback of
  the retained metadata through the unchanged admission contract identifies only
  `memory_capacity`: **4,196,491,264 available bytes**, below the **4,294,967,296**
  initial margin by **98,476,032 bytes** (about 94 MiB).

The selected profile, primary user, package identities, storage, power and
thermal observations passed their preceding checks. The model gate remained
closed. This is one bounded snapshot, not a permanent phone-support verdict or
a new measurement from replaying retained metadata.

Both parser refusals and the initial full-test error remain retained. Private
serials, transport IDs, fingerprints, process lists and raw diagnostics stay
outside Git. No phone package was installed or updated, no model was copied or
loaded, and no app, emulator belonging to another project, or system setting
was changed for these phone checks.

Android/Rust/Gradle/manifest/dependency sources are unchanged from `fc0e8a5b`.
The prior [488-JVM/build/paired-APK evidence](PHYSICAL_MODEL_HARNESS_VERIFICATION_2026-10-25.md)
remains dated evidence; it was not rerun or relabeled as phone execution.
Next phone work requires a meaningfully fresh capacity state and complete fresh
admission, followed by the isolated precheck before any model transfer.
