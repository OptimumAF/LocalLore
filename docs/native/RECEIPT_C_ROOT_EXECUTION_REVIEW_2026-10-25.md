# Explicit C-root receipt execution review — 2026-10-25

Refs #9 (M05.05 prerequisite), #5 (M01.05 support). Independent review claim
6395142427 under coordinator claim 6395108793. This report covers the exact
explicit C-root cohort, its frozen inputs, recorded results and host closure.
It changes no implementation or milestone acceptance state.

The actual real-model **IMPORT passed**. **PLAY failed with
`LocalInferenceUncertain`; the guarded gift and REOPEN remain blocked.** No
successful canonical gift, post-SDK model recheck or restart qualification is
inferred from this attempt.

## Source and admission review

Execution source was `daad3b598a43b0fe862d894c5633a7ce77892ead`; APK compilation
source was `ea924a2c2cd7db78e342062225e0aaff52ff7b05`. The reviewer independently
rehashed all 1,522 source files (18,539,289 bytes) against both the frozen
snapshot and current checkout, with no mismatch. The compilation-equality diff
contains only the six recorded host/test/documentation files. All 206 entries
in the compiled Android source index (2,216,712 bytes) match both the current
source and execution snapshot. The reviewer did not rebuild either APK.

The fixed APK pair content hashes matched the retained artifact audits:

| Artifact | SHA-256 |
| --- | --- |
| Receipt APP | `fea69522642c5562134eab602cce55d006632fa451b40e55a247ce6a649c6140` |
| Receipt TEST | `7a8a32bedc574b4b3d57e476be54518d05dc641d6952c01ac8f70def2a326eb9` |

The coordinator's full script run is retained as **690 PASS**, 57.839 s runner
time, owned completed 0 with known cleanup at 58,547 ms. Its 81,314-byte raw
output independently rehashes to
`737f845d1e5e36542546cb0fae0b376afba7b499081a8092d7898d24c8bc3ff4`.
This is reviewed coordinator evidence, not another 690-test reviewer run.

The reviewer checked the exact typed disabled proposals and their bindings
before the coordinator issued each separate grant:

| Proposal | SHA-256 |
| --- | --- |
| PREPARE | `b2e6ffe58295fb6749a07e951bf0a116c179d873903072d104e312f0f81c4b3b` |
| RUN | `f0e9cc5807bca0fbc530fa91bfbb7be07cae77b4e912ab8cb324d80dbfa4fd86` |
| PREFLIGHT | `dc0305da7e9770e5c57f0b63b3550ffec1527fbf87b00be4ee18a18b5075fdfe` |
| CANDIDATE | `579ce9f139fd88598b6855f1535c89ea68490b0ecb2751250b36eca30c2b7d92` |

The preparation target was absent at admission review. Exact C40/D40 GiB host
floors, 12 GiB available host RAM, 8 GiB guest RAM, 12 GiB userdata, 8 GiB SD,
two cores, fixed ports and 1,800-second owner limit remained bound. No fallback
or old-target adoption was introduced. The preparation client completed 0 with
known cleanup at 28,172 ms; its 645 stderr bytes are retained. The normalized
config, registry and preserved generated config independently matched their
three metadata hashes. Userdata was absent before launch; guest boot was not
inferred from the running descriptor.

All 909 installation paths matched the proposal. The reviewer independently
content-rehashed 905 non-image installation/source inputs (1,332,025,888 bytes)
without mismatch. Four installed SDK `.img` hashes and the new initial SD hash
were inspected only as recorded identity/size metadata. The coordinator's
full installation/prepared verification is separate; this reviewer read no
virtual-disk content. Existing registry/config metadata matched; console-token
content was not read by the reviewer.

Before dispatch, all 79 PREFLIGHT inputs (87,570,455 bytes) and 83 CANDIDATE
inputs (87,576,696 bytes) matched both their live metadata/source/APK paths and
create-only input archives. The pinned owner/worker/launcher PID, creation time
and executable metadata matched at both reviews. More than the required owner
lifetime remained. These observations were admission checks, not capacity or
port reservations. The model path was statted only: fixed regular, nonlinked,
nonreparse 2,588,147,712-byte source, absent from generic input archives. Existing
human local-copy/SDK consent was bound; the reviewer supplied no new authority.

## Actual phase results

| Phase | Recorded result | Independent replay |
| --- | --- | --- |
| SOURCE_PREFLIGHT | 1 PASS, 12 true checks | Strict runner, proof and three fact sets agree |
| IMPORT | 1 PASS, 16 true checks | Strict runner, prior-phase link, proof and two fact sets agree |
| PLAY | Failed with `LocalInferenceUncertain` | Strict runner rejects; passive worker record is retained |
| REOPEN | Not invoked | No proof or later guest command exists |

PREFLIGHT used the fixed original 61-byte probe. Its 43 client outputs were
independently rehashed and replayed: empty namespace, fixed installed pair,
new distinct UIDs, exact selected identity/API/ABI/page size, volume and storage
facts. The owned child completed 0 with known capture/cleanup in 41,797 ms,
416 stdout bytes and zero stderr. Probe streaming did not attest remote exit;
the app-domain proof independently verified the probe. No model copy or SDK
execution is credited to PREFLIGHT.

IMPORT completed in 91,750 ms. Its staged-source verification and production
receipt import each recorded one open, one close and exactly 2,588,147,712
bytes. The proof includes actual READY and full accepted-model recheck checks,
with SDK/native publication false, and links the prior preflight hash and
changed process identity. Its SHA-256 is
`c7e511a67370caea7067e776f09b8ee2bb6fdb3ea5acc247476cc6d66f0d9c38`.
The after-import fact replay preserves the fixed APK/UID/volume identity and
shows APP absent with one permitted TEST helper. This is an import observation,
not the later canonical story REOPEN result.

The CANDIDATE cohort stopped at `instrument-PLAY`: 28 known-clean client
closures, two instrumentation commands, no pair updates. Instrumentation client
return code 0 does not mean its test passed. The failed PLAY transcript is
6,867 bytes, SHA-256
`55a430931ab5dc65c8104db7294e7ef7f1dbe23dce910546ea84b6d9b0371502`.
There is no PLAY or REOPEN proof and no post-PLAY fact dispatch. The owned
candidate child returned 2 with known capture/cleanup at 292,672 ms, 453 stdout
bytes and zero stderr.

## Passive PLAY observation

The strict worker extractor reproduces the retained 30-counter version-1
record, SHA-256
`ba097fabf578886923a402bc7af46d6f48b0d07d4ec413ca6f5c0518775d0610`.
Its saturation list is empty. Paired entries below show entered/returned,
except the explicitly named known-close counters:

| Observation | Count |
| --- | ---: |
| Admission; engine create; initialize admission; initialize | Each 1 / 1 |
| Role admission | 2 / 2 |
| Conversation create | 2 / 1 |
| Send admission; send | Each 1 / 1 |
| Message | 24 / 24 |
| Done | 1 / 1 |
| Error; cancel | Each 0 / 0 |
| Drain settled | 1 |
| Conversation close entered / known | 1 / 1 |
| Engine close entered / known | 0 / 0 |
| Uncertain notification | 0 |

These are bounded historical observations sampled before the existing failure
catch/finally. They neither form one jointly atomic lifecycle state nor prove
caller-observed drain, hidden native reclamation or a healthy owner. In
particular, zero `UNCERTAIN` or engine-close counters do not override the failed
runner. The unmatched conversation-create observation does not establish
narrator versus repair role, cause, valid proposal or a hidden native hang.
The fixture never reached its Prepared-dependent commit path; no successful
gift is claimed. No additional model hash was forced after uncertain ownership.

## Host closure and sealed evidence

After the candidate terminal, the coordinator requested the exact owned stop.
The owner result records `stop_requested`, known capture/cleanup and verified
closure, 749,297 ms, worker return 1, 13,777 stdout bytes and 1,908 stderr bytes.
The host post-stop record reports all three recorded identities absent and
ports free. Those are coordinator observations reviewed as metadata; the
reviewer made no new process-control or guest call. `guest_flush_claimed` is
false. Owned host closure is not SDK/native release or guest flush evidence.

The reviewer independently rehashed every file in all four sealed inventories
and checked their complete file sets, with no mismatch:

| Inventory | Files | Bytes | Inventory SHA-256 |
| --- | ---: | ---: | --- |
| Host | 1,533 | 18,921,195 | `7adedfd65f9d982a162250965a095ae8ae6ac69e9adc548c6919c2d67319849f` |
| Environment metadata | 25 | 392,813 | `fd56e6950748d0818d0f56fcf5b0a2c5a57c1cf8d840a0508fa4f189b03b4070` |
| Preflight | 182 | 87,674,800 | `8c09a6669f3028d13bc1026bf0e4c8054659d20117e9d2bcfff41702316f35f2` |
| Candidate | 156 | 87,669,188 | `ce29463cedcd886a6600f041a8ec53fe4d4845a54bdb5cc49b17821dbf8aa7e8` |
| Total | 1,896 | 194,657,996 | — |

The 17 copied closed-owner records (27,172 bytes) also match their bounded
original metadata/raw/config files. No model weights or virtual disks are in
these inventories. Raw private diagnostics and process identities stay local;
this report contains only bounded results and evidence identities.

## Remaining gate

No concrete frozen-input or evidence-integrity blocker was found. The observed
PLAY failure itself prevents qualification of the real SDK gift, post-SDK model
continuity and canonical restart/reopen. Physical phone, ARM64, 16 KiB pages,
power-loss behavior, quality and existing device/model integrity holds remain
outside this cohort. DocumentsUI/provider delivery was not exercised.

The next useful task is source/host investigation of the observed worker
boundary without retrying this uncertain root. Any later live cohort requires
its own frozen inputs, preserved state, fresh capacity/identity checks and
coordinator admission. This review authorizes no retry, cleanup, merge, release
or milestone checkoff.
