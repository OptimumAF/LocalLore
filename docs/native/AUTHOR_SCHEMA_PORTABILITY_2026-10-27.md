# Initial-world schema portability

M09.02, with supporting M10.02/M10.03. Bounded correction in review; owner
acceptance and full task checklists remain unchanged. This follow-up depends
on unmerged PR #225 and preserves its native authoring boundary.

## Problem and correction

The original author schema contains two `uniqueItems:true` predicates, for
character and world-fact `known_by` arrays. Rust sends that schema through the
existing structured author request. Open text and variable-length arrays make
the finite-regex codec decline it, so the SDK receives public JSON Schema.
Pinned LLGuidance1.3.0 does not implement `uniqueItems` under its strict defaults.

The correction replaces only those two predicates with array-valued enum
choices: all64 nonempty unique permutations of references0..3 for character
visibility, and all65 choices including empty for fact visibility. Original
type/items/min/max constraints remain. Rust still checks actual actor existence,
self knowledge, route reachability, world bounds and complete initial origin.
No compiler leniency, ignored keyword, null schema, mechanical grant, new repair
or generation-budget change is introduced.

Order matters in the original/edited proposal provenance and origin hash, even
though materialized knowledge is a set. Every previously accepted typed array
ordering remains representable; restricting output to sorted subsets would
silently narrow that domain. The request remains `initial-world-v1`,1024 output
tokens,8192 output bytes and120 seconds. Its compact schema is3456 bytes; the
bundled source is8117 bytes. No dependency, model, SDK or runtime pin changes.

Primary sources: the [implemented vocabulary and constant-array compiler](https://raw.githubusercontent.com/guidance-ai/llguidance/v1.3.0/parser/src/json/schema.rs),
[strict keyword check](https://raw.githubusercontent.com/guidance-ai/llguidance/v1.3.0/parser/src/json/shared_context.rs),
and [pinned LiteRT constrained-decoding build](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/runtime/components/constrained_decoding/BUILD).

## Actual checks

The unchanged4869-byte bundled schema, SHA256
`8f0438f091039118e180f1a3189ea5a958f2f730e8a97848fde2d48835895421`,
actually compile-refuses in an owned isolated native process:334ms, return2,
`case_compile`, known cleanup and0 stderr. All five native controls pass.
No model or Android SDK runs in that probe.

The old local oracle runtime is absent at the inspected historical C: paths.
The existing exact MIT-licensed LLGuidance1.3.0 code wheel is restored after
fresh [official metadata](https://pypi.org/pypi/llguidance/1.3.0/json) and
[license](https://raw.githubusercontent.com/guidance-ai/llguidance/v1.3.0/LICENSE)
checks:2789946 bytes, SHA256
`1d1cd1c8618d1a13605d3e057c978651e551c8c469b481ee4041f1d6c436002d`.
The existing launcher verifies every wheel/extracted file before native import.
This restores an isolated developer tool, without a global install, app
dependency or model download. Its provisioning/RED evidence is separately
preserved with zero missing/mismatched originals, copies or ZIP members.

Executed code `aa535d94` passes6 new integration tests,3 exporter tests and12
existing author-world adversaries,21 total, with0 failures/ignored. Focused
Clippy, formatting and diff checks pass. The bounded owner returns0 in24584ms
with known cleanup/capture,0 stderr and2000 unchanged historical tracked inputs;
879 compiled inputs include the two new Rust sources. A prior actual attempt
passes5/6 integration tests and fails a test oracle comparing derived prose
containing intentionally changed content-hash IDs. The corrected assertion
compares the explicit world/character propositions and logical actor-name
knowledge sets, while still requiring distinct origin/seed hashes and exactly
retained ordered provenance. That failed attempt remains preserved; no
production validation is changed to accommodate it.

The exporter captures the exact schema from a production author request and
emits3 cases/162 samples:132 positives and30 negatives. The full-schema case
uses original Ashglass/Copper proposals. Separate grammar-only cases exercise
all64/65 permutations; they grant no cross-field engine eligibility. Rust
tests independently retain actual-actor/self-knowledge/native-origin guards.

The actual native compiler and byte-mask oracle passes all162 samples and five
controls in598ms, return0, known cleanup and0 stderr. The original exported
corpus is28588 bytes, SHA256
`93dc10649de09ec828f425696f65d24d248bb2f5321aed60d4c573b71e516682`.
Exact production schema SHA256:
`b47513d1be6fb9ef77561325530193c3c329f7c06ae657ea87e1b3c24ede2914`.
The byte tokenizer loads no model or tokenizer file. Mask acceptance checks
include EOS/sticky native error state, rather than only wrapping schema text.

Both evidence selections are privately preserved and independently replayed
with0 missing/mismatched files. The original RED recovery has10 originals plus
one helper control,11 copies and12 ZIP members; ZIP SHA256 is
`033d6719a0ea52acb85fbb8c91d20022e7a77d53d8ce9c1df6609f7269f3c454`.
The successful proof selection has59 new GREEN/native originals plus two small
RED references,62 indexed copies including its helper and63 ZIP members. It
retains the actual failed attempt-v1 and successful attempt-v2 separately, and
checks the old RED archive without duplicating the wheel/runtime. Proof index
SHA256 is
`50572eaf9bdf8f275e29d07ed0d3840355d569222d6401965ed0265387495f06`;
ZIP SHA256 is
`d58c21f893cb2d88d0f977a847b847664ad34e2f01340c5b75737e128b5fad6a`.
Independent verification result SHA256 is
`ef462a39313deccb5a51c42347b7f00502c6ba54258d47ce6d272221d6d6c127`.
Preservation flags remain false for product qualification: byte retention is
separate from the test results above and the pending Android/model gates.

## Corrected-source host and Android qualification

The follow-up runs commit `4068e5a6` (production code `aa535d94`) against a
fresh 879-input compiled-source map, SHA256
`14d9465a689a071cd5b718bc27aacb060e91378ebc47c30d5992209a5c4472bc`.
All 2,001 tracked inputs remain unchanged during each host/SDK build owner;
the separate host checkout matches all 879 compiled inputs in the Android
checkout. These results belong to the corrected source, rather than the older
877-input results.

| Executed check | Result |
| --- | --- |
| Rust core, storage, workspace, Android, exporter and standalone linker tests | 985 passed, 0 failed, 11 ignored |
| Python scripts and five benchmark suites | 1,716 passed, no failures/errors/skips |
| Both Clippy configurations, Rust/linker formatting, frontend verification/formatting, Android fixture compatibility | Passed |
| Ordinary input-process APK build and JVM tests | 308 passed in 36 XML suites; 11 APK audits passed |
| LiteRT candidate build, JVM tests, lint, dependency/analyzer and APK audits | 572 passed in 56 XML suites; all audits passed |
| Fresh API35/x86_64 native component guest | All 10 methods passed; owned verification 249,577 ms |
| Separate fresh API35/x86_64 original-story guest | All 8 methods passed; owned verification 303,888 ms |

The JVM counts overlap between profiles; they are not 880 distinct tests.
Current lint analyses and reports actually execute in both builds. Lint records
zero errors, three ordinary app/controller warnings and ten candidate warnings;
the candidate analyzer audit records `analysis_did_work:true`. Ordinary Gradle
executes 124 of 126 tasks; the candidate executes 84 of 87. All 19 host owners
(18 planned plus the separately recorded fixture gate) and both SDK build
owners close with return0, known cleanup/capture and zero owner stderr.

The ordinary product APK is 27,548,472 bytes, SHA256
`1342c3fcac846e13eccb0c9da3624bced8a1314829346832b25c09ac2eeb863d`;
its test APK is 2,188,299 bytes, SHA256
`b9159113342a9783748637eacad1680f17857c39571c399696ad3ffc48febeab`.
The controller APK is 55,073 bytes, SHA256
`6ea09f4c5105d62e61498d2bebc05de52ce597e30b9681e4975a323b36ef7693`.
The candidate product APK is 78,241,840 bytes, SHA256
`e9f7e4c2d8ffe0ea978e2ea8fa75f62520218bc9b5cb2358994dc49e7eaa2c87`.
Actual ZIP-library inspection finds the exact 8,117-byte bundled schema,
SHA256 `024e505ed1e34dfe89d828574e59ae5da8e0f84ae892b1a0eeb2c5c0d35d73df`,
in both x86_64 and arm64-v8a Rust libraries of both audited product APKs.
Packaged ARM64 bytes do not establish ARM64 execution.

The native gate and authoring journey use the same three ordinary audited APKs
on two separately prepared, owned guests. The journey exercises strict author
input/proposal bounds, reads/cancel without creation, lost-ACK creation recovery
after reopen without generation, visible scripted-provider labeling, edits
invalidating consent, edited-world creation/reopen, preserving the current
player draft on cancel, and a generated turn with scoped receipts. This is real
Compose/JNI/Rust execution with scripted inference, not an SDK/model turn.

Independent file-only reviews verify all 18 exact method start/pass pairs and
174 complete SDK2 metadata/raw pairs (81 native, 93 authoring). Every SDK
command has adjacent server observations, and every observer's actual PID and
listener frame matches the admitted existing server. Before/after source maps
remain identical. Both guest owners then close after their exact bound STOP
requests, with verified cleanup/capture and no guest-flush claim. Seven bounded
metadata files per guest are copied to C: with no mismatches. One final
listener-only observation confirms the existing server is unchanged and left
running; it makes no device call or server lifecycle operation. No unrelated
emulator is stopped.

Initial directory/source-map setup refusals and an isolated-Python launcher
import refusal are retained separately; they are not executed product tests.
Two existing Rust files had line-ending-only differences between checkouts.
Their original bytes were preserved before normalization to the exact tracked
LF bytes and before the current source maps/owners were established. Relative
to the previous 877-input map, 876 inputs are byte-identical, the schema changes,
and two Rust test/export sources are added.

A separate [native build-input correction](https://github.com/OptimumAF/LocalLore/blob/02860fb7835b53fbfd0b75b6bb111df2091916a7/docs/android/NATIVE_PROMPT_INPUTS_2026-10-27.md)
is proposed in PR #234. Its configured-task RED/GREEN proof finds the missing
prompt inputs and verifies their registration. It is not integrated into these
879-input APKs and does not imply that a stale APK caused an earlier result.
The cold-built APKs above already contain the correct schema. Current private
records and audited APKs remain outside public Git; final byte-retention
receipts and the source-bundle hash belong on tickets #13/#14, separately from
feature acceptance.

## Reproduction and remaining gates

With Rust1.93.1 and cached dependencies:

```text
cargo test --locked --offline -p locallore --all-features --test author_schema_portability
cargo test --locked --offline -p locallore --all-features --example initial_world_schema_cases
cargo test --locked --offline -p locallore --all-features --test m09_initial_world_adversaries
cargo run --locked --offline -p locallore --all-features --example initial_world_schema_cases
cargo clippy --locked --offline -p locallore --all-features --test author_schema_portability --example initial_world_schema_cases -- -D warnings
```

The exporter writes only bounded synthetic corpus JSON to stdout. Feed its
exact bytes to the existing `benchmarks/llguidance_oracle.py --corpus <file>
--module-root <verified-runtime-lib>` under an owned worker after
`scripts.llguidance_oracle.verify_runtime` checks the isolated runtime. Keep
the corpus/schema strings unchanged. The production Cargo graph does not link
LLGuidance or gain `serde_json/preserve_order` from this development oracle.

The full host matrix uses `cargo test --locked --offline` for `locallore`,
`locallore-storage`, `locallore-workspace` and `locallore-android`, all with
`--all-features`; the workspace check also enables
`locallore-storage/development-fixtures`. The exporter example and standalone
linker are checked separately. Existing frontend/Python suites and
`cargo run --locked --offline -p locallore --example android_fixtures -- --check`
also run. Each command and its original output are retained under an owned
worker, including actual failures. The existing
`benchmarks/android_process_verification.py` fixed `build`, `components` and
`original-story` phases produce the current APK/method evidence. They retain
their original command, owner, client and generation budgets.

The older 877-input creation19/broad89 results keep their earlier source/APK
attribution; those larger emulator phases are not rerun for this schema-only
change. Next runnable work is actual SDK/model author generation under fresh
device/resource admission, including a fresh check of the authorized phone's
availability. No current phone-absence claim is made. Neither the native byte
oracle nor scripted Android checks establish the model's tokenizer, inference
completion, creative quality, physical/ARM64 performance, cancellation latency
or native drain. Full task checklists remain pending owner acceptance.
No other emulator stop, system setting, server lifecycle, release or merge is
performed. Private evidence and the wheel stay outside public Git.
