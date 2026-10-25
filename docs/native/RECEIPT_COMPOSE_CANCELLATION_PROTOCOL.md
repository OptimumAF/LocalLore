# Real receipt Compose cancellation and visible recovery

Refs #9 (M05.05), #5 (M01.05). This source-only fixture is not execution,
phone qualification, performance evidence or a release. Root claim6397202908;
fixture claim6397217589. Earlier API cancellation and original real receipt
proofs remain separate and unchanged.

## Surface and phase selection

`ReceiptComposeCancellationActivity` is a receipt-only, nonexported
`MainActivity` subclass. It overrides only `createWorkspaceTransport`, calling
the production `CandidateLocalModel.createTransport` with its instance trace.
`MainActivity` still constructs its actual `ShellViewModel`, `DurableGateway`,
production Compose screen and normal callbacks. The test reads the existing
ViewModel using `ViewModelProvider`; no replacement factory, callback injection,
fake result, response delay or SDK route is installed.

The empty Compose rule launches this Activity manually only after exact class
selection, prior proof verification and off-Main full model verification/runtime
admission. The selector must equal the class name exactly before Context/storage
IO. Each class contains one ordinary JUnit method:

| Class | Method | Phase | Whole-phase cap |
| --- | --- | --- | ---: |
| `ReceiptComposeCancelTest` | `cancelsRealTurnThroughComposeControls` | `UI_CANCEL` |170000ms|
| `ReceiptComposeRecoverTest` | `sendsRecoveryGiftThroughCompose` | `UI_RECOVER` |170000ms|
| `ReceiptComposeReopenTest` | `showsRecoveredGiftWithoutSdk` | `UI_REOPEN` |120000ms|

Package prefix is `org.locallore.app`. These borrow only existing PLAY/REOPEN
deadline constants; they never use the old phase selector/proof emitter. The
870/900s aggregate/outer caps,920s entry, SDK60s turn/5s cleanup and resource
floors remain unchanged. Per-phase caps do not promise all worst cases fit the
aggregate. No automatic phase retry is permitted.

## Actual UI actions and observations

UI_CANCEL requires the old source-preflight/import family only, with no existing
workspace. MainActivity uses `autoCreateIfEmpty=false`: the test verifies the
visible empty library and clicks `reset-demo` (New story) once. It checks visible
revision0, player-owned potion and empty canon before entering the fixed original
action `I give my last potion to Mira.` in `play-input` and clicking `play-send`.
Both `inference-provider` and `play-provider` must display the actual LOCAL
labels; the header is `Local Rust engine · local inference configured`.

The test first brings `cancel-turn` into view during the actual preparing state,
then polls the existing trace for one returned DIRECTOR message and no observed
terminal/cancel/engine-close/uncertainty. The Activity must remain RESUMED and
the production ViewModel busy/preparing before one actual Cancel-button click.
A missed window fails without retry. The historical sample is not an atomic
native-active observation or proof of cancellation causation.

The production ViewModel deliberately cancels its own pending caller Job and
invokes actual `cancelSaved`. This test does not substitute direct gateway/VM
Send, Cancel, create or commit calls, nor copy the API test's original-Deferred
Rejected assertion. While the Activity is still RESUMED it requires all busy,
preparing, checking-cancellation and recovery-required flags false, visible
`Cancellation checked. Showing the accepted saved history.`, revision0 and
unchanged potion. Actual trace cancel/drain/known-close predicates and the
production borrowable-owner guard must also pass before canonical inspection.

After full accepted-model rehash the existing owner guard runs again. Only then
does the Activity close. `MainActivity.onStop` auto-cancellation and ViewModel
disposal cannot earn the earlier UI cancellation checks. The native handle must
become InvalidHandle, and a fresh post-close trace must still satisfy the final
predicate before proof emission. No quarantine/reset/force cleanup is added.

UI_RECOVER requires a different `(pid,start)` from UI_CANCEL, checks visible and
canonical revision0, enters the same fixed action and clicks Send once. The
production ViewModel performs the actual local turn, validates and commits it.
The test requires the displayed accepted notice, revision1, spent potion and
both actual persisted player/narrator messages, plus the exact canonical gift,
single receipt/profile, known SDK close and full model recheck. This recheck
occurs AFTER the production ViewModel's automatic commit; it is not a precommit
full-hash gate. The unchanged production runtime guards still run before SDK
boundaries. Transcript scrolling and lookup use the unique production
`message-body-<SceneMessage.id>` tag, require exactly one body, and compare that
body's actual Text semantics exactly to the accepted message. Visibility still
requires the same nonempty clipped on-screen portion through `isDisplayed()`;
the retained composer draft is neither cleared nor used as a text fallback.
Failures carry only fixed `COMPOSE_TRANSCRIPT_*` codes: MISSING (no body composed
after scroll), DUPLICATE, SCROLL (body exists but scrolling failed), TEXT,
VISIBILITY, or LOOKUP (semantics query itself failed). No diagnostic includes
narration, matcher text or a framework cause. The earlier generic visibility
failure did not identify the failing lookup or message, so this correction
addresses a demonstrated source ambiguity without attributing that actual
failure's cause. It never clicks the scripted Give-potion/demo controls.

UI_REOPEN requires another different `(pid,start)`, full accepted verification
and production UI launch. It shows the persisted revision1/gift and unchanged
receipt without Send/Cancel or worker events. It also closes its owned surface
and verifies native-handle closure. PID reuse with changed start is acceptable.

Use the existing Compose dependencies and default test-clock advancement.
Wall-clock-bounded `waitUntil` observes external ViewModel/SDK work; virtual time
never expires an SDK deadline. Do not register active SDK work as an idling
resource (that would block the Cancel action), or use new-alpha clock bypasses.
UI assertions/actions run on the test thread; main-thread lifecycle checks do
not perform nested Compose synchronization. Scroll/synchronization overhead may
miss the real window and must fail, not fabricate it. See the official
[Compose synchronization contract](https://developer.android.com/develop/ui/compose/testing/synchronization).

## Closed proof codec

New fixed internal root: `no_backup/receipt-compose-cancel-proof-v1`.
`ComposeCancellationProof` reuses only the old pure identity/capacity value types;
it has a separate closed phase grammar and exact check sets. Identity UID is at
least10000, PID positive, start nonnegative. Maps are size-bounded before copying,
exact-key/all-true and immutable. Encoding takes only typed numeric/Boolean/enum
data and lowercase64-hex hashes; no arbitrary JSON, raw errors, paths or text.

Common keys are exactly the original real proof keys:

```text
version,phase,pid,start,uid,process,model_bytes,model_sha256,
source_verify_opened,source_verify_closed,source_verify_bytes,
source_import_opened,source_import_closed,source_import_bytes,
sdk_invoked,publication_native_invoked,elapsed_ms,
userdata_free_before,userdata_free_after,external_free_before,external_free_after,
memory_total_bytes,memory_available_before,memory_available_after,checks
```

Version1; process `org.locallore.app.modelvolumeverify`; model bytes2588147712
and SHA`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
All six source counters are0, publication_native_invoked false. SDK flag true
only for UI_CANCEL/UI_RECOVER. Initial source is never resolved in these classes;
the old import receipt remains the actual staged-source evidence.

All phases add `prior_pid,prior_start,revision,receipt_count`:

| Phase | Prior hash | Extras | Revision/receipts |
| --- | --- | --- | --- |
| UI_CANCEL |`prior_import_sha256`|`sample_worker_trace_sha256,worker_trace_sha256`|0/0|
| UI_RECOVER |`prior_cancel_sha256`|`receipt_sha256,repairs,fallback,worker_trace_sha256`|1/1|
| UI_REOPEN |`prior_recover_sha256`|`receipt_sha256`|1/1|

Repairs0..1, actual Boolean fallback; no invented cancellation receipt hash.
Userdata floor1GiB+128MiB, external2GiB, total RAM7..8GiB, initial available4GiB,
final available0..total. These observations do not weaken actual volume guards.

Progressive fixed manifests contain4/7/9 files:

```text
CANCEL: cancel-v1.json, cancel-ready-v1.txt,
        cancel-sample-worker-v2.json, cancel-worker-v2.json
RECOVER adds: recover-v1.json,recover-ready-v1.txt,recover-worker-v2.json
REOPEN adds: reopen-v1.json,reopen-ready-v1.txt
```

Each JSON/sidecar is a regular, nonlinked, own-UID printable-ASCII file1..4096B.
Ready files are empty. Every write is exclusive CREATE_NEW/NOFOLLOW/full-write/
force; ready is last. Exact manifests and SHA-linked prior proof/sidecars are
checked before the next phase. Failure preserves partial files without adoption
or deletion. Old real and API-cancellation namespaces are not written.

Worker traces retain strict v2 shape. Sample/final cancel and recovery predicates
are the same frozen public recording-point checks as the
[API cancellation protocol](RECEIPT_REAL_CANCELLATION_PROTOCOL.md). Final cancel
time/counts/previous nonnull timestamps cannot decrease and its already-returned
creation record must match the sample exactly. These are one-trace-history
constraints, not jointly atomic native state or hidden resource health. Final
traces are refreshed after surface/native close; zero uncertainty alone is not
health authority. Failure uses the existing bounded v2 reporter and preserves
the original test failure, never a positive proof.

## Exact checks

UI_CANCEL26:

```text
prior_import_proof_exact,memory_eligible,candidate_access_receipt,accepted_full_recheck,
runtime_guard_passed,production_main_activity,production_shell_viewmodel,production_transport_local,
empty_library_visible,new_story_clicked_once,canonical_zero_before,initial_zero_visible,
local_provider_visible,fixed_input_visible,send_clicked_once,preparing_visible,sampled_public_inflight,
cancel_clicked_once,cancellation_settled_visible,worker_drain_closed_known,canonical_zero_after,
accepted_post_sdk_full_recheck,source_unopened,candidate_owner_retained,native_handle_closed,cancel_control_displayed
```

UI_RECOVER24:

```text
prior_cancel_proof_exact,process_identity_changed,memory_eligible,candidate_access_receipt,
accepted_full_recheck,runtime_guard_passed,production_main_activity,production_shell_viewmodel,
production_transport_local,initial_canonical_zero,initial_zero_visible,local_provider_visible,
fixed_input_visible,send_clicked_once,accepted_gift_visible,worker_drain_closed_known,canonical_revision_one,
canonical_given_to_mira,canonical_single_receipt,local_profile_exact,accepted_post_sdk_full_recheck,
source_unopened,candidate_owner_retained,native_handle_closed
```

UI_REOPEN17:

```text
prior_recover_proof_exact,process_identity_changed,memory_eligible,candidate_access_receipt,
accepted_full_recheck,runtime_guard_passed,production_main_activity,production_shell_viewmodel,
production_transport_local,retained_gift_visible,no_send_or_cancel,no_worker_events,canonical_revision_one,
canonical_gift_receipt_unchanged,source_unopened,candidate_owner_retained,native_handle_closed
```

The67 new checks complement old preflight12/import16; no positive runtime,
DocumentsUI, performance, reliability or phone-support result follows from
authored tests. Central compilation, signed artifacts, independent review,
fresh admission and actual ordinary PASS/proof/known cleanup remain required.
