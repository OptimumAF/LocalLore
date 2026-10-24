# Cache-aware admission and capacity observations, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.05), base
`fdf144a`. Both actual fresh samples were refused by the new admission policy.
No eligible non-model capacity candidate was found in the fixed legacy runtime
area. No SDK run or storage mutation followed. The protected A/B Gemma caches
and [prior sealed integrity evidence](MODEL_INTEGRITY_DEVICE_2026-10-23.md)
were preserved; inference and owner acceptance remain pending.

## Actual read-only observations

Inventory showed four online emulators and zero physical devices; only the two
authorized A/B aliases were inspected. Both were already booted API35/x86_64.
The exact installed benchmark APK was
`715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6`.
The existing experiment remains harness `e7beb858b271aa4636f2f5e7b34deedda1fc3f21`,
LiteRT-LM Android0.18.1 CPU, runtime pin
`bda624851d74be34d4e1f7fac1fc4155939539c7`; its60-second/350-director/220-narrator
budgets were not exercised or changed. Benchmark process absence and exact
package identity were checked; current21-APK maps matched preflight after both
the inspection and final sampling on each target.

The metadata-only probe was confined to the fixed marked legacy runtime area
specified by the [native controller protocol](../../../benchmarks/spike/android/controller/README.md).
The existence test returned `ABSENT` on both devices, so no cache/run entries
were enumerated: **zero eligible candidate bytes** and no400 MiB artifact
preservation/removal plan. No matching historical runtime process was observed.
The source review found that protocol's native ELF cache, transfer staging and
supervisor runs all use the same fixed area. Other app-private warm requests,
weights, caches, saves and arbitrary directories were not cleanup candidates.
This is a bounded candidate check, not a global storage inventory.

Protected fixed model/cache-prefix metadata remained unchanged across the
packet. A's generated cache was788,412,736 bytes; B had no matching generated
cache. Neither cache contents nor model weights were read, hashed, copied,
repaired, moved, evicted or deleted. No app/SDK start, stop, restart, inference,
emulator/image operation or package mutation occurred. Model-source/B identity
was not refreshed for control admission because the storage gate refused before
that stage; the previous hashes are historical observations, not a fresh pass.

## Frozen policy and measured refusal

Actual CLI execution used `benchmarks/android_probe_admission.py` at
`9e66529da41d78c999c4bff786539fa24a12ab30`, source SHA256
`20fcfa3bc2971e89e4c30bdc9bd2916bd0665d2bc0f096eef1134242289d22f0`,
checked against its Git blob. Samples have exactly five fields: `version:1`,
`host_free_bytes`, `evidence_free_bytes`, `guest_free_bytes`, `cache_bytes`.
All byte values are bounded nonnegative integers. Host/guest/cache values were
fresh read-only OS measurements; the fixed cache prefix was statted, not read.
They are sequential measurements rather than an atomic storage snapshot.

| Actual field | A | B |
|---|---:|---:|
| Host free bytes | 4,941,430,784 | 4,942,188,544 |
| Evidence volume free bytes | 121,868,603,392 | 121,865,961,472 |
| Guest data free bytes | 1,054,388,224 | 1,800,540,160 |
| Existing generated cache bytes | 788,412,736 | 0 |
| Pure CLI exit | 2 | 2 |
| Before status | blocked | blocked |
| Reasons | host_headroom, guest_headroom | host_headroom, guest_headroom |

The policy reserves4 GiB host,1 GiB guest and10 GiB evidence capacity, plus a
planned1 GiB cache-growth allowance **before** starting. Consequently the before
requirements are5,368,709,120 host bytes and2,147,483,648 guest bytes. Neither
sample met either requirement; both evidence-volume measurements passed.
The1 GiB allowance is an engineering budget, not a measured SDK maximum. This is
a new explicit admission policy, not a retroactive change to earlier guards.

For an admitted future run, after-policy floors remain4/1/10 GiB; cache growth
and net guest/host consumption must each stay within1 GiB. Those after conditions
were not measured here because no run was admitted. OS free-space deltas alone
would not prove causal SDK consumption. The implementation wraps the complete
legacy controller, including its first SDK stop; callers must explicitly choose
`run_play_probe_with_admission`. Unchanged direct legacy calls are not globally
fenced by this packet.

A separate API exercise used each frozen actual sample with a no-SDK sentinel:
one sample callback, **zero probe calls**, `probe_dispatched=false`, no post
sample. No real device callback was passed to that exercise. It demonstrates the
blocked path on the actual inputs without invoking SDK lifecycle code. It is
not a failed model generation or a real after-run/unknown-ownership test.

## Commands, ownership and logging limits

Executed argument sets, with private locations redacted:

```text
python <private-observer>
python <private-fixed-runtime-metadata-inspector>
python <private-fresh-sampler>
python -B <frozen-root>/benchmarks/android_probe_admission.py --sample <A-private-sample.json>
python -B <frozen-root>/benchmarks/android_probe_admission.py --sample <B-private-sample.json>
```

The sampler ran each CLI once using the existing bounded process owner and
retained its stdout/status/exit/cleanup metadata. It then exercised the API
with those same inputs and a sentinel; it did not resample to seek admission.
No transport timeout or failed observation was retried. No model bytes left a
device, and no new build, dependency, SDK binary or profile was introduced.

One preflight logging gap is preserved: the reused wrapper's whitespace-sensitive
instrumentation left `host_storage:null` even though device identity/metadata
checks completed. That report was not rewritten or used as an admission input.
Separate programmatic read-only guards ran before/after fixed-area inspection
and around fresh sampling. All five recorded read-only host checks passed the
1 GiB/ample-evidence collection gate: C minimum4,941,430,784/maximum5,082,030,080;
evidence minimum121,859,919,872/maximum122,979,065,856 bytes. This lower collection
gate did not authorize an SDK run or replace the5 GiB pre-run requirement.

All **314 recorded device commands** completed with return0 and client cleanup
confirmed:104 preflight,108 inspection and102 sampling. Both pure CLI children
also completed cleanly with expected exit2. The final selected/inventory host
ADB client census was0, with one ordinary server. All21 APK identities and
protected model/cache metadata were preserved at the recorded checkpoints;
this does not assert byte-for-byte immutability of every save or unrelated OS
file. Journals were closed before aggregate creation, and the device lease was
released. No device calls followed sealing.

## Next bounded task

No safe reclamation plan exists in the inspected area. Preserve both caches and
prepare a separately reviewed capacity/cache-placement feasibility packet rather
than widening cleanup to user/app data. The pinned SDK exposes writable
`EngineConfig.cacheDir`, defaulting to the model's parent; a new experiment could
explicitly select a validated cache directory with a new artifact identity.
Actual SDK behavior at that location remains unmeasured.
[LiteRT-LM pinned configuration](https://raw.githubusercontent.com/google-ai-edge/LiteRT-LM/bda624851d74be34d4e1f7fac1fc4155939539c7/kotlin/java/com/google/ai/edge/litertlm/Config.kt)

An app-owned secondary cache volume is a source-supported candidate, conditional
on mounted state and measured independent capacity. Android's external-cache
API can also return emulated storage backed by the same userdata partition;
choosing an external-looking path alone does not supply capacity. Such a future
probe must reject absent/insufficient/shared-volume fallback and protect the
existing files; no cache path was changed here.
[Context.getExternalCacheDirs](https://developer.android.com/reference/android/content/Context#getExternalCacheDirs())

Changing cache placement would not automatically satisfy this frozen userdata
policy. Any volume-aware sampler or policy would need explicit review as part
of the new experiment, rather than relabeling external capacity as the existing
`guest_free_bytes` measurement.

The documented emulator SD-image option is a startup option, not a live change
to an already running device. A fresh-image/attachment or startup plan therefore
requires separate review/authorization and preservation of original images.
No current card's capacity, accessibility or suitability was established in this
packet. No image creation, resizing, restart or attachment was performed.
[Emulator SD images and startup options](https://developer.android.com/studio/run/emulator-commandline)

The next control would additionally need fresh source/B full identity, process
and package checks, sufficient host and actual guest/cache-volume capacity, the
explicit tested admission wrapper, and a separate coordinator admission. These
observations authorize no automatic B control, weakened budget or model-quality,
profile, ARM64 or physical-phone claim. A's earlier unexplained mismatch is not
resolved by metadata preservation or a storage refusal.

## Sealed private evidence

`sealed-index.json` (4,567 bytes), SHA256
`5e2fecac8e3e47427b1a86b6763b4f8e22c54feff74a25291994f9475239bb9e`,
binds all25 retained files below. Raw arguments, paths, process metadata and
wrapper source stay private. Public basenames/lengths/hashes contain no weights,
transport identifiers, raw diagnostics or player data. The prior integrity
packet's sealed files were not changed.

| Private evidence ID | Bytes | SHA256 |
|---|---:|---|
| A-admission-execution.json | 822 | `a3590b9caab022d0c8ebd14133939b46d36f62e294e93eed8801e9dc01f591a8` |
| A-admission.json | 514 | `577f2f4824b7f9ab1ad90f89feb44998ec89095ee3c5e8a4914a0774324e30a2` |
| A-sample.json | 160 | `ba9f6b5e63520ee425e968c81d8c368e56d85a155dd39baff764ad18d37dd88d` |
| A-sentinel-fence.json | 879 | `aeb30a7416e61a2719b049b89e076bb87d14844f6e0499d552005d1bd3c3bc0b` |
| admission-observations.json | 8093 | `bea8289de97dfb4992bce5eab9598c12bc4fe9429be775d4887f808c3dd3ba6a` |
| admission-observations.log | 610 | `645398c5a78e9fe8b484f86b78a32e267771493cd3b253379c817368f947290f` |
| B-admission-execution.json | 814 | `c1715dc883acde084cef7828099cb4a6aa5b04ca6cc7f956249ed2cc337f6ec1` |
| B-admission.json | 506 | `3966f0300c1a9f8934abe704695d25bbb9a5d739a3490a4f3a1ac598cfd3c732` |
| B-sample.json | 152 | `99f1115e9dd9dab4b3c03b1bee0d278adafc6c258e8b3d7c60265263590a5870` |
| B-sentinel-fence.json | 871 | `20a563a9326d97c88f07d3da6016988b7caf3e60bd445bb6f94ac7cf75fed2a1` |
| handoff.public.json | 3741 | `20d24f059e502dc45eb579bd0cfb9b564602feba3b019564cc83781befeab47e` |
| host-client-census.json | 93 | `24a7e17216fa837c1f1fd06d181a2aa257aa0ea26a27d41c53cfcfaf78ca8b1b` |
| inspect_runtime.py | 4392 | `455be2ab5cb21cde7f837f339b32b7de30363b00871479790ca57186264036d2` |
| inspection-transport.jsonl | 156254 | `d5db5b4c12f400801f21d6488cceab6bf9fa9f25f6c77f8eea9558bc43ef039b` |
| inventory-raw.json | 620 | `3935d73bcbb250e5dd0d9d1e8cf668eb30b8770f760518d56936b3bb8a6af5c5` |
| observe.py | 6882 | `781a1727ae51965a978fce5ce8fb5cfed981ea14b0a6536fe33b35beb8d9cf73` |
| owner-v1 | 28 | `f1a2b311501660239b2aa16a5c906c101d69b6c658ef43e0e54d739514ae45ef` |
| preflight.json | 6490 | `26b848c5ae40306f20104a3232d6988b480d3bf86e23488d31314129050f16cc` |
| preflight.log | 376 | `31736319f6857f4e52be11336e4080cc9e8e645270f568492d61f2cade5db01f` |
| runtime-metadata.json | 6808 | `6f5c5f4e28cccb4a18fc589aca5132458978b5d7d860d7131c7f2fa889697a73` |
| runtime-metadata.log | 426 | `ead9df59f2dd3b1bd4eee3d38ae134d87aa0c80e5c44a47980d0dbc825a0cafd` |
| sample-transport.jsonl | 77458 | `fe6998ef89af32a92a50d1ae8023ad914de6c4bed337668db444be0710b8fa77` |
| sample_admission.py | 4403 | `710ffa4fd6c33a3ae5aee14017e48c409a59188190a786ceb6826c2770bac734` |
| storage-checks.jsonl | 535 | `716dfd265575d19d8bb70f8362c530b8d4f76ad68500b1492981441bf2f77b8c` |
| transport.jsonl | 68192 | `7e8e5e37339ecef31e170b9b362a303f2eff8e045947a830087f862d2a9b0494` |

Documentation validation checks these bindings, strict sample/CLI equality,
zero-dispatch sentinel records, APK/metadata preservation, links, privacy and
whitespace. No full host suite or device-model run is claimed by those checks.
