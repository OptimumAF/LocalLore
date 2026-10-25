# Ordinary setup, local scene and player memory qualification

Refs #9 (M05.05), #5 (M01.05), #10 (supporting player-memory surface).
Root claim6398062716; author claim6398119552. This document specifies authored
tests, not an execution or phone-support result. Existing import, cancellation
and Compose proof families retain their exact contracts and data.

## Real route

Each selected method manually launches the exact `LocalModelSetupActivity` with
an empty Compose rule. No test calls Candidate.store/installed before its real
READY observation. The ordinary controller performs its full accepted-model
verification on IO, and the actual enabled `model-start` button launches the
exact `LiteRtPlayActivity` and finishes setup. A lifecycle callback captures that
actual RESUMED Activity; it does not create a substitute Activity or factory.
The test retrieves its existing ShellViewModel and reads its already-constructed
transport getter ON MAIN. Null observation fails; no retained-VM fallback or
new owner is constructed. The passive receipt-only worker snapshot has no setter,
reset or callback injection; null is never coerced to zero.

The borrowed transport is command-capable, not an enforced read-only capability.
This fixture uses only fixed `resume`/`play_snapshot` inspection commands through
it, with the actual production borrowable-owner guard before/after inspection.
It never substitutes direct create/Send/commit/cancel calls for user actions.
New story, Send, kind selection, inspector navigation/search and Start are actual
production Compose controls. No demo-action buttons are used for invalid-text
controls. Teardown finishes the actual play Activity on Main, observes DESTROYED
and checks the captured native handle becomes InvalidHandle; it never directly
closes a borrowed transport. Setup/Activity disposal cannot earn prior UI checks.

| Exact class | Single method | Phase | Cap |
| --- | --- | --- | ---: |
| `ReceiptOrdinaryStartTest` | `startsFromSetupAndCommitsRealGift` | `ORDINARY_START` |170000ms|
| `ReceiptOrdinaryDialogueTest` | `inspectsGiftRejectsInvalidActionsAndRecordsDialogue` | `ORDINARY_DIALOGUE` |170000ms|
| `ReceiptOrdinaryReopenTest` | `reopensTwoReceiptsThroughSetupWithoutSdk` | `ORDINARY_REOPEN` |120000ms|

Namespace is `org.locallore.app`. Exact class selection precedes Context/storage
IO. Every phase requires a changed `(pid,start)` from its linked predecessor,
including START from IMPORT; PID reuse with changed start is valid. There is no
same-process reset or second candidate admission. Old source preflight/import
are reused only as prerequisites, not rerun by these classes.

## Outcomes

START requires an absent workspace and proof root. Actual ordinary setup READY
is its initial accepted full check; there is no manual prewarm check. After Start
it verifies the empty library and clicks New story once. It enters original
Action `I give my last potion to Mira.` and clicks Send once. Actual production
VM validation/automatic commit must display revision1, spent potion and both
accepted transcript bodies. Native receipts must contain the exact original
request and one player→Mira potion transfer, plus the actual built-in profile.
An explicit full model recheck occurs AFTER commit. The owner guard repeats
after that hash; final public-close trace validation occurs after Activity and
native-handle close. Source/model copying is not repeated.

DIALOGUE starts in a new process through the same ordinary setup route and
checks the entire native START receipt array/gift SHA before new work. It uses
the four existing inspector tabs: Progression, History, Relationships, Knowledge.
History must display recorded input/narration with Event#1 provenance; the real
source button opens the eligible event and returns to records. Progression and
Relationships show typed canonical fields/sources. Knowledge positively shows
the player-known public seed canary `SECRET-TIDE-731`; this is not a forbidden
leak. Both hidden NPC beliefs (`The tideglass relic is in old-ruins.` and `Rowan
may possess the tideglass relic.`), and the unknown beacon-mark proposition
(`An old repair mark is scratched inside the dry well.`), must return zero
eligible rows/total and the actual empty UI. Browsing must leave native canon
unchanged. The UI remains a player-only lens, not an NPC/omniscient viewer.

Actual original Action inputs `I use ability blink.` and the duplicate gift
must produce Ability/Inventory notices and unchanged native canon/receipts.
The existing Rust finite-English guard and Engine preflight reject these before
director construction. This is real-route mechanical refusal, not a claim that
the model safely rejected an adversarial proposal. The passive guards snapshot
must EMPIRICALLY have every SDK count0, all last_ms null, creations0 and no
saturation; a missing snapshot fails. UI draft/catalog changes are not canon and
are not required to remain identical.

It then selects actual Dialogue, enters `Where is the tideglass relic?` and
clicks Send once. The real Rust path still requests director (optional repair)
then narrator: `play.rs` skips only the Action compiler for Dialogue, uses an
empty factual retrieval query, generates the director, stages the exact speech,
then generates narration from approved evidence. Accepted revision2/receipt2
must retain the first gift exactly. The second request and said event preserve
the literal question as a recorded statement, with Event#2 provenance and no
new canonical truth. Existing known-truth rows remain unchanged. This does not
claim that the model answered the question, verified its proposition or passed
general secret-prompt resistance. The explicit full model hash again follows
production automatic commit; runtime guards remain unchanged before SDK work.

REOPEN uses a third new process and the actual setup Start route, visibly shows
all four retained transcript bodies/revision2/spent potion, and compares the
full native receipt array and both individual receipt hashes. It performs no
Send/Cancel and requires a nonnull passive snapshot with all counts0, last_ms
null and creations0 after close. Accepted-model recheck, owner guard and known
native-handle closure remain required.

## Closed proof and file contract

Fixed internal root `no_backup/receipt-ordinary-scene-proof-v1`; progressive
file sets3/7/10:

```text
START: start-v1.json,start-ready-v1.txt,start-worker-v2.json
DIALOGUE adds: dialogue-v1.json,dialogue-ready-v1.txt,guards-worker-v2.json,dialogue-worker-v2.json
REOPEN adds: reopen-v1.json,reopen-ready-v1.txt,reopen-worker-v2.json
```

JSON and traces are regular, nonlinked, own-UID printable ASCII1..4096B; ready
files are empty. Writes are exclusive CREATE_NEW/NOFOLLOW/full-write/force,
ready last. Each next phase validates exact manifests and prior proof/trace hashes;
malformed, partial or extra files refuse and remain. No old namespace deletion,
adoption, clear/uninstall or failure retry is authorized.

Common JSON keys are EXACT old real-family keys:

```text
version,phase,pid,start,uid,process,model_bytes,model_sha256,
source_verify_opened,source_verify_closed,source_verify_bytes,
source_import_opened,source_import_closed,source_import_bytes,
sdk_invoked,publication_native_invoked,elapsed_ms,
userdata_free_before,userdata_free_after,external_free_before,external_free_after,
memory_total_bytes,memory_available_before,memory_available_after,checks
```

Version1, UID≥10000, exact debug process/model constants from the old proof
codec. All source counters0 and publication_native_invoked false; SDK true for
START/DIALOGUE, false REOPEN. No staged source object is resolved here. The old
IMPORT proof remains the actual source-open/close/copy evidence.
All phases add `prior_pid,prior_start,revision,receipt_count,receipts_sha256,
gift_receipt_sha256,worker_trace_sha256`. Full native receipt arrays—not UI
presentation—are canonically serialized and SHA256 hashed. Revisions/counts
are fixed1/1,2/2,2/2 by phase. Prior hash keys are `prior_import_sha256`,
`prior_start_sha256`, `prior_dialogue_sha256` respectively.
START also has actual `repairs`0..1/Boolean`fallback`; DIALOGUE adds those and
`dialogue_receipt_sha256,guards_worker_trace_sha256`; REOPEN adds only
`dialogue_receipt_sha256`. No arbitrary extras/strings are accepted. Check maps
are size-bounded before immutable copying, exact-key and all true. Hashes are
exact lowercase64hex. Old storage/RAM floors and strict elapsed caps remain.

START/DIALOGUE v2 traces require returned roles[D,N] or[D,D,N], failureNONE,
matching create/send/DONE/drain/conversation-close entered/known counts,
engine-close entered/known1, messages>0, ERROR/CANCEL/UNCERTAIN0 and no saturation.
Guards→dialogue final snapshot time/counts/prior nonnull times never decrease;
zero snapshots are not compared byte-for-byte because snapshot_ms advances.
These are historical recording points, not atomic SDK state, hidden native
reclamation, performance timings or future-callback immunity. No nonnull trace
or healthy owner is inferred from zero uncertainty alone. Failures may emit
one bounded fresh passive v2 snapshot per process; diagnostic failure cannot
replace the original test failure or create a positive proof.

## Exact checks

COMMON14 included in EVERY phase:

```text
memory_eligible,setup_activity_exact,setup_ready_visible,start_enabled,start_clicked_once,setup_finished,
play_activity_exact,play_resumed,production_shell_viewmodel,constructed_transport_observed,
production_transport_local,source_unopened,candidate_owner_retained,native_handle_closed
```

START28 = COMMON14 plus:

```text
prior_import_proof_exact,new_story_clicked_once,canonical_zero_before,local_provider_visible,fixed_action_visible,
send_clicked_once,gift_visible,gift_receipt_exact,local_profile_exact,canonical_revision_one,single_receipt,
full_model_postcheck,owner_guard_postcheck,worker_closed_known
```

DIALOGUE43 = COMMON14 plus:

```text
prior_start_proof_exact,process_identity_changed,initial_gift_receipts_exact,progression_visible,
history_provenance_visible,relationships_visible,knowledge_known_truth_visible,hidden_belief_search_empty,
hidden_beacon_search_empty,event_source_navigation_visible,inspector_canon_unchanged,ability_action_rejected,
duplicate_gift_rejected,guards_canon_unchanged,guards_worker_zero,dialogue_kind_selected,fixed_dialogue_visible,
dialogue_send_clicked_once,dialogue_visible,literal_dialogue_receipt_exact,statement_not_truth,known_truth_unchanged,
gift_receipt_preserved,canonical_revision_two,two_receipts,local_profile_exact,full_model_postcheck,
owner_guard_postcheck,worker_closed_known
```

REOPEN23 = COMMON14 plus:

```text
prior_dialogue_proof_exact,process_identity_changed,two_receipts_exact,retained_transcript_visible,
canonical_revision_two,no_send_or_cancel,worker_zero,full_model_postcheck,owner_guard_postcheck
```

The94 new checks plus old preflight12/import16 total122. Phase170/170/120s,
aggregate870/outer900/entry920, SDK60/cleanup5 and host-owner/resource limits are
unchanged; no worst-case sum is promised to fit. Root runs compilation, audits,
pure tests and a separately admitted controlled execution. No authored test
proves a runtime pass, phone/ARM64/16KiB, DocumentsUI, sustained quality, privacy,
thermal/memory pressure, power-loss or broader milestone gate.
