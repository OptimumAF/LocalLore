// MOCK gateway, actual capture controller/decoder. No model, app or filesystem export.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID, createHash } from "node:crypto";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(directory, `capture-controller-${randomUUID()}.mjs`);
const compiled = await build({
    stdin: {
        contents:
            'export { CaptureController } from "./ui/capture-controller"; export { Controller } from "./ui/controller";',
        resolveDir: fileURLToPath(new URL(".", import.meta.url)),
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, compiled.outputFiles[0].contents);
const { CaptureController, Controller } = await import(
    pathToFileURL(target).href
);
const session = {
    id: "session-a",
    scope: { story: "synthetic-capture", branch: "main" },
    revision: 0,
    name: "Synthetic",
};
const attempt = {
    identity: {
        scope: session.scope,
        base_revision: 0,
        observer: "player",
        turn: "original-turn",
        attempt: 1,
    },
};
const calls = [],
    natives = [];
let enabled = false,
    status = "recorded",
    holdRead = null,
    holdConfigure = null,
    holdPreview = null,
    corrupt = null,
    revokeError = null;
const gate = () => {
    let release, entered;
    const waiting = new Promise((r) => (release = r)),
        ready = new Promise((r) => (entered = r));
    return { release, entered, waiting, ready };
};
const data = (q) => ({
    scope: q.scope,
    head: q.expected_head,
    base_revision: q.base_revision,
    observer: "private_player_generation_capture",
    details: {
        version: 1,
        status: enabled ? status : "disabled",
        identity:
            enabled && ["recorded", "truncated"].includes(status)
                ? attempt.identity
                : null,
        artifacts:
            enabled && ["recorded", "truncated"].includes(status)
                ? [
                      {
                          kind: "raw_director_output",
                          ordinal: 0,
                          value: {
                              text: "PRIVATE_CANARY",
                              encoding: "utf8",
                              bytes: 14,
                              sha256: "0".repeat(64),
                          },
                      },
                  ]
                : [],
        exact_reconstruction: false,
        privacy: "Synthetic private capture",
    },
});
const gateway = {
    async call(q) {
        calls.push(structuredClone(q));
        if (q.op === "trace_capture_revoke") {
            if (revokeError) throw Error(revokeError);
            enabled = false;
            return { version: 1, scope: q.scope, revoked: true };
        }
        if (q.op === "trace_capture_configure") {
            if (holdConfigure) {
                const h = holdConfigure;
                holdConfigure = null;
                h.entered();
                await h.waiting;
            }
            enabled = true;
            return {
                version: 1,
                scope: q.scope,
                head: q.expected_head,
                enabled: true,
                capture: "explicit_private_details",
                retention_seconds: 600,
            };
        }
        assert.equal(q.op, "trace_capture_read");
        const value = data(q);
        if (corrupt) corrupt(value);
        if (holdRead) {
            const h = holdRead;
            holdRead = null;
            h.entered();
            await h.waiting;
        }
        return value;
    },
    async native(name, args) {
        natives.push({ name, args: structuredClone(args) });
        if (name === "capture_revoke") return { revoked: true };
        if (name === "capture_save") {
            assert.equal(args.consent, true);
            return {
                status: "saved",
                mode: "private_trace",
                location: "Synthetic selected folder",
            };
        }
        assert.equal(name, "capture_preview");
        const q = {
                scope: args.selection.scope,
                expected_head: args.selection.expected_head,
                base_revision: args.selection.base_revision,
            },
            text = JSON.stringify(data(q), null, 2);
        const manifest = {
            format: "locallore-private-trace",
            version: 1,
            mode: "private_trace",
            privacy: "private_generation_capture",
            scope: q.scope,
            revision: q.expected_head,
            files: [
                {
                    path: "capture.json",
                    bytes: Buffer.byteLength(text),
                    sha256: createHash("sha256").update(text).digest("hex"),
                },
            ],
        };
        const value = {
            token: `token-${natives.length}`,
            manifest,
            expires_seconds: 300,
            files: [
                { path: "capture.json", bytes: Buffer.byteLength(text) },
                {
                    path: "manifest.json",
                    bytes: Buffer.byteLength(JSON.stringify(manifest)),
                },
            ],
            text,
        };
        if (holdPreview) {
            const h = holdPreview;
            holdPreview = null;
            h.entered();
            await h.waiting;
        }
        return value;
    },
};
const c = new CaptureController(gateway);
const settle = async () => {
    for (let i = 0; i < 100 && c.get().controlBusy; i++)
        await new Promise((r) => setImmediate(r));
    assert.equal(c.get().controlBusy, false);
};
c.contextChanged(session, 0, true, attempt);
await c.configure(false);
assert.equal(calls.length, 0, "no implicit opt-in");
await c.read();
assert.equal(c.get().reply.details.status, "disabled");
await c.configure(true);
assert.equal(c.get().enabled, true);
await c.read();
assert.match(JSON.stringify(c.get().reply), /PRIVATE_CANARY/);
const configured = calls.filter(
    (q) => q.op === "trace_capture_configure",
).length;
c.contextChanged(session, 1, true, attempt);
await settle();
assert.equal(c.get().reply, null);
assert.equal(
    c.get().enabled,
    true,
    "head advance preserves future-attempt consent",
);
await c.read();
assert.equal(c.get().reply.head, 1);
assert.equal(
    calls.filter((q) => q.op === "trace_capture_configure").length,
    configured,
);
for (const kind of [
    "disabled",
    "expired",
    "not_retained",
    "truncated",
    "recorded",
]) {
    status = kind;
    enabled = true;
    await c.read();
    assert.equal(c.get().reply.details.status, kind);
}
for (const change of [
    (v) => v.head++,
    (v) => (v.scope = { story: "foreign", branch: "main" }),
    (v) => (v.details.exact_reconstruction = true),
    (v) => (v.details.identity.turn = "foreign-turn"),
    (v) => (v.details.artifacts[0].ordinal = 8),
    (v) => (v.details.artifacts[0].kind = "hidden_reasoning"),
    (v) => (v.details.artifacts[0].value = "x".repeat(49153)),
]) {
    corrupt = change;
    await c.read();
    assert.equal(c.get().reply, null);
    assert.equal(c.get().error, "Wire");
}
corrupt = null;
const read = gate();
holdRead = read;
const reading = c.read();
await read.ready;
c.contextChanged(session, 1, false, null);
assert.equal(c.get().reply, null, "lens clears synchronously");
read.release();
await reading;
await settle();
assert.equal(c.get().reply, null);
assert.equal(c.get().enabled, null);
c.contextChanged(session, 1, true, attempt);
await settle();
await c.configure(true);
const configure = gate();
holdConfigure = configure;
const configuring = c.configure(true);
await configure.ready;
c.contextChanged(session, 1, false, null);
configure.release();
await configuring;
await settle();
assert.equal(enabled, false, "late configure is revoked before any next grant");
c.contextChanged(session, 1, true, attempt);
await settle();
await c.configure(true);
await c.preview();
const preview = c.get().preview;
assert(preview);
const saves = natives.filter((x) => x.name === "capture_save").length;
await c.save(false);
assert.equal(
    natives.filter((x) => x.name === "capture_save").length,
    saves,
    "second export consent required",
);
await c.save(true);
assert.equal(c.get().saved, "Synthetic selected folder");
assert.deepEqual(
    natives.at(-1).args,
    { token: preview.token, consent: true },
    "no renderer bytes/path saved",
);
const previewGate = gate();
holdPreview = previewGate;
const previewing = c.preview();
await previewGate.ready;
c.contextChanged(
    {
        ...session,
        id: "session-b",
        scope: { story: "another-story", branch: "main" },
    },
    0,
    false,
    null,
);
previewGate.release();
await previewing;
await settle();
assert.equal(c.get().preview, null);
assert.equal(c.get().reply, null);
assert(
    natives.some((x) => x.name === "capture_revoke" && x.args.token),
    "late preview token explicitly revoked",
);
c.contextChanged(session, 1, true, attempt);
await settle();
await c.configure(true);
revokeError = "Busy";
await c.disable();
assert.equal(c.get().enabled, null);
assert.match(c.get().cleanup, /Busy/);
assert.equal(c.get().reply, null);
revokeError = null;
await c.disable();
assert.equal(c.get().enabled, false);
await c.dispose();
let metadataEnabled = true;
const combinedGateway = {
    native: gateway.native,
    async call(q) {
        if (q.op === "open") return { revision: 0 };
        if (q.op === "play_snapshot")
            return {
                scope: q.scope,
                revision: 0,
                rules: "fantasy_v1",
                inventory: {},
                receipts: [],
                player: {
                    scope: q.scope,
                    revision: 0,
                    observer: "player",
                    self_state: { name: "Rowan", energy: 2, location: "quay" },
                    facts: {},
                    beliefs: [],
                    observations: [],
                },
            };
        if (["inspect", "close"].includes(q.op)) return {};
        if (q.op === "trace_read")
            return {
                scope: q.scope,
                head: q.expected_head,
                base_revision: q.base_revision,
                observer: q.observer,
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                snapshot: {
                    version: 1,
                    status: metadataEnabled
                        ? "bounded_metadata_window"
                        : "disabled",
                    exact_reconstruction: false,
                    attempts: [],
                },
            };
        if (["trace_clear", "trace_configure"].includes(q.op)) {
            enabled = false;
            if (q.op === "trace_configure") metadataEnabled = q.enabled;
            return {
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                ...(q.op === "trace_clear"
                    ? { cleared: true }
                    : { enabled: q.enabled }),
            };
        }
        if (q.op === "trace_capture_configure") metadataEnabled = true;
        return gateway.call(q);
    },
};
const raw = new CaptureController(combinedGateway, () => gameplay.readTrace());
const gameplay = new Controller(
    combinedGateway,
    undefined,
    "capture-control-test",
    () => {
        void raw.disable();
    },
);
await gameplay.attach(session);
await gameplay.showTrace();
raw.contextChanged(session, 0, true, attempt);
const settleRaw = async () => {
    for (let n = 0; n < 100 && raw.get().controlBusy; n++)
        await new Promise((r) => setImmediate(r));
    assert.equal(raw.get().controlBusy, false);
};
for (const action of ["clear", "disable"]) {
    await raw.configure(true);
    await raw.read();
    assert(raw.get().reply);
    const clearing = gameplay.controlTrace(action);
    assert.equal(
        raw.get().reply,
        null,
        "metadata control synchronously clears private presentation",
    );
    await clearing;
    await settleRaw();
    assert.equal(raw.get().enabled, false);
    assert.equal(enabled, false);
}
await raw.dispose();
await gameplay.dispose();
console.log(
    "PASS: MOCK actual capture/gameplay controllers and decoder consent, retention states, hostile replies, head advance, late read/configure/preview, lens/session revoke, token-only second-consent save, Busy revocation honesty and metadata clear/disable coupling.",
);
