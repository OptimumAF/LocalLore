// Actual-controller regression: complete inspection context and late-response fencing.
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import evidencePath from "node:path";
import { randomUUID } from "node:crypto";
import assert from "node:assert/strict";
const dir = process.env.LOCALLORE_CHECK_OUTPUT_DIR
    ? pathToFileURL(
          evidencePath.resolve(process.env.LOCALLORE_CHECK_OUTPUT_DIR) +
              evidencePath.sep,
      )
    : new URL("artifacts/checks/", import.meta.url);
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

// Removed fields must resolve their prior origin, not query a nonexistent after-field.
const fieldKey = '["field","player","item/potion"]';
const former = {
    kind: "field",
    key: fieldKey,
    actor: "player",
    field: "item/potion",
    value: {
        type: "item",
        value: { owner: "player", quantity: 1, healing: true, return_to: null },
    },
    source: { kind: "seed", value: "synthetic" },
    origin: "canonical_field",
};
const removed = {
    kind: "change",
    key: '["change","potion"]',
    before_revision: 0,
    after_revision: 1,
    before: former,
    after: null,
    origin: "derived_comparison",
};
const navigation = [];
let navHeld = null;
let boundaryVisible = true,
    messageWithoutSources = false;
const navGateway = {
    async call(command) {
        if (command.op === "open") return { revision: 1 };
        if (command.op === "play_snapshot")
            return {
                scope: command.scope,
                revision: 1,
                inventory: {},
                receipts: [],
                player: {
                    scope: command.scope,
                    revision: 1,
                    observer: "player",
                    self_state: { name: "Rowan", energy: 2, location: "quay" },
                    facts: {},
                    beliefs: [],
                    observations: [],
                },
            };
        if (command.op === "close" || command.op === "inspect") return {};
        assert.equal(command.op, "inspection_query");
        const q = command.query;
        navigation.push(structuredClone(q));
        const event = {
            kind: "event",
            key: "accepted-gift",
            origin: "recorded_observation",
            event: {
                sequence: 1,
                scope: q.scope,
                turn: "accepted-gift-turn",
                story_time: 100,
                participants: ["player", "mira"],
                witnesses: ["player", "mira"],
                consequence: {
                    effect: "given",
                    item: "potion",
                    to: "mira",
                    quantity: 1,
                },
            },
        };
        const message = {
            kind: "message",
            key: "recorded-message",
            origin: "recorded_message",
            turn: "accepted-gift-turn",
            message_kind: "narration",
            text: "Recorded display",
            event_ids: messageWithoutSources ? [] : [1],
        };
        let rows = [];
        if (q.view === "turn_diff") rows = [removed];
        if (q.view === "provenance" && q.at_revision === 0)
            rows = [
                {
                    kind: "provenance",
                    key: fieldKey,
                    sources: [former.source],
                    origin: "canonical_field",
                },
            ];
        if (q.view === "history")
            rows = boundaryVisible
                ? q.observer.kind === "character"
                    ? [event]
                    : messageWithoutSources
                      ? [message]
                      : [event, message]
                : [];
        const result = {
            version: 1,
            scope: q.scope,
            head: 1,
            revision: q.at_revision ?? 1,
            story_time: 100,
            observer: q.observer,
            view: q.view,
            privacy:
                q.observer.kind === "player"
                    ? "player_visible"
                    : q.observer.kind === "character"
                      ? "private_character"
                      : "private_omniscient",
            status: "supported",
            total: rows.length,
            rows,
            next_cursor: null,
            unsupported: [],
        };
        if (navHeld) {
            const hold = navHeld;
            navHeld = null;
            hold.entered();
            await hold.waiting;
        }
        return result;
    },
};
const nav = new Controller(navGateway);
await nav.attach({ id: "nav", scope, revision: 1, name: "Synthetic" });
await nav.showQuery();
await nav.browseInspection({ view: "turn_diff", atRevision: 1 });
await nav.whyInspection(nav.get().query.page.rows[0]);
assert.equal(nav.get().query.page.revision, 0);
assert.equal(nav.get().query.page.rows[0].key, fieldKey);
assert.equal(nav.get().query.trace.stage, "prior_provenance");
assert.equal(nav.get().query.trace.change.after, null);
assert.match(nav.get().query.notice, /absent at r1/);
assert(
    !navigation.some((q) => q.view === "provenance" && q.at_revision === 1),
    "removed field origin must never be relabelled as after-head provenance",
);
await nav.showChangeTurnHistory();
assert.equal(nav.get().query.page.revision, 1);
assert.equal(nav.get().query.page.view, "history");
assert.equal(nav.get().query.trace.stage, "turn_history");
assert.equal(nav.get().query.selectedKey, "accepted-gift");
assert.equal(nav.get().query.page.rows[0].event.consequence.item, "potion");
let row = nav.get().query.page.rows.find((r) => r.kind === "message");
await nav.whyInspection(row);
assert.equal(
    navigation.at(-1).view,
    "history",
    "message sources must not use a nonexistent field-provenance key",
);
row = nav.get().query.page.rows.find((r) => r.kind === "event");
await nav.whyInspection(row);
assert.equal(
    navigation.at(-1).view,
    "history",
    "event itself is its accepted source",
);
messageWithoutSources = true;
await nav.browseInspection({ view: "history", atRevision: 1 });
const count = navigation.length;
await nav.whyInspection(nav.get().query.page.rows[0]);
assert.equal(navigation.length, count);
assert.match(nav.get().query.notice, /No accepted event source/);
messageWithoutSources = false;
nav.setView("lab");
await new Promise((r) => setTimeout(r, 0));
nav.setObserver("mira");
await new Promise((r) => setTimeout(r, 0));
await nav.browseInspection({ view: "turn_diff", atRevision: 1 });
await nav.whyInspection(nav.get().query.page.rows[0]);
boundaryVisible = false;
const start = navigation.length;
await nav.showChangeTurnHistory();
assert.equal(
    navigation.length,
    start + 1,
    "hidden boundary must not infer a raw Player turn ID",
);
assert.match(nav.get().query.notice, /unavailable/);
await nav.browseInspection({
    view: "provenance",
    search: JSON.stringify(fieldKey),
    atRevision: 0,
});
nav.setObserver("sable");
assert.equal(nav.get().query.search, "");
assert.equal(nav.get().query.atRevision, null);
assert.equal(nav.get().query.trace, null);
await new Promise((r) => setTimeout(r, 0));
await nav.browseInspection({
    view: "provenance",
    search: JSON.stringify(fieldKey),
    atRevision: 0,
});
nav.returnToPlay();
assert.equal(nav.get().view, "play");
assert.equal(nav.get().observer, "player");
assert.equal(nav.get().inspection, null);
assert.equal(nav.get().query.shown, false);
assert.equal(nav.get().query.page, null);
assert.equal(nav.get().query.search, "");
assert.equal(nav.get().query.atRevision, null);
assert.equal(nav.get().query.trace, null);
await nav.showQuery();
await nav.browseInspection({
    view: "provenance",
    search: JSON.stringify(fieldKey),
    atRevision: 0,
});
await nav.attach({
    id: "different-session",
    scope: { story: "other-synthetic", branch: "main" },
    revision: 1,
    name: "Different story",
});
assert.equal(nav.get().query.search, "");
assert.equal(nav.get().query.atRevision, null);
assert.equal(nav.get().query.trace, null);
boundaryVisible = true;
await nav.browseInspection({ view: "history", atRevision: 1 });
let sourceEntered, sourceRelease;
const sourceReady = new Promise((r) => (sourceEntered = r)),
    sourceWaiting = new Promise((r) => (sourceRelease = r));
navHeld = { entered: sourceEntered, waiting: sourceWaiting };
const delayedSource = nav.whyInspection(
    nav.get().query.page.rows.find((r) => r.kind === "event"),
);
await sourceReady;
await nav.attach({
    id: "third-session",
    scope: { story: "third-synthetic", branch: "main" },
    revision: 1,
    name: "Third story",
});
assert(
    nav
        .get()
        .query.page.rows.some(
            (r) => r.kind === "event" && r.event.sequence === 1,
        ),
);
sourceRelease();
await delayedSource;
assert.equal(
    nav.get().query.selectedKey,
    null,
    "old source helper must not select new story's coincident Event 1",
);
assert.equal(
    nav.get().query.notice,
    "",
    "old accepted-source notice must not enter the new story",
);
await nav.dispose();
console.log(
    "PASS: removed-field prior provenance and permitted turn sources; event/message routing; hidden-cause refusal; Return to Play and story/lens parameter clearing.",
);
