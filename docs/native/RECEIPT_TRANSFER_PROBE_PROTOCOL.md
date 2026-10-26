# Original synthetic receipt transfer controls

Refs #9 (M05.05 prerequisite), #5 (M01.05 supporting). Disabled by default;
no model weights, inference, story writes, runtime selection or production
controller change. This measures transport after the retained PR178 copy timeout.
The [official-source research](RECEIPT_TRANSFER_SOURCE_RESEARCH_2026-10-25.md)
motivates controls; it does not establish the cause of any installed failure.

The host source is a create-only file named `locallore-transfer-fixture-v1.bin`:
1024 identical 1 MiB blocks from SHAKE256 of the original fixed seed
`LocalLore original transfer fixture v1` followed by LF. Its exact size is
1,073,741,824 bytes and SHA256 is
`93b6ba41cf54e72a26ab955cdf953420847be6229f592ea79770362c91558c3f`.
Generation holds one block, forces the file and refuses an existing destination.
Repeated blocks are synthetic controls, not a model or a compression benchmark.
The file is excluded from generic read-all binding validation and evidence copies.

A new source/APK-bound grant and live exact emulator owner are required after
the original 12-check receipt preflight. The profile remains API35/x86_64,
8 GiB RAM, four CPUs, 12 GiB userdata and 8 GiB removable storage. All prior
uncertain targets remain quarantined. The new grant permits only synthetic copy;
weight and SDK grants are not part of this scope. The app and test APKs remain
the previously audited bytes. Every source, executable, lease, APK and four
preflight evidence records is bound before admission.

The coordinator uses three fixed controls in order, with distinct create-only
sinks under `no_backup/receipt-transfer-probe-v1`:

1. CAT: the existing `exec-in` path and `cat`.
2. DD_1M: the same path with `dd bs=1048576` and exclusive shell redirection.
3. SHELL_CAT: `shell -T -e none` and `cat`, only after separate protocol/binary gates.

Windows now refuses SHELL_BINARY/SHELL_CAT before any shell qualification or
stream dispatch. The actual retained binary control stopped at26B of768B while
reporting client0; the original host CRT text/binary control reproduces that EOF
signature. A binary-open parent file alone cannot qualify the child descriptor.
CAT/DD keep the proven `exec-in` route. The portable shell command descriptions
and strict binary proof parser remain for adversarial tests, not Windows runtime
admission. Historical failing outcomes are preserved; no large shell copy is
silently retried, escaped or treated as equivalent to the source.

No `of=`, truncation, append, rename, deletion, permissive path selector or
source/sink override is admitted. Parent directories, fixed owner marker, leaf
type and UID are checked. Full source SHA/size authentication and final held-FD
identity checks remain. Each mode has an exact live parent, proposal/grant/facts
hashes and a create-only claim consumed before the client is started. The client
timeout is still `min(150 seconds, parent remaining time - 5 seconds)`, inside a
180-second owned parent; the aggregate owner is 900 seconds with 920 seconds
required at entry. No clock shifts or increased budgets qualify a result.

After known client success/cleanup and the source/lease postchecks, a separate
guest read verifies full size/SHA256 and exact fixed path/UID. A full host cursor
or return code zero alone is not a destination proof. Failed/unknown client,
owner, capture, proof or process observation stops subsequent controls. The
next mode follows the previous exact proof and current package/process/storage
facts. No candidate installation or app instrumentation is part of this probe.

Immediately before SHELL_CAT, require a bounded `features` response containing
the exact whole-line `shell_v2`, actual fixed app-UID `exit 42` then `exit 0`
client results, and an original 768-byte binary copy/readback. Its bytes are
`bytes(range(256))` repeated three times, including NUL, CR/LF, 0x1A, tilde and
high bytes. Full SHA256 is
`f3a25aa93aa2fbba28d79260535bbd6a5eb0fc1c24a8b0f04e12b484c1dfe363`.
Those bytes are created in a fixed exclusive regular file in the owned stream
worker, authenticated and passed through the same held-FD client path as the
large source. A pipe-only input test does not qualify regular-file stdin.
The probe child omits TERM; production environment policy is untouched. No
large shell copy follows a failed gate. Earlier qualified CAT/DD controls remain
evidence if this later candidate fails. Even after qualification, summaries
conservatively leave `remote_exit_status_known` false; destination proof is
separate. Model staging now explicitly uses the byte-preserving `exec-in`
selector and its separately documented parent envelope in
[candidate protocol](RECEIPT_REAL_CANDIDATE_PROTOCOL.md); no shell substitution.

Private evidence retains every client raw output and metadata before parsing,
source input attribution, timing, proofs, failure-only stream observations and
host owner closure. No weights, selected tokenizer payloads, emulator images,
keys or raw private diagnostics are published. Host closure is not guest flush,
SDK drain, model acceptance, phone latency or full scene qualification.

The environment also checks Windows system commit headroom, separately from
physical RAM. Revised launch policy is one guest-sized allocation plus a separate
2 GiB project reserve (4/10 GiB for the existing 2/8 GiB profiles), identified as
`guest_plus_reserve_v2`. The former twice-guest charge was not supported by the
[version-matched source review](EMULATOR_COMMIT_REASSESSMENT_2026-10-25.md).
The helper is source-bound;
both parent and owned worker recheck before allocation/claim/SDK launch. A
snapshot is not a reservation or a launch guarantee. Insufficient capacity does
not authorize a smaller profile, interruption of another project, OS/pagefile
changes, or reuse of a stopped target.
