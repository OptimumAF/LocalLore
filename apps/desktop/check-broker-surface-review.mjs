// Actual controllers/gate, fixed mocked native IPC. No native or render execution.
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
const compiled = await build({
    entryPoints: [
        fileURLToPath(
            new URL("ui/broker-surface-review-journeys.ts", import.meta.url),
        ),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
const target = path.join(output, `broker-surface-review-${randomUUID()}.mjs`);
await writeFile(target, compiled.outputFiles[0].contents);
const { brokerSurfaceReviewJourneys } = await import(
    pathToFileURL(target).href
);
const results = await brokerSurfaceReviewJourneys();
await writeFile(
    path.join(output, "broker-surface-review.json"),
    JSON.stringify(
        { backend: "actual-controllers-mock-ipc", results },
        null,
        2,
    ),
);
console.log(JSON.stringify(results));
assert.equal(results.length, 8);
assert(
    results.every((result) => result.passed),
    "broker surface failures retained",
);
