// Actual frontend controllers/helper with synthetic transport DTOs only.
// No accepted Rust receipt, durable save, native IPC, rendering or model proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID, webcrypto } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

globalThis.crypto ??= webcrypto;
const desktop = fileURLToPath(new URL("./", import.meta.url));
const bundle = await build({
    stdin: { contents: 'export { Controller } from "./ui/controller"; export { resumeTimeline } from "./ui/timeline-controller"; export { AuthorController } from "./ui/author-controller";', resolveDir: desktop, loader: "ts" },
    bundle: true, platform: "node", format: "esm", write: false,
});
const { Controller, resumeTimeline, AuthorController } = await import(`data:text/javascript;base64,${Buffer.from(bundle.outputFiles[0].contents).toString("base64")}`);
const clone = (value) => structuredClone(value);
const parent = { story: "timeline-review", branch: "main" };
const child = { story: "timeline-review", branch: "corrected" };
const sha = (value) => createHash("sha256").update(value).digest("hex");
const tests = [], test = (name, run) => tests.push({ name, run });
const forbidden = new Set(["create", "submit", "prepare", "commit", "free_text", "grant_lab"]);
function thin(scope, revision, domain) {
    return { version: 2, domain_version: domain, scope: clone(scope), revision, rules: "fantasy_v1", player: { observer: "player", self_state: { name: "Rowan", location: "quay", alive: true, energy: 2, abilities: { steady: 1 }, attributes: { resolve: 3 }, injuries: [], affiliations: [], goals: [] } }, inventory: {} };
}
function legacy(scope, revision) {
    return { scope: clone(scope), revision, rules: "fantasy_v1", player: { scope: clone(scope), revision, observer: "player", self_state: { name: "Rowan", location: "quay", energy: 2 }, facts: {}, beliefs: [], observations: [] }, inventory: {}, receipts: [] };
}
class Gateway {
    playSnapshotV2 = true;
    calls = [];
    fault = null;
    childDomain = 2;
    async call(command) {
        this.calls.push(clone(command));
        assert(!forbidden.has(command.op), "resume helper cannot generate, create or grant");
        const isChild = command.scope?.branch === child.branch;
        const revision = isChild ? 2 : 3;
        if (command.op === "workspace") return { persistent: true, location: "synthetic", schema_version: 1, database_schema_version: 5, stories: [{ scope: clone(parent), title: "Synthetic author child", revision: 3, drafts: 0 }] };
        if (command.op === "resume") return { session: `session-${command.scope.branch}`, scope: clone(isChild && this.fault === "parent-resume" ? parent : command.scope), revision };
        if (command.op === "open") return { revision };
        if (command.op === "close") return {};
        if (command.op === "play_snapshot_v2") return thin(isChild && this.fault === "wrong-snapshot-scope" ? parent : command.scope, isChild && this.fault === "wrong-snapshot-head" ? revision + 1 : command.expected_revision, isChild ? this.childDomain : 1);
        if (command.op === "play_snapshot") {
            assert(!isChild || this.childDomain === 1, "Domain2 never falls through to legacy receipt context");
            return legacy(command.scope, command.expected_revision);
        }
        throw Error(`UnexpectedSyntheticOperation:${command.op}`);
    }
}
async function fixture() {
    const gateway = new Gateway(), controller = new Controller(gateway);
    await controller.library();
    await controller.resume(parent);
    assert.equal(controller.selected()?.id, "session-main");
    assert.equal(controller.get().play?.revision, 3);
    return { gateway, controller };
}
function noWrites(gateway) {
    assert(!gateway.calls.some((command) => forbidden.has(command.op)));
}

test("actual Controller corrected-child resume is accepted with playV2 and play:null", async () => {
    const { gateway, controller } = await fixture();
    await resumeTimeline(controller, child);
    assert.deepEqual(controller.selected()?.scope, child);
    assert.equal(controller.selected()?.id, "session-corrected");
    assert.equal(controller.selected()?.revision, 2);
    assert.equal(controller.get().play, null);
    assert.deepEqual(controller.get().playV2, thin(child, 2, 2));
    assert.equal(controller.get().visibleError, null);
    assert.equal(gateway.calls.filter((q) => q.op === "resume" && q.scope.branch === child.branch).length, 1);
    noWrites(gateway);
});

test("existing corrected-child session switch uses coherent V2 proof without a second resume", async () => {
    const { gateway, controller } = await fixture();
    await controller.resume(child);
    await controller.resume(parent);
    const count = gateway.calls.filter((q) => q.op === "resume").length;
    await resumeTimeline(controller, child);
    assert.equal(gateway.calls.filter((q) => q.op === "resume").length, count);
    assert.equal(controller.selected()?.id, "session-corrected");
    assert.equal(controller.get().play, null);
    assert.deepEqual(controller.get().playV2?.scope, child);
    assert.equal(controller.get().playV2?.revision, controller.selected()?.revision);
    noWrites(gateway);
});

test("legacy Domain1 child still proves success through the original player snapshot", async () => {
    const { gateway, controller } = await fixture();
    gateway.childDomain = 1;
    await resumeTimeline(controller, child);
    assert.deepEqual(controller.selected()?.scope, child);
    assert.equal(controller.get().playV2, null);
    assert.equal(controller.get().play?.revision, 2);
    assert.deepEqual(controller.get().play?.scope, child);
    noWrites(gateway);
});

for (const fault of ["parent-resume", "wrong-snapshot-scope", "wrong-snapshot-head"]) {
    test(`actual Controller refuses ${fault} instead of treating parent or stale projection as child proof`, async () => {
        const { gateway, controller } = await fixture();
        gateway.fault = fault;
        await assert.rejects(() => resumeTimeline(controller, child));
        const state = controller.get();
        if (fault === "parent-resume") assert.notDeepEqual(controller.selected()?.scope, child);
        else { assert.equal(state.playV2, null); assert.equal(state.play, null); }
        assert.notEqual(state.visibleError, null, "actual Controller reports the transport identity/projection refusal");
        noWrites(gateway);
    });
}

test("actual AuthorController Open confirmed child uses shared timeline adapter without false NotReady", async () => {
    const { gateway, controller } = await fixture();
    const calls = [], opened = [];
    const port = {
        // Synthetic closed workflow responses, not canonical Core receipts.
        prepareStart: async (raw) => {
            calls.push({ kind: "prepare", request: JSON.parse(raw) });
            return { version: 1, operation_id: 1, running: false, phase: "failed", error: "ArchiveBusy", result: null };
        },
        lookupStart: async (raw) => {
            const request = JSON.parse(raw); calls.push({ kind: "lookup", request });
            return { version: 1, operation_id: 2, running: false, phase: "completed", error: null, result: { version: 1, kind: "author_lookup", found: true, outcome: { version: 1, scope: clone(child), parent: clone(parent), fork_revision: 1, author_revision: 2, head_revision: 2, created: false } } };
        },
        commitStart: async () => { throw Error("MustNotApply"); },
        status: async () => { throw Error("MustNotPoll"); },
        cancel: async () => { throw Error("MustNotCancel"); },
        discardPreview: async () => true,
    };
    // Same real helper effect used by Main, without replacing its predicate.
    const author = new AuthorController(port, { refreshLibrary: () => controller.library(), openChild: async (scope) => { opened.push(clone(scope)); await resumeTimeline(controller, scope); } }, async () => {});
    author.contextChanged({ rootIncarnation: "synthetic-root", selectionEpoch: 1, session: "session-main", scope: clone(parent), head: 3, player: "player", observer: "omniscient", view: "lab", persistent: true, spoilerGranted: true, pending: false, brokerUncertain: false });
    author.setDraft({ fork_revision: 1, child_branch: child.branch, fact: "relic-location", expected_proposition: "SYNTHETIC_A", replacement: "SYNTHETIC_B", reason: "Synthetic reason" });
    author.setAuthorConsent(true);
    await author.prepare();
    assert(author.get().input, "public prepare retains exact input for readonly recovery");
    await author.lookup();
    assert.deepEqual(author.get().outcome?.scope, child);
    assert.equal(author.get().error, null);
    await author.openConfirmed();
    assert.deepEqual(opened, [child]);
    assert.equal(author.get().error, null, "successful Domain2 switch cannot become Unavailable/NotReady");
    assert.deepEqual(controller.selected()?.scope, child);
    assert.equal(controller.get().play, null);
    assert.equal(controller.get().playV2?.revision, 2);
    assert.deepEqual(calls.map((call) => call.kind), ["prepare", "lookup"]);
    noWrites(gateway);
    author.dispose();
});

const checks = [];
for (const { name, run } of tests) {
    try { await run(); checks.push({ name, passed: true }); }
    catch (error) { checks.push({ name, passed: false, error: String(error?.message ?? error).slice(0, 512) }); }
}
const sourceHashes = {};
for (const name of ["ui/timeline-controller.ts", "ui/controller.ts", "ui/author-controller.ts", "ui/main.tsx"]) sourceHashes[name] = sha(await readFile(path.join(desktop, name)));
const report = { version: 1, synthetic: true, evidence: "actual Controller, AuthorController and resumeTimeline with synthetic Gateway/workflow DTOs", checks, passed: checks.filter((row) => row.passed).length, failed: checks.filter((row) => !row.passed).length, sourceHashes, nativeIpc: false, modelExecution: false, rendering: "none", desktopInput: false, limitations: ["author effect uses Main's shared helper composition, not actual Main subscriptions", "no native canonical author save, receipt, durability or permission proof", "no Domain2 Timeline/Fork UI exposure or Android parity qualification"] };
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(desktop, "artifacts/checks");
await mkdir(output, { recursive: true });
const json = JSON.stringify(report, null, 2);
assert(Buffer.byteLength(json) <= 64 * 1024);
await writeFile(path.join(output, `domain2-timeline-resume-${randomUUID()}.json`), json, { flag: "wx" });
console.log(json);
if (report.failed) process.exitCode = 1;
