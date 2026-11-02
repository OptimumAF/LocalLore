// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST against D04_MSVC_DEPENDENCY_FACTS_CONTRACT_2026-11-01.
// SOURCE-ONLY / UNRUN. Synthetic JSON data only; no producer import, top-level
// run, filesystem, process, environment, SDK/library reads or source evaluation.
// Largest logical fixture is D20's8MiB directive text (32*4*65536), plus small
// records/digests. Immutable strings may share storage, but each occurrence is
// conservatively counted. D19 adds(17+9)*65536 logical text; all fixture text/buffer
// payloads stay below16MiB. Per-row temporary stringify/hash buffers are bounded
// synthetic fixture work, not a measured memory/peak or actual-input claim.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { MSVC_LIBRARY_METADATA_PROFILE } from './library_inputs.mjs';

const ID = 'msvc-library-metadata-v1', KIND = 'library_metadata_dependency_first_v1';
const INVALID = 'LibraryMetadataDependencyFactsInvalid';
const OUTPUT_KEYS = ['version', 'kind', 'profileId', 'purpose', 'qualified',
  'linkQualification', 'closureComplete', 'captureComplete', 'status',
  'pinsSha256', 'catalogSha256', 'libraryNames', 'providedSlots', 'rows',
  'unresolvedNameIds', 'allReferencesInProvidedCatalog'];
const clone = value => JSON.parse(JSON.stringify(value));
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const sorted = values => [...values].sort();
const eq = (a, b) => assert.deepEqual(a, b);
function metadata(libraries = [], directives = []) {
  // Property insertion order deliberately matches the accepted helper.
  return { objects: 1, imports: 0, directives: [...directives], defaultLibraries: [...libraries] };
}
function result(libraries = [], directives = []) {
  return { profileId: ID, purpose: 'build_input_metadata_only', qualified: false,
    linkQualification: false, closureComplete: false, metadata: metadata(libraries, directives),
    sections: 0, deviations: { unknownMachineObjects: 0, unusedRelocationPointers: 0, terminalNulSections: 0 } };
}
function fixture() {
  const observations = Array.from({ length: 32 }, (_, i) => ({ slot: i + 1, result: result() }));
  const pins = observations.map(({ slot, result: r }) => ({ slot,
    metadataSha256: digest(r.metadata), libraryCount: r.metadata.defaultLibraries.length }));
  const catalog = Array.from({ length: 15 }, (_, i) => ({ slot: i + 18, name: `catalog-${String(i).padStart(2, '0')}.lib` }));
  return { pins, observations, catalog };
}
function repin(f, index) {
  const m = f.observations[index].result.metadata;
  f.pins[index] = { slot: index + 1, metadataSha256: digest(m), libraryCount: m.defaultLibraries.length };
}
function libraries(f, index, names) { f.observations[index].result.metadata.defaultLibraries = [...names]; repin(f, index); }
function directives(f, index, tokens) { f.observations[index].result.metadata.directives = [...tokens]; repin(f, index); }
function longName(i, length = 259) {
  const prefix = String(i).padStart(2, '0') + '-';
  return prefix + 'a'.repeat(length - prefix.length - 4) + '.lib';
}
function longDirectives(count) {
  return Array.from({ length: count }, (_, i) => {
    const prefix = '/X:' + String(i).padStart(3, '0') + ':';
    return prefix + 'a'.repeat(65536 - prefix.length);
  });
}
function deeplyFrozen(value) {
  if (value && typeof value === 'object') {
    assert(Object.isFrozen(value), 'Expected deeply frozen data');
    for (const child of Object.values(value)) deeplyFrozen(child);
  }
}
function refuse(project, f) {
  let caught;
  try { project(f.pins, f.observations, f.catalog); } catch (error) { caught = error; }
  assert(caught instanceof Error, 'Expected fixed dependency refusal');
  assert.equal(caught.message, INVALID);
}
function emptyExpected(f) {
  return { version: 1, kind: 'msvc_library_dependency_facts_v1', profileId: ID,
    purpose: 'build_input_metadata_only', qualified: false, linkQualification: false,
    closureComplete: false, captureComplete: true, status: 'metadata_facts_complete',
    pinsSha256: digest(f.pins), catalogSha256: digest(f.catalog), libraryNames: [],
    providedSlots: [], rows: Array.from({ length: 32 }, (_, i) => ({ slot: i + 1, libraryIds: [] })),
    unresolvedNameIds: [], allReferencesInProvidedCatalog: true };
}

export async function runLibraryMetadataDependencySelfchecksV1(api) {
  if (!api || typeof api.projectLibraryMetadataDependenciesV1 !== 'function') {
    throw Error('UNRUN_SETUP: dependency facts API unavailable');
  }
  const project = api.projectLibraryMetadataDependenciesV1;
  const run = f => project(f.pins, f.observations, f.catalog);
  const cases = [], add = (id, fn) => cases.push([id, fn]);

  add('D01', () => { const f = fixture(), r = run(f); eq(r, emptyExpected(f)); assert.equal(MSVC_LIBRARY_METADATA_PROFILE.id, ID); assert.equal(MSVC_LIBRARY_METADATA_PROFILE.version, 1); });
  add('D02', () => { const f = fixture(); libraries(f, 0, [f.catalog[5].name]); const r = run(f); eq(r.libraryNames, [f.catalog[5].name]); eq(r.providedSlots, [23]); eq(r.rows[0], { slot: 1, libraryIds: [0] }); eq(r.unresolvedNameIds, []); assert.equal(r.allReferencesInProvidedCatalog, true); });
  add('D03', () => { const f = fixture(); libraries(f, 8, ['unresolved.lib']); const r = run(f); eq(r.libraryNames, ['unresolved.lib']); eq(r.providedSlots, [null]); eq(r.rows[8].libraryIds, [0]); eq(r.unresolvedNameIds, [0]); assert.equal(r.allReferencesInProvidedCatalog, false); assert.equal(r.closureComplete, false); });
  add('D04', () => { const f = fixture(); libraries(f, 0, ['alpha.lib', 'zeta.lib']); libraries(f, 1, ['alpha.lib']); libraries(f, 31, ['zeta.lib']); const r = run(f); eq(r.libraryNames, ['alpha.lib', 'zeta.lib']); eq(r.rows[0].libraryIds, [0, 1]); eq(r.rows[1].libraryIds, [0]); eq(r.rows[31].libraryIds, [1]); eq(r.unresolvedNameIds, [0, 1]); });
  add('D05', () => { const f = fixture(); libraries(f, 17, [f.catalog[0].name, f.catalog[1].name]); libraries(f, 18, [f.catalog[0].name]); const r = run(f); eq(r.providedSlots, [18, 19]); eq(r.rows[17].libraryIds, [0, 1]); eq(r.rows[18].libraryIds, [0]); assert.equal(r.allReferencesInProvidedCatalog, true); assert.equal(r.closureComplete, false); });
  add('D06', () => { const f = fixture(); [f.observations[0], f.observations[1]] = [f.observations[1], f.observations[0]]; refuse(project, f); const g = fixture(); g.observations[1].slot = 1; refuse(project, g); });
  add('D07', () => { const f = fixture(); f.pins[0].metadataSha256 = '0'.repeat(64); refuse(project, f); const g = fixture(); g.observations[0].result.metadata.directives = ['/X:changed']; refuse(project, g); const h = fixture(); const m = h.observations[0].result.metadata; h.observations[0].result.metadata = { defaultLibraries: m.defaultLibraries, directives: m.directives, imports: m.imports, objects: m.objects }; refuse(project, h); });
  add('D08', () => { const f = fixture(); f.pins[0].libraryCount = 1; refuse(project, f); });
  add('D09', () => { for (const count of [31, 33]) { const f = fixture(); if (count === 31) f.observations.pop(); else f.observations.push(clone(f.observations[31])); refuse(project, f); } });
  add('D10', () => { const f = fixture(); f.observations[0].extra = 'untrusted'; refuse(project, f); });
  add('D11', () => { for (const value of ['strict-v1', 'unknown', new String(ID)]) { const f = fixture(); f.observations[0].result.profileId = value; refuse(project, f); } const f = fixture(); f.observations[0].result.purpose = 'link_qualification'; refuse(project, f); });
  add('D12', () => { for (const key of ['qualified', 'linkQualification', 'closureComplete']) for (const value of [true, 0, 'false', null]) { const f = fixture(); f.observations[0].result[key] = value; refuse(project, f); } });
  add('D13', () => { const f = fixture(); f.observations[0].result.extra = 1; refuse(project, f); for (const key of Object.keys(result())) { const g = fixture(); delete g.observations[0].result[key]; refuse(project, g); } });
  add('D14', () => { const f = fixture(); f.observations[0].result.metadata.extra = []; refuse(project, f); for (const key of Object.keys(metadata())) { const g = fixture(); delete g.observations[0].result.metadata[key]; refuse(project, g); } });
  add('D15', () => { const f = fixture(); directives(f, 0, ['/Z:later', '/A:earlier']); refuse(project, f); });
  add('D16', () => { const f = fixture(); directives(f, 0, ['/X:same', '/X:same']); refuse(project, f); });
  add('D17', () => { for (const token of ['/X:\0', '/X:\t', '/X:\n', '/X:\r', '/X:\x7f', '/X:\u00e9', '/X:\ud83d\ude00']) { const f = fixture(); directives(f, 0, [token]); refuse(project, f); } });
  add('D18', () => { const valid = fixture(); directives(valid, 0, longDirectives(1)); eq(run(valid).libraryNames, []); const f = fixture(); directives(f, 0, ['/X:' + 'a'.repeat(65534)]); assert.equal(f.observations[0].result.metadata.directives[0].length, 65537); refuse(project, f); });
  // Pure fixtures establish refusal, not instrumentation of hashing order.
  // Source review separately verifies the required bounded pre-stringify walk.
  add('D19', () => { const f = fixture(), tokens = longDirectives(17); directives(f, 0, tokens); assert(tokens.reduce((n, t) => n + t.length, 0) > 1048576); refuse(project, f); const escaped = fixture(), quotes = Array.from({ length: 9 }, (_, i) => { const prefix = '/Q:' + String(i).padStart(3, '0') + ':'; return prefix + '"'.repeat(65536 - prefix.length); }); directives(escaped, 0, quotes); assert(quotes.reduce((n, t) => n + t.length, 0) < 1048576); assert(quotes.reduce((n, t) => n + JSON.stringify(t).length, 0) > 1048576); refuse(project, escaped); });
  add('D20', () => { const f = fixture(), tokens = longDirectives(4); for (let i = 0; i < 32; i++) directives(f, i, tokens); assert.equal(tokens.reduce((n, t) => n + t.length, 0) * 32, 8388608); assert(tokens.reduce((n, t) => n + JSON.stringify(t).length, 0) * 32 > 8388608); assert(Buffer.byteLength(JSON.stringify(f.observations[0].result.metadata)) < 1048576); refuse(project, f); });
  add('D21', () => { for (const names of [['zeta.lib', 'alpha.lib'], ['alpha.lib', 'alpha.lib']]) { const f = fixture(); libraries(f, 0, names); refuse(project, f); } });
  add('D22', () => { for (const name of ['bad/name.lib', 'bad\\name.lib', '../bad.lib', 'bad..name.lib', 'drive:name.lib', '"quoted.lib"', 'bad\0.lib', 'bad\t.lib', 'bad\u00e9.lib']) { const f = fixture(); libraries(f, 0, [name]); refuse(project, f); } });
  add('D23', () => { for (const name of ['UPPER.lib', 'alpha.LIB', ' untrimmed.lib', 'untrimmed.lib ', 'extensionless', '.hidden.lib']) { const f = fixture(); libraries(f, 0, [name]); refuse(project, f); } });
  add('D24', () => { const f = fixture(), name = longName(0); assert.equal(name.length, 259); libraries(f, 0, [name]); const r = run(f); eq(r.libraryNames, [name]); eq(r.unresolvedNameIds, [0]); const g = fixture(); libraries(g, 0, [longName(0, 260)]); refuse(project, g); });
  add('D25', () => { const names = Array.from({ length: 33 }, (_, i) => `union-${String(i).padStart(2, '0')}.lib`); const f = fixture(); libraries(f, 0, names.slice(0, 17)); libraries(f, 1, names.slice(17)); assert(f.pins.every(p => p.libraryCount <= 32)); refuse(project, f); const g = fixture(); libraries(g, 0, names); refuse(project, g); });
  add('D26', () => { for (const change of [f => f.catalog.pop(), f => f.catalog.push({ slot: 33, name: 'extra.lib' }), f => [f.catalog[0], f.catalog[1]] = [f.catalog[1], f.catalog[0]], f => f.catalog[1].name = f.catalog[0].name, f => f.catalog[0].extra = 1, f => f.catalog[0].name = '../unsafe.lib', f => delete f.catalog[3]]) { const f = fixture(); change(f); refuse(project, f); } });
  add('D27', () => {
    const valid = fixture(); const upper = valid.observations[0].result; upper.metadata.objects = 65536; upper.sections = 262144; upper.deviations = { unknownMachineObjects: 65536, unusedRelocationPointers: 262144, terminalNulSections: 262144 }; repin(valid, 0); eq(run(valid).libraryNames, []);
    for (const value of [-1, 0.5, NaN, Infinity, '0', true, 65537, Number.MAX_SAFE_INTEGER + 1]) for (const key of ['objects', 'imports']) { const f = fixture(); f.observations[0].result.metadata[key] = value; repin(f, 0); refuse(project, f); }
    const sum = fixture(); sum.observations[0].result.metadata.objects = 65536; sum.observations[0].result.metadata.imports = 1; repin(sum, 0); refuse(project, sum);
    for (const value of [-1, 0.5, '0', 262145]) { const f = fixture(); f.observations[0].result.sections = value; refuse(project, f); }
    for (const [key, max] of [['unknownMachineObjects', 65536], ['unusedRelocationPointers', 262144], ['terminalNulSections', 262144]]) for (const value of [-1, 0.5, '0', max + 1]) { const f = fixture(); f.observations[0].result.deviations[key] = value; refuse(project, f); }
    const extra = fixture(); extra.observations[0].result.deviations.extra = 0; refuse(project, extra); const missing = fixture(); delete missing.observations[0].result.deviations.unknownMachineObjects; refuse(project, missing);
  });
  add('D28', () => {
    for (const change of [f => f.pins.pop(), f => f.pins.push(clone(f.pins[31])), f => [f.pins[0], f.pins[1]] = [f.pins[1], f.pins[0]], f => f.pins[1].slot = 1, f => f.pins[0].extra = 1, f => delete f.pins[0].metadataSha256, f => f.pins[0].metadataSha256 = 'A'.repeat(64), f => f.pins[0].metadataSha256 = 'g'.repeat(64), f => f.pins[0].metadataSha256 = 'a'.repeat(63), f => f.pins[0].libraryCount = true, f => f.pins[0].libraryCount = -1, f => f.pins[0].libraryCount = 0.5, f => f.pins[0].libraryCount = 33]) { const f = fixture(); change(f); refuse(project, f); }
  });
  add('D29', () => { const f = fixture(); libraries(f, 0, [f.catalog[0].name, 'unknown.lib']); const before = JSON.stringify(f), r = run(f), next = run(f), retained = JSON.stringify(r); assert.equal(JSON.stringify(f), before); deeplyFrozen(r); assert.notEqual(r, next); assert.notEqual(r.libraryNames, next.libraryNames); assert.notEqual(r.rows, next.rows); assert.notEqual(r.rows[0], next.rows[0]); assert.notEqual(r.rows[0].libraryIds, next.rows[0].libraryIds); assert.notEqual(r.libraryNames, f.observations[0].result.metadata.defaultLibraries); f.observations[0].result.metadata.defaultLibraries[0] = 'changed.lib'; f.catalog[0].name = 'changed.lib'; f.pins[0].metadataSha256 = '0'.repeat(64); assert.equal(JSON.stringify(r), retained); });
  add('D30', () => { const f = fixture(); f.catalog[0].name = 'alpha.lib'; f.catalog[1].name = 'middle.lib'; libraries(f, 0, ['alpha.lib', 'zeta.lib']); libraries(f, 1, ['middle.lib']); libraries(f, 17, ['alpha.lib', 'middle.lib', 'zeta.lib']); const r = run(f); eq(r.libraryNames, ['alpha.lib', 'middle.lib', 'zeta.lib']); eq(r.providedSlots, [18, 19, null]); eq(r.rows[0].libraryIds, [0, 2]); eq(r.rows[1].libraryIds, [1]); eq(r.rows[17].libraryIds, [0, 1, 2]); eq(r.unresolvedNameIds, [2]); assert.equal(r.allReferencesInProvidedCatalog, false); });
  add('D31', () => { const f = fixture(); directives(f, 0, ['/X:private-marker', 'printable "opaque" \\ text']); libraries(f, 0, [f.catalog[2].name]); const r = run(f); eq(Object.keys(r).sort(), [...OUTPUT_KEYS].sort()); assert.equal(r.version, 1); assert.equal(r.kind, 'msvc_library_dependency_facts_v1'); assert.equal(r.profileId, ID); assert.equal(r.purpose, MSVC_LIBRARY_METADATA_PROFILE.purpose); eq([r.qualified, r.linkQualification, r.closureComplete, r.captureComplete], [false, false, false, true]); assert.equal(r.status, 'metadata_facts_complete'); assert.equal(r.pinsSha256, digest(f.pins)); assert.equal(r.catalogSha256, digest(f.catalog)); assert.equal(r.rows.length, 32); assert(r.rows.every((row, i) => row.slot === i + 1 && Object.keys(row).sort().join(',') === 'libraryIds,slot')); const text = JSON.stringify(r); assert(!text.includes('private-marker') && !text.includes('opaque') && !text.includes('directives') && !text.includes('path')); });
  add('D32', () => { const f = fixture(), names = Array.from({ length: 32 }, (_, i) => longName(i)); assert(names.every(n => n.length === 259)); assert.equal(Buffer.byteLength(JSON.stringify(names)), 8385); f.catalog = names.slice(0, 15).map((name, i) => ({ slot: i + 18, name })); for (let i = 0; i < 32; i++) libraries(f, i, names); const r = run(f); eq(r.libraryNames, names); eq(r.providedSlots, [...Array.from({ length: 15 }, (_, i) => i + 18), ...Array(17).fill(null)]); eq(r.unresolvedNameIds, Array.from({ length: 17 }, (_, i) => i + 15)); assert(r.rows.every((row, i) => row.slot === i + 1 && row.libraryIds.length === 32 && row.libraryIds.every((id, j) => id === j))); assert(r.rows.every(row => Buffer.byteLength(JSON.stringify(row)) <= 128)); assert(Buffer.byteLength(JSON.stringify({ ...r, rows: [], libraryNames: [] })) <= 2048); assert(Buffer.byteLength(JSON.stringify(r) + '\n') <= 16384); deeplyFrozen(r); });

  assert.deepEqual(cases.map(([id]) => id), Array.from({ length: 32 }, (_, i) => 'D' + String(i + 1).padStart(2, '0')), 'Frozen dependency FIRST roster');
  const failed_case_ids = [];
  for (const [id, execute] of cases) { try { await execute(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: KIND, executed: cases.length, passed: cases.length - failed_case_ids.length,
    failed: failed_case_ids.length, failed_case_ids };
}
