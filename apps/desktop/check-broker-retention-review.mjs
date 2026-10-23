// Gate/controller with mocked IPC; no native/WebView/model execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import path from "node:path";
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(output, { recursive: true });
const target = path.join(output, `broker-review-${randomUUID()}.mjs`);
const compiled = await build({
    entryPoints: [
        fileURLToPath(
            new URL("ui/broker-retention-review-journeys.ts", import.meta.url),
        ),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { brokerRetentionReviewJourneys } = await import(
    pathToFileURL(target).href
);
const results = await brokerRetentionReviewJourneys();
await writeFile(
    path.join(output, "broker-retention-review.json"),
    JSON.stringify({ backend: "actual-controller-mock-ipc", results }, null, 2),
);
console.log(JSON.stringify(results));
assert.equal(results.length, 6);
assert(
    results.every((result) => result.passed),
    "broker retention review failures retained",
);
