// Actual Rust Core/Host-library JSON -> existing strict decoder. No IPC/render/model.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { lstat, readFile } from "node:fs/promises";
import path from "node:path";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";

const directory = process.env.LOCALLORE_V2_FIXTURE_DIRECTORY;
assert.ok(directory && path.isAbsolute(directory), "Set LOCALLORE_V2_FIXTURE_DIRECTORY to an existing absolute fixture directory");
const file = path.join(directory, "v2-native-fixtures.json");
const stat = await lstat(file);
assert.ok(stat.isFile() && !stat.isSymbolicLink() && stat.size > 0 && stat.size <= 1024 * 1024, "Expected one bounded regular synthetic fixture file");
const bytes = await readFile(file);
assert.ok(bytes.length > 0 && bytes.length <= 1024 * 1024);
const fixture = JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes));
const exact = (value, keys) => {
  assert.ok(value !== null && typeof value === "object" && !Array.isArray(value));
  assert.deepEqual(Object.keys(value).sort(), [...keys].sort());
};
exact(fixture, ["version", "producer", "cases"]);
assert.equal(fixture.version, 1);
assert.equal(fixture.producer, "rust-core-host-library");
assert.ok(Array.isArray(fixture.cases) && fixture.cases.length === 4);
const compiled = await build({ entryPoints: [fileURLToPath(new URL("./ui/v2-view-model.ts", import.meta.url))], bundle: true, platform: "node", format: "esm", write: false });
assert.equal(compiled.outputFiles.length, 1);
const { checkedPlaySnapshotV2, checkedPageV2 } = await import(`data:text/javascript;base64,${Buffer.from(compiled.outputFiles[0].contents).toString("base64")}`);
const unwrap = reply => {
  exact(reply, ["version", "status", "data"]);
  assert.equal(reply.version, 1);
  assert.equal(reply.status, "ok");
  return reply.data;
};
const views = ["profiles", "history", "relationships", "knowledge", "promises", "provenance", "turn_diff", "summaries", "retrieval_indexes"];
const observerKey = observer => observer.kind === "character" ? `character:${observer.id}` : observer.kind;
const ids = new Set();
let snapshots = 0, pages = 0, paged = 0, historical = 0;
for (const value of fixture.cases) {
  exact(value, ["id", "scope", "head", "domain_version", "selected_player", "snapshot", "pages"]);
  assert.ok(["default-domain1", "default-domain2", "custom-domain1", "custom-domain2"].includes(value.id));
  assert.ok(!ids.has(value.id)); ids.add(value.id);
  assert.ok(Array.isArray(value.pages) && value.pages.length > 0 && value.pages.length <= 256);
  const snapshot = checkedPlaySnapshotV2(unwrap(value.snapshot), value.scope, value.head);
  assert.equal(snapshot.domain_version, value.domain_version);
  assert.equal(snapshot.player.observer, value.selected_player);
  assert.equal(snapshot.player.observer, value.id.startsWith("custom-") ? "hero" : "player");
  snapshots++;
  const coverage = new Map();
  for (const capture of value.pages) {
    exact(capture, ["label", "query", "reply"]);
    assert.ok(["current", "historical", "paged", "private-reason-search"].includes(capture.label));
    assert.deepEqual(capture.query.scope, snapshot.scope);
    assert.equal(capture.query.expected_head, snapshot.revision);
    // Player identity comes from this exact coherent native snapshot, never the query.
    const page = checkedPageV2(unwrap(capture.reply), capture.query, snapshot.player.observer);
    assert.deepEqual(page.scope, snapshot.scope);
    pages++;
    if (capture.label === "current") {
      assert.equal(capture.query.at_revision, null);
      assert.equal(capture.query.cursor, null);
      assert.equal(capture.query.search, "");
      const key = observerKey(capture.query.observer);
      if (!coverage.has(key)) coverage.set(key, new Set());
      assert.ok(!coverage.get(key).has(page.view));
      coverage.get(key).add(page.view);
    }
    if (capture.label === "historical") { assert.equal(capture.query.at_revision, 1); historical++; }
    if (capture.label === "paged") { assert.equal(capture.query.limit, 1); paged++; }
    if (capture.label === "private-reason-search") assert.equal(page.total, 0);
  }
  const lenses = [{ kind:"player" }, { kind:"character", id:"mira" }, { kind:"character", id:snapshot.player.observer }, { kind:"omniscient" }];
  if (snapshot.player.observer !== "player") lenses.push({ kind:"character", id:"player" });
  assert.equal(coverage.size, lenses.length);
  for (const lens of lenses) assert.deepEqual([...(coverage.get(observerKey(lens)) ?? [])].sort(), [...views].sort());
  const full = (lens, view) => value.pages.find(p => p.label === "current" && p.query.view === view && observerKey(p.query.observer) === observerKey(lens)).reply.data;
  for (const lens of lenses) {
    const history = full(lens, "history");
    const segments = value.pages.filter(p => p.label === "paged" && observerKey(p.query.observer) === observerKey(lens));
    assert.ok(segments.length > 0);
    assert.equal(segments[0].query.cursor, null);
    const rows = [];
    for (let index = 0; index < segments.length; index++) {
      const part = segments[index];
      assert.equal(part.reply.data.total, history.total);
      rows.push(...part.reply.data.rows);
      assert.equal(part.reply.data.next_cursor, index + 1 < segments.length ? segments[index + 1].query.cursor : null);
    }
    assert.deepEqual(rows, history.rows);
    const markers = history.rows.filter(row => row.kind === "author_correction");
    assert.equal(markers.length, value.domain_version === 2 && lens.kind === "player" ? 1 : 0);
    if (lens.kind === "character" && lens.id !== snapshot.player.observer) assert.ok(history.rows.every(row => row.kind !== "scoped_message"));
    const fact = full(lens, "knowledge").rows.find(row => row.kind === "knowledge" && row.id === "relic-location");
    assert.ok(fact);
    assert.equal(fact.text, value.domain_version === 2 && lens.kind === "omniscient" ? "SYNTHETIC_PRIVATE_WORLD_B" : "SYNTHETIC_OBSERVED_A");
  }
  if (value.domain_version === 2) {
    const own = full({ kind:"player" }, "history");
    const messages = own.rows.filter(row => row.kind === "scoped_message" && row.turn === "same-turn");
    assert.equal(messages.length, 4);
    assert.equal(new Set(messages.map(row => JSON.stringify([row.original_scope, row.message_kind]))).size, 4);
    assert.deepEqual(own.rows.filter(row => row.kind === "author_correction"), [{ kind:"author_correction", revision:2 }]);
  }
}
assert.equal(ids.size, 4);
assert.ok(paged > 0 && historical > 0);
console.log(JSON.stringify({ evidence:"Rust Core/Host-library producer JSON decoded by existing strict desktop V2 module; no IPC, render, persistence or model execution", fixtureSha256:createHash("sha256").update(bytes).digest("hex"), fixtureBytes:bytes.length, snapshots, pages, paged, historical }));
