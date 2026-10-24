// Frozen synthetic wire oracles. Not actual Core/native JSON or rendering evidence.
// Opt-in standalone command; no existing package script/test runner is changed.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";

const directory = process.env.LOCALLORE_CHECK_OUTPUT_DIR ?? fileURLToPath(new URL("./artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const target = path.join(directory, `v2-view-model-${randomUUID()}.mjs`);
const compiled = await build({ entryPoints: [fileURLToPath(new URL("./ui/v2-view-model.ts", import.meta.url))], bundle: true, platform: "node", format: "esm", write: false });
await writeFile(target, compiled.outputFiles[0].contents);
const { checkedPlaySnapshotV2: snapshot, checkedPageV2: page } = await import(pathToFileURL(target).href);
const scope = { story: "quay", branch: "child" }, original = { story: "quay", branch: "main" };
const clone = value => JSON.parse(JSON.stringify(value));
const actor = { name: "Rowan", location: "quay", alive: true, energy: 2, abilities: { steady: 1 }, attributes: { resolve: 3 }, injuries: ["cut-hand"], affiliations: ["quay-keepers"], goals: ["repair-beacon"] };
const thin = () => ({ version: 2, domain_version: 2, scope: clone(scope), revision: 3, rules: "fantasy_v1", player: { observer: "player", self_state: clone(actor) }, inventory: { potion: { owner: "player", quantity: 1, return_to: null, healing: true } } });
const query = () => ({ version: 2, scope: clone(scope), expected_head: 3, at_revision: null, observer: { kind: "player" }, view: "history", cursor: null, limit: 64, search: "" });
const message = (origin, sequence = 1) => ({ kind: "scoped_message", key: JSON.stringify(["history", String(sequence).padStart(20, "0"), "0_input", origin.story, origin.branch, "same-turn", "original_input"]), original_scope: clone(origin), turn: "same-turn", message_kind: "original_input", text: "<img src=x onerror=alert(1)>\u0000 🕯️", event_ids: [sequence], origin: "recorded_message" });
const marker = () => ({ kind: "author_correction", revision: 2 });
const event = () => ({ kind: "event", key: '["history","00000000000000000001","event"]', event: { sequence: 1, scope: clone(original), turn: "same-turn", story_time: 100, participants: ["player"], witnesses: ["player"], consequence: { effect: "time_advanced", from: 100, to: 101 } }, origin: "recorded_observation" });
const scoped = () => ({ kind: "scoped_event", value: { original_scope: clone(original), sequence: 1 } });
const envelope = (rows, q = query()) => ({ version: 2, scope: clone(scope), head: 3, revision: q.at_revision ?? 3, story_time: 100, observer: clone(q.observer), view: q.view, privacy: q.observer.kind === "player" ? "player_visible" : q.observer.kind === "character" ? "private_character" : "private_omniscient", status: "supported", total: rows.length, rows, next_cursor: null, unsupported: ["Additional shared fields unavailable"] });
let checks = 0;
function rejects(fn) { assert.throws(fn, /Wire/); checks++; }
function accepts(fn) { const result = fn(); checks++; return result; }

const input = thin();
const safe = accepts(() => snapshot(input, scope, 3));
assert.deepEqual(safe, input);
input.player.self_state.name = "mutated after decode";
assert.equal(safe.player.self_state.name, "Rowan"); checks++;
for (const domain of [1, 2]) { const v = thin(); v.domain_version = domain; accepts(() => snapshot(v, scope, 3)); }
const narrative = thin(); narrative.rules = "narrative_v1"; narrative.player.self_state.energy = 0; narrative.player.self_state.abilities = {}; narrative.player.self_state.attributes = {}; accepts(() => snapshot(narrative, scope, 3));
for (const mutate of [
    v => v.receipts = [], v => v.player.facts = {}, v => v.player.reason = "private", v => v.domain_version = 3,
    v => v.version = 1, v => v.revision = 2, v => v.scope.story = "foreign", v => v.scope.branch = "main",
    v => v.player.self_state.energy = 101, v => v.player.self_state.attributes.resolve = -101,
    v => v.player.self_state.abilities.steady = 0, v => v.player.self_state.abilities.steady = 65536,
    v => v.player.self_state.injuries.push("cut-hand"), v => v.inventory.potion.quantity = 0,
    v => v.inventory.potion.owner = "mira", v => v.player.self_state.alive = 1,
    v => v.player.self_state.name = "\ud800", v => v.revision = Number.MAX_SAFE_INTEGER + 1,
    v => v.player.self_state.name = "🌊".repeat(70000), v => v.player.observer = "",
]) { const v = thin(); mutate(v); rejects(() => snapshot(v, scope, 3)); }
const largeName = thin(); largeName.player.self_state.name = "n".repeat(3000); accepts(() => snapshot(largeName, scope, 3));
// Additional source-review oracle frozen before correcting conservative size accounting.
const exactCap = thin(); exactCap.player.self_state.name = "";
exactCap.player.self_state.name = "x".repeat(262144 - new TextEncoder().encode(JSON.stringify(exactCap)).length);
assert.equal(new TextEncoder().encode(JSON.stringify(exactCap)).length, 262144);
accepts(() => snapshot(exactCap, scope, 3));
exactCap.player.self_state.name += "x"; rejects(() => snapshot(exactCap, scope, 3));
const ownNames = thin(); ownNames.player.self_state.abilities = JSON.parse('{"__proto__":1,"constructor":2}');
const ownSafe = accepts(() => snapshot(ownNames, scope, 3));
assert.equal(Object.getPrototypeOf(ownSafe.player.self_state.abilities), Object.prototype); assert.equal(Object.hasOwn(ownSafe.player.self_state.abilities, "__proto__"), true); checks++;
let accessed = false;
const getter = thin(); Object.defineProperty(getter.player, "self_state", { enumerable: true, get() { accessed = true; throw Error("getter executed"); } });
rejects(() => snapshot(getter, scope, 3)); assert.equal(accessed, false); checks++;
const inherited = Object.create({ leaked: true }); Object.assign(inherited, thin()); rejects(() => snapshot(inherited, scope, 3));
const cycle = thin(); cycle.player.self_state.name = cycle; rejects(() => snapshot(cycle, scope, 3));
const symbolic = thin(); symbolic[Symbol("hidden")] = 1; rejects(() => snapshot(symbolic, scope, 3));

const rows = [message(original), marker(), message(scope, 3)];
const p = accepts(() => page(envelope(rows), query()));
assert.deepEqual(p.rows, rows); assert.deepEqual(Object.keys(p.rows[1]).sort(), ["kind", "revision"]); checks++;
assert.equal(p.rows[0].text, rows[0].text); checks++; // HTML/controls stay literal data; no DOM/execute API.
accepts(() => page(envelope([event()]), query()));
for (const observer of [{ kind: "character", id: "mira" }, { kind: "character", id: "player" }, { kind: "omniscient" }]) {
    const q = query(); q.observer = observer;
    rejects(() => page(envelope([marker()], q), q));
    if (observer.kind === "character" && observer.id === "mira") rejects(() => page(envelope([message(original)], q), q));
}
// Approved optional provenance argument: derive ONLY from a coherent native thin snapshot.
const qCustomPlayer = query(); qCustomPlayer.observer = { kind: "character", id: "custom-player" };
const customMessage = envelope([message(original)], qCustomPlayer);
accepts(() => page(customMessage, qCustomPlayer, "custom-player"));
rejects(() => page(customMessage, qCustomPlayer));
rejects(() => page(customMessage, qCustomPlayer, "mira"));
const qNpcNamedPlayer = query(); qNpcNamedPlayer.observer = { kind: "character", id: "player" };
rejects(() => page(envelope([message(original)], qNpcNamedPlayer), qNpcNamedPlayer, "custom-player"));
rejects(() => page(envelope([message(original)], qNpcNamedPlayer), qNpcNamedPlayer));
for (const mutate of [
    v => v.version = 1, v => v.head = 2, v => v.revision = 4, v => v.scope.story = "other",
    v => v.privacy = "private_omniscient", v => v.status = "unknown", v => v.reason = "private",
    v => v.rows[0].kind = "message", v => delete v.rows[0].original_scope,
    v => v.rows[0].original_scope.story = "foreign", v => v.rows[0].event_ids = [4],
    v => v.rows[0].event_ids = [1, 1], v => v.rows[0].event_ids = [2, 1],
    v => v.rows[0].origin = "canonical_truth", v => v.rows[0].proposal = {},
    v => v.rows[0].text = "🌊".repeat(20000), v => v.rows[0].original_scope.branch = "../main",
    v => v.rows[1].key = "invented", v => v.rows[1].origin = "derived_comparison",
    v => v.rows[1].revision = 0, v => v.rows[1].revision = 4, v => v.rows[1].reason = "private",
    v => v.rows.push(clone(v.rows[1])), v => v.rows.push({ ...clone(v.rows[0]), key: "different-key" }),
    v => v.next_cursor = "v2:1:hash", v => v.next_cursor = `1:1:${"a".repeat(64)}`,
    v => v.next_cursor = `2:0:${"a".repeat(64)}`, v => v.total = Number.MAX_SAFE_INTEGER + 1,
]) { const v = envelope(clone(rows)); mutate(v); v.total = Math.max(v.total, v.rows.length); rejects(() => page(v, query())); }
const duplicateKeys = envelope([event(), { ...event(), event: { ...event().event, sequence: 3 } }]); rejects(() => page(duplicateKeys, query()));
const qLimit = query(); qLimit.limit = 1; rejects(() => page(envelope(rows), qLimit));
const oversizeRows = envelope(Array.from({ length: 65 }, (_, i) => ({ ...marker(), revision: i + 1 }))); rejects(() => page(oversizeRows, query()));
const partial = envelope([message(original)]); partial.total = 5; partial.next_cursor = `2:1:${"a".repeat(64)}`; accepts(() => page(partial, query()));
const qHistorical = query(); qHistorical.at_revision = 1; const historical = envelope([message(original)], qHistorical); accepts(() => page(historical, qHistorical));
rejects(() => page(envelope([marker()], qHistorical), qHistorical));
const badQuery = query(); badQuery.search = "\u0000"; rejects(() => page(envelope([]), badQuery));
const qKnowledge = query(); qKnowledge.view = "knowledge";
const knowledge = { kind: "knowledge", key: '["observed","relic-location"]', id: "relic-location", subject: "player", text: "Observed A", confidence: null, sources: [scoped()], origin: "known_as_observed" };
accepts(() => page(envelope([knowledge], qKnowledge), qKnowledge));
for (const source of [{ kind: "scoped_event", original_scope: original, sequence: 1 }, { kind: "event", value: 1 }, { kind: "scoped_event", value: { original_scope: { story: "foreign", branch: "main" }, sequence: 1 } }, { kind: "scoped_event", value: { original_scope: original, sequence: 4 } }]) {
    const k = clone(knowledge); k.sources = [source]; rejects(() => page(envelope([k], qKnowledge), qKnowledge));
}
rejects(() => page(envelope([marker()], qKnowledge), qKnowledge));
const qUnsupported = query(); qUnsupported.view = "summaries";
const unsupported = envelope([], qUnsupported); unsupported.status = "unsupported"; accepts(() => page(unsupported, qUnsupported));
const rowFamilies = [
    ["profiles", { kind: "field", key: "field", actor: "player", field: "energy", value: { type: "number", value: 2 }, source: { kind: "seed", value: "lantern-quay-v1" }, origin: "canonical_field" }],
    ["relationships", { kind: "relationship", key: "relationship", from: "mira", to: "player", dimension: "trust", value: -3, source: scoped(), origin: "canonical_field" }],
    ["promises", { kind: "promise", key: "promise", id: "return-key", from: "player", to: "oren", terms: "Return key", deadline: 120, status: "open", return_item: "brass-key", sources: [scoped()], origin: "derived_comparison" }],
    ["provenance", { kind: "provenance", key: "provenance", sources: [{ kind: "withheld" }], origin: "known_as_observed" }],
    ["turn_diff", { kind: "change", key: "change", before_revision: 1, after_revision: 3, before: null, after: knowledge, origin: "derived_comparison" }],
];
for (const [view, row] of rowFamilies) { const q = query(); q.view = view; accepts(() => page(envelope([row], q), q)); }
const qPromise = query(); qPromise.view = "promises";
const wrongPromiseOrigin = clone(rowFamilies.find(([view]) => view === "promises")[1]); wrongPromiseOrigin.origin = "canonical_field";
rejects(() => page(envelope([wrongPromiseOrigin], qPromise), qPromise));
console.log(JSON.stringify({ suite: "synthetic-v2-wire-decoder", checks, native: false, model: false }));
