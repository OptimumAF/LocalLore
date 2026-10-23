// Fixed packaged resource staging; never stages or downloads model weights.
import { readFile, mkdir, writeFile } from "node:fs/promises";
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
    "add98cf02249141942c88e2517c2f5a4c9a91dbe9638bf7d3cd30c26916bce87";
const bytes = await readFile(source);
if (
    bytes.length > 16 * 1024 * 1024 ||
    createHash("sha256").update(bytes).digest("hex") !== expected
)
    throw new Error("UnapprovedWorker");
for (const destination of [
    path.join(root, "src-tauri", "runtime"),
    path.join(
        process.env.LOCALLORE_D04_TARGET_DIR ??
            path.join(root, "src-tauri", "target"),
        "debug",
        "runtime",
    ),
]) {
    await mkdir(destination, { recursive: true });
    await writeFile(
        path.join(destination, "locallore-llama-worker.exe"),
        bytes,
    );
}
console.log("Staged reviewed fixed CPU worker; no model bytes copied.");
