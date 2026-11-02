// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST: D04_MSVC_DEPENDENCY_OBSERVATION_CONTRACT_2026-11-01.
// SOURCE-ONLY / UNRUN. No producer import, top-level execution, filesystem,
// environment, process, SDK/binary input, network or source evaluation.
// Small synthetic JSON fixtures and independent SHA256s; conservatively<1MiB.
// Binding returns a fresh envelope retaining the EXACT parsed result reference;
// these cases do not claim a deep copy, freeze or real-input authentication.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const KIND = 'library_metadata_dependency_observer_first_v1';
const INVALID = 'DependencyObservationMismatch';
const ID = 'msvc-library-metadata-v1';
const clone = value => JSON.parse(JSON.stringify(value));
const digest = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const eq = (a, b) => assert.deepEqual(a, b);
function encode(profile) {
  // Independent expected wire construction, not a copied producer validator.
  const m = profile.metadata, d = profile.deviations;
  return [0, m.objects, m.imports, m.directives.length, m.defaultLibraries.length,
    profile.sections, d.unknownMachineObjects, d.unusedRelocationPointers,
    d.terminalNulSections, digest(m)];
}
function fixture() {
  const profile = { profileId: ID, purpose: 'build_input_metadata_only',
    qualified: false, linkQualification: false, closureComplete: false,
    metadata: { objects: 1, imports: 0, directives: ['/DEFAULTLIB:alpha'], defaultLibraries: ['alpha.lib'] },
    sections: 2, deviations: { unknownMachineObjects: 0, unusedRelocationPointers: 0, terminalNulSections: 0 } };
  const row = { slot: 1, strict: encode(profile), profile: encode(profile) };
  return { slot: 1, pair: { row, stopped: false, critical: null }, profile, expected: clone(row) };
}
function strictRefusal() {
  // Existing dictionary IDs: Format=0, one known in-range site=0. Context order
  // is memberIndex/memberOffset/sectionIndex/sections/directiveBytes/tokenCount/
  // actual/limit. This proves data binding, not provenance of a real refusal.
  return [1, 0, 0, 0, 8, 0, 1, 0, 0, null, null];
}
function refusalFixture() {
  const f = fixture(); f.pair.row.strict = strictRefusal(); f.expected = clone(f.pair.row); return f;
}
function refuse(bind, f) {
  let caught;
  try { bind(f.slot, f.pair, f.profile, f.expected); } catch (error) { caught = error; }
  assert(caught instanceof Error, 'Expected fixed observation refusal');
  assert.equal(caught.message, INVALID);
  return caught;
}

// Independent small facts/pins/catalog data; never invoke the projection to
// construct the validator's expected graph. Generic pins are schema fixtures,
// not authentication of an actual PR334 observation.
function factsFixture(empty = false) {
  const catalog = Array.from({ length: 15 }, (_, i) => ({ slot: i + 18,
    name: i === 0 ? 'alpha.lib' : `catalog-${String(i).padStart(2, '0')}.lib` }));
  const names = empty ? [] : ['alpha.lib', 'unknown.lib'];
  const rows = Array.from({ length: 32 }, (_, i) => ({ slot: i + 1,
    libraryIds: empty ? [] : i === 0 ? [0, 1] : i === 1 ? [1] : [] }));
  const pins = rows.map(row => {
    const metadata = { objects: 1, imports: 0, directives: [],
      defaultLibraries: row.libraryIds.map(id => names[id]) };
    return { slot: row.slot, metadataSha256: digest(metadata), libraryCount: row.libraryIds.length };
  });
  const facts = { version: 1, kind: 'msvc_library_dependency_facts_v1', profileId: ID,
    purpose: 'build_input_metadata_only', qualified: false, linkQualification: false,
    closureComplete: false, captureComplete: true, status: 'metadata_facts_complete',
    pinsSha256: digest(pins), catalogSha256: digest(catalog), libraryNames: names,
    providedSlots: empty ? [] : [18, null], rows, unresolvedNameIds: empty ? [] : [1],
    allReferencesInProvidedCatalog: empty };
  return { facts, pins, catalog };
}
function refuseFacts(check, f) {
  const before = JSON.stringify(f);
  let error;
  try { check(f.facts, f.pins, f.catalog); } catch (caught) { error = caught; }
  assert(error instanceof Error, 'Expected fixed facts refusal');
  assert.equal(error.message, 'DependencyObservationFactsInvalid');
  assert.equal(JSON.stringify(f), before);
}

export async function runDependencyObserverSelfchecksV1(api) {
  if (!api || typeof api.bindDependencyObservationV1 !== 'function' || typeof api.checkDependencyFactsV1 !== 'function') {
    throw Error('UNRUN_SETUP: dependency observation API unavailable');
  }
  const bind = api.bindDependencyObservationV1;
  const cases = [], add = (id, run) => cases.push([id, run]);

  add('B01', () => {
    const f = fixture(), a = bind(f.slot, f.pair, f.profile, f.expected), b = bind(f.slot, f.pair, f.profile, f.expected);
    eq(Object.keys(a).sort(), ['result', 'slot']); assert.equal(a.slot, 1); assert.equal(a.result, f.profile); assert.notEqual(a, b); assert.equal(b.result, f.profile);
  });
  add('B02', () => {
    for (const value of [0, 33, 1.5, '1', true, null]) { const f = fixture(); f.slot = value; refuse(bind, f); }
    for (const change of [f => f.pair.row.slot = 2, f => f.expected.slot = 2, f => f.slot = 2]) { const f = fixture(); change(f); refuse(bind, f); }
    const last = fixture(); last.slot = 32; last.pair.row.slot = 32; last.expected.slot = 32; assert.equal(bind(last.slot, last.pair, last.profile, last.expected).slot, 32);
  });
  add('B03', () => {
    for (const key of ['row', 'stopped', 'critical']) { const f = fixture(); delete f.pair[key]; refuse(bind, f); }
    const extra = fixture(); extra.pair.extra = 0; refuse(bind, extra);
    for (const value of [0, 'false', null]) { const f = fixture(); f.pair.stopped = value; refuse(bind, f); }
    for (const value of ['BaselineMismatch', false, 0, {}]) { const f = fixture(); f.pair.critical = value; refuse(bind, f); }
  });
  add('B04', () => {
    for (const rowKey of ['row', 'expected']) {
      for (const key of ['slot', 'strict', 'profile']) { const f = fixture(); delete (rowKey === 'row' ? f.pair.row : f.expected)[key]; refuse(bind, f); }
      const f = fixture(); (rowKey === 'row' ? f.pair.row : f.expected).extra = 1; refuse(bind, f);
    }
    // Matching malformed copies must fail validation, not only row equality.
    for (const change of [r => r.strict = null, r => r.profile = null, r => r.strict.pop(), r => r.strict.push(1),
      r => r.strict[0] = 2, r => r.strict[1] = -1, r => r.strict[5] = 65537,
      r => r.strict[6] = 1, r => r.strict[7] = 1, r => r.strict[8] = 1,
      r => r.strict[1] = 65536, r => r.profile[9] = 'A'.repeat(64)]) {
      const f = fixture(); change(f.pair.row); if (f.pair.row.strict?.[1] === 65536) f.pair.row.strict[2] = 1;
      f.expected = clone(f.pair.row); refuse(bind, f);
    }
    for (const change of [a => a[1] = 6, a => a[2] = 88, a => a[3] = -1, a => a[3] = 4297064448, a => a[4] = '8']) {
      const f = refusalFixture(); change(f.pair.row.strict); f.expected = clone(f.pair.row); refuse(bind, f);
    }
  });
  add('B05', () => {
    // Pair and saved row agree with each other, but not with the actual result.
    for (let index = 1; index <= 9; index++) {
      const f = fixture(); f.pair.row.profile[index] = index === 9 ? '0'.repeat(64) : f.pair.row.profile[index] + 1;
      f.expected = clone(f.pair.row); refuse(bind, f);
    }
  });
  add('B06', () => {
    for (const change of [m => m.objects++, m => m.directives[0] = '/DEFAULTLIB:beta', m => m.defaultLibraries[0] = 'beta.lib']) {
      const f = fixture(); change(f.profile.metadata); refuse(bind, f);
    }
  });
  add('B07', () => {
    for (const key of ['qualified', 'linkQualification', 'closureComplete']) for (const value of [true, 0, 'false', null]) {
      const f = fixture(); f.profile[key] = value; refuse(bind, f);
    }
  });
  add('B08', () => {
    for (const value of ['strict-v1', 'unknown', new String(ID)]) { const f = fixture(); f.profile.profileId = value; refuse(bind, f); }
    const purpose = fixture(); purpose.profile.purpose = 'runtime_authority'; refuse(bind, purpose);
    for (const objectKey of ['result', 'metadata', 'deviations']) {
      const select = f => objectKey === 'result' ? f.profile : f.profile[objectKey];
      const original = select(fixture());
      for (const key of Object.keys(original)) { const f = fixture(); delete select(f)[key]; refuse(bind, f); }
      const extra = fixture(); select(extra).extra = 'untrusted'; refuse(bind, extra);
    }
    for (const change of [p => p.sections = 262145, p => p.sections = 0.5,
      p => p.deviations.unknownMachineObjects = 65537, p => p.deviations.unusedRelocationPointers = 262145,
      p => p.deviations.terminalNulSections = -1, p => p.metadata.objects = 65537,
      p => p.metadata.imports = true, p => p.metadata.directives = ['/Z:later', '/A:earlier'],
      p => p.metadata.defaultLibraries = ['alpha.lib', 'alpha.lib']]) {
      const f = fixture(); change(f.profile); f.pair.row.profile = encode(f.profile); f.expected = clone(f.pair.row); refuse(bind, f);
    }
  });
  add('B09', () => {
    const stopped = fixture(); stopped.pair.stopped = true; stopped.pair.critical = 'JobStopped'; refuse(bind, stopped);
    const refused = fixture(); refused.pair.row.profile = strictRefusal(); refused.expected = clone(refused.pair.row); refuse(bind, refused);
  });
  add('B10', () => {
    const valid = refusalFixture(); assert.equal(bind(valid.slot, valid.pair, valid.profile, valid.expected).result, valid.profile);
    for (const change of [r => r.strict[1]++, r => r.strict[5]++, r => r.strict[9] = '0'.repeat(64)]) {
      const f = fixture(); change(f.pair.row); refuse(bind, f);
    }
    for (const change of [a => a[1] = 3, a => a[2] = 1, a => a[3] = 1, a => a[4] = 10, a => a[9] = 4]) {
      const f = refusalFixture(); change(f.pair.row.strict); refuse(bind, f);
    }
  });
  add('B11', () => {
    const f = fixture(), m = f.profile.metadata;
    f.profile.metadata = { defaultLibraries: m.defaultLibraries, directives: m.directives, imports: m.imports, objects: m.objects };
    eq([...Object.values(m)].flat().sort(), [...Object.values(f.profile.metadata)].flat().sort());
    assert.notEqual(digest(f.profile.metadata), f.pair.row.profile[9]); refuse(bind, f);
  });
  add('B12', () => {
    const f = fixture(), before = JSON.stringify(f), r = bind(f.slot, f.pair, f.profile, f.expected);
    assert.equal(JSON.stringify(f), before); eq(Object.keys(r).sort(), ['result', 'slot']);
    assert.equal(r.slot, f.slot); assert.equal(r.result, f.profile); assert.equal(r.result.metadata, f.profile.metadata);
    assert.notEqual(r, f.pair); assert.notEqual(r, f.pair.row); assert.notEqual(r, f.expected);
    const invalid = fixture(), marker = 'private-observation-payload-D:/not-an-input'; invalid.profile.extra = marker;
    const error = refuse(bind, invalid); assert(!error.message.includes(marker)); assert(!JSON.stringify(error).includes(marker));
  });

  add('B13', () => {
    // A nullable context hole serializes exactly like a valid null. Equality
    // alone and slice(...).every(...) therefore fail to reject these cases.
    for (const which of ['pair', 'expected']) {
      const f = refusalFixture();
      delete (which === 'pair' ? f.pair.row.strict : f.expected.strict)[9];
      assert.equal(JSON.stringify(f.pair.row), JSON.stringify(f.expected));
      refuse(bind, f);
    }
    const undefinedContext = refusalFixture(); undefinedContext.pair.row.strict[9] = undefined; refuse(bind, undefinedContext);
    const inherited = refusalFixture(), inheritedValues = Object.create(Array.prototype);
    inheritedValues[9] = null; Object.setPrototypeOf(inherited.pair.row.strict, inheritedValues);
    delete inherited.pair.row.strict[9]; assert.equal(Object.hasOwn(inherited.pair.row.strict, 9), false); refuse(bind, inherited);
    for (const mode of ['strict', 'profile']) {
      const f = fixture(); delete f.pair.row[mode][3]; f.expected = clone(f.pair.row); refuse(bind, f);
    }
    for (const field of ['directives', 'defaultLibraries']) {
      const f = fixture(); delete f.profile.metadata[field][0];
      f.pair.row.profile = encode(f.profile); f.expected = clone(f.pair.row); refuse(bind, f);
    }
    const check = api.checkDependencyFactsV1;
    const missingName = factsFixture(); delete missingName.facts.libraryNames[1];
    // Preserve the old map/flatMap hole-skipping interpretation so that this
    // specifically reaches the prior validator's false acceptance, not merely
    // a different unresolved-list mismatch.
    missingName.facts.unresolvedNameIds = []; missingName.facts.allReferencesInProvidedCatalog = true;
    refuseFacts(check, missingName);
    for (const change of [f => delete f.facts.providedSlots[1], f => delete f.facts.rows[3],
      f => delete f.facts.rows[0].libraryIds[1], f => delete f.facts.unresolvedNameIds[0],
      f => delete f.pins[3], f => delete f.catalog[3]]) {
      const f = factsFixture(); change(f); f.facts.pinsSha256 = digest(f.pins); f.facts.catalogSha256 = digest(f.catalog); refuseFacts(check, f);
    }
  });
  add('B14', () => {
    const check = api.checkDependencyFactsV1;
    for (const empty of [false, true]) {
      const f = factsFixture(empty), before = JSON.stringify(f);
      assert.equal(check(f.facts, f.pins, f.catalog), undefined); assert.equal(JSON.stringify(f), before);
    }
    for (const provided of [false, true]) {
      const f = factsFixture(); f.facts.libraryNames.push('z-unused.lib');
      if (provided) {
        f.catalog[1].name = 'z-unused.lib'; f.facts.catalogSha256 = digest(f.catalog);
        f.facts.providedSlots.push(19);
      } else {
        f.facts.providedSlots.push(null); f.facts.unresolvedNameIds.push(2);
      }
      // Every field is coherent except exact union coverage: index2 is unused.
      refuseFacts(check, f);
    }
  });
  add('B15', () => {
    const check = api.checkDependencyFactsV1;
    for (const value of [new Number(1), '1', true, null, undefined, -1, 0, 0.5, 2, NaN, Infinity, Number.MAX_SAFE_INTEGER + 1]) {
      const f = factsFixture(); f.facts.unresolvedNameIds = [value]; refuseFacts(check, f);
    }
    const twoMissing = () => {
      const f = factsFixture(); f.facts.libraryNames.push('zeta.lib'); f.facts.providedSlots.push(null);
      f.facts.unresolvedNameIds.push(2); f.facts.rows[2].libraryIds = [2];
      f.pins[2] = { slot: 3, metadataSha256: digest({ objects: 1, imports: 0,
        directives: [], defaultLibraries: ['zeta.lib'] }), libraryCount: 1 };
      f.facts.pinsSha256 = digest(f.pins); return f;
    };
    const validIds = twoMissing(); assert.equal(check(validIds.facts, validIds.pins, validIds.catalog), undefined);
    for (const ids of [[], [1], [2, 1], [1, 2, 2], [1, 3], [0, 2]]) {
      const f = twoMissing(); f.facts.unresolvedNameIds = ids; refuseFacts(check, f);
    }
    // Inert data prototypes, not getters/proxies or an execution attack. A
    // boxed record's own fields can look right while JSON serializes to0.
    const wrappers = [record => Object.assign(new Number(0), record),
      record => Object.assign(Object.create({ foreignMarker: 0 }), record)];
    for (const wrap of wrappers) {
      for (const target of ['facts', 'pin', 'catalog', 'row']) {
        const f = factsFixture();
        if (target === 'facts') f.facts = wrap(f.facts);
        if (target === 'pin') f.pins[0] = wrap(f.pins[0]);
        if (target === 'catalog') f.catalog[0] = wrap(f.catalog[0]);
        if (target === 'row') f.facts.rows[0] = wrap(f.facts.rows[0]);
        f.facts.pinsSha256 = digest(f.pins); f.facts.catalogSha256 = digest(f.catalog);
        refuseFacts(check, f);
      }
      for (const target of ['pair', 'rows', 'profile', 'metadata', 'deviations']) {
        const f = fixture();
        if (target === 'pair') f.pair = wrap(f.pair);
        if (target === 'rows') { f.pair.row = wrap(f.pair.row); f.expected = wrap(f.expected); }
        if (target === 'profile') f.profile = wrap(f.profile);
        if (target === 'metadata') f.profile.metadata = wrap(f.profile.metadata);
        if (target === 'deviations') f.profile.deviations = wrap(f.profile.deviations);
        // Keep the profile's actual canonical digest coherent when its
        // metadata wrapper changes JSON representation. Only type is invalid.
        f.pair.row.profile = encode(f.profile);
        f.expected.profile = [...f.pair.row.profile];
        refuse(bind, f);
      }
    }
    const plainFacts = factsFixture();
    for (const record of [plainFacts.facts, ...plainFacts.pins, ...plainFacts.catalog, ...plainFacts.facts.rows]) Object.setPrototypeOf(record, null);
    assert.equal(check(plainFacts.facts, plainFacts.pins, plainFacts.catalog), undefined);
    const plainBinding = fixture();
    for (const record of [plainBinding.pair, plainBinding.pair.row, plainBinding.expected,
      plainBinding.profile, plainBinding.profile.metadata, plainBinding.profile.deviations]) Object.setPrototypeOf(record, null);
    const accepted = bind(plainBinding.slot, plainBinding.pair, plainBinding.profile, plainBinding.expected);
    assert.equal(accepted.result, plainBinding.profile);
  });

  assert.deepEqual(cases.map(([id]) => id), Array.from({ length: 15 }, (_, i) => 'B' + String(i + 1).padStart(2, '0')), 'Frozen observer FIRST roster');
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: KIND, executed: cases.length, passed: cases.length - failed_case_ids.length,
    failed: failed_case_ids.length, failed_case_ids };
}
