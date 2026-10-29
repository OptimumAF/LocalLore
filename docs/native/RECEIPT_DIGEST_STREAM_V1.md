# Receipt SHA256 streaming comparison

M10.02 / supporting M09.06, 2026-10-29. This host-only packet follows
[phase observations](HOST_GUARD_PHASES_V1.md) and the preserved, refused
[guarded restart run](GUARDED_RESTART_RUN_2026-10-29.md).
The complete restart gate remains refused. No guest, Android build, model,
device, shared service, production storage ledger or system setting is used.

## Implementation and contract

`receipt_avd_environment.digest(path)` retains fresh `safe_path`, a new SHA256,
binary open, complete reads and context-managed closure on every call. It now
allocates one reusable 1 MiB bytearray and hashes `memoryview(buffer)[:count]`
after each `readinto`. Positive short reads continue; only integer zero ends
the stream. Non-integer, boolean, negative and oversized counts refuse with
the fixed `invalid_hash_read` reason before hashing or retrying them.

There is no result, metadata, handle or global mutable buffer cache. All other
functions, imports and call sites retain their original AST, including source
and tool revalidation, binding/proof/query positions, ownership and deadlines.
The separate model verifier is unchanged. This does not provide an immutable
input lease or an atomic snapshot of concurrent writes.

The existing Python 3.9 API surface is retained. Official
[Python 3.9 IO documentation](https://docs.python.org/3.9/library/io.html#io.BufferedIOBase.readinto)
documents reusable-buffer reads, short reads and read errors.
[`hashlib.file_digest`](https://docs.python.org/3.14/library/hashlib.html#hashlib.file_digest)
was added in 3.11 and changed nonblocking error handling in 3.14. It is only a
comparison reference here. No dependency or interpreter upgrade is introduced.
Actual execution uses Windows Python **3.14.7**; 3.9 grammar parses, but its
interpreter has not been executed in this packet.

## Frozen experiment

The [protocol](../../benchmarks/fixtures/receipt_digest_comparison_v1.json)
SHA256 is `565d142b39f0a8d1b962f2a0b746e455611c68cb07aa80f27df8d586c592cd42`.
The [exact runner](../../benchmarks/receipt_digest_comparison.py) SHA256 is
`c40059d58c42083d07cc1fef1a2f21c3b45f7084797a5977b2fdc7ae7ed9bd94`.
Both were frozen and independently reviewed before execution, with the freeze
recorded in [ticket comment 6509160041](https://github.com/OptimumAF/LocalLore/issues/14#issuecomment-6509160041).

Clean baseline `255696ad91906a509faad6110e2b941670c7abe2` supplies the actual
original digest. Five synthetic files have public tool-size classes, with ten
weighted calls reading **99,589,280 bytes** per method. A separate batch of
32 small files reads **513,024 bytes**. These are size proxies for a subset of
host checks, not an entire live guard. Unique retained corpus: 37 files,
**68,389,656 bytes**, generated from an original repeating byte pattern.
No actual SDK, model, token or private source contents populate the corpus.

One warmup and five rotating measured rounds cover all five methods. Each
method occupies every order position once. Timings include fresh path checks,
new hash/buffer allocation, open/read/close and strict read-count validation.
Expected hashes use independent logical chunking; independent complete disk
reads verify the corpus before and after. Every timed return hash is checked.
All 30 samples remain in the [raw sample artifact](../../benchmarks/fixtures/receipt_digest_comparison_samples_v1.jsonl);
[results](../../benchmarks/fixtures/receipt_digest_comparison_result_v1.json)
retain exact nanosecond medians and every method's disposition.

The predeclared criterion requires at least 5% lower weighted median and no
more than 10% small-batch regression, plus Python 3.9 eligibility and successful
correctness checks. Qualifiers rank by weighted median, then small median,
then declared order. No tuning, repeat capture or changed criterion occurred.

| Method | Weighted median ms | Change | Small-batch median ms | Change | Disposition |
| --- | ---: | ---: | ---: | ---: | --- |
| Original 1 MiB read | 277.4485 | baseline | 37.2596 | baseline | Baseline |
| 64 KiB readinto | 263.9716 | -4.8574% | 26.9117 | -27.7724% | Misses 5% gate |
| 256 KiB readinto | 260.5894 | -6.0765% | 26.9877 | -27.5685% | Second qualifier |
| 1 MiB readinto | 260.1231 | -6.2445% | 34.3709 | -7.7529% | First qualifier; selected |
| stdlib file_digest | 258.3951 | -6.8674% | 26.8227 | -28.0113% | Requires 3.11+; ineligible |

This is one warm Windows host sample. Balanced ordering reduces but does not
eliminate background load, cache and ordering effects. The close 1 MiB/256 KiB
ranking does not establish statistical significance or an optimal buffer for
other workloads. It does not measure end-to-end guard, Android, model or
inference speedup, and cannot repair the earlier runtime refusal.

The finite experiment exits 0 in **15,603 ms** with known cleanup/capture,
empty output streams, stable 2,223 source hashes and no covered policy attempts.
All expected/before/after corpus maps are identical. Exact tool bindings cover
the Python executable, its DLL and `hashlib.py`, not every native crypto backend.
Independent file-only readback recomputes all medians, integer gates, ordering,
per-call sums/hashes and corpus bytes; it does not repeat timing.

## Reproduction and correctness evidence

The runner takes `--protocol`, its exact `--protocol-sha256`, and a missing
absolute D: `--output` directory. Run it by absolute path from a **clean physical
D: worktree at the pinned baseline**, using the exact recorded Python version
and process-local `TEMP`, `TMP`, `TMPDIR=D:\Dev\_Temp`. The runner refuses a
different baseline/version or an existing output. A future reproduction needs
its own bounded storage plan; the recorded packet has no recapture allowance.
The 180-second owned worker pins source/runner/protocol/tool inputs and preserves
terminal failure and raw captures. Its cooperative Python audit denies covered
non-D writes and production-migration IO; it is not an OS/native IO sandbox.

Eight original API-neutral methods pass the unchanged baseline (owned worker
5,324 ms/exit0) and the selected candidate (5,273 ms/exit0). Their source and
assertions are identical. They cover empty/all-byte/boundary/tail hashes,
positive short reads and poisoned unused buffer tails, read failure/cancellation
identity and closure, path/link refusal before open, and actual ordinary/mapped
synthetic D-file mutations despite restored size/mtime metadata.

Three separately added candidate-specific methods pass (5,024 ms/exit0): ten
malformed count variants refuse without retry/hash/finalization, invalid counts
after a valid prefix refuse, and hash-update errors/interrupts preserve the
original exception and close the file. No baseline RED is claimed for them.
All focused checks have zero failures/errors/skips/exclusions, stable source
bindings, known cleanup/capture, empty stderr and no forbidden IO attempts.

Independent AST review proves the selected loop matches the measured algorithm
after only fixed-size/alias/local-name substitution. The rest of the environment
module and ten caller modules retain their AST. One caller differs only in
CRLF/LF between existing worktrees; the original raw-byte review assertion
failure is retained and explicitly distinguished from a product failure.

Private source/control/raw evidence remains under
`D:/Dev/Experiments/LocalLore/2026-10-29-stream-hash-v1` with D: recovery.
Frozen source/build/guest evidence remains untouched. Any future runtime use
needs new source/build admission and applicable device/guest authorization;
the full restart, physical/ARM64, sustained performance and app journey gates
remain open.
