# Retained-parent deletion UI verification, 2026-10-26

Supporting M10.02/M08.05/M08.01, based on draft/unmerged PR #208 at0ee763e5.
This packet exercises the existing real MainActivity/dialog/controller/native
deletion path; its [protocol](ANDROID_RETAINED_PARENT_UI_PROTOCOL.md) keeps the
two new UI cases separate from the earlier native10 and broad89 rosters.
Full milestone tasks remain unchecked pending broader criteria and owner acceptance.

## Implemented and host-checked

The two original Android cases seed a new typed Rust root/P/G fixture before
MainActivity launch. They drive actual Compose selection and deletion buttons,
compare complete eligible player/receipt views and catalog records, exercise
Cancel then explicit confirmation, and reject one stale P3 preview after a
separate typed writer reaches P4. Retained child messages are also checked in
their rendered Compose rows. There is no SQL, substituted gateway, root
retirement, model, new dependency, or retention decision implemented in Kotlin.

The fixed `retained-ui` host phase admits only that one class/two methods with
the existing fresh namespace, source/build/tool/server/lease/user guards and
original client bounds. Its closed `retained_ui-v1.json` cannot replace either
old gate. Realistic interleaved-client host cases reject partial/skipped/extra
frames, changed bytes, wrong counts/phases, missing class copies and unknown
cleanup. The shared strict roster validator retains the existing broad89 checks.

The pre-integration driver subset passed36 tests in11.864s, owner12,475ms/0,
known cleanup/stderr0. After integrating the exact Android source roster,
all40 driver tests passed in12.877s, owner13,402ms/0, known cleanup/stderr0,
757 unchanged mapped inputs. Original stdout8,219B SHA-256
`64dadb3967fbd43fe2acdcfc6ddb28601bd7756d7fea9067d2534dd17eef8050`.
These are host checks, not compilation or an executed Android result.
The final rendering/refusal assertions were added afterward; fresh full-host,
JVM/build/audit and actual owned-guest UI checks remain pending at this checkpoint.

## Phone gate kept separate

A single fresh read-only availability observation used the phone harness source
from [unmerged #186 at5bca14e6](https://github.com/OptimumAF/LocalLore/pull/186),
in a separate clean worktree. Three clean captured host clients completed in
an owned8,812ms process, exit0/known cleanup/stderr0;92 source bindings match
before/after. Four device-list entries advertised no matching authorized
Samsung profile candidate. Target calls are exactly0. No phone memory sampling,
installation, model copy/load/inference, or substituted emulator occurred.
This snapshot establishes no current phone resources or arbitrary-device identity.

Independent recovery verification matches14 originals/ZIP entries,30,213B,
without mismatch/extra/duplicate/unsafe entries. ZIP14,486B SHA-256
`f2c86b3c2f6a609d4908f4ba9cb303094bedb363a758f7c623f57acae175e942`;
both4,544B indexes match SHA-256
`99b569b6c431fe0ea5f82f0a94401a2b87998725f4072bd39eda6a6406096fdc`.
The separately verified complete-history5bca14e6 bundle is8,978,989B, SHA-256
`c4607005b7d3f9ef4bf5973d13ef616f47c56d7f260cc2cfff4d357b33e235d0`.
Private serials, process data, exact commands and raw diagnostics remain private.

The independent [official runtime/model source review](https://github.com/OptimumAF/LocalLore/issues/5#issuecomment-6424190293)
confirms the existing pinned compatibility/license references; it selects no
new dependency/profile and proves no fit or physical performance. M01.01/M01.02/
M01.05 phone-model supporting execution stays blocked on actual selected-device
availability and unchanged fresh admission. No favorable resampling loop, other
emulator stop, system-setting/global ADB lifecycle change, merge or release.
