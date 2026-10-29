# Protocol4 frontend reader decoder freeze

Date: 2026-10-27. Task D07.06, supporting D04.04 (#29/#25).
Source base: `98d80d9e82cf9929bab1ffd20440cc7fa48eebcd`.
Independent branch: `test/d07-v4-reader-frontend` in the released isolated
`source-d07-main-native-review` checkout.

This is a **SOURCE-ONLY, UNRUN** first oracle freeze. It implements no production
decoder, native handler, panel, runtime or selected-case seam. The existing
public decoder functions are present, so Root can execute the unchanged baseline
before implementation. No behavioral RED/GREEN or compilation result is claimed
at this author handoff. The four Core reader checks reported by Root are a
separate evidence class; this document does not rerun or extend their claims.

## Frozen public surfaces and transport contract

The new `apps/desktop/check-scene-reader-review.mjs` bundles only the actual
`ui/comparison-reader-model.ts` and calls existing public functions:

- `checkedReaderSource(wrapper, token, binding)`.
- `checkedReaderSummary(wrapper, token, binding)`.
- `checkedReaderEvidence(wrapper, token, source, selectedRow, request)`.
- `sameReaderSource` for the existing source-identity comparison.

No new production API, injected fault hook, Engine/Receipt constructor or
provider is required. Fixtures are explicitly synthetic JavaScript DTOs.
Opaque synthetic receipt/capture bodies test transport copying only. They are
not accepted Rust objects, genuine native evidence or model-origin attestations.
The decoder validates bounded closed wire metadata; Rust remains the canonical
state, observer filtering, source validation and execution authority.

Retain valid Protocol2/3 decoding. Protocol4 must be a distinct source/report/row
variant, not V3 with synthetic retrieval/literal metrics. The two independently
written descriptor expectations have all15 required native fields:
arm, prompt_version, narration_policy, director_schema_id, narrator_schema_id,
context_policy, compiler_version, context_version, literal_source_version,
literal_render_version, literal_schema_version, literal_packing_version,
forwarded_budget_version, scene_frame_version and scene_capture_gate_version.
Literal uses prompt2.10 and Relevant memory prompt2.9 with the exact scene-frame
suffixes and grounded-prose2.4-scene-frame-v1. Each descriptor's nullable
context/compiler/literal fields must be explicitly present; self-consistently
changing both report and row to a different tuple does not make it supported.

Carry the actual closed V4 report and row shape from
`crates/locallore-eval/src/memory_comparison_v4.rs` losslessly. In particular,
retain required nullable reason, narrator prompt/schema/frame and actual receipt
hashes, retained capture/recording hashes, timing/repair/fallback fields and
opaque role/trace/stage diagnostics. Preserve required null versus an absent
property. Report source/suite/reference/profile identities, exact descriptor
order, `source_bound_committed_rows`, setup/load fields and limitations remain
metadata. This frontend does not regenerate hashes, evaluate provenance or
recompute a source-bound/privacy count into engine authority.

Construction status is the closed set
`validated_committed_scene_narrator_v1`, `not_applicable_guard`,
`not_applicable_dependency`, `unavailable`; privacy status is
`checked_finite_sentinels`, `not_applicable_guard`, `unavailable`.
Status and failure cause must be retained independently. In particular,
`observer_or_output_privacy_violation` and
`observer_or_output_privacy_evidence_unavailable` remain different causes even
when both public statuses are unavailable. No receipt or missing evidence earns
a finite privacy PASS. Decoding a diagnostic label does not authenticate a
provider, raw output, Director/compiler execution or general semantic privacy.

The source4 and report4 discriminants must agree. Exact report/row descriptors,
physical arms, normalized row order/identity and input fingerprints must agree.
The existing bounded descriptor-first copy must reject accessors without calling
them, prototypes, cycles, unsafe numbers, unknown closed fields and over-budget
sources/summaries. Opaque JSON diagnostics remain data rather than a new closed
execution schema. Do not reject an otherwise valid historical read merely
because `source_matches` is false.

Every source remains read_only=true and execution_available=false. The summary
retains `selected_protocol4_rerun_not_implemented`. No new selected4 execution,
provider configuration or admission is inferred from accepted transport metadata.
The frozen positive packet retains human_reviewed0, not_reviewed and qualityfalse,
including the original eight-sample needs-improvement limitation. Tests do not
invent a new human rubric or a frontend quality decision.

## Finite independent cases

The checker covers:

- Lossless old2/3 source/summary controls and distinct lossless4, including
  explicit read-only/unavailable rerun, source mismatch and human-quality limits.
- Detachment without dropping opaque diagnostics; exact physical descriptors,
  every descriptor field's presence and unsupported self-consistent mutations.
- Descriptor/order/row/fingerprint/version mismatches; required nullable row and
  report fields; all new hash fields; refusal of inherited legacy row metrics.
- Allowed construction/privacy statuses, noncommitted/recovered cause
  distinctions, unknown statuses, future closed fields and unsafe numbers.
- Descriptor-first getters/prototypes/cycles and existing source/summary caps.
- Both Query2 edges with synthetic empty Player pages, exact observer/scope/head/
  binding checks, Omniscient opaque receipt/capture/output transport and early
  actor raw refusal without reading an evidence getter.
- Foreign evidence identity/observer/edge/revision/grant, exact missing-receipt
  availability reasons, raw evidence budget and token binding.

Negative unsupported4 cases can pass on a baseline which rejects all4 inputs.
They qualify refusal behavior only together with the positive4 controls. The
unchanged checker records all individual failures, exits nonzero on any failure
and marks its result decoder_only/synthetic_dto, with Rust/Store, native IPC,
WebView, rendered UI and model execution false. A baseline lacking4 support is
an executable feature gap, not permission to weaken any positive or negative
oracle. Root owns interpretation of actual baseline and later results.

Existing `check-literal-comparison-reader.mjs` currently calls protocol4 the
unknown future protocol. Once support4 is added, that historical sentinel must
be explicitly advanced to5, preserving its existing strict-future intent and
prior evidence. This freeze does not edit that checker or any production file.

## Reproduction, ownership and remaining gates

After integrating this frozen source, Root can run from `apps/desktop`:

```powershell
node check-scene-reader-review.mjs
```

The existing esbuild dependency is reused without changes. The checker creates
only unique create-new bundle and result JSON files under existing gitignored
`apps/desktop/artifacts/checks` by default, or the existing explicit
LOCALLORE_CHECK_OUTPUT_DIR convention. It does not launch an application, native
helper, browser or model, and has no arbitrary execution endpoint.

The author ran no Node/esbuild/compiler/formatter/Cargo/test, native application,
model, device, desktop or protected-resource operation. Author checks are source/
API/fixture inspection, diff/whitespace and commit/hash inspection only. Root
owns the first baseline, production decoder implementation and unchanged rerun.

Controller scheduling, native grant/lease/close/transfer lifecycle, actual Store
or Query2 isolation, actual IPC/WebView and panel layout are not qualified here.
No render files are produced by this decoder-only checker. Those require their
own existing-controller application journeys and inspected application-owned
renders, with evidence classes kept separate. Selected3/source4 execution and
new model/human quality qualification remain separate later gates. The original
human needs-improvement assessment is unchanged.

## Supplemental R3 selected-artifact framing freeze

Frozen independently from `2e2e74fc`, before the later
`ComparisonReaderPanel.tsx` artifact framing production change. Refs #29
D07.03/.05/.06. The original174 decoder cases remain unchanged. Two appended
headless behavioral cases use a separately built actual public
`ComparisonReaderController` and `ComparisonReaderPanel`, existing React static
HTML rendering and closed synthetic native4 reader metadata. This supplemental
source is **UNRUN** by its author; no current headless/native outcome is claimed.

The fixture calls public `contextChanged`, `pickManaged`, `setObserver`,
`loadSummary`, `select`, `inspect` and `close`. It does not substitute controller
state, add a native field, compute engine state or authenticate a receipt/raw
body. Admission uses existing native managed entry; follow-ups use existing
ReaderV1 source/summary/evidence/close with their exact current query keys. The
fixture validates closed source/report/selected metadata and reads receipt or
the exact no-receipt reason before displaying a synthetic Director output.
The panel's `selected`/`turn` closures and public renderer are exercised through
these real APIs. Every fixture closes/disposes in `finally`.

The oracles are:

1. For a failed selected native4 row with `UnknownReference`, retained raw output
   and no accepted receipt, the actual `.comparison-evidence` container must
   identify the selected row/arm and inspection observer, its failed phase and
   error, and absent accepted receipt **before its raw `<pre>` body**. A ready
   read-only report and available raw artifact must not make the failed row
   appear accepted. Labels earlier elsewhere in the report do not satisfy this
   artifact-local framing oracle.
2. For a committed selected native4 row, that same artifact-local prefix must
   identify the selected source story/branch, observer, before4/after5 cut,
   committed phase and available accepted receipt. Human/prose quality must
   remain explicitly unreviewed/not established, with no positive
   prose/narration/quality-accepted claim. The same independent case exercises
   both recorded `fallback:true` and `fallback:false`; neither value nor a
   commit establishes acceptance of generated prose. Existing report human
   fields remain0 / not_reviewed / qualityfalse.

The raw body is a public synthetic marker, not copied prose or private captured
material. Native-lane DTOs are transport fixtures only; zero actual engine,
model, Store or native runtime operations are executed by them. There is no
frontend reconstruction of an accepted canonical state. The two new cases are
separately categorized; bundling/API/fixture/source-attribution/close failures
are explicit setup failures and cannot establish the intended behavioral RED.
The result retains original decoder case count plus supplemental cases/source
hashes and marks its new static-HTML evidence explicitly. It no longer describes
the entire checker as decoder-only. HTML files remain bounded, create-new and
local/gitignored under the existing output convention.

Root must first measure the proposed176-case checker and retain actual baseline
failures before changing the panel, then rerun these unchanged oracles after
the display fix. This scope verifies text order and membership in the actual
artifact container; static HTML does **not** prove viewport placement, native
WebView rendering, mounted interactions or layout. Those remain separately
qualified by app-owned captures and individual inspection. Author activity was
limited to source/API/fixture/diff inspection and commit preparation: no Node,
formatter, Cargo, app, asset/model, device or desktop action. Existing actual
cohort captures stay frozen; the original human needs-improvement assessment,
pending human review, canonical authority and acceptance gates remain unchanged.

## Supplemental R3 visible artifact geometry freeze

Frozen independently from `c3c13a2b`, before the CSS change. Refs #29 D07.06.
This adds one closed optional `--artifact-geometry-v1` group to the existing
checker and preserves its default176 cases. It asserts visible geometry and
hit-testing, **not CSS rule text, a selector implementation, or a required
`position` value**. The source author ran no Node/browser/formatter/Cargo/app,
asset/model, profile/link probe, phone or desktop operation. This is an
**UNRUN source freeze**; Root owns its first actual baseline and unchanged rerun.

The existing package pins Playwright1.64.1 and the application-owned headless
harness already uses Chromium. Root separately verified its installed browser
prerequisites. The new group reuses the existing actual public controller
fixture and real `ComparisonReaderPanel` React static markup, plus the complete
current `ui/style.css`. It never launches the full Rust/stdio/native harness,
starts a server, downloads a browser, connects to a user's browser or controls
the desktop. A single newly launched persistent **headless** context gets a
fresh UUID output/profile on physical D:. TEMP/TMP are set inside its actual
Node process; inherited output redirection outside ordinary D: ancestry is
refused before directory creation. Every page network request is aborted.

One failed native4 transport row with actual selected metadata, retained raw
body and no accepted receipt is reused. After the same
`.comparison-evidence.scrollIntoView({block:'start'})` action at1280x900 and
620x900, the actual evidence heading, source paragraph and case-phase/error
paragraph must fit in the viewport. Top/middle/bottom point samples must hit
their respective target elements or descendants. A sticky header painted over
even the upper part of a phase line therefore fails, while labels elsewhere in
the DOM cannot satisfy the check. The measured header positions are diagnostic,
not expected CSS strings. Existing R3 semantic receipt/source/quality checks
remain independent and unchanged.

A fixture-only inert, aria-hidden900px scroll tail follows the actual Panel.
It supplies one viewport of scroll range without overriding product CSS or
changing the Panel. The artifact's actual bounding-box top must be within1px
of the requested viewport start before any behavioral classification; missing
scroll range is a setup/calibration failure, never a behavioral GREEN. The
selection-only control likewise requires measured scrolling before checking
its retained context. These synthetic fixture conditions do not establish the
document geometry of the complete native app.

Two controls prevent a blanket loss of context/privacy: after public
`clearEvidence`, selected context must remain visible while scrolling at both
widths; after public `setObserver({kind:'character',id:'mira'})`, summary/evidence
must clear and the narrow view must expose neither private phase/error nor raw
body. No controller-state stub, new authorization field or engine reconstruction
is introduced. Five observations belong to one optional geometry case, making
the proposed optional run177 cases only when setup succeeds. Setup failures are
separate from a meaningful behavioral RED.

The local result records actual selected browser executable and version, CSS
and component/checker source hashes, bounded measurements, network/page errors
and local viewport PNG hashes. Its explicit rendering class is headless
Chromium, never native WebView2. No native rendering, actual model generation,
canonical correctness, OS accessibility, runtime/Job/descendant cleanup or
human-quality result follows from this group. Source fixtures contain only
public synthetic markers; original native captures and raw outputs stay frozen.

Root can later run from physical D: `apps/desktop`, after source review and
with the existing installed browser:

```powershell
$env:TEMP='D:/Dev/_Temp'
$env:TMP=$env:TEMP
node check-scene-reader-review.mjs --artifact-geometry-v1
```

No install/download fallback exists. Bundle/browser/fixture/timeouts/cleanup
failures remain setup failures with failed local evidence. Execution is bounded
by a60s geometry deadline plus one10s close allowance. No second browser is
admitted after a launch/close uncertainty; `browserDrainUnknown` cannot qualify
success and Root must resolve ownership before starting later app work. This is
not a claim that simulated bounds prove actual browser process-tree cleanup.
Root will measure baseline first, apply the narrow production CSS change and
repeat unchanged headless checks, then separately require actual native
bounding-box checks and inspect every new application-owned render. Core work
and quality/acceptance gates remain pending until that UI gate is handled.
