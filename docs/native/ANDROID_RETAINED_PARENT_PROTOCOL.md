# Retained-parent saved-task contract v1

M10.02/M05.05 lifecycle supporting, M08.05/M08.01 retained ancestry supporting,
and M09.03 draft/notice supporting. Base: unmerged PR #200 at `65c07ba2`.
This contract specifies a test, not an executed result or milestone acceptance.

## Authority and fixture

[ADR-0009](../adr/0009-retained-parent-deletion.md) forbids individual root
retirement. Keep the existing root, active-child and retired-leaf cases intact.
The new create-only case is `restore_retained_parent`, with exactly the original
four controller arguments plus `fixture_test_sha256`. It cannot adopt a partial
fixture, replay a Send, retry retirement, force-stop or clear a saved task.

Through the existing real UI, create two roots A/B, sorted by native story ID.
All words below are original synthetic Dialogue, never grants of world truth:

1. Send ROOT on Broot: Broot head1.
2. Review/consent/confirm a fork P at1, then explicitly resume P.
   Reopen the exact confirmed root/P recovery hint, verify its identity and
   lookup-only state, then separately consent to Forget that hint. Require P1,
   its accepted ROOT and gameplay/create counters unchanged. Close the panel;
   only a later explicit new request may prepare a different child identity.
3. Send PREFIX on P: P head2.
4. Review/consent/confirm a fork G at2, then explicitly resume G at2.
5. Explicitly return to P2 and send TAIL: P head3. G must stay2, Broot1, A0.
6. Enter DRAFT on P3 without sending it. Save/HOME, require a newer after-super
   acknowledgement and exact STOPPED task, kill only the fixed product and
   require its old process gone before either native helper.

The first old producer's final saved/command gameplay vectors must both be
`3,0,3,3,0,4` for free_text/submit/prepare/commit/cancel/other. Three explicit
Sends and two observed register/run fork pairs account for these numbers.

ROOT is the unchanged legacy DIALOGUE literal. New strings are exactly:

```text
PREFIX = SYNTHETIC retained-parent prefix: Mira, snow 雪 and café 🌊.
Keep this accepted statement in the retained child.

TAIL = SYNTHETIC unreachable-parent tail: Mira, this belongs only to the parent after the child fork.

DRAFT = SYNTHETIC retired-parent unsent draft: Mira, lanterns 🌊 and snow 雪.
Never send or restore this after retirement.
```

Only PREFIX and DRAFT contain one LF. No trailing LF belongs to these strings.
Host source literals must use ASCII Unicode escapes or explicitly read UTF-8;
PowerShell's default stdin encoding must not define expected fixture digests.

## Closed controller fixture and result

Use controller-private `process-controller-retained-parent-v1/fixture-v1.json`,
scope `locallore_retained_parent_process_fixture_v1`, version1. Its exact17 keys:

```text
version, scope, case, controller_uid, product_uid, signature_sha256,
origin_run_id, origin_product_sha256, fixture_test_sha256, roots_at_creation,
root, parent, retained_child, root_text_sha256, retained_prefix_sha256,
unreachable_tail_sha256, parent_draft_sha256
```

`roots_at_creation` contains A0/B0; `root` is Broot1, `parent` is P3, and
`retained_child` is G2. All scope records retain exact story/branch/head keys.
All three branch IDs differ. Original fixtures/result schemas stay unchanged.

The new result keeps the4096-byte cap. It has a load summary and
`retained_helpers`, two exact summaries with mode/pid/uid/started_uptime_ms/
proof_sha256, plus retired-only last_helper_exit. Full native proofs stay in
fixed private files and are hash-bound rather than duplicated in the result.
Do not raise the cap to accommodate this case. Entry uptime is not an OS
process-start claim. The120s controller and existing shell/client bounds stay.

## Fixed native fixture interface

Extend the existing test-only bootstrap by an exact14-argument path; preserve
every old11-argument rule and old leaf-worker proof. There is no selectable
class, package, database path, SQL or gameplay operation in the new arguments:

```text
mode, run_id, expected_uid, product_sha256, test_sha256, native_path,
story_a, story_b, root_branch, target_parent, saved_pid,
retained_child, target_revision, retained_revision
```

Modes remain load/probe/retire. The last two arguments are literal3 and2,
respectively. Non-load requires root/P/G distinct, fixed identifiers and a
positive disappeared saved PID. Load keeps the original sentinels
load_a/load_b/main/load_child/0 and appends load_retained/3/2. It calls only the
existing NativeArchive.close(0) to qualify actual loading, opening no database.
Choose the new hardcoded worker only for the validated14-argument shape.

Keep the already qualified fixed-home, UID, APK/certificate/hash, immutable
two-APK classpath, stored/aligned native ZIP path, boot-parent child loader,
old-PID absence and bounded parser guards. Main must not reference native
classes before constructing that loader. No new production/JNI API/dependency.
The saved proof must bind nonce, product UID, disappeared PID, after-super
event, P hint, factory1 and the exact initial gameplay vector above.

The new worker's namespace is `locallore_retained_parent_fixture_v1`, version1,
with exactly the old18 success-key names. Scope hash is UTF-8:

```text
2\nA\nB\nroot\nP\nG\n3\n2\n
```

Load has null before/after, zero commits and both close flags true. Each non-load
before/after snapshot has exactly eight keys:

```text
other_head, root_head, target_head, target_physical_head, target_active,
retained_head, retained_active, preserved_sha256
```

Before: A0/root1/P3-active-physical3/G2-active. After probe: unchanged. After
retirement: A0/root1/P-unavailable-physical2/G2-active. Public target_head is
null after retirement; it is not the retained private-prefix revision.

Use only existing typed NativeWorkspace/NativeArchive calls. Validate current
catalogv2 physical graph first, then active choices. Preview version2 must bind
the exact story/title/root/P/head3, retainedDescendants `{G:2}`, retainedHeads
`{P:2}`, removedBranches empty, nine decoded row-count keys, branches0/turns1,
one committed/zero noncommitted removed turns. The fixed fresh scripted fixture
has this exact source-derived nine-row oracle, pending actual execution:
memory_job_packets0, memory_jobs0, derived_memory0, event_witnesses2,
accepted_events1, turns1, branch_projections1, branch_entities0, branches0.
An independent native stale-Ready case adds one noncommitted turn and therefore
turns2; it does not change the external saved-task fixture's expected counts.
Probe closes its capability owner without commit. Retirement prepares anew,
writes a create-only intent marker, commits once, and requires retainedThrough2,
collected0/deletedTurns1/invalidated[P]. Refuse public P resume afterward.

Preserve the canonicalized eligible `play_snapshot` data for A0/Broot1/G2,
including their original receipt scopes. This is player/receipt evidence, not
hidden full-world equality. Exact sidecar envelope:

```text
{"version":1,"scope":"locallore_retained_parent_preserved_v1",
 "views":{"other":<A0 data>,"root":<Broot1 data>,"retained":<G2 data>}}
```

Serialize keys recursively in lexical order, arrays in native order, standard
JSON quoting/numbers, UTF-8 with no final LF. Retain create-only
`probe-before-v1.json`, `probe-after-v1.json`, `retire-before-v1.json`,
`retire-after-v1.json` under the fixed owned
`no_backup/retained-parent-selection-fixture-v1/RUN/` root. Each is capped at
262144 bytes, with a four-file aggregate cap of1048576 bytes, not a larger
per-client output allowance. Fail rather than truncate or enlarge an envelope.
Its digest is preserved_sha256. All four digests must match.
Require exact scope/revision and ROOT/PREFIX receipts on G, no TAIL; do not
promote a transcript or hash to canonical authority. Replays come from Rust.

All raw native handles close synchronously before success; helper PID must be
gone and no product process alive before relaunch. Preserve the15s watchdog,
4096-byte single-LF helper output and4160-byte exact transport capture with
both exit footers, merged stderr and raw-first persistence. Quiet framing and
one-use intent/capability remain mandatory. Unknown mutation/cleanup stops the
case permanently. Binary host readback uses scoped exec-out, not newline
normalization. Raw sidecars/diagnostics remain private and excluded from Git.

## Restored behavior and controls

Restore the same saved task with a new process/factory1 and original P hint.
Fresh native catalogs must fall back to lexical A0 with the existing exact
unavailable-selection notice, blank Action input, no accepted message body and
zero automatic gameplay/create/fork. An explicit native reread consumes the
notice. Save/stop/kill again; the second old vector is all zero. Restore settled
A0 again with no repeated notice, retired hint/draft resurrection or automatic
action.

Explicitly inspect Broot1 and G2. The selectable catalog is exactly root/G;
retired P's physical prefix remains available only to Rust ancestry replay.
G retains ROOT/PREFIX receipts and no TAIL; never send a G turn in this case.
Return to A0 blank without cross-scope text. Retain all existing root,
active-child and retired-leaf controls on matching artifact/source versions.
Tests may expose real defects; fix them without weakening engine authority,
oracle predicates, original cases, admission rules or privacy promises.

This remains scripted API35/x86_64 supporting evidence until actually run.
No physical-device/model, power-loss, forensic deletion, all-history latency,
full deletion-UI or owner-acceptance claim follows from the contract.
