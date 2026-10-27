// FIRST SOURCE FREEZE: UNCOMPILED/UNRUN at handoff, before the new API exists.
// Actual public Controller + raw synthetic Gateway DTOs only. No Rust/native
// IPC/bootstrap, model, DOM, rendering, canonical commit or quality evidence.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { fileURLToPath } from "node:url";

const FIXED = "scene-native-fixture-v1";
const OMIT_PERMIT = Symbol("default-permit");
const clone = (value) => structuredClone(value);
const scope = { story: "scene-bootstrap", branch: "main" };
const session = () => ({
    id: "scene-bootstrap-session",
    scope: clone(scope),
    revision: 0,
    name: "Synthetic scene",
});
const ready = () => ({ provider: FIXED, kind: "synthetic_fixture" });
const metadata = () => ({
    provider: FIXED,
    real_model: false,
    loaded: false,
    status: "configured_fixture_owner",
    // Opaque transport data. Deliberately not a Rust PlayProfile claim.
    profile: {
        id: FIXED,
        model_sha256: "opaque-not-an-engine-hash",
        context_tokens: "opaque-not-an-engine-budget",
        extra: { tags: ["synthetic", null, true, 7] },
    },
});
const nativeModel = (loaded = false) => ({
    operation_id: 4,
    phase: loaded ? "loaded" : "unloaded",
    loaded,
    imported: loaded,
    resident: loaded,
    error: null,
    percent: loaded ? 100 : 0,
    profile: null,
});
const thin = (revision = 0) => ({
    version: 2,
    domain_version: 1,
    scope: clone(scope),
    revision,
    rules: "fantasy_v1",
    player: {
        observer: "player",
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
const legacy = (revision = 0) => ({
    scope: clone(scope),
    revision,
    rules: "fantasy_v1",
    inventory: {},
    receipts: [],
    player: {
        scope: clone(scope),
        revision,
        observer: "player",
        self_state: { name: "Rowan", energy: 2, location: "quay" },
        facts: {},
        beliefs: [],
        observations: [],
    },
});
function deferred() {
    let resolve, reject;
    const promise = new Promise((yes, no) => {
        resolve = yes;
        reject = no;
    });
    return { promise, resolve, reject };
}
async function drain() {
    for (let i = 0; i < 24; i++) await Promise.resolve();
}
class Gateway {
    calls = [];
    nativeCalls = [];
    response = metadata();
    realLoaded = false;
    modelRead = null;
    providerRead = null;
    snapshot = thin();
    submitted = [];
    head = 0;
    constructor(useThin = false) {
        if (useThin) this.playSnapshotV2 = true;
    }
    async native(command, args) {
        this.nativeCalls.push({ command, args: clone(args ?? {}) });
        assert.equal(
            command,
            "model_status",
            "metadata cannot configure/import/load a provider",
        );
        if (this.modelRead) return this.modelRead();
        return nativeModel(this.realLoaded);
    }
    async call(command) {
        this.calls.push(clone(command));
        switch (command.op) {
            case "model_status":
                // Preserve raw descriptors on adversarial DTOs. Never clone or
                // stringify a response before the actual Controller decodes it.
                return this.providerRead ? this.providerRead() : this.response;
            case "open":
                return { revision: this.head };
            case "close":
                return {};
            case "play_snapshot":
                return legacy(this.head);
            case "play_snapshot_v2":
                return this.snapshot;
            case "free_text":
                this.submitted.push(clone(command));
                return this.status("queued");
            case "prepare":
                return this.status("failed", "Agency");
            default:
                throw Error(`Unexpected synthetic operation ${command.op}`);
        }
    }
    status(phase, error = null) {
        const request = this.submitted.at(-1).request;
        return {
            scope: clone(request.scope),
            turn: request.turn,
            expected_revision: request.expected_revision,
            phase,
            error,
            receipt: null,
        };
    }
}

let constructors;
try {
    constructors = {};
    for (const [name, flag] of [
        ["undefined", undefined],
        ["false", "false"],
        ["true", "true"],
    ]) {
        const compiled = await build({
            entryPoints: [
                fileURLToPath(new URL("./ui/controller.ts", import.meta.url)),
            ],
            bundle: true,
            platform: "node",
            format: "esm",
            write: false,
            ...(flag === undefined
                ? {}
                : { define: { __DEV_HARNESS__: flag } }),
        });
        const module = await import(
            `data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].contents).toString("base64")}`
        );
        assert.equal(
            typeof module.Controller.prototype.refreshFreeTextProvider,
            "function",
            "future public refreshFreeTextProvider API is required",
        );
        const controller = new module.Controller(
            new Gateway(),
            undefined,
            "bootstrap-setup",
        );
        assert.equal(
            controller.get().freeTextProvider,
            null,
            "future State.freeTextProvider field is required and starts unready",
        );
        constructors[name] = module.Controller;
    }
} catch (error) {
    throw Error(
        `SETUP failure, not behavioral RED: ${String(error?.message ?? error)}`,
    );
}
function make(flag = "true", permit = true, useThin = false) {
    const gateway = new Gateway(useThin);
    const Controller = constructors[flag];
    const controller =
        permit === OMIT_PERMIT
            ? new Controller(
                  gateway,
                  undefined,
                  "scene-bootstrap-test",
                  (work) => work(),
              )
            : new Controller(
                  gateway,
                  undefined,
                  "scene-bootstrap-test",
                  (work) => work(),
                  permit,
              );
    return { gateway, controller };
}
async function attached(flag = "true", permit = true, useThin = false) {
    const f = make(flag, permit, useThin);
    await f.controller.attach(session());
    await f.controller.refreshModel();
    assert.equal(f.controller.get().model.loaded, false);
    return f;
}
const providerCalls = (g) => g.calls.filter((c) => c.op === "model_status");
const writes = (g) =>
    g.calls.filter((c) =>
        [
            "submit",
            "free_text",
            "prepare",
            "commit",
            "author_preview",
            "author_apply",
        ].includes(c.op),
    );
const tests = [];
const test = (name, run) => tests.push({ name, run });

for (const flag of ["undefined", "false", "true"]) {
    for (const permit of [OMIT_PERMIT, false]) {
        test(`${flag}-build-${String(permit)}-permit-cannot-enable-fixture`, async () => {
            const { controller: c, gateway: g } = await attached(flag, permit);
            try {
                await c.refreshFreeTextProvider();
                assert.equal(providerCalls(g).length, 0);
                assert.equal(c.get().freeTextProvider, null);
                c.setPlayMode("local");
                assert.equal(c.get().playMode, "fixture");
                assert.equal(c.get().visibleError, "ModelUnavailable");
                assert.equal(c.get().model.loaded, false);
                assert.equal(writes(g).length, 0);
            } finally {
                await c.dispose();
            }
        });
    }
}
for (const flag of ["undefined", "false"]) {
    test(`${flag}-build-ignores-explicit-true-development-permit`, async () => {
        const { controller: c, gateway: g } = await attached(flag, true, true);
        try {
            await c.refreshFreeTextProvider();
            assert.equal(providerCalls(g).length, 0);
            assert.equal(c.get().freeTextProvider, null);
            assert.equal(c.get().playV2, null);
            assert.deepEqual(c.get().play, legacy());
            assert.equal(
                g.calls.filter((v) => v.op === "play_snapshot").length,
                1,
            );
            c.setPlayMode("local");
            assert.equal(c.get().visibleError, "ModelUnavailable");
            assert.equal(c.get().model.loaded, false);
        } finally {
            await c.dispose();
        }
    });
}

test("valid-actual-Host-metadata-is-two-field-fixture-readiness-without-model-mutation", async () => {
    const { controller: c, gateway: g } = await attached();
    try {
        const beforeModel = clone(c.get().model);
        const beforeNative = g.nativeCalls.length;
        const beforeReads = providerCalls(g).length;
        await c.refreshFreeTextProvider();
        assert.equal(providerCalls(g).length, beforeReads + 1);
        assert.deepEqual(providerCalls(g).at(-1), { op: "model_status" });
        assert.equal(
            g.nativeCalls.length,
            beforeNative,
            "fixture status uses Host gateway.call, not model-manager native status",
        );
        assert.deepEqual(c.get().freeTextProvider, ready());
        assert.deepEqual(Object.keys(c.get().freeTextProvider).sort(), [
            "kind",
            "provider",
        ]);
        assert.deepEqual(c.get().model, beforeModel);
        assert.equal(c.get().model.loaded, false);
        assert.equal(
            c.get().playMode,
            "fixture",
            "readiness is not automatic mode selection",
        );
        assert.equal(writes(g).length, 0);
    } finally {
        await c.dispose();
    }
});

test("development-permit-alone-does-not-admit-local-before-any-provider-read", async () => {
    const { controller: c, gateway: g } = await attached();
    try {
        assert.equal(c.get().freeTextProvider, null);
        c.setPlayMode("local");
        assert.equal(c.get().playMode, "fixture");
        assert.equal(c.get().visibleError, "ModelUnavailable");
        assert.equal(providerCalls(g).length, 0);
        assert.equal(writes(g).length, 0);
        assert.equal(c.get().model.loaded, false);
    } finally {
        await c.dispose();
    }
});

test("permitted-ready-legacy-controller-sends-actual-free_text-without-loaded-model", async () => {
    const { controller: c, gateway: g } = await attached();
    try {
        await c.refreshFreeTextProvider();
        c.setPlayMode("local");
        assert.equal(c.get().playMode, "local");
        c.setInputKind("dialogue");
        c.setDraft("The quay is quiet.");
        await c.send();
        assert.equal(g.submitted.length, 1);
        const command = g.submitted[0];
        assert.deepEqual(Object.keys(command).sort(), [
            "op",
            "request",
            "session",
        ]);
        assert.equal(command.op, "free_text");
        assert.equal(command.session, session().id);
        assert.deepEqual(command.request, {
            version: 1,
            scope: clone(scope),
            turn: "scene-bootstrap-test-1",
            expected_revision: 0,
            intent: {
                kind: "free_text",
                value: { kind: "dialogue", text: "The quay is quiet." },
            },
        });
        assert.equal(command.mode, undefined);
        assert.equal(command.profile, undefined);
        assert.equal(command.construction, undefined);
        assert.equal(c.get().model.loaded, false);
        assert.equal(c.get().play.revision, 0);
        assert.equal(c.get().pending, null);
        assert.equal(
            c.get().visibleError,
            "Agency",
            "synthetic rejection does not claim native commit",
        );
    } finally {
        await c.dispose();
    }
});

test("ordinary-loaded-model-admission-is-unchanged-in-normal-build", async () => {
    const f = make("false", true);
    const { controller: c, gateway: g } = f;
    g.realLoaded = true;
    try {
        await c.attach(session());
        await c.refreshModel();
        await c.refreshFreeTextProvider();
        c.setPlayMode("local");
        c.setDraft("I wait for one tide tick.");
        await c.send();
        assert.equal(g.submitted.length, 1);
        assert.equal(g.submitted[0].request.intent.kind, "free_text");
        assert.equal(c.get().model.loaded, true);
        assert.equal(c.get().freeTextProvider, null);
        assert.equal(providerCalls(g).length, 0);
    } finally {
        await c.dispose();
    }
});

const badReplies = [
    ["null", () => null],
    ["array", () => []],
    ["wrong-provider", () => ({ ...metadata(), provider: "other" })],
    ["real-model", () => ({ ...metadata(), real_model: true })],
    ["loaded-model", () => ({ ...metadata(), loaded: true })],
    ["wrong-status", () => ({ ...metadata(), status: "configured" })],
    ["extra-top-key", () => ({ ...metadata(), owner: "forged" })],
    [
        "missing-top-key",
        () => {
            const v = metadata();
            delete v.real_model;
            return v;
        },
    ],
    ["null-profile", () => ({ ...metadata(), profile: null })],
    ["array-profile", () => ({ ...metadata(), profile: [] })],
    [
        "missing-profile-id",
        () => ({ ...metadata(), profile: { opaque: true } }),
    ],
    ["wrong-profile-id", () => ({ ...metadata(), profile: { id: "other" } })],
    [
        "profile-oversize",
        () => ({
            ...metadata(),
            profile: { id: FIXED, opaque: "x".repeat(1_048_576) },
        }),
    ],
    [
        "profile-cycle",
        () => {
            const v = metadata();
            v.profile.cycle = v.profile;
            return v;
        },
    ],
    [
        "top-custom-prototype",
        () => Object.assign(Object.create({ inherited: true }), metadata()),
    ],
    [
        "profile-custom-prototype",
        () => ({
            ...metadata(),
            profile: Object.assign(Object.create({ inherited: true }), {
                id: FIXED,
            }),
        }),
    ],
];
for (const [name, invalid] of badReplies) {
    test(`malformed-${name}-clears-readiness-with-Wire-and-no-dispatch`, async () => {
        const { controller: c, gateway: g } = await attached();
        try {
            await c.refreshFreeTextProvider();
            assert.deepEqual(c.get().freeTextProvider, ready());
            g.response = invalid();
            await c.refreshFreeTextProvider();
            assert.equal(c.get().freeTextProvider, null);
            assert.equal(c.get().visibleError, "Wire");
            assert.equal(c.get().model.loaded, false);
            c.setPlayMode("local");
            assert.equal(c.get().playMode, "fixture");
            assert.equal(c.get().visibleError, "ModelUnavailable");
            assert.equal(writes(g).length, 0);
        } finally {
            await c.dispose();
        }
    });
}
for (const kind of [
    "provider-getter",
    "profile-getter",
    "id-getter",
    "nested-getter",
    "toJSON",
]) {
    test(`descriptor-first-${kind}-runs-no-response-code`, async () => {
        const { controller: c, gateway: g } = await attached();
        let invoked = 0;
        try {
            await c.refreshFreeTextProvider();
            const v = metadata();
            const getter = () => {
                invoked++;
                return FIXED;
            };
            if (kind === "provider-getter" || kind === "profile-getter") {
                Object.defineProperty(
                    v,
                    kind === "provider-getter" ? "provider" : "profile",
                    { enumerable: true, get: getter },
                );
            } else if (kind === "id-getter") {
                Object.defineProperty(v.profile, "id", {
                    enumerable: true,
                    get: getter,
                });
            } else if (kind === "nested-getter") {
                Object.defineProperty(v.profile.extra, "private", {
                    enumerable: true,
                    get: getter,
                });
            } else {
                Object.defineProperty(v.profile, "toJSON", {
                    enumerable: false,
                    value() {
                        invoked++;
                        return { id: FIXED };
                    },
                });
            }
            g.response = v;
            await c.refreshFreeTextProvider();
            assert.equal(
                invoked,
                0,
                "inspect data descriptors before reading/stringifying DTOs",
            );
            assert.equal(c.get().freeTextProvider, null);
            assert.equal(c.get().visibleError, "Wire");
            assert.equal(writes(g).length, 0);
        } finally {
            await c.dispose();
        }
    });
}

test("lost-readiness-blocks-legacy-send-while-local-mode-stays-selected", async () => {
    const { controller: c, gateway: g } = await attached();
    try {
        await c.refreshFreeTextProvider();
        c.setPlayMode("local");
        c.setDraft("I wait for one tide tick.");
        g.response = null;
        await c.refreshFreeTextProvider();
        assert.equal(c.get().playMode, "local");
        await c.send();
        assert.equal(c.get().visibleError, "ModelUnavailable");
        assert.equal(c.get().playMode, "local");
        assert.equal(writes(g).length, 0);
        assert.equal(c.get().model.loaded, false);
    } finally {
        await c.dispose();
    }
});

test("dev-permit-retains-actual-checked-Domain1-thin-snapshot-for-V2-route", async () => {
    const { controller: c, gateway: g } = await attached("true", true, true);
    try {
        assert.deepEqual(c.get().playV2, thin());
        assert.equal(c.get().playV2.domain_version, 1);
        assert.equal(c.get().play, null);
        assert.equal(g.calls.filter((v) => v.op === "play_snapshot").length, 0);
        assert.deepEqual(c.semantic().player, thin().player);
        assert.deepEqual(c.semantic().transcript, {
            source: "query2",
            status: "owned_by_scoped_controller",
        });
        assert.equal(c.get().model.loaded, false);
        assert.equal(writes(g).length, 0);
        // Main's actual V2PlayController send is a later integration test.
    } finally {
        await c.dispose();
    }
});

test("dev-without-permit-keeps-existing-Domain1-legacy-route", async () => {
    const { controller: c, gateway: g } = await attached("true", false, true);
    try {
        assert.equal(c.get().playV2, null);
        assert.deepEqual(c.get().play, legacy());
        assert.equal(
            g.calls.filter((v) => v.op === "play_snapshot_v2").length,
            1,
        );
        assert.equal(g.calls.filter((v) => v.op === "play_snapshot").length, 1);
    } finally {
        await c.dispose();
    }
});

test("dev-thin-routing-still-rejects-unchecked-hidden-extra-fields", async () => {
    const { controller: c, gateway: g } = make("true", true, true);
    g.snapshot = { ...thin(), facts: { private: "SYNTHETIC_PRIVATE_TRUTH" } };
    try {
        await c.attach(session());
        assert.equal(c.get().visibleError, "Wire");
        assert.equal(c.get().playV2, null);
        assert.equal(c.get().play, null);
        assert.equal(g.calls.filter((v) => v.op === "play_snapshot").length, 0);
        assert.equal(writes(g).length, 0);
    } finally {
        await c.dispose();
    }
});

for (const oldBad of [false, true]) {
    test(`older-${oldBad ? "bad" : "valid"}-provider-read-cannot-overwrite-newer-${oldBad ? "ready" : "Wire"}`, async () => {
        const { controller: c, gateway: g } = await attached();
        const old = deferred();
        try {
            g.providerRead = () => old.promise;
            const first = c.refreshFreeTextProvider();
            await drain();
            g.providerRead = null;
            g.response = oldBad ? metadata() : null;
            await c.refreshFreeTextProvider();
            const currentErrors = c.errors.snapshot();
            old.resolve(oldBad ? null : metadata());
            await first;
            assert.deepEqual(c.get().freeTextProvider, oldBad ? ready() : null);
            assert.equal(c.get().visibleError, oldBad ? null : "Wire");
            assert.equal(c.get().model.loaded, false);
            assert.deepEqual(
                c.errors.snapshot(),
                currentErrors,
                "obsolete reads cannot add obsolete Wire evidence",
            );
        } finally {
            old.resolve(null);
            await c.dispose();
        }
    });
}

test("provider-read-sequence-is-independent-of-ordinary-model-refresh", async () => {
    const { controller: c, gateway: g } = await attached();
    const held = deferred();
    try {
        g.providerRead = () => held.promise;
        const read = c.refreshFreeTextProvider();
        await drain();
        await c.refreshModel();
        held.resolve(metadata());
        await read;
        assert.deepEqual(c.get().freeTextProvider, ready());
        assert.deepEqual(c.get().model, nativeModel(false));
        assert.equal(writes(g).length, 0);
    } finally {
        held.resolve(null);
        await c.dispose();
    }
});

test("late-provider-rejection-cannot-poison-newer-ready-state", async () => {
    const { controller: c, gateway: g } = await attached();
    const held = deferred();
    try {
        g.providerRead = () => held.promise;
        const read = c.refreshFreeTextProvider();
        await drain();
        g.providerRead = null;
        await c.refreshFreeTextProvider();
        const currentErrors = c.errors.snapshot();
        held.reject(Error("Wire"));
        await read;
        assert.deepEqual(c.get().freeTextProvider, ready());
        assert.equal(c.get().visibleError, null);
        assert.deepEqual(c.errors.snapshot(), currentErrors);
    } finally {
        held.resolve(null);
        await c.dispose();
    }
});

test("disposed-controller-refuses-new-provider-read-and-late-publication", async () => {
    const { controller: c, gateway: g } = await attached();
    await c.refreshFreeTextProvider();
    assert.deepEqual(c.get().freeTextProvider, ready());
    const held = deferred();
    g.providerRead = () => held.promise;
    const read = c.refreshFreeTextProvider();
    await drain();
    const disposal = c.dispose();
    await drain();
    held.resolve(metadata());
    await Promise.all([read, disposal]);
    assert.equal(c.get().disposed, true);
    assert.equal(c.get().freeTextProvider, null);
    const before = providerCalls(g).length;
    await c.refreshFreeTextProvider();
    assert.equal(providerCalls(g).length, before);
    assert.equal(c.get().freeTextProvider, null);
});

test("malformed-provider-errors-are-bounded-categories-without-profile-payload", async () => {
    const { controller: c, gateway: g } = await attached();
    try {
        g.response = {
            ...metadata(),
            provider: "SYNTHETIC_PRIVATE_METADATA_MUST_NOT_BE_LOGGED",
        };
        for (let i = 0; i < 80; i++) await c.refreshFreeTextProvider();
        assert.equal(c.get().freeTextProvider, null);
        assert.equal(c.get().visibleError, "Wire");
        const errors = c.errors.snapshot();
        assert.ok(errors.length > 0 && errors.length <= 64);
        assert.ok(errors.every((error) => error.category === "Wire"));
        assert.ok(
            !JSON.stringify(errors).includes("SYNTHETIC_PRIVATE_METADATA"),
        );
        assert.equal(writes(g).length, 0);
    } finally {
        await c.dispose();
    }
});

const failures = [];
for (const { name, run } of tests) {
    try {
        await run();
    } catch (error) {
        failures.push(`${name}: ${String(error?.message ?? error)}`);
    }
}
assert.deepEqual(
    failures,
    [],
    "frozen development scene bootstrap Controller oracles",
);
console.log(
    `PASS ${tests.length} Controller-only scene bootstrap cases; synthetic Gateway, no native/model/render evidence.`,
);

// ADDITIVE FIRST DISPOSAL-WINDOW FREEZE: SOURCE ONLY / UNRUN at handoff.
// Preserve the original 43 cases/runner above. These public Controller checks
// start after dispose() is CALLED, not only after its Promise has completed.
const disposalCaseStart = tests.length;

test("dispose-called-same-tick-admits-no-new-provider-status-read", async () => {
    const { controller: c, gateway: g } = await attached();
    let closing, reading;
    try {
        await c.refreshFreeTextProvider();
        assert.deepEqual(c.get().freeTextProvider, ready());
        const beforeCalls = providerCalls(g).length;
        const beforeErrors = c.errors.snapshot();
        closing = c.dispose();
        // Intentionally no await/drain between these public calls.
        reading = c.refreshFreeTextProvider();
        const admittedCalls = providerCalls(g).length - beforeCalls;
        await Promise.all([reading, closing]);
        assert.equal(admittedCalls, 0, "disposal admission must close synchronously before invalidate() yields");
        assert.equal(c.get().freeTextProvider, null);
        assert.equal(c.get().disposed, true);
        assert.deepEqual(c.errors.snapshot(), beforeErrors);
        assert.equal(writes(g).length, 0);
    } finally {
        await Promise.allSettled([reading, closing].filter(Boolean));
        await c.dispose();
    }
});

test("held-legacy-cancel-disposal-window-cannot-resurrect-provider-readiness-or-errors", async () => {
    const observations = [];
    for (const reply of ["valid", "malformed"]) {
        const { controller: c, gateway: g } = await attached();
        const prepare = deferred();
        const cancel = deferred();
        let preparationEntered = false;
        let cancellationEntered = false;
        let closingSettled = false;
        let sending, closing, reading;
        const ordinaryCall = g.call.bind(g);
        g.call = async (command) => {
            if (command.op === "prepare") {
                g.calls.push(clone(command));
                preparationEntered = true;
                return prepare.promise;
            }
            if (command.op === "cancel") {
                g.calls.push(clone(command));
                cancellationEntered = true;
                return cancel.promise;
            }
            return ordinaryCall(command);
        };
        try {
            await c.refreshFreeTextProvider();
            c.setPlayMode("local");
            c.setDraft("I wait for one tide tick.");
            sending = c.send();
            await drain();
            assert.equal(preparationEntered, true, "actual legacy send must enter its held prepare");
            assert.equal(g.submitted.length, 1);
            closing = c.dispose();
            void closing.then(
                () => { closingSettled = true; },
                () => { closingSettled = true; },
            );
            await drain();
            assert.equal(cancellationEntered, true, "actual invalidate must cancel the original admitted request");
            assert.equal(closingSettled, false, "the held legacy cancel keeps actual disposal in flight");
            assert.equal(c.get().disposed, false, "preserve existing legacy cancellation before terminal disposal");
            assert.equal(c.get().freeTextProvider, null);
            const beforeCalls = providerCalls(g).length;
            const beforeErrors = c.errors.snapshot();
            const beforeVisibleError = c.get().visibleError;
            g.response = reply === "valid" ? metadata() : null;
            reading = c.refreshFreeTextProvider();
            await reading;
            observations.push({
                reply,
                admittedCalls: providerCalls(g).length - beforeCalls,
                readiness: c.get().freeTextProvider,
                errors: c.errors.snapshot(),
                beforeErrors,
                visibleError: c.get().visibleError,
                beforeVisibleError,
                loaded: c.get().model.loaded,
            });
        } finally {
            // Release every held actual Gateway call even when an assertion
            // fails. Both returns keep the original scope/turn/revision.
            const request = g.submitted.at(-1)?.request;
            const cancelled = request ? {
                scope: clone(request.scope), turn: request.turn,
                expected_revision: request.expected_revision,
                phase: "cancelled", error: null, receipt: null,
            } : null;
            cancel.resolve(cancelled);
            prepare.resolve(cancelled);
            await Promise.allSettled([reading, sending, closing].filter(Boolean));
            await c.dispose();
        }
        assert.equal(c.get().freeTextProvider, null);
        assert.equal(c.get().disposed, true);
    }
    assert.equal(observations.length, 2);
    for (const observation of observations) {
        assert.equal(observation.admittedCalls, 0, `${observation.reply}: no Host metadata admission after dispose-called`);
        assert.equal(observation.readiness, null, `${observation.reply}: no readiness resurrection during legacy cancellation`);
        assert.deepEqual(observation.errors, observation.beforeErrors, `${observation.reply}: no obsolete error evidence`);
        assert.equal(observation.visibleError, observation.beforeVisibleError);
        assert.equal(observation.loaded, false);
    }
});

const disposalFailures = [];
for (const { name, run } of tests.slice(disposalCaseStart)) {
    try { await run(); }
    catch (error) { disposalFailures.push(`${name}: ${String(error?.message ?? error)}`); }
}
assert.deepEqual(disposalFailures, [], "additive dispose-called provider admission fences");
console.log(`PASS ${tests.length - disposalCaseStart} additive Controller disposal-window cases; synthetic Gateway only.`);
