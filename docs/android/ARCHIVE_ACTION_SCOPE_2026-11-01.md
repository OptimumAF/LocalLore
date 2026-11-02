# Archive controls belong to the displayed view

B71, 2026-11-01. Refs #13 (M09.06; supporting M09.03/M09.05), #14 (M10.02).
Supporting implementation is in review; full task criteria remain unchecked
pending owner acceptance and broader qualification. Based on open, unmerged
PR #340 at `28238b73b542e71eb0b8a328d49f83f58362c5d4`.

## Reproduced failures and fix

Retained archive toolbar callbacks could capture a preview, open a picker,
cancel or close a newer presentation, including another story. Existing exact
preview/import DTO checks were necessary but did not bind actions to the actual
rendered view. Separately, slow collectors of the value-equal ArchiveUiState
stream could miss a genuine same-story close/reopen and keep the previous
object. Adding an exact-state guard alone would leave that UI unable to act.

Seven controller action overloads now require the exact current visible
ArchiveUiState and a live owner before running their existing logic. They cover
Dismiss, Cancel, Capture, import/export picker start, import confirmation and
Open imported. Two ViewModel picker wrappers preserve that scope while retaining
the original one-outstanding-ticket behavior. MainActivity collects a transient
identity ArchiveFrame, captures one plain rendered state and passes it through
every archive callback. All 23 controller publications wrap the actual current
state in a new frame, preserving delivery across equal-valued replacements.
Existing DTO equality and state API remain unchanged.

Seven narrow referential button keys retire old clickable nodes when their
displayed authority changes. The dialog and scroll container stay stable.
Existing token/reference/one-shot, busy/picker/drain, cancellation and disposal
checks remain. A stale action causes no work; a fresh action keeps explicit
consent and joined closing. The B70 root-first/corrected-library wording stays.
No Rust/JNI/native protocol, canonical event, storage schema, observer grant,
gameplay, dependency, SDK, runtime or model change is introduced.

## Ownership and source

Root reuses `D:/Worktrees/locallore-record-actions-ui-v1` on
`fix/m09-archive-action-scope-v1`; owns controller/ViewModel/Main/Dialog, new UI
journeys, integration, execution and docs. Agent S uses separate
`locallore-record-actions-flow-v1` / `test/m09-archive-action-scope-v1`, owning
only ArchiveActionScopeTest.kt, original commit `a6f64417`. Agent F uses separate
`locallore-player-profile-ui-v1` / `test/m09-archive-frame-delivery-v1`, owning
only ArchiveFrameDeliveryTest.kt, original commit `277996f5`. An independent
reviewer authors no product/test code. No authorship overlap or owner acceptance
is inferred from review. Writer/reviewer claims are released at handoff.

The two independent JVM files are byte-identical throughout FIRST, GREEN and
both full builds. Their SHA256 values are
`98d3eab724cab40ca1df5c12594f6f6aca0a240d0b354180a0808a9fecbc37a4`
and `006777c1ece69565b3b2acc1065413adb31349a9684e0053c5b8e166022d710a`.
Reflective scoped-overload/flow discovery falls back to the existing paths on
unchanged production, permitting behavioral FIRST rather than compile failure.
Genuine close/reopen flow cases require no repeated native token. Some callback
DTO-copy edge cases use synthetic transport and do not prove token recurrence.

## Verification actually executed

Each phase uses a 900-second Windows Job owner, actual child identity/start
barrier, complete raw capture, verified cleanup and unchanged before/after source
maps. Existing Rust1.93.1/JDK21/Android tools and locked dependencies are reused
offline, with D: TEMP/TMP/TMPDIR and Cargo/Gradle caches. No new dependency choice.

Targeted command from the repository root:

```text
apps/android/gradlew.bat -p apps/android --offline --no-daemon --max-workers=2 :app:testDebugUnitTest --tests org.locallore.app.ArchiveActionScopeTest --tests org.locallore.app.ArchiveFrameDeliveryTest
```

| Phase / source | Actual result |
| --- | --- |
| FIRST `0eba4815ae2ea48de8aa224cbf0ce0038b82e6ff`, production identical to #340 | **11 executed: nine assertion failures, two positive controls pass**, zero errors/skips. Callback 8 has 7 failures/1 pass; real-flow 3 has 2 failures/1 pass. Owner14,089ms. |
| Same targeted command, `7d6e560525da2142a67f0554c96c78c9836e905b` | **Same 11 GREEN**, zero failures/errors/skips; owner19,452ms. |
| `python -I -S -B scripts/check.py android --offline`, `7d6e5605` | **505 JVM/62 XML pass**, lint/APK audits pass, owner45,311ms. Superseded for the encoding finding below; all outputs preserved before correction. |
| Same full command, final code `632677d1791b53413ed7fe60446b5e9bba8b2882` | **505 unique JVM/62 XML**, including all 11 unchanged new cases, zero failures/errors/skips. Lint zero errors/one existing warning/one hint; both public APK audits pass. Owner42,837ms. |
| `git diff --check` | Pass before publication. |

The first full build executes 15 of 81 tasks; the corrected build executes 14,
67 up-to-date. JVM runs again. Rust build task is **UP-TO-DATE**, using unchanged
B70 native outputs; original release/alias/generated/merged/stripped/APK chains
are revalidated. No fresh native compilation or native/ARM64 execution is claimed.
No exclusions, clean, install, emulator or device task is used. Three source ZIPs
retain FIRST 2,582, GREEN 2,583 and final 2,583 inputs; GREEN and the superseded full
build share one ZIP. Final documentation changes only README and this report.

The callback cases cover copied/equal-reopened/cross-story states, current DTO
grants with stale pages, noncooperative busy work and outstanding pickers, scoped
VM entry points, disposal, one-shot writer and joined closing. Real production
controller/VM flows exercise slow same-story reopen and sequential lifecycle
delivery. Three Compose journeys use actual controller/frame collection and
retained clickable semantics with monotonic synthetic tokens: export replacement,
other-story import/Open and equal reopen/Close. Concrete runtime-JUnit bodies
77/85/130 code units are present only in the test APK. **UNRUN on Android**;
compilation/DEX is not touch, geometry, accessibility or real native I/O evidence.

## Review finding and retained evidence

Independent review catches an unintended encoding change in Root's file rewrite:
two existing ellipses became mojibake because text was read without explicit
UTF-8. The running build finishes and its complete raw/XML/APK/native output is
preserved. A separate commit restores exactly U+2026 at those two sites using
explicit UTF-8. All non-ASCII lines in both files then match the base exactly;
all other reviewed source and the eleven oracles remain unchanged. The corrected
full gate above is the final qualified result. The original source review retains
the finding; addendum 2,031B SHA256
`bc30adedc30d43e4f5050e430ea14c74fdfe7b0a81759abde7ade93a04729346`
records its resolution. No assertion or timeout is weakened, and the original
nine failures remain failures in their historical phase.

| Final APK | Bytes | SHA256 |
| --- | ---: | --- |
| org.locallore.app | 28,359,726 | `5571e2477bc1dc19bffa3950b9e2a0c59758446ecb9510a6b838b4a5f66f6c64` |
| org.locallore.app.test | 2,522,863 | `cc0fc317420189208f267b27ff1a95ef139fea96454319f97564dd91b476e036` |

Recorded common signer:
`17ed497138b20dc1657d54039802305cfe0e3b782c73feaad20359c954707564`.
Four packaged native libraries pass16KiB ELF/ZIP checks; test permission is only
REORDER_TASKS. The test APK is byte-identical across both full builds; the product
APK changes with the two restored notices. The superseded product hash is
`9c6b148744b945ef9ccbfee7d0a7fb5eeab716f37028ff2bf729638dc0febd17`.

Captures: `D:/Dev/Experiments/LocalLore/2026-11-01-archive-action-scope-v1`;
selected recovery uses the matching `D:/Dev/Recovery/LocalLore` path.
Closed evidence 45,566B SHA256
`1ff20af56bc011b3b704da1dfff0c45b39c284bdb87409bc7fe98ee8b4fed547`.
FIRST/GREEN each preserve their two new JUnit reports. Their copied old lint and
reused immutable APK/native files retain B70 attribution, not current targeted
qualification. Each full build preserves all 63 reports (62 JUnit+lint) and four
APK/native copies 53,701,485B before any regeneration. B70's 65 original/copy pairs
were verified before build reuse; its selected historical copies remain intact.
Earlier working generated paths now regenerate, so those historical copies,
source ZIPs/maps and dated receipts own the old evidence. No old generated path
is claimed byte-identical to the newest build.

Independent closed readback takes3.136s with no findings or authorship overlap:
`closed-reader-v2.json`, 20,730B SHA256
`7a348735dae74c39259e13d833a0b0072230dd15ba74d72e1965258ae72aaa78`.
It joins all four commands/owners/raw streams/source maps, three ZIPs, unchanged
oracles, copied reports/historical artifacts/current originals, native chains,
recorded audits, compiled UI definitions and the Unicode resolution. Its first
reader incorrectly demanded a successful task line in FIRST; that false823B
receipt and script remain frozen. V2 accepts exactly the expected FAILED suffix
only for FIRST with worker1/nine AssertionErrors/two controls/zero errors/skips;
all other phases still require success. No source/test change or rerun is used
to correct that reader setup error.

Final reconstruction uses the tested ZIP plus exactly two documentation overlays,
without another full ZIP. Controls remain below 64MiB, selected recovery below
256MiB; generated outputs are sampled every two seconds and at terminal below
3GiB (final 659,393,245B). This is not a filesystem quota, global cache/TEMP peak
bound or full build-tree backup. All failed/frozen/versioned evidence is retained;
ordinary scratch is not silently promoted to selected recovery.

## Open gates and next task

M09.06 supporting fix and M10.02 host evidence are in review; full criteria remain
unchecked. Current Android UI qualification needs matching authority and fresh
guarded admission. Pending SDK14 #338/#337 inputs, SDK13 and other guests remain
untouched. No prior approval grants this new APK/UI cohort. No emulator, ADB,
phone discovery, ledger/settings/model operation, unrelated stop, private upload,
merge or release occurs. Physical/model/ARM64/accessibility/causal OS-death and
full milestone acceptance remain separate.

Next host-runnable task: test deletion-dialog consent and cancellation controls
across replacement presentations, using synthetic data and proving any retained-
action failure before changing its fences. No live player story deletion is needed.
