// Actual evaluation controller + inert React SSR; failure row is an explicit mock, no native runner claim.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";
const root = fileURLToPath(new URL(".", import.meta.url)),
    output =
        process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
        path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const file = path.join(output, `evaluation-${randomUUID()}.cjs`);
const built = await build({
    stdin: {
        contents:
            'export {EvaluationController} from "./ui/evaluation-controller";export {EvaluationPanel} from "./ui/EvaluationPanel";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
await writeFile(file, built.outputFiles[0].contents);
const {
    EvaluationController,
    EvaluationPanel,
    createElement,
    renderToStaticMarkup,
} = (await import(pathToFileURL(file).href)).default;
const id = "11111111-1111-1111-1111-111111111111",
    token = "22222222-2222-2222-2222-222222222222";
const catalog = {
    version: 1,
    cases: [{ id: "spent-potion", unsupported: null }],
    runs: [],
    location: "<synthetic>",
    retention: "private",
    caps: {},
};
const report = {
    version: 1,
    lane: "deterministic_fake_shared_host",
    synthetic: true,
    quality_accepted: false,
    completed: true,
    cancelled: false,
    binding_sha256: "a".repeat(64),
    model: null,
    runtime: null,
    hardware: null,
    android_parity: "not_run",
    unsupported_lanes: ["real_model"],
    provenance: {},
    cases: [
        {
            id: "spent-potion",
            status: "failed",
            unsupported: null,
            provider_requests: [],
            turns: [
                {
                    id: "gift-0",
                    intent: {},
                    phase: "committed",
                    error: null,
                    revision: 1,
                    canonical_sha256: "b".repeat(64),
                    narration: "<img src=x onerror=alert(1)>",
                    fallback: null,
                    repairs: null,
                },
            ],
            checks: [
                {
                    id: "mock-only-missing-item",
                    stage: "canonical",
                    turn: "gift-0",
                    status: "failed",
                    expected: 1,
                    actual: 0,
                },
            ],
        },
    ],
};
const status = {
    version: 1,
    run_token: token,
    run_id: id,
    operation_id: null,
    running: false,
    phase: "completed",
    error: null,
    completed_cases: 1,
    completed: true,
};
let release;
let held = false;
const calls = [];
const c = new EvaluationController(async (name, args) => {
    calls.push({ name, args });
    if (held && name === "evaluation_catalog")
        return await new Promise((r) => (release = r));
    if (name === "evaluation_catalog") return catalog;
    if (name === "evaluation_read")
        return {
            version: 1,
            run_token: token,
            run_id: id,
            case_id: null,
            report,
        };
    return status;
});
c.contextChanged("story-a|lab|player", true);
held = true;
const waiting = c.show();
c.contextChanged("story-b|play|player", false);
release(catalog);
await waiting;
assert.equal(c.get().catalog, null);
assert.equal(c.get().shown, false);
held = false;
c.contextChanged("story-b|lab|omniscient", true);
await c.show();
await c.start();
assert.equal(c.selected().status, "failed");
c.selectTurn("gift-0");
assert.equal(c.get().selectedTurn, "gift-0");
assert(!calls.some((c) => c.name === "host_call"));
const html = renderToStaticMarkup(
    createElement(EvaluationPanel, {
        controller: c,
        context: "story-b|lab|omniscient",
        allowed: true,
    }),
);
assert(html.includes("mock-only-missing-item"));
assert(html.includes("Expected"));
assert(html.includes("Actual"));
assert(html.includes("D05 story-inspector bridge unavailable"));
assert(html.includes("D06 trace unavailable"));
assert(html.includes("&lt;img"));
assert(!html.includes('<img src="x"'));
c.contextChanged("story-b|lab|mira", true);
assert.equal(c.get().report, null);
assert.equal(c.get().selectedTurn, null);
let startRelease;
const late = new EvaluationController(async (name) =>
    name === "evaluation_start"
        ? await new Promise((r) => (startRelease = r))
        : catalog,
);
late.contextChanged("a", true);
const start = late.start();
late.contextChanged("b", false);
startRelease(status);
await start;
assert.equal(late.get().status, null);
const malformed = new EvaluationController(async (name) =>
    name === "evaluation_read"
        ? {
              version: 1,
              run_token: token,
              run_id: id,
              case_id: null,
              report: { ...report, quality_accepted: true },
          }
        : status,
);
malformed.contextChanged("x", true);
await malformed.start();
assert.equal(malformed.get().error, "EvaluationInvalidReply");
// A held native read must not publish after a new story/lens context.
let readRelease, readEntered;
const readReady = new Promise((r) => (readEntered = r));
const heldRead = new EvaluationController(async (name) => {
    if (name === "evaluation_read") {
        readEntered();
        return await new Promise((r) => (readRelease = r));
    }
    return status;
});
heldRead.contextChanged("first|lab|player", true);
const oldRead = heldRead.start();
await readReady;
heldRead.contextChanged("second|lab|mira", true);
readRelease({
    version: 1,
    run_token: token,
    run_id: id,
    case_id: null,
    report,
});
await oldRead;
assert.equal(heldRead.get().report, null);
assert.equal(heldRead.get().status, null);
// Cancel must retain the exact observed native operation, even when its reply is late.
let cancelRelease, cancelEntered, statusRelease, statusEntered;
const cancelReady = new Promise((r) => (cancelEntered = r)),
    statusReady = new Promise((r) => (statusEntered = r));
const exact = new EvaluationController(async (name, args) => {
    if (name === "evaluation_start")
        return {
            ...status,
            running: true,
            completed: false,
            completed_cases: 0,
            operation_id: 7,
        };
    if (name === "evaluation_status") {
        statusEntered();
        return await new Promise((r) => (statusRelease = r));
    }
    if (name === "evaluation_cancel") {
        assert.equal(args.operationId, 7);
        cancelEntered();
        return await new Promise((r) => (cancelRelease = r));
    }
    return catalog;
});
exact.contextChanged("old|lab|player", true);
const original = exact.start();
await statusReady;
const stopping = exact.cancel();
await cancelReady;
exact.contextChanged("new|play|player", false);
cancelRelease(status);
statusRelease(status);
await Promise.all([original, stopping]);
assert.equal(exact.get().status, null);
assert.equal(exact.get().error, null);
const wrongContext = renderToStaticMarkup(
    createElement(EvaluationPanel, {
        controller: c,
        context: "new-context",
        allowed: true,
    }),
);
assert.equal(wrongContext, "");
console.log(
    "PASS: evaluation controller late catalog/start/context fencing, bounded synthetic-only decoder, report-internal source selection, inert expected/actual failure-row MOCK render and explicit unavailable D05/D06 bridges.",
);

// Curated adapter tests use the SAME actual controller; all replies in this block are MOCK.
const scope = { story: "mock-evaluated-story", branch: "main" };
const curatedCatalog = {
    version: 1,
    cases: Array.from({ length: 6 }, (_, i) => ({
        id: i === 0 ? "spent-potion" : `mock-case-${i}`,
        turns: 4,
        sources: Array.from({ length: 4 }, (_, n) => ({
            turn: n === 0 ? "gift-0" : `mock-turn-${n}`,
            scope,
        })),
    })),
    runs: [],
    location: "<synthetic curated>",
    caps: {},
    approved_profile: null,
    model: {},
};
const curatedReport = {
    ...structuredClone(report),
    lane: "scripted_curated_shared_host",
};
const curatedStatus = {
    ...status,
    lane: "scripted",
    client_id: id,
    source_binding: "a".repeat(64),
    snapshot: {
        version: 1,
        binding_sha256: "a".repeat(64),
        resume_compatible: true,
        completed: true,
        checkpointed_stories: 1,
        budget: { roles_charged: 2 },
        report: curatedReport,
    },
};
const roleText = "<img src=x onerror=alert(1)>";
const evidence = {
    version: 1,
    run_token: token,
    run_id: id,
    evidence: {
        version: 1,
        case_id: "spent-potion",
        turn_id: "gift-0",
        binding_sha256: "a".repeat(64),
        scope: { branch: "main", story: scope.story },
        revision: 1,
        canonical_sha256: "b".repeat(64),
        observer: { kind: "omniscient" },
        page: {
            version: 1,
            scope,
            head: 1,
            revision: 1,
            story_time: 100,
            observer: { kind: "omniscient" },
            view: "turn_diff",
            privacy: "private_omniscient",
            status: "supported",
            total: 0,
            rows: [],
            next_cursor: null,
            unsupported: [],
        },
        receipt: { synthetic_mock: true },
        outputs: [
            {
                role: "director",
                text: roleText,
                bytes: new TextEncoder().encode(roleText).length,
                sha256: "c".repeat(64),
            },
        ],
        role_metrics: null,
        missing: ["historical_context"],
        exact_reconstruction: false,
        read_only: true,
        generation_grant: false,
    },
};
let loseAck = true,
    originalClient,
    heldEvidence = null,
    badEvidence = null;
const curatedCalls = [];
const cu = new EvaluationController(async (name, args) => {
    curatedCalls.push({ name, args: structuredClone(args) });
    if (name === "evaluation_catalog") return catalog;
    assert.equal(name, "evaluation_curated");
    if (args.action === "catalog") return curatedCatalog;
    if (args.action === "start") {
        originalClient = args.query.clientId;
        if (loseAck) {
            loseAck = false;
            throw Error("EvaluationIo");
        }
        return { ...curatedStatus, client_id: originalClient };
    }
    if (args.action === "lookup") {
        assert.equal(args.query.clientId, originalClient);
        return { ...curatedStatus, client_id: originalClient };
    }
    if (args.action === "evidence") {
        if (heldEvidence) return await heldEvidence;
        return badEvidence ?? evidence;
    }
    return { ...curatedStatus, client_id: originalClient };
});
cu.contextChanged("curated|lab|omniscient", true);
await cu.show();
await cu.curatedShow();
await cu.curatedStart("scripted");
assert.equal(cu.get().pendingClient, originalClient);
assert.equal(cu.get().curatedError, "EvaluationIo");
await cu.curatedRecover();
assert.equal(cu.get().curatedStatus.client_id, originalClient);
assert.equal(cu.get().pendingClient, null);
cu.curatedSelectTurn("gift-0");
await cu.curatedInspect();
assert(
    cu.get().curatedEvidence,
    "actual controller admits bound evaluated evidence",
);
const curatedMarkup = renderToStaticMarkup(
    createElement(EvaluationPanel, {
        controller: cu,
        context: "curated|lab|omniscient",
        allowed: true,
    }),
);
assert(curatedMarkup.includes("&lt;img"));
assert(!curatedMarkup.includes("<img"));
assert(curatedMarkup.includes("not retained"));
for (const mutate of [
    (v) => (v.evidence.binding_sha256 = "d".repeat(64)),
    (v) => (v.run_id = token),
    (v) => (v.evidence.scope.story = "foreign"),
    (v) => (v.evidence.revision = 2),
    (v) => (v.evidence.outputs[0].bytes = 1),
    (v) => (v.evidence.generation_grant = true),
]) {
    badEvidence = structuredClone(evidence);
    mutate(badEvidence);
    await cu.curatedInspect();
    assert.equal(cu.get().curatedEvidence, null);
    assert.equal(cu.get().curatedError, "EvaluationInvalidReply");
}
badEvidence = null;
let releaseEvidence;
heldEvidence = new Promise((r) => (releaseEvidence = r));
const oldEvidence = cu.curatedInspect();
await new Promise((r) => setImmediate(r));
cu.contextChanged("other|play|player", false);
releaseEvidence(evidence);
await oldEvidence;
assert.equal(cu.get().curatedEvidence, null);
assert.equal(cu.get().curatedStatus, null);
let releaseCatalog;
const lateCurated = new EvaluationController(
    async () => await new Promise((r) => (releaseCatalog = r)),
);
lateCurated.contextChanged("first|lab|omniscient", true);
const loading = lateCurated.curatedShow();
lateCurated.contextChanged("second|lab|player", true);
releaseCatalog(curatedCatalog);
await loading;
assert.equal(lateCurated.get().curatedCatalog, null);
console.log(
    "PASS: MOCK actual curated controller preserves lost-ack identity, rejects foreign/binding/revision/raw-size/grant evidence, clears late context, and escapes raw report/output in SSR. This is not native runner/UI execution.",
);
