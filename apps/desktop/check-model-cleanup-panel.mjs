// Run from apps/desktop: node check-model-cleanup-panel.mjs
// Actual Controller.refreshModel validation + ModelPanel static HTML semantics.
// Synthetic native status/held action; no native IPC, WebView, image or model.
// refreshModel currently checks loaded/phase; this adds no replacement decoder.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const cohort = randomUUID();
const prefix = `model-cleanup-panel-${cohort}`;
const bundle = path.join(output, `${prefix}.cjs`);
const built = await build({
    stdin: {
        contents:
            'export {Controller} from "./ui/controller";export {ModelPanel} from "./ui/ModelPanel";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const { Controller, ModelPanel, createElement, renderToStaticMarkup } = (
    await import(pathToFileURL(bundle).href)
).default;
const sourceHashes = Object.fromEntries(
    await Promise.all(
        ["ui/controller.ts", "ui/ModelPanel.tsx"].map(async (name) => [
            name,
            createHash("sha256")
                .update(await readFile(path.join(root, name)))
                .digest("hex"),
        ]),
    ),
);
const warning =
    "Local worker cleanup could not be confirmed. Choose Unload model to retry cleanup before loading another model.";
const cases = [
    {
        name: "resident-cleanup",
        phase: "failed",
        resident: true,
        loaded: false,
        error: "Cleanup",
        busy: false,
        disabled: [true, true, false],
    },
    {
        name: "resident-loaded",
        phase: "loaded",
        resident: true,
        loaded: true,
        error: null,
        busy: false,
        disabled: [true, true, false],
    },
    {
        name: "clean-unloaded-imported",
        phase: "unloaded",
        resident: false,
        loaded: false,
        error: null,
        busy: false,
        disabled: [false, false, true],
    },
    {
        name: "pending-unloading",
        phase: "unloading",
        resident: true,
        loaded: false,
        error: null,
        busy: true,
        disabled: [true, true, true],
    },
];
function status(item) {
    return {
        operation_id: 7,
        phase: item.phase,
        resident: item.resident,
        loaded: item.loaded,
        imported: true,
        error: item.error,
        percent: item.busy ? 40 : 100,
        profile: null,
        available_profile: {
            id: "synthetic-profile",
            model_bytes: 1,
            model_sha256: "a".repeat(64),
            runtime_revision: "synthetic-only",
            device: "Synthetic CPU fixture",
            qualification: "Synthetic plumbing; no model execution.",
        },
    };
}
const text = (html) =>
    html
        .replace(/<[^>]*>/g, "")
        .replaceAll("&amp;", "&")
        .replace(/\s+/g, " ")
        .trim();
function disabled(html, label) {
    const buttons = [
        ...html.matchAll(/<button\b([^>]*)>([\s\S]*?)<\/button>/g),
    ].filter((match) => text(match[2]) === label);
    assert.equal(buttons.length, 1, `one actual panel button: ${label}`);
    return /\bdisabled(?:=|\s|$)/.test(buttons[0][1]);
}
const realSetInterval = globalThis.setInterval;
const realClearInterval = globalThis.clearInterval;
const intervals = new Set();
let intervalId = 0;
globalThis.setInterval = () => {
    const id = ++intervalId;
    intervals.add(id);
    return id;
};
globalThis.clearInterval = (id) => intervals.delete(id);
const results = [];
try {
    for (const item of cases) {
        let nativeStatus = status(item),
            release,
            action;
        const calls = [];
        const controller = new Controller({
            async native(command) {
                calls.push(command);
                if (command === "model_status")
                    return structuredClone(nativeStatus);
                assert.equal(command, "model_unload");
                assert.equal(item.busy, true);
                return new Promise((resolve) => {
                    release = resolve;
                });
            },
            async call() {
                throw new Error("UnexpectedSyntheticHostCall");
            },
        });
        try {
            controller.showModel();
            await controller.refreshModel();
            if (item.busy) {
                action = controller.modelAction("model_unload");
                await controller.refreshModel();
            }
            const state = controller.get();
            assert.deepEqual(state.model, nativeStatus);
            assert.equal(state.modelShown, true);
            assert.equal(state.modelBusy, item.busy);
            assert.equal(state.visibleError, null);
            const html = renderToStaticMarkup(
                createElement(ModelPanel, { controller, state }),
            );
            assert.ok(Buffer.byteLength(html) <= 32768);
            await writeFile(
                path.join(output, `${prefix}-${item.name}.html`),
                html,
                { flag: "wx" },
            );
            const controls = [
                "Choose GGUF & import local copy",
                "Load CPU model",
                "Unload model & cancel local work",
            ];
            assert.deepEqual(
                controls.map((label) => disabled(html, label)),
                item.disabled,
            );
            const alerts = [
                ...html.matchAll(/<p\b[^>]*role="alert"[^>]*>([\s\S]*?)<\/p>/g),
            ].map((match) => text(match[1]));
            assert.deepEqual(alerts, item.error === "Cleanup" ? [warning] : []);
            const phase = item.busy
                ? "Unloading and waiting for local work to stop - 40%"
                : item.phase;
            assert.ok(html.includes(`role="status">${phase}</p>`));
            assert.equal(html.includes("<progress"), item.busy);
            assert.ok(text(html).includes("No downloads or cloud fallback."));
            assert.ok(
                calls.every(
                    (command) =>
                        command === "model_status" ||
                        (item.busy && command === "model_unload"),
                ),
            );
            results.push({
                name: item.name,
                passed: true,
                model: state.model,
                busy: state.modelBusy,
            });
        } catch (error) {
            results.push({
                name: item.name,
                passed: false,
                error: String(error.message).slice(0, 600),
            });
        } finally {
            if (release) {
                nativeStatus = status({
                    ...item,
                    phase: "unloaded",
                    resident: false,
                    loaded: false,
                    error: null,
                    busy: false,
                });
                release({});
            }
            await action;
            await controller.dispose();
        }
    }
    assert.equal(
        intervals.size,
        0,
        "held synthetic action leaves no polling interval",
    );
} finally {
    globalThis.setInterval = realSetInterval;
    globalThis.clearInterval = realClearInterval;
}
const report = {
    suite: "model-cleanup-panel",
    execution:
        "synthetic actual-controller status + React static HTML semantics",
    native_ipc: false,
    native_rendering: false,
    render_images: false,
    model_execution: false,
    sourceHashes,
    passed: results.filter((result) => result.passed).length,
    failed: results.filter((result) => !result.passed).length,
    results,
};
await writeFile(
    path.join(output, `${prefix}.json`),
    JSON.stringify(report, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(report));
if (report.failed) process.exitCode = 1;
