// Frozen acknowledgement regressions, exact baseline f240579. Source-only freeze.
// Run from apps/desktop: node check-archive-v3-ack.mjs
// Real existing transport decoders + BrokerRetention, synthetic JSON. No native
// IPC, canonical writes, WebView, model, Android runtime or replacement validator.
// Root owns first actual RED and the production correction. String(array) enum
// coercion is a source finding, not an executed result or Rust authority bypass.
// Original check-archive-v3.mjs 82 cases and Android 9 tests remain unchanged.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const cohort = randomUUID();
const target = path.join(output, `archive-v3-ack-${cohort}.mjs`);
const built = await build({
    stdin: {
        contents: 'export {decodePreview,decodeStatus,decodeArchiveCompletion,decodeArchiveBinding,archiveBinding} from "./ui/archive-model";export {BrokerRetention} from "./ui/broker-retention";',
        resolveDir: root,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, built.outputFiles[0].contents);
const {
    decodePreview, decodeStatus, decodeArchiveCompletion,
    decodeArchiveBinding, archiveBinding, BrokerRetention,
} = await import(pathToFileURL(target).href);

const token = "11111111-1111-1111-1111-111111111111";
function preview(kind = "import") {
    return {
        version: 1, token, kind, warning: "Full private synthetic archive",
        preview: {
            version: 3, story_id: "synthetic-ack", title: "Synthetic accepted history", root_branch: "main",
            branch_heads: { main: 1, child: 3 }, committed_turns: 3, bytes: 1024,
            payload_sha256: "a".repeat(64),
            privacy_warning: "Full private synthetic accepted records, including author corrections and private discovery bindings.",
            noncommitted_workflow_transferred: false,
        },
    };
}
const terminal = (result, id = 17) => ({
    version: 1, operation_id: id, running: false, phase: "completed", error: null, result,
});
const running = (id = 17) => ({
    version: 1, operation_id: id, running: true, phase: "validating", error: null, result: null,
});
const cancelled = (id = 17) => terminal({ version: 1, status: "cancelled" }, id);
const imported = () => ({
    version: 1, status: "imported", root: { story: "synthetic-ack", branch: "main" },
    branches: 2, committed_turns: 3, staging_cleanup_complete: true,
    pending_workflow_resumed: false, model_loaded: false,
});
const exported = () => ({
    version: 1, status: "exported", location: "synthetic.locallore-story.json", payload_sha256: "a".repeat(64),
});
const identity = { surface: "archive", action: "archive_import_preview" };
const competing = { surface: "archive", action: "archive_export_preview" };
const cases = [];
const test = (name, run) => cases.push({ name, run });
const completion = (result, kind) => decodeArchiveCompletion(
    decodeStatus(terminal(result)), `archive_${kind}`, archiveBinding(decodePreview(preview(kind))),
);

test("literal running phase remains valid and nonterminal", () => {
    assert.equal(decodeStatus(running()).phase, "validating");
    assert.equal(decodeStatus(running()).running, true);
});
test("literal native cancelled preview acknowledgement remains valid", () => {
    assert.equal(decodeArchiveCompletion(decodeStatus(cancelled()), "archive_import_preview").status, "cancelled");
});
test("literal imported result keeps actual root/count/exclusion metadata", () => {
    assert.deepEqual(completion(imported(), "import"), imported());
});
test("literal exported result remains bound to the actual preview hash", () => {
    assert.deepEqual(completion(exported(), "export"), exported());
});

for (const status of ["imported", "exported", "cancelled", "failed"]) {
    test(`reject array terminal status [${status}] before payload guards can be bypassed`, () => {
        // Deliberately missing the imported/exported/failed fields. Coercion
        // currently passes membership, then strict string branches skip checks.
        assert.throws(() => decodeStatus(terminal({ version: 1, status: [status] })), /Wire/);
    });
}
test("reject array-valued running phase", () => {
    assert.throws(() => decodeStatus({ ...running(), phase: ["validating"] }), /Wire/);
});
for (const kind of ["import", "export"]) {
    test(`reject array preview kind [${kind}] at the decoder boundary`, () => {
        const wire = preview(kind);
        wire.kind = [kind];
        assert.throws(() => decodePreview(wire), /Wire/);
    });
    test(`reject array retained-binding kind [${kind}] at the decoder boundary`, () => {
        const binding = { ...archiveBinding(decodePreview(preview(kind))), kind: [kind] };
        assert.throws(() => decodeArchiveBinding(binding), /Wire/);
    });
}

for (const [name, mutate] of [
    ["missing root", (v) => { delete v.root; }],
    ["over branch cap", (v) => { v.branches = 33; }],
    ["over canonical record cap", (v) => { v.committed_turns = 4097; }],
    ["unverified staging cleanup", (v) => { v.staging_cleanup_complete = false; }],
    ["resumed pending workflow", (v) => { v.pending_workflow_resumed = true; }],
    ["loaded model", (v) => { v.model_loaded = true; }],
]) test(`literal imported payload still rejects ${name}`, () => {
    const result = imported();
    mutate(result);
    assert.throws(() => completion(result, "import"), /Wire/);
});
for (const [name, mutate] of [
    ["missing location", (v) => { delete v.location; }],
    ["missing checksum", (v) => { delete v.payload_sha256; }],
    ["malformed checksum", (v) => { v.payload_sha256 = "not-a-checksum"; }],
]) test(`literal exported payload still rejects ${name}`, () => {
    const result = exported();
    mutate(result);
    assert.throws(() => completion(result, "export"), /Wire/);
});
test("literal imported result cannot change the captured story or root", () => {
    const result = imported();
    result.root.story = "foreign-story";
    assert.throws(() => completion(result, "import"), /Wire/);
});
test("literal exported result cannot change the captured checksum", () => {
    const result = exported();
    result.payload_sha256 = "b".repeat(64);
    assert.throws(() => completion(result, "export"), /Wire/);
});

async function uncertain() {
    const gate = new BrokerRetention(() => false);
    await gate.start(identity, async () => running());
    assert.equal(gate.get().operation, 17);
    // A malformed own-ID completion establishes actual transport uncertainty
    // while retaining its known operation identity. No new native operation.
    gate.observe(terminal({ version: 1, status: "imported" }));
    assert.equal(gate.get().operation, 17);
    assert.equal(gate.get().unknown, true);
    assert.equal(gate.get().consumed, false);
    return gate;
}
for (const status of ["imported", "exported"]) {
    test(`array [${status}] acknowledgement cannot settle original known-ID uncertainty`, async () => {
        const gate = await uncertain();
        gate.observe(terminal({ version: 1, status: [status] }));
        assert.equal(gate.get().operation, 17);
        assert.equal(gate.get().unknown, true);
        assert.equal(gate.get().consumed, false);
        assert.equal(gate.get().terminal, false);
    });
    test(`array [${status}] acknowledgement cannot admit a competing shared start`, async () => {
        const gate = await uncertain();
        gate.observe(terminal({ version: 1, status: [status] }));
        let dispatched = 0;
        await assert.rejects(() => gate.start(competing, async () => {
            dispatched++;
            return cancelled(18);
        }), /ArchiveBusy/);
        assert.equal(dispatched, 0);
        assert.equal(gate.get().identity.action, identity.action);
        assert.equal(gate.get().operation, 17);
    });
}
test("exact valid native cancelled acknowledgement resolves only the original operation", async () => {
    const gate = await uncertain();
    let dispatched = 0;
    await assert.rejects(() => gate.start(competing, async () => {
        dispatched++;
        return cancelled(18);
    }), /ArchiveBusy/);
    gate.observe(cancelled());
    assert.equal(gate.get().operation, 17);
    assert.equal(gate.get().unknown, false);
    assert.equal(gate.get().terminal, true);
    assert.equal(gate.get().consumed, true);
    assert.equal(dispatched, 0, "Native terminal observation does not dispatch another operation");
    await gate.start(competing, async () => {
        dispatched++;
        return cancelled(18);
    });
    assert.equal(dispatched, 1, "Only a later explicit start dispatches");
    assert.equal(gate.get().operation, 18);
});

const results = [];
for (const { name, run } of cases) {
    try {
        await run();
        results.push({ name, status: "pass" });
    } catch (error) {
        results.push({ name, status: "fail", error: String(error?.message ?? error).slice(0, 512) });
    }
}
const failed = results.filter((r) => r.status === "fail").length;
const report = {
    suite: "archive-v3-ack", execution: "synthetic actual decoder + retained broker gate; no native execution",
    passed: results.length - failed, failed, results,
};
await writeFile(path.join(output, `archive-v3-ack-${cohort}.json`), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
assert.equal(failed, 0, `${failed} Archive3 acknowledgement oracle(s) failed`);
