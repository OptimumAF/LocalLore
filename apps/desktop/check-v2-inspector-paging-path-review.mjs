// Independent fixed-path FIRST. SOURCE ONLY / UNCOMPILED / UNRUN at freeze.
// Actual launcher block in a VM, with path.win32 and a fixed UUID dependency.
// No filesystem, child, fixture, database, native app or OS path-limit execution.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { createHash } from "node:crypto";
import { runInNewContext } from "node:vm";
import path from "node:path";

const sourceUrl = new URL("./v2-inspector-paging-harness.mjs", import.meta.url);
const UUID = "d05a1234-5abc-4def-8abc-123456789abc";
const BASE = "D:\\CodexLocalLore\\01a165d9-ff25-7500-a550-1099087d4e37\\author-integration-artifacts\\d05-v2-inspector-paging-20261029-v1";
const hash = (bytes) => createHash("sha256").update(bytes).digest("hex");
const plain = (value) => JSON.parse(JSON.stringify(value));
const setup = [], cases = [], results = [];
const register = (group, name, body) => cases.push({ group, name, body });
let source = "", block = null, blockStart = -1, blockEnd = -1;
try { source = await readFile(sourceUrl, "utf8"); }
catch (error) { setup.push({ stage: "actual-launcher-source", error: String(error?.code ?? "SourceUnavailable"), classification: "UNRUN_SETUP; no behavioral result" }); }
if (!setup.length) try {
    const start = "// d05-paging-path-policy-v1:start", end = "// d05-paging-path-policy-v1:end";
    blockStart = source.indexOf(start); blockEnd = source.indexOf(end, blockStart + start.length);
    assert(blockStart >= 0 && blockEnd > blockStart && source.indexOf(start, blockStart + start.length) < 0 && source.indexOf(end, blockEnd + end.length) < 0, "UniqueActualPathBlock");
    block = source.slice(blockStart + start.length, blockEnd);
    assert.match(block, /\bfunction\s+fixedPagingWorkspace\s*\(\s*folder\s*,\s*identifier\s*\)/, "ActualFixedWorkspaceHelper");
    assert.match(block, /\bconst\s+folder\s*=\s*path\.join\(\s*base\s*,\s*`p-\$\{randomUUID\(\)\}`\s*,?\s*\)/, "ActualShortFixedPacketLeaf");
} catch (error) { setup.push({ stage: "actual-path-block-extraction", error: String(error?.message ?? error).slice(0, 500), classification: "UNRUN_SETUP; missing helper/seam is not behavioral RED" }); }

function actual(base = BASE) {
    let draws = 0;
    const api = runInNewContext(`(() => { "use strict"; ${block}\nreturn {folder,fixedPagingWorkspace}; })()`, { path: path.win32, base, randomUUID: () => { draws++; return UUID; } }, { timeout: 1000 });
    assert.equal(typeof api.fixedPagingWorkspace, "function", "ActualCallablePathHelper");
    return { api, draws: () => draws };
}
function expected(folder, identifier = UUID) {
    const workspace = path.win32.join(folder, `d05-v2-inspector-paging-native-${identifier}`);
    return { workspace, database: path.win32.join(workspace, "stories-v1.sqlite") };
}
// Input-string construction only, not a replacement implementation of the guard.
function folderForDatabaseLength(length, unicode = false) {
    const suffix = expected("D:\\p-" + UUID).database.slice(("D:\\p-" + UUID).length);
    const padding = length - suffix.length - "D:\\".length - ("\\p-" + UUID).length;
    assert(padding > 0);
    const leaf = unicode ? "\u{1f642}".repeat(Math.floor(padding / 2)) + "a".repeat(padding % 2) : "a".repeat(padding);
    const folder = `D:\\${leaf}\\p-${UUID}`;
    assert.equal(expected(folder).database.length, length);
    return folder;
}

register("actual-caller", "one-planned-call-before-admission-packet-mkdir-no-fallback", () => {
    const budget = source.indexOf("// d05-paging-budget-policy-v1:start"), mkdir = source.indexOf("await mkdir(folder");
    assert(budget > blockEnd && mkdir > budget, "ActualPathPreflightBeforeAdmissionAndCreation");
    // Count actual helper call syntax; discard only its declaration. No copied
    // initializer, prescribed local result name or general JS parser/evaluator.
    const calls = [...source.matchAll(/\bfixedPagingWorkspace\s*\(/g)].filter((match) => !/\bfunction\s*$/.test(source.slice(Math.max(0, match.index - 30), match.index)));
    assert.equal(calls.length, 1, "ExactlyOneActualPlannedWorkspaceSelection");
    assert(calls[0].index < budget && calls[0].index < mkdir, "ActualWorkspaceCallerBeforeAnyPacketCreation");
});
register("actual-block", "actual-current-base-short-packet-leaf-with-fixed-UUID", () => {
    const h = actual(); assert.equal(h.api.folder, path.win32.join(BASE, `p-${UUID}`));
    // A caller inside the block may select the one workspace identifier too.
    assert(h.draws() === 1 || h.draws() === 2, "FixedPacketPlusOptionalSingleWorkspaceIdentifier");
});
for (const identifier of [UUID, "0e87b1c0-cafe-4567-8abc-111111111111"]) register("actual-schema", `exact-workspace-and-database-leaf:${identifier}`, () => {
    const h = actual(), result = h.api.fixedPagingWorkspace(h.api.folder, identifier), wanted = expected(h.api.folder, identifier);
    assert.deepEqual(plain(result), wanted); assert.deepEqual(Object.keys(result).sort(), ["database", "workspace"]);
    assert.equal(result.database.length, 244, "MeasuredCurrentBaseStringUses244UTF16Units");
    assert.equal((result.database + "-journal").length, 252); assert((result.database + "-journal").length < 260);
});
register("actual-schema", "explicit-helper-does-not-redraw-or-change-fixed-folder", () => {
    const h = actual(), before = h.draws(), folder = h.api.folder;
    const first = h.api.fixedPagingWorkspace(folder, UUID), second = h.api.fixedPagingWorkspace(folder, UUID);
    assert.deepEqual(plain(first), plain(second)); assert.equal(h.draws(), before); assert.equal(h.api.folder, folder);
});
for (const length of [247, 248, 249, 260, 512]) register("UTF16-boundary", `ASCII-database-${length}`, () => {
    const h = actual(), folder = folderForDatabaseLength(length);
    if (length <= 248) { const result = h.api.fixedPagingWorkspace(folder, UUID); assert.deepEqual(plain(result), expected(folder)); assert.equal(result.database.length, length); }
    else assert.throws(() => h.api.fixedPagingWorkspace(folder, UUID), "Over248RefusesWithoutShorterOrAlternatePathFallback");
});
for (const length of [248, 249]) register("UTF16-boundary", `surrogate-pair-database-${length}`, () => {
    const h = actual(), folder = folderForDatabaseLength(length, true), wanted = expected(folder);
    assert(wanted.database.length > [...wanted.database].length, "ActualTestStringContainsUTF16SurrogatePairs");
    assert(Buffer.byteLength(wanted.database, "utf8") > wanted.database.length, "UTF8LengthIsNotTheContract");
    if (length === 248) assert.deepEqual(plain(h.api.fixedPagingWorkspace(folder, UUID)), wanted);
    else assert.throws(() => h.api.fixedPagingWorkspace(folder, UUID), "UTF16LimitCannotBeReplacedByCodepointCount");
});
for (const [name, identifier] of [
    ["empty", ""], ["uppercase", UUID.toUpperCase()], ["no-hyphens", UUID.replaceAll("-", "")],
    ["short", UUID.slice(0, -1)], ["long", UUID + "0"], ["leading-space", " " + UUID], ["trailing-space", UUID + " "],
    ["path-prefix", "../" + UUID], ["nonhex", UUID.replace("d", "g")], ["wrong-separator", UUID.replace("-", "_")],
    ["null", null], ["undefined", undefined], ["number", 17], ["object", {}], ["array", []],
]) register("UUID-refusal", name, () => { const h = actual(); assert.throws(() => h.api.fixedPagingWorkspace(h.api.folder, identifier)); });
for (const [name, folder] of [
    ["empty", ""], ["relative", "relative"], ["packet-only", `p-${UUID}`], ["dot-relative", ".\\packet"],
    ["parent-relative", "..\\packet"], ["drive-relative", "D:packet"], ["null", null], ["undefined", undefined],
    ["number", 1], ["boolean", false], ["object", {}],
]) register("folder-refusal", name, () => { const h = actual(); assert.throws(() => h.api.fixedPagingWorkspace(folder, UUID)); });

if (block && !setup.length) try { actual(); }
catch (error) { setup.push({ stage: "actual-block-vm-registration", error: String(error?.message ?? error).slice(0, 500), classification: "UNRUN_SETUP; actual block not registered" }); }
for (const item of cases) {
    if (setup.length) continue;
    try { await item.body(); results.push({ group: item.group, name: item.name, passed: true }); }
    catch (error) { results.push({ group: item.group, name: item.name, passed: false, error: String(error?.message ?? error).slice(0, 600) }); }
}
if (source) assert.equal(hash(await readFile(sourceUrl, "utf8")), hash(source), "ActualLauncherSourceUnchanged");
const report = { version: 1, kind: "d05_v2_inspector_paging_path_first_v1", sourceSHA256: source ? hash(source) : null, actualBlockSHA256: block ? hash(block) : null,
    setup, authored: cases.length, executed: results.length, passed: results.filter((item) => item.passed).length, failed: results.filter((item) => !item.passed).length,
    groups: Object.fromEntries([...new Set(cases.map((item) => item.group))].map((group) => [group, cases.filter((item) => item.group === group).length])), checks: results,
    evidence: "Actual future launcher block with path.win32/fixed fake UUID, plus actual caller source-order inspection. String/VM evidence only.",
    limits: ["SOURCE author did not compile/execute this check. Root separately registers/runs.", "No filesystem, database, Store pinning, MAX_PATH behavior, SQLite sidecar, native fixture, IPC, WebView or desktop execution is proven.", "The real-base244/sidecar252 figures are UTF16 string calculations, not a successful database creation.", "Physical D/ordinary ancestor/alias safety remains the existing native/launcher guards; this helper only preflights the declared string limit.", "Original failed269-character native packet and old245 policy cases remain unchanged; no retry or new runtime budget is admitted.", "Missing source/marker/helper or VM registration is nonpassing UNRUN_SETUP, never zero-case PASS or behavioral RED."] };
console.log(JSON.stringify(report));
if (setup.length || report.failed || report.executed !== report.authored) process.exitCode = 1;
