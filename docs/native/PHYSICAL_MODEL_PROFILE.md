# Explicit physical model profile

Refs #5 (M01.01/M01.05), coordinator claim 6406017018. This is a pure pre-install
policy for the previously observed alias P, not a universal phone minimum,
hardware tier, allocation guarantee or measured model result. The independent
inventory is [recorded separately](../runtime/android/PHYSICAL_DEVICE_INVENTORY_2026-10-25.md).

`benchmarks/physical_model_contract.py` performs no IO, subprocess, device or OS
API operation. Its only assessment entrypoint is `assess(sample)`. Caller-supplied
booleans do not authenticate authorization, physical identity, package absence
or preservation; the separately admitted trusted collector must establish those
facts and retain their identity/freshness/ownership bindings.

## Fixed profile and model

| Constant or predicate | Contract |
| --- | --- |
| Profile | `s918u1_api36_arm64_4k_v1` |
| New isolated pair | `org.locallore.app.phoneverify` / `org.locallore.app.phoneverify.test` |
| Model | 2,588,147,712 bytes; SHA256 `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` |
| Observed hardware | SM-S918U1, API 36, SM8550, kalama; first ABI arm64-v8a; 4,096-byte pages |
| Kernel-visible RAM band | 10–12 GiB inclusive; earlier observation 11,581,173,760 bytes |
| Available RAM | At least 4 GiB; an existing project margin, not an OS requirement |
| Power and battery | USB powered; scale 100 and level at least 20; temperature 0–399 tenths Celsius |
| Thermal status | Exactly 0 |
| Namespace | New pair absent; prior known modelverify pair's host-verified metadata unchanged |

Available RAM in the earlier inventory was only 3,311,497,216 bytes. That sample
is a memory refusal under this policy, not evidence of current eligibility.
The old installed pair is preserved; this module never supplies a replace,
uninstall, user-app control or settings action.

## One shared internal filesystem

The original staged source and accepted model are two complete copies in the
new app's internal storage. Before either exists, require:

`2 × 2,588,147,712 + 2,147,483,648 = 7,323,779,072 bytes free`.

Use one `internal_free_bytes` observation. Shared/emulated storage views are
not added together and do not become independent space. The explicit physical
shared reserve is 2 GiB. It is at least the existing userdata floor of
1 GiB + 128 MiB and the importer's 256 MiB margin; those margins are included,
not added repeatedly. The earlier removable-volume reserve of 2 GiB is a
different policy. Neither legacy emulator policy changes here.

This pre-install snapshot cannot authorize a later copy. APK/ART installation
and source-directory creation consume space: the Android/host path must freshly
recheck the two-copy budget afterward, before staging. After the source copy
exists, the missing accepted copy plus the same 2 GiB reserve must remain.
The actual context-derived source and accepted roots must be independently
proved to belong to the new app UID on the same internal filesystem. No UID or
filesystem proof is invented before the app exists. Existing full-hash,
create-only, path/owner, receipt, cancellation and unknown-owner fences remain
mandatory. This margin is not a cache-peak bound or a live quota.

## Closed observations and result

The exact flat input keys are `version`, `authorized`, `physical`, `model`,
`api`, `soc_model`, `board_platform`, `abis`, `page_bytes`, `memory_total_bytes`,
`memory_available_bytes`, `internal_free_bytes`, `battery_level`, `battery_scale`,
`usb_powered`, `temperature_tenths_celsius`, `thermal_status`, `new_app_absent`,
`new_test_absent`, `prior_pair_unchanged`. Version is exactly integer 1. Booleans
are literal booleans; numeric fields reject booleans, floats, strings and nulls.
Byte values are unsigned nonnegative values within signed 64-bit range, with
available memory no greater than total. Metadata tokens and the unique ABI list
are bounded; unknown keys are refused. Thermal status accepts only integers
0–6, battery values are consistent bounded integers, and the temperature value
is a bounded signed integer. Structurally valid but ineligible observations
receive fixed reasons; unavailable or malformed samples receive only
`invalid_sample` and no partial observation.

Output has exactly `version`, `scope`, `profile`, `status`, `reasons`,
`required_internal_free_bytes`, `required_available_memory_bytes`, `observed`.
Scope is `physical_model_admission`; status is `admitted` or `refused`. Reasons
are ordered: `invalid_sample`, `unauthorized`, `not_physical`, `profile_mismatch`,
`memory_capacity`, `storage_capacity`, `power_or_temperature`, `thermal_capacity`,
`namespace_collision`, `prior_pair_changed`. Valid observations expose only
seven numeric resource/power fields; no serial, UID, path, mount identifier,
exception text or caller-selected destination is echoed. Reports are fresh
values and do not grant device operations.

Peak memory, cache growth, sustained temperature, inference completion, quality,
model/SDK compatibility and runtime acceptance require separately admitted
measurements. Passing this contract alone qualifies none of them.
