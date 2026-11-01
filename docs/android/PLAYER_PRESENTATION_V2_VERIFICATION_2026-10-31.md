# Coherent Android player presentation V2

B41. Refs #307; #13 (M09.04/M09.06); #14 (M10.02).
Supporting implementation is verified on the host and packaged for Android.
Current-source emulator verification and owner acceptance remain pending; all
full milestone checkboxes stay unchanged.

## Result and contract

Android now reads `play_presentation_v2` through the existing narrow Host/FFI
boundary. It can represent both actual Domain1 and corrected Domain2 histories,
including opaque native player identities. The native engine supplies current
player state, owned inventory, and the latest twenty whole eligible accepted
turns with explicit window bounds. Each turn preserves original ancestor scope,
turn identity, ordered event IDs, original accepted intent and recorded narration.
Rust applies lineage/head/player eligibility before selecting whole receipts.
Author payloads, unobserved NPC/private state and generation internals stay out.

The strict Kotlin decoder renders this native projection. The gateway retains
attachment identity, head, player-binding and catalog checks across suspensions;
the view model retains exact current-timeline object identity and late-result,
cancellation and disposal fences. There is no legacy-operation fallback or
empty-history substitution. Reads do not run inference or commit events.

Two representation refinements are part of the
[frozen contract](../native/PLAYER_PRESENTATION_V2.md):

- A valid native reply can grow when Android re-encodes slash characters. The
  actual fixture is 41,514 raw envelope bytes and 77,479 slash-escaped data bytes.
  The object allocation bound is 262,144 bytes; the original JNI raw limit
  remains 65,536 bytes and the Host limit remains 262,144 bytes. Strings and whole
  turns are preserved without clipping or adaptive omission.
- A public Engine accepts `Promise.deadline=u64::MAX`. Only the new presentation
  DTO's `promise.deadline` and `believe.claim_event` use canonical unsigned decimal
  strings. Kotlin validates the exact range and renders numeric JSON using
  `BigInteger` in a deep copy. Accepted requests/receipts remain numeric, and the
  native DTO stays unchanged. No Double/Long rounding or gameplay rules are added.

Legacy Domain1 `play_snapshot`, its intentional Domain2 `Version` refusal and
thin `play_snapshot_v2` remain unchanged. The refreshing new operation stays
blocked while local inference owns resources, as `open` does; cancellation must
drain first. Only the new Domain2 UI fixture's observation helpers move to the
new endpoint. Direct legacy controls and shared Domain1 conservation helpers
remain. Existing synthetic transport fixtures gain the exact new display shape
while preserving their negative/cancellation assertions and captured requests.

No dependency, model, SDK, database schema, native raw limit, app permission or
inference-policy change is introduced. Gameplay remains local, and Kotlin gains
no gameplay authority. The shared Host request schema adds one operation; all
previous schema bytes are retained, with six generated TypeScript lines added.

## Exact execution source and artifacts

Executed source is **`42ae8f6b7df7373696d35c9a294b6d0517c8886c`**, all **2,369 raw
tracked inputs**, frozen at `D:/Worktrees/LocalLore-record-ui-host-v1` on
`impl/m09-player-presentation-v2`. The later reporting checkout is
`D:/Worktrees/LocalLore-record-ui-archive-v1`, branch
`impl/m09-player-presentation-packet-v2`; reporting must not replace the frozen
source in the build proof. The implementation stacks on open/unmerged PR305
`c6dfd53e0993aa98c42cf268c10a36c43f3522b1`, which depends on open/unmerged PR304.

Private controls/captures are under
`D:/Dev/Experiments/LocalLore/2026-10-31-player-presentation-v2`.
Every project command uses a physical D: working directory and process-local D:
temporary/cache outputs. Installed Java21/SDK and Rust1.93.1 remain in place.
Source/tool pins, actual worker identity, finite Windows Job ownership, output
capture and cleanup accompany the qualified cohorts.

The actual offline public pipeline compiles Rust release JNI for **x86_64**
(1m31s) and **arm64-v8a** (1m34s), builds both APKs, runs all **408 JVM tests / 46
XML reports** with zero failures/errors/skips, and passes lint with zero errors
(one existing `GradleDependency` Warning and `AutoboxingStateCreation` Hint).
Product and instrumentation-pair audits pass. Packaged ELF LOAD alignment is
16,384 bytes; the test-only permission remains `REORDER_TASKS`.

| Artifact | Bytes | SHA256 |
| --- | ---: | --- |
| `org.locallore.app.archiveverify` product APK | 27,838,412 | `ffa33dca97ec97d1e3f09df96f0a79ff057c2c583c4276add4358c122c8eb92e` |
| `org.locallore.app.archiveverify.test` test APK | 2,263,192 | `bf7c7b9e50a773dea68a8de3807b176e3b239192a70bbda10fbed77e0464dc53` |
| Current-source build manifest | 16,946 | `a8543cd5c421e69d386f0e4b36f9280e771ae1813e09011eae91e562e5135c60` |

Certificate SHA256 is
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
The manifest is `record-ui-build-v2.json` in the private root; its existing
serialized contract remains `record-ui-build-v1`. Current-source verification
passes all ten real annotated test selectors, exact APK roles, 408/46, the new
28-method presentation policy plus existing Query2 fifteen/Transcript eight,
source/head/tool/raw/task joins and lint. It invokes no target admission or device.

## Executed checks

```text
cargo +1.93.1 test --workspace --exclude locallore-desktop-spike --locked --offline -- --quiet
cargo +1.93.1 clippy --workspace --exclude locallore-desktop-spike --all-targets --locked --offline -- -D warnings
cargo +1.93.1 fmt --all -- --check
cargo +1.93.1 build --locked --offline -p locallore-workspace --example android_player_presentation_fixture
<built android_player_presentation_fixture.exe> <fresh D: scratch directory>
<fixed isolated Python driver loading the four record-UI proof test modules>
<verified Gradle wrapper> :app:testDebugUnitTest --tests <presentation classes> -x :app:buildRustAndroid --offline ...
python -I -S -B scripts/check.py android --archive-verification --offline
python -I -S -B <fixed build-manifest writer and verify_current reader>
```

The focused JVM cohort excludes native compilation only for that isolated
transport/decoder test stage. The final public three-command pipeline above is
unchanged and executes native compilation, all JVM tests, lint and both audits.
Its ten-method SDK7 runtime roster is unchanged.

| Qualified cohort | Actual result | Owner elapsed ms |
| --- | --- | ---: |
| Native missing-endpoint FIRST | Six behavioral RED; one separately diagnosed oversized-fixture setup failure | 18,107 |
| Valid native overflow FIRST | Twenty committed turns, largest receipt 40,980 B, state 259,891 B, presentation turns 265,462 B; missing endpoint RED | 1,634 |
| Initial new native / old thin compatibility | 14 pass | 10,784 |
| Native unsigned-value FIRST | Real accepted max deadline and claim; old numeric DTO fails string contract | 10,685 |
| Full Rust final | **1,070 pass / 11 ignored / 0 fail**, 147 targets | 253,405 |
| Final seven-case native capture | Fresh SQLite/ordinary Host, exact conservation assertions pass | 3,098 |
| Targeted JVM routing/slash FIRST | Two behavioral RED with explicit routing oracle | 25,084 |
| JVM unsigned-value FIRST after setup correction | Real captured value refuses in old decoder | 28,309 |
| Final focused JVM | **28 pass**, includes 18 independent Gateway/VM cases and ten wire cases | 29,370 |
| Clippy all targets | Warnings denied, exit0 | 19,323 |
| Build-proof FIRST | Nine rebound method/source subcases incorrectly accepted before enforcement | 6,229 |
| Build/controller/contract/client proof tests | **23 pass**, including exact new presentation policy adversaries | 86,793 |
| Final format check | Exit0 | 3,406 |
| Public offline Android pipeline | **408/46 pass**, JNI/build/lint/two audits pass | 300,457 |
| Outer public supervision | Exact child, source/control and known capture/cleanup pass | 306,969 |
| Build manifest + real current-source replay | Exit0, exact ten-selector/408/46/source/APK proof | 10,170 |

The full Rust input profile pins the native implementation, Cargo/schema,
fixtures, assets and other repository inputs while excluding the independent
Android Kotlin/JVM-corpus consumer files. Native inputs stayed unchanged during
consumer integration. The 28 focused JVM cases are included in the final 408;
they are not added to that total. Neither test counts nor cross-compilation
establish Android execution, model quality or physical-device performance.

## Genuine corpus and conservation

The committed JVM corpus is byte-identical to the actual seven-case native
capture: **163,309B**, SHA256
`92b09a37e1340508afabecac964ba6c89724fb236cc246f585e6d569278e2034`.
The original six-case raw capture remains private; its committed corpus and
source versions remain in Git history. Failed raw captures remain private. The production Store imports the genuine opaque-player Archive3 from
PR305; ordinary Host reads main/head4, corrected/head5 and rediscovered/head6. Additional
original empty, mixed24-turn, slash20-turn and unsigned-value stories exercise
zero history, absolute window IDs9..48, representation size and full u64 range.

Expected intent/narration messages come independently from accepted originals.
Presentation-only decimal fields are checked against original numeric values.
Exact archive bytes, canonical bytes and every accepted-history basis are
conserved around reads. No model/provider is loaded by that ordinary reader.
The mixed FreeText history is genuinely accepted through the scripted provider;
it is not a retagged Actions request. No real-model claim follows.

Native whole-turn eligibility predicate units cover hidden/partial/foreign/empty
identity sets. Current public commands always include the player as a witness,
so these unit tuples are not presented as forged accepted receipts or proof of
an independently generated NPC-only history.

## Failure preservation and bounded storage

Original compile/setup failures, behavioral RED captures and raw outcomes remain.
The test-only `JSONObject.similar` call was replaced by exact recursive checks
compatible with Android's API. The unsigned fixture's genuine Dialogue turn is
retained after correcting an Actions-only setup assumption. The initial
catalog adversary combined an advanced branch row with an old root catalog;
the decoder correctly returned `Malformed`. Its corrected test retains that
negative, then checks coherent catalog advance → `Stale` and valid recovery.
No timeout, identity fence, native refusal or cancellation assertion is weakened.

The first JVM transport synthesized `Version` even for Domain1; it was replaced
with an explicit missing-route assertion. Its failures are not attributed to a
native Domain1 refusal or Android raw execution. Actual native legacy refusal
remains separately exercised. The original B40 emulator result stays
8 pass / 1 fail / 1 unrun; this packet does not relabel it as fixed runtime evidence.

Broad Rust attempts preserve a stale-schema failure, a budget monitor stop on
an intentional temporary junction, and a preserved-directory/PID collision.
The final runner uses create-only per-cohort temporary directories. Budget-only
link metadata can name only targets inside the same already charged temporary
tree, with no alias traversal; source/control pins remain strict. Unexpected
directory-enumeration errors fail closed. One early stopped run lost its final
ownership receipt during post-meter failure; its cleanup is not retroactively
qualified. Later runners save the returned owner result before postflight.

Unrun inherited-output/meter drafts and a pre-worker path-spelling refusal stay
retained. Both public wrappers were independently reviewed before activation.
The public inner 900-second acceptance bound remains unchanged; the exact outer
1200-second wrapper includes source/tool hashing and cleanup. Ordinary checks
remain bounded 900 seconds. All old controls remain intact.

The initial owned closed JVM build was retained with all 1,682 files / 18,570,345 B
rehashed before a fresh build namespace was used. Named source/output/temp roots
measured 3,574,529,667 B after admission, below 8 GiB stop / 10 GiB cap. This is a
sampled point observation, not an operating-system quota or peak claim. Prior
packets, caches and retained guest state remain separately preserved. Selected
source/APK/control recovery and publication receipts are recorded in ticket
handoff; model weights, signing keys and guest images are excluded.

## Remaining acceptance

M09.04 supporting code and M09.06/M10.02 supporting host evidence are ready for
review. #307 still requires a fresh applicable emulator grant and actual rerun
of both genuine corrected-history Compose cases plus controls from these exact
APKs. The B40 one-run grant is spent; no new boot, guest reuse, retirement, ADB,
phone discovery or model operation occurred here. The other emulator, shared
ADB service, system settings, existing saves and old captured state remain.

The older process-proof protocol correctly counts the new operation as `other`;
a distinct version is required before new-source process-profile qualification.
M01.01/M01.02/M10.05 physical-phone/model gates remain blocked or unverified.
Physical phone/ARM64 execution, real inference and story quality, accessibility,
causal OS-death, runtime privacy observations and release acceptance remain open.
No merge or release is authorized or performed.
