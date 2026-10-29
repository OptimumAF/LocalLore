// Independent context FIRST: SOURCE ONLY / UNCOMPILED / UNRUN at handoff.
// Actual SelectedEvaluationView + real React SSR. Its controller/subscription
// prop is an explicitly immutable FRONTEND STATE DOUBLE, NOT actual Controller.
// No private controller mutation, native grants/IPC, DOM/pixels or Core proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
const clone = (v) => structuredClone(v), h = (v) => v.repeat(64);
const RUN = "11111111-1111-1111-1111-111111111111", CLIENT = "22222222-2222-2222-2222-222222222222";
const TOKEN = "33333333-3333-3333-3333-333333333333", PLAN = "44444444-4444-4444-4444-444444444444";
const READER = "55555555-5555-5555-5555-555555555555";
const omni = { kind: "omniscient" }, player = { kind: "player" }, mira = { kind: "character", id: "mira-frame-observer" };
const scope = { story: "saved-frame-story", branch: "saved-frame-branch" };
const selection = { turn: "saved-frame-turn", clicked_arm: "right", index: 4 };
const candidate = { turn: "unrelated-reader-candidate", arm: "left" };
const source = { readerClientId: READER, runToken: TOKEN, binding: h("a") };
const RAW = "RAW_RECEIPT_PRIVATE_FRAME_CANARY_73", DIAG = "DIAGNOSTIC_PRIVATE_FRAME_ERROR_91";
const before = [7103, 8309], after = [7107, 8311], operation = 9203;
const v3Arms = [
    { arm: "literal_player_v1", prompt_version: "locallore-play-v2.6-literal-director-v1", narration_policy: "grounded-prose-v2.2", director_schema_id: "locallore-director-literal-v1", context_policy: null, compiler_version: null, context_version: null, literal_source_version: 1, literal_render_version: 1, literal_schema_version: 1, literal_packing_version: 1, forwarded_budget_version: 1 },
    { arm: "relevant_memory_v1", prompt_version: "locallore-play-v2.5", narration_policy: "grounded-prose-v2.2", director_schema_id: "locallore-director-v2", context_policy: "state_relevant_memory_v1", compiler_version: 2, context_version: 2, literal_source_version: null, literal_render_version: null, literal_schema_version: null, literal_packing_version: null, forwarded_budget_version: 1 },
];
const v4Arms = [
    { ...v3Arms[0], arm: "literal_scene_v1", prompt_version: "locallore-play-v2.10-literal-director-v1-scene-frame-v1", narration_policy: "grounded-prose-v2.4-scene-frame-v1", narrator_schema_id: "locallore-narrator-v2", scene_frame_version: 1, scene_capture_gate_version: 1 },
    { ...v3Arms[1], arm: "relevant_memory_scene_v1", prompt_version: "locallore-play-v2.9-scene-frame-v1", narration_policy: "grounded-prose-v2.4-scene-frame-v1", narrator_schema_id: "locallore-narrator-v2", scene_frame_version: 1, scene_capture_gate_version: 1 },
];
function tagged(version) { return version === 1 ? {} : { source_protocol_version: version + 1, constructions: clone(version === 3 ? v4Arms : v3Arms) }; }
function prepared(version = 3) {
    return { version, kind: "selected_prepared", binding: h("b"), lane: "scripted_selected_case", selection: clone(selection),
        arms: ["left", "right"].map((arm, i) => ({ arm, scope: clone(scope), before_head: before[i], prefix_sha256: h("d"), input_semantic_sha256: h("e") })),
        ...(version === 3 ? { source_binding: source.binding } : {}), ...tagged(version) };
}
function summary(version = 3) {
    return { version, kind: "selected_read", binding: h("c"), lane: "scripted_selected_case", selection: clone(selection),
        arms: ["left", "right"].map((arm, i) => ({ arm, scope: clone(scope), before_head: before[i], after_head: after[i], available: true })),
        read_only: true, execution_available: false, ...tagged(version) };
}
function status(phase = "completed", metadata = null) {
    return { version: 1, kind: "selected_evaluation", client_id: CLIENT, operation_id: operation, phase,
        running: ["preparing", "running", "cancelling"].includes(phase), lane: "scripted_baseline", plan_token: phase === "prepared" ? PLAN : null,
        run_id: phase === "prepared" ? null : RUN, run_token: phase === "completed" || phase === "paused" ? TOKEN : null,
        binding: phase === "completed" || phase === "paused" ? h("c") : null, prepared: metadata,
        error: null, cause: null, cleanup_required: false };
}
function evidence(kind = "receipt", observer = omni) {
    const body = kind === "receipt" ? { kind: "receipt", receipt: { synthetic_private_canary: RAW } }
        : kind === "missing" ? { kind: "missing", reason: "no_accepted_receipt" }
        : { kind: "query", page: { version: 2, scope: clone(scope), head: after[0], revision: after[0], story_time: 17, observer: clone(observer), view: "knowledge", privacy: observer.kind === "player" ? "player_visible" : observer.kind === "character" ? "private_character" : "private_omniscient", status: "supported", total: 0, rows: [], next_cursor: null, unsupported: [] } };
    return { version: 1, binding: h("c"), row: { turn: selection.turn, arm: "left" }, scope: clone(scope), before_head: before[0], after_head: after[0], observer: clone(observer), edge: "after", read_only: true, generation_grant: false, body };
}
function row(version = 3, arm = "left", error = "AbilityUnavailable") {
    const i = arm === "left" ? 0 : 1;
    const common = { turn: selection.turn, arm, phase: "failed", error, expected: "GuardRejected(AbilityUnavailable)", passed: true, failures: [], quality_flags: [], roles: 0, roles_known: true, elapsed_ms: 0, actual_receipt_sha256: null };
    if (version === 3) return { ...common, construction: clone(v4Arms[i]), construction_evidence_status: "not_applicable_guard", construction_evidence_reason: null, construction_matches: true,
        privacy_evidence_status: "not_applicable_guard", fallback: null, repairs: null, recovered_without_checkpoint: false,
        first_final_response_ms: null, commit_elapsed_ms: null, narrator_prompt_sha256: null, narrator_schema_sha256: null, scene_frame_sha256: null };
    return { ...common, privacy_passed: false, context_evidence_available: false, ...(version === 2 ? { construction: clone(v3Arms[i]), construction_evidence_status: "not_applicable_guard", construction_matches: true, literal_source_units: null, literal_selected_start: null, literal_selected_units: null, fallback: null } : {}) };
}
function diagnostics(version = 3, rows = [row(version)]) {
    return { version, kind: "selected_diagnostics", binding: h("c"), lane: "scripted_selected_case", completed: true, rows,
        physical_setups: 0, physical_setup_ms: null, left_charged_ms: 0, right_charged_ms: 0, left_reserved_roles: 0, right_reserved_roles: 0,
        human_reviewed: 0, ...(version === 3 ? { human_rubric: "not_reviewed" } : {}), quality_accepted: false, unavailable: ["scripted_lane_no_native_setup_measurement"], ...tagged(version) };
}
function state(patch = {}) {
    return { context: "synthetic-view-context", allowed: true, observer: clone(omni), clientId: null, status: null, catalog: null,
        summary: null, evidence: null, diagnostics: null, cleanup: null, pending: null, busy: false, uncertain: false, error: null, ...patch };
}
function freeze(value) { if (value !== null && typeof value === "object") { for (const item of Object.values(value)) freeze(item); Object.freeze(value); } return value; }
function publicationDouble(initial) {
    let published = freeze(clone(initial));
    const calls = [], listeners = new Set();
    const controller = { get: () => published, subscribe: (listener) => { listeners.add(listener); return () => listeners.delete(listener); }, sourceNeedsRefresh: () => false };
    for (const name of ["setObserver", "prepare", "start", "status", "cancel", "close", "catalog", "open", "resume", "loadSummary", "readEvidence", "readDiagnostics", "cleanupStatus", "retryCleanup"]) controller[name] = (...args) => { calls.push({ name, args }); return Promise.resolve(); };
    return { controller, calls, publish: (next) => { published = freeze(clone(next)); for (const listener of [...listeners]) listener(); } };
}

// A finite token reader over real React SSR output, NOT a browser DOM or an
// accessibility parser. It locates semantic groups by class/aria and ancestry,
// allowing ordinary tag/whitespace/layout changes. No CSS/pixel assertion here.
function entities(value) { return value.replace(/&(?:amp|lt|gt|quot|apos|nbsp|#x27|#39);/g, (v) => ({ "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&apos;": "'", "&nbsp;": " ", "&#x27;": "'", "&#39;": "'" })[v]); }
const normalized = (value) => entities(value).replaceAll("_", " ").replace(/\s+/g, " ").trim();
function structure(html) {
    const nodes = [], stack = [], voids = new Set(["area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"]);
    for (const token of html.matchAll(/<!--[\s\S]*?-->|<\/?[A-Za-z][^>]*>|[^<]+/g)) {
        const value = token[0]; if (value.startsWith("<!--")) continue;
        if (!value.startsWith("<")) { for (const node of stack) node.text += `${entities(value)} `; continue; }
        const match = /^<(\/?)([A-Za-z][\w:-]*)([^>]*)>$/.exec(value); if (!match) continue;
        const tag = match[2].toLowerCase();
        if (match[1]) { const index = stack.map((v) => v.tag).lastIndexOf(tag); if (index >= 0) { for (const node of stack.splice(index)) node.end = token.index + value.length; } continue; }
        const attrs = {};
        for (const attr of match[3].matchAll(/([\w:-]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+)))?/g)) attrs[attr[1]] = entities(attr[2] ?? attr[3] ?? attr[4] ?? "");
        const node = { tag, attrs, text: "", start: token.index, end: token.index + value.length, parent: stack.at(-1) ?? null, children: [] };
        if (node.parent) node.parent.children.push(node); nodes.push(node);
        if (!voids.has(tag) && !value.endsWith("/>")) stack.push(node);
    }
    assert.equal(stack.length, 0, "BalancedReactSsrStructureRequired");
    for (const node of nodes) node.text = normalized(node.text);
    const frames = nodes.filter((v) => /(?:^|\s)selected-attempt-context(?:\s|$)/.test(v.attrs.class ?? ""));
    for (const frame of frames) assert.equal(frame.attrs["aria-label"], "Selected attempt context");
    return { nodes, frames, html };
}
function adjacent(frame, artifact) {
    if (frame.start >= artifact.start && frame.end <= artifact.end) return true;
    if (!frame.parent || frame.parent !== artifact.parent) return false;
    const siblings = frame.parent.children; return Math.abs(siblings.indexOf(frame) - siblings.indexOf(artifact)) === 1;
}
function localFrame(rendered, label, expected = []) {
    const artifact = rendered.nodes.find((v) => v.attrs["aria-label"] === label); assert(artifact, `ActualArtifact:${label}`);
    const frame = rendered.frames.find((v) => adjacent(v, artifact) && expected.every((s) => v.text.includes(normalized(s))));
    assert(frame, `LocalSemanticFrame:${label}:${expected.join("/")}`); return frame;
}
function has(frame, ...values) { for (const value of values) assert(frame.text.toLowerCase().includes(normalized(String(value)).toLowerCase()), `FrameMissing:${value}:${frame.text}`); }
function currentObserver(frame, observer) {
    const value = observer.kind === "character" ? observer.id : observer.kind;
    assert.match(frame.text, /observer/i); has(frame, value);
}
function receiptState(frame, displayed) {
    const match = /(?:raw\s+)?receipt(?:\s+display(?:ed)?(?:\s+state)?)?/i.exec(frame.text); assert(match, `ReceiptDisplayLabel:${frame.text}`);
    let part = frame.text.slice(match.index, match.index + 150);
    const tail = part.slice(match[0].length), next = /\b(?:visible\s+error|error|pending|operation|workflow|observer|story|branch|selection|before|after)\b/i.exec(tail);
    if (next) part = part.slice(0, match[0].length + next.index);
    const negative = /\bnot\s+(?:displayed|shown)\b|\bnone\b|\bunavailable\b|\bno\b/i.test(part);
    if (displayed) { assert.match(part, /displayed|shown|yes/i); assert.equal(negative, false, `ReceiptActuallyDisplayed:${part}`); }
    else assert.equal(negative, true, `NoRawReceiptDisplayed:${part}`);
}

async function main() {
    assert(path.isAbsolute(output), "AbsoluteContextOutputRequired"); await mkdir(output, { recursive: true });
    const prefix = `selected-scene-context-first-${randomUUID()}`;
    const files = ["check-selected-scene-context-review.mjs", "ui/selected-evaluation-view.tsx", "ui/selected-evaluation-model.ts", "ui/style.css"];
    const sourceHashes = Object.fromEntries(await Promise.all(files.map(async (name) => [name, createHash("sha256").update(await readFile(path.join(root, name))).digest("hex")])));
    const checks = [], html = []; let m;
    async function report(setupError = null) {
        for (let i = 0; i < html.length; i++) await writeFile(path.join(output, `${prefix}-${i}.html`), html[i], { flag: "wx" });
        const result = { version: 1, kind: "selected_scene_context_first", sourceHashes, setup: setupError === null ? "ready" : "SETUP_UNRUN", setupError,
            checks: checks.length, passed: checks.filter((v) => v.passed).length, failed: checks.filter((v) => !v.passed).length, staticHtml: html.length, cases: checks,
            evidence: "Actual SelectedEvaluationView/React SSR with a frozen caller-owned frontend-state/controller-subscription DOUBLE. Not actual Controller/native/DOM/pixels.",
            limits: ["The source snapshots are synthetic typed presentation values, not Rust fixtures/receipts/grants.", "Effects/subscriptions do not run as client React during SSR; actor-prop-before-effect fences are observed directly.", "Minimal SSR token reader checks group values/structural vicinity, not browser layout/accessibility/focus or visual adjacency.", "No controller private-state mutation, actions/native calls, canonical mutation or quality acceptance is proven.", "Actual native geometry, images and observer isolation remain separately owned checks."] };
        await writeFile(path.join(output, `${prefix}.json`), JSON.stringify(result, null, 2), { flag: "wx" }); console.log(JSON.stringify(result));
        if (setupError !== null || result.failed || result.checks === 0) process.exitCode = 1;
    }
    try {
        const built = await build({ stdin: { contents: 'export {SelectedEvaluationView} from "./ui/selected-evaluation-view";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";', resolveDir: root, loader: "tsx" }, bundle: true, platform: "node", format: "cjs", jsx: "automatic", write: false, define: { __DEV_HARNESS__: "false" } });
        assert.equal(built.outputFiles.length, 1); const bundle = path.join(output, `${prefix}.cjs`); await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
        m = (await import(pathToFileURL(bundle).href)).default; assert.equal(typeof m.SelectedEvaluationView, "function");
    } catch (error) { await report(String(error?.message ?? error).slice(0, 900)); return; }
    function render(snapshot, props = {}) {
        const double = publicationDouble(snapshot), published = double.controller.get(), beforeJson = JSON.stringify(published);
        const text = m.renderToStaticMarkup(m.createElement(m.SelectedEvaluationView, { controller: double.controller, source, row: candidate, observer: omni, sourceProtocolVersion: 4, ...props }));
        assert.equal(JSON.stringify(published), beforeJson, "SsrDoesNotMutatePublishedDouble"); assert.equal(double.calls.length, 0, "NoActionFromContextRendering");
        html.push(text); const parsed = structure(text); assert(parsed.frames.length > 0, "RealProductContextGroupRequired");
        for (const frame of parsed.frames) {
            assert.equal(frame.text.includes(normalized(RAW)), false, "ContextDoesNotCopyRawReceiptBody");
            assert.doesNotMatch(frame.text, /quality\s*(?:acceptance\s*)?[:=]?\s*(?:accepted|passed)/i);
            assert(parsed.nodes.some((node) => node.start >= frame.start && node.end <= frame.end && /^(?:h[1-6]|strong)$/.test(node.tag) && /selected\s+attempt/i.test(node.text)), "VisibleSelectedAttemptHeading");
        }
        return parsed;
    }
    async function check(name, body) { try { await body(); checks.push({ name, passed: true }); } catch (error) { checks.push({ name, passed: false, error: String(error?.message ?? error).slice(0, 600) }); } }
    await check("idle: real context uses unavailable scope/heads and no invented receipt or acknowledged selection", () => {
        const value = render(state(), { source: null, row: null }); const frame = value.frames[0];
        currentObserver(frame, omni); assert.match(frame.text, /unavailable/i); assert.match(frame.text, /story|scope/i); assert.match(frame.text, /branch/i);
        assert.match(frame.text, /(?:visible\s+)?error\s*[:·-]?\s*unavailable/i, "NoAcknowledgementHasNoKnownErrorState");
        receiptState(frame, false); assert(!frame.text.includes(scope.story)); assert(!frame.text.includes(selection.turn));
    });
    await check("candidate only: reader row is optional and must be explicitly distinguished from an acknowledged attempt", () => {
        const value = render(state()); assert.match(value.frames[0].text, /unavailable/i);
        for (const frame of value.frames.filter((v) => v.text.includes(candidate.turn))) assert.match(frame.text, /candidate\s+source|current\s+reader\s+selection/i);
        for (const frame of value.frames) { assert(!frame.text.includes(scope.story)); receiptState(frame, false); }
    });
    await check("pending no ACK/metadata: current pending action cannot borrow candidate scope/heads or an operation ID", () => {
        const value = render(state({ clientId: CLIENT, busy: true, pending: { action: "prepare", clientId: CLIENT, operationId: null } }));
        const frame = value.frames.find((v) => /pending/i.test(v.text) && /prepare/i.test(v.text)); assert(frame); assert.match(frame.text, /unknown|unavailable/i);
        assert.match(frame.text, /(?:visible\s+)?error\s*[:·-]?\s*unavailable/i);
        assert(!frame.text.includes(String(operation))); assert(!frame.text.includes(scope.story)); receiptState(frame, false);
        if (frame.text.includes(candidate.turn)) assert.match(frame.text, /candidate\s+source|current\s+reader\s+selection/i);
    });
    for (const version of [1, 2, 3]) await check(`prepared${version}: local frame keeps saved turn/arm/scope/before, unavailable after and current workflow`, () => {
        const value = render(state({ clientId: CLIENT, status: status("prepared", prepared(version)) }), { sourceProtocolVersion: version + 1 });
        assert(value.frames.length >= 2, "WorkflowAndPreparedLocalFrames"); const frame = localFrame(value, "Prepared experiment identity", [selection.turn, scope.story, scope.branch]);
        has(frame, selection.clicked_arm, before[0], before[1], operation); currentObserver(frame, omni); assert.match(frame.text, /prepared/i); assert.match(frame.text, /unavailable/i); receiptState(frame, false);
        assert.match(frame.text, /(?:visible\s+)?error\s*[:·-]?\s*none/i, "AcknowledgedNullErrorIsNone");
        assert(value.frames.every((v) => !v.text.includes(candidate.turn)), "SavedAttemptNeverRelabeledFromNewReaderRow");
    });
    await check("summary: local frame uses actual before/after revisions with no receipt-display inference from completed workflow", () => {
        const value = render(state({ clientId: CLIENT, status: status(), summary: summary() }));
        const frame = localFrame(value, "Selected experiment summary", [selection.turn, scope.story, scope.branch]);
        has(frame, before[0], before[1], after[0], after[1], operation); currentObserver(frame, omni); assert.match(frame.text, /completed/i); receiptState(frame, false);
        assert(value.frames.every((v) => !v.text.includes(candidate.turn)));
    });
    await check("evidence receipt: local context says displayed only when the actual fenced raw receipt body is visible", () => {
        const value = render(state({ clientId: CLIENT, status: status(), summary: summary(), evidence: evidence() }));
        const frame = localFrame(value, "Displayed selected evidence", [selection.turn, "left", scope.story, scope.branch]);
        has(frame, before[0], after[0], operation); currentObserver(frame, omni); receiptState(frame, true); assert(value.html.includes(RAW));
    });
    await check("evidence missing receipt: absence is explicit and does not become displayed from completed state", () => {
        const value = render(state({ clientId: CLIENT, status: status(), summary: summary(), evidence: evidence("missing") }));
        const frame = localFrame(value, "Displayed selected evidence", [selection.turn, scope.story]); receiptState(frame, false); assert(!value.html.includes(RAW));
    });
    for (const observer of [player, mira]) await check(`query ${observer.kind}: local frame uses current permitted lens with no raw receipt displayed`, () => {
        const value = render(state({ observer, clientId: CLIENT, status: status(), summary: summary(), evidence: evidence("query", observer) }), { observer });
        const frame = localFrame(value, "Displayed selected evidence", [selection.turn, scope.story]); currentObserver(frame, observer); receiptState(frame, false);
        assert(!value.html.includes(RAW));
    });
    await check("pending start without new ACK: metadata stays prepared while pending operation remains unavailable", () => {
        const value = render(state({ clientId: CLIENT, status: status("prepared", prepared()), busy: true, pending: { action: "start", clientId: CLIENT, operationId: null } }));
        const frame = value.frames.find((v) => /pending/i.test(v.text) && /start/i.test(v.text)); assert(frame); has(frame, selection.turn, scope.story);
        assert.match(frame.text, /prepared/i); assert.match(frame.text, /unknown|unavailable/i); receiptState(frame, false);
    });
    await check("known pending read: frame shows actual pending action/operation without changing saved selection", () => {
        const value = render(state({ clientId: CLIENT, status: status("paused"), summary: summary(), busy: true, pending: { action: "evidence", clientId: CLIENT, operationId: operation } }));
        const frame = value.frames.find((v) => /pending/i.test(v.text) && /evidence/i.test(v.text)); assert(frame); has(frame, operation, selection.turn); assert.match(frame.text, /paused/i); receiptState(frame, false);
    });
    await check("workflow refusal: finite visible error is local context, with unavailable selected story when metadata never arrived", () => {
        const failed = status("failed"); Object.assign(failed, { run_id: null, error: "NativeUnavailable" });
        const value = render(state({ clientId: CLIENT, status: failed, error: "NativeUnavailable" }));
        const frame = value.frames.find((v) => v.text.includes("NativeUnavailable")); assert(frame); assert.match(frame.text, /failed/i); assert.match(frame.text, /unavailable/i); has(frame, operation);
        assert(!frame.text.includes(scope.story)); receiptState(frame, false);
    });
    await check("diagnostic row: completed workflow and failed guard/row error remain separate, not quality acceptance or receipt display", () => {
        const meta = summary(); meta.arms[0].after_head = before[0];
        const value = render(state({ clientId: CLIENT, status: status(), summary: meta, diagnostics: diagnostics() }));
        const parent = value.nodes.find((v) => v.attrs["aria-label"] === "Selected expected and actual results"); assert(parent);
        const frame = value.frames.find((v) => v.start >= parent.start && v.end <= parent.end && v.text.includes("AbilityUnavailable")); assert(frame);
        has(frame, selection.turn, "left", scope.story, scope.branch); currentObserver(frame, omni);
        assert.match(frame.text, /workflow(?:\s+phase)?\s*[:·-]?\s*completed/i); assert.match(frame.text, /(?:row|actual)(?:\s+phase)?\s*[:·-]?\s*failed/i);
        assert.match(frame.text, /(?:row|actual)(?:\s+error)?\s*[:·-]?\s*AbilityUnavailable/i); receiptState(frame, false);
    });
    await check("two diagnostic rows: each frame has its own row error/arm rather than reusing the other row", () => {
        const rows = [row(3, "left", "LEFT_ROW_ERROR_51"), row(3, "right", "RIGHT_ROW_ERROR_61")];
        const value = render(state({ clientId: CLIENT, status: status(), summary: summary(), diagnostics: diagnostics(3, rows) }));
        const a = value.frames.find((v) => v.text.includes(normalized(rows[0].error))), b = value.frames.find((v) => v.text.includes(normalized(rows[1].error)));
        assert(a && b && a !== b); has(a, "left"); has(b, "right"); assert(!a.text.includes(normalized(rows[1].error))); assert(!b.text.includes(normalized(rows[0].error)));
    });
    for (const payload of ["receipt", "diagnostics", "both"]) for (const observer of [player, mira]) await check(`actor-prop-before-effects ${observer.kind}/${payload}: private body and diagnostic context are fenced`, () => {
        const value = render(state({ clientId: CLIENT, status: status(), summary: summary(),
            evidence: payload === "diagnostics" ? null : evidence(), diagnostics: payload === "receipt" ? null : diagnostics(3, [row(3, "left", DIAG)]) }), { observer });
        assert(!value.html.includes(RAW)); assert(!normalized(value.html).includes(normalized(DIAG)));
        for (const frame of value.frames) { currentObserver(frame, observer); receiptState(frame, false); }
        assert(!value.nodes.some((v) => v.attrs["aria-label"] === "Displayed selected evidence" || v.attrs["aria-label"] === "Selected expected and actual results"));
    });
    await check("lost Lab access: stale retained private values do not leak through new context groups", () => {
        const value = render(state({ allowed: false, clientId: CLIENT, status: status(), summary: summary(), evidence: evidence(), diagnostics: diagnostics(3, [row(3, "left", DIAG)]) }));
        assert(!value.html.includes(RAW)); assert(!normalized(value.html).includes(normalized(DIAG))); for (const frame of value.frames) receiptState(frame, false);
    });
    await check("escaped diagnostic error stays inert text in its own context", () => {
        const marker = "FRAME_ROW_<script>unsafe()</script>";
        const value = render(state({ clientId: CLIENT, status: status(), summary: summary(), diagnostics: diagnostics(3, [row(3, "left", marker)]) }));
        const frame = value.frames.find((v) => v.text.includes(normalized(marker))); assert(frame); assert(!value.nodes.some((v) => v.tag === "script"));
    });
    await check("immutable subscription double publishes a new snapshot; actual View context cannot retain the previous artifact", () => {
        const double = publicationDouble(state({ clientId: CLIENT, status: status("prepared", prepared()) }));
        const first = m.renderToStaticMarkup(m.createElement(m.SelectedEvaluationView, { controller: double.controller, source, row: candidate, observer: omni, sourceProtocolVersion: 4 })); html.push(first);
        double.publish(state());
        const second = m.renderToStaticMarkup(m.createElement(m.SelectedEvaluationView, { controller: double.controller, source: null, row: null, observer: player, sourceProtocolVersion: 4 })); html.push(second);
        const frames = structure(second).frames; assert(frames.length > 0); assert(frames.every((v) => !v.text.includes(selection.turn) && !v.text.includes(scope.story)));
        for (const frame of frames) currentObserver(frame, player); assert.equal(double.calls.length, 0);
    });
    await report();
}
await main();
