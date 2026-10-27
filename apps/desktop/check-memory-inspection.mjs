// Frozen SOURCE ONLY before frontend implementation; UNCOMPILED/UNRUN.
// Source-shaped synthetic DTOs + actual controller/decoder and React SSR.
// No Rust acceptance, native IPC, WebView/pixels, provider/model/device proof.
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
const built = await build({
    stdin: {
        contents: `
export * from './ui/memory-inspection-model';
export * from './ui/memory-inspection-controller';
export * from './ui/MemoryInspectionPanel';
export {createElement} from 'react';
export {renderToStaticMarkup} from 'react-dom/server';`,
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
const bundle = path.join(output, `memory-inspection-${randomUUID()}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const m = (await import(pathToFileURL(bundle).href)).default;
const clone = (v) => structuredClone(v),
    hash = "a".repeat(64),
    otherHash = "b".repeat(64);
const scope = { story: "synthetic-inspection", branch: "main" };
const context = {
    session: "session-1",
    scope,
    expected_head: 64,
    player: "player",
    observer: "player",
    view: "lab",
    epoch: 1,
    persistent: true,
    domainVersion: 1,
    lab: true,
};
const coverage = {
    status: "verified",
    verified_head: 64,
    covered_through: 64,
    raw_delta_after: 64,
    fallback: null,
};
const packet = (index) => ({
    kind: "packet",
    index,
    version: 2,
    method: "deterministic-event-extractive-v2",
    from_exclusive: index * 2,
    through_revision: index * 2 + 2,
    receipt_count: 1,
    closure: { kind: "open_tail" },
    entry_count: 2,
    source_event_count: 2,
});
const descriptor = packet(0),
    ref = { scope, sequence: 1 };
const meta = {
    kind: "memory_inspection",
    version: 1,
    session: context.session,
    scope,
    head: 64,
    observer: "player",
    privacy: "player_visible",
    binding: hash,
    coverage,
    view: "packets",
    packet_index: null,
    total: 32,
    rows: Array.from({ length: 16 }, (_, i) => packet(i)),
    next_cursor: `mp1:16:${otherHash}`,
};
const event = {
    version: 1,
    scope,
    sequence: 1,
    turn: "typed-1",
    rules: "fantasy_v1",
    seed: "lantern-quay-v1",
    story_time: 100,
    participants: ["player"],
    witnesses: ["player"],
    outcome: {
        effect: "said",
        speaker: "player",
        text: "<script>literal 🌊\ncontrol</script>",
        audience: ["player"],
        source: 1,
    },
};
const entries = {
    ...meta,
    view: "entries",
    packet_index: 0,
    total: 2,
    rows: [
        {
            kind: "entry",
            packet_index: 0,
            index: 0,
            value: {
                class: "observation",
                origin: "statement",
                source: ref,
                event,
            },
        },
        {
            kind: "entry",
            packet_index: 0,
            index: 1,
            value: {
                class: "observed_time_span",
                from: 100,
                to: 101,
                source_events: [{ scope, sequence: 2 }],
            },
        },
    ],
    next_cursor: null,
};
const source = {
    kind: "memory_source",
    version: 1,
    session: context.session,
    scope,
    head: 64,
    observer: "player",
    privacy: "player_visible",
    binding: hash,
    packet_index: 0,
    source: ref,
    matched: true,
    page: {
        version: 2,
        scope,
        head: 64,
        revision: 2,
        story_time: 101,
        observer: { kind: "player" },
        view: "history",
        privacy: "player_visible",
        status: "supported",
        total: 1,
        rows: [
            {
                kind: "event",
                key: "event-original-1",
                event: {
                    sequence: 1,
                    scope,
                    turn: "typed-1",
                    story_time: 100,
                    participants: ["player"],
                    witnesses: ["player"],
                    consequence: event.outcome,
                },
                origin: "recorded_observation",
            },
        ],
        next_cursor: null,
        unsupported: [],
    },
};
const read = { action: "packets", binding: null, cursor: null, limit: 16 };
const readEntries = {
    action: "entries",
    binding: hash,
    cursor: null,
    limit: 16,
    packet: descriptor,
};
const readSource = {
    action: "source",
    binding: hash,
    packet: descriptor,
    source: ref,
};
const checks = [];
async function check(name, fn) {
    try {
        await fn();
        checks.push({ name, passed: true });
    } catch (error) {
        checks.push({
            name,
            passed: false,
            error: String(error.message ?? error).slice(0, 500),
        });
    }
}
const rejected = (v, c = context, r = read) =>
    assert.throws(() => m.checkedMemoryInspection(v, c, r), /Wire/);
function deferred() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
function fixture(transport) {
    const calls = [];
    const c = new m.MemoryInspectionController(async (command, args) => {
        calls.push({ command, args: clone(args) });
        return transport
            ? transport(command, args)
            : clone(
                  args.action === "packets"
                      ? meta
                      : args.action === "entries"
                        ? entries
                        : source,
              );
    });
    c.contextChanged(clone(context));
    return { c, calls };
}
async function selected() {
    const f = fixture();
    await f.c.refresh();
    await f.c.selectPacket(0);
    return f;
}

await check(
    "closed metadata uses actual native player, partial page and immutable copy",
    () => {
        const input = clone(meta),
            actual = m.checkedMemoryInspection(input, context, read);
        input.rows[0].method = "changed";
        assert.equal(actual.rows[0].method, descriptor.method);
        assert(Object.isFrozen(actual));
        assert(Object.isFrozen(actual.rows));
        assert.equal(actual.total, 32);
    },
);
await check(
    "actual entry shape keeps statements/time-span/Unicode inert",
    () => {
        const value = m.checkedMemoryInspection(entries, context, readEntries);
        assert.equal(value.rows[0].value.origin, "statement");
        assert.equal(
            value.rows[0].value.event.outcome.text,
            event.outcome.text,
        );
        assert.equal(value.rows[1].value.source_events[0].sequence, 2);
    },
);
await check(
    "source validates ACTUAL Page2 against retained through revision",
    () => {
        const value = m.checkedMemoryInspection(source, context, readSource);
        assert.equal(value.page.revision, descriptor.through_revision);
        assert.equal(value.matched, true);
    },
);
for (const [name, mutate] of [
    ["unknown authority key", (v) => (v.consent = true)],
    ["session mismatch", (v) => (v.session = "session-other")],
    ["scope mismatch", (v) => (v.scope.branch = "other")],
    ["head mismatch", (v) => (v.head = 63)],
    ["native player mismatch", (v) => (v.observer = "mira")],
    ["unsafe integer", (v) => (v.head = 9007199254740992)],
    ["fractional count", (v) => (v.total = 1.5)],
    ["privacy mismatch", (v) => (v.privacy = "private_omniscient")],
    ["packet method mismatch", (v) => (v.rows[0].method = "invented")],
    ["packet version mismatch", (v) => (v.rows[0].version = 1)],
    ["packet field injection", (v) => (v.rows[0].seed = "PRIVATE")],
    ["duplicate row identity", (v) => (v.rows[1] = clone(v.rows[0]))],
    ["cursor namespace", (v) => (v.next_cursor = `2:16:${hash}`)],
    ["cursor noncanonical offset", (v) => (v.next_cursor = `mp1:016:${hash}`)],
    ["cursor wrong offset", (v) => (v.next_cursor = `mp1:17:${hash}`)],
    ["coverage impossible range", (v) => (v.coverage.covered_through = 65)],
    ["whole UTF8 reply cap", (v) => (v.rows[0].method = "界".repeat(22000))],
])
    await check(`decoder rejects ${name}`, () => {
        const v = clone(meta);
        mutate(v);
        rejected(v);
    });
await check("descriptor binding mismatch rejects entry reply", () => {
    const v = clone(entries);
    v.binding = otherHash;
    rejected(v, context, readEntries);
});
await check("entry packet mismatch rejects", () => {
    const v = clone(entries);
    v.packet_index = 1;
    rejected(v, context, readEntries);
});
await check("entry effect closed shape/type and origin are checked", () => {
    for (const change of [
        (v) => (v.rows[0].value.event.outcome.path = "x"),
        (v) => (v.rows[0].value.event.outcome.source = "1"),
        (v) => (v.rows[0].value.origin = "belief"),
        (v) => (v.rows[0].value.source.sequence = 2),
        (v) => (v.rows[0].value.event.story_time = 9007199254740992),
    ]) {
        const v = clone(entries);
        change(v);
        rejected(v, context, readEntries);
    }
});
await check(
    "source wrong returned revision does not become its own expected revision",
    () => {
        const v = clone(source);
        v.page.revision = 64;
        rejected(v, context, readSource);
    },
);
await check("source false/foreign/missing exact match rejected", () => {
    for (const change of [
        (v) => (v.matched = false),
        (v) => (v.source.scope = { ...v.source.scope, branch: "foreign" }),
        (v) =>
            (v.page.rows[0].event.scope = {
                ...v.page.rows[0].event.scope,
                branch: "foreign",
            }),
        (v) => (v.page.rows = []),
    ]) {
        const v = clone(source);
        change(v);
        rejected(v, context, readSource);
    }
});
await check("inherited same-story original source branch is preserved", () => {
    const v = clone(source),
        r = clone(readSource);
    // structuredClone preserves aliases inside each fixture. Replace the source
    // scopes so this case cannot also mutate the selected Page2/envelope scope.
    v.source.scope = { ...v.source.scope, branch: "ancestor" };
    v.page.rows[0].event.scope = {
        ...v.page.rows[0].event.scope,
        branch: "ancestor",
    };
    r.source.scope = { ...r.source.scope, branch: "ancestor" };
    assert.deepEqual(v.scope, context.scope);
    assert.deepEqual(v.page.scope, context.scope);
    assert.equal(
        m.checkedMemoryInspection(v, context, r).source.scope.branch,
        "ancestor",
    );
});
await check(
    "prototype/accessor/symbol and own constructor authority rejected without getters",
    () => {
        let accessed = 0;
        const getter = clone(meta);
        Object.defineProperty(getter, "consent", {
            get() {
                accessed++;
                return true;
            },
            enumerable: true,
        });
        rejected(getter);
        assert.equal(accessed, 0);
        const hostile = Object.assign(
            Object.create({ grant: true }),
            clone(meta),
        );
        rejected(hostile);
        const symbol = clone(meta);
        symbol[Symbol("grant")] = true;
        rejected(symbol);
        const extra = clone(meta);
        Object.defineProperty(extra, "__proto__", {
            value: { grant: true },
            enumerable: true,
        });
        rejected(extra);
    },
);
await check(
    "raw fallback exposes no packets and valid prefix stays verified",
    () => {
        const v = clone(meta);
        v.coverage = {
            status: "raw_fallback",
            verified_head: null,
            covered_through: null,
            raw_delta_after: 0,
            fallback: "missing",
        };
        v.rows = [];
        v.total = 0;
        v.next_cursor = null;
        assert.equal(
            m.checkedMemoryInspection(v, context, read).coverage.fallback,
            "missing",
        );
        v.rows = [packet(0)];
        v.total = 1;
        rejected(v);
        const prefix = clone(meta);
        prefix.coverage.covered_through = 32;
        prefix.coverage.raw_delta_after = 32;
        prefix.total = 16;
        prefix.next_cursor = null;
        assert.equal(
            m.checkedMemoryInspection(prefix, context, read).coverage.status,
            "verified",
        );
    },
);
await check(
    "actual controller sends only closed raw-string read envelopes",
    async () => {
        const { c, calls } = await selected();
        await c.source(ref);
        assert.deepEqual(
            calls.map((v) => v.command),
            ["memory_inspection", "memory_inspection", "memory_inspection"],
        );
        const raw = calls.map((v) => JSON.parse(v.args.request));
        assert.deepEqual(raw[0], {
            version: 1,
            session: context.session,
            scope,
            expected_head: 64,
            observer: { kind: "player" },
            binding: null,
            cursor: null,
            limit: 16,
        });
        assert.equal(raw[1].binding, hash);
        assert.equal(raw[1].packet_index, 0);
        assert.deepEqual(raw[2], {
            version: 1,
            session: context.session,
            scope,
            expected_head: 64,
            observer: { kind: "player" },
            binding: hash,
            packet_index: 0,
            source: ref,
        });
        assert.equal(c.get().source.page.revision, 2);
        assert.equal(c.get().busy, false);
    },
);
await check(
    "packet paging preserves retained selected descriptor for source",
    async () => {
        const { c, calls } = await selected();
        // Separate source-shaped metadata page, same snapshot; selected0 is no
        // longer in the visible second page but must retain its checked descriptor.
        const f = fixture((_command, args) => {
            if (args.action !== "packets")
                return clone(args.action === "entries" ? entries : source);
            const q = JSON.parse(args.request);
            return q.cursor
                ? {
                      ...clone(meta),
                      rows: Array.from({ length: 16 }, (_, i) =>
                          packet(i + 16),
                      ),
                      next_cursor: null,
                  }
                : clone(meta);
        });
        await f.c.refresh();
        await f.c.selectPacket(0);
        await f.c.packetPage(meta.next_cursor);
        await f.c.source(ref);
        assert.equal(f.c.get().selected.index, 0);
        assert.equal(f.c.get().source.page.revision, 2);
        assert.equal(
            JSON.parse(f.calls[2].args.request).cursor,
            meta.next_cursor,
        );
        c.dispose();
        assert.equal(calls.length, 2);
    },
);
for (const [name, delta] of [
    ["NPC lens", { observer: "mira" }],
    ["grant", { lab: false }],
    ["play view", { view: "play" }],
    ["unsaved", { persistent: false }],
    ["Domain2", { domainVersion: 2 }],
]) {
    await check(
        `ineligible ${name} clears old data and sends no new read`,
        async () => {
            const { c, calls } = await selected();
            c.contextChanged({ ...clone(context), ...delta });
            assert.equal(c.get().packets, null);
            assert.equal(c.get().entries, null);
            assert.equal(c.canRead(), false);
            await c.refresh();
            assert.equal(calls.length, 2);
        },
    );
}
for (const [name, delta] of [
    ["head", { expected_head: 65 }],
    ["epoch", { epoch: 3 }],
    ["session", { session: "session-2" }],
    ["scope", { scope: { ...scope, branch: "other" } }],
]) {
    await check(`held old reply retired by ${name}`, async () => {
        const hold = deferred(),
            { c } = fixture(() => hold.promise);
        const work = c.refresh();
        c.contextChanged({ ...clone(context), ...delta });
        hold.resolve(clone(meta));
        await work;
        assert.equal(c.get().packets, null);
        assert.equal(c.get().busy, false);
        assert.equal(c.get().error, null);
    });
}
for (const action of ["dispose", "clear", "context"]) {
    await check(`synchronous pending ${action} prevents dispatch`, async () => {
        const { c, calls } = fixture();
        let once = true;
        c.subscribe(() => {
            if (once && c.get().busy) {
                once = false;
                if (action === "dispose") c.dispose();
                else if (action === "clear") c.clear();
                else c.contextChanged({ ...clone(context), observer: "mira" });
            }
        });
        await c.refresh();
        assert.equal(calls.length, 0);
        assert.equal(c.get().packets, null);
    });
}
await check(
    "dispose fences held source reply and sends no invented native cancellation",
    async () => {
        const hold = deferred(),
            f = fixture((_command, args) =>
                args.action === "source"
                    ? hold.promise
                    : clone(args.action === "entries" ? entries : meta),
            );
        await f.c.refresh();
        await f.c.selectPacket(0);
        const work = f.c.source(ref);
        f.c.dispose();
        hold.resolve(clone(source));
        await work;
        assert.equal(f.c.get().source, null);
        assert(f.calls.every((v) => v.command === "memory_inspection"));
    },
);
await check(
    "current binding error clears private data until explicit fresh read",
    async () => {
        let fail = false;
        const f = fixture((_command, args) => {
            if (fail) throw Error("Binding");
            return clone(args.action === "entries" ? entries : meta);
        });
        await f.c.refresh();
        await f.c.selectPacket(0);
        fail = true;
        await f.c.source(ref);
        assert.equal(f.c.get().error, "Binding");
        for (const field of ["packets", "selected", "entries", "source"])
            assert.equal(f.c.get()[field], null);
        const count = f.calls.length;
        await f.c.selectPacket(0);
        assert.equal(f.calls.length, count);
        fail = false;
        await f.c.refresh();
        assert.equal(f.c.get().error, null);
        assert(f.c.get().packets);
    },
);
await check("arbitrary source and unknown packet cannot dispatch", async () => {
    const f = await selected();
    const count = f.calls.length;
    await f.c.source({ scope: { ...scope, branch: "foreign" }, sequence: 1 });
    await f.c.selectPacket(31);
    assert.equal(f.calls.length, count);
});
await check(
    "SSR shows actual source/escaped text and no mutation/consent controls",
    async () => {
        const f = await selected();
        await f.c.source(ref);
        const html = m.renderToStaticMarkup(
            m.createElement(m.MemoryInspectionPanel, {
                inspection: f.c,
                context: clone(context),
            }),
        );
        assert.match(html, /Verified memory packets/);
        assert.match(html, /Original scope and event/);
        assert.match(html, /&lt;script&gt;/);
        assert(!html.includes("<script>"));
        assert(
            !/Prepare derived memory|Process one chunk|type="checkbox"|dangerouslySetInnerHTML/.test(
                html,
            ),
        );
    },
);
await check(
    "SSR stale props hidden, Domain2/unread/pending labels truthful",
    async () => {
        const f = fixture();
        let html = m.renderToStaticMarkup(
            m.createElement(m.MemoryInspectionPanel, {
                inspection: f.c,
                context: { ...clone(context), epoch: 3 },
            }),
        );
        assert.equal(html, "");
        f.c.contextChanged({ ...clone(context), domainVersion: 2 });
        html = m.renderToStaticMarkup(
            m.createElement(m.MemoryInspectionPanel, {
                inspection: f.c,
                context: { ...clone(context), domainVersion: 2 },
            }),
        );
        assert.match(html, /Domain 2/);
        assert.match(html, /disabled/);
        assert(!html.includes("PLAYER-ONLY"));
    },
);
const report = {
    version: 1,
    synthetic: true,
    nativeIpc: false,
    rendering: "react-ssr",
    checks,
    passed: checks.every((v) => v.passed),
    unavailable: [
        "Rust/native IPC",
        "WebView/pixels",
        "models/devices",
        "raw JSON duplicate-key detection after transport",
    ],
};
await writeFile(
    path.join(output, `memory-inspection-${randomUUID()}.json`),
    JSON.stringify(report, null, 2),
    { flag: "wx" },
);
console.log(
    JSON.stringify({
        passed: checks.filter((v) => v.passed).length,
        failed: checks.filter((v) => !v.passed).length,
        checks,
    }),
);
if (!report.passed) process.exitCode = 1;
