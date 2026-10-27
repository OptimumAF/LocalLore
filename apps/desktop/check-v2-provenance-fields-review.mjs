// FIRST frozen SOURCE ONLY / UNRUN at handoff. Actual public V2 controller,
// synthetic Gateway DTOs only: no Rust, IPC, rendering, model or canonical proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";

let V2PlayController;
try {
    const compiled = await build({
        entryPoints: [fileURLToPath(new URL("./ui/v2-play-controller.ts", import.meta.url))],
        bundle: true, platform: "node", format: "esm", write: false,
    });
    ({ V2PlayController } = await import(
        `data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].contents).toString("base64")}`
    ));
    for (const name of ["send", "refresh", "status", "retryExact", "traceReceipt"])
        assert.equal(typeof V2PlayController.prototype[name], "function", name);
} catch (error) {
    throw Error(`SETUP failure, not behavioral RED: ${String(error?.message ?? error)}`);
}
const clone = (value) => structuredClone(value);
const scene = () => ({ version: 1, frame_sha256: "a".repeat(64) });
const presentation = () => ({ version: 1, presentation_sha256: "b".repeat(64) });
const scenePolicy = "grounded-prose-v2.4-scene-frame-v1";
const sceneMemory = "locallore-play-v2.9-scene-frame-v1";
const sceneLiteral = "locallore-play-v2.10-literal-director-v1-scene-frame-v1";
const context = () => ({
    session: "provenance-session", scope: { story: "quay", branch: "child" },
    revision: 2, player: "player", view: "play", observer: { kind: "player" },
    persistent: true, pending: false, blocked: false, playMode: "fixture",
    inputKind: "action", action: "wait", fakeMode: "accepted",
});
const snapshot = (c) => ({
    version: 2, domain_version: 2, scope: clone(c.scope), revision: c.revision,
    rules: "fantasy_v1", player: { observer: c.player, self_state: {
        name: "Rowan", location: "quay", alive: true, energy: 2,
        abilities: {}, attributes: {}, injuries: [], affiliations: [], goals: [],
    } }, inventory: {},
});
const page = (query) => ({
    version: 2, scope: clone(query.scope), head: query.expected_head,
    revision: query.at_revision ?? query.expected_head, story_time: 101,
    observer: clone(query.observer), view: query.view,
    privacy: query.observer.kind === "player" ? "player_visible" : "private_character",
    status: "supported", total: 0, rows: [], next_cursor: null, unsupported: [],
});
function play(request, prompt = sceneMemory, presented = false) {
    return {
        version: 2, policy: scenePolicy, prompt_version: prompt,
        profile: {
            id: "synthetic-transport", model_sha256: "1".repeat(64),
            runtime_revision: "2".repeat(40), template_sha256: "3".repeat(64),
            worker_sha256: "4".repeat(64), profile_manifest_sha256: "5".repeat(64),
            context_tokens: 4096, director_tokens: 350, narrator_tokens: 350,
            deadline_ms: 5000, repair_limit: 1,
        },
        repairs: 0, fallback: false,
        narration: { text: "Time advances.", event_ids: [request.expected_revision + 1], speaker: "narrator" },
        stages: [{ stage: "narration", elapsed_ms: 1 }],
        ...(prompt === sceneMemory || prompt === sceneLiteral ? { scene: scene() } : {}),
        ...(presented ? { story_presentation: presentation() } : {}),
    };
}
function receipt(request) {
    return {
        request: clone(request), proposal: {
            version: 1, scope: clone(request.scope), turn: request.turn,
            expected_revision: request.expected_revision, commands: [{ op: "wait", ticks: 1 }],
        }, events: [{
            version: 1, scope: clone(request.scope), sequence: request.expected_revision + 1,
            turn: request.turn, rules: "fantasy_v1", seed: "lantern-quay-v1", story_time: 101,
            participants: ["player"], witnesses: ["player"],
            outcome: { effect: "time_advanced", from: 100, to: 101 },
        }], narration: "Time advances.",
    };
}
function fixture(makePlay, route) {
    let current = context(), request, controller;
    const calls = [];
    const status = (phase) => {
        const accepted = phase === "committed" ? receipt(request) : null;
        if (accepted && makePlay) accepted.play = makePlay(request);
        return { turn: request.turn, scope: clone(request.scope),
            expected_revision: request.expected_revision, phase, error: null, receipt: accepted };
    };
    const gateway = { call: async (command) => {
        calls.push(clone(command));
        if (command.op === "submit") request = clone(command.request);
        if (route) {
            const handled = route(command, status);
            // Deliberately return raw adversarial DTOs, without stringify/clone.
            if (handled !== undefined) return await handled;
        }
        if (command.op === "play_snapshot_v2") return snapshot(current);
        if (command.op === "inspection_query") return page(command.query);
        if (command.op === "submit") return status("queued");
        if (command.op === "prepare") return status("ready");
        if (command.op === "commit" || command.op === "turn_status") return status("committed");
        if (command.op === "cancel") return status("cancelled");
        throw Error("Unsupported");
    } };
    controller = new V2PlayController(gateway, async () => {
        current = { ...current, revision: request.expected_revision + 1 };
        controller.selectedContextChanged(current);
    }, "provenance-test");
    controller.selectedContextChanged(current);
    return {
        controller, calls, status,
        get request() { return request; }, get context() { return current; },
        select(next) { current = clone(next); controller.selectedContextChanged(current); },
        async send() { await controller.refresh(false); await controller.send(); },
    };
}
function deferred() {
    let resolve;
    const promise = new Promise((done) => { resolve = done; });
    return { promise, resolve };
}
const tick = async () => { for (let i = 0; i < 12; i++) await Promise.resolve(); };
const tests = [];
const test = (name, run, calibration = false) => tests.push({ name, run, calibration });
const committed = (f) => {
    assert.equal(f.controller.get().status?.phase, "committed");
    assert.ok(f.controller.get().receipt);
    assert.equal(f.controller.get().uncertain, null);
    assert.equal(f.controller.get().error, null);
    return f.controller.get().receipt;
};
test("calibration-existing-no-play-receipt-and-actual-refresh-path", async () => {
    const f = fixture(); await f.send();
    assert.equal(committed(f).play, undefined);
    assert.equal(f.controller.get().snapshot.revision, 3);
    assert.deepEqual(f.calls.filter((c) => ["submit", "prepare", "commit"].includes(c.op)).map((c) => c.op),
        ["submit", "prepare", "commit"]);
}, true);
test("old-2.1-through-2.8-absent-provenance-stays-transport-compatible", async () => {
    for (const prompt of ["locallore-play-v2.1", "locallore-play-v2.2", "locallore-play-v2.3",
        "locallore-play-v2.4", "locallore-play-v2.5", "locallore-play-v2.6-literal-director-v1",
        "locallore-play-v2.7-story-presentation-v1", "locallore-play-v2.8-literal-director-v1-story-presentation-v1"]) {
        const f = fixture((r) => ({ ...play(r, prompt), policy: "historical-opaque-policy" }));
        await f.send(); const actual = committed(f).play;
        assert.equal(actual.prompt_version, prompt);
        assert.equal(Object.hasOwn(actual, "scene"), false);
        assert.equal(Object.hasOwn(actual, "story_presentation"), false);
    }
}, true);
test("existing-opaque-policy-context-and-count-provenance-are-not-engine-validated-in-transport", async () => {
    const f = fixture((r) => ({ ...play(r, "unknown-opaque-prompt"), policy: "unknown-opaque-policy",
        context_policy: "unknown-opaque-context-policy", context: { transport_only: "bounded counts" } }));
    await f.send(); assert.deepEqual(committed(f).play, {
        ...play(f.request, "unknown-opaque-prompt"), policy: "unknown-opaque-policy",
        context_policy: "unknown-opaque-context-policy", context: { transport_only: "bounded counts" },
    });
}, true);
for (const prompt of [sceneMemory, sceneLiteral]) for (const presented of [false, true])
    test(`${prompt}-presentation-${presented}-preserves-exact-closed-fields`, async () => {
        const f = fixture((r) => play(r, prompt, presented)); await f.send();
        assert.deepEqual(committed(f).play, play(f.request, prompt, presented));
    });
for (const prompt of ["locallore-play-v2.7-story-presentation-v1", "locallore-play-v2.8-literal-director-v1-story-presentation-v1"])
    test(`${prompt}-preserves-existing-presentation-binding`, async () => {
        const f = fixture((r) => ({ ...play(r, prompt, true), policy: "grounded-prose-v2.3-story-presentation-v1" }));
        await f.send(); assert.deepEqual(committed(f).play.story_presentation, presentation());
    });
const fields = [["scene", "frame_sha256"], ["story_presentation", "presentation_sha256"]];
for (const [field, hashKey] of fields) {
    const valid = () => ({ version: 1, [hashKey]: "a".repeat(64) });
    for (const [name, invalid] of [
        ["null", () => null], ["array", () => []], ["missing-hash", () => ({ version: 1 })],
        ["extra-future-key", () => ({ ...valid(), future: true })],
        ["future-version", () => ({ ...valid(), version: 2 })],
        ["string-version", () => ({ ...valid(), version: "1" })],
        ["numeric-hash", () => ({ ...valid(), [hashKey]: 123 })],
        ["uppercase-hash", () => ({ ...valid(), [hashKey]: "A".repeat(64) })],
        ["short-hash", () => ({ ...valid(), [hashKey]: "a".repeat(63) })],
        ["nonhex-hash", () => ({ ...valid(), [hashKey]: "g".repeat(64) })],
        ["oversize", () => ({ ...valid(), [hashKey]: "a".repeat(70_000) })],
    ]) test(`${field}-${name}-refuses-as-Wire-and-retains-original-uncertainty`, async () => {
        const f = fixture((r) => ({ ...play(r, "opaque-existing-prompt"), [field]: invalid() }));
        await f.send();
        assert.equal(f.controller.get().receipt, null);
        assert.equal(f.controller.get().error, "Wire");
        assert.deepEqual(f.controller.get().uncertain.request, f.request);
        assert.equal(f.controller.get().pending, null);
    });
    for (const kind of ["field-getter", "hash-getter", "toJSON", "custom-prototype"])
        test(`${field}-${kind}-rejected-before-user-code-or-provenance-publication`, async () => {
            let invoked = 0;
            const f = fixture((r) => {
                const value = play(r, "opaque-existing-prompt");
                const binding = valid();
                if (kind === "field-getter") Object.defineProperty(value, field, {
                    enumerable: true, get() { invoked++; return binding; },
                });
                else {
                    if (kind === "hash-getter") Object.defineProperty(binding, hashKey, {
                        enumerable: true, get() { invoked++; return "a".repeat(64); },
                    });
                    if (kind === "toJSON") Object.defineProperty(binding, "toJSON", {
                        enumerable: false, value() { invoked++; return valid(); },
                    });
                    value[field] = kind === "custom-prototype"
                        ? Object.assign(Object.create({ inherited: true }), binding) : binding;
                }
                return value;
            });
            await f.send();
            assert.equal(invoked, 0, "transport must inspect descriptors before stringify/getters/toJSON");
            assert.equal(f.controller.get().receipt, null);
            assert.equal(f.controller.get().error, "Wire");
            assert.deepEqual(f.controller.get().uncertain.request, f.request);
        });
}
test("dropped-committed-reply-recovers-original-scene-fields-by-status-without-resubmission", async () => {
    let first = true;
    const f = fixture((r) => play(r, sceneMemory, true), (c) => {
        if (c.op === "commit" && first) { first = false; return Promise.reject(Error("Transport")); }
    });
    await f.send(); const request = clone(f.request);
    assert.equal(f.controller.get().receipt, null);
    assert.deepEqual(f.controller.get().uncertain.request, request);
    await f.controller.status();
    assert.deepEqual(committed(f).play, play(request, sceneMemory, true));
    assert.equal(f.calls.filter((c) => c.op === "submit").length, 1);
    assert.equal(f.calls.filter((c) => c.op === "commit").length, 1);
});
test("dropped-admission-exact-retry-preserves-request-and-new-fields", async () => {
    let admissions = 0;
    const f = fixture((r) => play(r, sceneLiteral, true), (c) => {
        if (c.op === "submit" && ++admissions === 1) return Promise.reject(Error("Transport"));
        if (c.op === "turn_status") return Promise.reject(Error("UnknownTurn"));
    });
    await f.send(); const request = clone(f.request);
    await f.controller.retryExact();
    assert.deepEqual(committed(f).play, play(request, sceneLiteral, true));
    assert.deepEqual(f.calls.filter((c) => c.op === "submit").map((c) => c.request), [request, request]);
});
test("same-object-scene-receipt-inspection-uses-current-head-and-no-write", async () => {
    const f = fixture((r) => play(r, sceneMemory, true)); await f.send();
    const actual = committed(f), before = f.calls.length;
    assert.equal(await f.controller.traceReceipt(clone(actual)), null);
    assert.equal(f.calls.length, before);
    const result = await f.controller.traceReceipt(actual);
    assert.equal(result, f.controller.get().inspection);
    assert.equal(result.query.view, "turn_diff");
    assert.equal(result.query.at_revision, 3);
    assert.equal(result.query.expected_head, 3);
    assert.equal(result.query.observer.kind, "player");
    assert.deepEqual(f.calls.slice(before).map((c) => c.op), ["inspection_query"]);
});
for (const [name, mutation] of [
    ["session", { session: "other-session" }],
    ["scope", { scope: { story: "other-story", branch: "main" } }],
    ["revision", { revision: 4 }],
    ["lens", { view: "lab", observer: { kind: "character", id: "mira" } }],
]) test(`held-scene-commit-${name}-retirement-does-not-publish-private-receipt`, async () => {
    const held = deferred();
    const f = fixture((r) => play(r, sceneMemory, true), (c) => c.op === "commit" ? held.promise : undefined);
    await f.controller.refresh(false);
    const running = f.controller.send(); await tick();
    assert.equal(f.calls.filter((c) => c.op === "commit").length, 1, "actual commit dispatch prerequisite");
    const request = clone(f.request);
    f.select({ ...f.context, ...mutation });
    held.resolve(f.status("committed")); await running;
    assert.equal(f.controller.get().receipt, null);
    assert.equal(f.controller.get().status, null);
    assert.equal(f.controller.get().context.session, f.context.session);
    assert.deepEqual(f.calls.find((c) => c.op === "commit").scope, request.scope);
});
const results = [];
let calibrated = true;
for (const item of tests) {
    if (!calibrated) { results.push({ name: item.name, outcome: "not_run_setup_failed" }); continue; }
    try { await item.run(); results.push({ name: item.name, outcome: "passed" }); }
    catch (error) {
        results.push({ name: item.name, outcome: item.calibration ? "fixture_calibration_failed" : "failed",
            error: String(error?.message ?? error).slice(0, 2048) });
        process.exitCode = 1;
        if (item.calibration) calibrated = false;
    }
}
console.log(JSON.stringify({ evidence: "headless actual-controller synthetic Gateway transport only",
    nativeIpc: false, rustExecution: false, rendering: false, modelExecution: false,
    passed: results.filter((r) => r.outcome === "passed").length,
    failed: results.filter((r) => r.outcome === "failed").length,
    setupFailures: results.filter((r) => r.outcome === "fixture_calibration_failed").length,
    results }));
