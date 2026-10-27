// FIRST source freeze: UNCOMPILED / UNRUN. Closed synthetic native launcher.
// No desktop input, window activation, screen capture, model assets or downloads.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir, lstat, realpath } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";

if (process.argv.length !== 2) throw Error("ClosedSceneHarnessArgumentsRequired");
const root = fileURLToPath(new URL(".", import.meta.url));
async function ownedDirectory(value) {
    if (!value || !path.isAbsolute(value)) throw Error("TrustedOwnedDirectoryRequired");
    const resolved = path.resolve(value);
    if ((await realpath(resolved)).toLowerCase() !== resolved.toLowerCase()) throw Error("UnsafeOwnedDirectory");
    for (let current = resolved; ; current = path.dirname(current)) {
        const info = await lstat(current);
        if (!info.isDirectory() || info.isSymbolicLink()) throw Error("UnsafeOwnedDirectory");
        if (path.dirname(current) === current) break;
    }
    return resolved;
}
const artifactRoot = await ownedDirectory(process.env.LOCALLORE_M07_MEMORY_ARTIFACT_ROOT);
const targetRoot = await ownedDirectory(process.env.LOCALLORE_M07_MEMORY_TARGET_DIR);
if ((process.env.LIBSQLITE3_FLAGS ?? "").trim()) throw Error("OrdinaryUncappedSQLiteRequired");
const folder = path.join(artifactRoot, `scene-native-cohort-${randomUUID()}`);
await mkdir(folder); // Never reuse, remove or recursively clean an existing directory.
const executable = path.join(targetRoot, "debug", "locallore-desktop-spike.exe");
const git = promisify(execFile);
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const sourceRevision = (await git("git", ["rev-parse", "HEAD"], { cwd: root })).stdout.trim();
const sourceDirty = !!(await git("git", ["status", "--porcelain"], { cwd: root })).stdout.trim();
const sourceInputs = [
    "scene-harness.mjs", "ui/scene-native-journeys.ts", "ui/main.tsx", "ui/controller.ts",
    "ui/model.ts", "ui/journeys.ts", "ui/v2-play-controller.ts", "ui/v2-view-model.ts",
    "ui/V2PlayPanel.tsx", "ui/App.tsx", "ui/style.css", "build.mjs", "package.json", "package-lock.json",
    "src-tauri/src/main.rs", "src-tauri/src/harness.rs", "src-tauri/src/scene_harness.rs",
    "src-tauri/src/models.rs", "src-tauri/src/lease.rs", "src-tauri/src/shutdown.rs",
    "src-tauri/Cargo.toml", "src-tauri/build.rs", "src-tauri/tauri.conf.json", "../../Cargo.lock",
    "../../fixtures/lantern_quay.json", "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs", "../../crates/locallore/src/engine/staged_scene_play.rs",
    "../../crates/locallore/src/play.rs", "../../crates/locallore/src/play/scene_narration.rs",
    "../../crates/locallore/src/play/scene_narration/renderer.rs",
    "../../crates/locallore/src/inspection_query_v2.rs", "../../crates/locallore/src/author_correction.rs",
    "../../crates/locallore-workspace/src/lib.rs", "../../crates/locallore-storage/src/lib.rs",
];
async function currentHashes(files) {
    return Object.fromEntries(await Promise.all(files.map(async (file) => [file,
        hash(await readFile(path.isAbsolute(file) ? file : path.join(root, file)))])));
}
const startInputSHA256 = await currentHashes(sourceInputs);
async function unchangedSource() {
    if ((await git("git", ["rev-parse", "HEAD"], { cwd: root })).stdout.trim() !== sourceRevision
        || (await git("git", ["status", "--porcelain"], { cwd: root })).stdout.trim()
        || JSON.stringify(await currentHashes(sourceInputs)) !== JSON.stringify(startInputSHA256))
        throw Error("SceneHarnessSourceChanged");
}
let builtProducts = null;
async function unchangedProducts() {
    if (!builtProducts || JSON.stringify(await currentHashes(["dist/app.js", executable])) !== JSON.stringify(builtProducts))
        throw Error("SceneHarnessProductChanged");
}
Object.assign(process.env, { CARGO_BUILD_JOBS: "1", CARGO_PROFILE_DEV_DEBUG: "0",
    CARGO_PROFILE_TEST_DEBUG: "0", CARGO_INCREMENTAL: "0" });
let runNumber = 0;
async function run(command, args, env = {}) {
    await unchangedSource();
    if (command === executable) {
        if (args.length) throw Error("ClosedNativeArgumentsRequired");
        await unchangedProducts();
    }
    const log = `run-${++runNumber}`, started = new Date().toISOString();
    const inherited = { ...process.env }, bounded = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    for (const key of Object.keys(inherited)) if (key.startsWith("LOCALLORE_") && /HARNESS|TEST_|ARTIFACT_DIR/.test(key)) delete inherited[key];
    let timedOut = false, truncated = false;
    const result = await new Promise((resolve) => {
        const child = spawn(command, args, { cwd: root, stdio: ["ignore", "pipe", "pipe"], windowsHide: true,
            shell: false, env: { ...inherited, ...env } });
        for (const channel of ["stdout", "stderr"]) child[channel].on("data", (chunk) => {
            const available = 262144 - bounded[channel].length;
            if (chunk.length > available) truncated = true;
            if (available > 0) bounded[channel] = Buffer.concat([bounded[channel], chunk.subarray(0, available)]);
        });
        const timer = setTimeout(() => { timedOut = true; child.kill(); }, command === "cargo" ? 900000 : 240000);
        child.once("error", (error) => { clearTimeout(timer); resolve({ code: null, signal: null, error: error.code ?? "SpawnFailure" }); });
        child.once("close", (code, signal) => { clearTimeout(timer); resolve({ code, signal, error: null }); });
    });
    for (const channel of ["stdout", "stderr"]) await writeFile(path.join(folder, `${log}-${channel}.log`), bounded[channel], { flag: "wx" });
    await writeFile(path.join(folder, `${log}-process.json`), JSON.stringify({ ...result, timedOut, truncated,
        command: command === executable ? "<owned-target>/debug/locallore-desktop-spike.exe" : command,
        args, sourceRevision, started, ended: new Date().toISOString() }, null, 2), { flag: "wx" });
    await unchangedSource();
    if (command === executable) await unchangedProducts();
    if (result.code !== 0 || timedOut || truncated) throw Error(`SceneHarnessChildFailure:${log}`);
}
await writeFile(path.join(folder, "source-manifest.json"), JSON.stringify({ version: 1, synthetic: true,
    qualification: "pending", sourceRevision, sourceDirty, node: process.version, inputSHA256: startInputSHA256,
    backend: "native", desktopControl: false, realModelGeneration: false }, null, 2), { flag: "wx" });
if (sourceDirty) throw Error("CleanCommittedSceneSourceRequired");
console.log(`SCENE native local artifacts: ${folder}`);
const labels = {
    initial: ["ready", "receipt", "receipt-diff", "pending", "cancelled", "unknown", "recovered", "switched", "observer", "enlarged"].map((s) => `scene-native-${s}`),
    restart: ["scene-native-restarted", "scene-native-recorded-diff"],
};
const reports = [], artifacts = {}, checks = new Set();
let originalError = null, candidateSummary = null, normalRestoration = null;
try {
    await run(process.execPath, ["build.mjs", "--harness"]);
    await run("cargo", ["build", "--manifest-path", "src-tauri/Cargo.toml", "--locked", "--offline",
        "--features", "dev-harness", "--bin", "locallore-desktop-spike", "--jobs", "1", "--target-dir", targetRoot]);
    builtProducts = await currentHashes(["dist/app.js", executable]);
    await writeFile(path.join(folder, "product-manifest.json"), JSON.stringify({ sourceRevision, productSHA256: builtProducts }, null, 2), { flag: "wx" });
    for (const sceneCase of ["literal", "memory"]) {
        const caseFolder = path.join(folder, `scene-native-${randomUUID()}`);
        await mkdir(caseFolder);
        const db = path.join(caseFolder, "stories-v1.sqlite");
        let firstOracle = null;
        for (const stage of ["initial", "restart"]) {
            const directory = path.join(caseFolder, stage);
            // run() clears every inherited harness/test control before these
            // fixed flags. No renderer selects a workspace, policy or provider.
            await run(executable, [], { LOCALLORE_D02_HARNESS: "1", LOCALLORE_D04_SCENE_HARNESS: sceneCase,
                LOCALLORE_TEST_MEMORY: "0", LOCALLORE_TEST_WORKSPACE: db,
                LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0", LOCALLORE_D02_ARTIFACT_DIR: directory });
            const filenames = await readdir(directory), bytes = await readFile(path.join(directory, "report.json"));
            if (bytes.length > 262144) throw Error("SceneReportBudget");
            const report = JSON.parse(bytes.toString("utf8"));
            if (report.synthetic !== true || report.passed !== true || report.stage !== stage || report.sceneCase !== sceneCase
                || report.realModelGeneration !== false || report.nativeIpc !== true || report.rendering !== "native-webview2"
                || report.desktopControl !== false || !Array.isArray(report.checks)) throw Error(`SceneJourneysFailed:${sceneCase}:${stage}:${report.failedCheck ?? "Report"}`);
            for (const check of report.checks) { if (typeof check !== "string") throw Error("InvalidSceneCheck"); checks.add(`${sceneCase}:${check}`); }
            const proof = report.finalOracle;
            if (!proof || proof.case !== sceneCase || proof.new_commits !== 5 || proof.head !== (sceneCase === "literal" ? 6 : 7)
                || proof.untouched_preserved !== true || proof.other_preserved !== true || proof.observer_isolated !== true
                || proof.real_model !== false) throw Error("SceneFinalStoreProof");
            if (stage === "initial") firstOracle = proof;
            else if (proof.canonical_sha256 !== firstOracle.canonical_sha256
                || JSON.stringify(proof.observer_sha256) !== JSON.stringify(firstOracle.observer_sha256)
                || proof.fixture_factories !== 0 || proof.fixture_polls !== 0) throw Error("SceneColdReopenMismatch");
            const actual = filenames.filter((name) => name.endsWith(".png")).map((name) => name.slice(0, -4)).sort();
            if (JSON.stringify(actual) !== JSON.stringify([...labels[stage]].sort())) throw Error("SceneCaptureLabels");
            const permitted = new Set(["report.json", ...labels[stage].flatMap((label) => [`${label}.png`, `${label}.json`, `${label}.capture.json`])]);
            if (filenames.some((name) => !permitted.has(name))) throw Error("UnexpectedSceneArtifact");
            for (const name of permitted) {
                const data = await readFile(path.join(directory, name));
                if (data.length > (name.endsWith(".png") ? 16777216 : 262144)) throw Error("SceneArtifactBudget");
                artifacts[`${sceneCase}/${stage}/${name}`] = { bytes: data.length, sha256: hash(data) };
                if (name.endsWith(".capture.json")) {
                    const capture = JSON.parse(data.toString("utf8"));
                    if (capture.rendering !== "native-webview2" || capture.synthetic !== true
                        || !labels[stage].includes(capture.label)) throw Error("SceneNotNativeRendering");
                } else if (name.endsWith(".png")) {
                    if (!data.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))) throw Error("ScenePngHeader");
                } else if (name !== "report.json") {
                    const snapshot = JSON.parse(data.toString("utf8"));
                    if (snapshot.synthetic !== true || !Number.isSafeInteger(snapshot.uiRevision)
                        || snapshot.aggregate?.revision !== snapshot.uiRevision || !snapshot.v2 || !snapshot.oracle
                        || !Array.isArray(snapshot.dom?.structure) || snapshot.dom.structure.length > 256
                        || typeof snapshot.dom.text !== "string" || snapshot.dom.text.length > 48000
                        || snapshot.provider?.kind !== "synthetic_fixture") throw Error("SceneSemanticSnapshot");
                }
            }
            reports.push({ sceneCase, stage, path: path.relative(folder, directory), checks: report.checks.length, proof });
        }
    }
    await unchangedSource(); await unchangedProducts();
    candidateSummary = { synthetic: true, backend: "native", desktopControl: false, realModelGeneration: false,
        actualProcessRestart: true, sourceRevision, sourceDirty, node: process.version,
        captures: 24, checks: [...checks], reports, artifacts, inputSHA256: startInputSHA256,
        harnessProductSHA256: builtProducts, limitations: ["fixed synthetic Wait-only scene fixture", "no real-model quality or human assessment", "no offline/device qualification"] };
} catch (error) { originalError = error; }
finally {
    // Restore exactly the normal frontend/app without launching that image,
    // including after failed setup, journey, artifact or product checks.
    try {
        await run(process.execPath, ["build.mjs"]);
        await run("cargo", ["build", "--manifest-path", "src-tauri/Cargo.toml", "--locked", "--offline",
            "--no-default-features", "--bin", "locallore-desktop-spike", "--jobs", "1", "--target-dir", targetRoot]);
        normalRestoration = { passed: true, launched: false, productSHA256: await currentHashes(["dist/app.js", executable]) };
    } catch (error) {
        normalRestoration = { passed: false, launched: false, error: String(error?.message ?? error).slice(0, 500) };
        originalError ??= error;
    }
    await writeFile(path.join(folder, "normal-restoration.json"), JSON.stringify(normalRestoration, null, 2), { flag: "wx" });
}
if (originalError || !candidateSummary || normalRestoration?.passed !== true) {
    await writeFile(path.join(folder, "failure-observation.json"), JSON.stringify({ sourceRevision, passed: false,
        ended: new Date().toISOString(), error: String(originalError?.message ?? "SceneIncomplete").slice(0, 500),
        normalRestoration, terminalSourceRevision: (await git("git", ["rev-parse", "HEAD"], { cwd: root })).stdout.trim(),
        terminalDirty: (await git("git", ["status", "--porcelain"], { cwd: root })).stdout.trim(),
        reports, artifacts }, null, 2), { flag: "wx" });
    throw originalError ?? Error("SceneIncomplete");
}
await writeFile(path.join(folder, "summary.json"), JSON.stringify({ ...candidateSummary, passed: true, normalRestoration }, null, 2), { flag: "wx" });
console.log(`SCENE NATIVE PASS: ${checks.size} assertions,24 application-owned captures; local artifacts: ${folder}`);
