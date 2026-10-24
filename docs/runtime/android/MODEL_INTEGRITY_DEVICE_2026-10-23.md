# Read-only model integrity observations, 2026-10-23

Refs [#5](https://github.com/OptimumAF/LocalLore/issues/5) (M01.03/M01.05),
base `aec8ad0`. This follows the [authorized copy report](https://github.com/OptimumAF/LocalLore/blob/1bde6a50a66be087d8b18fd0a81e6e0413d90d64/docs/runtime/android/LOCAL_COPY_VERIFICATION_2026-10-23.md),
not a new inference experiment. Source and B matched the pinned identity; A was
stable within this scan but mismatched the source and its own earlier recheck.
The cause remains unestablished. Both caches were preserved, all inference is
held, and task acceptance remains pending.

## Identity, coverage and observations

The required installed benchmark APK remained
`715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6`
on both selected targets. It is the existing experimental build from harness
`e7beb858b271aa4636f2f5e7b34deedda1fc3f21`, with LiteRT-LM Android0.18.1 CPU
pinned to `bda624851d74be34d4e1f7fac1fc4155939539c7`. No SDK initialization,
inference, app start/stop/restart, provisioning, repair, deletion, cache eviction,
model transfer, dependency or runtime change occurred in this packet.

Inventory showed four online emulators and zero physical devices. Only the two
authorized A/B aliases were inspected: already booted Android15/API35 x86_64.
The benchmark process and matching process-name prefix were absent before and
throughout guarded reads. All21 current LocalLore APK identities on each target
were captured before and checked unchanged after that target's observation.
This does not audit every save database or assert that unrelated OS activity
made no storage changes.

Each receipt covers all **2,588,147,712 bytes** in **78** contiguous ordered
32 MiB chunks. Chunks0–76 have33,554,432 bytes; chunk77 starts at2,583,691,264 and
has4,456,448 bytes. Three receipts retain234 records. There were six independent
whole-file SHA256 observations: before/after for source, A and B.

| Target | Whole-file SHA256 before and after | Complete chunk comparison |
|---|---|---|
| Source | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` | Two complete source passes, with repeated chunk equality |
| A | `2dde0b287178132dc8b0fdcbd30fba12b087f54993c0e7ee6d135a5394921700` | Chunks0–71 match;72–77 differ |
| B | `181938105e0eefd105961417e8da75903eacda102c4fce9ce90f50b97139a63c` | All78 match |

A's differing chunks cover the following intervals, totaling172,228,608 bytes
of chunk coverage. This is not the number of individual changed bytes and does
not locate the first differing byte inside chunk72.

| Index | Offset | Bytes |
|---:|---:|---:|
| 72 | 2415919104 | 33554432 |
| 73 | 2449473536 | 33554432 |
| 74 | 2483027968 | 33554432 |
| 75 | 2516582400 | 33554432 |
| 76 | 2550136832 | 33554432 |
| 77 | 2583691264 | 4456448 |

The earlier A recheck was
`59d70767f8f7a8710fb2d1427e3cf94917ca5b6847fdbfd11f1fcf2617f0eb4d`;
the new bracketed reads were both `2dde0b…`. An unchecked interim progress
message repeated the historical value; it was corrected against the current
receipt/log. That message was not another scan, a failed observation or a retry.

A/B named-file and bounded cache-prefix metadata remained equal across each
bracket: regular/non-link checks, filesystem device/inode, mode, size and exposed
mtime/ctime. Access times were not used as identity. A's separate XNNPACK cache
remained788,412,736 bytes; its content was not read. B had no matching generated
cache file. Source inspection checked one regular named file/handle and its full
fingerprints before/after; private preflight metadata and the tested inspector's
identity flag retain that binding without publishing unique identifiers.

## Read method and limits

The read-only verifier was `benchmarks/model_integrity.py` at
`727806087b83fd109fd5e43d7042d0715c08addd`, source SHA256
`1660fb02085cf63b7c4accdbf77ac94a4f257037def596fa8663d87bed008096`.
Its exact receipt fields are `version`, `chunk_bytes`, `identity_unchanged`,
`before`, `after`, `chunks`; each chunk has only `index`, `offset`, `bytes`,
`sha256`. The source inspector performs two complete bounded-memory reads over
one handle and checks named-file/handle fingerprints and repeated chunks.

Private device wrappers used the existing frozen `TrackedDevice` helper. Before
long reads they checked host storage, benchmark process absence and exact APK;
process/storage guards also ran before each chunk. Full SHA256 came from separate
whole-file commands, not from hashing a list of chunk digests. Each device chunk
used fixed4096-byte `dd` blocks with exact offset/count, on-device `wc -c` length
confirmation, then a separate on-device `sha256sum` read under `set -o pipefail`.
Only counts/digests/metadata left the device. Independent whole-file reads
bracketed the complete chunk pass; regular-file metadata and all current APKs
were checked again afterward.

Commands were invoked as follows, with private wrapper locations redacted:

```text
python <private-observer>
python <private-collector> source
python <private-collector> A
python <private-collector> B
```

These are redacted argument records, not public runnable wrapper paths. Remote
commands used the fixed benchmark package and app-private model; no arbitrary
file search, SQL, SDK execution or file write was exposed. The exact private
wrapper versions and their hashes are sealed below. Source reads and comparison
used `inspect_file`, `validate` and `compare`; no new build or dependency was
needed. The coordinator independently ran the pinned CLI comparisons.

Stable fingerprints and repeated hashes are trusted read observations, not proof
against a hostile same-UID filesystem race or evidence of durable backend
writeback. No cache flush, forced model writeback, reboot, filesystem repair or
model overwrite was attempted. These readings neither identify a historical
change time nor establish SDK mutation, host disk-full corruption or any other
cause. The earlier pinned-source review remains limited to its inspected paths.
No narrative-quality, profile, throughput, ARM64 or phone pass is claimed.

## Storage gates and retained failures

Two setup failures preceded all complete model observations:

- The first inventory wrapper accessed a nonexistent `ProcessResult.stderr`
  field while serializing metadata. Its `AttributeError` record and wrapper were
  retained; the inventory result's full status fields were not retained. The
  corrected wrapper used the actual `stderr_bytes` interface and completed the
  preflight. It did not restart a timed-out model observation.
- The first source attempt failed the unchanged1 GiB host-free gate before any
  model/device read launched. That guard was initially outside the catch, so its
  exact failed free-space value was not recorded. A distinct subsequent short
  measurement showed655,175,680 bytes free. Both facts are preserved separately.
  No model scan was launched until the coordinator completed preservation-first
  relocation and hash verification of its inactive compiler outputs.

The read-only gate was1 GiB host free plus ample secondary-volume capacity.
This did not lower the separate4 GiB inference gate. After resume,166 per-call
storage checks all passed: C minimum5,198,635,008/maximum5,317,955,584 bytes;
secondary-volume minimum123,806,466,048/maximum123,910,684,672 bytes.

| Stage | Host C free bytes | Secondary volume free bytes |
|---|---:|---:|
| Corrected preflight | 1,738,420,224 | 132,783,120,384 |
| Source start/end | 5,316,431,872 / 5,304,524,800 | 123,910,684,672 / 123,910,647,808 |
| A start/end | 5,317,955,584 / 5,277,483,008 | 123,910,631,424 / 123,903,750,144 |
| B start/end | 5,276,401,664 / 5,198,635,008 | 123,903,741,952 / 123,806,466,048 |

Guest data free before/after was A1,054,400,512/1,054,269,440 bytes and
B1,800,536,064/1,800,622,080 bytes. Read-only measurements do not attribute those
small changes to a particular actor. The observed A cache plus a1 GiB reserve
is1,862,154,560 bytes, exceeding B's final free space by61,532,480 bytes. This is
an admission concern for future cache growth, not a retroactively stricter claim
about the old before-only1 GiB guard. The observed cache is not a known maximum.
Next work must preserve existing data while establishing cache-growth/storage
admission before any separately authorized B control; matching B alone does not
authorize inference. A's unexplained mismatch remains a separate blocker.

## APK preservation and evidence bindings

The following common map was independently read after each device and exactly
matched that device's21-entry preflight map. The two final maps were equal.

| Package | APK SHA256 on A and B |
|---|---|
| org.locallore.app | `652a7bd3f0ab157bdb0fa07e8191b27210ce03e0dbb28f5e79766dd51062fd43` |
| org.locallore.app.archivecapacity | `aa09afc46d0921a1e43f739a3c6331f2fbd839301f533d2ca5ac0b5c4e4e6bb2` |
| org.locallore.app.archivecapacity.test | `1d7fdbe216a7d720f0d3342711159cb61053f27dbdf45a2b8b572d4037aef967` |
| org.locallore.app.archiveverify | `5a058eef62d1e56e9326ac71a959bd1205ae9a96820b42626abda6530e93944f` |
| org.locallore.app.archiveverify.test | `ffbbaab9b7ebeeb4322904567dfc66308b299463bdffe2b3074520aa1132fa08` |
| org.locallore.app.capacityfaultsv3 | `e149627f2d36ea3491124806c3e982991dc7b78d0224d478a923b05632799d2f` |
| org.locallore.app.capacityfaultsv3.test | `ff04a113c96e8dbda617b49132d1483a24f268793532eb26976ffe6fa07e56d4` |
| org.locallore.app.capacityrelief | `7968c0e15ae7058c89a03f88a1ed6c79899a1fa6aefd7bac7befba79c395c1c0` |
| org.locallore.app.capacityrelief.test | `81366501c6876470e7639c00f14bb439c3a256b50a4792159079d0586cac1708` |
| org.locallore.app.capacityreliefv3 | `3e8ae7bbaeb80f2d917d089e8a6d35350ab01483128636a172314126938ac8a9` |
| org.locallore.app.capacityreliefv3.test | `c795af855cf80dd52adb1452c1e4be985074da813de2a7d7aec9d74218438334` |
| org.locallore.app.capacityv3 | `2877ed91202d5f70d48e65e64fd61791d724ce5f809d271ec3c6ce716dead4c7` |
| org.locallore.app.capacityv3.test | `f367b24c3c53902371c9ec1411ab553e22c3b218c773feeb34794fc913c46634` |
| org.locallore.app.parentverify | `9a68c915ce963a38a5a0beeafbc7465ff4d8c28b65953457b3a8beeb45aa6d17` |
| org.locallore.app.parentverify.test | `6fa5ea0703aabee5b0d783a57f44c5986a240ce0c57cb3c02fa4930975848889` |
| org.locallore.app.storydelete | `5bc796b6ec25d7d3a40915c0965e7e03473a532760314766e1b2b42210df4319` |
| org.locallore.app.storydelete.test | `3181eea3396d4378b9250c9896e9dccc4823695c86536745e18d6e5a0fb8063b` |
| org.locallore.app.test | `8a3a479d9f83c4f2f487fe101aa4b521ddf0c6396a42377a0977eb1f93540236` |
| org.locallore.app.timelineverify | `6531e71834f7a6e8c14f0b9abec64c8a4dca1b783c3ce0bb3e6332a760987117` |
| org.locallore.app.timelineverify.test | `17d34f5deb4f59881637158ff82f2ef8b3107b787bbd2f969310462c1cc2576e` |
| org.locallore.runtimebench.litert | `715a6c4521592256b1ee6e1bf9ec4d0f3f1974dcdde040781269163efbc534a6` |

All702 retained transport records completed with return code0 and client cleanup
confirmed. After both collectors exited, the selected/inventory host ADB client
census was0, with one ordinary server. The initial inventory serialization
failure's missing fields are not silently reconstructed. The transport journal
records alias, operation, sequence, status, output and stderr byte count;
command arguments are bound by private wrapper-source hashes, not duplicated in
that journal. It was closed and hashed **before** creating the aggregate/index.
No more device calls occurred; the A/B read-only lease was released.

All31 retained private files are sealed by `sealed-index.json` (4,951 bytes),
SHA256 `9f544120124819770fee5b5fc9744d213d708c47ddcca11a0cdd196a39f87524`.
The files remain private; basenames, lengths and hashes below publish no weights,
private paths, transport identifiers, raw diagnostics or player data.

| Private evidence ID | Bytes | SHA256 |
|---|---:|---|
| A-chunks.jsonl | 10401 | `ebf8058380c76dc7a91a77dcb3a7fb196d89aef6ae0f6d651391a0b94b2b27d1` |
| A-comparison.json | 656 | `e19f2dc97efad635fd97d74d79fe14477ef8c55cec3f4d98392b453b45d2cdf1` |
| A-facts.json | 4942 | `d2f1d426b97686e7b9c94098a97e42c8489a10995344b757698212e1c2ac0c72` |
| A-final.log | 2122 | `52d2daaa08141160ea8c8f2866337ea17fdcf6b24a763b2e0a3b86aec7f5cf83` |
| A-receipt.json | 13879 | `e862af7a035e15993bcca33f2aab76c1bab31d24d427d9433750876cf16f8d1e` |
| B-chunks.jsonl | 10401 | `29f41790c5892f99eb28326e447d9917591a305190f88103db4e1a67c6982e47` |
| B-comparison.json | 116 | `d00c1ec276187dc98a781ee9f1b8dbd1d27cfe761131185c8445409c62a2b6b6` |
| B-facts.json | 3802 | `ac575e69c905469a73fbe3dc14499abda2c19bacd81642f61af1fb23bc4d991b` |
| B-final.log | 1785 | `6bdc33c9307a2f910b5cd9c36b68eadc8b5eddf9500f96b7a7b0db26586095f6` |
| B-receipt.json | 13879 | `5ee4288f1ca2ba8490b6fff1e7432fd85e70a0ba488cba8d60177fa75b9daa4d` |
| collect-initial.py | 5320 | `93265b846874c98f43ba0f1b956de642190843eb86cf91295355ae9925cef9f9` |
| collect-v2.py | 5417 | `43f1a35924f214f817b266ab85d40548ba97ef7bfe637f977a8ef373e5a4eb0b` |
| collect.py | 5551 | `d2465632c216446c755b0ba9671eb1ff664c93b32c5c87b6f0eacbbbbd79eead` |
| handoff.public.json | 7598 | `d9b09eed56d02712c4d8c9a4de85195d52a3d4eae1e15aae3f5483db6fefc7b7` |
| host-client-census.json | 129 | `09cb376e202b46a8bf91eeee11f7a9a71f51be878cfb76ef31332fe518149046` |
| inventory-raw-v2.json | 620 | `3935d73bcbb250e5dd0d9d1e8cf668eb30b8770f760518d56936b3bb8a6af5c5` |
| observe-initial.py | 6145 | `31ba0214aa7694916aaecce6f0a772e938ab5a5388127922c363c75a1ca7266c` |
| observe-v2.py | 6222 | `b0714df62c64a37b17fd9399b87b9b7c7252c991df085f8cd69f53a059f2e3af` |
| observe-v3.py | 6560 | `583e9e1cc76516423684556e7939f4324090c9f0c8fe97f1dde8ac802f2894d3` |
| observe.py | 6711 | `33946b2f74f29e8b9da9ee6d6485bf71827d9ba6071db0cbb952910451fdccfe` |
| owned-output-sizes.json | 2050 | `9bab7081a88926c36c94e82d45daeab78df6ea6b9187ea6f3390bd4a8ce9a9cb` |
| owner-v1 | 28 | `859a9b3c387a6da1230c8e5c6a740791744eecfc803fd7760fb4259a44fbc1bc` |
| preflight-v2.json | 6438 | `9059675caba9e636f0dfcf5cb36f808391c0dc87a321e9eee59bb11ab62b51c9` |
| preflight.json | 244 | `08ea84b187bc0e46c7bfe8faea938f035136e875f120a1af0e9d542c890ee617` |
| source-facts.json | 618 | `f2c3593ca58328a6c95eff21a5140eba6751e0223ed4e079a16a7d5d38252ce3` |
| source-final.log | 338 | `66b42e457c27ef8b835c3d126a4761825189c81254f02cc8a280e9d2ed4d4332` |
| source-receipt.json | 13879 | `5ee4288f1ca2ba8490b6fff1e7432fd85e70a0ba488cba8d60177fa75b9daa4d` |
| source-storage-blocked.json | 457 | `6f6101f25844317d09fe5f93a6ada4320b01884899180daa565c078f25f75f10` |
| storage-checks.jsonl | 17762 | `8259a0dd1e646808de440bae2f1437a086ebc634ef2b5bd72e75e48dafd1457e` |
| transport-binding.json | 294 | `9e99b60092ba05309cededa0bba9016845ac6811339bd7bba8c6e488aad90c21` |
| transport.jsonl | 1798861 | `fd46e5a31d72d5cfcdfd3f18e80c1e3ca75516fd42e8db82cb9dafdf3e6330aa` |

The source and B receipts have the same digest because their hash-only records
are identical; their independent reads are bound by separate facts and journal
records. Documentation validation rechecks the sealed hashes, receipt coverage,
comparison results, metadata/APK preservation, links and sanitization. Owner
acceptance and all inference/model/device qualification gates remain separate.
