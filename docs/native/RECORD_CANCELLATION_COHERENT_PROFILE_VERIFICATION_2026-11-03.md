# Coherent profile host verification — 2026-11-03

Refs M10.02 `RECORD_CANCELLATION_UI_COHERENT_PROFILE`, supporting M09.04/M09.06.
Full task criteria remain unchecked; implementation is in review.

Base open/unmerged PR391 is `38a00b252e4cbbb583bc0160fec0ad4ca79c77db`.
The profile role is immutable commitc89b9e4f/tree d29c520f, 2,664 files. Current
tested code is `5e232b3080e854aafb5d38d17a499897875ec635`, tree
`f3a0ea6aec02c44daa2b9358c677dd7c1b9bc9c4`, 2,665 files. Only subsequent
documentation changes are excluded from that tested tree. The source catalog
and current operator roles deliberately have different heads/counts.

## Actual checks

Windows/Python3.14; physical D: source, fixtures, output and process-local TEMP/TMP.
Workers are frozen before launch with the checked unchanged180-second host owner.
Metadata drivers deny real process/socket dispatch and restrict writes to owned
scratch/captures. SDK/build/admission observations in synthetic tests are fake.

| Scope | Methods | Actual result | Owner seconds |
| --- | ---: | --- | ---: |
| New profile FIRST against old routing | 4 | 2 assertion failures, 2 existing source refusals/errors | 12.277 |
| New current FIRST against old contract generation | 4 | 1 assertion failure, 3 existing authority refusals/errors | 1.022 |
| Profile + existing profile/controller/activation boundaries | 41 | 0 failures/errors/skips | 133.041 |
| New current generation after wiring | 4 | 0 failures/errors/skips | 1.051 |
| Current metadata + unchanged parent boundaries | 74 | 0 failures/errors/skips | 16.787 |
| Current exact-literal host cohort | 3 | 0 failures/errors/skips | 4.747 |

**114 unique method IDs** =41+74+3 minus four repeated profile methods. The
four-method focused repeat is not additive. The eight original method bodies
are unchanged across FIRST/final. FIRST results demonstrate old routing rejecting
new-generation positive expectations, not missing APIs or retroactive defects in
the old source. Original executing source copies, workers, logs and failures remain.

The new tests use pure metadata/import/binding ports with fixed independent root,
head/tree/catalog anchors. Current nested authority tests verify exact operator,
contract, proposal and review-reference joins before any inner invocation. This
is not positive execution approval. Physical-D inherited cohorts retain their
existing NT gates; no Linux or complete CI qualification follows.

The host cohort launches four real Python literal children across three methods.
Before Popen, the driver requires exact six-element argv, current Python with
`-I -S -B`, owned script path/bytes, pipes, shell=false and CREATE_NO_WINDOW.
Only two reviewed literal body hashes are allowed. The matching audit event is
required; other process/socket dispatch is denied. These are barrier/job/identity/
clock/capture tests, not SDK/emulator cleanup. The children are not suspended:
their barrier blocks preflight until checked job assignment/started publication.
Unknown-close observation first verifies native close success then injects a false
observation; it does not demonstrate an actual OS CloseHandle failure. Original
operation2400/guest1800 limits are not empirically exercised by short host tests.

## Genuine file-only source and input checks

The frozen-role preflight completes in5.533s owner with known cleanup. It loads
real namespace/module origins under the reconstructed role, runs real `_source`
and checker guards, checks all28 source bindings and invokes public
`verify_frozen_product` without a replacement reader. Returned metadata is
value-equal to the original32,140B/SHA2564d39b74a... saved descriptor. Source maps
before/after match all2,664 raw files and the full Git catalog. No APK/JVM rebuild,
Android or native engine execution is claimed.

Actual public `inspect_fixed()` completes40.901s owner (40.816s timed body), known
cleanup, checking2,664 profile files,28 benchmark sources and928 installed files,
5,282,289,699B per planned installed pass, twice. The inspector's final ledger/
capacity observation is retained. All execution/admission flags remain false;
no guest, authority, run controls or operation directory is created. Planning
output is create-only, and all prior generations remain immutable.

New handoff9,255B/50e86854...; prepare173,620B/fbfb3b37...;
capacity568B/017b601a.... Capacity would fit at the captured ledgerc0d39, not admit
or authorize. Old pre-retirement84ad observations and old-profile refusals retain
their historical attribution. No old namespace is injected with the new reader.

Current inner/outer genuine file-only entries complete3.633s/1.125s owner, known
cleanup. The inner reconstructs the actual full profile Git tree; both load the
current fixed bindings, then public main refuses absent authority. No dispatch
attempt is observed and operational directories stay absent. Their before/after
current maps match all2,665 files and final metadata/host maps. Positive
authorized preflight/preparation/admission/boot/cleanup is still unrun.

## Reproduction and limits

Private frozen controls include `run_owned.py phase1-first-v1`,
`phase1-final-v1`, `phase2-first-v1`, `phase2-new-v1`, `final-v1`,
`run_entry_owned.py genuine-fresh-v1`, `genuine-parent-v1`, `host-new-v1`,
`run_frozen_preflight.py`, `run_inspection.py`, `freeze_profile.py` and
`commit_current.py`. The immutable role is constructed only after phase1 passes,
from exact committed Git objects. No clean-worktree assertion substitutes for
the closed raw catalog.

The six profile/activation regression modules are retained with the original
assertions. Current fixture root/head/tree/count expectations are explicitly
advanced to the new known role, including the full2664-row catalog vectors and
independent call counts; negative mutation assertions are not weakened. The
count-named method is versioned2664. Parent operator body is unchanged; fresh
operator changes only `_SOURCE_FILE_COUNT`. Both contracts change fixed metadata
pins, not engine/storage/process mechanisms.

B75 authors the two original test files and independently reviews production;
B72 independently reviews source, oracle quality and evidence and drafts the
private proposal. Nobody receives independent-quality credit for their own
authored artifact. Root integrates shared contracts and publication. Final source,
documentation, proposal, publication and archive audits are separate records,
not owner acceptance.

The managed worktree tool again rejects the physical repository outside chat
roots. A verified raw Git snapshot and alternate index preserve normal892/index897;
agents retain existing separate worktrees and Root alone integrates proposals.
All originals/recovery are under matching
`D:/Dev/Experiments/LocalLore/2026-11-03-record-cancellation-coherent-v1` and
`D:/Dev/Recovery/LocalLore` basename, with a combined256MiB ordinary retention
budget. This includes both source roles and retained synthetic wire data. Final
manifests measure coverage; no guest/evidence/model data is deleted for capacity.
No private raw diagnostics, credentials, stories or weights are uploaded.

**SDK18 Android0/5.** No actual operational authority, preparation/boot, SDK/ADB
service/model/phone action, shared operational ledger/lock/admission write,
preserved-data deletion, settings change, other-emulator stop, release or merge.
Toy fixture metadata/authority/ledger writes remain isolated. Continue without
phone; no rediscovery is performed. No new runtime/model/SDK/native dependency.

Next: finish the exact reviewed outer-operation proposal, then obtain fresh
scope-specific preparation/boot approval and current locked admission. Metadata
and old spent SDK15/retirement grants do not supply that authority.
