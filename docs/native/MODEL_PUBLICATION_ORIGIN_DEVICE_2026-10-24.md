# Native publication-origin device evidence

Refs #9 (M05.05 prerequisite) and #5 (M01.05 support), root claim 6384948023,
device/fixture subclaim 6384961894. On 2026-10-24, one ordinary selected diagnostic
passed **1 PASS / 0 FAIL** and observed **RENAME_INVALID**, with
`origin_classified=true` and the unchanged fixed STORAGE refusal. The resolved
native wrapper returned EINVAL in this fresh call. **Publication did not succeed**:
the exact 63-byte stage remained intact and the destination remained absent.
This result does not establish an exact filesystem cause or classify any earlier
failed attempt. Positive publication/store qualification remains blocked.

The fixture was developed separately from unmerged PR142 head `e05fc869` and
handed off in source-only commit `cf96adcd5707f549f519c2db68a70ba0316f5191`.
Compiled source was `69342d8ccc87fad61045ec516caca52bf74961d5`.
The exact selected instrumentation shape was:

```text
am instrument -w -r -e class org.locallore.app.ModelPublicationOriginTest#classifyFreshPublicationOriginWithoutFallback org.locallore.app.modelvolumeverify.test/androidx.test.runner.AndroidJUnitRunner
```

The actual B emulator ran Android 15/API35, x86_64, with 4 KiB pages. The fixture
admitted the production Context-owned volume and used only the fresh fixed
`model-publication-origin-v1` sibling, with a distinct internal
`model-publication-origin-proof-v1` receipt root. Previous failed volume and
publication-diagnostic roots were not read or written. Their 148/219/320-file
stopped/sealed histories remain unchanged. There was no LocalModelStore, SDK,
Engine, story workspace, real-weight, UI, picker or normal-launcher call.

Exactly one direct native publication and one result callback were observed.
The four new categories distinguish missing symbol, EINVAL, ENOSYS and EOPNOTSUPP
while retaining fixed STORAGE failures; only those categories set
`origin_classified`. Legacy UNSUPPORTED and UNKNOWN remain accepted observations
without origin qualification. PUBLISHED would require exact destination bytes
and an absent stage. A refusal requires its fixed mapping, exact preserved stage
and absent destination. DESTINATION_EXISTS would contradict the initially absent
destination and fail the diagnostic. Nothing retries, deletes, replaces or falls
back. Nullable file-key metadata is not mandatory inode proof.

The forced bounded proof recorded RENAME_INVALID, one callback, exact stage
bytes/hash, absent destination, actual Context candidate-root absence,
`publication_succeeded=false` and `positive_store_qualification=false`.
Diagnostic PASS establishes this bounded classification/preservation slice,
not successful store import, removable-storage support or model/runtime support.
It does not turn the earlier UNSUPPORTED observation into retrospective EINVAL
evidence, nor identify an earlier attempt's underlying cause.

The proposal was initially disabled. Root and independent reviewer rehashed all
1,663 bindings / 172,484,785 bytes, including 64 shared and 13 private source
copies, before the one exact GO. Proposal SHA256 was
`bc7d7413915e40bad4de1df92c58d6e3c6362915dcf0a04dc134454a1e7fd131`;
the authorized copy changed only two admission flags, SHA256
`51cc3981744f3e8067f03f610e403cb5ed48ee2847332eded1527bb68caed3be`.

The original owned execution reached authoritative tool exit 0 and child return
code 0, known client cleanup, 43,891 ms elapsed, 482 stdout bytes and zero stderr
bytes. Stdout SHA256 was
`b8bf2132b6866c31055f299a7c7e66c7f2499dc73dd0e1712b3af4424ed77ed1`.
All 105 device clients had terminal/known-cleanup receipts. Two same-pair APK
updates preserved the other 33 APK hashes and all 35 installed UIDs. All
conditional APP/TEST stops were zero; final metadata observed no owned or passive
processes. This is an observation, not a native/SDK natural-cleanup qualification.
Cleanup guards captured PID/UID/name; they did not observe process start time.

Actual Context external-free observations were 3,556,827,136 before and
3,556,818,944 after. Userdata observations were 1,299,030,016 before/after;
final controller userdata was 1,299,017,728 bytes, above the unchanged
1,207,959,552-byte controller floor. These are boundary observations, not
reservations. The after observation is **1,178,812,416 bytes short** of the
unchanged 4,735,631,360-byte real-artifact import requirement. This capacity block
is independent of RENAME_INVALID. No model-copy admission or cleanup was attempted.

The local mocked controller/protocol suite passed 37 tests with zero failures,
errors or skips. Coordinator-owned offline regular and volume builds each passed
299 JVM tests across 31 suites, zero failures/errors/skips, zero lint errors and
seven warnings. Signed APK/native/backup audits passed. Both Android ABIs were
built; ARM64 and 16 KiB execution were not performed. The immutable host seal is
1,488 files / 170,117,736 bytes, SHA256
`81835dcbcfe140154f56c11432a4749ba6294d740ccd7fc187a469dd5c7dca5d`.

Root accepted the original consumed tool terminal before the frozen local-only
closure revalidated raw clients, bound sources/artifacts, proof and final gates.
The final sealed selection contains 327 files / 1,957,888 bytes; index SHA256 is
`7a87494483a08197d9fd59c889d835080be8e6ada88b4e6d995051826ad923d5`.
Independent final review rehashed all 327 files without mismatch and checked the
105 raw clients, proof, final package/UID maps and capacity observations (review
commit `1f243d47e38089ab2e99569c0a8752052a175076`). Raw identities, paths and
diagnostics stay local. Preservation follows the closed command scope and exact package checks;
this is not a whole-userdata byte audit. The single authorization is consumed,
with no live follow-on authority.

No clear/reset/uninstall, old-33 lifecycle, external-path traversal, A, real model,
SDK, Engine or workspace action occurred. Full M05.05/M01.05, physical phone,
ARM64/16KiB, real-model/SDK and A/#117/#119 gates remain incomplete. The next task
is a separately reviewed bounded EINVAL/publication compatibility investigation
or an explicit design decision, preserving no-clobber semantics and capacity
reserves. No remedy, storage change or publication fallback is authorized here.
