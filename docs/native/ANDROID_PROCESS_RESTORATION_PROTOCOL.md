# Process-restoration verification contract v1

M05.05/M10.02 supporting work and M09.03 preparation. Implementation and actual
execution are separate gates. This protocol grants no gameplay/model authority.

## Product and controller

The debug-only product is `org.locallore.app.draftprocessverify`, using the real
`org.locallore.app.MainActivity`, Rust workspace and scripted inference. A new
`localLoreInputProcessVerification=true` leaf requires input-draft verification,
its exclusive `.gradle-input-process` cache, and debug-only outputs. Ordinary
builds do not enable the verification observers or resource-ID export.

The separate controller is `org.locallore.app.draftprocesscontroller`, with its
own self-targeted `org.locallore.processverify.ProcessRestoreInstrumentation`.
It has no activity, service, receiver, provider, shared UID, network permission,
model, native library or external runtime dependency. It uses framework
Instrumentation/UiAutomation APIs available at minSdk26. It never instruments
the product process or substitutes a ViewModel/transport/provider.

The controller accepts only `case=restore_non_default`, a 16-lowercase-hex
`run_id`, a 64-lowercase-hex `product_sha256`, and `cohort=create|reuse`.
Product/controller UIDs must differ and debug signing must match. The fixed
product APK must match the supplied hash; arguments cannot select a package,
component, path or shell program. Its application ID and instrumentation target
are always the controller's own identity.

## Saved navigation

The UI hint is exactly `[Int(1), story, branch]`, with native ASCII IDs of
1–64 characters (`[A-Za-z0-9_-]`). The Activity stores it in the nested
`locallore.navigation.v1` Bundle using exact `version`, `story`, `branch` keys.
It never carries revision, title, session, request/turn key, canonical state or
provider work. An unresolved initial snapshot/recovery preserves the previous
pending hint; a coherent selected snapshot replaces it; a settled empty library
clears it. A retained ViewModel ignores a newly constructed factory hint.

`DurableGateway(initialScopeHint=...)` must resolve the hint against the fresh
native story catalog and existing strict active-branch decoder before native
resume and publication. Missing/retired targets may fall back to the normal
available selection/empty library with `selectionRestoreUnavailable=true`.
Malformed catalogs, transport/storage errors and resume races remain recovery
errors. Consume the hint only after a coherent snapshot/empty resolution; never
reapply it after subsequent user navigation. No auto-create, generation, prepare
or commit is authorized by a hint.

## Verification-only observations

MainActivity accepts intent extra `locallore.process.run_id` only when this debug
verification profile is enabled. The run ID is also saved as
`locallore.process.run_id.v1`. Missing/invalid IDs disable observation; the
controller then refuses missing proof. No ordinary application log is added.

The product emits atomic bounded JSON at fixed app-private leaves:
`no_backup/process-verify-v1/RUN_ID/created.json`, `saved.json`, `commands.json`.
Each is at most4096 UTF-8 bytes, with these exact fields:

```text
version: Int1
scope: "locallore_process_verify_v1"
run_id: hex16
pid, uid, task_id, sequence: nonnegative integers (pid positive)
process_start_uptime_ms: nonnegative integer
event: "created" | "saved_after_super" | "command"
restored_state: boolean
factory_creations: nonnegative integer
hint_present: boolean
hint_sha256: hex64 | null
operations: exact keys below, each a bounded nonnegative integer
```

Operation keys are `workspace`, `branches`, `resume`, `create`, `open`,
`play_snapshot`, `free_text`, `submit`, `prepare`, `commit`, `cancel`, `other`.
Unknown operation names increment only `other`; no raw operation/payload is
stored. Exactly `close`, `capabilities`, and `model_status` are known resource /
metadata operations omitted from these gameplay/read counters; arbitrary names
are never ignored. Counters describe attempted calls at the actual transport boundary, not
canonical success. The factory count describes real transport construction.
No text, Bundle dump, request key, path, NPC knowledge or narration is recorded.

Hint digest is SHA256 of UTF-8 `1\nSTORY\nBRANCH\n`, or null for no valid hint.
`saved.json` is written only AFTER `super.onSaveInstanceState` and the navigation
Bundle write. STOPPED alone does not prove state was saved. The observer must
not retain an Activity, change canonical behavior, or be enabled by story text.

Verification exports existing test tags as raw accessibility resource IDs:
`story-list`, `workspace-detail`, `inference-provider`, `reset-demo`,
`saved-library`, `saved-story-ID` menu items, `play-input`,
`play-kind-dialogue`, `play-kind-action`, `play-send`, `recover-save`.
Traverse bounded fresh nodes under the exact product package; tags are not
`package:id/tag` names. Do not reuse nodes across transitions or process death.
On API34+, clear only this UiAutomation connection's accessibility cache before
reacquiring nodes; the guarded call is unavailable on older versions. This does
not clear app data or change settings. Header observations expose only
MISSING/EMPTY/VALID/MALFORMED and length, never the observed text. Readiness is
bounded at15s within the unchanged120s case deadline. A missing header permits
one bounded backward reveal per polling attempt; empty text waits and nonempty
malformed text refuses.

Saved-story head reads traverse only the exact tagged menu item's visible,
product-owned subtree (at most32 nodes, depth8). Require one unique nonempty
label with the exact story/revision suffix; identical merged copies are allowed,
conflicting labels refuse. This accommodates the separate popup's nested label
without searching unrelated nodes or navigating away from the retained draft.

## Actual process oracle

Create exactly two genuine native stories in the fresh product, freeze their
ordered IDs/root branches/zero heads in a bounded private controller fixture,
and deliberately select lexical non-first B. In reuse mode, require the same
owned fixture/catalog and zero heads before a new uncommitted attempt; do not
regenerate, clear, silently adopt or skip a failed cohort.
Create counters are cumulative within each process. Initial admission permits0,
or exactly2 only with an explicitly validated reusable fixture. New creation
adds2; reuse adds0. Restored processes requirecreate0. A committed B1 fixture is
never admitted as an uncommitted retry.

Type the predefined original Unicode/newline dialogue (under2048 bytes) and
prove B0 and no gameplay-operation calls. HOME must be followed by the exact
task's STOPPED state AND a newer after-super save acknowledgement for the same
PID/start/task and B hint digest. Then `am kill --user0 PRODUCT` may run. Require
the old process to disappear; command exit zero alone is insufficient.
After disappearance and before relaunch, independently read the old saved and
commands records. Require matching old identity, distinct bounded producer
sequences and exact
terminal gameplay vectors, so a new process's zeroed counters cannot hide work
in the dying process. The first terminal vector is entirely zero; the second
has exactly free_text1/prepare1/commit1 and submit0/cancel0/other0.
The synchronized producer uses one counter across its files; a read-only
command may write after the after-super save. Either relative order is valid,
but equal sequences are impossible. The saved acknowledgement must still be
newer than the pre-HOME observation, and both terminal gameplay vectors must
still match the acknowledged producer exactly.

Relaunch only the fixed ACTION_MAIN/CATEGORY_LAUNCHER component with NEW_TASK,
no force-stop, task clear, reset or multiple-task fallback. Require SAME task,
new PID/start identity, restored-state/factory acknowledgement, B0 and exact
draft/kind. Check attempted gameplay calls remain zero before explicit Send.
Reselect B through the actual library for a native reread without submitting.
One explicit Send must produce B1; another saved-task death/relaunch must retain
B1/draft with zero automatic gameplay calls and A0. Count no partial cycle as
success. Native branch/failure/retry behavior has independent unit coverage;
branch-specific actual process death is not implied by this root-branch case.

Controller results use one bounded JSON `proof` instrumentation result with
version1, fixed scope `locallore_process_controller_v1`, case/run ID,
`status=passed|failed`, fixed stage/reason, check count, process-death count and
private identity/fixture observations. Success requires Activity.RESULT_OK and
the complete two-death oracle; no return-code-only or mock result is a pass.
Private observations/fixture files stay outside public reports.

The shell transport first checks an original Unicode/quotes/newline/backslash
control. Framework `executeShellCommand(String)` reaches `Runtime.exec(String)`;
the fixed three-token wrapper carries a bounded octal-encoded script without
whitespace inside its third token. Script/token bounds and NUL refusal are
explicit. Closing a timed-out output descriptor does not prove remote child
termination; uncertain attempts cannot be blindly retried. Task parsing accepts
the observed one- or two-space Hist delimiter, with adversarial parser controls.

See [actual execution and limitations](ANDROID_PROCESS_RESTORATION_VERIFICATION_2026-10-26.md).

The additive [active-child case](ANDROID_CHILD_PROCESS_RESTORATION_PROTOCOL.md)
uses a separate create-only fixture, actual reviewed fork and unchanged probe
v1. Optional NativeFork register/run mutation attempts map to `other` only in
the debug observer; status/lookup/cancel/close resource calls are outside that
mutation observation. Root expectations stay unchanged. See its separately
attributed [execution report](ANDROID_CHILD_PROCESS_RESTORATION_VERIFICATION_2026-10-26.md).
