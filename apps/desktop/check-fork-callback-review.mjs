// Headless controller review only. No browser/native app/device/model execution.
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import path from "node:path";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const compiled = await build({
    entryPoints: [
        fileURLToPath(
            new URL("ui/fork-callback-review-journeys.ts", import.meta.url),
        ),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
const file = path.join(directory, `fork-callback-review-${randomUUID()}.mjs`);
await writeFile(file, compiled.outputFiles[0].contents);
const { runForkCallbackReview } = await import(pathToFileURL(file).href);
const report = await runForkCallbackReview();
await writeFile(
    path.join(directory, "fork-callback-review.json"),
    `${JSON.stringify(report, null, 2)}\n`,
);
console.log(JSON.stringify(report));
if (report.results.some((result) => !result.passed)) process.exitCode = 1;
