# Explicit archive-alignment metadata v2 contract

Historical source contract below. Its subsequently implemented parser/API
passed a separately approved [224-group synthetic packet](D04_MSVC_ARCHIVE_ALIGNMENT_V2_VERIFICATION_2026-11-02.md).
That one-run grant is SPENT; SDK/native/link/quality qualification is not established.

Refs #25 D04.01/.02/.04 supporting; #31 D09.03 supporting; #21.
Root claim6588599049; `prep/msvc-archive-alignment-v2`, accepted base
`d3862614cb6654305d88d44901eda36b83f2a4e8`.
**SOURCE CONTRACT ONLY. No new parser, FIRST, execution or acceptance exists.**

## Evidence and interpretation

The separately approved [padding V2 packet](D04_UCRT_PADDING_V2_VERIFICATION_2026-11-02.md)
passed6 parent/24 Node gates and observed the SAME pinned285588B `ucrt.lib`:
member4/header98452, body[98512,98821),309B, alignment byte0 at98821. Its grant
is SPENT. All prior failed results and source copies remain preserved.

The current `library_inputs.mjs` archive parser checks LF(10) for every required
alignment byte in BOTH strict-v1 and metadata-v1. Its refusal is consistent
with the observed NUL(0); the successful observer does not pass that parser.

The [Microsoft PE/COFF Archive Member Headers specification](https://learn.microsoft.com/en-us/windows/win32/debug/pe-format#archive-member-headers)
describes even-address headers and LF alignment padding. The current primary
[LLVM Archive.cpp reader](https://llvm.org/doxygen/Object_2Archive_8cpp_source.html),
`ArchiveMemberHeader::getNextChildLoc` at source564–587, advances by the member
size aligned to2 without testing the skipped byte. These sources were refreshed
on2026-11-02; LLVM's page identifies itself as24.0.0git. This is source reading,
not an executed linker/compiler test, and does not establish this input's
conformance, object validity, target ABI, selected closure or linkability.

Keep strict-v1 and metadata-v1 exactly as accepted. Add a DISTINCT metadata-v2
interpretation that explicitly reports the observed alignment deviation.
It is not a repair, normalized input, hidden fallback or claim of conformance.

## Initial ownership and preserved versions

First owned path is this NEW contract only. After independent contract review,
freeze NEW `native/llama-worker/library_archive_alignment_v2_first.mjs` on a
separate serialized author branch BEFORE producer edits. Proposed producer
ownership is ONLY `native/llama-worker/library_inputs.mjs`, reusing its current
bounded parser and job implementation once. No second parser or copied body
decoder. Coordinator owns integration; reviewers read without concurrent edits.

Preserve existing `inspectLibraryInputs`, `createLibraryMetadataJob`,
`MSVC_LIBRARY_METADATA_PROFILE`, their input/mode selection, LF refusal,
result/snapshot/descriptor shapes, error categories/context, bounds and ordering.
In particular the existing metadata FIRST F03 explicitly rejects the v2 ID
through the OLD factory; keep it unchanged and passing. All original legacy,
metadata-profile, dependency and observer assertions remain intact.

No changes to `library_metadata_dependencies.mjs`, its v1 result projection,
existing observer/collector/roster/descriptor, profile-v1.json, worker/runtime,
engine/storage/memory, desktop/Android consumers, dependencies or locks belong
to this first slice. The existing v1 projection MUST refuse v2 data. Any later
consumer/projection/observation requires its own versioned contract, FIRST,
source binding and applicable admission; old grants are never reused.

## New closed API

Add ONLY these public exports beside the accepted API:

```javascript
MSVC_LIBRARY_METADATA_PROFILE_V2
createLibraryMetadataJobV2(profileId)
```

The new deeply frozen plain-data descriptor has exactly id,version,purpose,limits:
id `msvc-library-metadata-v2`, version2, purpose `build_input_metadata_only`.
Its limit keys and values EXACTLY match metadata-v1. No caller override is added.
Neither descriptor nor a parsed result grants file access, generation or build
authority. These are development Buffer-only interfaces, not application IPC.

New factory accepts ONLY the exact primitive-string v2 ID, without coercion,
trimming, case folding, aliases, wrapper objects, implicit v1 upgrade or caller
limits. Reject invalid IDs using the existing fixed profile error behavior.
It returns the existing frozen inspect/snapshot job interface. New job accepts
ONLY `strict-v1` and its own exact v2 ID as inspect modes; OLD job continues
accepting ONLY `strict-v1` and its own v1 ID. Unsupported mode attempts retain
the existing stop behavior. No renderer or environment selector is introduced.

The same entry-identity WeakMap, per-mode duplicate-attempt refusal, input/
section/attempt charging, stop state and exclusive byte ceilings apply to both
factories. No identity deduplication, second budget, reset/refund, cap change or
preallocated caller-supplied successful metadata replaces actual parsing.

`snapshot()` keeps exactly profileId,inputCount,inputBytes,attempts,sections,
stopped; new job profileId is v2. Snapshot copies remain frozen. Results keep
exactly profileId,purpose,qualified,linkQualification,closureComplete,metadata,
sections,deviations, with all three qualification flags FALSE. Metadata retains
objects,imports,directives,defaultLibraries and existing canonical ordering.
Parser results remain ordinary per-call data objects, as in the accepted API;
this adds no result-freezing requirement. Mutating a returned result must not
change a job's counters/stop state, descriptor or another parse result. Only
the descriptor, job interface and snapshot copies are required to be frozen.

## Narrow parsing difference

ONLY the new job's v2 mode changes required archive alignment interpretation:

* For an odd member end, require exactly one in-bounds alignment byte. Accept
  only LF(10) or NUL(0), then advance once to the next even address. Missing or
  every other byte value still refuses with the existing fixed padding sites.
* No pad is consumed for an even end. No scanning for another header, fabricated
  padding, resynchronization, mutation, byte deletion or unknown-member skip.
* Header fields/end marker/signature, body/next-header bounds, longnames/indexes,
  machine/import/BIGOBJ/COFF/directive rules and existing size/work accounting
  otherwise remain unchanged. The accepted v1 metadata COFF compatibility
  cases apply unchanged in the new v2 mode; this adds no other compatibility.
* Count every NUL required alignment byte across archive members, including
  linker/longnames members, not embedded body/longname/directive NULs. The count
  may exceed objects+imports. The new v2 result's deviations has exactly the old
  three keys plus `nulArchivePaddingMembers`, an integer0..65536. LF contributes0;
  raw COFF input contributes0. No raw member bytes/names/paths enter this counter.
* Strict mode, even in a v2 job, keeps the EXACT old three deviation keys and
  LF-only behavior. Old v1 mode/standalone strict results never gain the new key.
* A later body/header error is still a refusal. Do not turn a partial archive or
  a deviation count into successful metadata. Retain existing failure charges
  and fixed context rather than inventing partial success or new authority.
* Keep envelope traversal before object-body parsing. In particular a strict
  NUL-padding refusal occurs before any COFF sections are declared/charged,
  even if an earlier member would otherwise be a valid object. The new v2
  mode may parse/charge bodies only after the whole archive envelope passes.

Internal reuse may parameterize private parsing/job helpers, but only the new
fixed v2 mode can set the private NUL-alignment policy. Extra user arguments,
fields, metadata/profile-v1 selection or JSON cannot enable it elsewhere.

## Independent FIRST before producer

Independent FIRST must call the real old/new APIs against original synthetic
Buffers; no SDK or copied private payload, filesystem, children or model. Freeze
actual cases and exact counts BEFORE implementation. Required matrix:

1. Closed, deeply frozen descriptor/interface/snapshot and closed ordinary
   per-call result data; unchanged limits
   and false qualification; old factory rejects v2 and new factory rejects v1.
   Reject malformed/coercible IDs/modes without evaluating coercion hooks.
2. Genuine structurally valid synthetic odd-body archives: LF succeeds in old
   strict/v1 and new strict/v2 with exactly appropriate shapes; NUL succeeds
   ONLY in new v2 with the explicit counter, while every strict/v1 path refuses.
3. Check every other alignment-byte value, missing/truncated required padding,
   malformed header end/signature, even-end no-skip behavior and extra garbage.
4. Multiple odd LF/NUL members, linker/longnames framing and correct next-member
   traversal; exact NUL count and same underlying object/directive metadata.
   A later malformed/unsupported member cannot be silently skipped or published.
5. Input immutability; no sanitization/fallback; raw COFF/LF paths and unchanged
   v1 compatibility deviations. No fixture represents native build acceptance.
6. Same Buffer in two modes charges input once/attempt twice, repeated-mode
   refusal stops; distinct equal/subarray entries charge independently; errors
   retain reservations/declared sections, caps and no-reset behavior. Preserve
   old complete boundary suites and explicitly cover the new factory's route.
7. New v2 data, including forged v1-labelled data retaining the fourth deviation
   key, cannot satisfy the unchanged v1 dependency projection. Historical
   v1 descriptor/result/refusal and all original FIRST assertions remain intact.

Tests must fail for actual wrong policy/shape/accounting, not merely missing
imports or unavailable setup. Any future test execution must report actual
counts and distinguish setup/compile failure from behavioral evidence. No RED,
GREEN or parser acceptance is claimed by this source-only contract.

## Admission and later work

There is NO new test child, import, parser execution, SDK observation, native
build/link, worker/model/app/device/OS/render work or output cap approval here.
Before code checks, prepare/review exact programs, tools, source/fixture/memory/
log bounds and fresh full reservations under the current2540KiB evidence cap,
original target baseline and every unchanged limit. Retain all failed output.
No deletion, evidence relocation/reclassification, cap reset or automatic retry.

The PR364 V2 grant is spent. Its original local reader/supervisor/history remain
frozen. A changed public parser hash cannot be used with those frozen guards.
Any later input observation or changed projection needs new exact source pins,
closed output version, unchanged-input identity and separate finite authority.
Do not infer that a v2 parser now accepts the observed library without an actual
separately admitted measurement. Keep AuthorDisabled and full D04/D09/desktop,
physical-device and human-quality gates open until their real criteria pass.
