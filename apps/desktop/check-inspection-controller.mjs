// Actual-controller regression: complete inspection context and late-response fencing.
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
const dir = new URL("artifacts/checks/", import.meta.url);
await mkdir(dir, { recursive: true });
const output = new URL(`inspection-controller-${randomUUID()}.mjs`, dir);
const bundled = await build({
    entryPoints: [fileURLToPath(new URL("ui/controller.ts", import.meta.url))],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
await writeFile(output, bundled.outputFiles[0].contents);
const { Controller } = await import(output.href);
const scope = { story: "synthetic-inspection", branch: "main" };
let queries = [],
    held = null,
    corrupt = false;
const gateway = {
    async call(command) {
        if (command.op === "open") return { revision: 0 };
        if (command.op === "play_snapshot")
            return {
                scope,
                revision: 0,
                inventory: {},
                receipts: [],
                player: {
                    scope,
                    revision: 0,
                    observer: "player",
                    self_state: { name: "Rowan", energy: 2, location: "quay" },
                    facts: {},
                    beliefs: [],
                    observations: [],
                },
            };
        if (command.op === "inspect" || command.op === "close") return {};
        assert.equal(command.op, "inspection_query");
        const q = structuredClone(command.query);
        queries.push(q);
        const observer =
            q.observer.kind === "character"
                ? { id: q.observer.id, kind: "character" }
                : q.observer;
        const page = {
            version: 1,
            scope,
            head: 0,
            revision: q.at_revision ?? 0,
            story_time: 100,
            observer,
            view: q.view,
            privacy:
                q.observer.kind === "player"
                    ? "player_visible"
                    : q.observer.kind === "character"
                      ? "private_character"
                      : "private_omniscient",
            status: "supported",
            total: 1,
            rows: [
                {
                    kind: "field",
                    key: q.search || "row",
                    actor:
                        q.observer.kind === "character"
                            ? q.observer.id
                            : "player",
                    field: "name",
                    value: { type: "text", value: "Visible name" },
                    source: { kind: "seed", value: "synthetic" },
                    origin: "canonical_field",
                },
            ],
            next_cursor: null,
            unsupported: [],
        };
        if (corrupt) {
            corrupt = false;
            page.privacy = "private_omniscient";
        }
        if (held) {
            const h = held;
            held = null;
            h.entered();
            await h.waiting;
        }
        return page;
    },
};
const c = new Controller(gateway);
await c.attach({ id: "s", scope, revision: 0, name: "Synthetic" });
await c.showQuery();
assert.equal(c.get().query.page.observer.kind, "player");
let enter, release;
const entered = new Promise((r) => (enter = r)),
    waiting = new Promise((r) => (release = r));
held = { entered: enter, waiting };
const stale = c.browseInspection({ view: "knowledge", search: "PRIVATE_OLD" });
await entered;
const fresh = c.browseInspection({ view: "history", search: "new" });
assert.equal(c.get().query.page, null);
await fresh;
release();
await stale;
assert.equal(c.get().query.page.view, "history");
assert.equal(c.get().query.page.rows[0].key, "new");
c.setView("lab");
await new Promise((r) => setTimeout(r, 0));
c.setObserver("mira");
await new Promise((r) => setTimeout(r, 0));
assert.equal(
    c.get().query.page.observer.id,
    "mira",
    "sorted JSON field order must not reject the same observer",
);
c.setView("play");
await new Promise((r) => setTimeout(r, 0));
assert.equal(c.get().query.page.observer.kind, "player");
corrupt = true;
await c.queryInspection();
assert.equal(c.get().query.error, "Wire");
assert.equal(c.get().query.page, null, "wrong privacy page must never render");
await c.showQuery(false);
assert.equal(c.get().query.page, null);
assert.equal(c.get().query.busy, false);
assert(
    queries.every(
        (q) =>
            q.scope.story === scope.story &&
            q.expected_head === 0 &&
            q.cursor === null &&
            q.limit === 12,
    ),
);
await c.dispose();
console.log(
    "PASS: exact inspection context fences delayed replies; sorted observer JSON accepted; wrong privacy and closed views cleared.",
);
