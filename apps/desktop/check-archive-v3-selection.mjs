// Frozen D08.01/.05 source-only oracles, base88fbab7568c505359f11fddb2bf2c1ac7b997cdf.
// UNRUN at freeze. Root owns execution: node check-archive-v3-selection.mjs
// Real ArchivePanel + React SSR + ArchiveController, synthetic native gateway.
// No DOM, WebView, native IPC/authority, App/main mount or actual grant proof.
// Capture the actual JSX-created props during real SSR; never call a hooked
// component directly or replace its decisions with a test implementation.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import { createHash, randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";

const root = fileURLToPath(new URL(".", import.meta.url));
const output = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const cohort = randomUUID();
const panelSource = await readFile(path.join(root, "ui/ArchivePanel.tsx"), "utf8");
const panelSha256 = createHash("sha256").update(panelSource).digest("hex");
const built = await build({
    stdin: {
        contents: 'export {ArchivePanel} from "./ui/ArchivePanel";export {ArchiveController} from "./ui/archive-controller";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";export {created} from "selection-review-elements";',
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
    jsx: "transform",
    jsxFactory: "__selectionElement",
    jsxFragment: "__selectionFragment",
    plugins: [{
        name: "capture-real-panel-elements",
        setup(plugin) {
            plugin.onResolve({ filter: /^selection-review-elements$/ }, () => ({ path: "elements", namespace: "selection-review" }));
            plugin.onLoad({ filter: /.*/, namespace: "selection-review" }, () => ({
                contents: 'import {createElement,Fragment} from "react";export const created=[];export const __selectionFragment=Fragment;export function __selectionElement(type,props,...children){const element=createElement(type,props,...children);created.push(element);return element;}',
                loader: "js",
                resolveDir: root,
            }));
            plugin.onLoad({ filter: /[\\/]ArchivePanel\.tsx$/ }, async ({ path: filename }) => ({
                contents: 'import {__selectionElement,__selectionFragment} from "selection-review-elements";\n' + await readFile(filename, "utf8"),
                loader: "tsx",
                resolveDir: path.dirname(filename),
            }));
        },
    }],
});
const bundle = path.join(output, `archive-v3-selection-${cohort}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents);
const { ArchivePanel, ArchiveController, createElement, renderToStaticMarkup, created } = (await import(pathToFileURL(bundle).href)).default;
const clone = (value) => structuredClone(value);
const scope = { story: "synthetic-selection", branch: "corrected" };
const context = "selected-session|lab|omniscient";
const token = "11111111-1111-1111-1111-111111111111";
const terminal = (result) => ({ version: 1, operation_id: 17, running: false, phase: "completed", error: null, result });
const preview = () => ({
    version: 1, token, kind: "export", warning: "Full private whole story snapshot; explicit consent required.",
    preview: {
        version: 3, story_id: scope.story, title: "Synthetic corrected story", root_branch: "main",
        branch_heads: { main: 1, corrected: 7 }, committed_turns: 3, bytes: 1024,
        payload_sha256: "a".repeat(64),
        privacy_warning: "Full private accepted records include author corrections, reasons, prior truth and private discovery source bindings.",
        noncommitted_workflow_transferred: false,
    },
});
const thin = () => ({
    version: 2, domain_version: 2, scope: clone(scope), revision: 7, rules: "fantasy_v1",
    player: { observer: "player", self_state: { name: "Rowan", location: "quay", alive: true, energy: 2, abilities: {}, attributes: {}, injuries: [], affiliations: [], goals: [] } },
    inventory: {},
});
function deferred() {
    let resolve;
    const promise = new Promise((r) => { resolve = r; });
    return { promise, resolve };
}
async function settle() {
    // Bounded microtask drainage for immediate synthetic gateways, no sleeps.
    for (let n = 0; n < 24; n++) await Promise.resolve();
}
function fixture({ domain = 2, allowed = true, answer } = {}) {
    const calls = [];
    const session = { id: "selected-session", scope: clone(scope), revision: 99 };
    // Cached session revision deliberately differs: export uses coherent play head7.
    const state = domain === 2 ? { play: null, playV2: thin() } : {
        play: { scope: clone(scope), revision: 7, receipts: [], inventory: {}, player: { observer: "player" } }, playV2: null,
    };
    const gameplay = {
        get: () => state,
        selected: () => session,
        library: async () => { assert.fail("Export must not refresh/import/open a story"); },
        resume: async () => { assert.fail("Export must never automatically select a story"); },
    };
    const archive = new ArchiveController(async (name, args = {}) => {
        calls.push({ name, args: clone(args) });
        if (name === "archive_discard" || name === "archive_cancel") return null;
        return answer ? answer(name, args) : terminal(preview());
    }, gameplay.library);
    archive.contextChanged(context, allowed);
    archive.show();
    function render({ key = context, permitted = allowed } = {}) {
        created.length = 0;
        const html = renderToStaticMarkup(createElement(ArchivePanel, { archive, controller: gameplay, context: key, allowed: permitted }));
        return { html, elements: [...created] };
    }
    return { calls, session, state, gameplay, archive, render };
}
function text(node) {
    if (node === null || node === undefined || typeof node === "boolean") return "";
    if (Array.isArray(node)) return node.map(text).join("");
    if (typeof node === "object") return text(node.props?.children);
    return String(node);
}
function button(rendered, label) {
    const found = rendered.elements.filter((element) => element.type === "button" && text(element.props.children) === label);
    assert.equal(found.length, 1, `Expected one actual rendered ${label} button`);
    return found[0].props;
}
const cases = [];
const test = (name, run) => cases.push({ name, run });

test("selected Domain2-only snapshot enables actual private export button", () => {
    const f = fixture();
    const rendered = f.render();
    assert.equal(f.state.play, null);
    assert.equal(f.state.playV2.domain_version, 2);
    assert.equal(Boolean(button(rendered, "Preview private export").disabled), false);
    assert.equal(f.calls.length, 0, "Rendering must not dispatch native work");
});
test("actual Domain2 export handler sends exact selected session scope and coherent head", async () => {
    const f = fixture();
    const action = button(f.render(), "Preview private export");
    assert.equal(Boolean(action.disabled), false);
    action.onClick();
    await settle();
    assert.deepEqual(f.calls, [{ name: "archive_export_preview", args: { session: f.session.id, scope, expectedRevision: 7 } }]);
    assert.equal(f.archive.get().busy, false);
    assert.equal(f.archive.get().error, null);
    assert.equal(f.archive.get().preview.token, token);
    assert.equal(f.archive.get().consent, false);
    f.archive.dispose();
});
test("ordinary Play1 actual export handler keeps exact head and session", async () => {
    const f = fixture({ domain: 1 });
    const action = button(f.render(), "Preview private export");
    assert.equal(Boolean(action.disabled), false);
    action.onClick();
    await settle();
    assert.deepEqual(f.calls, [{ name: "archive_export_preview", args: { session: "selected-session", scope, expectedRevision: 7 } }]);
    assert.equal(f.archive.get().error, null);
    f.archive.dispose();
});
test("private Lab denial hides panel and blocks direct controller export/import actions", async () => {
    const f = fixture({ allowed: false });
    assert.equal(f.render().html, "");
    await f.archive.previewExport("selected-session", scope, 7);
    await f.archive.previewImport();
    assert.deepEqual(f.calls, []);
    assert.equal(f.archive.get().preview, null);
});
test("old context panel renders nothing and never dispatches", () => {
    const f = fixture();
    f.archive.contextChanged("different-session|lab|omniscient", true);
    assert.equal(f.render().html, "");
    assert.deepEqual(f.calls, []);
});
test("retained old actual export handler cannot dispatch after selected context changes", async () => {
    const f = fixture({ domain: 1 });
    const old = button(f.render(), "Preview private export");
    f.session.id = "different-session";
    f.session.scope = { story: "different-story", branch: "main" };
    f.state.play = { ...f.state.play, scope: clone(f.session.scope), revision: 2 };
    f.archive.contextChanged("different-session|lab|omniscient", true);
    old.onClick();
    await settle();
    assert.deepEqual(f.calls, [], "Old context's closure must not initiate a new export");
    assert.equal(f.archive.get().preview, null);
});
test("retained actual export handler cannot use an obsolete same-session revision", async () => {
    const f = fixture({ domain: 1 });
    const old = button(f.render(), "Preview private export");
    f.state.play = { ...f.state.play, revision: 8 };
    old.onClick();
    await settle();
    assert.deepEqual(f.calls, [], "A new action needs a coherent current render, never the old head");
});
for (const retirement of ["selection", "lens", "dispose"]) {
    test(`held Domain2 preview late reply is discarded after ${retirement}`, async () => {
        const pending = deferred();
        const f = fixture({ answer: () => pending.promise });
        // Same real ArchiveController action as the UI; isolated from baseline
        // disabled-button defect so late-completion assertions remain meaningful.
        const work = f.archive.previewExport("selected-session", scope, 7);
        assert.deepEqual(f.calls, [{ name: "archive_export_preview", args: { session: "selected-session", scope, expectedRevision: 7 } }]);
        assert.equal(f.archive.get().busy, true);
        if (retirement === "dispose") f.archive.dispose();
        else f.archive.contextChanged(retirement === "lens" ? "selected-session|play|player" : "different-session|lab|omniscient", retirement !== "lens");
        pending.resolve(terminal(preview()));
        await work;
        await settle();
        assert.deepEqual(f.calls.slice(1), [{ name: "archive_discard", args: { token } }]);
        for (const field of ["preview", "status", "result"]) assert.equal(f.archive.get()[field], null);
        assert.equal(f.archive.get().busy, false);
        assert.equal(f.archive.get().consent, false);
        if (retirement === "dispose") {
            // Actual App unmount is outside this checker. Even a deliberately
            // retained stale render must contain no retired private preview.
            assert.doesNotMatch(f.render().html, /archive-preview|Synthetic corrected story|I reviewed this/);
        } else assert.equal(f.render().html, "");
    });
}
test("V3 actual preview labels canonical records and actual second-consent handler confirms token only", async () => {
    const f = fixture({ answer: (name) => {
        if (name === "archive_export_preview") return terminal(preview());
        assert.equal(name, "archive_export");
        return terminal({ version: 1, status: "exported", location: "synthetic-private.locallore-story.json", payload_sha256: "a".repeat(64) });
    } });
    await f.archive.previewExport("selected-session", scope, 7);
    let rendered = f.render();
    assert.match(rendered.html, /<dt>Accepted records<\/dt><dd>3<\/dd>/);
    assert.doesNotMatch(rendered.html, /<dt>Accepted turns<\/dt>/);
    assert.match(rendered.html, /author corrections/);
    assert.match(rendered.html, /private discovery source bindings/);
    const label = "Choose folder and export exact snapshot";
    assert.equal(Boolean(button(rendered, label).disabled), true);
    await f.archive.confirm();
    assert.equal(f.calls.length, 1, "No confirmation before second consent");
    const checkbox = rendered.elements.find((element) => element.type === "input" && element.props.type === "checkbox");
    assert.ok(checkbox, "Actual rendered consent input must exist");
    checkbox.props.onChange({ target: { checked: true } });
    rendered = f.render();
    assert.equal(Boolean(button(rendered, label).disabled), false);
    button(rendered, label).onClick();
    await settle();
    assert.deepEqual(f.calls[1], { name: "archive_export", args: { token, consent: true } });
    assert.equal(f.archive.get().result.status, "exported");
    assert.equal(f.archive.get().preview, null);
    assert.equal(f.archive.get().consent, false);
    assert.equal(f.calls.length, 2);
    f.archive.dispose();
});

const results = [];
for (const { name, run } of cases) {
    try { await run(); results.push({ name, status: "pass" }); }
    catch (error) { results.push({ name, status: "fail", error: String(error?.message ?? error).slice(0, 800) }); }
}
const failed = results.filter((result) => result.status === "fail").length;
const report = {
    suite: "archive-v3-selected-domain2", frozen_against: "88fbab7568c505359f11fddb2bf2c1ac7b997cdf", panelSha256,
    execution: "actual React SSR component handlers and ArchiveController, synthetic gateway; no DOM/native IPC/WebView/App-main mount or authority proof",
    passed: results.length - failed, failed, results,
};
await writeFile(path.join(output, `archive-v3-selection-${cohort}.json`), JSON.stringify(report, null, 2));
console.log(JSON.stringify(report));
assert.equal(failed, 0, `${failed} selected Domain2 archive oracle(s) failed`);
