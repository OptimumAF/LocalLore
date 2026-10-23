// Actual controller with mocked IPC. No native/browser/device execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import path from "node:path";
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(output, {recursive:true});
const target = path.join(output, `memory-callback-${randomUUID()}.mjs`);
const compiled = await build({entryPoints:[fileURLToPath(new URL("ui/memory-callback-review-journeys.ts",import.meta.url))],bundle:true,platform:"node",format:"esm",write:false});
await writeFile(target, compiled.outputFiles[0].contents);
const {memoryCallbackReviewJourneys} = await import(pathToFileURL(target).href);
const checks = await memoryCallbackReviewJourneys();
assert.equal(checks.length,30);
await writeFile(path.join(output,"memory-callback-review.json"),JSON.stringify({backend:"mock",passed:true,checks},null,2));
console.log(`PASS: ${checks.length} actual-controller callback assertions with mocked IPC.`);
