import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
const root = new URL(".", import.meta.url);
for (const args of [
    ["build.mjs"],
    ["node_modules/typescript/bin/tsc", "--noEmit"],
    ["check-contract.mjs"],
    ["check-export-controller.mjs"],
    ["check-model-controller.mjs"],
    ["check-early-cancel.mjs"],
    ["check-model-refresh.mjs"],
    ["check-inspection-controller.mjs"],
    ["check-trace-controller.mjs"],
    ["check-capture-controller.mjs"],
    ["check-evaluation-controller.mjs"],
    ["check-archive-controller.mjs"],
]) {
    const code = await new Promise((resolve, reject) => {
        const child = spawn(process.execPath, args, {
            cwd: root,
            stdio: "inherit",
            shell: false,
        });
        child.on("error", reject);
        child.on("exit", resolve);
    });
    assert.equal(code, 0, `Frontend check ${args[0]}`);
}
const normal = await readFile(new URL("dist/app.js", root), "utf8");
for (const marker of [
    "harness_checkpoint",
    "harness_reopen",
    "harness_finish",
    "uncertain-commit-retry-original-id-once",
    "heldPrepare",
    "harness:durable",
    "restart-retry-does-not-double-apply",
    "harness_oracle",
    "harness_export_case",
    "harness_model_case",
    "real-free-text-potion-committed",
    "query-native-durable-workspace",
    "d05-external-wait",
    "d06-native-default-disabled",
    "d06-external-wait",
    "d07-native-evaluation-checkpoints",
    "harness_evaluation_case",
    "harness_archive_case",
    "harness_capture_case",
    "private-capture-native-production-play",
    "MALFORMED_SYNTHETIC_DIRECTOR",
    "d08-native-durable-workspace",
    "legacy-v1-native-migrated-resume",
    "export-snapshot-independent-of-later-turn",
])
    assert(
        !normal.includes(marker),
        `Test hook leaked into normal bundle: ${marker}`,
    );
console.log(
    "PASS: strict TypeScript, current request/schema checks, and no development journey/control hooks in normal frontend.",
);
