# Guarded archive UI harness

This host implementation adds one fixed, model-free Android test profile for
M10.02 and supporting M09.03/M09.05/M09.06/M10.03. It exercises the existing
archive-verification APK pair through the same bounded owner, storage admission
and binary client mechanisms as the model profiles. The
[dated verification](../../android/ARCHIVE_UI_HARNESS_VERIFICATION_2026-10-30.md)
records actual host/build results. Android execution remains pending.

## Fixed boundary

`benchmarks/owned_ui_contract.py` defines `owned-emulator-archive-ui-v1`,
`sdk-archive-ui-v1`, client version 6, and the archiveverify / archiveverify.test
packages. Admission data cannot select a package, contract, verifier or lease
implementation. Model material, run-as, model probes and arbitrary selectors
are excluded. SDK4/SDK5 defaults, model requirements and existing protocols stay
unchanged; this profile does not relabel an earlier session or restart receipt.

The exact ordered roster in `INSTRUMENTATIONS` contains ten methods:

| Group | Methods | Intended evidence when actually run |
| --- | ---: | --- |
| TranscriptFollowScreenTest | 4 | History position, tail visibility, composer position, stale branch callback |
| SystemThemeTest | 2 | Draft preservation and explicit cancellation callbacks across theme changes |
| ShellLayoutTest | 2 | Pending-response cancel callback and small viewport/double-font controls |
| PlayInputScreenTest | 2 | Scoped drafts, validation, duplicate submission, cancellation and disposal |

Eight methods use synthetic UI state. Two PlayInput methods use scripted
inference and the actual Rust engine when executed on Android. Their pending
cancellation is deliberately gated before native preparation; cancellation
while an actual provider is running needs separate evidence. No method uses a
real model or qualifies story quality.

## Build admission before native dispatch

From a physical D: checkout, set process-local TEMP/TMP/TMPDIR to
`D:\Dev\_Temp` and use the existing offline build environment and signing setup:

```powershell
python scripts/check.py android --archive-verification --offline
```

Capture that unchanged public runner with the finite owner and raw source/tool
bindings used by the repository's qualified build protocol. A plain console
transcript alone is insufficient. `archive_ui_build.PUBLIC_FILES` defines the
seven required records in its closed public-run directory. Then, from that
same clean, frozen checkout:

```powershell
python benchmarks/archive_ui_build.py --public-run D:\path\to\closed-run --output D:\path\to\ui-build-v1.json
```

This file/Git-only command does not start SDK tools, a service or a target. It
requires the exact current clean HEAD and raw source maps, pinned tools,
successful original public commands/audits, fresh critical Gradle task states,
345 unique JVM cases in 41 coherent XML reports with zero failures/errors/skips,
lint without Error/Fatal, matching package/signature/APK pins, and all ten
public annotated JUnit definitions in test DEX and absent from product DEX.
Repeated bare Gradle headings are allowed because warning grouping produces
them; every observed matching state must still indicate execution. Missing,
cached or up-to-date critical tasks refuse admission.

Keep the executed checkout frozen, including its original generated outputs.
Changing even its documentation invalidates the current-head binding. A later
documentation-only reporting commit belongs in a separate checkout. Copies and
source ZIPs preserve evidence but do not substitute new paths into the original
admission. `verify_current(admission)` also binds the two APKs to the admission's
artifact roles. Parent owner, worker and independent live observer each check
the build before their native operation. Lightweight per-client ownership,
source, identity and deadline guards remain active.

## Target execution requires separate admission

No guest is authorized by this guide or by creating a build manifest. Read the
current designated storage-controlled checkout and
[shared storage rules](RECEIPT_AVD_STORAGE.md) before any preparation. The fixed
future guest path is
`D:\Dev\Experiments\LocalLore\2026-10-30-archive-ui-v1\avd-v1`;
API35/x86_64, 8 GiB RAM, four cores and existing finite ownership/storage
constraints apply. Do not repurpose a previous guest, duplicate the registry,
or invoke SDK creation directly. Existing guest capacity and fresh owner
authorization are independent prerequisites.

The [read-only storage preflight](ARCHIVE_UI_STORAGE_PREFLIGHT_2026-10-30.md)
records the exact first-root candidate, preserved evidence and missing executor
boundary. It grants neither retirement nor a new guest run.

`owned_ui_owner.py` uses the existing owner CLI with its fixed profile.
After separately qualified admission/running bindings, the controller accepts
only those two records and their digests:

```powershell
python benchmarks/archive_ui_controller.py --admission D:\path\to\admission.json --admission-sha256 <digest> --running D:\path\to\running.json --running-sha256 <digest>
```

The controller creates only `controller-v1` below the admitted root. It checks
boot/API/ABI/user, initially absent packages, binary APK transfer and hashes,
installation, and installed UID/path/hash before and after the cohort. Each
fixed method is dispatched once. Bounded boot-readiness polling is separate
from test execution; there are no test retries. Raw failed attempts survive
parsing. Exit zero without the required JUnit start/pass/end evidence refuses.
Source drift or unknown cleanup cannot qualify a completed run.

`verify_controller_result(result_binding, admission_binding, running_binding,
expected_caller)` independently replays contiguous client/proof/claim/session
records and canonical evidence sidecars against an externally supplied caller
binding. It checks cleanup and all ten ordered parser results. Host fixtures
exercise this graph using simulated native/wire seams; they do not establish
target execution or feature acceptance.

## Compatibility and limits

No runtime, model, SDK or library dependency is introduced. Current official
[AndroidJUnitRunner documentation](https://developer.android.com/reference/androidx/test/runner/AndroidJUnitRunner)
supports the per-method `Class#method` selector. The existing binary wire uses
[AOSP shell v2](https://android.googlesource.com/platform/packages/modules/adb/+/refs/heads/main/docs/dev/services.md),
which supports separate output streams and exit status on API24 and later;
the fixed target is API35. These checks do not establish compatibility with a
physical phone. Touch, IME, TalkBack, process recreation, provider-running
cancellation, network privacy and real-model gates remain separate.
