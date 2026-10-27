# D09 AppContainer feasibility: Rust-first frozen contract

Refs #31 D09.02/.05/.06. Base accepted `3f75b5d6`. SOURCE ONLY at freeze;
no compile, child, network, profile or ACL operation has been executed by author.
This is a developer qualifier, not an app sandbox feature or an offline verdict.

## Scope and authority

The only new executable is `offline-qualifier`, required feature `dev-harness`.
It accepts no arguments in parent mode, or exactly `--self-canary` internally.
It launches only a newly copied image of itself. No arbitrary executable, shell,
path, port, script or remote execution interface is provided. Non-Windows exits
Unsupported. Existing `windows=0.62.2` APIs are enabled by feature forwarding
inside dev-harness only; no new package/version/checksum or production handler.

The parent derives a fresh UUID and a create-only evidence directory under its
temporary directory. It creates a unique `locallore.offline.<uuid>` profile with
zero capability SIDs. AlreadyExists is a failure, never adoption or cleanup of an
existing profile. Its profile folder is obtained through the Windows API. A new
fixture child directory holds only the qualifier image, one-time challenge and
tiny files. ACL changes apply only to that newly created directory and its new
contents, granting the current user, SYSTEM and exact package SID; a low integrity
label permits its intended writes. No ACL changes to ancestors, existing files,
system runtime or original model/worker files. No model files are involved.

The same copied executable runs once normally for positive control and once in
the zero-capability AppContainer. Native-only bounded stdin contains the fixed
case identity, profile moniker, challenge and parent-owned listener addresses.
The canary derives the fixture path from that profile; no path is a request field.
It validates the profile/UUID/challenge marker and its own copied image location.

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

The replacement private `create_owned_directory` pins ordinary ancestors
without delete sharing, then atomically creates ONE generated component relative
to the pinned parent with cached `NtCreateFile`: FILE_CREATE, directory,
open-reparse-point and synchronous mode. Both return status and IO_STATUS_BLOCK
must report successful new creation. The returned handle must identify an
ordinary directory. Existing directory/file/reparse collisions refuse; no
existing object is adopted. ACL uses SetSecurityInfo on this exact new handle.
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
