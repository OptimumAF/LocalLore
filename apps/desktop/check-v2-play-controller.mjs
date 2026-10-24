// Frozen scheduling oracles: synthetic Gateway, NOT IPC/render/Core/model execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";
const compiled = await build({
    entryPoints: [
        fileURLToPath(new URL("./ui/v2-play-controller.ts", import.meta.url)),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
const { V2PlayController } = await import(
    `data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].contents).toString("base64")}`
);
const clone = (value) => structuredClone(value);
const context = () => ({
    session: "session-1",
    scope: { story: "quay", branch: "child" },
    revision: 2,
    player: "player",
    view: "play",
    observer: { kind: "player" },
    persistent: true,
    pending: false,
    blocked: false,
    playMode: "fixture",
    inputKind: "action",
    action: "wait",
    fakeMode: "accepted",
});
const thin = (c) => ({
    version: 2,
    domain_version: 2,
    scope: clone(c.scope),
    revision: c.revision,
    rules: "fantasy_v1",
    player: {
        observer: c.player,
        self_state: {
            name: "Rowan",
            location: "quay",
            alive: true,
            energy: 2,
            abilities: { steady: 1 },
            attributes: { resolve: 3 },
            injuries: [],
            affiliations: [],
            goals: [],
        },
    },
    inventory: {},
});
const page = (q, rows = []) => ({
    version: 2,
    scope: clone(q.scope),
    head: q.expected_head,
    revision: q.at_revision ?? q.expected_head,
    story_time: 100,
    observer: clone(q.observer),
    view: q.view,
    privacy:
        q.observer.kind === "player"
            ? "player_visible"
            : q.observer.kind === "character"
              ? "private_character"
              : "private_omniscient",
    status: ["summaries", "retrieval_indexes"].includes(q.view)
        ? "unsupported"
        : "supported",
    total: rows.length,
    rows,
    next_cursor: null,
    unsupported: [],
});
const receipt = (request) => ({
    request: clone(request),
    proposal: {
        version: 1,
        scope: clone(request.scope),
        turn: request.turn,
        expected_revision: request.expected_revision,
        commands: [{ op: "wait", ticks: 1 }],
    },
    events: [
        {
            version: 1,
            scope: clone(request.scope),
            sequence: request.expected_revision + 1,
            turn: request.turn,
            rules: "fantasy_v1",
            seed: "lantern-quay-v1",
            story_time: 101,
            participants: ["player"],
            witnesses: ["player"],
            outcome: { effect: "time_advanced", from: 100, to: 101 },
        },
    ],
    narration: "Time advances.",
});
const status = (request, phase, error = null) => ({
    turn: request.turn,
    scope: clone(request.scope),
    expected_revision: request.expected_revision,
    phase,
    error,
    receipt: phase === "committed" ? receipt(request) : null,
});
function deferred() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
const tick = async () => {
    for (let n = 0; n < 12; n++) await Promise.resolve();
};
const tests = [];
function test(name, run) {
    tests.push({ name, run });
}
function fixture(route) {
    let c = context(),
        request;
    const calls = [];
    const gateway = {
        call: async (command) => {
            calls.push(clone(command));
            if (command.op === "submit" || command.op === "free_text")
                request = clone(command.request);
            if (route) {
                const handled = route(command, request);
                if (handled !== undefined) return await handled;
            }
            if (command.op === "play_snapshot_v2") return thin(c);
            if (command.op === "inspection_query") return page(command.query);
            if (command.op === "submit" || command.op === "free_text")
                return status(request, "queued");
            if (command.op === "prepare") return status(request, "ready");
            if (command.op === "commit") return status(request, "committed");
            if (command.op === "cancel") return status(request, "cancelled");
            if (command.op === "turn_status")
                return status(request, "committed");
            throw Error("Unsupported");
        },
    };
    const controller = new V2PlayController(gateway, async () => {}, "v2-test");
    controller.selectedContextChanged(c);
    return {
        controller,
        calls,
        get request() {
            return request;
        },
        get ctx() {
            return c;
        },
        select(next) {
            c = clone(next);
            controller.selectedContextChanged(c);
        },
    };
}
test("thin2-and-history-without-legacy-context", async () => {
    const f = fixture();
    await f.controller.refresh();
    assert.equal(f.controller.get().snapshot.domain_version, 2);
    assert.equal(f.controller.get().history.query.version, 2);
    assert.ok(
        !f.calls.some((c) => c.op === "play_snapshot" || c.op === "inspect"),
    );
    assert.ok(!("receipts" in f.controller.get().snapshot));
});
test("accepted-actual-key-status-and-receipt", async () => {
    const f = fixture();
    await f.controller.refresh();
    await f.controller.send();
    assert.equal(f.controller.get().status.phase, "committed");
    assert.deepEqual(f.controller.get().receipt.request, f.request);
    assert.equal(f.controller.get().pending, null);
    assert.equal(f.controller.get().uncertain, null);
    assert.deepEqual(
        f.calls
            .filter((c) => ["submit", "prepare", "commit"].includes(c.op))
            .map((c) => c.op),
        ["submit", "prepare", "commit"],
    );
});
test("rejected-action-does-not-commit", async () => {
    const f = fixture((c, r) =>
        c.op === "prepare" ? status(r, "failed", "Ability") : undefined,
    );
    await f.controller.refresh();
    await f.controller.send();
    assert.equal(f.controller.get().error, "Ability");
    assert.equal(f.controller.get().receipt, null);
    assert.ok(!f.calls.some((c) => c.op === "commit"));
});
test("local-free-text-never-falls-back-to-fixture", async () => {
    const f = fixture((c) =>
        c.op === "free_text"
            ? Promise.reject(Error("ModelUnavailable"))
            : undefined,
    );
    f.select({ ...f.ctx, playMode: "local", inputKind: "dialogue" });
    await f.controller.refresh();
    f.controller.setDraft("Speak literally <no markup> 雪");
    await f.controller.send();
    assert.equal(f.request.intent.kind, "free_text");
    assert.equal(f.request.intent.value.kind, "dialogue");
    assert.ok(!f.calls.some((c) => c.op === "submit"));
    assert.equal(f.controller.get().error, "ModelUnavailable");
});
test("pending-send-is-deduplicated-and-cancel-before-ack-uses-original-key", async () => {
    const admission = deferred();
    const f = fixture((c) =>
        c.op === "submit" ? admission.promise : undefined,
    );
    await f.controller.refresh();
    const first = f.controller.send();
    assert.equal(f.controller.send(), first);
    await tick();
    await f.controller.cancel();
    assert.ok(!f.calls.some((c) => c.op === "cancel"));
    admission.resolve(status(f.request, "queued"));
    await first;
    assert.deepEqual(
        f.calls.filter((c) => c.op === "cancel").map((c) => c.turn),
        [f.request.turn],
    );
    assert.ok(!f.calls.some((c) => c.op === "prepare" || c.op === "commit"));
    assert.equal(f.controller.get().status.phase, "cancelled");
});
test("unknown-ack-retains-full-request-and-exact-retry-never-new-key", async () => {
    let admissions = 0;
    const f = fixture((c) =>
        c.op === "submit" && ++admissions === 1
            ? Promise.reject(Error("Transport"))
            : c.op === "turn_status"
              ? Promise.reject(Error("UnknownTurn"))
              : undefined,
    );
    await f.controller.refresh();
    await f.controller.send();
    const original = clone(f.request);
    assert.deepEqual(f.controller.get().uncertain.request, original);
    await f.controller.send();
    assert.equal(admissions, 1);
    await f.controller.retryExact();
    assert.equal(admissions, 2);
    assert.deepEqual(
        f.calls.filter((c) => c.op === "submit").map((c) => c.request),
        [original, original],
    );
});
test("context-retirement-keeps-unknown-and-suppresses-stale-presentation", async () => {
    const admission = deferred();
    const f = fixture((c) =>
        c.op === "submit" ? admission.promise : undefined,
    );
    await f.controller.refresh();
    const running = f.controller.send();
    await tick();
    const original = clone(f.request);
    f.select({
        ...f.ctx,
        session: "session-2",
        scope: { story: "other", branch: "main" },
    });
    admission.resolve(status(original, "queued"));
    await running;
    assert.equal(f.controller.get().receipt, null);
    assert.equal(f.controller.get().snapshot, null);
    assert.deepEqual(f.controller.get().uncertain.request, original);
    assert.ok(!f.calls.some((c) => c.op === "prepare" || c.op === "commit"));
    await f.controller.send();
    assert.equal(f.calls.filter((c) => c.op === "submit").length, 1);
});
test("committed-latch-wins-late-cancel", async () => {
    const cancelled = deferred(),
        committed = deferred();
    const f = fixture((c) =>
        c.op === "commit"
            ? committed.promise
            : c.op === "cancel"
              ? cancelled.promise
              : undefined,
    );
    await f.controller.refresh();
    const running = f.controller.send();
    await tick();
    const cancelling = f.controller.cancel();
    await tick();
    committed.resolve(status(f.request, "committed"));
    await running;
    cancelled.resolve(status(f.request, "cancelled"));
    await cancelling;
    assert.equal(f.controller.get().status.phase, "committed");
    assert.ok(f.controller.get().receipt);
});
test("malformed-committed-result-keeps-uncertainty", async () => {
    const f = fixture((c, r) =>
        c.op === "commit"
            ? { ...status(r, "committed"), receipt: {} }
            : undefined,
    );
    await f.controller.refresh();
    await f.controller.send();
    assert.equal(f.controller.get().receipt, null);
    assert.equal(f.controller.get().error, "Wire");
    assert.ok(f.controller.get().uncertain);
});
test("observer-control-and-head-changes-fence-delayed-prepare", async () => {
    for (const mutation of [
        { observer: { kind: "omniscient" }, view: "lab" },
        { revision: 3 },
        { inputKind: "dialogue" },
        { action: "dialogue" },
        { fakeMode: "rejected" },
        { playMode: "local" },
    ]) {
        const ready = deferred();
        const f = fixture((c) =>
            c.op === "prepare" ? ready.promise : undefined,
        );
        await f.controller.refresh();
        const running = f.controller.send();
        await tick();
        f.select({ ...f.ctx, ...mutation });
        ready.resolve(status(f.request, "ready"));
        await running;
        assert.ok(!f.calls.some((c) => c.op === "commit"));
        assert.ok(f.controller.get().uncertain);
    }
});
test("late-snapshot-cannot-replace-newer-context", async () => {
    const read = deferred();
    let first = true;
    const f = fixture((c) =>
        c.op === "play_snapshot_v2" && first
            ? ((first = false), read.promise)
            : undefined,
    );
    const old = f.controller.refresh();
    const stale = thin(f.ctx);
    f.select({ ...f.ctx, revision: 3 });
    await f.controller.refresh();
    read.resolve(stale);
    await old;
    assert.equal(f.controller.get().snapshot.revision, 3);
});
test("lab-is-read-only-and-all-nine-views-bind-current-observer", async () => {
    const f = fixture();
    f.select({
        ...f.ctx,
        view: "lab",
        observer: { kind: "character", id: "mira" },
    });
    await f.controller.refresh();
    await f.controller.send();
    assert.ok(!f.calls.some((c) => c.op === "submit" || c.op === "free_text"));
    for (const view of [
        "profiles",
        "history",
        "relationships",
        "knowledge",
        "promises",
        "provenance",
        "turn_diff",
        "summaries",
        "retrieval_indexes",
    ]) {
        await f.controller.readQuery({ view, atRevision: null, search: "" });
        assert.deepEqual(f.controller.get().inspection.query.observer, {
            kind: "character",
            id: "mira",
        });
    }
});
test("original-scoped-source-stays-selected-child-and-must-match-actual-event", async () => {
    const source = {
        kind: "scoped_event",
        value: {
            original_scope: { story: "quay", branch: "main" },
            sequence: 1,
        },
    };
    const f = fixture((c) =>
        c.op === "inspection_query" &&
        c.query.view === "history" &&
        c.query.search
            ? page(c.query, [
                  {
                      kind: "event",
                      key: "source-event",
                      event: {
                          sequence: 1,
                          scope: { story: "quay", branch: "main" },
                          turn: "ancestor",
                          story_time: 100,
                          participants: ["player"],
                          witnesses: ["player"],
                          consequence: {
                              effect: "time_advanced",
                              from: 99,
                              to: 100,
                          },
                      },
                      origin: "recorded_observation",
                  },
              ])
            : undefined,
    );
    await f.controller.refresh();
    await f.controller.source(source);
    const inspected = f.controller.get().inspection;
    assert.deepEqual(inspected.query.scope, { story: "quay", branch: "child" });
    assert.equal(inspected.query.at_revision, null);
    assert.equal(f.controller.get().sourceMatched, true);
    assert.deepEqual(
        f.controller.get().source.value.original_scope,
        source.value.original_scope,
    );
    await f.controller.source({
        ...source,
        value: {
            ...source.value,
            original_scope: { story: "quay", branch: "child" },
        },
    });
    assert.equal(f.controller.get().sourceMatched, false);
});
test("reentrant-subscriber-cannot-dispatch-second-turn", async () => {
    const admission = deferred();
    const f = fixture((c) =>
        c.op === "submit" ? admission.promise : undefined,
    );
    await f.controller.refresh();
    let reentered = false;
    f.controller.subscribe(() => {
        if (f.controller.get().pending && !reentered) {
            reentered = true;
            void f.controller.send();
        }
    });
    const running = f.controller.send();
    await tick();
    assert.equal(f.calls.filter((c) => c.op === "submit").length, 1);
    admission.resolve(status(f.request, "queued"));
    await running;
});
test("own-root-head-advance-keeps-actual-receipt-and-reconciles-once", async () => {
    let c = context(),
        request,
        controller,
        refreshes = 0;
    const gateway = {
        call: async (command) => {
            if (command.op === "play_snapshot_v2") return thin(c);
            if (command.op === "inspection_query") return page(command.query);
            if (command.op === "submit") {
                request = clone(command.request);
                return status(request, "queued");
            }
            if (command.op === "prepare") return status(request, "ready");
            if (command.op === "commit") return status(request, "committed");
            throw Error("Unsupported");
        },
    };
    controller = new V2PlayController(
        gateway,
        async () => {
            refreshes++;
            c = { ...c, revision: request.expected_revision + 1 };
            controller.selectedContextChanged(c);
        },
        "own-head",
    );
    controller.selectedContextChanged(c);
    await controller.refresh(false);
    await controller.send();
    assert.equal(refreshes, 1);
    assert.equal(controller.get().snapshot.revision, 3);
    assert.equal(controller.get().status.phase, "committed");
    assert.deepEqual(controller.get().receipt.request, request);
});
test("late-original-status-error-cannot-pollute-another-session", async () => {
    const lookup = deferred();
    const f = fixture((c) =>
        c.op === "submit"
            ? Promise.reject(Error("Transport"))
            : c.op === "turn_status"
              ? lookup.promise
              : undefined,
    );
    await f.controller.refresh();
    await f.controller.send();
    const original = clone(f.request);
    const reading = f.controller.status();
    f.select({
        ...f.ctx,
        session: "session-2",
        scope: { story: "other", branch: "main" },
    });
    lookup.reject(Error("Closed"));
    await reading;
    assert.equal(f.controller.get().error, null);
    assert.deepEqual(f.controller.get().uncertain.request, original);
});
test("snapshot-player-must-match-coherent-root-player", async () => {
    const f = fixture((c) =>
        c.op === "play_snapshot_v2"
            ? thin({ ...context(), player: "hero" })
            : undefined,
    );
    await f.controller.refresh();
    assert.equal(f.controller.get().error, "Wire");
    assert.equal(f.controller.get().snapshot, null);
    assert.ok(!f.calls.some((c) => c.op === "inspection_query"));
});
test("unknown-ack-cancel-needs-actual-original-status-before-native-cancel", async () => {
    const f = fixture((c, r) =>
        c.op === "submit"
            ? Promise.reject(Error("Transport"))
            : c.op === "turn_status"
              ? status(r, "queued")
              : undefined,
    );
    await f.controller.refresh();
    await f.controller.send();
    await f.controller.cancel();
    assert.ok(!f.calls.some((c) => c.op === "cancel"));
    assert.ok(f.controller.get().uncertain);
    await f.controller.status();
    await f.controller.cancel();
    assert.equal(f.calls.filter((c) => c.op === "cancel").length, 1);
    assert.equal(f.controller.get().status.phase, "cancelled");
    assert.equal(f.controller.get().uncertain, null);
});
test("other-root-work-blocks-admission", async () => {
    for (const flag of ["pending", "blocked"]) {
        const f = fixture();
        f.select({ ...f.ctx, [flag]: true });
        await f.controller.refresh();
        await f.controller.send();
        assert.ok(
            !f.calls.some((c) => c.op === "submit" || c.op === "free_text"),
        );
    }
});
test("late-private-query-cannot-replace-new-observer-page", async () => {
    const old = deferred();
    let first = true,
        oldQuery;
    const f = fixture((c) =>
        c.op === "inspection_query" && c.query.view === "knowledge" && first
            ? ((first = false), (oldQuery = clone(c.query)), old.promise)
            : undefined,
    );
    f.select({
        ...f.ctx,
        view: "lab",
        observer: { kind: "character", id: "mira" },
    });
    await f.controller.refresh(false);
    const reading = f.controller.readQuery({
        view: "knowledge",
        atRevision: null,
        search: "",
    });
    await tick();
    f.select({ ...f.ctx, observer: { kind: "omniscient" } });
    await f.controller.refresh(false);
    await f.controller.readQuery({
        view: "knowledge",
        atRevision: null,
        search: "",
    });
    old.resolve(page(oldQuery));
    await reading;
    assert.deepEqual(f.controller.get().inspection.page.observer, {
        kind: "omniscient",
    });
});
test("original-native-rejection-survives-durable-phase-only-status-without-forging-cause", async () => {
    let rejected = false;
    const f = fixture((c, r) => {
        if (rejected && c.op === "prepare")
            return Promise.reject(Error("Inventory"));
        if (rejected && c.op === "turn_status") return status(r, "failed");
        return undefined;
    });
    await f.controller.refresh();
    await f.controller.send();
    const accepted = clone(f.controller.get().receipt);
    f.select({ ...f.ctx, revision: 3 });
    await f.controller.refresh();
    rejected = true;
    await f.controller.send();
    assert.equal(f.controller.get().error, "Inventory");
    await f.controller.status();
    assert.equal(f.controller.get().status.phase, "failed");
    assert.equal(
        f.controller.get().status.error,
        null,
        "the authoritative saved status does not retain a cause",
    );
    assert.equal(
        f.controller.get().error,
        "Inventory",
        "keep only the actual previously observed error for this original operation",
    );
    assert.ok(
        f.controller
            .get()
            .notice.includes("saved status has no retained cause"),
    );
    assert.deepEqual(f.controller.get().receipt, accepted);
    assert.equal(f.calls.filter((c) => c.op === "commit").length, 1);
    assert.equal(f.controller.get().pending, null);
    assert.equal(f.controller.get().uncertain, null);
});
let passed = 0;
for (const test of tests) {
    try {
        await test.run();
        passed++;
    } catch (error) {
        console.error(
            JSON.stringify({
                test: test.name,
                error: String(error?.message ?? error).slice(0, 2048),
            }),
        );
        process.exitCode = 1;
    }
}
console.log(
    JSON.stringify({
        evidence:
            "synthetic Gateway/controller scheduling only; no native IPC/render/Core/model",
        passed,
        total: tests.length,
    }),
);
