// Fixed app-owned WebView2 journeys. No desktop capture, input, dialogs or model.
import assert from "node:assert/strict";
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import {
    mkdir,
    readFile,
    writeFile,
    readdir,
    lstat,
    realpath,
} from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";

if (process.argv.length !== 2)
    throw Error("ClosedComparisonReaderArgumentsRequired");
// reader-policy-v1:start
function readerDiagnosticMode(environment) {
    const pick = (name) => {
        const keys = Object.keys(environment).filter(key => key.toUpperCase() === name);
        if (keys.length > 1) throw Error("AmbiguousReaderModeAlias");
        return keys.length ? environment[keys[0]] : undefined;
    };
    const diagnostic = pick("LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER");
    const scene = pick("LOCALLORE_D07_SCENE_COMPARISON_READER");
    const literal = pick("LOCALLORE_D07_LITERAL_COMPARISON_READER");
    if (diagnostic !== undefined && diagnostic !== "0" && diagnostic !== "1")
        throw Error("ClosedDiagnosticReaderModeRequired");
    if (diagnostic !== "1") return false;
    if (scene !== "1" || (literal !== undefined && literal !== "0"))
        throw Error("DiagnosticSceneReaderModeRequired");
    return true;
}
function readerChildEnvironment(environment) {
    return Object.fromEntries(Object.entries(environment).filter(([key]) => !/^LOCALLORE_/i.test(key)));
}
// reader-policy-v1:end
process.env.TEMP = "D:/Dev/_Temp";
process.env.TMP = "D:/Dev/_Temp";
const diagnosticMode = readerDiagnosticMode(process.env);
const root = fileURLToPath(new URL(".", import.meta.url));
const literalMode = process.env.LOCALLORE_D07_LITERAL_COMPARISON_READER === "1";
const sceneMode = diagnosticMode || process.env.LOCALLORE_D07_SCENE_COMPARISON_READER === "1";
if (literalMode && sceneMode)
    throw Error("ExclusiveComparisonReaderModeRequired");
const protocolVersion = sceneMode ? 4 : literalMode ? 3 : 2;
async function ownedDirectory(value) {
    if (!value || !path.isAbsolute(value))
        throw Error("TrustedOwnedDirectoryRequired");
    const resolved = path.resolve(value);
    if (path.parse(resolved).root.toLowerCase() !== "d:\\")
        throw Error("PhysicalDOwnedDirectoryRequired");
    if ((await realpath(resolved)).toLowerCase() !== resolved.toLowerCase())
        throw Error("UnsafeOwnedDirectory");
    for (let current = resolved; ; current = path.dirname(current)) {
        const info = await lstat(current);
        if (!info.isDirectory() || info.isSymbolicLink())
            throw Error("UnsafeOwnedDirectory");
        if (path.dirname(current) === current) break;
    }
    return resolved;
}
await ownedDirectory(root);
const base = await ownedDirectory(
    process.env.LOCALLORE_D07_COMPARISON_READER_ARTIFACT_ROOT,
);
const target = await ownedDirectory(
    process.env.LOCALLORE_D07_COMPARISON_READER_TARGET_DIR,
);
if ((process.env.LIBSQLITE3_FLAGS ?? "").trim())
    throw Error("OrdinaryUncappedSQLiteRequired");
const folder = path.join(base, `comparison-reader-native-${randomUUID()}`);
await mkdir(folder, { recursive: false });
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const digest = (bytes) => createHash("sha256").update(bytes).digest("hex");
const git = promisify(execFile);
const revision = (
    await git("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
assert.equal(
    (
        await git("git", ["status", "--porcelain"], {
            cwd: root,
        })
    ).stdout.trim(),
    "",
    "CleanSourceRequired",
);
const sourceFiles = [
    "comparison-reader-harness.mjs",
    "ui/comparison-reader-model.ts",
    "ui/comparison-reader-controller.ts",
    "ui/ComparisonReaderPanel.tsx",
    "ui/comparison-reader-journeys.ts",
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/style.css",
    "ui/controller.ts",
    "ui/model.ts",
    "ui/index.html",
    "ui/host.generated.ts",
    "host-v1.schema.json",
    "build.mjs",
    ".prettierrc.json",
    "package.json",
    "package-lock.json",
    "src-tauri/src/comparison_commands.rs",
    "src-tauri/src/comparison_reader_harness.rs",
    "src-tauri/src/evaluation.rs",
    "src-tauri/src/evaluation/comparison.rs",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/build.rs",
    "src-tauri/Cargo.toml",
    "src-tauri/tauri.conf.json",
    "../../Cargo.lock",
    "../../crates/locallore-eval/src/memory_comparison_v4.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/scene_v4.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/scene_v4/desktop_api.rs",
    "../../crates/locallore-eval/src/local_lane/comparison/desktop_api.rs",
    "../../crates/locallore-eval/src/scene_capture_v1.rs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs",
    "../../crates/locallore/src/play/scene_narration.rs",
    "../../crates/locallore-storage/src/lib.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    ...(diagnosticMode ? [
        "../../crates/locallore-eval/src/narration_diagnostic_companion_v1.rs",
        "../../crates/locallore-eval/src/local_lane/comparison.rs",
        "../../crates/locallore-eval/src/local_lane/comparison/turn_execution.rs",
        "../../crates/locallore-eval/src/local_lane/comparison/selected.rs",
        "src-tauri/src/models.rs",
    ] : []),
];
async function hashes(files) {
    return Object.fromEntries(
        await Promise.all(
            files.map(async (file) => [
                file,
                digest(
                    await readFile(
                        path.isAbsolute(file) ? file : path.join(root, file),
                    ),
                ),
            ]),
        ),
    );
}
const initialSourceHashes = await hashes(sourceFiles);
async function unchangedSource() {
    if (
        (
            await git("git", ["rev-parse", "HEAD"], { cwd: root })
        ).stdout.trim() !== revision ||
        (
            await git("git", ["status", "--porcelain"], { cwd: root })
        ).stdout.trim() ||
        JSON.stringify(await hashes(sourceFiles)) !==
            JSON.stringify(initialSourceHashes)
    )
        throw Error("ComparisonReaderSourceChanged");
}
let builtProducts = null;
const productFiles = [
    "dist/app.js",
    "dist/style.css",
    "dist/index.html",
    executable,
];
async function unchangedProducts() {
    if (
        !builtProducts ||
        JSON.stringify(await hashes(productFiles)) !==
            JSON.stringify(builtProducts)
    )
        throw Error("ComparisonReaderProductChanged");
}
const executions = [];
let ownedDrainUnknown = false;
const unknownOwnedChildren = [];
async function run(label, command, args, env = {}, limit = 240000) {
    if (ownedDrainUnknown) throw Error("ComparisonReaderOwnedDrainUnknown");
    await unchangedSource();
    if (command === executable) {
        if (args.length) throw Error("ClosedNativeArgumentsRequired");
        await unchangedProducts();
    }
    const started = new Date().toISOString();
    const output = { stdout: Buffer.alloc(0), stderr: Buffer.alloc(0) };
    const inherited = diagnosticMode ? readerChildEnvironment(process.env) : { ...process.env };
    if (!diagnosticMode) for (const key of Object.keys(inherited))
        if (
            key.startsWith("LOCALLORE_") &&
            /HARNESS|TEST_|ARTIFACT_DIR|COMPARISON_READER/.test(key)
        )
            delete inherited[key];
    let directPid = null,
        directKillAttempted = false,
        directKillReturned = null,
        directKillError = null,
        overflow = false,
        timedOut = false;
    const maximum = 256 * 1024;
    const result = await new Promise((resolve) => {
        const child = spawn(command, args, {
            cwd: root,
            shell: false,
            windowsHide: true,
            stdio: ["ignore", "pipe", "pipe"],
            env: {
                ...inherited,
                CARGO_BUILD_JOBS: "1",
                CARGO_INCREMENTAL: "0",
                CARGO_PROFILE_DEV_DEBUG: "0",
                CARGO_PROFILE_TEST_DEBUG: "0",
                ...env,
                TEMP: "D:/Dev/_Temp",
                TMP: "D:/Dev/_Temp",
            },
        });
        directPid = child.pid ?? null;
        let settled = false,
            grace = null;
        const unknown = (reason) => {
            if (!ownedDrainUnknown)
                unknownOwnedChildren.push({
                    label,
                    pid: directPid,
                    reason,
                    processTreeContained: false,
                });
            ownedDrainUnknown = true;
        };
        const finish = (value, detach = false) => {
            if (settled) return;
            settled = true;
            clearTimeout(timer);
            if (grace !== null) clearTimeout(grace);
            if (detach) {
                child.stdout.destroy();
                child.stderr.destroy();
                child.unref();
            }
            resolve(value);
        };
        for (const channel of ["stdout", "stderr"])
            child[channel].on("data", (chunk) => {
                const available = maximum - output[channel].length;
                if (chunk.length > available) overflow = true;
                if (available > 0)
                    output[channel] = Buffer.concat([
                        output[channel],
                        chunk.subarray(0, available),
                    ]);
            });
        const timer = setTimeout(() => {
            timedOut = true;
            // A direct-child close never proves descendant drain. Fail closed;
            // there is no Job/process-tree containment or timeout qualification.
            unknown("TimeoutDirectChildOnly");
            grace = setTimeout(
                () =>
                    finish(
                        {
                            exit: null,
                            signal: null,
                            closed: false,
                            error: "OwnedDrainUnknown",
                        },
                        true,
                    ),
                5000,
            );
            directKillAttempted = true;
            try {
                directKillReturned = child.kill();
            } catch (error) {
                directKillError = error?.code ?? "KillFailure";
            }
        }, limit);
        child.once("error", (error) => {
            if (settled) return;
            if (directPid !== null) unknown("ChildErrorWithPid");
            finish(
                {
                    exit: null,
                    signal: null,
                    closed: false,
                    error: error.code ?? "SpawnFailure",
                },
                directPid !== null,
            );
        });
        child.once("close", (exit, signal) => {
            finish({ exit, signal, closed: true, error: null });
        });
    });
    await writeFile(path.join(folder, `${label}.stdout.log`), output.stdout, {
        flag: "wx",
    });
    await writeFile(path.join(folder, `${label}.stderr.log`), output.stderr, {
        flag: "wx",
    });
    const entry = {
        label,
        command,
        args,
        started,
        ended: new Date().toISOString(),
        ...result,
        timedOut,
        overflow,
        directPid,
        directKillAttempted,
        directKillReturned,
        directKillError,
        ownedDrainUnknown,
        unknownOwnedChildren,
        processTreeContained: false,
        sourceRevision: revision,
        stdoutBytes: output.stdout.length,
        stderrBytes: output.stderr.length,
    };
    executions.push(entry);
    await writeFile(
        path.join(folder, "executions.json"),
        JSON.stringify(executions, null, 2),
    );
    if (ownedDrainUnknown)
        throw Error(`ComparisonReaderOwnedDrainUnknown:${label}`);
    await unchangedSource();
    if (command === executable) await unchangedProducts();
    assert(!timedOut, `${label}:owned-process-timeout`);
    assert(!overflow, `${label}:bounded-output-overflow`);
    assert.equal(result.exit, 0, `${label}:exit`);
}
let readerInventoryStats = null;
async function inventory(directory) {
    const files = {};
    let bytes = 0, entries = 0;
    async function visit(current, depth) {
        assert(depth <= 8, "FixtureDepth");
        entries++;
        if (diagnosticMode) assert(entries <= 8192, "DiagnosticFixtureEntryBudget");
        for (const name of (await readdir(current)).sort()) {
            const full = path.join(current, name),
                stat = await lstat(full);
            assert(!stat.isSymbolicLink(), "FixtureLink");
            if (stat.isDirectory()) await visit(full, depth + 1);
            else {
                entries++;
                if (diagnosticMode) assert(entries <= 8192, "DiagnosticFixtureEntryBudget");
                assert(
                    stat.isFile() && stat.size <= 8 * 1024 * 1024,
                    "FixtureFileBudget",
                );
                bytes += stat.size;
                assert(Number.isSafeInteger(bytes) && bytes <= (diagnosticMode ? 128 : 64) * 1024 * 1024, "FixtureTotalBudget");
                assert(Object.keys(files).length < (diagnosticMode ? 8192 : 2048), "FixtureCountBudget");
                files[
                    path.relative(directory, full).replaceAll(path.sep, "/")
                ] = digest(await readFile(full));
            }
        }
    }
    await visit(directory, 0);
    readerInventoryStats = { entries, files: Object.keys(files).length, bytes };
    return files;
}
async function modelCandidateAbsent() {
    try {
        await lstat(path.join(folder, "models"));
        throw Error("DiagnosticModelDirectoryUnexpected");
    } catch (error) {
        if (error.code !== "ENOENT") throw error;
    }
}
const reports = [];
const artifacts = {};
async function checkedArtifact(file, maximum) {
    const info = await lstat(file);
    assert(
        info.isFile() && !info.isSymbolicLink() && info.size <= maximum,
        "ReaderArtifactBudget",
    );
    const bytes = await readFile(file);
    assert(bytes.length <= maximum, "ReaderArtifactBudget");
    artifacts[path.relative(folder, file).replaceAll(path.sep, "/")] = {
        bytes: bytes.length,
        sha256: digest(bytes),
    };
    return bytes;
}
async function artifactJson(file) {
    return JSON.parse(
        (await checkedArtifact(file, 256 * 1024)).toString("utf8"),
    );
}
let expectedFixtures = null,
    expectedDiagnosticFreeze = null,
    originalError = null,
    normalRestoration = null,
    candidateSummary = null;
await writeFile(
    path.join(folder, "source-manifest.json"),
    JSON.stringify(
        {
            version: 1,
            sourceRevision: revision,
            sourceClean: true,
            protocolVersion,
            ...(diagnosticMode ? { diagnosticReader: true } : {}),
            synthetic: true,
            modelExecution: false,
            inputSHA256: initialSourceHashes,
            node: process.version,
        },
        null,
        2,
    ),
    { flag: "wx" },
);
console.log(`COMPARISON READER local artifacts: ${folder}`);
try {
    await run("frontend-build", process.execPath, ["build.mjs", "--harness"]);
    await run(
        "native-build",
        "cargo",
        [
            "build",
            "--manifest-path",
            "src-tauri/Cargo.toml",
            "--locked",
            "--offline",
            "--features",
            "dev-harness",
            "--jobs",
            "1",
            "--target-dir",
            target,
        ],
        {},
        900000,
    );
    builtProducts = await hashes(productFiles);
    await writeFile(
        path.join(folder, "product-manifest.json"),
        JSON.stringify(
            { sourceRevision: revision, productSHA256: builtProducts },
            null,
            2,
        ),
        { flag: "wx" },
    );
    if (diagnosticMode) await modelCandidateAbsent();
    for (const stage of ["initial", "restart"]) {
        const directory = path.join(folder, stage);
        await run(
            `app-${stage}`,
            executable,
            [],
            {
                LOCALLORE_D02_HARNESS: "1",
                LOCALLORE_D03_HARNESS: "0",
                LOCALLORE_D04_HARNESS: "0",
                LOCALLORE_D05_HARNESS: "0",
                LOCALLORE_D06_HARNESS: "0",
                LOCALLORE_D06_CAPTURE_HARNESS: "0",
                LOCALLORE_D07_HARNESS: "0",
                LOCALLORE_D07_CURATED_HARNESS: "0",
                LOCALLORE_D08_HARNESS: "0",
                LOCALLORE_D08_TIMELINE_HARNESS: "0",
                LOCALLORE_D08_FORK_HARNESS: "0",
                LOCALLORE_M07_LEGACY_HARNESS: "0",
                LOCALLORE_M07_MEMORY_HARNESS: "0",
                LOCALLORE_M08_AUTHOR_HARNESS: "0",
                LOCALLORE_TEST_STORAGE_FAILURE: "0",
                LOCALLORE_D07_COMPARISON_READER_HARNESS: "1",
                LOCALLORE_D07_LITERAL_COMPARISON_READER: literalMode
                    ? "1"
                    : "0",
                LOCALLORE_D07_SCENE_COMPARISON_READER: sceneMode ? "1" : "0",
                ...(diagnosticMode ? { LOCALLORE_D07_NARRATION_DIAGNOSTIC_READER: "1" } : {}),
                LOCALLORE_D02_ARTIFACT_DIR: directory,
                LOCALLORE_TEST_MEMORY: "0",
                LOCALLORE_TEST_WORKSPACE: path.join(
                    folder,
                    "stories-v1.sqlite",
                ),
                LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
            },
            sceneMode ? 960000 : 240000,
        );
        const report = await artifactJson(path.join(directory, "report.json"));
        reports.push({ stage, report });
        if (diagnosticMode && report.passed !== true)
            throw Error(`Journeys:${stage}:${report.failedCheck ?? "IncompleteDiagnosticReader"}`);
        if (diagnosticMode) {
            await modelCandidateAbsent();
            assert.equal(report.diagnosticReader, true, "ClosedDiagnosticReaderJourney");
            assert.equal(report.modelObservation.reservation_sequence, 0);
            assert.equal(report.modelObservation.owner_present, false);
            assert.equal(report.modelObservation.retained_evaluations, 0);
            assert.equal(report.diagnosticPendingImage, "unavailable_no_io_hold_seam");
            assert.equal(report.pendingImage, "held_picker_only");
            const codes = report.expectedDiagnosticErrors.map(e => [e.action, e.code]);
            assert.deepEqual(codes, stage === "restart" ? [] : [
                ["direct_actor_diagnostic_denial", "Forbidden"],
                ["malformed_companion_refusal", "EvaluationIntegrity"],
            ], "ActualBoundedExpectedRefusals");
            assert.deepEqual(report.errors, report.expectedDiagnosticErrors.flatMap(e => e.broker_delta), "ExpectedErrorsAreNotZeroedOrRelabeled");
        }
        assert.equal(
            report.passed,
            true,
            `Journeys:${stage}:${report.failedCheck}`,
        );
        assert.equal(report.realModelGeneration, false, "SyntheticReaderOnly");
        assert.equal(report.nativeIpc, true, "ActualNativeReaderPathsRequired");
        assert.equal(
            report.protocolVersion,
            protocolVersion,
            "ActualReportProtocolRequired",
        );
        const opened = await artifactJson(
            path.join(
                directory,
                stage === "restart"
                    ? "comparison-restarted.json"
                    : "comparison-open.json",
            ),
        );
        assert(
            opened.fixtureInventory &&
                Object.keys(opened.fixtureInventory).length > 0,
            "ActualProducerInventoryRequired",
        );
        assert.equal(
            opened.comparison.source.protocol_version,
            protocolVersion,
            "ActualClosedReaderProtocol",
        );
        assert.equal(
            opened.comparison.summaryProjection.report.version,
            protocolVersion,
            "ActualReportProtocol",
        );
        if (diagnosticMode) {
            const proof = opened.diagnosticFixtureProof;
            assert.equal(proof.kind, "narration_diagnostic_reader_fixture_v1");
            assert.equal(proof.version, 1); assert.equal(proof.protocol_version, 4); assert.equal(proof.synthetic, true);
            assert.deepEqual(proof.fixtures.map(f => f.id), ["diagnostic-recorded", "diagnostic-legacy", "diagnostic-missing", "diagnostic-unavailable", "diagnostic-rejected", "diagnostic-malformed"]);
            assert.deepEqual(proof.fixtures.map(f => [f.expected_status, f.expected_error]), [["recorded",null],["no_declaration",null],["no_observation",null],["host_unavailable",null],["host_rejected",null],[null,"EvaluationIntegrity"]]);
            assert.deepEqual(proof.inventory_limits, { entries:8192, bytes:128*1024*1024, file_bytes:8*1024*1024, depth:8 });
            assert.equal(opened.comparison.source.rows.length, 12);
        } else if (sceneMode) {
            const proof = opened.fixtureProof;
            assert.equal(
                proof?.source_gate,
                "fresh_domain1_committed_narrator_input_only",
                "ActualSceneFixtureProof",
            );
            for (const [lane, rows] of [
                ["paired", 24],
                ["rollout", 12],
            ]) {
                assert.equal(proof[lane].rows, rows, "FixedSceneRows");
                assert.equal(
                    proof[lane].source_matches,
                    true,
                    "ActualSceneSourceMatch",
                );
                assert.equal(
                    proof[lane].human_reviewed,
                    0,
                    "NoInventedHumanReview",
                );
                assert.equal(
                    proof[lane].quality_accepted,
                    false,
                    "NoQualityAcceptance",
                );
                assert.equal(
                    proof[lane].models_executed,
                    false,
                    "NoModelsInFixture",
                );
                assert.equal(
                    proof[lane].execution_available,
                    false,
                    "ReaderNeverGrantsExecution",
                );
            }
            assert.equal(
                opened.comparison.summaryProjection.report
                    .source_bound_committed_rows,
                proof.paired.source_bound_committed_rows,
                "ActualSourceBoundInputCountPreserved",
            );
        }
        const actual = await inventory(
            path.join(folder, "comparison-fixtures"),
        );
        if (diagnosticMode) {
            assert.deepEqual(readerInventoryStats, opened.diagnosticFixtureProof.inventory_stats, "ActualCompleteSixFixtureInventoryStats");
            const frozen=await artifactJson(path.join(folder,"diagnostic-reader-fixtures-v1.json"));
            assert.deepEqual(frozen.fixture_inventory, actual, "ExternalFrozenInventoryMatchesAllBytes");
            const freezeHash=artifacts["diagnostic-reader-fixtures-v1.json"].sha256;
            if(expectedDiagnosticFreeze)assert.equal(freezeHash,expectedDiagnosticFreeze,"RestartPreservesExternalFreezeBytes");
            expectedDiagnosticFreeze=freezeHash;
        }
        assert.deepEqual(
            actual,
            opened.fixtureInventory,
            `CompleteFixtureBytesUnchanged:${stage}`,
        );
        if (expectedFixtures)
            assert.deepEqual(
                actual,
                expectedFixtures,
                "RestartPreservesEveryOriginalFixtureByte",
            );
        expectedFixtures = actual;
        const captures = (await readdir(directory)).filter((name) =>
            name.endsWith(".png"),
        );
        const labels = (diagnosticMode && stage === "restart" ? ["restarted", "finished"] : [
            stage === "restart" ? "restarted" : "open",
            "receipt",
            "capture",
            "outputs",
            "narrow",
            "mira",
            "sable",
            "guard",
            "pending",
            "closed",
            "unknown",
            "recovered",
            "rollout",
            "switched",
            "finished",
        ]).map((name) => `comparison-${name}`);
        assert.deepEqual(
            captures.slice().sort(),
            labels.map((name) => `${name}.png`).sort(),
            `ActualWebViewImages:${stage}`,
        );
        const permitted = new Set([
            "report.json",
            ...labels.flatMap((label) => [
                `${label}.png`,
                `${label}.json`,
                `${label}.capture.json`,
            ]),
        ]);
        assert(
            (await readdir(directory)).every((name) => permitted.has(name)),
            "ClosedReaderArtifactRoster",
        );
        for (const name of captures) {
            const png = await checkedArtifact(
                path.join(directory, name),
                16 * 1024 * 1024,
            );
            assert(
                png.length <= 16 * 1024 * 1024 &&
                    png
                        .subarray(0, 8)
                        .equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10])),
                "BoundedActualPng",
            );
            const capture = await artifactJson(
                path.join(directory, name.replace(/\.png$/, ".capture.json")),
            );
            assert.equal(
                capture.rendering,
                "native-webview2",
                `ActualNativeRendering:${name}`,
            );
            assert.equal(capture.label, name.slice(0, -4), "ExactCaptureLabel");
            const snapshot = await artifactJson(
                path.join(directory, name.replace(/\.png$/, ".json")),
            );
            assert.equal(
                snapshot.semanticVersion,
                2,
                `SemanticVersion:${name}`,
            );
            const state = snapshot.comparison;
            if (diagnosticMode) {
                const label=name.slice(0,-4);
                const expectedSource={"comparison-open":"diagnostic-recorded","comparison-restarted":"diagnostic-recorded",
                    "comparison-receipt":"diagnostic-recorded","comparison-capture":"diagnostic-unavailable",
                    "comparison-outputs":"diagnostic-rejected","comparison-narrow":"diagnostic-recorded",
                    "comparison-mira":"diagnostic-recorded","comparison-sable":"diagnostic-recorded",
                    "comparison-guard":"diagnostic-missing","comparison-rollout":"diagnostic-legacy",
                    "comparison-pending":"diagnostic-recorded","comparison-closed":"diagnostic-recorded",
                    "comparison-unknown":"diagnostic-malformed","comparison-recovered":"diagnostic-recorded",
                    "comparison-switched":"diagnostic-recorded","comparison-finished":"diagnostic-recorded"};
                assert.equal(snapshot.diagnosticProvenance.source, expectedSource[label], "ExactCaptureSourceMapping");
                assert.equal(report.diagnosticCaptures[label].provenance, snapshot.diagnosticProvenance.provenance);
                const expectedStatus={"comparison-open":"recorded","comparison-restarted":"recorded",
                    "comparison-capture":"host_unavailable","comparison-outputs":"host_rejected",
                    "comparison-narrow":"recorded","comparison-guard":"no_observation",
                    "comparison-rollout":"no_declaration","comparison-recovered":"recorded"}[label];
                assert.deepEqual(snapshot.diagnostic, state.diagnostic);
                if (expectedStatus) assert.equal(state.diagnostic?.diagnostic.status, expectedStatus, "ActualFiveStatusCapture");
                else assert.equal(state.diagnostic, null, "NoDiagnosticLeakIntoClearedOrErrorCapture");
                if (label === "comparison-unknown") assert.equal(state.error, "EvaluationIntegrity");
                if (["comparison-mira","comparison-sable"].includes(label)) {
                    assert.equal(snapshot.observer.kind, "character");
                    assert.equal(state.summaryProjection, null); assert.equal(state.evidence, null);
                }
                assert.deepEqual(snapshot.diagnosticGeometryFailures, [], "ActualContextGeometryAndHitTests");
                assert(snapshot.diagnosticGeometry.context.length > 0, "ActualFinitePositiveContextGeometry");
            }
            const selected = state.source?.rows.find(
                (row) =>
                    row.row.turn === state.selected?.turn &&
                    row.row.arm === state.selected?.arm,
            );
            assert.deepEqual(
                snapshot.selectedStory,
                selected?.source.scope ?? null,
                `ExperimentScope:${name}`,
            );
            assert.equal(
                snapshot.gameplayContext.revision,
                snapshot.uiRevision,
                `GameplayRevision:${name}`,
            );
            assert.equal(
                snapshot.visibleError,
                state.error,
                `VisibleError:${name}`,
            );
            assert.equal(
                snapshot.selectedReport,
                state.status?.run_token ?? null,
                `ReportToken:${name}`,
            );
            const evidence = state.evidence;
            const revision = evidence
                ? evidence.body.kind === "query"
                    ? evidence.body.page.revision
                    : evidence.edge === "before"
                      ? evidence.before_head
                      : evidence.edge === "after"
                        ? evidence.after_head
                        : null
                : (selected?.source.after_head ?? null);
            assert.equal(
                snapshot.revision,
                revision,
                `InspectionRevision:${name}`,
            );
            assert.deepEqual(
                snapshot.displayedReceipt,
                evidence?.body.kind === "receipt"
                    ? evidence.body.receipt
                    : null,
                `DisplayedReceipt:${name}`,
            );
            if (evidence) {
                assert.deepEqual(
                    snapshot.observer,
                    evidence.observer,
                    `DisplayedObserver:${name}`,
                );
                assert.deepEqual(
                    snapshot.selectedStory,
                    evidence.scope,
                    `DisplayedScope:${name}`,
                );
                if (evidence.body.kind === "query") {
                    assert.equal(
                        evidence.edge,
                        state.querySelection.edge,
                        `QueryEdge:${name}`,
                    );
                    assert.equal(
                        evidence.body.page.view,
                        state.querySelection.view,
                        `QueryView:${name}`,
                    );
                    const selectedValues = snapshot.dom.controls
                        .filter((control) => control.tag === "SELECT")
                        .map((control) => control.value);
                    assert(
                        selectedValues.includes(state.querySelection.edge) &&
                            selectedValues.includes(state.querySelection.view),
                        `ActualControlSelection:${name}`,
                    );
                }
            }
            if (state.status?.running)
                assert.equal(
                    snapshot.pendingOperation?.id,
                    state.status.operation_id,
                    `ActualPendingOperation:${name}`,
                );
            else if (state.uncertain) {
                assert.equal(
                    snapshot.pendingOperation?.id,
                    null,
                    `UnknownPendingIdentity:${name}`,
                );
                assert.equal(
                    snapshot.pendingOperation?.phase,
                    "acknowledgement_unknown",
                    `UnknownPendingPhase:${name}`,
                );
            } else if (state.busy)
                assert.equal(
                    snapshot.pendingOperation?.id,
                    null,
                    `UnobservedPendingIdentity:${name}`,
                );
            else
                assert.equal(
                    snapshot.pendingOperation,
                    null,
                    `NoInventedPendingOperation:${name}`,
                );
        }
    }
    await unchangedSource();
    await unchangedProducts();
    candidateSummary = {
        version: 1,
        passed: true,
        sourceRevision: revision,
        sourceClean: true,
        protocolVersion,
        ...(diagnosticMode ? { diagnosticReader: true, inventoryStats: readerInventoryStats,
            inventoryLimits:{entries:8192,bytes:128*1024*1024,file_bytes:8*1024*1024,depth:8},
            modelDirectoryAbsentAfterExit:true, externalFreezeSha256:expectedDiagnosticFreeze,
            captureProvenance:reports.map(item=>({stage:item.stage,captures:item.report.diagnosticCaptures})),
            expectedErrorEvidence:reports.map(item=>({stage:item.stage,errors:item.report.errors,expected:item.report.expectedDiagnosticErrors})) } : {}),
        synthetic: true,
        nativeIpc: true,
        rendering: "actual-hidden-unfocused-webview2",
        desktopInput: false,
        nativeDialogsAutomated: false,
        modelExecution: false,
        executions,
        reports,
        artifacts,
        fixtureFiles: Object.keys(expectedFixtures).length,
        fixtureInventory: expectedFixtures,
        executableSha256: builtProducts[executable],
        harnessProductSHA256: builtProducts,
        inputSHA256: initialSourceHashes,
        limitations: [
            "Synthetic scripted inference only",
            "Fixed native picker doubles; OS dialogs not automated",
            sceneMode
                ? "Protocol4 selected-case rerun and comparison execution unavailable"
                : "Read-only reader; selected controls remain separate",
            "Native handle/ack recovery is in memory",
            "Access-time expiry does not guarantee wall-clock release",
            "Whole-report snapshot is last validated at open; selected evidence is refreshed",
            "Native images require separate visual inspection",
            "No Job/process-tree containment or timeout-drain qualification",
            ...(diagnosticMode ? ["Diagnostic pending image unavailable; picker-pending image only",
                "Stored unavailable/rejected/malformed fixtures are trusted metadata controls",
                "seq0/no owner/retained0 are ModelManager observations, not independent SDK-load telemetry",
                "Ordinary shutdown metadata-probes the absent task-owned models candidate; no zero-path-probe claim",
                "Six-fixture collector8192entries/128MiB is separate from unchanged Core run/namespace/library quotas"] : []),
        ],
    };
} catch (error) {
    originalError = error;
} finally {
    if (ownedDrainUnknown) {
        normalRestoration = {
            passed: false,
            launched: false,
            skipped: true,
            error: "OwnedDrainUnknown",
            processTreeContained: false,
            unknownOwnedChildren,
        };
    } else {
        try {
            await run("normal-frontend-restoration", process.execPath, [
                "build.mjs",
            ]);
            await run(
                "normal-native-restoration",
                "cargo",
                [
                    "build",
                    "--manifest-path",
                    "src-tauri/Cargo.toml",
                    "--locked",
                    "--offline",
                    "--no-default-features",
                    "--bin",
                    "locallore-desktop-spike",
                    "--jobs",
                    "1",
                    "--target-dir",
                    target,
                ],
                {},
                900000,
            );
            normalRestoration = {
                passed: true,
                launched: false,
                productSHA256: await hashes(productFiles),
            };
        } catch (error) {
            normalRestoration = {
                passed: false,
                launched: false,
                error: String(error?.message ?? error).slice(0, 500),
                remainingStepsSkipped: ownedDrainUnknown,
                processTreeContained: false,
                unknownOwnedChildren,
            };
            originalError ??= error;
        }
    }
    await writeFile(
        path.join(folder, "normal-restoration.json"),
        JSON.stringify(normalRestoration, null, 2),
        { flag: "wx" },
    );
}
if (originalError || !candidateSummary || normalRestoration?.passed !== true) {
    await writeFile(
        path.join(folder, "failure-observation.json"),
        JSON.stringify(
            {
                sourceRevision: revision,
                passed: false,
                protocolVersion,
                error: String(
                    originalError?.message ?? "IncompleteReaderCohort",
                ).slice(0, 500),
                executions,
                reports,
                artifacts,
                ownedDrainUnknown,
                unknownOwnedChildren,
                normalRestoration,
            },
            null,
            2,
        ),
        { flag: "wx" },
    );
    throw originalError ?? Error("IncompleteReaderCohort");
}
await writeFile(
    path.join(folder, "qualification.json"),
    JSON.stringify({ ...candidateSummary, normalRestoration }, null, 2),
    { flag: "wx" },
);
console.log(
    JSON.stringify({
        passed: true,
        artifactDirectory: folder,
        sourceRevision: revision,
        stages: reports.length,
        nativeIpc: true,
        modelExecution: false,
    }),
);
