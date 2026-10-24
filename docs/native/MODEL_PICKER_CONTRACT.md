# Local model picker integration fixture

Refs [#9](https://github.com/OptimumAF/LocalLore/issues/9), M05.05 provisioning
prerequisite and M05.04 supporting. This packet builds on the unmerged
[model setup candidate](MODEL_PROVISIONING_CONTRACT.md). It changes no gameplay
authority, model selection, native publication operation or dependency.

## Shared setup wiring

`LocalModelSetupActivity` has one internal immutable construction seam:
`LocalModelSetupDependencies`. The normal implementation always supplies the
fixed `CandidateLocalModel` identity, IO-established private store, process
admission and paired play Activity. Neither Intent extras, document metadata,
URI, model text nor a saved state bundle can select a profile or expected hash.

The selected stream still enters through the same `OpenDocument` contract and
`ContentResolver.openInputStream` callback. The same ViewModel controls
admission, cancellation and UI state; the same store performs bounded hashing,
locking and native no-clobber publication. File/provider operations remain on
IO. The current Activity supplies the play action; a retained ViewModel stores
only the check/install/admission closures and no Activity reference.

The existing safe policy for an unrecognized late picker result remains:
a fresh controller does not import an old result without its pending selection.
It checks its private copy and asks for another selection if needed. Retained
Activity recreation keeps its pending controller. These are different cases;
ordinary recreation is not evidence of process death.

## Explicit synthetic profile

`localLoreModelPickerVerification=true` requires both
`localLoreModelSetupVerification=true` and `localLoreLiteRtVerification=true`.
The strict debug-only profile uses `org.locallore.app.modelpickerverify`, the
existing exclusive SDK project cache and a separate `build-model-picker`
output directory. Other profiles exclude its source and manifest overlays.
The ordinary and regular model-setup APK audits reject both the fixture
Activity and a leaked helper-only fixture identity in DEX.

The sole launcher remains the real fixed model setup. A non-exported
`ModelPickerFixtureActivity` is compiled only in the explicit fixture profile.
It inherits the picker, resolver, ViewModel and screen. Its immutable identity
describes 63 original ASCII bytes, SHA256
`648c91a9de82e613189b3920a2098f5d803eb6e244f39b2b631cce24b7be8de0`.
Its only root is `model-picker-fixture-v1` below its own canonical no-backup
directory, resolved on IO. Its play action always refuses and constructs no
inference owner. The first preparation requires that confined root absent;
the fixture performs no reset or recursive deletion.

This lets successful synthetic imports use production wiring without changing
the actual model identity or pretending that tiny data is a runnable model.
No weights, account, downloader, Internet permission or inference is added.

## Real document provider and ownership

The conditional TEST APK alone declares `ModelPickerDocumentsProvider` and its
control provider in one separate `:model_picker_provider` process. The document
provider retains the platform `MANAGE_DOCUMENTS` protection, explicit selected
URI grants and DocumentsUI discovery action. The control surface authenticates
the exact installed target/test UIDs before accepting a fixed operation.
It accepts no paths, filenames, model bytes, arbitrary commands or permissions.

Fixed synthetic documents contain valid bytes, same-length wrong bytes, a
controlled open failure or a blocked read. A bounded transaction token selects
only those virtual records. Reconfiguration refuses an active or failed owner;
stale controls are rejected. Public API-26 proxy descriptors report actual
`onRelease` callbacks. A separate authenticated control releases blocked reads.
Callback emergency deadlines are fixture failures, never cleanup evidence.

The integration tests observe actual local-only `OPEN_DOCUMENT` launches and
use the actual DocumentsUI root and result delivery. They do not mock the
ActivityResultRegistry, grant permissions through shell adoption, select a real
document or trust provider metadata as configuration. They check temporary read
grants, no persisted grant, exact safe failures, cancellation retaining the
slot, descriptor release, stage cleanup and a valid retry.

## Process-restart boundary and evidence

The preparation and readback methods must be selected in separate
instrumentation processes. Preparation preserves the tiny verified copy and a
bounded private PID/start receipt. The readback rejects the same process,
rehashes the private model and opens no provider. Raw process identifiers and
private paths remain local; only aggregate results belong in public reports.

Device execution requires a separate source/artifact-bound admission. Only the
new disposable fixture APP/TEST namespace may be stopped after terminal tests,
fresh signed-package/UID/process proof and zero active descriptor assertions.
The controller must observe process absence before selecting readback. Existing
31 packages, saves, models and caches remain outside that lifecycle scope.
No A or real-model operation follows from this fixture admission.

Official sources checked for this design: [Activity results](https://developer.android.com/training/basics/intents/result),
[proxy descriptors](https://developer.android.com/reference/android/os/storage/StorageManager#openProxyFileDescriptor(int,%20android.os.ProxyFileDescriptorCallback,%20android.os.Handler)),
and [descriptor release callbacks](https://developer.android.com/reference/android/os/ProxyFileDescriptorCallback).
Actual execution results and limitations belong in the dated verification,
device and independent-review reports. A passing synthetic picker flow cannot
qualify real model import performance, SDK cancellation, phone support, ARM64
execution, narrative quality or the full M05.05 exit gate.
