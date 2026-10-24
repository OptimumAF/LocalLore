// Frozen pure-gate vectors. No native, WebView, model or desktop execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import path from "node:path";
const out =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(out, { recursive: true });
const target = path.join(out, `broker-retention-${randomUUID()}.mjs`);
const compiled = await build({
    entryPoints: [
        fileURLToPath(new URL("ui/broker-retention.ts", import.meta.url)),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { BrokerRetention } = await import(pathToFileURL(target).href);
const checks = [];
const check = (v, label) => {
    assert(v, label);
    checks.push(label);
};
const identity = {
    surface: "memory",
    session: "session-1",
    story: "memory-controls-synthetic",
    branch: "main",
    head: 1,
    action: "step",
};
// Native-shaped MOCK metadata replaces the original gate-only cross-surface
// placeholders. Every original admission/retention assertion remains unchanged.
const forkIdentity = {...identity,surface:"fork",action:"fork",child:"fixture-child",at:0};
const archiveIdentity = {...identity,surface:"archive",action:"archive_import_preview"};
const forkOp = (id=1)=>({version:1,operation_id:id,running:false,phase:"completed",error:null,result:{kind:"fork",outcome:{version:1,scope:{story:identity.story,branch:forkIdentity.child},parent:{story:identity.story,branch:identity.branch},fork_revision:forkIdentity.at,head_revision:forkIdentity.at,created:true}}});
const archiveOp = (id=1)=>({version:1,operation_id:id,running:false,phase:"completed",error:null,result:{version:1,status:"cancelled"}});
const op = (running, id = 1, action = identity.action) => ({
    version: 1,
    operation_id: id,
    running,
    phase: running ? "memory_maintenance" : "completed",
    error: null,
    result: running
        ? null
        : {
              version: 1,
              kind: "memory_maintenance",
              action,
              session: identity.session,
              scope: { story: identity.story, branch: identity.branch },
              expected_head: identity.head,
              maintenance: {
                  version: 1,
                  scope: { story: identity.story, branch: identity.branch },
                  head: identity.head,
                  action,
                  job: null,
              },
          },
});
let busy = true;
const gate = new BrokerRetention(() => busy);
let resolve;
const held = new Promise((r) => (resolve = r));
const pending = gate.start(identity, () => held);
await assert.rejects(
    () => gate.start(forkIdentity, async () => forkOp()),
    /ArchiveBusy/,
);
check(true, "inflight-crosssurface-start-blocked");
resolve(op(false));
await pending;
await assert.rejects(
    () =>
        gate.start(archiveIdentity, async () => archiveOp()),
    /ArchiveBusy/,
);
check(true, "terminal-awaiting-controller-consumption-retained");
busy = false;
await gate.start(archiveIdentity, async () => archiveOp(2));
check(true, "consumed-terminal-allows-next-explicit-start");
const unknown = new BrokerRetention(() => false);
await assert.rejects(
    () =>
        unknown.start(identity, async () => {
            throw Error("Transport");
        }),
    /Transport/,
);
check(unknown.get()?.unknown === true, "unknown-ack-retains-fixed-identity");
check(
    unknown.get()?.identity.story === identity.story &&
        unknown.get()?.identity.action === "step",
    "retained-identity-is-original",
);
await assert.rejects(
    () =>
        unknown.start(forkIdentity, async () => forkOp()),
    /ArchiveBusy/,
);
check(true, "unknown-ack-blocks-other-surface");
await assert.rejects(
    () =>
        unknown.recoverMemory(
            { ...identity, story: "different-story", action: "status" },
            async () => op(false),
        ),
    /ArchiveBusy/,
);
check(true, "different-scope-passive-read-cannot-resolve-original-unknown");
await assert.rejects(
    () =>
        unknown.recoverMemory(
            { ...identity, head: 2, action: "status" },
            async () => op(false),
        ),
    /ArchiveBusy/,
);
check(true, "different-head-passive-read-cannot-resolve-original-unknown");
await assert.rejects(
    () =>
        unknown.recoverMemory({ ...identity, action: "status" }, async () => {
            throw Error("Stale");
        }),
    /Stale/,
);
check(unknown.get()?.unknown, "stale-original-status-preserves-barrier");
await unknown.recoverMemory({ ...identity, action: "status" }, async () =>
    op(false, 3, "status"),
);
check(
    !unknown.get()?.unknown,
    "exact-original-passive-status-observed-terminal",
);
const acknowledged = new BrokerRetention(() => false);
await assert.rejects(() =>
    acknowledged.start(identity, async () => {
        throw Error("Transport");
    }),
);
check(
    !acknowledged.acknowledgeUnresolved(false),
    "unresolved-release-requires-explicit-consent",
);
check(acknowledged.get()?.unknown, "no-consent-preserves-barrier");
check(
    acknowledged.acknowledgeUnresolved(true),
    "consented-release-is-explicit",
);
check(
    acknowledged.get()?.acknowledgedUnresolved === true &&
        acknowledged.get()?.identity.story === identity.story,
    "release-retains-original-uncertainty-metadata",
);
let actualCalls = 0;
await assert.rejects(
    () =>
        acknowledged.start(forkIdentity, async () => {
            actualCalls++;
            throw Error("ArchiveBusy");
        }),
    /ArchiveBusy/,
);
check(
    actualCalls === 1,
    "released-presentation-still-obeys-actual-native-busy",
);
const known = new BrokerRetention(() => false);
await known.start(identity, async () => op(true, 4));
known.observe(op(false, 99));
check(
    known.get()?.operation === 4 && !known.get()?.terminal,
    "foreign-operation-cannot-release-known-barrier",
);
known.observe(op(false, 4));
check(
    known.get()?.terminal,
    "actual-exact-terminal-status-releases-known-operation",
);
await assert.rejects(
    () =>
        new BrokerRetention(() => false).start(
            { ...identity, prose: "not permitted" },
            async () => op(false),
        ),
    /InvalidInput/,
);
check(true, "identity-rejects-unknown-prose-fields");
await writeFile(
    path.join(out, "broker-retention.json"),
    JSON.stringify({ backend: "pure-mock", passed: true, checks }, null, 2),
);
console.log(`PASS: ${checks.length} pure broker retention assertions.`);
