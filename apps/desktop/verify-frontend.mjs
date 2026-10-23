import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import assert from "node:assert/strict";
const root = new URL(".", import.meta.url);
for (const args of [
    ["build.mjs"],
    ["node_modules/typescript/bin/tsc", "--noEmit"],
    ["check-contract.mjs"],
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
    "harness_oracle",
])
    assert(
        !normal.includes(marker),
        `Test hook leaked into normal bundle: ${marker}`,
    );
console.log(
    "PASS: strict TypeScript, current request/schema checks, and no development journey/control hooks in normal frontend.",
);
