# Android system chooser archive proof

M08.06 bounded follow-up to the Android archive and platform roundtrip proofs.
This packet exercises the real MainActivity callbacks and Android DocumentsUI,
with the unchanged shared archive v1 validator and seven-call NativeArchive.
The native engine remains the only gameplay and import authority.

## Test boundary

Only the instrumentation APK contains ChooserArchiveProvider. It is a genuine
DocumentsProvider in a separate process, protected by MANAGE_DOCUMENTS with
temporary URI grants. The application receives no storage permission or provider.
The fixed root is `LocalLore test archives`; its authority is the instrumentation
package plus `.chooser`. A separate `.control` test authority has only bounded
configure/stats calls, restricted to the exact target/test UID before dispatch.
It delegates to the protected provider under its own process identity and never
grants document access. The product I/O
uses the actual URI returned by the system picker, without adopted permissions.

The provider retains fresh, synthetic run directories and create-new outputs.
Source titles and document IDs are test constants, never filesystem paths from
archives or UI titles. Configuration supplies at most 128 KiB per original
synthetic archive; the product's existing 32 MiB archive limit stays unchanged.
No user files, models, default workspace resets, or preexisting destinations are
used. Actual imported test stories remain in the isolated verification app;
each run obtains a new engine-allocated story ID instead of overwriting history.

## Checks

The tests navigate DocumentsUI using framework accessibility APIs, checking the
foreground package and semantic nodes before acting. MainActivity launches its
registered GetContent/CreateDocument contracts. Import requests one openable
content copy through `*/*` with the exact JSON, octet-stream and plain-text MIME
filters; it does not request source write, persistable or prefix access. Import
must produce a native
preview without adding a story before the explicit confirmation. Successful
import offers an explicit fresh session; replay, continuation and duplicate
resource rejection are checked against real Rust outcomes. Export captures the
native preview before the system creates a fresh document and the returned URI
is written; captured native bytes and provider bytes must match.

Selected future-version, malformed and same-ID archives must fail safely and
leave accepted state and prior library entries intact. Error/cancel controls
must recover. Existing descriptor, cancellation, recreation and process-owner
tests remain relevant; picker success alone does not establish those gates.

## Sources and limits

The current official [DocumentsProvider guide](https://developer.android.com/guide/topics/providers/create-document-provider)
requires an exported, grant-capable provider protected by MANAGE_DOCUMENTS and a
DOCUMENTS_PROVIDER intent filter. Its [API contract](https://developer.android.com/reference/android/provider/DocumentsProvider)
describes system-issued document grants. No dependency or runtime pin changes.
The [OpenDocument contract](https://developer.android.com/reference/android/content/Intent#ACTION_OPEN_DOCUMENT)
includes read/write document grants. The app consumes one bounded copy, so its
import uses [GetContent](https://developer.android.com/reference/androidx/activity/result/contract/ActivityResultContracts.GetContent)
instead. Earlier dated reports retain their original OpenDocument attribution;
the fixed tests still require the selected source URI's WRITE grant to be denied.
Custom call permission checks belong to the provider, as documented by
[ContentProvider.call](https://developer.android.com/reference/android/content/ContentProvider#call(java.lang.String,%20java.lang.String,%20android.os.Bundle)).

These are synthetic API35/x86_64 emulator checks. They cannot qualify physical
phones, ARM64 execution, hostile providers, cloud synchronization, real-model
quality, production disk exhaustion, process death or full M08 acceptance.
Private raw observations and app data stay outside Git. Published evidence must
distinguish each attempt and exact artifact identity; never infer byte-identical
builds or successful picker I/O from a launched Activity alone.
