# Same-boot original AUTHOR restart controller v1

Refs #13 (M09.06), #14 (M10.02). Implementation contract; live execution needs
fresh, concrete authorization. Existing guest/model/SDK4 claims remain spent.
No model/runtime/dependency change or second inference backend is introduced.

## Profiles and source ownership

Root owns shared pure contract/closed-reader internals, new
owned_restart_contract.py/android_process_verification_v5.py and this document.
Native/client specialist owns shared owned_target_owner.py/
android_process_client_v4.py internals and fixed owned_restart_owner.py/
android_process_client_v5.py adapters. Workflow specialist owns
original_author_restart_controller.py, native/android_author_process_probe.c
and scripts/build_android_author_process_probe.py. Adversaries own three new
contract/client/controller tests. Separate D worktrees; no overlapping writes.

Share mechanisms through explicit private profile parameters/fixed concrete
classes, never global monkeypatch, metadata retagging or caller-supplied verifier.
Old public functions/CLI/default class remain strictly v1/SDK4. New wrappers
select their fixed module/type and reject old inputs. Old recorded source
cohorts remain in Git/private recovery; no historical observation is normalized.

New target protocol `owned-emulator-restart-target-v1`; SDK protocol
`sdk-owned-restart-v1`, client version5, `sdk-session-v5.json`; socket proof
protocol `owned-restart-socket-proof-v1`. Ready/running/owner/capture filenames
otherwise stay unchanged under a fresh root, but tags/source sets differ.
Boot claim is `owned-restart-boot-claim-v1.json`. Fixed fresh guest root:
`D:/Dev/Experiments/LocalLore/2026-10-29-author-restart-controller-v1/avd-v1`.
Same15937/5592/5593 ports,8GiB/four cores, API35/x86_64,1700s owner ceiling and
1800s approved maximum. No existing AVD is reused/reset/moved or booted here.

The shared core exposes a private frozen ContractProfile/Contract implementation;
legacy public wrappers construct only the original profile. New fixed module
exports the same validate_admission/running/session/operation/proof/query/ready/
claim/client-record/source_bindings/revalidate_inputs API plus constants.
Profile fields include protocol tags, client_version/session_file/owner_script,
guest_root/boot_claim_file/source_names, instrumentation map, artifact keys.
All nested validation calls must carry the same selected profile; no fallback.
New module also exposes `instrumentation_kind(argv)` and `claim_record(...)`.
Legacy results/claim keys remain exact; new claims add only `prerequisite`.
The restart executable closure has23 benchmark files, plus an optional package
initializer when present. The C source and builder are separately bound build
inputs; the former must be the current Root Git source, not a basename match.

New `LiveOwnedRestartTarget` reuses the held native owner implementation with a
fixed restart contract. New `OwnedRestartSdkCapture` reuses the binary wire
implementation with exact fixed lease type, restart contract and v5 verifier.
Subclass/plugin/caller-supplied boolean authorization must not replace these.
Worker/parent fixed CLI wrapper selects the same profile before input validation
or side effects. Full source closure includes every new executable validator,
controller and owner adapter in addition to the prior dependencies.

## New artifacts, recipes and claims

Artifacts retain build/product_apk/test_apk/model/probe, adding process_probe
(binary <=64MiB) and process_probe_source (the exact new C source under Git).
Build/transfer gates bind current source/APKs/helper/toolchain; large input
hashing remains outside streaming liveness polls. No model weights enter Git.

Existing bounded recipes remain; new recipes stage the bound process probe with
dd at `/data/local/tmp/locallore-author-process-probe-v1`, hash it, chmod700,
then invoke that exact path with `--boot` or `--snapshot PID UID`. PID is decimal
1..2147483647; UID decimal10000..2147483647. No arbitrary executable/path/script,
signal/kill command, shell recovery, model input or OS setting is exposed.

Instrumentation map is exactly the two original import/AUTHOR methods plus:
`org.locallore.app.OriginalAuthorRestartInstrumentedTest#recordsOriginalAuthorAfterExternalRestartWithoutInference`.
Import/AUTHOR/restart claims are separate create-only files in claims-v1. New
claim fields are version/protocol/admission_sha256/kind/operation_sha256/caller/
prerequisite. Import/AUTHOR require null prerequisite. Restart requires the bound
`admission.root/restart-prerequisite-v1.json`, deeply verified before dispatch.
A refused/dispatched attempt stays spent; no retry/favorable rerun.

## Native process observation packet

First-party C helper has no signal/kill/model/file-mutation operation. It reads
kernel boot ID and, in snapshot mode, opens a PIDFD for only the explicit PID,
reads that process's UID/start ticks, polls it without waiting, and closes its
own FD exactly once. ESRCH is absence; unsupported syscall, permissions, races
or uncertain close are refusals, never absence. Actual native errno is retained.
A wrapper exit0 means a complete packet was emitted, not semantic acceptance.
Malformed argv fails; output <=4096B. NDK29 cross-build uses installed tools and
new physical-D output, never provisions a dependency or boots a guest.

Exact JSON keys:
version, protocol, mode, boot_id, pid, expected_uid, observed_uid, start_ticks,
state, pidfd_opened, poll_revents, pidfd_closed, proc_opened, proc_closed, error, errno.
Version1/protocol `android-author-process-probe-v1`; canonical lower-case UUID
boot_id. Mode boot/snapshot. Boot requires null pid/uid/ticks, state boot,
pidfd_opened false/poll_revents null/pidfd_closed null/error null/errno0.
Procdir FD acquisition precedes PIDFD and proc metadata uses openat on that held
proc inode, preventing a recycled numeric PID from retargeting pathname reads.
proc_opened/proc_closed preserve that resource separately; qualified alive/exited
requires true/true. Absence permits false/null, or true/true when ESRCH occurs
after opening the proc directory.
Snapshot pid/expected_uid are the validated argv. State absent requires errno3
(ESRCH), observed_uid/start_ticks null, no FD opened/poll/close, error null.
State alive/exited requires observed_uid==expected_uid, positive start_ticks,
pidfd_opened true, pidfd_closed true,error null,errno0; alive poll_revents0,
exited POLLIN and/or POLLHUP (1,16,17). Any other result refuses. Refused packets
preserve native observations/nulls and a fixed error category; never fabricate
successful fields. No retry of an uncertain numerical FD close.
Refused error categories are exactly pidfd_unsupported, pidfd_permission,
proc_permission, proc_race, uid_mismatch, io, close and malformed. Nullable
observations remain nullable; a root UID observed during a mismatch is retained
as0, never rewritten to the requested application UID.

## Controller and prerequisite

Controller uses only the fixed v5 capture, source-bound new owner and explicit
admission+running+build bindings. Verify current source and artifact hashes,
absent package pair, guest profile/user0/resources, then stage/install APKs and
helper, verify binary65B probe/full local model hash, and run exactly one import
and one AUTHOR. Original raw JUnit/native/diagnostic validators remain required.
Collect original bytes/rosters with bounded run-as SHA/tar and post-hash checks;
never reconstruct native output. Preserve every failure and both model copies.

Observe helper --boot before model operations. After completed original AUTHOR,
recheck package UID/APK identity, observe its declared PID/UID, force-stop only
APP user0, then observe that exact PID again. Boot IDs must all equal; after
state must absent or exited. If exited, any observed before start_ticks must
match. Permission/unsupported/race is unqualified. Record whether the original
process was already terminal; do not claim an explicit kill caused a death when
instrumentation had already ended it. Never signal by numeric PID.

Prerequisite exact fields:
version,protocol,admission,running,session,caller,import_proof,author_proof,
author_artifacts,import_instrumentation,author_instrumentation,boot_initial,
probe_before,force_stop,probe_after,package_checks.
Protocol `original-author-restart-prerequisite-v1`. All file values are exact
{path,bytes,sha256} bindings; author_artifacts is the original17-name map;
package_checks binds the current product/test UID+APK getter records. Selected
client records must pass full v5 source/session/context/raw proof replay and
exact recipes. Order: boot_initial < import < AUTHOR < package checks <
probe_before < force_stop < probe_after. Identity/session/admission/source/UID/
APK/boot must agree. Baseline import/AUTHOR proofs use the unchanged current1.1
reader. A record with the third method cannot be a prerequisite witness (acyclic
validation). Metadata alone is not execution authentication.

Closed replay also derives each local artifact path from session.root and
replays its qualified SDK listing, pre-hash, binary tar and post-hash records
between the corresponding instrumentation and the next phase. Exact names,
UID, bytes, hashes, non-link regular tar members and order must agree. An
otherwise valid proof borrowed from another capture cannot qualify. Check the
current23 source files, current C source and admitted Python bytes before and
after prerequisite replay. The file-only reader does not call a DLL-location,
process, socket, SDK or target API. Live owner guards separately bind the actual
loaded runtime and held native resources.

After publishing the verified prerequisite atomically, consume the restart
claim and invoke the one passive method. Collect its six sidecars/proof, require
original validate_restart and JUnit, then --boot again with the same ID. Verify
complete v5 client roster/proofs and final lifecycle record. Resource closure
and owned guest-before-server stop remain separate mandatory results. SDK/file
failure poisons the case; do not use later calls to repair a captured failure.

Controller `run(admission_binding,running_binding,build_binding,output_root)`
constructs only the fixed concrete restart owner/capture. It grants no authority
and creates no outer process; a separately admitted finite owner is required.
Request exact11 keys: version,protocol,admission,running,build,root,head,sources,
python,controller,seconds. Version1, protocol
`original-author-restart-controller-request-v1`, seconds1200. The request and
result filenames are `request-v1.json` and `controller-result-v1.json` under
the new output root.

Result exact16 keys: version,protocol,request,session,prerequisite,
restart_instrumentation,boot_final,restart_proof,restart_artifacts,client_count,
outcome,phase,reason,observer_handles_closed,feature_acceptance,elapsed_ms.
Protocol `original-author-restart-controller-v1`; outcome completed/refused;
feature_acceptance false. Phase admission/install/binary_probe/model_transfer/
import/author/death/restart/collect/completed. Reason null/checks_failed/deadline/
resource_uncertain. Evidence pins remain null until observed; restart_artifacts
always has the six original names, with nullable pins after a failure. Preserve
partial files and unknown closure rather than inventing completion.

Build admission has12 exact keys: version,scope,head,sources,compiled,build_files,
fresh_lint_files,apks,counts,independent_build,independent_lint,process_probe_build.
Scope `owned_restart_android_build_admission_v1`. Current source/compiled counts
are derived, with588 actually executed JVM tests in58 reports, fresh analyzer
work, both audited APKs and qualified finite build owners. The native build
manifest has17 exact keys: version,scope,ndk_revision,target,source,builder,tools,
command,environment,request,started,owner,compile,binary,elf,passed,
feature_acceptance. Scope `android_author_process_probe_build_v1`, NDK29.0.14206865,
target x86_64-linux-android35. Retain actual compiler-source/output paths; compare
cross-worktree source bytes explicitly rather than rewriting provenance.

## Acceptance and limits

Host tests cover exact profile separation, typed recipes, claims/prerequisite
binding/order, malformed/refused native packets, boot changes, UID/PID reuse,
partial/cancelled/late/source-changed streams and unknown cleanup. Preserve all
old negative assertions. Real NDK build proves compilation/package identity,
not kernel PIDFD/SELinux behavior. Verify official primary sources and preserve
compatibility limits. No physical-device/ARM64/performance/quality claim follows.

Only after source/build/host checks pass, prepare a concrete reviewable fresh
scope for user approval. Until then NO AVD creation/boot, service/target/model
call or copy. Existing other emulator/system settings remain untouched.
