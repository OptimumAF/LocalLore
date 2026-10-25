# Finite-regex storage admission plan, 2026-10-25

Refs #9 (M05.01/.02/.05/.06) and #5 (M01.01 preparation only), claim [6401921941](https://github.com/OptimumAF/LocalLore/issues/9#issuecomment-6401921941). This source-only follow-up preserves the earlier [C-root snapshot and small compression experiment](FINITE_REGEX_DEVICE_ADMISSION_2026-10-25.md). The new available D: capacity makes a **plain new D-root preferable to introducing compressed VM backing**. This report supplies a staged admission plan, not an emulator/model/SDK grant or a physical-device result.

The user's requested removal of four archived generated targets was automatically rejected before dispatch. No removal, bypass or retry was performed by this reviewer. The increased D: capacity must not be attributed to that rejected removal. A separate merge owner is using C: for its own checks; free space and available memory are observations, not reserved resources.

## Fresh host sample

Read-only CIM metadata at **2026-10-25 19:10:55 UTC**:

| Resource | Available bytes | Unchanged required floor | Headroom |
| --- | ---: | ---: | ---: |
| C: NTFS | 50,899,107,840 | 42,949,672,960 (40 GiB) | 7,949,434,880 |
| D: NTFS | 83,453,370,368 | 42,949,672,960 (40 GiB) | 40,503,697,408 |
| Host available RAM | 29,599,277,056 | 12,884,901,888 (12 GiB) | 16,714,375,168 |

These samples support planning a fresh D:-backed target with substantial disk margin. They do not establish current CPU availability, port availability, a new live owner, boot, guest capacity or final APK identity. No device inventory or targeted device call, SDK, VM, model/cache/image read, copy, build or test was performed in this follow-up.

## Finite volume budget instead of an invented cache maximum

Source inspection in the coordinator checkout at `3efe84dfeb22aa7a314a7a3ce91a35a2106df0a3` confirms:

- The unchanged four-core profile requests 8192 MiB guest RAM, four vCPUs, a 12 GiB userdata volume and an 8 GiB SD image. Scoped registry/content/emulator-home/temp paths derive from one new root; no link or cross-drive redirection is needed.
- `AndroidReceiptModelAccess` places receipt control in app-private userdata and accepted data below the selected removable app-files root. `ReceiptModelTransaction` places both `model.litertlm` and `cache` inside that external data root. `CandidateLocalModel` supplies those paths to `LiteRtRoleWorker`, whose `EngineConfig` passes that cache directory to the pinned SDK. This proves the configured cache path, not an SDK filesystem sandbox.
- The full staging source remains in userdata. The accepted model and its configured SDK cache share the same finite SD volume. Both model copies are 2,588,147,712 bytes; neither is another host allocation **in addition to** budgeting its entire guest disk backing. An existing host source is read-only, not a third new model copy.

Consequently, a verified **single 8 GiB backing for that guest SD** can budget the accepted model and arbitrarily changing cache contents together. There is no need to invent a per-cache byte maximum or promote a historical cache size to a ceiling. Other guest temporary writes are covered by the independently finite userdata volume when they actually reside there. Guest low-space or native failure remains a possible measured outcome; this plan does not promise successful inference.

Budget the two primary volumes at their full logical capacities, without any compression saving:

```text
12 GiB userdata + 8 GiB SD = 21,474,836,480 bytes
D headroom above40 GiB    = 40,503,697,408 bytes
remaining for other D growth = 19,028,860,928 bytes
```

The prepared SD contract permits up to another 1 MiB of image-format length. Count its actual size. The remaining approximately17.72 GiB is real planning margin for additional generated backing, filesystem/QCOW2 metadata, temporary files and evidence; it is **not a claimed measured requirement**. Before admitting model work, inventory the new target's actual writable backing graph and allocated/logical lengths. If a raw base and a writable overlay both remain, count each host file independently. A guest volume bound does not by itself cap duplicate host images, emulator logs/temp files, host pagefile growth or unrelated writers. SDK source images already present and read-only are not new copies unless the actual plan creates copies.

For scale, an actual additional12 GiB userdata overlay would still leave6,143,959,040 bytes of that D: margin for other growth; this is conditional accounting, not a claim that such an overlay exists. Retain the full capacity of each actual writable backing plus bounded temporary/evidence growth. Keep logical guest size, current allocated bytes and remaining possible host growth as three separate facts.

This is now a concrete finite primary-disk budget that fits the snapshot, rather than the earlier insufficient C-root margin. It does not require worst-case compression ratios, an unbounded-cache prediction, or changing the guest profile. An unexpected backing graph is grounds to stop and recalculate within the existing margin, not silently assume a smaller image or raise an allocation ceiling.

## Keep the stronger40/40 requirement explicit

The existing environment helper deliberately has different defaults: D-root uses C:16 GiB/D:40 GiB, while C-root uses40/40. Its shared device facts use still lower existing host floors. Those defaults alone **cannot establish this assignment's stronger40/40 policy**.

Use a separately frozen, hash-bound **additive coordinator guard** for the new D-root. Do not edit the helper defaults, spoof proposal values, choose a link, or claim that the existing16 GiB check was40 GiB. The guard must independently retain C:/D: free-byte samples and require each at least42,949,672,960 before and after environment preparation, boot admission, tiny preflight, the full source stream, import, and each fixed ordinary SDK/reopen phase. Check12 GiB available host RAM again before environment/SDK admission; the existing at-least-eight-logical-CPU and exact guest four-CPU checks remain separate. Bind this private guard in a separate outer manifest/grant keyed to the exact inner proposal/grant/source hashes: the helper's closed proposal/auth shapes and exact SDK/source binding set do not permit extra guard fields or arbitrary extra bindings.

Ordinary success must require both the original operation outcome and these additive post-checks. Preserve an original timeout/error separately from a failed storage postcondition. If cleanup or the live owner becomes unknown, issue no dependent post-sample/device/hash/recovery call; retain uncertainty and stop. A phase-boundary check is not a hard filesystem quota, continuous monitor or guarantee against another owner consuming space during a bounded phase. Do not claim such a guarantee. The unchanged reserve is still an actual admission/postcondition gate; concurrent resource loss can produce a faithfully retained failed observation.

A separately bound2-second host-metadata monitor can reduce detection delay without claiming continuous reservation. Its failed sample, unknown cleanup or floor breach must block subsequent phases. For a live RUN supervisor it may request only the exact proposal-bound owned stop receipt, then await known terminal cleanup. PREPARE has no stop-receipt watcher: any monitor-assisted cancellation there must use the outer existing owned Job/cancel-event mechanism and preserve the partial target and original result. Writing a RUN stop receipt cannot be described as stopping PREPARE. Monitor and operation outcomes remain separately retained; no external owner is stopped.

## Exact staged handoff

The earlier document gives the installed CLI shapes. For this plain D-root plan use the same calls with a new ordinary D: path, **without compression**, and the stronger guard above:

1. **Freeze the environment procedure first; finish actual artifact qualification before device work.** A create-only host PREPARE can be independently admitted while APK assembly is finishing: freeze its exact installed environment tools/source, new path, resource guard and outer grant. Before boot/preflight installation/model work, require actual final APK assembly, lint, dependency/signature/manifest/native/alignment audit and source readback. Pin both qualified APKs and the new codec/selector dependencies in the real-route source closure. Do not reuse old static APK hashes merely because host512/native215 checks passed. Bind the guard, original helpers, prepare/run source and fixed phase selectors through the proper inner and outer manifests. Each grant remains disabled until its own exact closure is reviewed; no fake final-APK assertion is needed for independent host preparation.
2. **Admit only preparation first.** Fresh paths and fixed ports must be absent/free. With the stronger host samples and separate matching environment prepare grant, call `receipt_avd_environment.py plan-prepare --root <new-D-root> ... --real-model-candidate --four-core-candidate`, then its exact `prepare` phase. This creates the fixed SD and generated config, not a model or SDK owner. Retain allocated/logical metadata and40/40 post-check. Keep any failed/partial target untouched. The small compression probe is not a prerequisite for this plain route.
3. **Admit boot on the exact prepared root.** Use `plan-run` and its separate hash-bound run grant, preserving the 1800-second ceiling and owned supervisor/descriptor. Confirm actual new writable files and their backing relationship, guest identity/CPU, memory, empty package namespace and independent userdata/external capacity. No existing AVD is adopted or restarted. Before model work, subtract any additional backing allocation from the remaining D: margin; do not count a primary volume twice or omit a duplicate.
4. **Run the reviewed tiny real-source preflight.** Its existing180-second driver needs at least200 seconds remaining on that same lease. It installs only the pinned fresh pair and streams the original61-byte probe with local-copy/SDK flags false. It must pass exact runner/proof/UID/mount/owner/capacity checks and the stronger host post-check. Do not run the alternative old synthetic `receipt_fresh_target` install first on this same initially-empty target.
5. **Then freeze the single ordinary model/SDK grant.** Standing local-copy permission covers this isolated destination; do not add a new human approval requirement. The coordinator's exact grant still binds the successful preflight, source identity, same descriptor and future destination. Before transfer, retain userdata at least3,796,107,264 bytes free, plus APK requirements before installation; external before import at least4,735,631,360 bytes. These stronger controller floors remain unchanged. Require at least920 seconds left before the existing900-second ordinary driver. Freeze all static/hash work early enough that review does not consume the lease.
6. **One fixed sequence, without retry:** `receipt_ordinary_scene.py run --proposal <ordinary-proposal> --authorization <ordinary-grant> --evidence <new-evidence>` performs the once-only held-FD stream/import, ordinary gift, dialogue/inspection and no-SDK reopen. A client-zero stream is still transfer-only; app-domain full model verification/receipt authority remains mandatory. The same finite8 GiB volume budgets model plus cache, while runtime rechecks retain the existing guest low-space floor. Do not raise timeouts, reduce output criteria, bypass failed owners or dispatch an alternative PLAY sequence into that namespace.
7. **Close honestly.** Retain raw-first output, original failures, exact proofs and additive storage results. Only known-safe owner state permits proposal-bound stop and closure verification. An observation may fail despite the available planning margin; keep it rather than manufacturing success. No old emulator/model/cache cleanup or automatic new attempt is authorized.

## Current disposition

There is **no longer a blanket storage objection to planning the plain D-root primary volumes** at the measured free space. The next runnable step is root's exact artifact/guard/source freeze and a separately admitted new-D-root preparation/boot observation, followed by the existing tiny preflight and conditional ordinary grant. No further model-size or native-cache research is needed merely to invent a cache maximum: verify the finite backing enclosure instead. This preparation does not waive the remaining actual gates, guarantee timing/capacity under concurrent activity, grant execution, or satisfy full M05/M01/physical-phone acceptance.

At handoff I read the final artifact manifest and current static receipt pins: app75,041,504 bytes / SHA-256 `83797af66672e5bab89e17d53339478eb7c57bee66773c9c72edd13466911a8a`, test2,056,615 bytes / `e5d09b0f436237b51c647b4cc43a74e8f76b08bfdfe045907aa89ee6724f359d`. Manifest SHA-256 is `86a61b33aa591e6fb689b879ee9f01cc65304ff43657854f36060f4969698db5`; its values match those source pins. The companion implementation reviewer independently qualified packaging; I did not rerun its build/audits or hash the APKs. The local read-only preparation index binds two files /1,804 bytes, SHA-256 `a6167f060c93b98a88a13f83436271b237b5df0b3d91c1d9c18bb212094cb618`, containing host metadata and seven source byte bindings. Only this new document is changed in Git.
