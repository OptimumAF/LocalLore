# Original AUTHOR restart controller: bounded verification, 2026-10-29

Refs #13 (M09.06), #14 (M10.02); draft PR #257, stacked on open/unmerged #256.
Supporting implementation is in_review. Full tasks remain unchecked. This
report preserves the bounded runtime outcome and earlier host checkpoints with
their original source attribution. The [M10 ticket](https://github.com/OptimumAF/LocalLore/issues/14)
and [PR](https://github.com/OptimumAF/LocalLore/pull/257) remain the live trackers.
Earlier spent guest scopes and claims are not reused; the still-unused approval
for this packet's first boot is retained as described below.

## Latest actual run: import and AUTHOR pass; external restart incomplete

At frozen executable/build source `f589f270b323726f5f07e53b86197593535e135b`,
the guard optimization passes **686 Python tests**, zero failures/errors/skips,
with2,079 unchanged source inputs (239,828ms finite owner, exit0). The current
offline Android build passes **588 rerun JVM tests/58 XML reports** and both APK
audits (48,176ms0). Separate fresh lint passes in118,282ms0: actual analyzer work,
zero errors/fatal findings and10 warnings. Independent build/lint readback passes.
These are host/build results, not Android restart acceptance.

Current build admission binds2,079 tracked/936 compiled inputs. The rebuilt APK
paths remain under `sdk-build-v2`; their bytes/hash match the original approved
APKs, rather than relabeling the old paths as a new build:

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| Product APK |78,289,152|`0ad6f03adf0179438570c7d4a7933f2ef7b1fd929ce7361c2627749168439fa9`|
| Test APK |2,272,447|`215731ef23e46f1dd1d97f9fb846672eaa954467332069f8723520f3101a0221`|

The original explicit human reply remains immutable. A separate execution
binding connects that same still-unused first-boot/import/AUTHOR approval to
the current host-only correction, unchanged APK/helper/model content and the
same prepared fresh guest. It claims no new human reply and expands no action
or lifetime. The failed first owner namespace and original source/build records
remain intact. New admission SHA256:
`fb274727568f4646ee92837e8a3a0bc7ff6379a343036f3d1fd4d5c461144a22`;
current build admission `2b47ddceb16eb5ba13b2f76c799e291358c62b8b3000f731c9b89948d4579b24`.

The second isolated owner passes its unchanged3,000ms initial version/devices
proofs in1,427ms/1,777ms, including complete replies and checked socket/client
closure. Its API35/x86_64 guest uses the approved8GiB/four cores. Exact ownership,
registration, Android profile, package identities and guest storage checks pass.
Both APKs and the13,848B read-only helper are installed and verified; the helper
actually runs for the initial boot-ID observation. The binary-transfer probe
passes. The existing2,588,147,712B local Gemma model transfers in77,213ms and its
full device hash matches
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
No model download or external upload occurs. The existing runtime profile pins
revision `bda624851d74be34d4e1f7fac1fc4155939539c7`.

Actual import instrumentation31 passes (41,224ms client), followed by AUTHOR
instrumentation43 (54,903ms client). Both return0 with empty stderr. Original
proof validators, JUnit witnesses and recorded listing/pre-hash/binary-tar/
post-hash collections agree. The engine accepts one creation; exact retry has
`created=false`, the same scope/revision, and an ordinary native reopen returns
the same snapshot bytes. Worker evidence records exactly one AUTHOR conversation
creation, settled drain and known conversation/engine close. This is one
synthetic-premise model result, not broad story-quality or performance evidence.

The controller does **not** complete external restart. During later package
checks in phase `death`, command55 returns0/completed with empty stderr and
recorded socket/input/sender/cleanup flags true, but its measured7,932ms exceeds
the remaining effective7,872ms. Its final client guard necessarily encounters
session expiry by then. The first caught body exception is not serialized, so
the earliest rejecting invocation cannot be identified. The poisoned capture
maps to generic `resource_uncertain`; this is not evidence of a resource leak.
The controller result is refused,55 clients,1,223,032ms including finalization;
finite parent ends child1 at1,248,240ms with known capture/cleanup and empty
streams. No old-PID snapshot, AUTHOR force-stop, restart prerequisite/claim,
passive restart method, six restart sidecars or new PLAYER turn is produced.

The fixed stop launcher publishes only this admission's stop after known
controller termination. The actual owner ends0 in1,404,498ms with
`qualified_target=true, stop_requested`; **all15 cleanup flags pass**, with
guest termination/wait and captures preceding private-server closure. Source
and launcher checks remain stable. No operation stops the other emulator,
changes system settings or operates the shared ADB lifecycle. No merge/release.

A separate finite expected-refusal audit passes in16,363ms0, empty streams and
111 unchanged source/interpreter pins. It binds the actual started controller
worker separately from the actual started target-owner worker. The unchanged
full controller reader refuses `capability`; the audit independently verifies
the54 qualified clients, both command55 proofs, original import/AUTHOR/JUnit/
collection graph, refusal and closed owner. Audit success does not qualify the
controller. Key private evidence hashes, with no private contents published:

| Record | SHA256 |
| --- | --- |
| Refused controller result |`de2fb5ba2f3f2f8953f76bb0c2f7b597ea15b8d795b9efe62a30ee394f70c7ea`|
| Command55 |`84878c52b0fcfba9a9f0733a48f61cab8a72930fbb2badf137ec2c4e5884c793`|
| Closed target owner |`9f1bf54e82720f8dc17c720457f95125a7bb4a64a175fd41535f6665c410f033`|
| Expected-refusal audit worker |`c6d6e2f9e10b09dd13dd9fd5a240619a408f8f2f64fa1fde49f59a10c360cd45`|
| Independent timing review |`d91cdbdab41c8a98aa789378e07c7f9453513126d579658684233c2003d5d271`|

The closed timing review totals616,718ms across saved client elapsed windows.
Those include after-proofs and are not shell-only latencies. Before-proof
internal timing adds272,149ms outside those windows; after-proof272,108ms is
already nested inside them. The220 version/devices query exchanges total
403,221ms nested inside proof timing. The remaining334,165ms mixes guards,
validation, initialization, persistence and close without stage timestamps.
These observations identify substantial validation cost but cannot attribute
every gap or establish phone/model latency. All full before-connect,
before-send and after-response checks, both queries, deep readers and the
1,200s session budget remain unchanged.

The drivers ran from the physical D Root checkout with TEMP/TMP/TMPDIR set
to `D:/Dev/_Temp`. Private create-only drivers and captures remain under
`D:/Dev/Experiments/LocalLore/2026-10-29-author-restart-controller-v1` (`<B>`).
These entry points identify the executed drivers; their retained requests bind
the exact child commands and source inputs:

```text
python -I -B <B>/check-integrated-v2.py guardfix
python -I -B <B>/build-sdk-v2.py
python -I -B <B>/lint-current-v2.py
python -I -S -B benchmarks/owned_restart_owner.py --admission <B>/target-admission-v2.json --admission-sha256 fb274727568f4646ee92837e8a3a0bc7ff6379a343036f3d1fd4d5c461144a22
python -I -S -B <B>/run-restart-controller-v2.py run
python -I -S -B <B>/run-restart-controller-v2.py stop
python -I -S -B <B>/closed-review-v2/failure-audit-v2.py run
```

The original host-only success-audit draft remains unrun; a distinct failure
audit preserves the actual refusal. A separate D recovery already verifies
453 runtime metadata/raw files totaling9,552,350B by original/copy hashes.
The closed guest's bulk recovery is recorded separately after completion;
original failures, spent claims, guest state, models and prior backups stay
preserved. No private diagnostics, saves, weights or credentials enter Git.

M09.06/M10.02 supporting code remains **in_review**; full tasks stay unchecked.
The external-restart gate is blocked for this spent case. Next runnable work is
bounded host phase timing/hash-work accounting within the unchanged full guards
and pure replays, followed by a tested justified optimization. Another guest or
model attempt needs a new concrete scope and applicable approval. Phone/ARM64,
accessibility, quality, performance and complete journey acceptance remain open.

## Implemented boundary

The [fixed protocol](ORIGINAL_AUTHOR_RESTART_CONTROLLER_V1.md) adds separate
restart owner/SDK5 entry points over explicit shared private mechanisms. Legacy
SDK4 public entry points retain their original profile. The fixed controller
allows one import, one AUTHOR and one passive restart method; it requires
current code/APK/helper/model bindings, complete original native/JUnit evidence,
same-boot PID/UID observations and terminal prior-process state. The LLM/engine
authority, canonical events and original proof validators remain unchanged.

Closed replay binds canonical sidecar paths to actual recorded SDK listing,
pre-hash, binary tar and post-hash bytes. It rejects borrowed files, duplicate
method witnesses, wrong session/caller/budget/head, changed boot/PID birth,
malformed/refused kernel packets and incomplete resources. Its fixed build
reader checks declared current source bytes, exact compiler recipe/tool roster,
actual bounded ELF bytes and bound reports. Live tracked completeness and the
external held worker remain separate authorities.

## Actual integrated host cohort

At `4bce93d6cb6769fdc29e8fff404c4212abe67d77`, the finite Root cohort passes
**677 Python tests**, zero failures/errors/skips, **2,077 unchanged tracked
inputs**, owner **131,831ms / exit0**, known cleanup/capture, stderr0.

Executed from physical
`D:/Dev/Worktrees/LocalLore/LocalLore-starter-native`, with TEMP/TMP/TMPDIR
`D:/Dev/_Temp`:

```text
python -B D:/Dev/Experiments/LocalLore/2026-10-29-author-restart-controller-v1/check-integrated-v1.py first
```

The bound helper loads these `scripts.tests` modules through unittest:
test_windows_native_tcp_state, test_android_process_client_v3,
test_android_process_verification_v3, test_adb_held_socket,
test_adb_held_socket_windows, test_adb_held_socket_probe,
test_windows_tcp_control, test_windows_tcp_observation,
test_android_process_client, test_android_process_verification,
test_android_external_controller, test_isolated_adb_lease,
test_owned_target_contract, test_android_process_client_v4,
test_original_author_restart_proof, test_original_author_model_proof,
test_original_author_prompt_provenance, test_original_author_diagnostic,
test_original_author_stream_admission, test_original_story_verification,
test_owned_restart_contract, test_android_process_client_v5,
test_original_author_restart_controller.

Result SHA256 `abd8b3062b73d5421e2f2f9b831a6457751532cb4488e9e752a4729f5e85ae16`;
request `15b624ed56732bc05391774d2998ba93bf81339104aa354f0cedcb77ee82cfd1`;
helper `1856d9df68c6ae6db912615585af8e8b3f94f694df6818799872b90eedbee85b`.
These private files, raw streams and synthetic graphs remain on D:.

The677 include529 earlier transport/owner checks,104 original AUTHOR/restart
checks,28 restart-contract cases,10 SDK5 cases and6 controller/build cases.
The full controller fixture uses the actual fixed classes, wire framing,
create-only third claim and deep proof/collection/JUnit readers. Native owner,
socket responses and bulk model/APK input IO are explicitly simulated through
exact input-pin seams; it does not transfer2.59GB, invoke a model or run Android.
Separate SDK5 tests exercise actual binary wire handling with small original
bytes, cancellation, post-proof failure and uncertain close.

## Preserved discoveries

| First failure | Correction and distinct verification |
| --- | --- |
| Unchanged legacy97:1 failure/9 errors after shared refactor | Restore instrumentation-only claim classification; same97 pass, including current reader |
| Original15 pure contract cases:wrong C basename accepted by shape gate | Add early basename refusal; same15 pass; full live byte/path gate was already strict |
| Original24 complete graphs:7 TypeErrors | Preserve values after void shape/integer checks; unchanged24 pass |
| New collection positive:fixed recipe order disagrees with sorted JSON | Use protocol constant order; same positive passes |
| Duplicate import/AUTHOR rows:2 assertion failures | Enforce one-method ledger in prefix/full roster; unchanged2 subcases pass |
| Controller stderr/under-Git output:2 assertion failures | Refuse before following SDK/input/observer action; same2 pass |

Three initial full-flow fixture setup errors (guard keyword signature, synthetic
epoch, owner budget) are retained separately. Their corrections do not change a
product guard or establish a product RED/GREEN result. Later canonical-path,
borrowed-sidecar, altered-tar, invalid probe/JUnit and ELF/tool/recipe adversaries
pass. No failed captured outcome is repaired or relabeled.

## Actual native compile and limits

The first installed NDK29.0.14206865 x86_64/API35 compile passes in a finite
2,288ms owner, exit0, complete capture/cleanup and empty streams. Command entry:
`python -B scripts/build_android_author_process_probe.py --ndk <installed-NDK29> --output <fresh-physical-D-folder>`.
The helper source and builder are unchanged since that build. Actual Choice
source paths are retained and compared by bytes with Root, never rewritten.

ELF13,848B SHA256
`8c9408c4af7ce73d4e39dde712c291dd1d5e042e53ff407414dfa4d864d41972`;
manifest `7f3a540e38b123b202eff466861b51d339857c4fc15280ef59b9c4da2592ee40`.
It is a64-bit PIE, machine62, `/system/bin/linker64`, libc.so/libdl.so. Independent
file-only replay also checks the actual image and fixed tool recipe. The helper
has **never been executed**. The started receipt records identity only; file
consistency does not authenticate execution. The actual finite build owner is
separate measured evidence.

Pinned kernel/AOSP sources and installed-image limits are linked in the protocol.
No AVD creation/boot, service/target/device query, model copy/inference, other
emulator stop, settings change, merge or release occurred for this checkpoint.
Actual kernel/SELinux behavior, same-boot Android restart, phone/ARM64, quality,
performance and full milestone acceptance remain unqualified. The next gate is
current-source Android build plus actual-build-bound simulated result replay,
then a concrete fresh execution scope requiring applicable user authorization.

## Later approved preparation and failed initial proof

The human explicitly approved the fresh API35/x86_64 D guest,8GiB/four cores,
30-minute limit, isolated APK/helper installation, local model copy/import,
one AUTHOR attempt and passive restart. The received reply is bound separately
to the original proposal; pending proposal bytes are never overwritten.
Actual host admission passes with29,887,803,392B available memory and
22,689,005,568B available commit, above the unchanged floors. SDK guest creation
completes in3,804ms with exit0/known child cleanup; preparation and final immutable
checks pass. SDK stderr is recorded as645B, not an empty-stream claim. The guest
is prepared but **never booted** in this attempt. The existing local model is
rehashed successfully; no model copy or inference occurs.

At the frozen `d05143d5` source/build, the first isolated target owner fails.
Parent supervision ends in6,977ms, exit1, known capture/cleanup and empty streams.
The created private ADB process is terminated/waited and its handles/pipes/capture
close; the nine created-resource closure flags are true. Six guest flags remain
false because no guest was created. Do not report all15 shutdown flags passing.
No devices-list proof, boot claim, launcher, guest, ready descriptor, SDK session,
model transfer/import, AUTHOR or passive restart is produced.

The captured complete version reply is `OKAY00040029`. Both original v2
observation/table validators pass with their raw state bytes unchanged. Exact
closed proof replay rejects **budget:3,219ms exceeds3,000ms**. The worker's generic
`proof` result and parent's generic `owner` result do not identify TCP state as
the rejecting predicate. Full proof SHA256:
`0e957c7825ea97c2877bb2504f6c99557da824f2e0988a8cc21c5c90d0844ff8`.
The final post-response bracket and checked close are present; existing data
cannot distinguish final-bracket versus cleanup-tail expiration. No original
stage durations are invented, and no live retry is made to seek a favorable
measurement. Independent read-only replays agree.

Exactly three subsequent unchanged host-only input-validation calls take
466.35ms,503.98ms and538.32ms, with2,078 source pins unchanged and44 unique assets
totaling70,258,426B. This is current-host cost evidence, not causal attribution
to the earlier3,219ms. The source has five whole-target validations per initial
exchange, including two outside its three mandatory cryptographic brackets.

The focused implementation at `48aa2965` retains full source/tool/auth/identity
checks before connect, before send and after response. Only redundant outer
checks become held-identity/clock/stop/capture/auth checks plus the small server
admission binding. The three-second total, frames, raw observations, closure
checks and readers remain unchanged. The first original nine synthetic guard
tests fail five cost/count/sequence assertions, with no resource-leak claim;
the same nine pass after the fix. The complete-response3,219ms and exact3,000ms
refusals remain required. The test cost model is synthetic and does not label
an unmeasured stage of the original attempt.

New-source integrated/build checks and explicit metadata rebinding are required
before further live use. Preserve the failed owner namespace and the prepared,
unbooted guest; do not overwrite old grants, source cohorts, proofs or claims.
The original approved first boot/import/AUTHOR scope has not been exercised.
Actual Android restart, model execution for this packet and full milestone
acceptance remain unqualified. The other emulator, shared ADB service and system
settings are untouched; no merge, release, private upload or weight download.
