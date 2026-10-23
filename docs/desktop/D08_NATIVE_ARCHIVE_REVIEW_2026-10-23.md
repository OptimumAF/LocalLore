# D08 desktop playable archive caller review — 2026-10-23

Reviewed source `1d088329f3fafbd1a91ae8a182889b312edc7e96` in isolated
`review/d08-native-archive` / `source-archive-ui-review`.
Reviewer `/root/app_storage_review`; #30 claim 6367086631. Sole authored path is
this new report. Production source remained unchanged.

This is an independent review of the desktop adapter, controller and rendering
boundary for D08.01/.02/.03/.07 partial, plus the desktop prerequisite for .06.
The reviewer authored shared archive/fork and pinned staging Store code. Those
are dependencies, **not independently reviewed or self-approved here**. No branch
switching/rewind UI (.04), author corrections (.05), bidirectional desktop/Android
chooser loop, full D08 acceptance or release is established by this report.

## Findings and authority

No additional substantive blocker was found in the reviewed desktop caller and
controller source. This conclusion is bounded to the paths and checks below;
it is not a security certification or owner acceptance.

The normal IPC commands accept fixed session/scope/head, opaque UUID preview
tokens, explicit consent booleans and exact numeric operation identities. They
accept no renderer-selected filesystem path, archive bytes, SQL, model, command
or arbitrary format/mode. Both transfer confirmation commands refuse absent
consent before scheduling work. Import source and export destination are selected
by native dialogs; fixed development picker replacements enter the same
post-selection operations. A renderer consent boolean is a trusted local UI
boundary, not proof against a compromised renderer or OS.

Export first uses the existing Host Full inspection permission/session/scope/head
check, then independently captures a coherent Store archive and checks the
selected branch head in that snapshot. The authorization inspection bundle is
discarded; it never becomes the playable archive format. Further accepted play
does not rewrite an already captured export. Full private whole-story scope is
explicit, even when the selected session is one branch. Import never treats an
inspection snapshot as a playable archive or loads a referenced model.

`Data::Export` and `Data::Import` are native-only variants. Import retains both
the exact selected bytes and a shared opaque `ValidatedArchive`. Preview title,
identity, branch heads, size and checksum are derived from that captured object.
Confirm removes one native token and enforces its data variant: an import token
cannot be exported as if it were an export token. Later edits to the selected
file cannot change those captured bytes. Two preview capabilities per broker and
one active worker are explicit bounds; these are not whole-process heap limits.

Tokens carry their window epoch and expire for confirmation 600 seconds after
creation. `take` checks that fixed creation time, rather than extending it on
read. Expired bytes are pruned on later preview admission or window teardown;
there is no background ten-minute erasure timer. The corrected controller label
accurately describes capability expiry, not secure erasure or bounded RSS.

## Lifecycle, transaction and failure boundaries

`WindowLease::capture` admits only the current native `main-<epoch>` window.
Synchronous destruction invalidates the epoch before scheduling cleanup. Broker
admission holds the registration mutex through handle registration. The worker
waits on a start channel until its join handle is stored, then checks the lease
and cancellation flag. Thus drain cannot miss a worker admitted just before
destruction. Previous finished workers are joined before another is admitted;
the broker does not spawn an unbounded backlog. Retire is best effort under a
busy broker mutex, but lease invalidation independently makes `Work::cancelled`
true; drain joins the exact old-epoch worker and removes its preview tokens.

Existing source tests exercise spawn failure, caught worker panic, destruction
between admission and registration, old-window retirement and fresh-window
admission. They were read, not rerun by this reviewer. A native picker can remain
open until the user cancels its dialog; drain waits for that worker and reopening
waits for cleanup. The panel says native picker cancellation uses the dialog.
No claim of forcibly terminating a noncooperative native dialog is justified.

Before destination import, the adapter validates/replays the bytes in a new
private staging Store, checks the resumed root head and closes that Store. It
requires cleanup of the exact staging filenames before proceeding. It then
consumes the original validated token into the actual application Store through
the shared transactional importer. Existing story identity remains Conflict;
there is no silent overwrite, remap or merge. Imported stories are saved but
opened only through a separate explicit resume action. Old pending operation
identities/status and model selection are not restored.

The caller now invokes `Store::create_new_pinned`, retaining the ancestor chain
while the staging constructor holds its main/sidecar reservations. This is the
correct adoption point for the separately authored shared correction. It is a
disposable MEMORY-journal staging Store, not the durable destination. The known
native planted-journal regression remains in source. This report neither
repeats that attack nor independently qualifies the shared constructor.

Cancellation is cooperative through validation, staging and destination import.
A transaction already past its cancellation checks can commit before a later
cancel/close wins; cancellation is not rollback of a completed import. The UI
states that a committed transaction wins and directs users to the final result.
Lost acknowledgement is not converted into import success or automatic retry.
The explicit library refresh recovers a committed identity, and another import
of that identity conflicts. Unknown acknowledgement therefore remains distinct
from a guaranteed failed transaction.

Export writes one new bounded partial file, checks cancellation while writing,
syncs it, then uses the existing handle-based nonoverwrite finalizer under the
lease gate. On failure the caller reports exact partial cleanup status. Staging
cleanup is limited to four known filenames and one new directory, without
recursive traversal. Failure cleanup does not promise forensic erasure or removal
of external copies; the panel explicitly warns about retained staging files,
selected exports and OS backups. Shared-filesystem same-user tampering and
process-death/disk-full qualification are not established by a source review.

## Renderer privacy and decoding

The main controller synchronously notifies archive context changes before React
renders a new selected session/view/observer. Context change/hide/dispose rotates
the archive epoch, clears preview/result/consent and attempts exact token discard
and operation cancellation. A delayed initial preview result is discarded; a
delayed poll cannot install a preview into the new context. Old cancellation
failure cannot overwrite a newer preview. `ArchivePanel` also checks the current
context and Lab view before rendering, closing the intermediate-render gap.

The decoder bounds UUIDs, IDs, branch count, revisions, turn count, byte count,
hashes, title and warning lengths; terminal/running phase combinations are
checked. Imported outcomes require no pending-workflow resume, no model load and
successful staging cleanup. Confirmed import identity and exported checksum are
compared with the reviewed preview before showing success. The decoder validates
the fixed native contract; it does not independently authenticate archive origin.

Untrusted titles/warnings and paths are React text. No raw HTML insertion or
archive-provided URL/script execution was found. The panel distinguishes full
private playable archives from D03 inspection, states hidden facts/every branch,
lists excluded private traces/caches/weights/workflow state, and requires a fresh
checkbox after each preview. Play/context changes suppress private preview
rendering. This UI lens is not a separate native principal; native Full authority
still comes from trusted Host construction, not a renderer observer string.

Normal frontend compilation defines `__DEV_HARNESS__=false`; archive journeys
are behind that static branch and the existing verifier scans for their markers.
Native fixed picker state, fault switches and harness command handler are
`dev-harness`/test gated. Tauri's manifest lists harness permission names in the
normal configuration, but the normal invoke handler has no corresponding harness
implementation. Permissions alone do not install a command. This was checked in
source; no normal native binary or frontend hook scan was executed here.

## Reviewer execution and attribution

One bounded existing test was executed against these actual controller/model/
React sources, using native doubles (no dialog, application or model process):

```text
Node v24.19.0 (existing bundled runtime, not a latest/security qualification)
node check-archive-controller.mjs
PASS: actual archive controller stale-context/consent and strict private metadata
fences; inert React preview with explicit staging/conflict/exclusion labels.
git diff --check
PASS
```

Dependencies were read through an ignored junction in this isolated checkout to
the task's existing desktop dependencies. Generated test bundle was written only
to task-local `d08-archive-review-checks`; log `d08-archive-review-controller.log`.
The script covers a held initial preview across Lab→Play/story change, held poll
and rejected old cancellation across contexts, wrong imported identity, unchecked
consent, malformed metadata and inert rendering of hostile title text. These are
controlled JavaScript/native doubles, not end-to-end native IPC evidence.

The reviewer did not run Rust/native tests, build or launch an app, operate a
dialog/CUA/device/model, or inspect protected resources. Coordinator-reported
corrected native44+contracts2 and earlier62-assertion/17-image/5-launch journey
results are separate execution evidence. The final `1d08832` journey rerun was
pending at assignment; no final63 result is invented here. Source inspection
confirms that its pending-cancellation capture now checks an actually running
`importing` operation before requesting cancellation, rather than labeling a
post-cancel snapshot as pending.

## Frozen reviewed bytes

SHA-256, paths under `apps/desktop/`:

| Path | SHA-256 |
| --- | --- |
| src-tauri/src/archive.rs | `86126101e9923a4ed7536bf2ac59566cc48cea43d291d0ad1b3c1db7f411f881` |
| src-tauri/src/archive_commands.rs | `0581739284016bde929ae47b7b48ed08f6bc64939ef9159e0cc633280b800e8d` |
| src-tauri/src/main.rs | `f9681ef88ed1421a6f23c6d734fc143068857a5a7fe73a79339bf8fd71a0b59b` |
| src-tauri/src/lease.rs | `b7a919127c7244622abf3cb7cf59a0f4c550af85bafab234b35602c55df44e55` |
| ui/archive-controller.ts | `9fe0606679fceb33a0940d78c027fb614d2482b54eb4bf2fae464731968a6c39` |
| ui/archive-model.ts | `284451ef5ff9a85f60595a1ce844d073f64ad7d4ae916fe9757f3375cf6975cb` |
| ui/ArchivePanel.tsx | `377dd1e6fb90ad6ae9bee5b596d0e80541edc7c3ed85b1be5d9bdb79de9a9722` |
| ui/main.tsx | `a203c37c9b1bd721b454aa03d5f875712dacceab9a023cd52b247dc06dd61089` |
| ui/archive-journeys.ts | `d9e35945b5f87d978b43845b733874fe2c8b9f41c33072c3ff9cf052c7e5440b` |
| check-archive-controller.mjs | `8249cf396ef9b8427786c02f30360ed575b2bb4d535abae3325ecc6e8cf42be8` |
| build.mjs | `cc44e2f79a9b3eb59af6cf4fc2f87f2b3e6aad62b75b64f4fee7a3b0be420492` |
| verify-frontend.mjs | `2e3df3309b7be0486bc97752057a9c3e9f13c13521788cecc768c8672087351a` |
| src-tauri/build.rs | `5791899bb12d963d0abda6ac4a090a4745ddfb32015e385158cff8f6fdef791f` |
| src-tauri/tauri.conf.json | `9a7a2f13cabcfbe5e87842436baad90d0262694a9f9b92bd986aeebc90758946` |

Next runnable coordinator gate: finish the corrected final source-bound native
journey and integrated compatibility/publication checks, preserving separate
attribution for picker doubles, actual dialogs, Android chooser transfer and
physical hardware. No milestone checkbox, favorable score or acceptance claim
is made by this review.
