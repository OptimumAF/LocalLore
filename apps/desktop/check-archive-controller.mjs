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
                'export {ArchiveController} from "./ui/archive-controller";export {ArchivePanel} from "./ui/ArchivePanel";export {decodePreview,decodeStatus} from "./ui/archive-model";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
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
        v.preview.version = 3;
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
