# D04 sealed Node compile attempt v1

Refs #25 (D04.01/.02/.04), #31 (D09.03/.05) and #21.
This private entry composes the Windows output-root lease, held object
reader, compiler host, supervisor and candidate A observation. Import
does no I/O. It has no application command, runtime profile loader or
retry path.

## Sealed profile and assembly

The future admitted build must create one self-contained
`worker_artifact_compile_attempt_v1.mjs` on physical D:. Bundle this
module, one literal reviewed profile, the independently admitted input
and writer checks, and a fixed bootstrap. Use the already pinned
esbuild version in the desktop dependency lock, Node ESM format, and
allow only Node built-ins as external imports. Review the bundle
inputs and exact output before holding it in the native parent.
No module initializer may perform experiment I/O or start a child.
No bundle or fixture was created for this source slice.

The exact private profile contains config, authority, environment,
node, helper, entry, evidenceRoot, outputParentIdentity, outputMaxBytes,
spend, writerPolicy and namespace. Use the existing recipe config and
authority. Node and helper are exact path, bytes and SHA-256 pins.
Entry is the intended absolute path of the final bundled file.
Environment is windows, path, include and temp. PATH and INCLUDE
are ordered canonical semicolon-separated path lists. All project
paths are on D:. The target, temp and evidence roots are distinct
and do not overlap the protected input directories. The output
parent identity uses the Node filesystem identity expected by the
existing root lease.

`workerArtifactCompileAttemptScopeV1(profile)` gives the exact scope
for the native parent plan. The scope binds canonical profile fields
and the derived attempt/recipe/baseline/closure/grant context.
It omits the entry file digest. An entry cannot include its own hash.
The native parent pins the final bundle separately. Keep all other
bindings acyclic too. The retained pre-existing spend, namespace and
writer policy records may bind the base attempt. A final scope or
bundle binding is a separate record and must not be embedded as
a digest input to itself. The authority and independent guard checks
are not generated from placeholder strings or future expected results.

The fixed bootstrap calls `runWorkerArtifactCompileAttemptV1(profile,
owner, signal)` once. Its owner has exactly two private methods,
`check(request, signal, admitted)` and
`excludeWriters(request, admitted)`. The last argument is the frozen,
verified scope, context, ready hash, ready record and normalized profile.
Check must produce fresh, actual #408 input and storage checks. Exclusion
must independently confirm outside-writer exclusion while the Node
observer is still alive. It may not substitute a configured digest or
wait for outer Job zero while that same observer is alive. The native
parent verifies the outer Job after Node exits. Do not interpret the
parent's closed unused stdin as cancellation.

## Verify before creating output roots

Require the pinned Windows x64 Node 24.22.1 entry with zero script
arguments or runtime flags and without options or coverage in the
environment. Check the actual executable, argv entry, module URL,
SystemRoot and private temp. The inherited ready locator must equal
the exact derived `parent-ready.json` under the admitted evidence
directory. It supplies a locator only.

Read the actual ready file (at most 4,096 bytes) and executing entry
(at most 2 MiB) using ordinary named paths, held positional reads,
one-byte EOF probes, known closes and stable held/named identities.
Reject malformed UTF-8, oversized input, duplicate keys, added fields,
noncanonical record order or bytes, different parent/current PIDs,
an unexpected Job flag/count, mismatched grant/context, or different
actual entry length or hash. Compare the ordered Node and helper
pins with the independently pinned profile. Native file IDs must
be distinct, nonzero identifiers on one volume. Treat native IDs
as native facts, separately from Node's dev and ino values.

The same exact ready hash can bind both the Job and the held helper
because the actual native record describes both. The separate
namespace and writer policy remain external obligations.
Check the evidence directory is unchanged across those reads and
verify the output parent using the Node identity before composing
the production factories. Cancellation is forwarded to the existing
observation once created.

## Result and verification

Return the actual #408 report and retention flag as
`{version:1,kind:'compile_attempt_result_v1',scope,parentReady,report,retained}`.
The fixed bootstrap may write one compact bounded result to stdout for
the native parent. A pre-ready refusal must produce a bounded failure
without creating any candidate roots. The parent retains startup and
closure evidence even if Node dies before a terminal record exists.

The source-only FIRST file contains twelve in-memory groups for profile
and ready validation. After separate admission, run it with the exact
pinned Node 24.22.1 on its fixed source path. Expected stdout is one
compact JSON line with kind compile_attempt_first_v1 and groups 12.
This does not exercise native readiness I/O, Win32 Job behavior, the
helper, compiler or actual outside-writer checks. The bundle and
native entry still need a bounded synthetic qualification, then a
separate real compiler admission. LINK, artifact adoption, model
execution and desktop qualification remain separate.
