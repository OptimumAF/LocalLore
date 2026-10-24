# Independent preservation-collection review, 2026-10-23

Refs #5, M01.05 partial, claim `6376152312`. Base: `498a5250cc5f3b55bc4371295814ce4a5acb6e02`. I authored only the independent test file and this report, and performed source/evidence reads and pure host tests. I performed no device, SDK, model, build or GitHub operation.

The collector separates a safe observed mismatch from unsafe ownership or boundary uncertainty. A mismatch must remain failed while allowing later independent canonical checks. An uncertain owner must stop all further observations. Neither collecting every row nor retaining a checkpoint establishes canonical replay or full preservation.

## Independent source and tests

Reviewed production commits are `6173ba0` plus `3e205f9`; tested module SHA256 is `c1d040439e7208d19df82edbe83fa51ad087ca0fb0371feb87c06439a3aabd4f`. The implementation freezes validated callback references, uses literal-True sticky ownership/boundary predicates, surrounds observations with fresh boundaries, deep-copies fixed reports into a bounded host-only sink, and never publishes provisional preservation success to that sink.

The coordinator identified an initial checkpoint-entry edge: ownership already lost at checkpoint entry could allow another loop iteration and a redundant stopped checkpoint. I independently reproduced it against immutable `6173ba0`: the targeted regression failed with three sink calls instead of two. The corrected `3e205f9` stops after the one fenced host checkpoint. This was a host-only reproduction, not a device or production SDK failure.

Actual command against corrected source:

```powershell
python -B -E -m unittest discover -s scripts/tests -p test_android_preservation.py -v
```

The first selection passed **21 tests in 0.019 seconds**; the final selection passed **22 tests in 0.020 seconds**, both exit zero. The original-source targeted selection recorded **one expected regression failure in 0.001 seconds**, exit one. All logs and exit records remain retained. Test commit: `d94019ef82c906a828b9e221013c98aee9601ae8`. Selections overlap and are not added as unique tests.

The tests cover all eight nonmatch/error positions, continued canonical observations after cache mismatch/unavailability, exact successful nine-checkpoint/sixteen-boundary flow, upfront validation, frozen callback bindings, truthy impostors and exception privacy, failed post-boundaries, ownership lost during each callback class, checkpoint-entry loss, poisoned/failed final sinks, sticky first failure, and malicious sink-copy mutation. Every sink checkpoint keeps `preservation_verified=false`; only the final returned result can pass after the last sink and ownership recheck. A failed or poisoned sink is not retried.

The review's selected-file index binds nine files / 32,245 bytes, including frozen source/test copies and every executed selection. Index: **1,529 bytes**, SHA256 `18bbf32f575ae77953bacc8e42b207c15f3526b3b4e7f97ea0b0b641fd03f156`.

## Private adapter source review

I reviewed frozen controller v6, SHA256 `6a5538cabf33e60d38c3905963c7ce6ddf0aac2fb5b040e7ba79d00e5359c36c`, and its fixed 180-second owned driver. Fresh selected-package hash/UID/root and process-namespace checks surround observations; relevant additional package owners receive their own fences. Raw output precedes interpretation, uncertain clients stop later reads, and checkpoint files use fresh host-only paths. This source assessment is not device execution or owner acceptance.

Draft review corrected safe new-sidecar and size-only model changes being treated as structural failures, optional dangling-link omission, nested/depth-hidden links, and a temporary known-file-only cache listing that would have hidden extra regular files. Required path/kind/owner guards remain mandatory. Full metadata/hash/absence comparisons determine preservation; content-only subfacts do not promote a mismatch.

I additionally identified that `find -exec stat ... \;` could omit a failed child command without a failing overall status. Official Android 15 [find source](https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-15.0.0_r1/toys/posix/find.c) confirms the semicolon form uses the child result as a predicate. The corrected adapter enumerates every bounded regular path, rejects unsafe kinds/links and unexpanded deepest directories, then checks one `stat` invocation and exact returned path/count correspondence. Official [stat](https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-15.0.0_r1/toys/other/stat.c) and [error handling](https://android.googlesource.com/platform/external/toybox/+/refs/tags/android-15.0.0_r1/lib/lib.c) set nonzero status for failed operands. This is not an atomic-filesystem or installed-binary fault-injection proof.

The separate official-source index binds six source/binding files / 69,622 bytes: **1,137 index bytes**, SHA256 `a57b8b1e6bf8a60a61069b965cbbf0e271be26d9256c17781fc43d3e9f00c8f5`. The original test index remains unchanged.

## Actual evidence audit

The separately owned read-only cohort completed in **65,469 ms**, child exit zero with known cleanup. All eight checks completed through 16 boundaries and nine checkpoints. Seven matched; cache metadata mismatched. Thus `collection_complete=true` and `preservation_verified=false`. Exit zero proves completed collection, not preservation success. The coordinator's bound full-suite log records **402 passing script tests in 4.988 seconds**, including the 22 independent methods.

I independently rehashed all **1,353 selected files / 1,232,891 bytes** against the **230,349-byte** device index, SHA256 `bf4656309c630ab2c183138501cecd85e5c964962a11426ede920b7c38e33236`, with zero mismatches. All 627 command stdout sizes/hashes and terminal zero/known-clean records matched. Raw package/path/hash blocks reconstructed the initial and final A21/B23 maps; 119 APK-hash commands were retained. The final inventory reported four emulators, no other devices and both selected targets ready.

Raw outputs for all three old canonical sets and the separate phase journal matched their complete historical metadata/hash/size/absence baselines after uniform line-ending normalization. Present-file counts were respectively 2/2/3/2. This is a fresh finite file comparison, not SQLite replay, a whole-model hash, proof against transient changes or completion of the earlier missing final observations. All 25 samples met their fresh inspection floors; the earlier 64-MiB post-consumption failure remains unchanged.

Independent cache comparison reproduced the guarded directory-inode difference and owner-marker mtime/ctime shifts of minus one second. The traced cache also had owner-marker inode and timestamp differences, with the same timestamp shifts. Prior cache metadata matched. Cache/marker payloads were not hashed; cause remains unestablished. No criterion was dropped to convert these differences into a pass.

The [safe aggregate](PRESERVATION_RESULTS_2026-10-23.json), **4,435 LF bytes**, SHA256 `f533011c9cfac0b29de98cc1f56e87a18c00c879d7c303b76e24f6a068767b5f`, matches the retained result, comparison counts, cache deltas and storage samples. The [verification](PRESERVATION_VERIFICATION_2026-10-23.md) and [device report](PRESERVATION_DEVICE_2026-10-23.md) preserve these limits without publishing private paths, process identities, raw file contents or model data. The independent readback receipt is retained separately from the unchanged test/source indexes. No remaining concrete blocker was found in this bounded packet.

## Authority and limits

The [protocol](PRESERVATION_COLLECTION_V1.md) correctly keeps trusted adapters responsible for bounded read-only transport, raw-first retention, verified package/path owners and complete baseline criteria. The collector is not a transport sandbox or hard watchdog. A fixed stopped report may be retained through a trusted host-only sink; it authorizes no further device read. Collection may finish with mismatches or unavailable observations, and final retention failure may leave `collection_complete=true` while preservation remains false.

Earlier missing final checks cannot be reconstructed or retrospectively marked passed. Full metadata, size/hash and absence comparisons must remain authoritative; content-only subfacts cannot excuse inode/timestamp differences. No inference retry, policy relaxation, successful runtime profile or milestone acceptance follows from this collector.

M01.05 remains partial and pending owner acceptance. The next coordinated task is a source-only M05.04 gap/claim audit; this report requests no further metadata collection or inference.
