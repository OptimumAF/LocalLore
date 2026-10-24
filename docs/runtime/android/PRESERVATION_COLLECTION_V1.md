# Independent preservation collection, version 1

Refs #5, M01.05 partial. This development-only collector fixes a fail-fast
observation gap: an old-cache metadata mismatch prevented later canonical-file,
journal, storage and inventory checks from being recorded. It changes neither
preservation criteria nor canonical authority. Earlier missing checks remain
missing; this API cannot reconstruct them.

## Fixed read-only adapters

`android_preservation.collect(checks, verify_boundary, clients_known, retain)`
accepts trusted, bounded adapters. It contains no ADB, filesystem transport,
SQLite opening, model call, retry, repair, installation or lifecycle operation.
The caller owns fresh admission, command deadlines and raw evidence retention.

`checks` is an exact dictionary with these eight callable keys, executed in this
fixed order regardless of dictionary insertion order:

1. `model_metadata`
2. `cache_metadata`
3. `prior_canonical`
4. `guarded_canonical`
5. `traced_canonical`
6. `phase_journal`
7. `storage`
8. `inventory`

Each callback retains raw bytes before interpreting them and returns exactly
`matched`, `mismatched` or `unavailable`. No payload is returned to the collector.
A safe value mismatch is an observation, not an exception. Unsupported or missing
comparison evidence is unavailable, not matched. Wrong file kind, link, uncertain
owner or unverified path must never be downgraded to a harmless mismatch.
Original full metadata/hash/size/absence criteria remain intact; content-only
subfacts cannot silently remove an inode/timestamp mismatch from the verdict.

`verify_boundary()` freshly verifies the selected APK/UID/app-root identity and
full process-namespace absence, returning literal `True` only when safe. Other
relevant owners must be verified by their specific adapters. Whole package maps
can be checked initially/finally without hashing unrelated APKs at every boundary.
`clients_known()` is a pure, non-dispatching predicate over sticky ownership
flags, also requiring literal `True`. Once false or failed, it cannot recover
within this invocation. It is checked around every adapter invocation. Adapters
must propagate every uncertain client/transport owner into that predicate.

`retain(checkpoint)` synchronously and durably writes one bounded host-only
checkpoint. It receives a deep copy and performs no hidden device operation or
dependent read. It must use the caller's owned output namespace and never
overwrite old evidence. Raw retention still belongs inside each check adapter.

All keys/callables are validated and references frozen before any callback runs.
There are at most eight checks, sixteen fresh boundary verifications and nine
checkpoint calls. Limits on each adapter's I/O are the trusted caller's duty;
the collector is not a sandbox or an uninterruptible-operation watchdog.

## Continuation and stop rules

Every check requires a fresh verified boundary both before and after observation.
A mismatch or explicit unavailable result can continue only when ownership and
the boundary remain known. Overall preservation stays false unless every check
matches. A command, parsing or unexpected callback exception, invalid result,
identity/process failure, ownership loss or retention failure stops the sequence.
No later boundary/check is dispatched after that fence.

Observations survive a failed post-check boundary with their row marked
unverified. A fixed stopped checkpoint may still be written through the trusted
host-only sink. A failed sink is never retried. Ownership lost during a sink
revokes retention completeness and success without dispatching another sink.
The first stop reason stays primary; later retention/ownership failures remain
visible through their separate flags.

## Bounded result and checkpoints

The exact top-level keys are `version=1`,
`scope=android_preservation_collection`, `status`, `checks`, `clients_cleaned`,
`boundary_verified`, `retention_complete`, `collection_complete`,
`preservation_verified`, and `stop_reason`.

Each of the eight rows is exactly `check`, `status`, `boundary_verified`.
Status is `not_run`, one of the three valid observations, or `error`. An
unverified matched observation is not preservation evidence. No arbitrary
exception, private path, identifier, model text or database payload is echoed.

Final status is `input_refused`, `observed` or `stopped`; interim checkpoints
may be `collecting`. `observed` means all eight observations and their post-check
boundaries completed, including mismatches/unavailable values. It is not a pass.
`collection_complete` can remain true if the final sink subsequently fails;
`retention_complete` and `preservation_verified` are then false. Stop reason is
`none`, `input`, `ownership_unknown`, `boundary_failed`, `check_failed`,
`invalid_check`, or `retention_failed`.

Every sink checkpoint has `preservation_verified=false`. Success is set only in
the final returned result after the last sink and local ownership recheck. The
caller retains that final result separately; a checkpoint must never substitute
for it. A true result describes a finite invocation of the admitted adapters,
not timeless ownership, canonical replay, model compatibility, safe retry or
permission for another experiment.
