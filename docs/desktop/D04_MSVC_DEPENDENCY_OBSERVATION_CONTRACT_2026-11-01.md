# Same32 dependency observation: preparation contract

Refs #25 D04.01/.02/.04 supporting, #31 D09.03 supporting, #21.
Root claim6569261802, branch `prep/msvc-dependency-observation-v1` from accepted
df73034ebcf03a448927be4aea617b603df61833. **SOURCE PREPARATION ONLY.**
Both PR334's input packet and PR343's code check are SPENT. No additional owner,
Stage, START, runner retention, Node check or input observation is authorized.

PR334 observed32 profile parses while preserving13 strict successes/19 refusals.
PR343 independently verified a pure bounded DEFAULTLIB-name/edge projection with
32 synthetic groups. Actual names/edges from the32 inputs remain unavailable:
counts/digests are not reversible metadata. This slice observes those facts;
it cannot establish selected-link members, complete DEFAULTLIB resolution,
ABI/link/build/runtime behavior or Author capability.

## Frozen dependencies and actual roster

Reuse helper9972c0eb, projectionf4afe4e1, existing cohort FIRST7ca31f68 (52 groups)
and dependency FIRSTafee9aed (32 groups), all unchanged. No new binary/archive/
directive parser, filesystem resolver, selected-member pruning or relaxed job
limit. Proposed sole child runs52+32+12 synthetic groups BEFORE constructing
the real adapter/state, then the SAME original17+15 inputs in saved order.
All96 must pass. No separate Node syntax/test child or automatic retry.

Pin original roster62eb0ab9 and diagnosticc7bce3ce, plus PR334's complete
snapshot611d5c5d8c8be232599fe4c0332032e25e693aad0f99a393902047bf7ef9334e.
Validate its full closed successful schema/proofs and settled retained evidence
before deriving expected rows, projection pins or SDK catalog. Require32 ordered
rows/64 attempts/359493030 input bytes/718986060 reads/1227142 sections, live job,
52/52,13 strict successes/19 refusals,32 profile parses and false qualifications.
Root arithmetic from retained JSON only gives71 library references and at most5
per row; it does not disclose or invent the actual library names.

Projection pins are32 ordered `{slot,metadataSha256,libraryCount}` records from
the saved profile arrays' fields9/4. Catalog is the original15 SDK
`{slot:18..32,name:requestedName}` records, exact saved order. Bind full JSON
digests of both arrays; no replacement cohort/catalog selected by arguments.
The original fixed search roots/identities remain checked by the held-file
adapter. Provided-slot matches are name joins, not a new filesystem search or
first-existing-path/closure attestation.

Use one accepted job once, strict then profile on each SAME held Buffer.
Preserve the established two complete file scans, reserve/actual counters,
canonical root/path/handle/leaf checks, post-pair in-memory Buffer hash and final
opened-identity-only rechecks; no third binary scan. Keep reserved and actual
bytes distinct, never refund, charge known returned bytes before live checks,
and finally-close without overwriting first failure. Selected-read ceiling
remains1GiB; fixed source/proof/tool/normal-image guard reads are additional,
explicitly disclosed work. No all-filesystem-I/O or atomic-snapshot claim.

## Private binding before projection

Retain an actual profile result only after the accepted pair succeeds AND its
entire encoded row equals the corresponding saved PR334 row. Full metadata
hash, object/import/directive/library counts, sections and all deviation counts
must match; digesting just names or counts is insufficient. A mismatching profile
never enters successful facts or repairs an earlier failed pair. No inference
about missing names is made after a refusal.

Freeze private callback
`bindDependencyObservationV1(slot,pair,profile,expectedRow)` before producer work.
It consumes JSON-data only and returns a NEW record ONLY `{slot,result:profile}`
on success; the caller retains ownership of the existing parsed profile object.
It does not promise to deep-freeze/copy that internal input. The eventual pure
projection still returns fresh deeply frozen output, as separately tested.

- slot is an integer1..32. pair has ONLY row,stopped,critical; stopped=false and
  critical=null. row and expectedRow have ONLY slot,strict,profile, both slots
  equal the argument. All modes are non-null encoded arrays under the existing
  dictionaries/bounds; strict success retains≤65536 sections/zero deviations.
  Both profile arrays are parsed (tag0), never a refusal. All row values match
  exactly by their full canonical JSON, including strict baseline/context.
- profile is the exact accepted eight-key metadata-job result for the explicit
  profile/purpose/false flags. Reuse the established full mode-result validator,
  including whole metadata digest; its encoded array must equal row.profile.
  Preserve metadata insertion order when hashing. No parser or alternate digest.
- Invalid/missing/extra/mismatching data throws ONLY
  `DependencyObservationMismatch`, without payloads. This is a private
  development callback, not app IPC, authenticity or Author authority. A future
  collector supplies hash-verified expectedRow; caller-supplied test data alone
  cannot authenticate a real observation.

The real loop may retain the raw profile result through a fixed internal job
wrapper, with one actual accepted job and unchanged inspect/snapshot calls.
Set its temporary result empty before each pair; capture only the profile mode;
admit the observation only after pair and Buffer checks. Keep failures sticky.
After32 matches and final source/identity guards, call the accepted projection
once on those32 actual results/pins/catalog. Never call it with a recovered
subset, invented empty metadata or a replaced job. No arbitrary callbacks,
paths, commands, limit selectors or runtime source evaluation.

## Independent additional FIRST

New portable `native/llama-worker/library_metadata_dependency_observer_first.mjs`
exports ONLY `async runDependencyObserverSelfchecksV1(api)`, no top-level run,
producer import, files/process/environment/network or source eval. The sole
callback is `api.bindDependencyObservationV1`. Missing callback throws
`UNRUN_SETUP: dependency observation API unavailable`. Fixtures independently
construct canonical accepted-profile metadata, mode digests and expected rows
using Node crypto; no actual binary or SDK data is needed. Budget fixture text/
buffers≤1MiB; this is not an OS peak-memory claim.

Freeze12 groups B01..B12 before binding producer edits:

| ID | Required assertion/control |
| --- | --- |
| B01 | Matching parsed pair/profile binds exact slot/result in a fresh record |
| B02 | Slot0/33/noninteger/duplicate mismatch between arguments/rows refuses |
| B03 | Missing/extra pair fields or nonboolean stopped/nonnull critical refuses |
| B04 | Missing/extra row fields, null modes or malformed encoded arrays refuses |
| B05 | Any profile encoded field mismatch (counts/sections/deviations/digest) refuses |
| B06 | Changed actual metadata/directives/library names with unchanged expected digest refuses |
| B07 | Any true/nonboolean qualification/link/closure flag refuses |
| B08 | Wrong profile/purpose or unknown/missing result/metadata/deviation field refuses |
| B09 | Stopped/refused profile pair refuses even when expected row copies it |
| B10 | Changed strict success/refusal/site/context refuses, no strict rewrite |
| B11 | Same metadata values with different insertion-order digest refuses |
| B12 | Inputs unchanged; exact object/result binding; no added authority/fields; errors contain no raw payload |

Return exact six keys version,kind,executed,passed,failed,failed_case_ids; version1,
kind`library_metadata_dependency_observer_first_v1`,12 groups and fixed IDs.
Preserve original assertions/IDs after findings. Source review is not a runtime
pass or behavioral RED. Re-running the old52 and32 groups in a future sole
child is part of a NEW finite grant, not reuse of their previous grants.

## Complete versus failed capture

Prepare one fixed supervisor/one fixed Node child, owner/Stage/source binding,
closed schemas, bounded concurrent streams, observed deadline, confirmed child
closure, sticky STOP and full-reserve controls. Preserve all global stops/prior
STARTs and exact own-START exception, source/proof/normal fences and no output
growth. No general remote server, arbitrary execution or desktop control.

Proposed whole report: version1, kind`msvc_dependency_observation_v1`, false
qualified/linkQualification/closureComplete, captureComplete boolean,
status`complete`/`stopped`, exact selfchecks `{cohort,projection,observer}` (the
52/32/12 six-key summaries), exact source/proof digests, an existing-format
cohort report and accepted projection facts or null, plus a fixed critical code
or null. Freeze the complete concrete envelope/proof dictionary and independent
validator BEFORE asking for execution; this paragraph is not a schema license.
No unbounded raw names/directives/paths or extra output fields.

Complete requires all three passed summaries, full coherent32/64 cohort,
32 exact saved-row bindings, accepted complete facts with matching pins/catalog,
32 ordered graph rows/71 references (each count from saved row), all input/source/
identity/retention guards, exit0 and empty complete stderr. Unknown names remain
in facts with null providedSlots; they do not grant further input lookup.
Even all references matched retains closureComplete=false.

A known-closed coherent failed partial must be retained as failed evidence,
including actual job/I/O/row prefix and FIRST summaries when available; facts
are null until the full projection succeeds. Preserve the first fixed cause;
binding/projection failure cannot be relabeled as a later source error. Keep
the existing cohort's validated partial accounting, with an explicit outer
binding/projection error where that is more precise than the inner report.
If the whole report cannot be encoded/validated, retain bounded raw/error bytes
and failure rather than recovering a successful subset. Startup/parse/FIRST
failure may emit no input report and must not claim any real observation.

A future report may need≤24576B including LF while keeping raw stdout24576 and
stderr1024. This new report allowance is only a proposal; old reports/caps and
all their failures remain unchanged. Prove actual full-envelope worst cases and
all physical/base64/decoded/snapshot costs before any owner decision. Original
cohort full rows and new dependency graph must not be silently omitted to fit.

### Exact outer envelope frozen before producer integration

The outer has ONLY version,kind,qualified,linkQualification,closureComplete,
captureComplete,status,selfchecks,proofs,cohort,facts,critical, in that insertion
order. Version1/kind`msvc_dependency_observation_v1`; all three qualification
flags false. selfchecks has ONLY cohort,projection,observer: exact successful
six-key52/32/12 summaries with their existing three kinds. Its cohort summary
must equal the inner cohort.selfchecks. No aggregate count can hide a failure.

proofs has ONLY reader,supervisor,helper,cohortFirst,projection,projectionFirst,
observerFirst,roster,diagnostic,cohortSnapshot,codebook,descriptor,pins,catalog;
each lowercase64hex. Couple the inner seven proof fields exactly: inner.reader
=outer.reader, supervisor=supervisor, helper=helper, first=cohortFirst,
roster=roster, descriptor=descriptor, codebook=codebook. Other fixed sources/
snapshots match their frozen pins; pins/catalog hash the arrays defined above.
For complete facts, their pinsSha256/catalogSha256 equal outer pins/catalog.
Parent independently checks all actual owner/source/Stage/proof references.

Complete requires captureComplete=true, status`complete`, outer critical=null,
inner status`complete` with null critical, exact expected full32 encoded rows
and all existing inner-schema counters. Inner JSON+LF must be exactly7071B:
row/count/dictionary/selfcheck values match PR334; changed own source proofs
remain fixed-length64hex. Facts have the accepted exact16-key shape, true
captureComplete but false qualification/link/closure flags; all32 graph rows'
library counts equal the saved profile counts,71 total and at most5 each.

Stopped requires captureComplete=false,status`stopped`,facts=null. Existing
inner critical codes remain allowed unchanged and outer critical must equal
the first inner critical in those cases. Two additional outer details:
`DependencyObservationMismatch` requires an inner stopped `ReportFailure`,
fully attempted current pair, nonempty prefix and every earlier row equal
the saved rows (current profile may be a known refusal or mismatching parse).
`DependencyProjectionRefused` requires a complete exact32-row inner cohort.
No outer success is inferred from an inner complete report. All later guard
failures preserve the earlier outer/inner first cause.

No extra field or padding capability. Bound the outer envelope with cohort=null
and facts=null to2048B. Preserve inner≤16384B and facts' separately validated
row≤128B, name-union-array≤8385B and empty-rows/names envelope≤2048B. These give
a conservative facts JSON+LF bound14561B, also checked explicitly. By branch:
complete7071+14561+2048=23680B <24576; stopped16384+2048=18432B <24576.
These overcount replaced nulls/newlines conservatively. Independently check the
WHOLE canonical strict UTF-8 JSON+LF≤24576B before emitting/retaining it.

The supervisor validates these schemas/couplings independently, including
per-slot strict baseline, full saved-row equality where required, fact names/
IDs/provided-slot/null resolution and graph counts. Complete process evidence
holds only bounded summary/digests plus raw/base64, never another full report.
Known-closed coherent failed snapshots remain failed; malformed/overlimit raw
output stays raw failure. A future complete packet reserve is at least126976B
(prior118784 plus8192 for the24576B snapshot), in addition to actual sources,
owner,Stage and prep records. Final actual sizes/envelope proof remain required.

## Storage and next admission

Current final charged metadata1801774B/cap1867776B leaves66002B. Cumulative
decoded allowance is18014B; future guards MUST carry it forward, including the
latest118B. Physical group53995650B/joint736317144B; conservative new-log charges
7189B give54002839B/736324333B. Target12356228504B/runtime210B unchanged.

Exact source sizes, final source retention plan, owner/Stage/prep records,
complete raw/base64/decoded/snapshot/process/START/result/Root-review/STOP reserve,
deadline/stream bounds, independent reviews and fresh actual fences/inventory
must be concrete before any separate finite input-read/cap decision. No new
cap is approved or inferred. Keep64MiB group,724MiB joint, original-baseline4GiB
target growth,576KiB old records,8MiB fixtures and all previous output/failures.
No deletion, compression, second output root or relabeling can make a forecast fit.

After source preparation, the next runnable action is separately admitted
synthetic gating plus SAME32 read-only dependency observation. This contract
permits none of it. No new library resolution, compiler/link/build, C++ worker,
model/app/native UI/device/OS work, downloads/settings/release or desktop control.
Full D04/D09, narrative quality and desktop epic acceptance remain open.
