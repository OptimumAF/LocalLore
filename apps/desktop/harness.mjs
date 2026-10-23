// Application-owned native/headless evidence runner. Never attaches to other apps.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { createHash } from "node:crypto";
import { createInterface } from "node:readline";
const root = fileURLToPath(new URL(".", import.meta.url));
const mode = process.argv[2];
if (!["native", "headless"].includes(mode))
    throw new Error("Use native or headless");
const executable = path.join(
    root,
    "src-tauri",
    "target",
    "debug",
    process.platform === "win32"
        ? "locallore-desktop-spike.exe"
        : "locallore-desktop-spike",
);
const parent = path.join(root, "artifacts");
await mkdir(parent, { recursive: true });
const directory = path.join(parent, `${mode}-${randomUUID()}`);
const git = async (...args) =>
    (await promisify(execFile)("git", args, { cwd: root })).stdout.trim();
const sourceRevision = await git("rev-parse", "HEAD");
const sourceDirty = (await git("status", "--porcelain")).length > 0;
async function run(command, args, options = {}) {
    return new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: root,
            stdio: "inherit",
            shell: false,
            ...options,
        });
        const timer = setTimeout(() => child.kill(), 210_000);
        child.once("error", reject);
        child.once("exit", (code) => {
            clearTimeout(timer);
            code === 0 ? resolve() : reject(new Error(`ChildExit${code}`));
        });
    });
}
await run(process.execPath, ["build.mjs", "--harness"]);
await run("cargo", [
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--locked",
    "--offline",
    "--features",
    "dev-harness",
]);
if (mode === "native") {
    await run(executable, [], {
        env: {
            ...process.env,
            LOCALLORE_D02_HARNESS: "1",
            LOCALLORE_D02_ARTIFACT_DIR: directory,
        },
    });
} else {
    await mkdir(directory);
    const { chromium } = await import("playwright");
    class Bridge {
        constructor() {
            this.next = 0;
            this.pending = new Map();
            this.child = spawn(executable, ["--host-stdio"], {
                cwd: root,
                stdio: ["pipe", "pipe", "ignore"],
                shell: false,
            });
            this.closed = new Promise((r) => this.child.once("exit", r));
            this.lines = createInterface({ input: this.child.stdout });
            this.lines.on("line", (line) => {
                try {
                    const { id, value } = JSON.parse(line);
                    this.pending.get(id)?.resolve(value);
                    this.pending.delete(id);
                } catch {
                    this.fail();
                }
            });
            this.child.on("error", () => this.fail());
            this.child.on("exit", () => this.fail());
        }
        fail() {
            for (const p of this.pending.values())
                p.reject(new Error("Transport"));
            this.pending.clear();
        }
        call(kind, args = {}) {
            const id = String(++this.next);
            return new Promise((resolve, reject) => {
                const timer = setTimeout(() => {
                    this.pending.delete(id);
                    reject(new Error("Transport"));
                }, 15000);
                timer.unref();
                this.pending.set(id, {
                    resolve: (value) => {
                        clearTimeout(timer);
                        resolve(value);
                    },
                    reject: (error) => {
                        clearTimeout(timer);
                        reject(error);
                    },
                });
                this.child.stdin.write(
                    JSON.stringify({ id, kind, ...args }) + "\n",
                );
            });
        }
        async close() {
            if (!this.child.stdin.destroyed && !this.child.stdin.writableEnded)
                this.child.stdin.end();
            let timer;
            try {
                await Promise.race([
                    this.closed,
                    new Promise((resolve) => {
                        timer = setTimeout(() => {
                            this.child.kill();
                            resolve();
                        }, 5000);
                    }),
                ]);
            } finally {
                clearTimeout(timer);
                this.fail();
                this.lines.close();
            }
        }
    }
    let bridge = new Bridge();
    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage({
        viewport: { width: 1280, height: 900 },
        reducedMotion: "reduce",
    });
    const labels = new Set(),
        captures = [],
        unexpected = [];
    let finish;
    const finished = new Promise((r) => (finish = r));
    const allowed = new Set([
        "initial",
        "play-accepted",
        "play-rejected",
        "pending",
        "cancelled",
        "retry",
        "failed",
        "malformed",
        "stale",
        "session-switch",
        "receipt",
        "observer",
        "play-return",
        "narrow",
        "enlarged",
        "reopened",
        "finished",
        "close",
        "copy",
        "pagination",
        "injection",
        "disposed",
    ]);
    await page.route("**/*", async (route) => {
        const url = new URL(route.request().url());
        if (url.origin !== "http://locallore.test") {
            unexpected.push("ExternalRequest");
            return route.abort();
        }
        const name =
            url.pathname === "/" ? "index.html" : url.pathname.slice(1);
        if (!["index.html", "app.js", "style.css"].includes(name)) {
            unexpected.push("UnknownAsset");
            return route.abort();
        }
        await route.fulfill({
            body: await readFile(path.join(root, "dist", name)),
            contentType: name.endsWith(".js")
                ? "text/javascript"
                : name.endsWith(".css")
                  ? "text/css"
                  : "text/html",
        });
    });
    await page.exposeBinding(
        "__localLoreAppHarness",
        async (_source, command, args = {}) => {
            switch (command) {
                case "host_call":
                    return bridge.call("host", { input: args.input });
                case "harness_stats":
                    return bridge.call("stats");
                case "harness_oracle":
                    return bridge.call("oracle", { receipts: args.receipts });
                case "harness_viewport":
                    if (!["wide", "narrow"].includes(args.preset))
                        throw new Error("ViewportInvalid");
                    await page.setViewportSize({
                        width: args.preset === "wide" ? 1280 : 680,
                        height: 900,
                    });
                    return null;
                case "harness_checkpoint": {
                    if (
                        !allowed.has(args.label) ||
                        labels.has(args.label) ||
                        labels.size >= 40 ||
                        args.snapshot?.synthetic !== true ||
                        !Number.isSafeInteger(args.snapshot.uiRevision) ||
                        JSON.stringify(args.snapshot).length > 262144
                    )
                        throw new Error("ArtifactInvalid");
                    labels.add(args.label);
                    await writeFile(
                        path.join(directory, args.label + ".json"),
                        JSON.stringify(args.snapshot, null, 2),
                    );
                    await page.screenshot({
                        path: path.join(directory, args.label + ".png"),
                        fullPage: true,
                        animations: "disabled",
                    });
                    const result = {
                        synthetic: true,
                        label: args.label,
                        rendering: "headless-chromium",
                        uiRevision: args.snapshot.uiRevision,
                    };
                    captures.push(result);
                    await writeFile(
                        path.join(directory, args.label + ".capture.json"),
                        JSON.stringify(result, null, 2),
                    );
                    return result;
                }
                case "harness_reopen":
                    await bridge.close();
                    bridge = new Bridge();
                    await page.goto("http://locallore.test/?reopened=1", {
                        waitUntil: "domcontentloaded",
                    });
                    return null;
                case "harness_finish":
                    await writeFile(
                        path.join(directory, "report.json"),
                        JSON.stringify(
                            {
                                ...args.report,
                                checkpoints: [...labels],
                                unexpectedRequests: unexpected,
                            },
                            null,
                            2,
                        ),
                    );
                    finish(args.report.passed && unexpected.length === 0);
                    return null;
                default:
                    throw new Error("Forbidden");
            }
        },
    );
    await page.addInitScript(() => {
        window.__TAURI__ = {
            core: {
                invoke: (command, args) =>
                    window.__localLoreAppHarness(command, args),
            },
        };
        window.__LOCALLORE_TEST__ = {
            enabled: true,
            backend: "headless",
            stage: location.search === "?reopened=1" ? "reopened" : "initial",
        };
    });
    let timeout;
    try {
        await page.goto("http://locallore.test/", {
            waitUntil: "domcontentloaded",
        });
        const pass = await Promise.race([
            finished,
            new Promise((_, reject) => {
                timeout = setTimeout(
                    () => reject(new Error("HarnessTimeout")),
                    180_000,
                );
            }),
        ]);
        if (!pass) throw new Error("JourneysFailed");
    } finally {
        clearTimeout(timeout);
        await browser.close();
        await bridge.close();
    }
}
const report = JSON.parse(
    await readFile(path.join(directory, "report.json"), "utf8"),
);
const required = [
    "initial",
    "play-accepted",
    "play-rejected",
    "pending",
    "cancelled",
    "retry",
    "failed",
    "malformed",
    "stale",
    "session-switch",
    "receipt",
    "observer",
    "play-return",
    "narrow",
    "enlarged",
    "reopened",
    "close",
    "copy",
    "pagination",
    "injection",
    "disposed",
];
const files = await readdir(directory);
for (const label of required)
    if (!files.includes(label + ".json"))
        throw new Error("MissingCheckpoint:" + label);
if (!report.passed) throw new Error("JourneysFailed");
const snapshots = await Promise.all(
    required.map(async (label) =>
        JSON.parse(
            await readFile(path.join(directory, label + ".json"), "utf8"),
        ),
    ),
);
const checks = [...new Set(snapshots.flatMap((s) => s.checks ?? []))];
const inputs = [
    "ui/controller.ts",
    "ui/model.ts",
    "ui/journeys.ts",
    "ui/App.tsx",
    "ui/main.tsx",
    "ui/style.css",
    "ui/host.generated.ts",
    "host-v1.schema.json",
    "package-lock.json",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/test_bridge.rs",
    "src-tauri/tauri.conf.json",
    "src-tauri/Cargo.lock",
    "src-tauri/Cargo.toml",
    "build.mjs",
    "harness.mjs",
    "dist/app.js",
    "src-tauri/target/debug/locallore-desktop-spike.exe",
    "../../crates/locallore/src/host.rs",
];
const hashes = Object.fromEntries(
    await Promise.all(
        inputs.map(async (file) => [
            file,
            createHash("sha256")
                .update(await readFile(path.join(root, file)))
                .digest("hex"),
        ]),
    ),
);
await writeFile(
    path.join(directory, "summary.json"),
    JSON.stringify(
        {
            synthetic: true,
            passed: true,
            backend: mode,
            sourceRevision,
            sourceDirty,
            checkpoints: required.length,
            checks,
            inputSHA256: hashes,
            rendering:
                mode === "native"
                    ? "See per-checkpoint CapturePreview results"
                    : "headless Chromium only; real Rust stdio host, not native WebView IPC",
            desktopControl: false,
        },
        null,
        2,
    ),
);
console.log(
    `D02 ${mode.toUpperCase()} PASS: ${required.length} checkpoints, ${checks.length} assertions. Local artifacts: ${directory}`,
);
