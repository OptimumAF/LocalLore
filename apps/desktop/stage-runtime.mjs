// Fixed packaged resource staging; never stages or downloads model weights.
import { readFile, mkdir, copyFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import path from "node:path";
import { fileURLToPath } from "node:url";
const root = fileURLToPath(new URL(".", import.meta.url));
const source = process.env.LOCALLORE_D04_WORKER_SOURCE;
if (!source)
    throw new Error(
        "Set LOCALLORE_D04_WORKER_SOURCE to the reviewed fixed native build artifact.",
    );
const expected =
    "eda393e923ddfd03ea57d91741d8f7948d1a4af13deb90c7d6c90c492e63ff58";
const bytes = await readFile(source);
if (
    bytes.length > 16 * 1024 * 1024 ||
    createHash("sha256").update(bytes).digest("hex") !== expected
)
    throw new Error("UnapprovedWorker");
for (const destination of [
    path.join(root, "src-tauri", "runtime"),
    path.join(root, "src-tauri", "target", "debug", "runtime"),
]) {
    await mkdir(destination, { recursive: true });
    await copyFile(
        source,
        path.join(destination, "locallore-llama-worker.exe"),
    );
}
console.log("Staged reviewed fixed CPU worker; no model bytes copied.");
