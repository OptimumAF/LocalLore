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

const retiredOffers = [];
const retiredDispatch = new EvaluationController(async (name) => {
    retiredOffers.push(name);
    return status;
});
retiredDispatch.contextChanged("same|lab|omniscient", true);
retiredDispatch.subscribe(() => {
    if (retiredDispatch.get().busy)
        retiredDispatch.contextChanged("same|lab|omniscient", false);
});
await retiredDispatch.start();
await retiredDispatch.show();
assert.deepEqual(retiredOffers, [], "same-key revocation must stop an offer");

const foreignRun = "33333333-3333-3333-3333-333333333333";
const builtInCalls = [];
const wrongOpen = new EvaluationController(async (name) => {
    builtInCalls.push(name);
    return { ...status, run_id: foreignRun };
});
wrongOpen.contextChanged("lab", true);
await wrongOpen.open(id);
assert.deepEqual(builtInCalls, ["evaluation_open"]);
assert.equal(wrongOpen.get().status, null);
assert.equal(wrongOpen.get().error, "EvaluationInvalidReply");

const runningStatus = {
    ...status,
    running: true,
    completed: false,
    completed_cases: 0,
    phase: "running",
    operation_id: 7,
};
const reportReply = {
    version: 1,
    run_token: token,
    run_id: id,
    case_id: null,
    report,
};
let polls = 0;
const wrongPoll = new EvaluationController(async (name) => {
    if (name === "evaluation_start") return runningStatus;
    if (name === "evaluation_read") return reportReply;
    assert.equal(name, "evaluation_status");
    return ++polls === 1 ? { ...runningStatus, operation_id: 8 } : status;
});
wrongPoll.contextChanged("lab", true);
await wrongPoll.start();
assert.equal(wrongPoll.get().status.operation_id, 7);
assert.equal(wrongPoll.get().error, "EvaluationInvalidReply");

const wrongLane = new EvaluationController(async (name) =>
    name === "evaluation_read"
        ? {
              ...reportReply,
              report: { ...report, lane: "scripted_curated_shared_host" },
          }
        : status,
);
wrongLane.contextChanged("lab", true);
await wrongLane.start();
assert.equal(wrongLane.get().report, null);
assert.equal(wrongLane.get().error, "EvaluationInvalidReply");

function deferred() {
    let resolve, reject;
    const promise = new Promise((done, fail) => {
        resolve = done;
        reject = fail;
    });
    return { promise, resolve, reject };
}

const builtInPollEntered = deferred(),
    builtInPoll = deferred(),
    lateCancel = deferred();
let cancelCalls = 0;
const cancelling = new EvaluationController(async (name) => {
    if (name === "evaluation_start") return runningStatus;
    if (name === "evaluation_status") {
        builtInPollEntered.resolve();
        return builtInPoll.promise;
    }
    if (name === "evaluation_cancel") {
        if (++cancelCalls === 1) throw Error("EvaluationIo");
        return lateCancel.promise;
    }
    assert.equal(name, "evaluation_read");
    return reportReply;
});
cancelling.contextChanged("lab", true);
const active = cancelling.start();
await builtInPollEntered.promise;
await cancelling.cancel();
assert.equal(cancelling.get().busy, true);
assert.equal(cancelling.get().error, "EvaluationIo");
const later = cancelling.cancel();
builtInPoll.resolve(status);
await active;
lateCancel.reject(Error("EvaluationIo"));
await later;
assert.equal(cancelling.get().busy, false);
assert.equal(cancelling.get().error, null);
assert.equal(cancelling.get().report.binding_sha256, report.binding_sha256);

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
const retiredSnapshots = [];
const releaseRetirement = cu.subscribe(() => retiredSnapshots.push(cu.get()));
cu.contextChanged("other|play|player", false);
releaseRetirement();
assert.equal(retiredSnapshots.length, 1);
assert.equal(retiredSnapshots[0].shown, false);
assert.equal(retiredSnapshots[0].curatedStatus, null);
assert.equal(retiredSnapshots[0].curatedEvidence, null);
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

const curatedOffers = [];
const retiredCuratedDispatch = new EvaluationController(async (name, args) => {
    curatedOffers.push({ name, args });
    return curatedStatus;
});
retiredCuratedDispatch.contextChanged("first|lab|omniscient", true);
retiredCuratedDispatch.subscribe(() => {
    if (retiredCuratedDispatch.get().curatedBusy)
        retiredCuratedDispatch.contextChanged("second|lab|omniscient", true);
    if (retiredCuratedDispatch.get().pendingClient)
        void retiredCuratedDispatch.curatedRecover();
});
await retiredCuratedDispatch.curatedStart("scripted");
retiredCuratedDispatch.contextChanged("second|lab|player", true);
await retiredCuratedDispatch.curatedShow();
assert.deepEqual(curatedOffers, []);
assert.equal(retiredCuratedDispatch.get().pendingClient, null);

let bindMode = "wrong-start-client";
let startOffered = false;
let secondOfferedClient;
const ownership = new EvaluationController(async (name, { action, query }) => {
    assert.equal(name, "evaluation_curated");
    if (bindMode === "wrong-start-client") {
        assert.equal(action, "start");
        startOffered = true;
        return { ...curatedStatus, client_id: foreignRun };
    }
    if (bindMode === "wrong-lookup-client") {
        assert.equal(action, "lookup");
        return { ...curatedStatus, client_id: foreignRun };
    }
    if (bindMode === "correct-lookup") {
        assert.equal(action, "lookup");
        return { ...curatedStatus, client_id: query.clientId };
    }
    if (bindMode === "wrong-start-lane") {
        assert.equal(action, "start");
        secondOfferedClient = query.clientId;
        return {
            ...curatedStatus,
            client_id: query.clientId,
            lane: "native",
            snapshot: null,
        };
    }
    if (bindMode === "wrong-open") {
        assert.equal(action, "open");
        return { ...curatedStatus, run_id: foreignRun };
    }
    if (bindMode === "open-with-pending") {
        assert.equal(action, "open");
        return { ...curatedStatus, client_id: secondOfferedClient };
    }
    if (action === "open") return curatedStatus;
    assert.equal(action, "resume");
    assert.equal(query.runToken, token);
    return {
        ...curatedStatus,
        run_token: foreignRun,
        ...(bindMode === "wrong-resume" ? { client_id: foreignRun } : {}),
    };
});
ownership.contextChanged("lab|omniscient", true);
let firstRecoveryNotice;
const beforeStartNotice = ownership.subscribe(() => {
    if (ownership.get().pendingClient)
        firstRecoveryNotice ??= startOffered;
});
await ownership.curatedStart("scripted");
beforeStartNotice();
assert.equal(firstRecoveryNotice, true);
const offeredClient = ownership.get().pendingClient;
assert.ok(offeredClient);
assert.equal(ownership.get().curatedStatus, null);
assert.equal(ownership.get().curatedError, "EvaluationInvalidReply");
bindMode = "wrong-lookup-client";
await ownership.curatedRecover();
assert.equal(ownership.get().pendingClient, offeredClient);
assert.equal(ownership.get().curatedStatus, null);
bindMode = "correct-lookup";
await ownership.curatedRecover();
assert.equal(ownership.get().curatedStatus.client_id, offeredClient);
assert.equal(ownership.get().pendingClient, null);
bindMode = "wrong-start-lane";
await ownership.curatedStart("scripted");
assert.equal(ownership.get().curatedStatus, null);
assert.equal(ownership.get().curatedError, "EvaluationInvalidReply");
bindMode = "wrong-open";
await ownership.curatedOpen(id);
assert.equal(ownership.get().curatedStatus, null);
assert.equal(ownership.get().curatedError, "EvaluationInvalidReply");
assert.equal(ownership.get().pendingClient, secondOfferedClient);
bindMode = "open-with-pending";
await ownership.curatedOpen(id);
assert.equal(ownership.get().curatedStatus.client_id, secondOfferedClient);
assert.equal(ownership.get().pendingClient, null);
bindMode = "wrong-resume";
await ownership.curatedOpen(id);
await ownership.curatedResume();
assert.equal(ownership.get().curatedStatus, null);
assert.equal(ownership.get().curatedError, "EvaluationInvalidReply");
bindMode = "correct-resume";
await ownership.curatedOpen(id);
await ownership.curatedResume();
assert.equal(ownership.get().curatedStatus.run_id, id);
assert.equal(ownership.get().curatedStatus.run_token, foreignRun);

const curatedPollEntered = deferred(),
    curatedPoll = deferred(),
    curatedCancel = deferred();
let curatedCancelCalls = 0;
let currentClient;
const curatedRunning = { ...curatedStatus, ...runningStatus, snapshot: null };
const stoppingCurated = new EvaluationController(async (name, args) => {
    if (name === "evaluation_cancel") {
        assert.equal(args.operationId, 7);
        if (++curatedCancelCalls === 1)
            return {
                ...curatedRunning,
                operation_id: 8,
                client_id: currentClient,
            };
        return curatedCancel.promise;
    }
    if (args.action === "start") {
        currentClient = args.query.clientId;
        return { ...curatedRunning, client_id: currentClient };
    }
    assert.equal(args.action, "status");
    curatedPollEntered.resolve();
    return curatedPoll.promise;
});
stoppingCurated.contextChanged("lab|omniscient", true);
const runningCurated = stoppingCurated.curatedStart("scripted");
await curatedPollEntered.promise;
await stoppingCurated.curatedCancel();
assert.equal(stoppingCurated.get().curatedBusy, true);
assert.equal(stoppingCurated.get().curatedError, "EvaluationInvalidReply");
const cancelCuratedLater = stoppingCurated.curatedCancel();
curatedPoll.resolve({ ...curatedStatus, client_id: currentClient });
await runningCurated;
curatedCancel.reject(Error("EvaluationIo"));
await cancelCuratedLater;
assert.equal(stoppingCurated.get().curatedBusy, false);
assert.equal(stoppingCurated.get().curatedError, null);
assert.equal(stoppingCurated.get().curatedStatus.run_id, id);
assert.equal(stoppingCurated.get().pendingClient, null);

console.log(
    "PASS: MOCK actual curated controller preserves lost-ack identity, rejects foreign/binding/revision/raw-size/grant evidence, clears late context, and escapes raw report/output in SSR. This is not native runner/UI execution.",
);
