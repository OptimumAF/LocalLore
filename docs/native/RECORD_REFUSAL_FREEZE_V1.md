# Coherent SDK18 refusal-test freeze

M10.02, supporting M09.06. Host implementation for review, not run authority.

This generation preserves the existing SDK18 protocol, five cancellation UI
selectors, original APK pair, guarded preparation, shared storage ledger,
one-shot claims, process ownership and deadlines. It uses fresh fixed slots:

| Role | Physical D: location under Dev/Experiments/LocalLore |
| --- | --- |
| Generation | 2026-11-03-record-refusal-freeze-v1 |
| Executing operators | Generation/candidate-source-v1 |
| Immutable runtime profile | Generation/frozen-profile-source-v1 |
| Planning output | Generation/inspection-v1 |
| Future controls | Generation/run-controls-v1 |
| Future guest | 2026-11-03-record-refusal-ui-v1/avd-v1 |
| Future runtime | 2026-11-03-record-refusal-ui-runtime-v1 |

First, commit the two profile files with four new fixed role literals. Freeze
that exact Git tree, its 2,671 files and catalog. The executing inspector and
operators are a separate role: bind their source head/tree/count/catalog to
that immutable profile, run the actual file-only inspector, then bind its exact
handoff/preparation records and final inner operator/contract bytes into the
parent contract. The parent body and inner refusal-reporting behavior remain
unchanged. This order avoids a source catalog referring to its own future bytes.

The profile is commit dbcafb0070734cbccbd420a159f6305bc6f9090d, tree
53c47a25b00f2ca868150f76d408c3789a6fcc3c. Its catalog is 755,007 bytes,
SHA256 aa58a83cd42933165f659b454d768b3b6c4cbc4458efabf300704e09fd50de31.
The executing code tree also contains one new test, so its 2,672-file count is
not the runtime profile count. Frozen files are raw Git bytes, with exact modes,
blob IDs, lengths and hashes; imports/checkers must originate in their assigned
role. Neither a path retag nor a changed hash alone refreshes a generation.

The inspector hashes current installed tools and revalidates the original build
attestation/APKs. It emits only create-only planning records with
execution_authorized=false, allow_environment_calls=false and root_go_pending=true.
Its same-ledger capacity preview grants no admission. It does not query current
resource_facts or port readiness, prepare/reserve a guest, start ADB or create
human/parent authority. An ordinary absent guest parent is a planning prerequisite;
creating that empty parent is not guest preparation.

The existing outer and inner public loaders must consume the new bound bytes
without substituted factories. Missing current authority and old canonical
authority pins must fail before a live attempt. Old B116/B119/B120 sources and
records remain immutable; the previous approval is spent. Unknown original B119
failure details are not recovered by this freeze.

Actual future preparation/boot still needs a reviewed exact proposal, fresh
applicable approval, locked admission, available resources/ports and all current
ownership checks. The unchanged limits include 8 GiB guest RAM/four cores,
30-minute guest/40-minute operation, 40 GiB preparing/live reservation,
two unretired roots/64 GiB shared admission, and the existing memory/commit floors.
No code here grants that approval or weakens those checks.
