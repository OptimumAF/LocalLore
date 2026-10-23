# Independent warm exchange adversarial checks

Task scope: M01.02/M01.04/M01.05, claim on ticket #5. The reviewer owns only
`benchmarks/test_android_warm_review.py` and this report in a separate worktree.
The coordinator owns controller fixes and integration; a separate SDK contributor
owns Java fixes. These checks use synthetic requests, results, metadata and
injected exceptions. They do not use ADB, model weights, private stories or a
physical device, and do not qualify inference quality or performance.

The initial controller source (uncommitted snapshot SHA-256
`bb3214c405be1441b14af4a97a0c7a37fcd37b14db7d31305346cf30a74aec6d`)
failed eight assertions across 32 independent test methods:

- A completed terminal with `warm_cancel_observed=true` was accepted, both by
  the terminal parser and by the coordinator's commit gate.
- An adapter's private exception, arbitrary stage and unknown SDK fields were
  copied directly into the public report.
- A defective oracle's director request in the narrator position reached the
  adapter and then the commit call; the coordinator relied on the normal
  adapter to validate role order.
- Unknown cleanup of a failed initial stop client was erased by a subsequent
  successful stop, yielding `adb_cleanup_complete=true`.
- Unknown cleanup of a failed package identity client during publication was
  similarly erased, permitting deletion of the owned directory.
- A valid preflight rejection with `director=null` was classified as oracle
  failure before the preflight result was inspected.
- A request transfer that exhausted the turn budget still released the
  instrumentation launcher before checking the budget again.

Read-only cross-language inspection also found the host publishing an owner
marker with a newline while Java required exact bytes without a newline.
The Java exchange initially omitted the legitimate `cancel.partial` file from
its known names and did not reject a foreign result that appeared after
construction but before its authorized publication. Those observations were
sent to the respective owners; they are distinct from synthetic test failures.

The tests also exercise strict nonce and integer-step identity, duplicate JSON
keys at nested levels, UTF-8 and byte limits, deeply nested input, worker result
limits, exact native owner counters, duplicate instrumentation results, role
ordering, individual cleanup proofs, deadline exhaustion during validation,
launcher join before package stop, preservation of files when launcher cleanup
is unknown, cancellation before validation, and idempotent session disposal.

After the first corrections at `ae717f0`, the original 32 methods passed.
Two additional synthetic contradictory-proof cases still failed: completed
owners accompanied by `cleanup_requires_process_termination=true`, and a host
`cancel_requested=true` that had not yet been observed by the SDK. The coordinator
now rejects both as independent barriers to commit.

Final reviewed controller: `9ac04b2`, source SHA-256
`272b5673ee82afa18ec56446a29f28def9d1616a9a07db36b1e4869bdecc610e`.
All 34 independent warm test methods pass. The broader command
`python -m unittest discover -s benchmarks -p 'test_android*.py' -v` passes all
86 methods (34 new warm methods plus 52 existing control/Android methods).
`python -m py_compile benchmarks/test_android_warm_review.py` and
`git diff --check` also pass.

Read-only inspection of the revised Java flow found the exact marker bytes,
allowed zero-length `cancel.partial` and early foreign-result checks corrected.
The SDK contributor owns its JVM build and tests; the coordinator owns actual
emulator/real-model experiments. This reviewer ran neither. Passing these
synthetic checks does not prove device cancellation or native disposal, and
does not explain any historical emulator transient. No remaining concrete
defect was found in the reviewed scope; this is not owner acceptance or a
milestone completion claim.
