// Parse the prepared workflow with the already locked frontend YAML dependency.
// This is a source policy check, not a hosted-run or security-approval substitute.
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";
const require = createRequire(
    new URL("../apps/desktop/package.json", import.meta.url),
);
const { load } = require("js-yaml");
const text = readFileSync(
    new URL("../.github/workflows/desktop.yml", import.meta.url),
    "utf8",
);
const workflow = load(text);
assert.deepEqual(Object.keys(workflow.on).sort(), ["pull_request", "push"]);
assert.deepEqual(workflow.on.push.branches, ["main"]);
assert.deepEqual(workflow.permissions, { contents: "read" });
assert.deepEqual(Object.keys(workflow.jobs), ["windows-x64"]);
assert.deepEqual(workflow.defaults, { run: { shell: "pwsh" } });
assert.deepEqual(workflow.env, {
    CARGO_PROFILE_DEV_DEBUG: "0",
    CARGO_PROFILE_TEST_DEBUG: "0",
    CARGO_INCREMENTAL: "0",
    PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD: "1",
});
const job = workflow.jobs["windows-x64"];
assert.equal(job["runs-on"], "windows-2025");
assert.equal(job["timeout-minutes"], 45);
const actions = job.steps.filter((step) => step.uses);
assert.deepEqual(
    actions.map((step) => step.uses),
    [
        "actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1",
        "actions/setup-node@820762786026740c76f36085b0efc47a31fe5020",
        "actions/setup-python@5fda3b95a4ea91299a34e894583c3862153e4b97",
    ],
);
assert.equal(actions[0].with["persist-credentials"], false);
assert.equal(actions[1].with["node-version"], "24.22.1");
assert.equal(actions[1].with["package-manager-cache"], false);
assert.equal(actions[2].with["python-version"], "3.14.9");
const runs = job.steps.filter((step) => step.run).map((step) => step.run);
assert(
    runs.every((run) => !run.includes("${{")),
    "Untrusted expression in run script",
);
const fixture = runs.findIndex(
    (run) =>
        run.startsWith(
            "cargo +1.93.1 build --manifest-path crates/locallore-local-runtime/Cargo.toml",
        ) && run.includes("--bin protocol-fixture"),
);
const tests = runs.findIndex(
    (run) =>
        run.startsWith(
            "cargo +1.93.1 test --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets",
        ) && run.includes("--features development-worker,engine-adapter"),
);
const clippy = runs.findIndex(
    (run) =>
        run.startsWith(
            "cargo +1.93.1 clippy --manifest-path crates/locallore-local-runtime/Cargo.toml --all-targets",
        ) &&
        run.includes("--features development-worker,engine-adapter") &&
        run.endsWith("-- -D warnings"),
);
assert(
    fixture >= 0 && tests > fixture && clippy > tests,
    "Standalone runtime needs fixture, all-target tests and Clippy in order",
);
assert(runs.at(-1).includes("--no-default-features"));
assert(runs.at(-1).endsWith("-- -C link-arg=/Brepro"));
for (const forbidden of [
    "pull_request_target",
    "self-hosted",
    "secrets.",
    "upload-artifact",
    "download-artifact",
    "write-all",
    "contents: write",
    "--features scene-probe",
    "npm run harness",
])
    assert(!text.includes(forbidden), `Forbidden CI policy: ${forbidden}`);
console.log(
    "PASS: desktop workflow parses; pinned read-only Windows tools, complete standalone runtime gate and normal final link policy.",
);
