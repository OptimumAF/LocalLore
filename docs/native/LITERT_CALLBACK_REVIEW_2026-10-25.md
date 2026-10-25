# Independent callback observation review — 2026-10-25

Refs #9 (M05.05), #5 (M01.05). Root claim 6399434479; review claim 6399531875.
Sole reviewer-owned report on `review/m05-callback-final`, from
`c4f032e8d00f9bb64978b1a389ed9b359b08eda8`. Prior pinned-source findings are
preserved in [callback research](LITERT_CALLBACK_RESEARCH_2026-10-25.md).

## Source and counterexamples reviewed

The integrated code keeps actual production setup, Candidate admission, worker,
resources and SDK invocation. It introduces no alternate transport, model,
callback provider, native getter, schema, deadline or resource-release authority.
Candidate creates the final bounded callback trace only in the explicit receipt
profile; the nullable getter has no reset/setter or owner-replacement power.

The six counters are historical observations of validated output chunks/bytes,
DONE and three closed error categories. A per-call handle binds its exact parent
slot by object identity. Only the first three configured requests are retained;
the independent total makes omissions explicit. One monitor protects begin,
paired output mutation and snapshots. Arithmetic is bounded, saturation means
overflow rather than merely reaching the cap, and copied collections/map entries
remain immutable. No caller strings, Throwable, path, identifier or clock enter
this trace. Configured caps/UTF-8 sizes are not tokenizer usage or full rendered
SDK input; accepted output omits rejected/filtered content.

The adapter first calls the unchanged `error(cancelledBoolean)`. Category delivery
is in a guarded finally: a diagnostic throw cannot replace an original callback
throw. Cancellation subclasses retain their old Boolean semantics. Local finite
type membership yields CANCELLED/SDK_JNI/OTHER without inspecting message, class
name, cause or stack. SDK_JNI is provenance, not a native numeric status or cause.
The default category method is no-op, preserving existing fake-resource seams.
No observed category releases a quarantined call or authorizes a commit.

Request accounting follows original validation/storage admission and precedes
conversation construction. The captured handle is passed to that OwnedCall.
Output accounting occurs only after original field, length, strict UTF-8,
cumulative-buffer and think-marker checks; a rejected chunk cannot inflate its
accepted counters. DONE accounting follows original callback bookkeeping/finally.
Late/duplicate/mixed terminal observations remain representable and cannot prove
native epilogue, quiescence, known close or future-callback immunity.

The strict optional 1339 decoder enforces closed version/fields/types, prefix
size, ASCII, bounds, contiguous first-three slots and declared-order saturation
subset. Missing is None rather than a fabricated zero record. JSON key order is
not required for parsing; producer serialization is canonical. Independent
1337/1338/1339 channels may coexist without invented cross-trace causal rules.
The controller retains client raw first, parses/persists callback metadata before
the unchanged positive runner/proof gate, and stops on malformed or failed
persistence. A diagnostic cannot promote a failed test to a positive proof.

Source review covered 15 producer tests and seven actual worker/owner integration
tests using four-byte synthetic files/resources: configured UTF-8 counts, accepted
empty chunks, invalid content/UTF-16/oversize paths, cancellation, late callbacks,
quarantine before category and zero delivery/commit/reuse/unsafe close. Sixteen
decoder tests and two added controller cases cover finite wire/privacy/framing,
independent channels, raw retention, malformed records and persistence refusal.
These are authored/source-review facts until actual retained results are checked.

The normalized worker source SHA
`d25b7d5a370c15dd858227a3298ff60edaf1559d2684a9279af677e0530d128a`
independently matches Candidate constant/MANIFEST and the Gradle guard. Explicit
source bindings include the producer, both JVM test files, contract, decoder and
host tests. APK audit excludes both new JVM test classes from APP. No concrete
source blocker was found; this is not owner acceptance or execution evidence.

## Actual verification and runtime disposition

Independent replay of terminal receipt and regular results matches copied XML:
476 tests /44 suites and 418 /39, respectively, zero failures/errors/skips; lint
zero errors and 19 /9 warnings. Both APP/TEST pairs match their copied artifact
hashes, all six audit/signature records are completed 0 with known cleanup and
matching raw captures. Extracted ARM64/x86_64 Rust-library bytes are equal
across profiles; that is packaging evidence, not ARM64 execution.

Both profiles'221 Android rows match current source. The receipt and Rust
compilation source is `c4f032e8d00f9bb64978b1a389ed9b359b08eda8`; regular is
`d57429ceeb04b1e50ad1d0f221d1ec8ce624b163`. In the broader 303-row Rust/fixture/
host-script index, receipt/Rust differ from execution only at one host test;
the regular index already includes that correction. It adds `owner.methods=1`
to model the completed IMPORT before selected START. The original 806-method
suite has one ERROR before intended dispatch/raw capture; it is retained.
Corrected targeted 36 methods pass 2.943s /owned 3390ms. This fixes test setup,
not app/Rust behavior, and does not waive the pending corrected full host gate.

The private preparation helper allows only that exact path and actual c4f to
d574 file bytes, then requires the final host source index to match execution.
It is not a general exception to source equality. Actual Rust/native build
inputs remain unchanged; claiming every broader 303-row index unchanged would
be inaccurate. Retained Rust raw 65 result blocks match 351 core pass/4 historical
ignores and 90 adapter pass/0 ignores, with fmt/Clippy and nine portable cases
passing. The reviewer inspected retained records only and ran no checks.

Corrected final Python is actual 806 PASS/64.321s, zero failures/errors/skips;
completed 0/known cleanup 65094ms, stdout 95203B SHA
`ddd8e904cab38384c8d612703a1a5b093ffa57290e64b7ec927360124d1f8a92`.
Its 221 Android and 303 broader Rust/script rows all match execution source
`f4af26e50aff2a9a031b03c669ca7007241cff1d`. The full execution snapshot matches
1572 current/snapshot files /19,310,999B at admission.

The actually admitted receipt APP is 75,025,120B SHA
`75639fa0097f0267249780c3c9caec3e81edcbdc59b9bf382cb985eb85583ebb`;
TEST is 2,056,611B SHA
`a1ccef7bf35f758092af1780e53b5748c733b71cb272427c007867bd7aa7dee5`.
Their current controller pins, copied artifacts and proposal/archive bindings
agree. Existing model/runtime identity and all profile/cleanup caps remain fixed.

## Fresh inputs and actual preflight

PREPARE `ab1628e8…807ce` and RUN `39e2221a…dd036` pass independent closed-policy,
linkage and preservation checks. The reviewer hashes 905 non-image software
contents /1,332,027,052B and checks four SDK images plus the blank 8GiB SD by
metadata only. Three immutable config/registry files and completed preparation
closure match; private token hash/old registry are preserved without disclosure.
The profile remains 8GiB guest RAM/four cores/12GiB userdata/8GiB SD/max 1800s,
C/D 40GiB and host 12GiB floors. Root performs the stronger full 909/blank-SD hash
checks. This review occurs after preparation; a running descriptor is already
present at the final linked-input observation, not evidence of boot or success.

Actual PREFLIGHT original 69270 was consumed by the coordinator with terminal 0.
Independent replay verifies 44 completed 0 known-clean client raw records, one
strict selected method PASS and 12 true checks/485ms/no SDK or model copy.
Outer child0/capture+cleanup true is 47407ms. Its proof SHA is
`9d9f0cf9a306e94ab5df85beb9f597add3b47f97f8235e276ccbc017221d5767`.

Preflight proposal SHA
`4929eeb190fde6e05b5d0e0a85200f0bc244eb42a9b0332e25c7294d0ab891c9`
has 127 exact archived inputs /87,709,213B. A first candidate builder refuses
131 inputs under the unchanged 128-binding cap before candidate proposal/grant
or transfer. The subsequent private builder combines four complete compiled
indexes into one bound JSON: all original paths, hashes and complete parsed
values independently equal the originals. It drops no compiled rows and changes
no required source/control/proof contract or count cap.

That builder itself was a preflight binding and was edited after preflight
completion. Exactly that one current preflight binding now differs; all archived
preflight copies remain exact. This is not a claim that all 127 current preflight
files still match, nor a fresh execution of its validator against the edited
helper. Runtime source, APKs and prior result/fact/proof/owned-result links remain
unchanged. The candidate has its own current helper and exclusive archive.

CANDIDATE SHA
`1ca87c3bcf7df8b5a25670a2703565ebba35234fad2153dbec7c8cab8909e052`
passes the strict ordinary-scope validator and all 128 current/archive hashes
/87,743,209B, including complete-index aggregation. Standing human local-copy/
SDK consent and actual preflight links match. Model contents are excluded from
generic bindings; only fixed metadata is reviewed. The cached-prelaunch cheap
lease recheck observes exact running `be8650a8…0397`, three live identities,
no stop/result and 1496.9s remaining against 920s. Candidate authorization is
already present at that observation; driver is absent. Root owns admission.

## Actual partial outcome

Original candidate 2600 was consumed by the coordinator with tool terminal 1;
the retained worker result is 2, child_exited, known capture/cleanup 368078ms.
Outer stdout 466B SHA
`488ef10e4a790c194a7aecbfe16325eaf5f75218b517cbbe8dade67b58f70c33`,
stderr 0. Independent replay verifies all 46 completed 0 candidate client records
and their stdout sizes/hashes, separate from 44 preflight clients. A shell0 is
not a JUnit pass. Three selected methods pass across P/I/START; Dialogue fails
and reopen is unrun. Only 56 of 122 planned checks qualify.

| Phase | Actual result | Checks / whole observation |
| --- | --- | --- |
| SOURCE_PREFLIGHT |1 PASS; no SDK/model copy |12 /485ms |
| IMPORT |1 PASS; model 2,588,147,712B; no SDK |16 /93010ms |
| ORDINARY_START |1 PASS; actual SDK gift, revision 1 /receipt 1, repairs 0 /fallback false |28 /82066ms |
| ORDINARY_DIALOGUE |1 FAIL; no positive proof |0 /51.239s runner |
| ORDINARY_REOPEN |UNRUN |0 /none |

Import proof SHA
`06460a8a2069017c533c6298aa612d5af06556a5cd1357bf416ef20b4753ab23`
links to the actual preflight; Start proof SHA
`db41ee8aead54a952c50e873759c3ceffa07cda5c5ea57dd0600ee0f72e44f59`
links the new process and positive worker trace. Gift receipt SHA is
`c885026d098ebd56f0b319f5658cad64a95ae88329fad2f2d76eb72c50795447`.
These are whole-test observations, not isolated generation, cancellation or UI
latency, and do not establish a causal performance difference.

Dialogue runner 6226B SHA
`8f231ad10c450233a8342cf7f3fa92dbdf8244c1e181cf838dca9a8eae0f77ff`
strictly refuses the unchanged positive grammar. Its independent raw 1337/1338/
1339 extraction equals all three retained sidecars. The new callback sidecar
450B SHA `cf62bdc4b176c7d89f747b2d79bebaaca97ec96e4981f27ddb4ccb60a4efa41e`
contains one DIRECTOR, context 4096 /max-output 350, prompt 6811 /schema 425
application UTF-8 bytes. It records 21 validated output chunks /61 bytes,
SDK_JNI=1, DONE/CANCELLED/OTHER=0 and no saturation. This actually exercises the
new failure transport and finite type classification, not a numeric status API.

Send-v1 records argument/public-call-site RETURNED=1, THROWN=0. Worker-v2 records
21 paired MESSAGE callbacks, one paired ERROR and CANCEL, UNCERTAIN=2, no DONE,
settled drain, known conversation/engine close or Narrator creation. Counters
are independent historical observations. ERROR plus SDK_JNI does not identify
which SDK/native stage failed; the configured 350 cap and 61 bytes do not reveal
tokens, EOS, truncation, context occupancy or error cause. Cleanup cancellation
is not proof of a user Cancel click. No Dialogue/reopen proof or post-failure
canonical/model inspection is credited; the last qualified canon is the gift.

## Known closure and final preservation

Only after candidate terminal consumption did root request the exact owned stop.
Original owner 61132 was consumed with tool terminal 0. Retained stop_requested
is 705782ms, worker 1 from requested job drain, capture/cleanup/closure true,
guest-flush false. Independently hashed copies match 11213 stdout and 1090 stderr
bytes. Post-stop host metadata observes the three recorded owner/worker/launcher
identities absent and ports free. Host/process preservation closure does not
prove hidden SDK reclamation, guest flush or final virtual-disk integrity.

Every inventory row's size/hash and each exact namespace file set were checked,
excluding the inventory files themselves; no weight/virtual-disk row was read.

| Namespace | Files / bytes | Inventory SHA-256 |
| --- | --- | --- |
| Host |1740 /175,541,437 |`ad4dbf108ce1fe02a9935ef1bcebd28bd4637ef38e78d829d096f3f884e04b84` |
| Environment |27 /390,231 |`ef6c4f6e3c88047155961b8319a80b896db8c15f7f462f0f4ba14934eab17431` |
| Preflight |234 /87,839,024 |`2bc2d710dc93a4dc2c28f2d8aa17940e311e6e82e5e8b97288b70de3fb7dd9d8` |
| Candidate |247 /87,897,317 |`f9571857508a77bebc2123785207d99ba2755134281720d876e02a9790f96767` |

Total 2248 indexed files /351,668,009B, excluding four inventory files. Current
1006 non-Markdown rows /13,409,674B still match execution f4af; later reporting
edits may affect documents only. No sealed namespace was modified by reviewer.

No reviewer build/test/SDK/ADB/AVD/model/image/disk/cache-content operation was
performed. Complete ordinary Dialogue/reopen, physical phone/ARM64 execution,
16KiB/runtime pressure, NPC secrecy/prompt resistance, quality and milestone
acceptance remain unqualified. Prior error causes remain unknown.

The next evidence gate may investigate a separately designed structured finite
SDK status channel. In the pinned asynchronous JNI adapter, the numeric code is
a separate argument and the message is `status.message()` payload, not an Absl
code-prefixed string. Kotlin embeds both into public exception text. Recovering
its code through that text requires message access and parsing, which this
packet does not perform or authorize. A structured API avoids that dependency;
neither approach is implemented or accepted here. No getter, retry, new native
call, forced commit or reuse of the uncertain owner follows from this report.
