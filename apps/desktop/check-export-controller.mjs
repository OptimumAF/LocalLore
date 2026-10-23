// Privacy/race regressions run the actual frontend controller, not a parallel reducer.
import { build } from "esbuild";
import { mkdirSync, writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
const folder = new URL("./artifacts/checks/", import.meta.url);
mkdirSync(folder, { recursive: true });
const file = new URL(`export-controller-${randomUUID()}.mjs`, folder);
const compiled = await build({
    entryPoints: [fileURLToPath(new URL("ui/controller.ts", import.meta.url))],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
writeFileSync(file, compiled.outputFiles[0].contents);
const { Controller } = await import(file.href);
const scope = { story: "synthetic", branch: "main" };
let cancelRelease,
    previewRelease,
    holdPreview = false,
    heldMode = "full";
const gateway = {
    async call(command) {
        if (command.op === "open")
            return { session: "session-1", scope, revision: 0 };
        if (command.op === "play_snapshot")
            return {
                scope,
                revision: 0,
                rules: "fantasy_v1",
                inventory: {},
                receipts: [],
                player: {
                    scope,
                    revision: 0,
                    observer: "player",
                    self_state: { name: "Rowan", energy: 2, location: "quay" },
                    facts: {},
                    beliefs: [],
                    observations: [],
                },
            };
        if (command.op === "inspect" || command.op === "close") return {};
        throw new Error("Unsupported");
    },
    async native(command, args) {
        if (command === "inspection_cancel")
            return new Promise((resolve) => {
                cancelRelease = () => resolve({ status: "cancelled" });
            });
        if (command === "inspection_preview") {
            heldMode = args.mode;
            if (holdPreview)
                await new Promise((resolve) => {
                    previewRelease = resolve;
                });
            return {
                token: randomUUID(),
                manifest: { scope, revision: 0, mode: heldMode },
                expires_seconds: 300,
                files: [{ path: "manifest.json", bytes: 2 }],
            };
        }
        throw new Error("Unsupported");
    },
};
const c = new Controller(gateway);
await c.attach({ id: "session-1", scope, revision: 0, name: "Synthetic" });
c.setView("lab");
c.setExportMode("full");
await c.previewExport();
assert.equal(c.get().exports.preview.manifest.mode, "full");
c.setExportMode("diagnostics");
assert.equal(c.get().exports.mode, "diagnostics");
assert.equal(c.get().exports.preview, null);
assert.equal(c.get().exports.opened, null);
cancelRelease();
c.setExportMode("full");
await c.previewExport();
c.setView("play");
assert.equal(c.get().exports.mode, "diagnostics");
assert.equal(c.get().exports.preview, null);
cancelRelease();
c.setView("lab");
c.setExportMode("full");
holdPreview = true;
const pending = c.previewExport();
while (!previewRelease) await new Promise((resolve) => setTimeout(resolve, 0));
c.setView("play");
previewRelease();
await new Promise((resolve) => setTimeout(resolve, 0));
cancelRelease();
await pending;
assert.equal(c.get().exports.preview, null);
assert.equal(c.get().exports.mode, "diagnostics");
await c.dispose();
console.log(
    "PASS: delayed native cancellation and stale Full preview cannot appear under Diagnostics or Play.",
);
