# Finite JSON spelling verification, 2026-10-25

Refs #9 (M05.01/M05.05), #5 (M01.05 supporting), root claim
[6403353570](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6403353570).
This packet follows open PR177 at `25f62147`. **Host gates pass; both fresh
attempts fail during source copy before import or SDK execution.** No
phone/backend/profile acceptance is inferred.
The [previous failed SDK observation](SDK_FORMAT_TOKENIZER_VERIFICATION_2026-10-25.md)
and all failed attempts remain retained.

## Change and reason

The old finite pattern requires literal spaces in the original Dialogue text.
The authenticated SP raw vocabulary has no ASCII-space pieces. A separate
representation/forcing matrix now tests that mismatch before changing the app.
The [bounded spelling contract](FINITE_JSON_SPELLINGS.md) preserves canonical
branches within the unchanged compilation budget and adds equivalent
space/non-ASCII string escapes. Expansion may trigger the existing null/fallback
path for a previously compilable schema. All original corpus forms pass. Engine
schema, exact user speech, actor/audience scopes, event/claim distinctions,
generation budgets, ownership fences, local-only operation and dependencies
remain unchanged. Explicit `no_forcing` is a host control, not a production fix.

Four new Rust integration tests cross actual proposal parsing, intent/Engine
validation, commit, observer filtering, replay/restore and idempotent retry.
Equivalent space/BMP/paired-surrogate spellings commit the exact same speech;
literal backslash-u, changed speech, malformed pairs, privileged/incorrect
operations and escaped remote-observer identifiers still refuse without canon
mutation. Their scripted narrator deliberately exercises the existing safe
fallback; these are synthetic-provider contract tests, not model-quality proof.

## Original-preserving native matrix

The new pure probe binds original corpus bytes and the exact old sidecar. It
keeps all13 schemas,215 rows (119 positive /96 negative) and three refusal
fixtures. SPACE_ESCAPES rewrites only actual spaces inside valid JSON string
lexemes. Strict typed decoded equality is required; malformed/duplicate/nonfinite/
unpaired/over-budget inputs remain unchanged and marked NOT_APPLICABLE. Original
hash/size correspondence remains for every row. Added forms never replace the
ORIGINAL controls or credit an unencodable negative as a rejection.

SPACE_ALTERNATIVES adds equivalent JSON escape branches only after checking the
old codec's restricted literal/group language and JSON-string position. DISABLED
forcing validates the exact pinned public-generated grammar shape, prefixes the
documented Lark directive, and calls the public Lark factory. No guessed JSON
option, raw pointer or ABI shortcut is used. Pinned public source:
[regex/Lark generation](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/api.rs#L30-L39),
[regex factory](https://github.com/guidance-ai/llguidance/blob/29e33a219f77be1cc37d8394630440f448d19945/parser/src/api.rs#L332-L336).

Each actual native job has a new source/input-bound private grant, the existing
verified1.3.0 wheel, a Job-assigned stdin barrier,180-second deadline and262144B
output cap. No inference engine or SDK is loaded. The callback remains synthetic
greedy raw-piece encoding, not an SP/SDK-equivalent encoder. All eight jobs have
known cleanup and stderr0. Result columns overlap; they are not summed coverage.

| Candidate spelling | Pattern | Forcing | Checked | Mismatches | Unencodable | Runtime failures | Status |
| --- | --- | --- | ---: | ---: | ---: | ---: | --- |
| Original |Old |Default |182 |0 |28 |27 |failed |
| Original |Old |Disabled |187 |0 |28 |10 |failed |
| Original |Space alternatives |Default |187 |0 |28 |0 |mismatch |
| Original |Space alternatives |Disabled |187 |0 |28 |0 |mismatch |
| Space escapes |Old |Default |188 |0 |4 |27 |failed |
| Space escapes |Old |Disabled |206 |1 |4 |9 |failed |
| Space escapes |Space alternatives |Default |211 |0 |4 |0 |mismatch |
| Space escapes |Space alternatives |Disabled |211 |0 |4 |0 |mismatch |

The last two controls check all119 positives and92 encodable negatives. Four
remaining unencodable rows are negatives, retained without rejection credit.
Statuses remain mismatch, not an all215-row model pass. Every transformed control
retains21 NOT_APPLICABLE negatives,24 SPACE_ESCAPED rows and170 unchanged rows.
This supports the representation correction, not a retrospective diagnosis of
SDK INTERNAL13 or proof of all possible SDK tokenizations.

## Production Kotlin and native pressure

The actual new Kotlin exporter checks every original positive and negative before
writing its create-only sidecar. Original corpus37,029B SHA256 is
`aac94a0ca1de3222a4774dd0a404b44f867d9712e6919c1a4ece553fdc7fc1a2`;
new sidecar8,591B SHA256 is
`60f2bd2c4fc268074db100f52ef95e26346c8f4beee0fef176ac61556a1e2981`.
The actual native byte oracle passes215/215 original candidates under the five
unchanged sanity gates, owner685ms/child0/known cleanup/stderr0. Its raw SHA256 is
`b3c2221685c10d0d9abf892b40f62d745065bcec68b2d883207d43c5b92b1a05`.

Using that **new supplied sidecar**, raw-piece ORIGINAL has187 checked /28
unencodable, zero mismatches/errors. SPACE_ESCAPES has211 checked /4 negative
unencodable, zero mismatches/errors/roundtrip differences with default and
disabled forcing. Both remain mismatch/child2 with known cleanup. Default raw
SHA256 is `f39141691413b5772e188da89137ef5aa14cd3e5f3ed4bf12fb695a2bb74d783`;
disabled raw is `169ad5b51470864f2277b502bcafcfb72348fd9a1c98a0558b4dac5282221b5c`.
ORIGINAL in this probe means no additional sidecar transformation; it does not
mean the old production pattern.

The optional actual Kotlin pressure export is83,980B, SHA256
`ba4a2fa41b000352e81f08fe015a4db7adf0412834908d5dacc5880af50c8e32`.
It contains the complete32,761-byte /2,519-space boundary pattern and two
positive/three negative candidates. Native byte matching passes all five,
owner577ms, raw SHA256
`7a375cce12515cc2d9291337cd31288c8cee235b0ce9113639cb8bf7bd96326a`.
Model-piece escaped matching checks four rows with no mismatches/errors; one
malformed unencodable negative remains uncredited. It returns mismatch/child2,
owner3469ms, raw SHA256
`04e84c2eb67fa45bfea080e9be30255f706e381e847c2f5ce4fb3f7939dfcb54`.
This is native compiler/matcher pressure, not a raised application output cap.

## Host and package checks

| Check actually run | Result / owned duration |
| --- | --- |
| Focused probe/comparator/oracle tests |67PASS,1045ms |
| Full CPython3.14.7 suite |967PASS /91.042s runner /92293ms owner |
| Cargo fmt |PASS5017ms |
| Clippy core all-targets with existing host feature |PASS16789ms |
| Rust core with existing host feature |365PASS /4 historical capture-only ignores,75528ms |
| Receipt JVM |528PASS /48 suites /0F/E/S,111047ms |
| Regular JVM |470PASS /43 suites /0F/E/S,92729ms |
| Receipt APP+TEST build |PASS73370ms |
| Regular APP+TEST build |PASS67330ms |
| Receipt lint/dependency/analyzer |PASS79117ms,0errors/19warnings |
| Regular lint/dependency/analyzer |PASS72905ms,0errors/9warnings |
| Receipt APK audit /signatures |PASS996 /811ms |
| Regular APK audit /signatures |PASS935 /747ms |

All final check owners above complete0 with known cleanup/stderr0. Full Python
raw SHA256 is `6adfabe7b105e4ae3eb9c6fc4bfb2c246ec13753109445fa443b075c3856b160`;
all148 captured Python source hashes are unchanged. Rust raw SHA256 is
`9f97569765112b85d51a2cd3aba7462f01edf71e21b6a315e2bfad16717ee706`.
Actual commands use locked/offline Rust1.93.1, explicit `--features host`, pinned
Java21, offline Gradle/no daemon/two workers, existing SDK and no provisioning.
Both Android profiles use the existing verification flags and lint9.4.1. Exact
argument arrays, XML and source bindings remain private local evidence.

Failures retained: the author's offline Gradle mini-project cannot resolve an
uncached build-only annotation dependency and downloads nothing. Its first
direct compiler run passes20 tests with a larger test stack; a meaningful default
stack rerun then finds19 passes/one Java Pattern stack overflow at maximum-length
matching. The test correction retains exact boundary math/compilation and64-space
matches; the final default-stack direct compiler run passes20 tests. The native
boundary above supplies the actual maximum matcher result. No JVM/application
stack/profile limit is raised. The root's first Clippy command omits the existing
host feature and finds a pre-existing host-gated test import; the corrected
command passes without a production dependency or source fix.

Codec source SHA256 is
`4d2a5e531c78b99c7dd3d0f203460fa79194e07b8266e395d071b939ccb6364c`,
bound into worker source
`efc5f9217b22ed772b10805fdd83122d9afe8647c374e6db234209748865ea52`.
Eight actual Android compilation bindings match. Controller source attribution
is `44103b8c`;95-file source manifest SHA256 is
`85e9993dd4c7bb1ff563d97a1f682e8f1c053e5039e5d168d7f06df18b4ad6d0`.

| Profile | APP SHA256 | TEST SHA256 |
| --- | --- | --- |
| Receipt |`c9325b6a50483afc0d928ab3d16c14c5a43caebacc4a96d11f16328f976f15fa` |`e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d` |
| Regular |`1af7bd97a9c8f40b95387376181a4791d362a9459078036c183695245e39c26e` |`8c14c03502faee7661b58a6862c5b35e9fec6e6371e40b9c2718daadd56ad1e5` |

## Fresh emulator sequence

The new isolated plain-D profile retains8GiB RAM/4CPU/12GiB userdata/8GiB SD,
1800-second owner and sampled2-second40GiB floor on both drives. Independent
review verifies all95 sources/eight compilation bindings/four APK hashes and
the real setup→default SDK route. Preparation succeeds with known closure; old
targets/caches are not adopted. Preflight passes12 checks/44 client commands,
owner64989ms/worker0/known cleanup/output/stderr0, tiny source only/SDKfalse.

The separately frozen ordinary proposal binds those four preflight records,
the same live owner, current source/APKs and standing local-copy consent. Its
owner terminates at source-stream after202160ms, worker2, known cleanup and
complete output capture, stderr0. There are14 client records, no candidate
instrumentation and no candidate installs. The final client returns2 with64-byte
generic `stream_failed` output, remote exit unknown. Raw SHA256 is
`5a852cfa71b96d8c5094908134a271fa02f590692a627200053c43a74302eb0e`.
This supplies no cause or destination proof and does not test the new SDK codec.

Only the exact proposal-bound host owner is stopped. Its final result is
`stop_requested`,653549ms, worker1, cleanup/closure/output complete, with
15770 stdout/1062 stderr bytes and no guest-flush claim. Owner-result SHA256 is
`2caa3f51561aadc395bac3aea4cd170e64c3748b99c75e7fb6e2890231f6d432`.
That target is quarantined; no guest/model/cache/image is reopened or adopted.
The original95 executed sources are independently captured before later edits.

Plan adjustment under #9 comment6403922055 adds a
[passive failure trace](RECEIPT_SOURCE_STREAM_TRACE.md) before a new target.
The stage, client timeout/code and held-FD cursor can distinguish host observations
without treating a full host cursor as delivered bytes. All existing guards,
five-second reserve,150-second client ceiling and180-second parent ceiling
remain unchanged. There is no retry on the consumed target. The first private
host test launcher requests an invalid capture budget and is refused before any
child; its source is retained and corrected to the existing262144-byte ceiling.

Full model import, real SDK gift/Dialogue and reopen remain **pending actual proof**.
After the failure-trace integration, the full Python suite passes988 tests in
110.535s (owned112763ms/0/known cleanup/stderr0). Raw177237-byte output SHA256 is
`1713de233e72967cf5b1adcc67c3a249a4b64cbcbd75a10883ff68dd14468127`.
This includes delayed emission-clock/serialization failures preserving the
original timeout exception and successful output. The prior967-test run above
remains evidence for the first source freeze, not the later controller bytes.
All106 benchmark/test Python files captured by that later launcher are unchanged.
The new99-source/eight-compile snapshot at `a3c50643` has manifest SHA256
`b1c308aa71edba183ed8539a2721f081007c5a7febe564104e62a74807dac78f`.
Independent review verifies every current/captured source and all four APKs.
Before the new preflight actually runs, one freeze request refuses because the
owner descriptor has not yet been published, and one CLI launch rejects an
incorrect `--evidence-root` argument. Neither launches a receipt worker or device
command. The subsequent launch uses the documented `--evidence` argument.
## Second fresh attempt: client timeout observed

The new target retains the same profile, owner lease and storage guard. Its new
preflight passes all 12 checks / 44 commands, owned 81,361 ms / worker 0,
cleanup/output complete and stderr 0. Proposal SHA256 is
`f0f6b95626141610ff503543295f33e96a2106103fb08687877496ea36fdd8af`.
The separate once-only copy/SDK grant binds four preflight records and 108 inputs;
ordinary proposal SHA256 is
`084d755039c176ff43806ead3d625b5c5c15f38785fae2ef85bbc10871436113`.

The ordinary owner stops at source-stream after 201,550 ms, worker 2, known
cleanup and complete output capture, stderr 0. All 14 client records remain;
candidate instrumentation and installs are both zero. The final client has
330 stdout bytes, SHA256
`459783d7e6cf1748172861ebfbf3e2b75eddb54295a054e775a10c18bd5a251d`.
The strict parser accepts one failure trace followed by the original generic
failure. Its observations are:

| Field | Actual observation |
| --- | --- |
| Last entered phase | CLIENT |
| Expected source bytes | 2,588,147,712 |
| Pre-transfer held-FD source hash/size check | true |
| Client budget | 140,906 ms |
| Client timeout | true |
| Client return code | absent |
| Host held-FD cursor | 2,471,362,560 bytes (95.49% of source) |
| Total trace elapsed | 174,199 ms; not saturated |

After the transfer attempt, the cursor is 116,785,152 bytes short of the source
end (the earlier authentication already hashed the whole file). This establishes
a client timeout with a partial host read, not a destination byte count or remote failure
cause. No import proof, SDK invocation, Rust gift, Dialogue or restart is
qualified. It supplies no new SDK result for the prospective codec correction.
The earlier generic failure remains unexplained; this trace does not rewrite it.

Only the exact proposal-bound host owner is stopped. Final owner status is
`stop_requested`, 443,607 ms, worker 1, cleanup/closure/output complete,
15,783 stdout / 1,059 stderr bytes, guest-flush claim false. Owner-result SHA256:
`e54acdd4013e3e7f97c70d7ce8d1d81d9b7770379516cc0ad70557cbe84a97ee`.
The final sampled guard stays healthy; its SHA256 is
`19d67300ae26c94a29508b581f421c5fedf6427ad96447eae275d486162e5cbe`.
No dependent guest/model/cache/image read or retry occurs. Both new targets and
all earlier uncertain targets remain quarantined.

## Retention and next runnable work

The sealed private host set contains 414 files / 5,248,321 bytes. Its 66,773-byte
index SHA256 is
`9c0a5da4bc9dce617e1dd030ab93ca972c8707c56b544b89d839260b5dc118bd`.
The final device set contains 353 files / 1,161,123 bytes. Its 52,957-byte index
SHA256 is `907b8109fd6ce22b86e5025f77d1e534b1e76222d1a7d47677fbf81d0b6c24c7`.
Models, tokenizer/metadata payloads, runtime libraries, emulator images/RAM and
keys are excluded; nothing in these private sets is uploaded. Initial sealing
retains its valid host index but refuses a legitimate `owner-stdout-v1.bin`
diagnostic filename. That partial device directory remains. A corrected helper
admits only additional stdout/stderr-v1 suffixes and creates a separate device-v2
group; it does not overwrite the failed selection.

Independent sealed-evidence review rehashes all 767 indexed files with zero
mismatches and checks all 116 command metadata/stdout pairs, eight preflight
bindings and both final owner/guard links. Both ordinary attempts stop at
command 14 with zero candidate instrumentation and no dependent dispatch. The
unsealed partial first device group is retained but is outside that final audit.
Final review clarifies compilation-budget wording in the spelling contract;
that documentation-only change follows the executed `a3c50643` source freeze.
Its old captured document remains intact; no production code or APK changes.

M05.01/M05.05 partial implementation is in review; full acceptance stays unchecked.
Next runnable work is a source-bound original synthetic transfer probe on a
separately admitted fresh target, measuring the fixed local transport before
another full-model attempt. Compare bounded transport choices while preserving
private ownership, source authentication, one-shot claims, cleanup, the existing
150-second client / 180-second parent limits and reserve. This packet does not
shift clocks or increase deadlines. Resolve the measured copy gate before
qualifying real import, corrected Dialogue or restart.

At unknown inference ownership, dependent observations/retry remain prohibited.
Phone/ARM64/16KiB/quality/sustained performance and full milestone acceptance
remain open. No merge, release, new backend/dependency or access change occurs.
