# Author packet A: retained baseline capture failure

Refs #25 D04.02 and draft PR301. **The first baseline is invalid; Author behavior
remains on hold.** The owner approved bounded code checks and metadata1152 to
1280KiB in reply `call_14b5bb739550487cae49278285b3fa3d`. That approval excluded
automatic retry and did not authorize an application or model run.

## What actually ran

Source `a07352542ebc27e83840ba34f23be67becf74926` is the independently reviewed
formatting of the old-behavior extraction. All16 FIRST groups and assertions were
preserved. The formatter exited0 with known closure, followed by a successful
offline build of the existing fixed synthetic `protocol-fixture` program.
Neither command executed an app, packaged worker or model.

The baseline Cargo command compiled the runtime test executable and started the16
filtered groups. Its stdout exceeded the6144-byte capture limit. The coordinator
made one kill attempt against its Cargo child27788, which closed with SIGTERM and
no numeric exit code. The retained process receipt records `overflow:true`,
`unknown:true`, `count:null`, and `processTreeContained:false`.

Captured stdout6144B and stderr964B are lossless **prefixes**, both marked
`complete:false`. The stdout ends inside the repeated failed-test-name list,
before the final summary. Visible failure labels and progress dots cannot
establish an executed16-case result, a final12/4 count or valid behavioral RED.
The original source, Stage, admission, START, STOP, raw prefixes and process
receipt remain unchanged. No GREEN or Author behavior commit is permitted from
that incomplete result.

The direct command ran from2026-10-31T06:56:43.838Z to06:56:51.480Z; its wrapper
reported7.642s and Cargo reported6.86s compilation. These are code-check costs,
not inference or user responsiveness measurements.

## Read-only observations and preservation

Post-failure checks found zero currently attributable target/test/fixture,
scoped compiler/tool and WebView processes, zero ambiguous matches, and zero
matches for the recorded PID or direct children. This is a later process
snapshot, **not retrospective descendant containment or successful drain proof**.
The original unknown/invalid classification is permanent.

Inventory after the failure measured37 retained runtime fixture roots/0B,
target12,278,854,670B, and metadata1,146,368B after the read-only review record.
The existing normal desktop binary retains SHA256
`0482d821a12a92333a9974a43f301d5fe36d5ca08e7c75843c3d04f19b0e6f1f`
and was never launched.

The compiled failed-baseline unit executable was preserved as an exclusive
ordinary copy in the same target:8,210,944B, SHA256
`6063b167cbd8366edddcf777a210fe6c06e4a14cbe8bf20fdfc2a6017351da5e`.
The target became12,287,065,614B. No test was executed for this preservation,
and no output was deleted or moved to a new target to fit a limit.

## Next decision

The capture limit was too small for the complete repeated failure roster. A
[separate R2 plan](D04_AUTHOR_CODE_R2_ADMISSION_2026-10-31.md) proposes one corrected
baseline with12KiB stdout/4KiB stderr. The larger output is unmeasured; it is
headroom, not a promised result. Preserve every original failure and carry the
successful format/prep only under their actual original source/tool identities.
Fresh closure observation, independent source review, full storage admission and
another explicit owner decision are required before any corrected invocation.

There was no app/native IPC/WebView/model/C++ worker/Android/device/OS qualification.
All four earlier native app grants remain spent. D04 and the desktop epic stay open.
