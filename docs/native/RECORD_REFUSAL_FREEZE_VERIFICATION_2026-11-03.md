# Coherent refusal freeze verification — 2026-11-03

M10.02, supporting M09.06. Host implementation in review. Android 0/5.

## Change and immutable roles

PR397 added safe refusal reasons, but its changed inner bytes deliberately did
not match the old outer pin. This packet rotates all six required production
identity/count/pin surfaces into one fresh generation. It does not change the
parent runner body, the inner stage/refusal behavior, SDK18 protocol, five UI
selectors, APK bytes, storage/authority/job mechanisms or deadlines.

Base PR397 is 0b1cc31f60645b77d9357361be3088a9b74d7b5a, tree
57c32439eb9e90ae69f503307b9db9c7dfb3fcd2. The profile-only commit
dbcafb0070734cbccbd420a159f6305bc6f9090d / tree
53c47a25b00f2ca868150f76d408c3789a6fcc3c changes exactly four role literals in
two files. Its immutable raw Git snapshot has 2,671 files / 38,198,383 bytes;
catalog 755,007 bytes / SHA256
aa58a83cd42933165f659b454d768b3b6c4cbc4458efabf300704e09fd50de31.
The executing candidate has 2,672 files, including the new original test.

Root used verified raw Git snapshots and alternate indexes after managed
worktree creation refused the physical repository as outside attached workspace
roots. Existing separate agent worktrees and normal repository HEAD/index were
preserved. GitHub tickets own claims, plan changes and acceptance; retired
Markdown trackers were not revived. No new dependency or SDK/model choice.

## Actual checks and original failures

Commands ran from D:/Dev/Repositories/LocalLore with process-local
TEMP/TMP/TMPDIR=D:/Dev/_Temp, using installed Python 3.14.7. Each checked owner
used existing runtime_spike SHA256
51e94325ed5e59a31c64fcc274e7a41c40b9dd969b09d39df7be56b0ee941598,
180-second deadline, 262,144 combined output cap, and a stdin barrier released
after job assignment. The genuine file-only workers changed to the frozen
profile root; unittest workers changed to the executing candidate.

```text
python D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1/run_host_owned.py baseline-v1
python D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1/run_file_owned.py inspect-v1
python D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1/run_host_owned.py final-v1
python D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1/run_file_owned.py bootstrap-v1
python D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1/run_host_owned_v2.py final-v2
python D:/Dev/Experiments/LocalLore/2026-11-03-record-refusal-freeze-v1/run_file_owned_v2.py bootstrap-v2
```

The first final/bootstrap pair ran concurrently, as did the corrected pair.

| Check | Actual result | Checked owner |
| --- | --- | --- |
| Original eight-method oracle on old generation | 8 assertion failures, 0 errors/skips; source unchanged | completed, exit1, 10.537s, known cleanup, stderr0 |
| Real public file-only inspector | four create-only records; 2,671 source files, 28 benchmark sources, 928 installed files | completed, exit0, 41.256s, known cleanup, stderr0 |
| First final host | no completed unittest result credited | completed, exit1, 0.544s, known cleanup, stderr1,126 bytes; payload not retained |
| First bootstrap | no successful bootstrap credited | completed, exit1, 0.303s, known cleanup, stderr1,199 bytes; payload not retained |
| Corrected final host | 104 unique methods / 22 classes, 0 failures/errors/skips; source unchanged | completed, exit0, 118.985s, known cleanup, stderr0 |
| Corrected real cold bootstrap | both public loaders consume new pins; missing/old authority refused; no live attempts | completed, exit0, 1.919s, known cleanup, stderr0 |

Root's binding helper introduced SOURCE=OUT/... before OUT was defined. A
separate read-only run reproduced NameError OUT on that unchanged bad module;
this diagnoses current source, not the discarded original stderr payload.
The bad two files and all failed controls/counts remain. Correction uses an
explicit physical Path and rebinds the outer fresh-contract hash. Original test
bytes/assertions, profile, inspection records and all execution gates stay intact.

Additive v2 workers redirect stderr to the captured stdout before project imports;
old worker files/launches/captures remain immutable. Interpreter/stdlib failures
before that redirect could still be count-only. Raw final unittest duration is
117.954s; result.seconds=118.238 includes post-run source hashing/record work;
the wider owner lifetime is 118.985s. No repeatability/performance claim follows.

The original new test is 18,628 bytes / SHA256
f5a5ed61028438c70ebe1ff8362da17c62ea06de58edae88745888b26daa706d,
unchanged throughout. Seven older test/fixture files change only current
generation literal identities; independent reversal restores every other byte
and assertion/control-flow AST. Historical OLD slots/negative cases remain.
One historical method name still contains 2664; its actual graph/count is 2671.
The 104 methods comprise eight new generation oracles, eight inherited refusal
oracles and 88 existing SDK18 checks. Tiny catalog seams/fake ports do not prove
the real source freeze; the actual inspector and loader checks supply that
separate evidence. Three existing host methods use four controlled literal
Python child attempts/Windows Job path, including injected ownership failures;
those refused cases are not successful inner ownership. Remaining fixtures are
synthetic. No Android, JNI or real inference result is credited.

## Actual file-only joins

Installed bytes per hash pass: 5,282,289,699; the inspector records two installed
hash passes. A Python audit hook installed before target imports observed zero
process/socket/forbidden-write attempts and allowed inspector writes only inside
the new inspection output. Bootstrap denies all writes. ADB key content opens
are denied; only its path metadata is consumed. Read-open file-size accounting
was 11,354,739,909 for inspection and 59,725,123 for bootstrap. This metric is
not total actual I/O: held-handle rehashes/seeks can reread bytes without a new
open. The declared read allowance was 36 GiB, alongside existing per-file/source/
reader caps and checked deadlines, not a system-wide I/O quota or OS security
boundary. No operational SDK executable or ADB service was dispatched.

Actual handoff: 9,021 bytes / SHA256
23e13dc8ef2a9a7dc169dc88bb3ef013767c6e223a126f75ba8d2423c151e041.
Preparation proposal: 173,555 bytes / SHA256
4dc63f47db5ab969402f9bac170641c8b6e4a37c494974e047b2369d5f3691aa.
Current inner: 31,655 bytes / SHA256
5a6b8968bb4f40b9488d16da520f6659963d90c6d74836b3f2578544bc97268e.
Current fresh contract: 7,602 bytes / SHA256
15f19a69be0696816dce8f395915b78f94607a7b0323807b21b481653de576d0.
Genuine parent and inner _parts consumed these exact source/pin roles; neither
used an injected factory. Actual missing-authority CLIs returned1, and both
loaders rejected the old canonical authority pin before creating live state.

The preview grants no admission. No current memory/commit/port readiness is
inferred: this inspector does not call resource_facts. Original B110 build/APK
attestation is revalidated, not rebuilt; its recorded JVM/Android compilation
facts retain their original attribution. No new JVM/Android execution occurs.

## Retention, limitations and next gate

The packet declares a 256 MiB combined ordinary source/control/test/recovery
allowance, including retained temporary originals. Ninety-six exact-prefix
fixture roots created in the final launch/terminal window contain 9,395 retained
files / 44,228,445 bytes. Originals plus verified copies are retained; copies
join recovery. Prefix/time-window selection is not cryptographic process
ownership, nor a capture of every intermediate fixture state. No older roots
are adopted or removed. Final archive/accounting and ticket/readback closure
are separately recorded under D:/Dev/Recovery/LocalLore with this packet's
2026-11-03-record-refusal-freeze-v1 basename.

The shared ledger, prior sealed records, other emulator and system settings are
preserved. An ordinary empty parent was created; guest/runtime/control/live/
authority paths stay absent. No prepare/reserve/recovery/retirement/boot, model,
phone discovery, shared ADB change, preserved-data deletion, private diagnostic
upload, release or merge. Toy validators may remove their isolated lockfiles.
The original B119 run stays failed/spent and its exact cause remains unknown.

Next gate: review an exact new operation proposal and current readiness. A new
actual run requires new applicable approval and guarded admission; this freeze
grants neither. Android0/5, physical/ARM64/model/gameplay/full-journey/CI and
owner acceptance remain unqualified; full checklist entries stay unchecked.
