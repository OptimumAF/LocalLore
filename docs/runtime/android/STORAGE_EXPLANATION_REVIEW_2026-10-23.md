# Independent storage-explanation review, 2026-10-23

Refs #5, M01.05 partial, claim `6376019687`. Reviewed from exact base `16453e77c6b45d160bfa2c996178d83f68edcd2e`; production explanation is coordinator commit `a965ddc`. I authored only the independent test file and this report. No device, SDK, model, build or GitHub operation was performed by this review.

No concrete defect was found in the reviewed explanation boundary. This host-only addition exposes the existing failed gate's physical-host accounting; it does not change admission, identify a responsible writer, repair preservation evidence or admit another inference attempt.

## Independent checks

The new `test_android_storage_explanation.py` has 20 methods covering all five physical-host partitions, canonical role order independent of private alias names, maximum shared reserve and summed growth, copy-byte accounting exactly once, signed consumption, exact/one-byte budget boundaries, guest-only failures, identity drift, strict malformed types/shapes/overflow, input nonmutation, privacy and both CLI modes. Tests include the preceding run's exact public numeric deltas using synthetic aliases.

Actual command:

```powershell
python -B -E -m unittest discover -s scripts/tests -p test_android_storage_explanation.py -v
```

First selection: **17 passed in 0.091 seconds**. After adding the retained numeric case and additional CLI boundaries: **20 passed in 0.111 seconds**. Both runs exited zero; logs and exit sidecars are retained. These overlapping selections are not added as unique tests. Test commit: `58bce63f200f5851b0c9933fb2b580ff3a0e9e19`.

An independent AST comparison against the frozen base confirmed unchanged `copy_size`, `validate`, `host_budgets`, `identity`, `before_probe`, `after_probe`, `run_with_admission`, `Observation` and `report`. The reviewed module bytes match coordinator source, SHA256 `f0493b72b3db69b4152bef2f5e28c2dac2faef81ff1dbdda113cdf5773c10d6a`. The new explanation delegates its authoritative post verdict to the original gate. Invalid samples raise without partial rows; CLI input failures use the fixed envelope. Identity drift produces the original blocked verdict and no comparisons. Host-row success cannot override guest or cache-growth failures.

The fixed failure envelope concerns sample/parsed-value validation. Argument-syntax errors retain existing `argparse` behavior; for example, a noninteger spelling of `--model-copy-bytes` fails argument parsing before the sample envelope. No broader all-invocations JSON guarantee is inferred.

## Retained observation reproduced offline

I independently matched the coordinator's selected input hashes to the preceding sealed device evidence and checked the retained CLI output against its receipt. The existing post result equals the original controller's post result exactly. The CLI returned **2**, with **1,444 stdout bytes**, SHA256 `97f7830024748454a081e7210de1fbbbd9c93dcce73b013706cc9d94ea25f69b`, and no stderr.

| Physical group expressed only by roles | Net consumption | Allowance | Result |
|---|---:|---:|---|
| Userdata host | 2,383,126,528 bytes | 67,108,864 bytes (64 MiB) | Consumption failed; reserve satisfied |
| Shared cache/evidence host | 805,814,272 bytes | 1,073,741,824 bytes (1 GiB) | Consumption and reserve satisfied |

The shared cache/evidence reserve is 10 GiB, applied once. These are whole-volume endpoint observations, not app-attributed writes or peak allocations. The earlier storage verdict remains blocked. This calculation neither diagnoses the timeout nor explains the older cache-directory/marker metadata difference or supplies missing final database preservation checks.

The independent review index binds six selected test/source-audit entries, 22,851 bytes. Index: **1,391 bytes**, SHA256 `88d00e60a7096c047d1d203cbe3a9049bf925c63f769ab770934ee82529cdd51`. It preserves both actual test runs and the input/output/source comparison receipt, without publishing private inputs or paths.

I also rehashed all 30 selected analysis entries / 160,893 bytes with zero mismatches; index SHA256 `651d80e56d59a04280b46693eda371733b2a16ed3481a476079d63626bd56cca`. The coordinator's bound full-suite log records **380 passing script tests in 5.369 seconds**, including these 20 methods. That is a coordinator execution, not an additional reviewer run.

The final [safe aggregate](STORAGE_EXPLANATION_RESULTS_2026-10-23.json), **2,706 LF bytes**, SHA256 `c8f1fa6ce0ea71adf28b41a8b160cbef6c692dea4298414cbc9233d940c1273d`, reproduces the retained CLI explanation exactly. The [verification](STORAGE_EXPLANATION_VERIFICATION_2026-10-23.md) and [analysis](STORAGE_EXPLANATION_ANALYSIS_2026-10-23.md) correctly preserve the failed storage verdict, uncertain metadata cause and missing final preservation evidence.

## Limits

The [protocol](STORAGE_EXPLANATION_V1.md) correctly distinguishes comparable supplied samples from authenticated identity, fresh admission, causal explanation and a passing cohort. Public rows disclose logical roles and accounting only; aliases, UUIDs, device identifiers, paths and exception prose are omitted. No policy ceiling, original controller output, runtime, model, dependency or canonical authority changed. The previous failed experiment remains failed, and full M01.05 acceptance remains pending.
