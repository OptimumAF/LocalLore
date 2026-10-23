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
console.log(
    "PASS: evaluation controller late catalog/start/context fencing, bounded synthetic-only decoder, report-internal source selection, inert expected/actual failure-row MOCK render and explicit unavailable D05/D06 bridges.",
);
