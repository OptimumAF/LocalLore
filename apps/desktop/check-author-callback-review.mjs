// Independent frozen actual-controller vectors. Synthetic transport only; no IPC/app/model.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { createHash, randomUUID, webcrypto } from "node:crypto";

globalThis.crypto ??= webcrypto;
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("./artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(
    directory,
    `author-callback-review-${randomUUID()}.mjs`,
);
const bundle = await build({
    entryPoints: [
        fileURLToPath(new URL("./ui/author-controller.ts", import.meta.url)),
    ],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(target, bundle.outputFiles[0].contents);
const { AuthorController } = await import(pathToFileURL(target).href);
const clone = (v) => JSON.parse(JSON.stringify(v));
const context = () => ({
    rootIncarnation: "review-root",
    selectionEpoch: 1,
    session: "review-session",
    scope: { story: "review-story", branch: "main" },
    head: 3,
    player: "player",
    observer: "omniscient",
    view: "lab",
    persistent: true,
    spoilerGranted: true,
    pending: false,
    brokerUncertain: false,
});
const draft = () => ({
    fork_revision: 1,
    child_branch: "review-child",
    fact: "relic-location",
    expected_proposition: "SYNTHETIC_OLD_A",
    replacement: "SYNTHETIC_NEW_B",
    reason: "SYNTHETIC_PRIVATE_REASON",
});
const status = (id, result) => ({
    version: 1,
    operation_id: id,
    running: false,
    phase: "completed",
    error: null,
    result,
});
const errorStatus = (id) => ({
    version: 1,
    operation_id: id,
    running: false,
    phase: "error",
    error: "Busy",
    result: null,
});
function preview(input, session, token) {
    const core = {
        version: 1,
        input: clone(input),
        child: { story: input.parent.story, branch: input.child_branch },
        before: {
            fact: input.operation.fact,
            proposition: input.operation.expected_proposition,
            source: {
                kind: "seed_fact",
                seed_id: "synthetic-review",
                fact: input.operation.fact,
            },
        },
        creation_revision: input.fork_revision + 1,
        retained_knowers: 2,
        excluded_suffix_events:
            input.expected_parent_revision - input.fork_revision,
        excluded_suffix_records: 1,
        original_preserved: true,
        downstream_replayed: false,
        new_child_requires_fresh_derivatives: true,
    };
    const json = JSON.stringify(core);
    return {
        version: 1,
        kind: "author_preview",
        session,
        preview_token: token,
        preview_sha256: createHash("sha256").update(json).digest("hex"),
        preview_json: json,
        expires_seconds: 600,
    };
}
function outcome(input, created) {
    return {
        version: 1,
        scope: { story: input.parent.story, branch: input.child_branch },
        parent: clone(input.parent),
        fork_revision: input.fork_revision,
        author_revision: input.fork_revision + 1,
        head_revision: input.fork_revision + 1,
        created,
    };
}
class Port {
    next = 0;
    prepares = 0;
    calls = [];
    cancels = [];
    discards = [];
    caps = new Set();
    failKind = null;
    lookupFound = true;
    prepareStart = async (raw) => {
        const request = JSON.parse(raw),
            id = ++this.next;
        this.calls.push({ kind: "prepare", request });
        this.prepares++;
        if (this.failKind === "prepare") return errorStatus(id);
        if (this.caps.size >= 4) throw Error("AuthorPreviewLimit");
        const token = randomUUID();
        this.caps.add(token);
        return status(id, preview(request.input, request.session, token));
    };
    commitStart = async (raw) => {
        const request = JSON.parse(raw),
            id = ++this.next;
        this.calls.push({ kind: "commit", request });
        this.caps.delete(request.preview_token);
        if (this.failKind === "commit") return errorStatus(id);
        return status(id, {
            version: 1,
            kind: "author_commit",
            session: request.session,
            outcome: outcome(request.input, true),
        });
    };
    lookupStart = async (raw) => {
        const request = JSON.parse(raw),
            id = ++this.next;
        this.calls.push({ kind: "lookup", request });
        if (this.failKind === "lookup") return errorStatus(id);
        return status(id, {
            version: 1,
            kind: "author_lookup",
            found: this.lookupFound,
            outcome: this.lookupFound ? outcome(request.input, false) : null,
        });
    };
    status = async () => {
        throw Error("UnknownArchiveOperation");
    };
    cancel = async (id) => {
        this.cancels.push(id);
        return errorStatus(id);
    };
    discardPreview = async (session, token) => {
        this.discards.push({ session, token });
        return this.caps.delete(token);
    };
}
function fixture() {
    const port = new Port(),
        effects = { refreshed: [], opened: [] };
    const controller = new AuthorController(
        port,
        {
            refreshLibrary: async () => {
                effects.refreshed.push(true);
            },
            openChild: async (scope) => {
                effects.opened.push(scope);
            },
        },
        async () => {},
    );
    controller.contextChanged(context());
    controller.setDraft(draft());
    return { controller, port, effects };
}
async function prepared(f) {
    f.controller.setAuthorConsent(true);
    await f.controller.prepare();
    assert.equal(
        f.controller.get().status,
        "preview",
        "valid actual decoder accepted synthetic preview",
    );
    f.controller.setPreviewRead(true);
}
const results = [];
async function test(name, body) {
    const f = fixture();
    try {
        await body(f);
        results.push({ name, passed: true });
    } catch (error) {
        results.push({
            name,
            passed: false,
            message: String(error?.message ?? error),
        });
    } finally {
        f.controller.dispose();
    }
}
function onceOnOperation(f, action) {
    let fired = false;
    const release = f.controller.subscribe(() => {
        if (!fired && f.controller.get().busy && f.controller.get().operation) {
            fired = true;
            action();
        }
    });
    return () => {
        release();
        assert.ok(fired, "synchronous operation notification was exercised");
    };
}
function onceOnSavedResult(f, action) {
    let fired = false;
    const release = f.controller.subscribe(() => {
        if (!fired && f.controller.get().status === "complete") {
            fired = true;
            action();
        }
    });
    return () => {
        release();
        assert.ok(fired, "synchronous saved-result notification was exercised");
    };
}

await test("old terminal prepare error cannot overwrite a different root", async (f) => {
    f.port.failKind = "prepare";
    const next = {
        ...context(),
        rootIncarnation: "new-review-root",
        selectionEpoch: 2,
        session: "new-session",
    };
    const release = onceOnOperation(f, () => f.controller.contextChanged(next));
    f.controller.setAuthorConsent(true);
    await f.controller.prepare();
    release();
    assert.ok(f.controller.matchesContext(next));
    assert.equal(
        f.controller.get().error,
        null,
        "old terminal error is absent from new root",
    );
    assert.equal(f.controller.get().status, "idle");
    assert.equal(f.controller.get().input, null);
});
await test("old terminal lookup error cannot clear a new selection's uncertainty", async (f) => {
    await prepared(f);
    f.port.failKind = "lookup";
    const next = {
        ...context(),
        selectionEpoch: 2,
        session: "other-session",
        head: 4,
    };
    const release = onceOnOperation(f, () => f.controller.contextChanged(next));
    await f.controller.lookup();
    release();
    assert.ok(f.controller.matchesContext(next));
    assert.equal(f.controller.get().error, null);
    assert.equal(
        f.controller.get().uncertain,
        true,
        "contextChanged pending recovery state survives the old callback",
    );
    assert.equal(f.controller.get().status, "uncertain");
});
await test("terminal error notification disposal stays closed", async (f) => {
    f.port.failKind = "prepare";
    const release = onceOnOperation(f, () => f.controller.dispose());
    f.controller.setAuthorConsent(true);
    await f.controller.prepare();
    release();
    assert.equal(f.controller.get().available, false);
    assert.equal(f.controller.get().error, null);
    assert.equal(f.effects.refreshed.length, 0);
});
for (const kind of ["commit", "lookup"]) {
    for (const retire of ["switch", "dispose"]) {
        await test(`${kind} saved-result ${retire} prevents stale library refresh`, async (f) => {
            await prepared(f);
            const next = {
                ...context(),
                selectionEpoch: 2,
                session: "other-session",
                scope: { story: "other-story", branch: "main" },
            };
            const release = onceOnSavedResult(f, () =>
                retire === "dispose"
                    ? f.controller.dispose()
                    : f.controller.contextChanged(next),
            );
            if (kind === "commit") await f.controller.confirm(true);
            else await f.controller.lookup();
            release();
            assert.equal(
                f.effects.refreshed.length,
                0,
                "no native presentation effect after retirement",
            );
            assert.equal(
                f.effects.opened.length,
                0,
                "never auto-open an old child",
            );
            assert.equal(f.controller.get().outcome, null);
        });
    }
    await test(`live ${kind} completion refreshes exactly once without auto-open`, async (f) => {
        await prepared(f);
        if (kind === "commit") await f.controller.confirm(true);
        else await f.controller.lookup();
        assert.equal(f.controller.get().status, "complete");
        assert.equal(
            f.controller.get().outcome.scope.branch,
            draft().child_branch,
        );
        assert.equal(f.effects.refreshed.length, 1);
        assert.equal(f.effects.opened.length, 0);
    });
}
await test("stale completed prepare is discarded, never presented in a new context", async (f) => {
    const next = { ...context(), selectionEpoch: 2, session: "other-session" };
    const release = onceOnOperation(f, () => f.controller.contextChanged(next));
    f.controller.setAuthorConsent(true);
    await f.controller.prepare();
    release();
    assert.equal(f.controller.get().preview, null);
    assert.equal(f.port.discards.length, 1);
    assert.equal(f.port.caps.size, 0);
    assert.equal(f.effects.refreshed.length, 0);
});
for (const found of [false, true]) {
    await test(`read-only lookup found=${found} retains or retires an unused native preview`, async (f) => {
        await prepared(f);
        const previous = f.controller.get().preview;
        f.port.lookupFound = found;
        await f.controller.lookup();
        const retained = f.controller.get().preview;
        const discarded = f.port.discards.filter(
            (d) => d.token === previous.preview_token,
        );
        assert.ok(
            retained?.preview_token === previous.preview_token ||
                discarded.length === 1,
            "a disappearing presentation must not abandon the native capability until TTL",
        );
        if (retained?.preview_token === previous.preview_token) {
            assert.ok(f.port.caps.has(previous.preview_token));
        } else {
            assert.equal(f.port.caps.has(previous.preview_token), false);
        }
        assert.equal(f.port.calls.filter((c) => c.kind === "commit").length, 0);
    });
}
await test("repeated prepare/lookup cannot exhaust four abandoned preview slots", async (f) => {
    f.port.lookupFound = false;
    for (let i = 0; i < 5; i++) {
        await prepared(f);
        await f.controller.lookup();
        assert.ok(
            f.port.caps.size <= 1,
            "only a visibly owned preview may remain",
        );
    }
    assert.equal(f.port.prepares, 5);
    assert.equal(f.port.calls.filter((c) => c.kind === "commit").length, 0);
});
console.log(
    JSON.stringify(
        {
            source: "aa8d56c",
            synthetic_transport: true,
            native_execution: false,
            cases: results,
        },
        null,
        2,
    ),
);
if (results.some((r) => !r.passed)) process.exitCode = 1;
