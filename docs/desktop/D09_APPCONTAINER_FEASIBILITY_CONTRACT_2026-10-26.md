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
