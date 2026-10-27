# D09 AppContainer feasibility: Rust-first frozen contract

Refs #31 D09.02/.05/.06. Base accepted `3f75b5d6`. SOURCE ONLY at freeze;
no compile, child, network, profile or ACL operation has been executed by author.
This is a developer qualifier, not an app sandbox feature or an offline verdict.

## Scope and authority

The only new executable is `offline-qualifier`, required feature `dev-harness`.
It accepts no arguments in parent mode, or exactly `--self-canary` internally.
The package's default run target remains the desktop application; this second
feature-gated executable does not make existing app run commands ambiguous.
It launches only a newly copied image of itself. No arbitrary executable, shell,
path, port, script or remote execution interface is provided. Non-Windows exits
Unsupported. Existing `windows=0.62.2` APIs are enabled by feature forwarding
inside dev-harness only; no new package/version/checksum or production handler.

The parent derives a fresh UUID and a create-only evidence directory under its
temporary directory. It creates a unique `locallore.offline.<uuid>` profile with
zero capability SIDs. AlreadyExists is a failure, never adoption or cleanup of an
existing profile. Managed profile storage is never opened or pinned. A separate
atomic new `fixture-<uuid>` directory is created in the same pinned task temporary
parent as the evidence directory; it holds only the qualifier image, one-time
challenge and tiny files. ACL changes apply only to that newly created directory and its new
contents, granting the current user, SYSTEM and exact package SID; a low integrity
label permits its intended writes. No ACL changes to ancestors, existing files,
system runtime or original model/worker files. No model files are involved.

The same copied executable runs once normally for positive control and once in
the zero-capability AppContainer. Native-only bounded stdin contains the fixed
case identity, run UUID, challenge and parent-owned listener addresses.
The canary derives the fixture from its own fixed copied executable's parent;
no path is a request field. Its exact directory component must be `fixture-<uuid>`
and its image name `offline-qualifier.exe`, on an absolute ordinary local-disk
path without parent/current components. It derives the package SID from the
fixed profile moniker and validates the bounded marker's exact run UUID, SID
and challenge. Its actual token must independently match the expected case/SID.

## Frozen checks

1. CreateProcessW uses an absolute fixed application name and fixed command line,
   CREATE_SUSPENDED, an explicit inherited anonymous-pipe handle list, and an
   owned Job with KILL_ON_JOB_CLOSE and no breakaway flags. Assign the Job before
   resume. AppContainer launch supplies SECURITY_CAPABILITIES with the created
   package SID and no capabilities. It adds no internet/private-network capability,
   loopback exemption, policy change or permissive fallback.
2. Before resume, the parent reads the actual child token. Baseline must not be
   AppContainer. Boxed must be AppContainer, match the exact package SID and have
   zero capabilities. The child independently reports the same facts. Missing,
   malformed or unavailable token information is failure, not an assumed default.
3. Both cases round-trip the bounded challenge over inherited anonymous pipes,
   read its marker, create a fixed tiny case file and let the parent read it back.
   A successful network denial with unusable local I/O is not feasibility success.
4. Enumerate local IPv4 adapters and deterministically select an up nonloopback
   address owned by this host. Bind one private TCP listener and UDP socket on
   that address with OS-assigned ports. There is no external endpoint. Baseline
   must exchange the exact one-time challenge/echo through BOTH same endpoints.
   Listener threads retain bounded observations and stop/join explicitly.
5. Boxed TCP connect and UDP send_to must return explicit WSAEACCES (10013),
   with no boxed challenge received. Timeout, refusal, unavailable interface,
   failed UDP bind, generic I/O error or no received packet is not proof of the
   requested policy denial. Loopback-only controls are not substituted.
6. Each actual child must reach a known terminal state. A finite deadline requests
   termination of only that owned child/Job and then positively waits. Job active
   process count must become zero; pipe/listener threads are joined. Unknown
   cleanup is preserved as unknown and prevents a passing result or profile deletion.
   DeleteAppContainerProfile is called only for this freshly created profile,
   outside the AppContainer and after known quiescence. Deletion failure remains
   failure; there is no recursive deletion of a computed filesystem target.
   `profile_delete_api_succeeded` records only a successful API return.
   `profile_storage_absence_checked:false` explicitly records that forensic
   absence of Windows-managed profile storage was not independently measured.

Evidence is create-only, bounded JSON and exact protocol stdout/stderr, retained
outside the profile before its deletion. Failed evidence is never overwritten or
repaired. It records phase, actual API/error outcomes, child token observations,
file/pipe/network checks, listener counts and cleanup/profile-deletion outcomes.
Raw local paths/addresses remain private; public reporting is sanitized. No
elapsed interval is a universal OS cleanup guarantee. Endpoint selection or
policy failures stop this attempt; no favourable automatic rerun or fallback.

## Deliberately not established

No WebView2, Tauri IPC, app rendering, model import/inference, approved llama
worker, DNS, IPv6, brokered service traffic or complete app offline journey runs
in this first gate. A self-canary is not an approved worker. Ordinary child token
inheritance is documented, but this does not prove all Chromium broker/network
processes inherit the proposed restriction. A later separately frozen gate must
observe actual app/WebView/worker tokens and useful file/IPC/render behavior.
COM/UDF/runtime incompatibility is a possible measured failure; never fix it by
granting network, disabling Chromium sandboxing or altering system ACLs.

This is runnable feasibility work, not a demonstrated external blocker. A failed
WebView follow-up can justify a separately admitted isolated environment; no
firewall, global network, CheckNetIsolation, OS feature, security alert or package
approval settings change is authorized by this source allocation.

## Root-only first qualification commands (UNRUN)

```text
cargo build --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --bin offline-qualifier --jobs 1 --target-dir <owned-target>
<owned-target>/debug/offline-qualifier.exe
```

Root records first compile and behavior failures separately, strict lint/format,
normal graph/hook exclusion/restoration and exact source/executable hashes. The
first actual process needs a separately reviewed execution slot; none ran here.

Primary sources checked during design: [AppContainer launch](https://learn.microsoft.com/en-us/windows/win32/secauthz/implementing-an-appcontainer),
[legacy Win32 children](https://learn.microsoft.com/en-us/windows/win32/secauthz/appcontainer-for-legacy-applications-),
[profile creation](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-createappcontainerprofile),
[profile deletion](https://learn.microsoft.com/en-us/windows/win32/api/userenv/nf-userenv-deleteappcontainerprofile).

## Pre-execution correction: pinned identity and complete drain

Independent source review of `d8389418` found that metadata-only path checks
did not pin identity across path-based ACL/copy/launch, and profile deletion
did not explicitly require each child's pipe threads to have drained. No
qualifier execution was authorized or performed before this correction.

The replacement private `create_owned_directory` pins ordinary local-disk
ancestors without write/delete sharing, then atomically creates ONE generated component relative
to the pinned parent with cached `NtCreateFile`: FILE_CREATE, directory,
open-reparse-point and synchronous mode. Both return status and IO_STATUS_BLOCK
must report successful new creation. The returned handle must identify an
ordinary directory. Existing directory/file/reparse collisions refuse; no
existing object is adopted. ACL uses SetSecurityInfo on this exact new handle.
Existing ancestor handles request read-attributes/traverse/synchronize only;
no ACL or data mutation occurs there. Writable directory handles already held by
another process conservatively refuse; no relaxed-sharing fallback or UNC path
is used. The newly created root also denies later writable directory opens,
including the access needed to replace its reparse data.
No path-named ACL mutation remains. WDK/System_IO feature forwarding stays
inside dev-harness, using the same windows0.62.2 package and unchanged lock.

The source executable is opened through ordinary pinned ancestors, read-only,
without write/delete sharing. Its sole copied destination is create_new. A
metadata-only no-delete identity guard spans closing the writer and obtaining
the final read-only no-write/delete pin. Matching native file identity plus
bounded full SHA256 comparison with the still-pinned self image is required
before launch. Writer interference, replacement or existing destination fails.
Self image is capped at256MiB; this admits no model/worker-copy input.

All ancestor/root/source/executable pins remain held through launch, child/job
and pipe/listener drain, profile-deletion attempt and final create-only evidence
write. Evidence has its own atomic new pinned directory outside the profile;
its final write never follows an unpinned root. Existing parent ACLs are never
changed. If holding pins prevents the Windows profile-deletion API, that remains
a measured failure; this source adds no permissive drop/retry fallback.

Deletion eligibility explicitly checks every attempted child's positive known
process cleanup AND threads_drained, as well as listener drain. False/unknown
flags preserve profile/evidence. A terminated process alone does not prove pipe
drain. No profile enumeration or computed recursive deletion is introduced.

The separately frozen Windows source tests use only new synthetic fixture
directories: held-root rename refusal; create collision with outside ACL/byte
sentinel unchanged; existing reparse-parent refusal (explicit opt-in symbolic
link privilege, never a silent pass); self-copy collision preservation; and
pipe/listener/child deletion decision negatives. They are UNCOMPILED/UNRUN.
Root must independently re-review, compile and qualify these before the fixed
self-canary runs. A source test is not an actual race/ACL/network measurement.

## Pre-execution correction: fixture outside managed profile storage

Independent source review of `00d2630f` identified that keeping ordinary-directory
and image guards under `GetAppContainerFolderPath` conflicts with the Windows
deletion API's instruction to close profile-storage handles before deletion.
The previous section preserves that intermediate design's safety constraints;
this layout replaces its use of managed storage. The source now calls neither
`GetAppContainerFolderPath` nor any filesystem helper on a derived profile path.

The fixture is an atomic new SID-ACL directory in the same captured task temporary
parent as private evidence, with distinct generated sibling names. Neither one
is inside Windows-managed profile storage. The canary uses only its own fixed
image parent and exact fixture/run UUID, derives the expected package SID from
the fixed profile name, checks the run/SID/challenge marker, and independently
checks its actual token. No caller-supplied path or new executable choice exists.
All ancestor/source/image/fixture/evidence pins remain held through final writes;
there is no guard drop, relaxed sharing, overwrite or deletion retry fallback.

The strict child/pipe/listener deletion eligibility predicate is unchanged.
Deletion success is renamed `profile_delete_api_succeeded` and explicitly paired
with `profile_storage_absence_checked:false`. A successful API return is a finite
observed result, not an independent claim that every profile-storage byte is gone.
Private synthetic fixture/evidence directories remain retained; this adds no
profile enumeration, recursive filesystem deletion or unrelated cleanup.

An additional Windows source-test group checks exact fixed self-image/fixture
location, run mismatch, invalid/relative/UNC/traversal paths and distinct
run/SID/challenge marker bindings. Existing frozen safety assertions remain.
Author verification is only `git diff --check`; all formatting, compilation,
Windows tests, token/profile/ACL/network/child APIs and actual qualification
remain UNRUN. Root must independently review this final layout before execution.

## Required outer image identity pin

Final independent source review of `68e2262d` found no additional concrete
source blocker, with this execution-boundary condition: before process creation,
the Root-owned fixed launcher must open the exact qualifier executable read-only
with read sharing only (no write/delete sharing), hash that held handle, and keep
it open through the qualifier's complete terminal observation. Require the
result's `copied_self_sha256` to equal that pinned source hash. The launcher must
also enforce its fixed executable/empty argument list, bounded local output and
deadline, and preserve failures rather than interpreting absence as success.

`current_exe()` followed by an open inside an already running process cannot by
itself prove its pathname was not replaced before that open. Internal pins and
copy comparison cover their actual opened objects; the outer pre-launch pin
closes the earlier boundary. This is a qualifier execution protocol, not a new
renderer command, generic app launcher, arbitrary execution hook or claim about
hostile OS compromise. Compilation, Windows safety tests and actual canary
execution remain prerequisites; source review is not runtime evidence.

The reviewed outer protocol also pins every ordinary local-disk ancestor of the
fixed image, working directory, task temporary and evidence directories before
creation or launch; no reparse traversal or relaxed-sharing fallback is allowed.
Generated evidence and proof directories stay pinned through final writes.
Proof reads are capped before allocation, and bind the exact canonical run UUID,
integer version and copied-image hash. Exceptional paths still terminate/reap
only the owned parent and join bounded readers; uncertain internal child/profile
cleanup is recorded as unknown, with no fallback profile deletion.
The fixed polling deadline rejects late completion even if the parent has exited.
Process creation itself is explicitly not preempted by that polling deadline.

## First actual attempt and bounded diagnostic correction

At clean `30b2b063` the qualifier builds. Its test-only descriptor helper first
failed compilation on distinct Win32/UTF16 error types; the corrected helper at
`72c0c2aa` passes four default safety tests and the separately explicit original
symlink test. All-target/all-feature Clippy passes after building the isolated
checkout's missing normal frontend prerequisite. No dependency download or
privilege/system-setting change was used. The actual outer Python is3.14.7;
previous historical Python versions do not describe this command.

The first fixed native attempt at unchanged `72c0c2aa` fails its ordinary
positive control: the baseline child exits1 before a file/network observation.
The immediate Job snapshot reports one active process despite the signaled child.
Cleanup remains unknown, so the unique profile is retained and the boxed case is
unattempted. Original proof, source/image hashes and outer positive parent-reap
record remain immutable. This is not network-isolation or full-app success.
The missing child stderr prevents diagnosis of its earlier error; no fixture,
stdin or token cause is inferred from that absence.

The source correction preserves one five-second total cleanup budget and still
requires an actual Job count0. It polls the owned Job within the remaining
budget, and independently waits for each reader's `is_finished()` before joining.
Completed bounded stdout/stderr is retained even if Job cleanup remains unknown;
unfinished readers remain unconfirmed. Cleanup success never changes a child
failure into a passing control. A real anonymous-pipe test covers non-EOF refusal
and capture of completed synthetic error bytes. This correction and any fresh
native attempt require their own source-attributed verification. Later cleanup
of the exact retained profile requires a separate verified ownership/absence
observation; it cannot repair the original Job/reader measurements.

## Subsequent actual failures and profile-free diagnosis, October27

These are failed feasibility measurements, not an offline qualification. The
branch now includes accepted main6f6608bf. Production renderer/default handlers,
engine, provider, storage and lock behavior are unchanged by the required-feature
qualifier. The package's explicit default-run preserves the existing app CLI.

The bounded cleanup correction atfee3cb74 captures the second baseline's actual
`Io:5` error. It positively observes Job0 after two polls, process reap and reader
drain; profile deletion reports API success. The boxed case is unattempted.
Fixed stage labels at7b34a898 narrow the same failure to reading the challenge.
At403e18cf actual parent challenge readback passes, but the child fails
`CanaryMarkerRead:ReadSmallOpen:Io:5`. No permission or sharing flags were relaxed.
Atc4f3ee3b private process-token observations show the same user, zero restricted
SIDs, medium parent integrity and low ordinary-child integrity. That attempt
also confirms drain/API deletion and never reaches the boxed case.

The six default file/ACL/pipe/deletion safety tests pass. The original real
symlink test separately passes when explicitly selected; one mistyped filter
selected zero tests and is preserved as noncoverage. A file-only ordinary and
verbatim-path challenge test passes without creating a profile or child.
Strict qualifier Clippy and binary builds pass at their separately recorded
source revisions. Compiler success is not a successful feasibility control.

An independently reviewed fixed read-only observer verifies original proof,
marker and full copied-image hashes before querying labels/DACLs through pinned
handles. The old fixture/image/marker have low no-write-up labels; ancestors
have no explicit mandatory label. User/system/package allow rules and ordinary
nonencrypted file attributes are observed. These facts do not explain or waive
the low child's access denial. Private user SIDs/absolute paths are not published.
Windows documents that a new process uses the lesser of caller and executable
integrity; this explains the low executable's process level, not the failed
marker access. [MIC](https://learn.microsoft.com/en-us/windows/win32/secauthz/mandatory-integrity-control),
[label query rights](https://learn.microsoft.com/en-us/windows/win32/secauthz/security-information).

### Fixed test-only ordinary low-integrity probe

The ignored unit-test parent copies only its own test executable to a new pinned
fixture. It derives a SID for the fixture ACL/marker but creates no profile.
Its only child argv selects one fixed ignored libtest case. The child derives
its fixture from its own exact image/UUID and canonical bounded stdin. The
production argv/parser/positive-control criteria remain unchanged. Parent and
child use the same suspended/Job/token/positive-drain ownership path.

The first source draft selected an AppContainer token. Independent review
identified the mismatch with the measured ordinary baseline; that draft was
corrected before execution. A successful measurement collection cannot waive
full-read failure. Missing native identity is null, not a claimed mismatch.

At clean0cb46320, default safety tests pass6 with3 ignored cases (real symlink,
probe parent, probe child). The explicitly selected probe actually **fails**:
medium full-read control passes; ordinary low child fails all five opens with
error5: attributes, data+synchronize, read-control, extended attributes and the
unchanged Rust generic read. Actual Job0/process reap/pipe drain are confirmed.
All raw rows and the failed summary are retained before the parent assertion.

At clean40432862 a final discriminating cohort again **fails**. Direct read-only
`CreateFileW` with explicit generic-read/read-sharing/open-existing/open-reparse
flags also returns Win32 error5. It does not establish identical effective Rust
calls or a Rust defect. Actual image/CWD/fixture/marker paths agree; marker
metadata is denied too. Read-only `OpenThreadToken` reports ERROR_NO_TOKEN1008,
so there is no observed thread impersonation token. Process and pipe cleanup
are confirmed. No ACL, token state, privilege, sharing or system-setting change
was made. There is no raw-open success fallback. No profile, network, app,
WebView, worker or model was used in either unit-test cohort.

Reproducer after explicit source review, from repository root:

```powershell
cargo test --manifest-path apps/desktop/src-tauri/Cargo.toml --features dev-harness --bin offline-qualifier --locked --offline --jobs 1 --target-dir $ownedTarget win::tests::low_integrity_file_read_mask_diagnostic -- --exact --ignored --nocapture --test-threads=1
```

Use the existing isolated cache and task-owned TEMP/TMP; serialize heavy work.
Do not directly select the child test without its owned bounded stdin. Preserve
the actual nonzero result. Further unchanged canary attempts are stopped while
independent desktop work continues. The cause of the file denial remains
unresolved, and whole-app offline/renderer/worker/network gates remain open.

### Separate cleanup of the original retained profile

Root reviewed a fixed create-only one-shot helper against the original four
artifact hashes, full copied-image hash, run/source/SID binding and positive
outer parent-reap evidence. Fresh read-only process enumeration confirms the
historical PID and exact original fixture image absent, with no unresolved
qualifier candidates. SID derivation matches the recorded package. Exactly one
`DeleteAppContainerProfile` call returns HRESULT0. No profile creation/adoption,
process control, recursive deletion, unrelated cleanup or retry occurs.

The separate cleanup record does not rewrite the original unknown-cleanup proof,
recover an old Job0 observation, or qualify offline operation. Managed profile
storage absence remains unchecked. Original fixtures and evidence are retained.

Fresh package-tool checks at403e18cf pass30 package tests,1 actual cached notice
attribution test,20 synthetic reproducibility-comparator tests and the workflow
policy checker. These do not qualify a current package, new two-path build,
installation, worker/UI execution, independent license review or distribution.
Python3.14.7, Node24.22.1 and Rust/Cargo1.93.1 are the actual command versions.
All raw diagnostics stay local; no model, user story or private path is uploaded.
