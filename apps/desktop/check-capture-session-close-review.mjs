// FIRST independent source freeze, author UNRUN. Actual public controllers and
// IpcGateway over an ordered synthetic Host-session transport; no Rust/native,
// accepted receipt, canonical write, model, DOM or rendering qualification.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const compiled = await build({
    stdin: {
        contents:
            'export {Controller} from "./ui/controller"; export {CaptureController} from "./ui/capture-controller"; export {IpcGateway,ErrorBuffer} from "./ui/model";',
        resolveDir: root,
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
    define: { __DEV_HARNESS__: "false" },
});
const bundle = path.join(output, `capture-session-close-${randomUUID()}.cjs`);
await writeFile(bundle, compiled.outputFiles[0].contents, { flag: "wx" });
const { Controller, CaptureController, IpcGateway, ErrorBuffer } = (
    await import(pathToFileURL(bundle).href)
).default;
const clone = (v) => structuredClone(v);
const a = {
    id: "capture-session-a",
    scope: { story: "synthetic-close-a", branch: "main" },
    revision: 0,
    name: "Synthetic A",
};
const b = {
    id: "capture-session-b",
    scope: { story: "synthetic-close-b", branch: "main" },
    revision: 0,
    name: "Synthetic B",
};
const identity = (s) => ({
    scope: clone(s.scope),
    base_revision: 0,
    observer: "player",
    turn: "synthetic-uncommitted-attempt",
    attempt: 1,
});
const attempt = (s) => ({
    identity: identity(s),
    provenance: Object.fromEntries(
        [
            "model_sha256",
            "worker_sha256",
            "profile_sha256",
            "config_sha256",
            "prompt_sha256",
            "schema_sha256",
            "runtime_revision",
            "engine_revision",
            "profile_label",
            "prompt_label",
            "schema_label",
        ].map((key) => [key, null]),
    ),
    outcome: "not_run",
    elapsed_us: 0,
    truncated: false,
    stages: [],
});
function gate() {
    let enter, release;
    const entered = new Promise((r) => {
            enter = r;
        }),
        waiting = new Promise((r) => {
            release = r;
        });
    return {
        seen: false,
        enter() {
            this.seen = true;
            enter();
        },
        release,
        entered,
        waiting,
    };
}
async function drain() {
    for (let i = 0; i < 20; i++) await new Promise((r) => setImmediate(r));
}
async function until(predicate, why) {
    for (let i = 0; i < 100; i++) {
        if (predicate()) return;
        await new Promise((r) => setImmediate(r));
    }
    assert.fail(why);
}
class Transport {
    events = [];
    open = new Set([a.id, b.id]);
    enabled = new Set();
    closeFailures = 0;
    nativeGate = null;
    hostGate = null;
    log(op, phase, session = null) {
        this.events.push({
            op,
            phase,
            session,
            afterClosed: session !== null && !this.open.has(session),
        });
    }
    invoke = async (name, args) => {
        if (name === "capture_revoke") {
            this.log(name, "start");
            if (this.nativeGate) {
                this.nativeGate.enter();
                await this.nativeGate.waiting;
            }
            this.log(name, "end");
            return { revoked: true };
        }
        assert.equal(
            name,
            "host_call",
            "only existing fixed native gateway operations",
        );
        const envelope = JSON.parse(args.input),
            q = envelope.command;
        assert.equal(envelope.version, 1);
        this.log(q.op, "start", q.session ?? null);
        const ok = (data) => {
            this.log(q.op, "end", q.session ?? null);
            return { version: 1, status: "ok", data };
        };
        const fail = (error) => {
            this.log(q.op, "error", q.session ?? null);
            return { version: 1, status: "error", error };
        };
        if (q.session && !this.open.has(q.session)) return fail("Closed");
        const s = q.session === b.id ? b : a;
        if (q.session)
            assert.deepEqual(
                q.scope,
                s.scope,
                "scope belongs to actual modeled session",
            );
        switch (q.op) {
            case "open":
                return ok({ revision: 0 });
            case "play_snapshot_v2":
                return ok({
                    version: 2,
                    domain_version: 1,
                    scope: clone(s.scope),
                    revision: 0,
                    rules: "fantasy_v1",
                    player: {
                        observer: "player",
                        self_state: {
                            name: "Rowan",
                            location: "quay",
                            alive: true,
                            energy: 2,
                            abilities: {},
                            attributes: {},
                            injuries: [],
                            affiliations: [],
                            goals: [],
                        },
                    },
                    inventory: {},
                });
            case "play_snapshot":
                return ok({
                    scope: clone(s.scope),
                    revision: 0,
                    rules: "fantasy_v1",
                    inventory: {},
                    receipts: [],
                    player: {
                        scope: clone(s.scope),
                        revision: 0,
                        observer: "player",
                        self_state: {
                            name: "Rowan",
                            location: "quay",
                            energy: 2,
                        },
                        facts: {},
                        beliefs: [],
                        observations: [],
                    },
                });
            case "inspect":
                return ok({});
            case "trace_read":
                return ok({
                    scope: clone(s.scope),
                    head: 0,
                    base_revision: q.base_revision,
                    observer: clone(q.observer),
                    configuration_scope: "window_host",
                    capture: "metadata_only",
                    full_capture: "unsupported",
                    snapshot: {
                        version: 1,
                        status: "bounded_metadata_window",
                        exact_reconstruction: false,
                        attempts: [attempt(s)],
                    },
                });
            case "trace_capture_configure":
                this.enabled.add(q.session);
                return ok({
                    version: 1,
                    scope: clone(s.scope),
                    head: 0,
                    enabled: true,
                    capture: "explicit_private_details",
                    retention_seconds: 600,
                });
            case "trace_capture_read":
                return ok({
                    scope: clone(s.scope),
                    head: 0,
                    base_revision: 0,
                    observer: "private_player_generation_capture",
                    details: {
                        version: 1,
                        status: "recorded",
                        identity: identity(s),
                        artifacts: [
                            {
                                kind: "selected_context",
                                ordinal: 0,
                                value: { synthetic: `PRIVATE-${s.id}` },
                            },
                        ],
                        exact_reconstruction: false,
                        privacy:
                            "Synthetic diagnostic DTO; no accepted state/model authority",
                    },
                });
            case "trace_capture_revoke":
                if (this.hostGate) {
                    this.hostGate.enter();
                    await this.hostGate.waiting;
                }
                this.enabled.delete(q.session);
                return ok({ version: 1, scope: clone(s.scope), revoked: true });
            case "close":
                if (this.closeFailures > 0) {
                    this.closeFailures--;
                    return fail("Busy");
                }
                this.open.delete(q.session);
                this.enabled.delete(q.session);
                // Successful close changes only this synthetic session model.
                this.events.push({
                    op: "close",
                    phase: "end",
                    session: q.session,
                    afterClosed: false,
                });
                return { version: 1, status: "ok", data: {} };
            default:
                assert.fail(`Unexpected synthetic Host operation: ${q.op}`);
        }
    };
}
async function fixture() {
    const transport = new Transport(),
        errors = new ErrorBuffer(),
        gateway = new IpcGateway(transport.invoke, errors);
    let capture;
    const controller = new Controller(
        gateway,
        errors,
        "capture-close-review",
        (work, closingSession) => capture.metadataControl(work, closingSession),
    );
    capture = new CaptureController(gateway, () => controller.readTrace());
    // Same public context subscription as main, without a parallel controller.
    const sync = () => {
        const s = controller.get();
        capture.contextChanged(
            controller.selected(),
            s.play?.revision ?? 0,
            s.view === "lab" &&
                s.observer === "omniscient" &&
                s.trace.shown &&
                !s.disposed,
            controller.traceAttempt(),
        );
    };
    const unsubscribe = controller.subscribe(sync);
    await controller.attach(clone(a));
    controller.requestLab();
    controller.acknowledgeLab(true);
    controller.setObserver("omniscient");
    await controller.showTrace();
    await until(
        () => !capture.get().controlBusy,
        "initial queued revocation settles",
    );
    await capture.configure(true);
    await capture.read();
    assert.ok(
        capture.get().reply,
        "actual Capture decoder holds a synthetic private diagnostic before close",
    );
    assert.ok(JSON.stringify(capture.get().reply).includes(`PRIVATE-${a.id}`));
    assert.deepEqual(errors.snapshot(), []);
    transport.events.length = 0;
    return {
        transport,
        errors,
        gateway,
        controller,
        capture,
        sync,
        async cleanup() {
            transport.nativeGate?.release();
            transport.hostGate?.release();
            unsubscribe();
            await capture.dispose();
            await controller.dispose();
        },
    };
}
const start = (events, op, session = undefined) =>
    events.findIndex(
        (e) =>
            e.op === op &&
            e.phase === "start" &&
            (session === undefined || e.session === session),
    );
const end = (events, op, session = undefined) =>
    events.findIndex(
        (e) =>
            e.op === op &&
            e.phase === "end" &&
            (session === undefined || e.session === session),
    );
function noPostCloseHost(events, session) {
    const closed = end(events, "close", session);
    assert.ok(closed >= 0, "modeled Host close really completed");
    assert.deepEqual(
        events.slice(closed + 1).filter((e) => e.session === session),
        [],
        "no old-scope Host call after close",
    );
}
const cases = [];
async function test(name, work) {
    try {
        await work();
        cases.push({ name, passed: true });
    } catch (error) {
        cases.push({
            name,
            passed: false,
            error:
                error instanceof Error
                    ? error.message.slice(0, 256)
                    : "failure",
        });
    }
}
await test("actual closeSession waits for native and Host capture revoke before Host close; repeated sync cannot reinstall old owner", async () => {
    const f = await fixture();
    let closing;
    const native = gate(),
        host = gate();
    f.transport.nativeGate = native;
    f.transport.hostGate = host;
    try {
        closing = f.controller.closeSession();
        await until(
            () => native.seen,
            "native capture revoke must be admitted",
        );
        assert.equal(
            start(f.transport.events, "close", a.id),
            -1,
            "native revoke gate blocks Host close",
        );
        assert.equal(
            f.capture.get().reply,
            null,
            "private reply clears before pending revoke",
        );
        f.sync(); // Exact old selected context may be notified while close waits.
        native.release();
        await until(
            () => host.seen,
            "Host capture revoke must be admitted while session is open",
        );
        assert.equal(
            start(f.transport.events, "close", a.id),
            -1,
            "Host revoke gate blocks Host close",
        );
        f.sync();
        host.release();
        await closing;
        await drain();
        assert.ok(
            end(f.transport.events, "capture_revoke") <
                start(f.transport.events, "close", a.id),
        );
        assert.ok(
            end(f.transport.events, "trace_capture_revoke", a.id) <
                start(f.transport.events, "close", a.id),
        );
        noPostCloseHost(f.transport.events, a.id);
        assert.equal(f.controller.selected(), null);
        assert.equal(f.capture.get().reply, null);
        assert.equal(f.capture.get().preview, null);
        assert.deepEqual(
            f.errors.snapshot(),
            [],
            "no swallowed or globally suppressed Closed diagnostic",
        );
    } finally {
        native.release();
        host.release();
        await Promise.allSettled([closing].filter(Boolean));
        await f.cleanup();
    }
});
await test("failed Host close retains honest selected session/error with cleared private data; normal sync permits retry", async () => {
    const f = await fixture();
    try {
        f.transport.closeFailures = 1;
        await f.controller.closeSession();
        await drain();
        assert.equal(f.controller.selected()?.id, a.id);
        assert.equal(f.controller.get().visibleError, "Busy");
        assert.equal(f.transport.open.has(a.id), true);
        assert.equal(f.capture.get().reply, null);
        assert.equal(f.capture.get().preview, null);
        assert.ok(
            f.errors
                .snapshot()
                .some((e) => e.source === "native" && e.category === "Busy"),
        );
        assert.ok(!f.errors.snapshot().some((e) => e.category === "Closed"));
        await f.controller.refresh();
        await f.controller.showTrace();
        await until(
            () => !f.capture.get().controlBusy,
            "failed-close normal context recovery settles",
        );
        await f.capture.configure(true);
        await f.capture.read();
        assert.ok(
            f.capture.get().reply,
            "new explicit capture action after honest failure remains usable",
        );
        f.transport.events.length = 0;
        await f.controller.closeSession();
        await drain();
        noPostCloseHost(f.transport.events, a.id);
        assert.equal(f.controller.selected(), null);
        assert.ok(!f.errors.snapshot().some((e) => e.category === "Closed"));
    } finally {
        await f.cleanup();
    }
});
await test("closing A cannot clear or globally revoke the already selected private capture B", async () => {
    const transport = new Transport(),
        errors = new ErrorBuffer(),
        gateway = new IpcGateway(transport.invoke, errors);
    const capture = new CaptureController(gateway);
    try {
        capture.contextChanged(clone(b), 0, true, attempt(b));
        await capture.configure(true);
        await capture.read();
        const before = capture.get();
        assert.ok(before.reply);
        assert.equal(before.enabled, true);
        transport.events.length = 0;
        // Direct Capture optional-Session seam only: not a claim that the whole
        // gameplay selection changed concurrently in a native application.
        await capture.metadataControl(async () => {
            await gateway.call({
                op: "close",
                session: a.id,
                scope: clone(a.scope),
            });
        }, clone(a));
        assert.equal(capture.get().reply, before.reply);
        assert.equal(capture.get().enabled, true);
        assert.equal(capture.get().permitted, true);
        assert.equal(transport.enabled.has(b.id), true);
        assert.equal(start(transport.events, "capture_revoke"), -1);
        assert.equal(start(transport.events, "trace_capture_revoke"), -1);
        noPostCloseHost(transport.events, a.id);
        assert.deepEqual(errors.snapshot(), []);
    } finally {
        await capture.dispose();
    }
});
await test("default Controller without capture integration closes normally without new capture IPC", async () => {
    const transport = new Transport(),
        errors = new ErrorBuffer(),
        gateway = new IpcGateway(transport.invoke, errors);
    const controller = new Controller(gateway, errors, "default-close-review");
    try {
        await controller.attach(clone(a));
        transport.events.length = 0;
        await controller.closeSession();
        assert.equal(controller.selected(), null);
        assert.equal(transport.open.has(a.id), false);
        assert.equal(
            transport.events.filter(
                (e) => e.op === "close" && e.phase === "start",
            ).length,
            1,
        );
        assert.ok(transport.events.every((e) => !e.op.includes("capture")));
        assert.deepEqual(errors.snapshot(), []);
    } finally {
        await controller.dispose();
    }
});
const result = {
    version: 1,
    cases,
    passed: cases.filter((c) => c.passed).length,
    failed: cases.filter((c) => !c.passed).length,
    headless_ordered_ipc_double: true,
    actual_public_controllers: true,
    actual_ipc_gateway: true,
    rust_host: false,
    native_ipc: false,
    native_webview: false,
    canonical_commit: false,
    model_execution: false,
};
await writeFile(
    path.join(output, `capture-session-close-${randomUUID()}.json`),
    JSON.stringify(result, null, 2),
    { flag: "wx" },
);
console.log(JSON.stringify(result));
if (result.failed) process.exitCode = 1;
