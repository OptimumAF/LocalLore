# Public format observation and selected tokenizer controls, 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05 supporting). Root claim
[6402500798](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6402500798).
This packet follows unmerged PR176 at `1c3602fd`. It preserves the
[earlier ordinary Dialogue failure](LLGUIDANCE_LITERAL_VERIFICATION_2026-10-25.md)
and introduces no generation-budget, engine-authority or dependency change.
Full task acceptance and physical-phone qualification remain open.

## Implementation

The optional [V2 send record](LITERT_SEND_TRACE_V2_CONTRACT.md) counts only the
prepared public response-format kind: REGEX, JSON_OBJECT or OTHER. The hook runs
inside dispatch immediately before `Conversation.sendMessageAsync`, and reads
only `ResponseFormat.type.value`. Null and throwing observers preserve argument
identity, successful return and the original dispatch failure. The record
contains no schema, pattern, speech, token text or private exception. Historical
V1 records remain strictly readable. This observes the application argument; it
does not prove native grammar application or SDK resource release.

The new development-only selected-section reader checks the bounded container
directory before reading eligible tokenizer and LlmMetadata payloads. It
validates signed/shared FlatBuffer vtables, union and string bounds, section
alignment/nonoverlap, unique typed/untyped selection, and exact bounded HF
decompression where applicable. Original malformed-container fixtures prove
that valid unselected graph/weight payloads are not read by this reader.
Directory bytes necessarily precede detecting an invalid header alias.

The opt-in launcher separately authenticates the whole original source twice
on a held handle, checks path/handle identity, and writes only selected
derivatives to a new private directory. Full-source authentication reads weights;
it never publishes them. The owner assigns a Windows Job before releasing the
stdin barrier, with a 180-second deadline and bounded output. Reports and their
artifacts are revalidated. Private ancestry is rechecked after source passes and
before publication/readback. These are trusted local checks, not atomic
protection against a malicious same-UID process. A decoded-byte cap is not a
Python object-heap quota; resource admission remains external.

Stop metadata is interpreted through a bounded protobuf subset. Exact raw-piece
lookup resolves string references; unsupported encoder fallback refuses rather
than guessing. Stop order is preserved and the first singleton supplies EOS.
SP pieces and HF ID-to-token strings remain raw vocabulary, with no implied
decoding or equivalence to the SDK callback. No production tokenizer is added.
The [official-source research](LITERT_TOKENIZER_ORACLE_RESEARCH_2026-10-25.md)
records the pinned APIs, model-container format and fidelity limits.

## Checks actually performed

All process results below have child0, known owned cleanup and zero stderr
unless explicitly stated otherwise. Timings are whole process observations,
not phone or inference latency.

| Check | Actual result |
| --- | --- |
| Receipt JVM |521 tests /48 suites, zero failures/errors/skips;95,413ms |
| Regular JVM |463 tests /43 suites, zero failures/errors/skips;94,418ms |
| Receipt APP + TEST assembly |72,661ms |
| Regular APP + TEST assembly |71,189ms |
| Receipt lint + dependency/analyzer audit |85,222ms;0 errors /19 warnings |
| Regular lint + dependency/analyzer audit |69,401ms;0 errors /9 warnings |
| Receipt APK audit / both signatures |863ms /724ms |
| Regular APK audit / both signatures |936ms /704ms |
| Selected reader/core/launcher + identity regressions |61 tests,0.924s runner /1,380ms owner |
| Send/controller/environment regressions after APK pin |182 tests,27.890s runner /28,507ms owner |
| Eight original tiny-file identity replays |Eight stable two-pass receipts;210ms owner |
| Initial comparator + inherited oracle controls |46 pure tests;467ms owner |
| Corrected comparator + inherited controls |50 pure tests;413ms owner |
| Final full Python suite after mask correction |950 tests /73.117s runner /74,267ms owner; zero failures/errors/skips |
| Actual selected-model extraction |11,654ms; authenticated source twice; native false |
| Actual bounded SP/stop interpretation |1,559ms; native false |

The 61-test raw stdout SHA256 is
`ab55365c1ebb471066bb43e21a67e41b98c17fe311157351b60fbb288d173e91`;
the 182-test raw SHA256 is
`ee43cd822433590f91a1935ebda4c078a5d31558568eee787959faece80f550e`.
These overlapping selections must not be added as distinct full-suite coverage.

Gradle ran pinned local Java21, offline, no daemon, two workers, existing wrapper,
explicit SDK, no toolchain/SDK download, and lint analyzer9.4.1. Receipt flags
were LiteRtVerification, ModelSetupVerification, ModelVolumeVerification and
ModelReceiptVerification; regular flags were the first two. Actual command
arrays, JVM XML, lint XML and audit/signature stdout are retained privately.
The seven Android compilation source hashes match their captured source bytes.
No Rust source changed; no fresh Rust execution is claimed by this packet.

The first broad Python run on CPython3.14.7 recorded881 tests and one error in
the actual tiny-file path/FD identity fixture, owner81,944ms/return1 with known
cleanup. Its raw SHA256 is
`f0dfa317ba5162e53ec3494d001fd01cb62ef63e56661e01d26ec89ed337c258`.
Eight new original tiny files reproduced four path-vs-FD ctime differences;
all eight birth times and remaining identity fields matched. The production
fingerprint now uses Windows birthtime where available, retaining legacy Windows
ctime fallback and POSIX ctime. All dev/inode/mode/size/mtime checks and both full
hashes remain. This follows the
[Python3.14 stat contract](https://docs.python.org/3.14/library/os.html#os.stat_result).
The original failure and diagnostic readbacks are preserved. A subsequent broad
run returned0 with known cleanup, but its unittest stderr details were not
retained; it is not credited as a final counted suite here.
The later946-test suite passes with complete retained stdout at `364a0232`.
After the actual native API correction, the final950-test suite passes at
`b088fe50`, with all146 captured Python source hashes unchanged before/after.
Its raw stdout SHA256 is
`035a5e975357121b4b58bc860e9c08e1a54bb2eaaa875a09122b1cea19067878`.
No failed or incompletely captured prior attempt is replaced by this result.

## Actual selected artifact

The admitted original Gemma file is2,588,147,712 bytes, SHA256
`181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c`.
Extraction source commit is `4c0dcac319571e65905313547e718e444395008e`.
Both full hashes and all source identity checks passed before publication.
The frozen proposal SHA256 is
`fb3f67dd748c550e434a70fc3c579d3e49b979cebef9a77b303de2449c5f2021`.

Container version1.5.0 has a1,872-byte header and12 sections. The uniquely
eligible tokenizer is **UNTYPED SENTENCEPIECE**, not HF JSON. Its selected
range is[32768,4721781),4,689,013 bytes, SHA256
`e594c8a90eb08d8bda498ff4747977dc827ae0c3c56b5c0d41a605a22d02ef03`.
LlmMetadata range[16384,28576) is12,192 bytes, SHA256
`00603838ac80fadd374ff3d7b6108cfa765bf1a76adfb9df95b3387d0d7e386f`.
No graph/weight artifact was emitted; all derivatives remain private.

The bounded reader observes262,144 raw vocabulary pieces /2,316,295 bytes.
Length-prefixed vocabulary SHA256 is
`1c42512eb91310b8b6b6622d6fd26c73aa8c3b216dab9f23a1c6797d858d8197`.
**Zero pieces contain an ASCII space byte**;31 contain a tab and31 a newline.
Metadata resolves three singleton stops and EOS1, with a start reference present.
Interpretation stdout SHA256 is
`0189400e90bac2dfe42ccdbfba9340783abfdd9ae97c3e80da36114b43f998fb`.
This supports testing space representation at the raw vocabulary boundary. It
does not diagnose SDK INTERNAL13, prove mask behavior, or authorize replacing
the original positive corpus with easier samples. HF semantic loading is not
applicable to this actual selected artifact.

## Frozen Android artifacts

| Profile | APP SHA256 | TEST SHA256 |
| --- | --- | --- |
| Receipt |`5cec5c77e3f53f75ac9e458b51a185590f76a2e217ca225a59a2ef8a5efb903d` |`e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d` |
| Regular |`2cf48fedd5028cb69c3b57b6d69561250a5c3f97be49f225068bd15f847b85b8` |`8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5` |

Receipt APP/TEST sizes are75,041,504 /2,056,615 bytes; regular sizes are
74,992,104 /1,869,719. The new94-file device-source manifest with seven
compilation bindings has SHA256
`28d5f2a9382ddc99f6f23c1ebdccf8ba29c4bb9dd2fd45fd906bbfc9e8e617cc`.
Its attribution is `8ca548cc`. Model weights and raw device diagnostics are
excluded from Git. This packet performs no merge or release.

## Fresh environment and preflight

A new plain-D target uses the existing8GiB RAM /4CPU /12GiB userdata /8GiB SD
profile, with a1,800-second proposal-bound owner and a2-second sampled guard
requiring40GiB free on both drives. Preparation completes with known child and
preservation closure. Independent source/evidence review matches all94 device
source hashes, seven compilation bindings, two receipt APK hashes and retained
521/463-test XML. The guard is sampled observation, not a storage reservation.
No old target, image or model cache is adopted.

The first preflight proposal is refused locally because my private APK copies
used different basenames from the controller's exact contract. No controller or
ADB command was dispatched. The refusal and helper remain retained. New
create-only same-byte copies use `app-debug.apk` and
`app-debug-androidTest.apk`; a separate helper/evidence folder qualifies the
subsequent attempt, without changing controller source or its filename checks.

Corrected preflight passes44 client commands and all12 app proof checks, with
four guest CPUs, tiny probe only, SDKfalse, full-model source counters0. Its
owner takes48,476ms, worker0, known cleanup and complete output, stderr0. A
separate proposal/grant binds those four preflight records, the same live owner,
the exact current source/APKs and existing local-copy consent. It admits the
ordinary import/Start/Dialogue/reopen sequence under the unchanged budgets.
This preflight alone establishes no SDK inference or scene/restart result.

## Native raw-piece controls and retained checker failure

The comparison authenticates the preserved LLGuidance1.3.0 Windows ABI3 wheel
and every installed file before import, using the existing verifier. Wheel
SHA256 is `1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`.
Each independently owned process has a new source/input-bound private grant,
stdin release barrier,180-second deadline and262,144-byte output cap. No
inference engine or SDK is loaded. Both schema and finite-regex modes retain
all13 original schemas,215 samples (119 positive /96 negative) and three
refusal fixtures. Five byte-tokenizer sanity checks pass in each process.

Original corpus-file SHA256 is
`aac94a0ca1de3222a4774dd0a404b44f867d9712e6919c1a4ece553fdc7fc1a2`;
the exact Kotlin-exported finite-pattern sidecar SHA256 is
`d2989fa17c242bf58e7ff902e3267b05d87401a0dbe6abc4de637c6f9a13918e`.
Index/schema hashes bind each sidecar row before insertion into a validation
copy. Original sample/schema strings are unchanged. The comparison's
`corpus_json_sha256` binds its compact input dictionary, separately from these
raw-file hashes. Output retains only indexes, enums, counts, sizes and hashes.

The actual SP artifact has no HF JSON, so only raw-piece mode is exercised.
The public Python wrapper uses those exact raw pieces, EOS1, no BOS, no special
IDs and `slices=[]`. Its callback performs synthetic longest-piece UTF-8
segmentation; it is **not a SentencePiece encoder or SDK-equivalent tokenizer**.
Unencodable originals remain present with acceptednull, first missing byte and
an independent encodable-prefix mask attempt. They never count as negative
rejections. Mask/state/EOS inconsistencies remain failures. Callback exceptions
become a sticky closed failure and never cross the Rust callback bridge.

The first real runs fail: JSON4,679ms and regex3,203ms, both child2/known cleanup,
all215 rows retained but zero fully checked. A behavior-preserving call observer
finds32,772-byte masks for262,144 words, while the initial checker expects32,768.
Its separate runs also fail and remain retained. This is a demonstrated
**host checker API mismatch**, not evidence of truncated SDK masks.

Pinned Python `compute_bitmask()` returns the complete SimpleVob storage;
TokTrie requests capacityV+1 and allocation uses floor(capacity/32)+1 words.
The exact Python storage size is therefore `4 * (floor((V+1)/32)+1)`, unlike
the pointer API's bound. Sources:
[Python binding](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/python_ext/src/llmatcher.rs#L426-L430),
[token-set capacity](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/toktrie/src/toktree.rs#L239-L246),
[storage allocation](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/toktrie/src/svob.rs#L252-L256).
Correction `b088fe50` requires that exact pinned size; adversarial boundary tests
reject other lengths and prove padding cannot authorize an out-of-range token,
replace missing in-range EOS, inflate prefix counts or hide sticky errors.

The new authenticated runs observe:

| Mode | Whole process | Full samples checked | Mismatches | Unencodable originals | Runtime failures | Result |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| JSON schema |4,220ms |187 |5 |28 |3 |failed /matcher_state |
| Finite regex |3,057ms |182 |0 |28 |27 |failed /matcher_state |

All13 grammars compile in both modes. Checked samples have zero roundtrip
differences. Runtime failures include prefix attempts, so these overlapping
columns must not be summed as independent samples. Both return2, with known
cleanup and stderr0; neither is an all-corpus pass. Final raw stdout hashes are
`a1a0c368c65f1777b9c838e8d06be964135d608ce5ac92133ac0d10bb545b085`
and `080d3448be3196cd794d78b7b7e8e46c58c766f6d862b11ee98e8d082fc77930`.

For the original425-byte ordinary schema, the86-byte positive first becomes
unencodable at byte58, an ASCII space, after15 synthetic greedy pieces. Its
finite-regex prefix attempt fails matcher_state; accepted remainsnull. This is
a host representation observation, **not a conversion of SDK chunks into token
IDs or proof of the SDK failure location**. Python's callback is additionally
treated as canonical by the native wrapper, despite being synthetic here;
forcing behavior therefore remains a fidelity gap. See the
[canonical default](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/toktrie/src/tokenv.rs#L83-L88).
No original positive is removed, no easier sample replaces it, and no production
serialization change is made by this packet. The next runnable control is an
equivalent JSON escape representation plus explicit forcing controls, preserving
decoded speech and the original positive/negative corpus before a new SDK attempt.

The executable host entry points are:

```text
python -B -E -m unittest discover -s scripts/tests -v
python -I -S -B scripts/litert_tokenizer_oracle.py extract
  --proposal <fresh-private-proposal.json> --authorization <matching-private-grant.json>
```

The second command requires the exact closed proposal/grant schema in its
launcher; it neither chooses a model nor grants itself admission. The native
comparison is the explicit library API
`compare_tokenizers(verified_module, None, raw_pieces, observed_eos, corpus)`
and `validate_report(report, corpus)`. Its caller owns verified-runtime admission,
the stdin barrier, process deadline, output capture and input/source hashes.
This packet's private source-bound worker used the existing `verify_runtime`,
`NativeBackend` and five byte controls before those calls. The HF-JSON API branch
is tested with fakes only; no actual HF artifact result is claimed here.

## Actual ordinary scene and stop

The new cohort qualifies **56 checks across three methods**: preflight12,
IMPORT16 and ordinary START28. Full import takes113,880ms in the app proof /
114.712s runner. Ordinary Start/gift takes97,385ms proof /97.787s runner.
The production setup UI opens the real play activity and actual SDK proposals
are validated and committed by Rust: revision1, one receipt, zero repairs,
fallbackfalse. START records two DONEs, two drains, two known Conversation
closes, one known Engine close and UNCERTAIN0, followed by the qualified full
model postcheck. These are synthetic-emulator observations, not phone latency.

Dialogue fails after65.338s. The failure-only V2 record now directly observes
REGEX1, JSON_OBJECT0, OTHER0, lastREGEX at the prepared public send argument.
Argument preparation and the public async call both return. The wrapper declares
INTERNAL13 after15 validated chunks /58 UTF-8 bytes, with one DIRECTOR request,
context4096, output cap350, prompt6811B and schema425B. Chunk/byte counts are
not token counts. The record proves no native grammar/tokenizer behavior.
DONE/drain/known Conversation close/known Engine close are0; UNCERTAIN2.

The ordinary controller stops at `instrument-ORDINARY_DIALOGUE`:446,078ms,
worker2, known host cleanup, output complete, stderr0,46 completed client
records. Raw failing command46 is6,664B, SHA256
`91643f8fc21ba0c1625749377d5622f1fe12a7ed047d7ba0e7d28303059f7378`.
**No Dialogue, ordinary reopen, post-failure canonical state or model/cache
observation is qualified.** Revision1/gift is the last qualified canonical
state; do not infer an absent second receipt or a successful restart.

Only the exact proposal-bound host owner is stopped after uncertainty. Its
terminal record is `stop_requested`,724,399ms, worker1, known cleanup, complete
output and preservation closure verified, guest-flushfalse. Its1,876 stderr
bytes remain private. Owner-result SHA256 is
`2106bce9c093a4ccf913b1bbb6684f8a39831d08c8c91347f84f4fd65aa9f32a`.
The final sampled guard is healthy, monitor_failedfalse, with C:87,552,225,280 /
D:139,058,237,440 bytes free, above the unchanged40GiB floors. Host termination
does not establish acknowledged SDK drain/close. This target and its model,
cache and mutable backing files are quarantined; there is no retry/adoption.

Independent readback matches all90 retained client stdout sizes/hashes/order,
the preflight→import→Start→worker raw proof chain and the single adjacent V2
failure record. Client0 is not the runner/proof oracle. Two successful preflight
installation clients separately retain151 /161 stderr bytes; no blanket zero
client-stderr claim is made. The closed device evidence index selects240 host
metadata/raw files /648,408 bytes, excluding weights, tokenizer derivatives,
AVD disks/RAM/cache/keys. Index SHA256 is
`c06f5953c86d467004ace2c70a71c5892b9796412c04e8e8dc45a76e0fc03e48`.
The separate host source/check/APK/control selection contains286 files /
156,850,969 bytes, index SHA256
`c1e2b1875a8b9ade4355695c42b5d794e0bf11da53d1ceee66debbf1bdb7bce1`.
It excludes actual model/tokenizer/PB payloads and emulator backings; hashes and
selected metadata are preserved locally, not uploaded as public raw diagnostics.

M05.01/M05.05 and supporting M01.05 are partial implementation/verification for
review. Complete Dialogue/reopen, phone/ARM64 execution,16KiB-page qualification,
sustained resource/performance and narrative-quality gates remain unchecked.
No architectural authority, local-only behavior, task acceptance criterion or
owner-only merge/release authority is changed. Claims hand off through #9/#5;
the next bounded task is the representation/forcing control described above.
