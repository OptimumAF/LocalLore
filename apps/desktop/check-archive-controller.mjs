// Actual archive controller/React render with controlled native doubles, not native execution.
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
const file = path.join(output, `archive-${randomUUID()}.cjs`),
    result = await build({
        stdin: {
            contents:
                'export {ArchiveController} from "./ui/archive-controller";export {ArchivePanel} from "./ui/ArchivePanel";export {decodePreview,decodeStatus,decodeArchiveCompletion} from "./ui/archive-model";export {BrokerRetention} from "./ui/broker-retention";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
            resolveDir: root,
            loader: "tsx",
        },
        bundle: true,
        platform: "node",
        format: "cjs",
        write: false,
    });
await writeFile(file, result.outputFiles[0].contents);
const {
    ArchiveController,
    ArchivePanel,
    decodePreview,
    decodeStatus,
    decodeArchiveCompletion,
    BrokerRetention,
    createElement,
    renderToStaticMarkup,
} = (await import(pathToFileURL(file).href)).default;
const token = "11111111-1111-1111-1111-111111111111",
    scope = { story: "synthetic", branch: "main" };
const preview = {
    version: 1,
    token,
    kind: "import",
    warning: "Full private",
    preview: {
        version: 1,
        story_id: "synthetic",
        title: "<img onerror=alert(1)>",
        root_branch: "main",
        branch_heads: { main: 1 },
        committed_turns: 1,
        bytes: 1024,
        payload_sha256: "a".repeat(64),
        privacy_warning: "Full private",
        noncommitted_workflow_transferred: false,
    },
};
const retirement = structuredClone(preview);
retirement.preview.version = 2;
retirement.preview.branch_heads = { main: 1, parent: 1, child: 1 };
retirement.preview.retired_branch_ids = ["collected", "parent"];
assert.equal(decodePreview(retirement).preview.version, 2);
for (const mutate of [
    (v) => {
        v.preview.version = 4;
    },
    (v) => {
        v.preview.version = 1;
    },
    (v) => {
        v.preview.retired_branch_ids = [];
    },
    (v) => {
        v.preview.retired_branch_ids = ["parent", "parent"];
    },
    (v) => {
        v.preview.retired_branch_ids = ["parent", "collected"];
    },
    (v) => {
        v.preview.retired_branch_ids = ["main"];
    },
    (v) => {
        v.preview.retired_branch_ids = ["bad/id"];
    },
    (v) => {
        v.preview.retired_branch_ids = Array.from(
            { length: 257 },
            (_, i) => `retired-${String(i).padStart(3, "0")}`,
        );
    },
    (v) => {
        v.preview.retired_branch_ids = Array.from(
            { length: 255 },
            (_, i) => `retired-${String(i).padStart(3, "0")}`,
        );
    },
]) {
    const bad = structuredClone(retirement);
    mutate(bad);
    assert.throws(() => decodePreview(bad), /Wire/);
}
let release;
const calls = [];
const invoke = async (name, args) => {
    calls.push({ name, args });
    if (name === "archive_import_preview")
        return new Promise((r) => (release = r));
    return { version: 1, discarded: true };
};
const c = new ArchiveController(invoke, async () => {});
c.contextChanged("A|lab|omniscient", true);
c.show();
const pending = c.previewImport();
c.contextChanged("B|play|player", false);
release({
    version: 1,
    operation_id: 1,
    running: false,
    phase: "completed",
    error: null,
    result: preview,
});
await pending;
assert.equal(c.get().preview, null);
assert.equal(c.get().shown, false);
assert(
    calls.some((x) => x.name === "archive_discard" && x.args.token === token),
    "late private preview capability revoked",
);
decodePreview(preview);
assert.throws(() =>
    decodePreview({
        ...preview,
        preview: {
            ...preview.preview,
            noncommitted_workflow_transferred: true,
        },
    }),
);
assert.throws(() =>
    decodeStatus({
        version: 1,
        operation_id: 0,
        running: false,
        phase: "completed",
        error: null,
        result: null,
    }),
);
const ui = new ArchiveController(
    async () => ({
        version: 1,
        operation_id: 2,
        running: false,
        phase: "completed",
        error: null,
        result: preview,
    }),
    async () => {},
);
ui.contextChanged("A|lab|omniscient", true);
ui.show();
await ui.previewImport();
const html = renderToStaticMarkup(
    createElement(ArchivePanel, {
        archive: ui,
        controller: {
            get: () => ({ play: { revision: 1 } }),
            selected: () => ({ id: "session", scope }),
            resume: async () => {},
        },
        context: "A|lab|omniscient",
        allowed: true,
    }),
);
assert(html.includes("&lt;img"));
assert(!html.includes("<img"));
assert(html.includes("Confirm staged import"));
assert(html.includes("Existing story identity always conflicts"));
assert(html.includes("Hidden") || html.includes("hidden facts"));
const retiredUi = new ArchiveController(
    async () => ({
        version: 1,
        operation_id: 88,
        running: false,
        phase: "completed",
        error: null,
        result: retirement,
    }),
    async () => {},
);
retiredUi.contextChanged("A|lab|omniscient", true);
retiredUi.show();
await retiredUi.previewImport();
const retiredHtml = renderToStaticMarkup(
    createElement(ArchivePanel, {
        archive: retiredUi,
        controller: {
            get: () => ({ play: { revision: 1 } }),
            selected: () => ({ id: "session", scope }),
        },
        context: "A|lab|omniscient",
        allowed: true,
    }),
);
assert(retiredHtml.includes("Retired ancestry only"));
assert(retiredHtml.includes("Reserved retired identities"));
assert(retiredHtml.includes("collected, parent"));
assert(retiredHtml.includes("Playable"));
const n = calls.length;
await c.confirm();
assert.equal(calls.length, n, "Play cannot confirm");
const complete = (operation_id, result) => ({
    version: 1,
    operation_id,
    running: false,
    phase: "completed",
    error: null,
    result,
});
const running = {
    version: 1,
    operation_id: 3,
    running: true,
    phase: "validating",
    error: null,
    result: null,
};
assert.throws(() => decodeStatus({ ...running, extra: "synthetic" }), /Wire/);
for (const result of [
    { version: 1, status: "cancelled" },
    { version: 1, status: "failed", error: "ArchiveIo", cleanup_complete: false },
    {
        version: 1,
        status: "failed",
        error: "Integrity",
        staging_cleanup_complete: true,
    },
]) {
    const status = decodeStatus(complete(7, result));
    assert.deepEqual(status.result, result);
    if (result.status === "failed") {
        const exportFailure = Object.hasOwn(result, "cleanup_complete");
        const owner = exportFailure ? "archive_export" : "archive_import";
        const other = exportFailure ? "archive_import" : "archive_export";
        assert.equal(decodeArchiveCompletion(status, owner), result);
        assert.throws(() => decodeArchiveCompletion(status, other), /Wire/);
        assert.throws(
            () => decodeArchiveCompletion(status, `${owner}_preview`),
            /Wire/,
        );
    }
    for (const extra of [
        { root: { story: "foreign", branch: "main" } },
        { location: "synthetic.locallore-story.json" },
    ]) {
        assert.throws(
            () => decodeStatus(complete(7, { ...result, ...extra })),
            /Wire/,
        );
    }
}

const offers = [];
const retiredDuringDispatch = new ArchiveController(
    async (name) => {
        offers.push(name);
        return complete(7, preview);
    },
    async () => {},
);
retiredDuringDispatch.contextChanged("A|lab|omniscient", true);
retiredDuringDispatch.show();
const releaseDispatchListener = retiredDuringDispatch.subscribe(() => {
    const { shown, busy } = retiredDuringDispatch.get();
    if (shown && busy)
        retiredDuringDispatch.contextChanged("B|play|player", false);
});
await retiredDuringDispatch.previewImport();
releaseDispatchListener();
assert.deepEqual(offers, [], "retiring during dispatch must prevent the offer");
assert.equal(retiredDuringDispatch.get().shown, false);

const exportPreview = {
    ...preview,
    kind: "export",
    preview: { ...preview.preview, branch_heads: { main: 1, child: 2 } },
};
for (const [reply, valid] of [
    [exportPreview, true],
    [
        {
            ...exportPreview,
            preview: { ...exportPreview.preview, story_id: "foreign" },
        },
        false,
    ],
    [
        {
            ...exportPreview,
            preview: { ...exportPreview.preview, branch_heads: { main: 1 } },
        },
        false,
    ],
    [
        {
            ...exportPreview,
            preview: {
                ...exportPreview.preview,
                branch_heads: { main: 1, child: 3 },
            },
        },
        false,
    ],
]) {
    const offeredScope = { story: "synthetic", branch: "child" };
    const exposed = [];
    const commands = [];
    const exporting = new ArchiveController(
        async (name, args) => {
            commands.push(name);
            assert.deepEqual(args.scope, { story: "synthetic", branch: "child" });
            return complete(8, reply);
        },
        async () => {},
    );
    exporting.contextChanged("A|lab|omniscient", true);
    exporting.subscribe(() => {
        offeredScope.branch = "later-selection";
        const value = exporting.get();
        if (value.status?.result) {
            exposed.push(value.status.result);
            assert.equal(
                value.preview?.token,
                token,
                "validated terminal status and preview publish together",
            );
        }
    });
    await exporting.previewExport("session", offeredScope, 2);
    assert.deepEqual(commands, ["archive_export_preview"]);
    assert.equal(exposed.length > 0, valid);
    assert.equal(exporting.get().preview?.token, valid ? token : undefined);
    assert.equal(exporting.get().error, valid ? null : "Wire");

    const retained = new BrokerRetention(() => false);
    await retained.start(
        {
            surface: "archive",
            action: "archive_export_preview",
            session: "session",
            story: "synthetic",
            branch: "child",
            head: 2,
        },
        async () => complete(8, reply),
    );
    assert.equal(retained.get().unknown, !valid);
    assert.equal(retained.get().terminal, valid);
    assert.equal(retained.get().consumed, valid);
    if (valid) {
        const verified = retained.get();
        retained.observe({ ...running, operation_id: 8 });
        assert.equal(
            retained.get(),
            verified,
            "late cancel snapshot cannot reopen a verified terminal archive",
        );
        await retained.start(
            { surface: "archive", action: "archive_import_preview" },
            async () => complete(9, preview),
        );
        assert.equal(retained.get().operation, 9);
    }
}

let statusRelease,
    first = true;
const cancelRejectors = [];
const heldCalls = [];
const held = new ArchiveController(
    async (name, args) => {
        heldCalls.push({ name, args });
        if (name === "archive_import_preview") {
            if (first) {
                first = false;
                return running;
            }
            return complete(4, {
                ...preview,
                token: "22222222-2222-2222-2222-222222222222",
            });
        }
        if (name === "archive_status")
            return new Promise((r) => (statusRelease = r));
        if (name === "archive_cancel" && args.operationId === 3)
            return new Promise((_, reject) => cancelRejectors.push(reject));
        return { version: 1, discarded: true };
    },
    async () => {},
);
held.contextChanged("A|lab|omniscient", true);
const reading = held.previewImport();
while (!statusRelease) await new Promise((r) => setTimeout(r, 1));
const cancellation = held.cancel();
held.contextChanged("A|play|player", false);
held.contextChanged("B|lab|omniscient", true);
await held.previewImport();
statusRelease(complete(3, preview));
for (const reject of cancelRejectors) reject(Error("Closed"));
await reading;
await cancellation;
assert.equal(held.get().preview.token, "22222222-2222-2222-2222-222222222222");
assert.equal(held.get().error, null);
assert(
    heldCalls
        .filter((x) => x.name === "archive_cancel")
        .every((x) => x.args.operationId === 3),
);
assert(
    heldCalls.some((x) => x.name === "archive_discard" && x.args.token === token),
    "a late result for the polled operation still revokes its own token",
);

function deferred() {
    let resolve, reject;
    const promise = new Promise((ok, fail) => {
        resolve = ok;
        reject = fail;
    });
    return { promise, resolve, reject };
}

const newerPreview = {
    ...preview,
    token: "33333333-3333-3333-3333-333333333333",
};
const wrongPollStarted = deferred(),
    wrongPollReply = deferred(),
    wrongPollDiscards = [];
let wrongPollOffers = 0;
const wrongPoll = new ArchiveController(
    async (name, args) => {
        if (name === "archive_import_preview")
            return ++wrongPollOffers === 1 ? running : complete(9, newerPreview);
        if (name === "archive_status") {
            wrongPollStarted.resolve();
            return wrongPollReply.promise;
        }
        if (name === "archive_discard") wrongPollDiscards.push(args.token);
        return running;
    },
    async () => {},
);
wrongPoll.contextChanged("A|lab|omniscient", true);
const retiredPoll = wrongPoll.previewImport();
await wrongPollStarted.promise;
wrongPoll.contextChanged("B|lab|omniscient", true);
await wrongPoll.previewImport();
wrongPollReply.resolve(complete(9, newerPreview));
await retiredPoll;
assert.deepEqual(
    wrongPollDiscards,
    [],
    "wrong-operation poll cannot revoke a newer preview",
);
assert.equal(wrongPoll.get().preview.token, newerPreview.token);

const activePollStarted = deferred(),
    activePollReply = deferred(),
    lateCancel = deferred();
let archiveOffers = 0,
    cancellations = 0;
const cancelling = new ArchiveController(
    async (name) => {
        if (name === "archive_import_preview") {
            archiveOffers++;
            return running;
        }
        if (name === "archive_status") {
            activePollStarted.resolve();
            return activePollReply.promise;
        }
        if (name === "archive_cancel") {
            if (++cancellations === 1) throw Error("Closed");
            if (cancellations === 2) return { ...running, operation_id: 99 };
            if (cancellations === 3) return running;
            return lateCancel.promise;
        }
        throw Error("unexpected command");
    },
    async () => {},
);
cancelling.contextChanged("A|lab|omniscient", true);
const activeAction = cancelling.previewImport();
await activePollStarted.promise;
await cancelling.cancel();
assert.equal(cancelling.get().error, "Closed");
assert.equal(cancelling.get().busy, true);
await cancelling.cancel();
assert.equal(cancelling.get().error, "Wire");
assert.equal(cancelling.get().busy, true);
await cancelling.previewImport();
assert.equal(archiveOffers, 1, "cancel failure cannot release the active offer");
await cancelling.cancel();
assert.match(cancelling.get().notice, /^Cancellation requested/);
assert.equal(cancelling.get().busy, true);
const pendingCancel = cancelling.cancel();
activePollReply.resolve(complete(3, preview));
await activeAction;
assert.equal(cancelling.get().preview.token, token);
assert.equal(cancelling.get().error, null);
const settledArchive = cancelling.get();
lateCancel.reject(Error("Closed"));
await pendingCancel;
assert.equal(
    cancelling.get(),
    settledArchive,
    "late cancel failure leaves completion intact",
);

let refreshed = 0;
const bad = new ArchiveController(
    async (name) =>
        name === "archive_import_preview"
            ? complete(5, preview)
            : complete(6, {
                  version: 1,
                  status: "imported",
                  root: { story: "foreign", branch: "main" },
                  branches: 1,
                  committed_turns: 1,
                  staging_cleanup_complete: true,
                  pending_workflow_resumed: false,
                  model_loaded: false,
              }),
    async () => {
        refreshed++;
    },
);
bad.contextChanged("A|lab|omniscient", true);
await bad.previewImport();
await bad.confirm();
assert.equal(
    bad.get().preview.token,
    token,
    "unchecked consent never invokes import",
);
bad.consent(true);
await bad.confirm();
assert.equal(bad.get().error, "Wire");
assert.equal(
    refreshed,
    0,
    "wrong imported identity never refreshes as success",
);
console.log(
    "PASS: actual archive controller stale-context/consent and strict private metadata fences; inert React preview with explicit staging/conflict/exclusion labels (native doubles).",
);
