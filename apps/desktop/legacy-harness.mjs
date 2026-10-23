// Fixed reconstructed synthetic-v1 native migration; no desktop input/model/SQL endpoint.
import { spawn, execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, readdir, symlink } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { randomUUID, createHash } from "node:crypto";
import assert from "node:assert/strict";
const exec = promisify(execFile);
const root = fileURLToPath(new URL(".", import.meta.url));
const folder = path.join(
    process.env.LOCALLORE_DESKTOP_ARTIFACT_ROOT ?? path.join(root, "artifacts"),
    `legacy-native-${randomUUID()}`,
);
await mkdir(folder, { recursive: true });
const fixture = path.join(folder, "legacy-fixture"),
    database = path.join(fixture, "stories-v1.sqlite");
const target =
    process.env.LOCALLORE_DESKTOP_TARGET_DIR ??
    path.join(root, "src-tauri", "target");
const executable = path.join(target, "debug", "locallore-desktop-spike.exe");
const helper = path.join(
    target,
    "debug",
    "examples",
    "native_legacy_workspace.exe",
);
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const readJSON = async (file) => JSON.parse(await readFile(file, "utf8"));
async function run(command, args, env = {}) {
    await new Promise((resolve, reject) => {
        const child = spawn(command, args, {
            cwd: root,
            stdio: "inherit",
            shell: false,
            env: { ...process.env, ...env },
        });
        const timer = setTimeout(() => child.kill(), 240000);
        child.once("error", reject);
        child.once("exit", (code) => {
            clearTimeout(timer);
            code === 0 ? resolve() : reject(new Error(`ChildExit${code}`));
        });
    });
}
await run("cargo", [
    "build",
    "--manifest-path",
    "../../Cargo.toml",
    "-p",
    "locallore-storage",
    "--example",
    "native_legacy_workspace",
    "--features",
    "development-fixtures",
    "--locked",
    "--offline",
    "--target-dir",
    target,
]);
const seeded = JSON.parse(
    (await exec(helper, ["create", fixture], { cwd: root, timeout: 30000 }))
        .stdout,
);
assert.equal(seeded.schema_version, 1);
assert.equal(seeded.revision, 1);
assert.equal(seeded.receipts, 1);
await writeFile(
    path.join(folder, "seed.json"),
    JSON.stringify(seeded, null, 2),
);
const checks = ["fixed-owner-seeded-actual-v1-before-app-start"];
let refused = false;
try {
    await exec(helper, ["create", fixture], { cwd: root, timeout: 30000 });
} catch (error) {
    refused =
        error.code === 1 &&
        error.stderr.trim() === "NewFixtureDirectoryRequired";
}
assert(refused);
assert.equal(hash(await readFile(database)), seeded.database_sha256);
checks.push("fixture-create-refuses-existing-directory-without-mutation");
const reparseTarget = path.join(folder, "reparse-target"),
    reparseParent = path.join(folder, "reparse-parent");
await mkdir(reparseTarget);
await symlink(reparseTarget, reparseParent, "junction");
refused = false;
try {
    await exec(helper, ["create", path.join(reparseParent, "legacy-fixture")], {
        cwd: root,
        timeout: 30000,
    });
} catch (error) {
    refused =
        error.code === 1 && error.stderr.trim() === "FixtureReparseRefused";
}
assert(refused);
assert.deepEqual(await readdir(reparseTarget), []);
checks.push("fixture-create-refuses-junction-parent-without-target-writes");
await run(process.execPath, ["build.mjs", "--harness"]);
await run("cargo", [
    "build",
    "--manifest-path",
    "src-tauri/Cargo.toml",
    "--locked",
    "--offline",
    "--features",
    "dev-harness",
    "--target-dir",
    target,
]);
const sourceRevision = (
    await exec("git", ["rev-parse", "HEAD"], { cwd: root })
).stdout.trim();
const sourceDirty =
    (await exec("git", ["status", "--porcelain"], { cwd: root })).stdout.trim()
        .length > 0;
const reports = [],
    verification = [];
let captures = 0;
for (const stage of ["initial", "restart"]) {
    const directory = path.join(folder, stage);
    await run(executable, [], {
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_TEST_MEMORY: "0",
        LOCALLORE_TEST_WORKSPACE: database,
        LOCALLORE_D02_ARTIFACT_DIR: directory,
        LOCALLORE_M07_LEGACY_HARNESS: "1",
        LOCALLORE_TEST_RESTART: stage === "restart" ? "1" : "0",
    });
    const report = await readJSON(path.join(directory, "report.json"));
    assert.equal(
        report.passed,
        true,
        `LegacyNativeFailed:${stage}:${report.failedCheck}`,
    );
    reports.push({ stage, report });
    checks.push(...report.checks);
    for (const name of await readdir(directory)) {
        if (name.endsWith(".png")) captures++;
        if (name.endsWith(".capture.json"))
            assert.equal(
                (await readJSON(path.join(directory, name))).rendering,
                "native-webview2",
            );
    }
    const verified = JSON.parse(
        (await exec(helper, ["verify", fixture], { cwd: root, timeout: 30000 }))
            .stdout,
    );
    assert.equal(verified.backup_count, 1);
    assert.equal(verified.backup.schema_version, 1);
    assert.equal(verified.live.schema_version, 2);
    for (const value of [verified.live, verified.backup]) {
        assert.equal(value.canonical_sha256, seeded.canonical_sha256);
        assert.equal(value.receipt_sha256, seeded.receipt_sha256);
        assert.equal(value.revision, 1);
        assert.equal(value.receipts, 1);
        assert(value.read_only_unchanged);
    }
    if (verification.length) assert.deepEqual(verified, verification[0].report);
    await writeFile(
        path.join(folder, `verify-${stage}.json`),
        JSON.stringify(verified, null, 2),
    );
    verification.push({ stage, report: verified });
}
checks.push(
    "actual-app-migrates-v1-to-v2-with-one-readonly-v1-backup",
    "migration-and-restart-retain-exact-original-canonical-state-and-receipt",
    "restart-retains-same-backup-bytes-and-no-extra-backup",
    "readonly-backup-verification-does-not-mutate-any-database",
);
const files = [
    "legacy-harness.mjs",
    "ui/legacy-journeys.ts",
    "ui/main.tsx",
    "ui/App.tsx",
    "ui/model.ts",
    "ui/controller.ts",
    "verify-frontend.mjs",
    "host-v1.schema.json",
    "ui/host.generated.ts",
    "src-tauri/src/main.rs",
    "src-tauri/src/harness.rs",
    "src-tauri/src/lease.rs",
    "src-tauri/src/test_bridge.rs",
    "src-tauri/Cargo.toml",
    "../../Cargo.lock",
    "../../crates/locallore-storage/Cargo.toml",
    "../../crates/locallore-storage/examples/native_legacy_workspace.rs",
    "../../crates/locallore-storage/migrations/001_initial.sql",
    "../../crates/locallore-storage/src/lib.rs",
    "../../crates/locallore-storage/src/catalog.rs",
    "../../crates/locallore-storage/src/turns.rs",
    "../../crates/locallore-workspace/src/lib.rs",
    "../../crates/locallore/src/host.rs",
    "../../crates/locallore/src/engine.rs",
    "dist/app.js",
    executable,
    helper,
];
const inputSHA256 = Object.fromEntries(
    await Promise.all(
        files.map(async (file) => [
            path.isAbsolute(file)
                ? `<native-target>/debug/${file === helper ? "examples/native_legacy_workspace.exe" : "locallore-desktop-spike.exe"}`
                : file,
            hash(
                await readFile(
                    path.isAbsolute(file) ? file : path.join(root, file),
                ),
            ),
        ]),
    ),
);
await writeFile(
    path.join(folder, "summary.json"),
    JSON.stringify(
        {
            synthetic: true,
            reconstructedV1: true,
            releasedAppHistoricalSave: false,
            passed: true,
            backend: "native",
            desktopControl: false,
            realModelGeneration: false,
            actualProcessRestart: true,
            sourceRevision,
            sourceDirty,
            captures,
            checks: [...new Set(checks)],
            reports,
            verification,
            inputSHA256,
        },
        null,
        2,
    ),
);
console.log(
    `LEGACY NATIVE PASS: ${new Set(checks).size} assertions, ${captures} captures, actual synthetic-v1 migration and process restart. Local artifacts: ${folder}`,
);
