# Isolated owned ADB lease, v2

Refs #14 (M10.02 support), #13 (M09.06 support), #5 (M01.01 support).

The first live v1 attempt at source `87508ba8` failed before any smart-socket
request: ADB rejected its numeric hostname, exited3221226505, and produced153
stderr bytes. Seven readiness captures had no selected rows. The unused-port
preflight passed; the held child exited naturally and recorded capture, pipe,
process, auth and preflight closure. No emulator/device/model operation ran.
That source, admission, failure and raw output remain frozen; v1 is not qualified.

V2 is the distinct protocol `isolated-adb-lease-v2`. Its exact foreground argv
is `[adb,-L,tcp:localhost:15937,server,nodaemon]`. All other v1 schemas, byte/source
guards, transport exclusions, strict IPv4 ownership observations, fixed frames,
history provenance, deadlines, stop binding and resource rules remain unchanged.
The v2 owner refuses a v1 admission/receipt; it never reinterprets the failure.
Schema `version` and existing private filenames remain1; the protocol tag selects
this corrected command contract.

Pinned AOSP commits `1cf2f017d312f73b3dc53bda85ef2610e35a80e9` and
`9084198a2d4b0f6a0f174260fb42da33485b684d` explain the observed error.
[`socket_spec.cpp`](https://android.googlesource.com/platform/packages/modules/adb/+/9084198a2d4b0f6a0f174260fb42da33485b684d/socket_spec.cpp)
recognizes only empty host or literal `localhost` as local; numeric127.0.0.1 takes
the unsupported hostname branch. The local branch calls `network_loopback_server`
with `prefer_ipv4=true`. Its Windows
[`_network_server`](https://android.googlesource.com/platform/packages/modules/adb/+/1cf2f017d312f73b3dc53bda85ef2610e35a80e9/sysdeps_win32.cpp)
constructs an AF_INET socket with INADDR_LOOPBACK and SO_EXCLUSIVEADDRUSE. This
spelling chooses that native branch without DNS, wildcard or IPv6 binding in
the reviewed source. Exact installed-source provenance remains unproven; a new
finite v2 run still must pass every actual process/endpoint and cleanup gate.

This corrects an observed command incompatibility rather than relaxing the
listener predicate or retrying a favorable table state. The initial review
covered command parsing but missed the native listen implementation; retain
that review and its correction alongside the failed run. V2 remains host-only:
no target registration, emulator boot, SDK dispatch or model action is admitted.
