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
const n = calls.length;
await c.confirm();
assert.equal(calls.length, n, "Play cannot confirm");
console.log(
    "PASS: actual archive controller stale-context/consent and strict private metadata fences; inert React preview with explicit staging/conflict/exclusion labels (native doubles).",
);
