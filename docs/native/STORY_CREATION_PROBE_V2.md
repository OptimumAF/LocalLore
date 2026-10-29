# Explicit starter creation and process probe v2

Status: historical introduction of probe2 at the starter-creation checkpoint.
The controller-result1 descriptions below preserve that checkpoint's scope.
Current controller admission uses the later
[creation/restoration result2 contract](CREATION_RESTORATION_RESULT_V2.md),
which exports separate saved/command creation maps for both old producers.
Its runtime evidence is recorded in the dated reports; historical decoding
does not qualify a current run. The product probe remains version2.

This source compatibility slice supports M09.02/M10.02. It is not new Android
execution evidence. Earlier process-restoration results retain their original
source, APK and probe-v1 attribution. The coordinator must compile and execute
the changed producer, controller and helper APKs before current qualification.

## Product record

The product now emits `version: 2`, scope `locallore_process_verify_v2`. Its
closed field set remains `version`, `scope`, `run_id`, `pid`, `uid`, `task_id`,
`sequence`, `process_start_uptime_ms`, `event`, `restored_state`,
`factory_creations`, `hint_present`, `hint_sha256`, `operations`.

The fixed private storage namespace remains
`no_backup/process-verify-v1/RUN/{created,saved,commands}.json`. The directory
name is not a claim that its record has version1. Existing run-ID guards,
cumulative process counters/factory count, after-super save, atomic writes and
4096-byte cap remain. Navigation-hint encoding and its `1\nSTORY\nBRANCH\n`
digest remain unchanged; this is not a new navigation-hint format.

The exact operation keys are the old twelve, followed by two distinct keys:

```text
workspace branches resume create open play_snapshot
free_text submit prepare commit cancel other
story_template create_named
```

Each counter is an integer in0..4096. Existing overflow refusal and sequence
bounds remain. Counters observe attempted calls at the transport observer,
before native dispatch; they do not establish JNI entry, insertion, success,
canonical mutation or resource ownership. `story_template` is a separately
observed read. `create_named` is never aliased to legacy `create` or ignored.
Exactly `close`, `capabilities`, `model_status` remain omitted metadata/resource
operations. Every unrecognized name increments `other`, without retaining text.

## Current controller and native fixture helpers

The current controller and both retirement fixture workers require probe2,
the matching scope and all fourteen operation keys. Helper success/failure
records keep their existing formats: only their input probe guard changes.

Each real New story action is followed by a bounded rendered starter dialog,
preview and enabled Create wait. The controller reveals the fixed confirm
button using only the product's creation-content scroller, proves no change
in either creation counter before confirmation, then performs exactly one
explicit Create click. It waits for the dialog to disappear before the
existing native workspace/catalog checks. It neither calls a creation
controller directly nor retries/adopts a partial fixture.

Existing creation-attempt totals count `create + create_named`. Both counters
remain separately visible. Comparisons around save, final old-process records
after death, and fork-review reset compare each key separately; opposite changes
cannot cancel in a sum. Fresh restored processes require both creation counters
zero. The six gameplay keys remain exactly `free_text`, `submit`, `prepare`,
`commit`, `cancel`, `other`, with their original vectors. Native-reread checks
still require increases of both `resume` and `play_snapshot`; a preview call
cannot satisfy that predicate.

The120-second case cap, existing shell/step/output bounds, original diagnostic
check counting and result `version:1` field sets remain unchanged. Added
consent/creation guards refuse without manufacturing extra diagnostic checks.
No existing82/123/139 expectations are widened. Current execution still needs
the coordinator's actual source/artifact/runtime gates.

## Host decoding and evidence limit

The product-record decoder preserves strict historical probe1: scope
`locallore_process_verify_v1`, exactly twelve operation keys. Probe2 requires
its matching scope and exactly fourteen keys. All three final records in one
stream must have the same version. The decoder returns the original parsed
version/fields; it does not normalize one version into another. Unknown keys,
mixed versions, coercible numbers/booleans, invalid types/bounds and automatic
creation in restored producer records refuse. Counter monotonicity includes
the two new keys for probe2. Existing historical-v1 synthetic fixtures remain.

The controller-result v1 terminal observations still export only the existing
six gameplay counters. They do **not** export first-old-process creation
counters. Preservation of those creation counts around the first death is a
source-pinned controller assertion in this slice, not an independently exported
raw counter pair. The final three product leaves can independently validate
creation counters for the second-old and third producers. A new terminal
creation map/result schema is deliberately outside this compatibility slice.

Authored host adversaries cover both closed versions, matching scopes, missing
or extra operation keys, mixed streams, strict new-counter types, automatic
named creation and separate preview counter history. Existing deep host
orchestration fixtures exercise both versions without changing original test
names. These mocked/source assertions are not saved-task or native execution.
