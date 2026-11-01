# MSVC metadata profile: source-only API contract

The frozen contract below preceded implementation. Its separately approved
code checks now pass112/112 and94/94; see [actual verification](D04_MSVC_METADATA_PROFILE_VERIFICATION_2026-11-01.md).
No SDK/profile adoption or broader qualification follows from those code tests.

Refs #25 D04.01/.02/.04, #31 D09.03 supporting; claim6561774956.
**Implementation/test preparation only; no new check or SDK-input run admitted.**
The [design proposal](D04_MSVC_METADATA_PROFILE_PROPOSAL_2026-11-01.md) records
primary precedent and interpretation limits. This contract freezes the new
pure-Buffer interface before independent FIRST source and producer edits.
It does not authorize a policy change in the app, a build or a linked worker.

## Existing strict API

`inspectLibraryInputs(buffer)` retains its exact current successful shape,
error messages/site/context and every default rule, including65536 aggregate
sections. Extra JavaScript arguments cannot opt that function into the new
profile. The existing112-case test file remains byte-identical. The actual
12709B prior helper is retained unchanged as local
`b2-library-strict-helper-frozen-a4f61e90.mjs`, SHA256
`5682460909b69f85763d1919d6b1e7f0a49e26f41c938f87fc61104ce0bdcfc5`.
Old executed scripts/Stages remain frozen and spent; evolving the normal source
checkout cannot authorize their replay under a mismatched live source hash.

## Closed new API

Export `MSVC_LIBRARY_METADATA_PROFILE`, a deeply frozen plain descriptor:

```text
id: msvc-library-metadata-v1
version: 1
purpose: build_input_metadata_only
limits:
  inputBytesExclusive: 268435456; memberBytesExclusive: 268435456
  memberSections: 65536; inputSections: 262144; jobSections: 2097152
  jobInputs: 32; jobInputBytes: 536870912; jobFileReadBytes: 1073741824
  members: 65536; longnames: 65536; tokens: 65536
  directiveBytes: 1048576; nameBytes: 4096; libraryNameBytes: 255
```

`createLibraryMetadataJob(profileId)` accepts only that exact primitive string,
with no coercion, custom limits, callbacks or environment selectors. It returns
a frozen object with only `inspect(buffer, mode)` and `snapshot()` methods.
Modes are exactly `strict-v1` and `msvc-library-metadata-v1`; unknown modes fail
before parsing. A buffer may be attempted once per mode in a job. Repeating a
mode or exceeding a job limit stops that job permanently; there is no reset.
Extra factory/inspect arguments are ignored and cannot select custom limits.
Byte-exclusive fields use `<`; all other numeric maxima are inclusive.

Register each distinct Buffer object once as one input entry and charge its
whole byte length before parsing. Equal hashes or overlapping backing memory
do not deduplicate distinct entries. The future fixed32 collector must create
one held buffer per roster entry and prove inputCount32. The same buffer feeds
strict/profile attempts; both attempts charge declared section work before its
table loop. Charges already reserved are never refunded after format refusal.
An over-budget prospective charge stops before that work; the error records
candidate/limit while the accepted aggregate remains within its bound.
Check/charge the job's declared section count after incrementing this attempt's
section count but before its member/input ceiling or section-table range/loop.
This conservative charge survives a subsequent per-input/member refusal.

Snapshot is a fresh frozen record with exactly profileId,inputCount,inputBytes,
attempts,sections,stopped. Ordinary format and per-input/member refusals can be
recorded and the fixed cohort continued; JOB resource/duplicate-mode/unknown-mode
failures are sticky. On a live job, unknown mode is checked before input type.
An already stopped job reports metadata_job_stopped before every other check.
Invalid non-Buffer or
exclusive input-byte failure is not a registered entry/attempt and does not
stop the job. Failed prospective job-entry charges register nothing. After
admission, consume mode/increment attempts before parsing; retain both on error.
Filesystem reads,
identity, cohort membership and actual IO counters belong to the separately
admitted collector; this Buffer-only module cannot measure filesystem reads.
Its descriptor's1GiB IO ceiling must be enforced by that future collector.

On success `inspect` returns exactly profileId,purpose,qualified,
linkQualification,closureComplete,metadata,sections,deviations. Qualification
flags are always false. `metadata` has the existing objects/imports/directives/
defaultLibraries shape; `sections` is this attempt's aggregate. `deviations`
has exactly unknownMachineObjects,unusedRelocationPointers,terminalNulSections,
all nonnegative integer counts (zero for successful strict mode). New wrapper
records never pretend that profile output was accepted by strict mode.
Result profileId is the actual mode used; snapshot profileId is always the
job descriptor ID. Purpose is always build_input_metadata_only in either mode.

The shared private parser may receive closed internal policy/meter state; no
caller-supplied limits or generic callback enters an exported API. Standalone
strict errors remain byte-contract compatible. New selection/job protocol
errors use existing bounded Error/site/context conventions: unknown selection
or duplicate mode is `LibraryInputsProfile`; a job resource overage is
`LibraryInputsSize`. No error includes raw bytes, paths or source text.
Fixed sites are metadata_profile (selection), metadata_repeat_attempt,
metadata_job_inputs, metadata_job_bytes and metadata_job_sections. Size errors
carry candidate/limit in the existing context. Any later inspect on a stopped
job throws LibraryInputsProfile/metadata_job_stopped with null context; snapshot
is still available. Standalone strict errors retain their original ordering.

## Interpretation and limits

Only the named profile has the proposed262144 per-input section limit; every
member is still processed and its65536 limit retained. Job2097152 counts strict
and profile attempts. Other existing range/overlap/member/name/token/directive
and unsafe DEFAULTLIB policies remain. No implicit selected-member whitelist.

Only normal COFF machine0 is additionally recorded as UNKNOWN, never AMD64.
Only a non-directive section with relocation count0, overflow flag clear and
headerTableEnd≤pointer≤memberEnd can retain an unused nonzero pointer without
dereferencing it. Other relocation and all line-pointer rules remain unchanged.
Only one final NUL after a nonempty, valid ASCII/optional-BOM and closed-quote
directive prefix is interpreted as a terminator; interior/double/hidden-tail
bytes and all other unsupported text still fail. Count every original byte in
the existing directive budget and never modify input bytes.
Nonempty means at least one lexical byte after optional BOM removal, not at
least one token: ASCII spaces followed by one NUL remain valid empty options.
Bare NUL and BOM-only+NUL fail; BOM+space+NUL is allowed. This does not infer
the unpublished text of any measured section.

FIRST must cover both old strict parity and these exact selection/resource/
sticky/interpretation contracts before producer changes. All tests remain
unrun until a separately reviewed bounded code-check admission. New profile
parsing, fixed32 compatibility, DEFAULTLIB closure, compiler/link/MT, real
worker/model/app/device and full desktop gates remain separate and unqualified.
