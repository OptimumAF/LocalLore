# D03 native verification - 2026-10-22

Final source: 571846aae311f135ca2bf8440f7f9bec4f90cce3, clean working tree at the
export run. Implementation commits bb8317a, 5f26ed5 and 571846a apply only to the
desktop app. Shared inspection/copy/budget APIs came from parent-owned commits
26e209f, c6f60a2 and e5ad25d. No protected runtime checkout, thread, model, device,
emulator or shared process was operated on.

The fixed native export journey passed **36 distinct assertions, 14 app-only PNGs
and four published exports**, including a real executable restart against the
same fresh synthetic SQLite workspace. Every publication passed exact inventory,
byte count and SHA256 verification; failed writes left no published partial export
or staging directory. The collision probe's preexisting empty target was retained.
The committed [evidence](D03_NATIVE_EVIDENCE_2026-10-22.json) records input hashes.
Local ignored artifact directory:
apps/desktop/artifacts/export-native-55a8b9b3-d671-4c9a-bb75-5749b2bd7502.
Its summary.json SHA256 is
360da5814f8425330fa65613d14a4aa63a067f02a47e6a0c924c718df14d631d.
Source hashes use exact local bytes; compare Git-normalized text when CRLF differs
between checkouts. The executable/frontend hashes bind the harness build, which
was followed by restoring and building the normal production configuration.

Coverage includes diagnostics excluding a private canary; renderer-supplied mode
and bytes failing to alter native captured data; Player export independent of a
later committed turn; explicit Full; delayed cancellation into Play; folder cancel;
unwritable, hostile parent, injected disk-full and target collision; stale preview
across story selection; private all-story consistent SQLite copy; untrusted local
folder reopening; inert hostile-looking story text; storage metadata; narrow
150% text layout; and process-restart reopening with unchanged canon.

Default native tests passed **10/10** (eight export regressions plus two window
lease regressions). Development native tests passed **12/12**, plus **2/2**
harness-wrapper tests. Native regression cases include immutable mode/bytes,
compact external manifest exact-byte retention and later edit rejection, bounded
abandoned-copy cleanup skipping active/foreign entries, pinned staging replacement
refusal, concurrent save/open lock ordering, cancellation/fault/collision cleanup,
and traversal/expiry/cache limits. Strict all-target Clippy passed with -D warnings
for both default and dev-harness configurations.

npm run check passed strict TypeScript, the Rust schema/action fixture checks,
hostile-wire/bounded-error checks, normal-asset hook absence, and actual-controller
regressions for delayed native cancellation, stale Full preview, and delayed
successful save acknowledgment across story attachment. Formatting passed for
frontend and Rust. The default native executable build and default tests passed
without launching the normal visible app. Normal local frontend assets and the
default executable were restored at the end.

The previous durable journey also passed **33 checks / 11 PNGs** at this source,
including same-workspace process restart and honest storage failure. Local ignored
artifacts: apps/desktop/artifacts/durable-native-2624a73d-f2d8-4e82-a0c0-fe74a0be58ee.

The complete legacy D02 controller journeys additionally passed in BOTH native
and headless modes: **163 assertions / 21 checkpoints each**, at clean source
571db8d (documentation-only after 571846a). Native artifacts:
apps/desktop/artifacts/native-67f9da17-0e30-49a5-894c-82f36d20a5e8; headless:
apps/desktop/artifacts/headless-8fe2c808-9551-42f3-af0a-e35dab02de08.
These include story switching, cancellation, late callbacks, close/reopen and
disposal sequencing affected by the export-presentation fence.

Visual review used this application's hidden native captures only. Final
export-narrow.png shows the feature warning, captured/current revision and file
table at 150% text with no horizontal overflow. export-open-readonly.png shows
literal hostile-looking text, not an injected element. Diagnostics, private DB
copy and storage captures label scope/privacy honestly. Synthetic captured JSON
and visible paths were redacted; normal product storage metadata shows actual
paths. Native WebView teardown emitted Chromium class-unregistration error1412
after successful shutdown; both process reports and exit codes were successful.

No desktop activation, desktop input, desktop capture, CUA, ADB or unrelated-app
automation was used. The native picker branch was compiled, while the harness
used trusted fixed synthetic folder choices. Real interactive picker UX, other
platforms, packaged installers and power-loss durability remain outside this gate.
