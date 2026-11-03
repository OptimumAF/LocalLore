// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST, contracta857bb16, frozen BEFORE producer. ALL16 UNRUN.
// Original synthetic JSON only; no producer fixture helper, parser, SDK,
// filesystem, process, environment, timer, source evaluation or top-level run.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const V1 = 'msvc-library-metadata-v1', V2 = 'msvc-library-metadata-v2';
const INVALID = 'WorkerPrelinkEvidenceV2Invalid', LIMIT = 'WorkerPrelinkEvidenceV2Limit';
const SETUP = 'WorkerPrelinkEvidenceV2Setup';
const INPUT = ['dependencySnapshot', 'runtimeSnapshot', 'catalog', 'dependencyRoot', 'runtimeRoot'];
const OUTPUT = ['version', 'kind', 'purpose', 'qualified', 'linkQualification',
  'closureComplete', 'status', 'anchors', 'profiles', 'counts', 'knownNames',
  'providedSlots', 'unresolvedNameIds', 'runtimeMetadataAvailable', 'knownNamesCovered', 'requiresFreshAdmission'];
const RUNTIME_PROOFS = ['module', 'parser', 'heldReader', 'collector', 'first', 'supervisor',
  'runtimeSnapshot', 'runtimeRootReview', 'paddingSnapshot', 'paddingRootReview', 'descriptor'];
const OUTER_PROOFS = ['reader', 'supervisor', 'helper', 'cohortFirst', 'projection', 'projectionFirst',
  'observerFirst', 'roster', 'diagnostic', 'cohortSnapshot', 'codebook', 'descriptor', 'pins', 'catalog'];
const COUPLINGS = [['reader', 'reader'], ['supervisor', 'supervisor'], ['helper', 'helper'],
  ['first', 'cohortFirst'], ['roster', 'roster'], ['descriptor', 'descriptor'], ['codebook', 'codebook']];
const CONTEXT = ['memberIndex', 'memberOffset', 'sectionIndex', 'sections', 'directiveBytes', 'tokenCount', 'actual', 'limit'];
const H = 'a'.repeat(64), OTHER = 'e'.repeat(64);
const eq = (a, b) => assert.deepEqual(a, b);
const clone = x => JSON.parse(JSON.stringify(x));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const raw = x => Buffer.from(JSON.stringify(x));
const digest = x => sha(raw(x));
const keys = (x, wanted) => eq(Object.keys(x).sort(), [...wanted].sort());
const throws = (fn, message = INVALID) => assert.throws(fn, { message });
function deepFrozen(x) {
  if (x !== null && typeof x === 'object') {
    assert(Object.isFrozen(x)); assert(!Buffer.isBuffer(x)); Object.values(x).forEach(deepFrozen);
  }
}
function gates(kind, count) {
  return { version: 1, kind, executed: count, passed: count, failed: 0, failed_case_ids: [] };
}
function refusal(sections = 0, overrides = {}) {
  return { status: 'refused', summary: null, error: { kind: 'LibraryInputsFormat',
    site: 'coff_relocation_pointer', context: { ...Object.fromEntries(CONTEXT.map(k => [k, null])),
      sections, directiveBytes: 0, tokenCount: 0 }, ...overrides } };
}
function parsed(mode, sections, names = []) {
  return { status: 'parsed', summary: { profileId: mode, objects: 1, imports: 0, sections,
    deviations: { unknownMachineObjects: 0, unusedRelocationPointers: 0, terminalNulSections: 0,
      ...(mode === V2 ? { nulArchivePaddingMembers: 0 } : {}) },
    metadataSha256: H, defaultLibraries: [...names] }, error: null };
}
function io(bytes) {
  return { reservedInputs: 1, reservedBytes: bytes, reservedReadBytes: 2 * bytes,
    actualReadBytes: 2 * bytes, opened: true, closed: true, verifiedPasses: 2 };
}
function runtimeRow(index) {
  const bytes = [20, 30][index];
  return { slot: 33 + index, name: ['ucrt.lib', 'vcruntime.lib'][index], rootIndex: [3, 1][index],
    status: 'complete', pin: { bytes, sha256: H, rootIdentity: 'synthetic-root-' + index,
      leafIdentity: 'synthetic-leaf-' + index }, io: io(bytes), strict: refusal(index * 2),
    profile: parsed(V2, [3, 5][index]) };
}
function runtimeSections(f) {
  f.runtimeSnapshot.job.sections = f.runtimeSnapshot.rows.reduce((total, row) => total +
    [row.strict, row.profile].reduce((n, mode) => n + (mode.status === 'parsed' ?
      mode.summary.sections : mode.error.context.sections ?? 0), 0), 0);
}
function graph(f, names = ['kernel32.lib', 'ucrt.lib', 'vcruntime.lib']) {
  const dep = f.dependencySnapshot, facts = dep.facts;
  facts.libraryNames = [...names];
  facts.rows = Array.from({ length: 32 }, (_, i) => ({ slot: i + 1,
    libraryIds: i === 0 ? names.map((_, id) => id) : [] }));
  dep.cohort.rows = facts.rows.map((row, i) => {
    const libraries = row.libraryIds.map(id => names[id]);
    const metadata = { objects: 1, imports: 0, directives: libraries.map(n => '/DEFAULTLIB:' + n),
      defaultLibraries: libraries };
    const profile = [0, 1, 0, libraries.length, libraries.length, 1, 0, i < 19 ? 1 : 0, 0, digest(metadata)];
    return { slot: i + 1, strict: i < 19 ? [1, 0, 36, 0, 8, 0, 1, 0, 0, null, null] : [...profile], profile };
  });
  const pins = dep.cohort.rows.map(row => ({ slot: row.slot,
    metadataSha256: row.profile[9], libraryCount: row.profile[4] }));
  facts.pinsSha256 = digest(pins); dep.proofs.pins = facts.pinsSha256;
  catalogCoupling(f);
}
function catalogCoupling(f) {
  const dep = f.dependencySnapshot, facts = dep.facts;
  facts.catalogSha256 = digest(f.catalog); dep.proofs.catalog = facts.catalogSha256;
  facts.providedSlots = facts.libraryNames.map(name => f.catalog.find(row => row.name === name)?.slot ?? null);
  facts.unresolvedNameIds = facts.providedSlots.flatMap((slot, i) => slot === null ? [i] : []);
  facts.allReferencesInProvidedCatalog = facts.unresolvedNameIds.length === 0;
}
function fixture() {
  const proofs = Object.fromEntries(OUTER_PROOFS.map(key => [key, H]));
  const cohort = { version: 1, kind: 'msvc_profile_cohort_v1', profileId: V1,
    purpose: 'build_input_metadata_only', qualified: false, linkQualification: false,
    closureComplete: false, captureComplete: true, status: 'complete',
    selfchecks: gates('msvc_profile_cohort_first_v1', 52),
    proofs: Object.fromEntries(COUPLINGS.map(([inner, outer]) => [inner, proofs[outer]])),
    job: { profileId: V1, inputCount: 32, inputBytes: 640, attempts: 64, sections: 64, stopped: false },
    io: { reservedInputs: 32, reservedBytes: 640, reservedReadBytes: 1280, actualReadBytes: 1280 },
    rows: [], strictRefusals: 19, profileParsed: 32, critical: null };
  const facts = { version: 1, kind: 'msvc_library_dependency_facts_v1', profileId: V1,
    purpose: 'build_input_metadata_only', qualified: false, linkQualification: false,
    closureComplete: false, captureComplete: true, status: 'metadata_facts_complete',
    pinsSha256: H, catalogSha256: H, libraryNames: [], providedSlots: [], rows: [],
    unresolvedNameIds: [], allReferencesInProvidedCatalog: false };
  const dependencySnapshot = { version: 1, kind: 'msvc_dependency_observation_v1',
    qualified: false, linkQualification: false, closureComplete: false, captureComplete: true,
    status: 'complete', selfchecks: { cohort: gates('msvc_profile_cohort_first_v1', 52),
      projection: gates('library_metadata_dependency_first_v1', 32),
      observer: gates('library_metadata_dependency_observer_first_v1', 15) },
    proofs, cohort, facts, critical: null };
  const runtimeSnapshot = { version: 2, kind: 'fixed_two_runtime_metadata_v2', purpose: 'build_input_metadata_only',
    qualified: false, linkQualification: false, closureComplete: false, captureComplete: true, status: 'complete',
    proofs: Object.fromEntries(RUNTIME_PROOFS.map(key => [key, H])),
    job: { profileId: V2, inputCount: 2, inputBytes: 50, attempts: 4, sections: 10, stopped: false },
    io: { reservedInputs: 2, reservedBytes: 50, reservedReadBytes: 100, actualReadBytes: 100 },
    rows: [runtimeRow(0), runtimeRow(1)], critical: null };
  const root = kind => ({ version: 1, kind, passed: true, knownClosed: true, noAutomaticRetry: true,
    sourceRevision: 'a'.repeat(40), process: H, result: H, snapshot: H,
    qualified: false, linkQualification: false, closureComplete: false });
  const f = { dependencySnapshot, runtimeSnapshot,
    catalog: Array.from({ length: 15 }, (_, i) => ({ slot: i + 18,
      name: i === 0 ? 'kernel32.lib' : 'known-' + String(i).padStart(2, '0') + '.lib' })),
    dependencyRoot: { ...root('b2_msvc_dependency_observation_root_review_v1'), settled: true, approvedPacketSpent: true },
    runtimeRoot: { ...root('runtime_metadata_v2_root_review_v1'), grantSpent: true } };
  graph(f); return f;
}
function pack(f = fixture(), keepRootSnapshots = false) {
  const input = { dependencySnapshot: raw(f.dependencySnapshot), runtimeSnapshot: raw(f.runtimeSnapshot), catalog: raw(f.catalog) };
  if (!keepRootSnapshots) {
    f.dependencyRoot.snapshot = sha(input.dependencySnapshot); f.runtimeRoot.snapshot = sha(input.runtimeSnapshot);
  }
  input.dependencyRoot = raw(f.dependencyRoot); input.runtimeRoot = raw(f.runtimeRoot);
  const anchors = Object.fromEntries(INPUT.map(key => [key, sha(input[key])]));
  assert(INPUT.reduce((n, key) => n + input[key].length, 0) < 128 * 1024, 'FIRST fixture-set ceiling');
  return { f, input, anchors };
}
function expected(p, status = 'metadata_available_known_names_covered') {
  return { version: 2, kind: 'worker_prelink_evidence_v2', purpose: 'build_input_metadata_only',
    qualified: false, linkQualification: false, closureComplete: false, status, anchors: { ...p.anchors },
    profiles: [{ firstSlot: 1, lastSlot: 32, profileId: V1 }, { firstSlot: 33, lastSlot: 34, profileId: V2 }],
    counts: { historicalInputs: 32, runtimeInputs: 2, historicalReferences: 3 },
    knownNames: ['kernel32.lib', 'ucrt.lib', 'vcruntime.lib'], providedSlots: [18, 33, 34],
    unresolvedNameIds: [], runtimeMetadataAvailable: true, knownNamesCovered: true, requiresFreshAdmission: true };
}

export async function runWorkerPrelinkEvidenceV2Selfchecks(api) {
  if (!api || typeof api.createWorkerPrelinkEvidenceV2 !== 'function' || Object.keys(api).length !== 1) {
    throw Error('UNRUN_SETUP: worker prelink evidence v2 factory unavailable');
  }
  const create = api.createWorkerPrelinkEvidenceV2, cases = [], add = (id, run) => cases.push([id, run]);
  const bind = p => create(p.anchors).bind(p.input);
  const invalid = (change, code = INVALID) => { const f = fixture(); change(f); const p = pack(f); throws(() => bind(p), code); };

  add('E01', () => {
    const p = pack(), binder = create(p.anchors); keys(binder, ['bind']); assert(Object.isFrozen(binder));
    const original = { ...p.anchors }; p.anchors.catalog = OTHER; eq(binder.bind(p.input).anchors, original);
    for (const bad of [null, [], {}, Object.create(original), { ...original, extra: H },
      { ...original, catalog: new String(original.catalog) }, { ...original, catalog: 'A'.repeat(64) },
      { ...original, catalog: H + '\n' }]) throws(() => create(bad), SETUP);
    let touched = 0; const accessor = { ...original };
    Object.defineProperty(accessor, 'catalog', { enumerable: true, get() { touched++; return original.catalog; } });
    throws(() => create(accessor), SETUP); assert.equal(touched, 0);
    const symbol = { ...original }; symbol[Symbol('extra')] = H; throws(() => create(symbol), SETUP);
    const nullPrototype = Object.assign(Object.create(null), original); eq(create(nullPrototype).bind(p.input).anchors, original);
  });
  add('E02', () => {
    const p = pack(), value = bind(p); eq(value, expected(p)); eq(Object.keys(value), OUTPUT); deepFrozen(value);
    assert.equal(value.counts.historicalReferences, 3); // synthetic graph, NOT the actual71-reference capture
    for (const flag of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(value[flag], false);
    assert.equal(value.requiresFreshAdmission, true); assert(Buffer.byteLength(JSON.stringify(value)) <= 12288);
  });
  add('E03', () => {
    const p = pack(), valid = bind(p);
    for (const key of INPUT) {
      const different = { ...p.input, [key]: Buffer.concat([p.input[key], Buffer.from(' ')]) };
      throws(() => create(p.anchors).bind(different)); // semantically same JSON, different raw-byte digest
    }
    const pretty = { ...p.input, catalog: Buffer.from(JSON.stringify(p.f.catalog, null, 2)) };
    const prettyAnchors = { ...p.anchors, catalog: sha(pretty.catalog) };
    const accepted = create(prettyAnchors).bind(pretty); eq(accepted, { ...valid, anchors: prettyAnchors });
    for (const bytes of [Buffer.from('{'), Buffer.from([0xc3, 0x28]),
      Buffer.concat([Buffer.from([0xef, 0xbb, 0xbf]), p.input.catalog])]) {
      const bad = { ...p.input, catalog: bytes }, anchors = { ...p.anchors, catalog: sha(bytes) };
      throws(() => create(anchors).bind(bad)); // digest MATCHES; strict decode/JSON/BOM still refuse
    }
    const malformed = { ...p.input, catalog: Buffer.from([0xff]) }; throws(() => create(p.anchors).bind(malformed));
    eq(bind(p), valid); // pure refusal cannot poison an otherwise unchanged call
  });
  add('E04', () => {
    const p = pack();
    for (const [key, maximum] of [['dependencySnapshot', 24576], ['runtimeSnapshot', 24576],
      ['catalog', 8192], ['dependencyRoot', 4096], ['runtimeRoot', 4096]]) {
      const bytes = Buffer.alloc(maximum + 1, 32), input = { ...p.input, [key]: bytes };
      const anchors = { ...p.anchors, [key]: sha(bytes) }; throws(() => create(anchors).bind(input), LIMIT);
      // Additive boundary calibration, still BEFORE producer. Valid original
      // JSON plus ASCII whitespace must pass at each inclusive byte ceiling.
      assert(p.input[key].length <= maximum);
      const padded = Buffer.concat([p.input[key], Buffer.alloc(maximum - p.input[key].length, 32)]);
      assert.equal(padded.length, maximum);
      const positiveInput = { ...p.input, [key]: padded };
      const positiveAnchors = { ...p.anchors, [key]: sha(padded) };
      if (key === 'dependencySnapshot' || key === 'runtimeSnapshot') {
        const rootKey = key === 'dependencySnapshot' ? 'dependencyRoot' : 'runtimeRoot';
        positiveInput[rootKey] = raw({ ...p.f[rootKey], snapshot: sha(padded) });
        positiveAnchors[rootKey] = sha(positiveInput[rootKey]);
      }
      assert(INPUT.reduce((sum, field) => sum + positiveInput[field].length, 0) < 128 * 1024);
      eq(create(positiveAnchors).bind(positiveInput), { ...expected(p), anchors: positiveAnchors });
    }
    for (const bad of [null, [], Object.create(p.input), { ...p.input, catalog: p.f.catalog },
      { ...p.input, catalog: new Uint8Array(p.input.catalog) }, { ...p.input, catalog: Buffer.alloc(0) },
      { ...p.input, extra: Buffer.from('{}') }]) throws(() => create(p.anchors).bind(bad));
    let touched = 0; const accessor = { ...p.input };
    Object.defineProperty(accessor, 'runtimeRoot', { enumerable: true, get() { touched++; return p.input.runtimeRoot; } });
    throws(() => create(p.anchors).bind(accessor)); assert.equal(touched, 0);
    const symbol = { ...p.input }; symbol[Symbol('extra')] = Buffer.from('{}');
    throws(() => create(p.anchors).bind(symbol));
    const nullPrototype = Object.assign(Object.create(null), p.input);
    eq(create(p.anchors).bind(nullPrototype), expected(p));
    const f = fixture(), long = Array.from({ length: 32 }, (_, i) => 'n' + String(i).padStart(2, '0') + 'x'.repeat(252) + '.lib');
    f.catalog = long.slice(0, 15).map((name, i) => ({ slot: i + 18, name })); graph(f, long);
    const q = pack(f), value = bind(q); eq(value.knownNames, long); assert.equal(value.knownNames.length, 32);
    assert(Buffer.byteLength(JSON.stringify(value)) <= 12288); assert.equal(value.status, 'known_names_unresolved');
  });
  add('E05', () => {
    const baseline = pack(); eq(bind(baseline), expected(baseline));
    for (const change of [f => f.dependencySnapshot.extra = 1, f => f.dependencySnapshot.kind = 'other',
      f => f.dependencySnapshot.version = 2, f => f.dependencySnapshot.captureComplete = false,
      f => f.dependencySnapshot.status = 'stopped', f => f.dependencySnapshot.qualified = true,
      f => f.dependencySnapshot.critical = 'private-error', f => f.dependencySnapshot.cohort.profileId = V2,
      f => f.dependencySnapshot.cohort.extra = 1, f => f.dependencySnapshot.cohort.job.stopped = true,
      f => f.dependencySnapshot.cohort.job.inputCount = 31, f => f.dependencySnapshot.cohort.job.attempts = 63,
      f => f.dependencySnapshot.cohort.profileParsed = 31, f => f.dependencySnapshot.cohort.rows.pop(),
      f => f.dependencySnapshot.cohort.rows[0].profile[0] = 1]) invalid(change);
    for (const key of ['cohort', 'projection', 'observer']) {
      invalid(f => f.dependencySnapshot.selfchecks[key].passed--);
      invalid(f => f.dependencySnapshot.selfchecks[key].failed_case_ids.push('synthetic_failure'));
      invalid(f => f.dependencySnapshot.selfchecks[key].kind = 'wrong_kind');
    }
    invalid(f => f.dependencySnapshot.cohort.selfchecks.passed--);
    for (const [inner] of COUPLINGS) invalid(f => f.dependencySnapshot.cohort.proofs[inner] = OTHER);
  });
  add('E06', () => {
    for (const change of [f => f.dependencySnapshot.facts.extra = 1,
      f => f.dependencySnapshot.facts.kind = 'other', f => f.dependencySnapshot.facts.profileId = V2,
      f => f.dependencySnapshot.facts.catalogSha256 = OTHER, f => f.dependencySnapshot.proofs.catalog = OTHER,
      f => f.dependencySnapshot.facts.pinsSha256 = OTHER, f => f.dependencySnapshot.proofs.pins = OTHER,
      f => f.dependencySnapshot.cohort.rows[0].profile[9] = OTHER,
      f => f.dependencySnapshot.cohort.rows[0].profile[4] = 2,
      f => f.catalog.pop(), f => f.catalog[0].slot = 19,
      f => f.catalog[1].name = f.catalog[0].name, f => f.catalog[0].name = '../bad.lib',
      f => f.catalog[0].name = 'Kernel32.lib', f => f.catalog[0].extra = 1]) invalid(change);
    // Even mutually matching supplied pin hashes must equal freshly derived profile pins.
    invalid(f => { f.dependencySnapshot.facts.pinsSha256 = OTHER; f.dependencySnapshot.proofs.pins = OTHER; });
  });
  add('E07', () => {
    for (const change of [f => f.dependencySnapshot.facts.rows.pop(),
      f => f.dependencySnapshot.facts.rows[1].slot = 1,
      f => f.dependencySnapshot.facts.rows[0].libraryIds = [0, 0, 2],
      f => f.dependencySnapshot.facts.rows[0].libraryIds = [0, 2, 1],
      f => f.dependencySnapshot.facts.rows[0].libraryIds = [0, 1, 3],
      f => f.dependencySnapshot.facts.rows[0].libraryIds = [0, null, 2],
      f => f.dependencySnapshot.facts.rows[0].libraryIds = [0, 1],
      f => f.dependencySnapshot.facts.rows[0].extra = 1,
      f => f.dependencySnapshot.facts.libraryNames.reverse(),
      f => f.dependencySnapshot.facts.libraryNames.push('zz-unused.lib'),
      f => f.dependencySnapshot.facts.libraryNames[1] = 'kernel32.lib']) invalid(change);
    // Repair pins/counts for the altered row; the unused third name still refuses.
    invalid(f => {
      f.dependencySnapshot.facts.rows[0].libraryIds = [0, 1];
      f.dependencySnapshot.cohort.rows[0].profile[4] = 2;
      const pins = f.dependencySnapshot.cohort.rows.map(r => ({ slot: r.slot, metadataSha256: r.profile[9], libraryCount: r.profile[4] }));
      f.dependencySnapshot.facts.pinsSha256 = digest(pins); f.dependencySnapshot.proofs.pins = digest(pins);
    });
  });
  add('E08', () => {
    for (const change of [f => f.dependencySnapshot.facts.providedSlots[1] = 33,
      f => f.dependencySnapshot.facts.providedSlots[0] = null,
      f => f.dependencySnapshot.facts.unresolvedNameIds = [],
      f => f.dependencySnapshot.facts.unresolvedNameIds.reverse(),
      f => f.dependencySnapshot.facts.allReferencesInProvidedCatalog = true]) invalid(change);
    const f = fixture(); f.catalog[1].name = 'ucrt.lib'; catalogCoupling(f);
    const p = pack(f); throws(() => bind(p));
    // Even a coherently joined old catalog cannot be silently overwritten by
    // the fixed33/34 runtime presence extension.
    const other = fixture(); other.catalog[1].name = 'vcruntime.lib'; catalogCoupling(other);
    throws(() => bind(pack(other)));
  });
  add('E09', () => {
    for (const change of [f => f.runtimeSnapshot.rows.reverse(), f => f.runtimeSnapshot.rows[0].slot = 34,
      f => f.runtimeSnapshot.rows[1].name = 'other.lib', f => f.runtimeSnapshot.rows[0].rootIndex = 1,
      f => f.runtimeSnapshot.rows[0].status = 'reading', f => f.runtimeSnapshot.rows[0].pin = null,
      f => f.runtimeSnapshot.rows[0].pin.bytes = 0, f => f.runtimeSnapshot.rows[0].pin.bytes = 285589,
      f => f.runtimeSnapshot.rows[1].pin.bytes = 38479, f => f.runtimeSnapshot.rows[0].pin.sha256 = H + '\n',
      f => f.runtimeSnapshot.rows[0].pin.rootIdentity = 'private/path',
      f => f.runtimeSnapshot.rows[0].pin.leafIdentity = 'x'.repeat(257),
      f => f.runtimeSnapshot.rows[0].io.verifiedPasses = 1, f => f.runtimeSnapshot.rows[0].io.closed = false,
      f => f.runtimeSnapshot.rows[0].io.opened = false, f => f.runtimeSnapshot.rows[0].io.actualReadBytes--,
      f => f.runtimeSnapshot.rows[0].io.reservedReadBytes--, f => f.runtimeSnapshot.io.actualReadBytes--,
      f => f.runtimeSnapshot.io.reservedBytes++, f => f.runtimeSnapshot.rows[0].io.extra = 1]) invalid(change);
  });
  add('E10', () => {
    for (const change of [f => f.runtimeSnapshot.job.profileId = V1,
      f => f.runtimeSnapshot.job.inputCount = 1, f => f.runtimeSnapshot.job.inputBytes = 49,
      f => f.runtimeSnapshot.job.attempts = 3, f => f.runtimeSnapshot.job.sections = 8,
      f => f.runtimeSnapshot.job.sections = 2097153, f => f.runtimeSnapshot.job.stopped = true,
      f => f.runtimeSnapshot.job.extra = 1]) invalid(change);
    const nullCharge = fixture(); nullCharge.runtimeSnapshot.rows[0].strict.error.context.sections = null;
    runtimeSections(nullCharge); const n = pack(nullCharge); eq(bind(n), expected(n));
    const declared = fixture();
    // Synthetic report-policy fixture, not a binary observation: a declaration
    // of300000 sections needs at least the56-byte BIGOBJ header before charge.
    declared.runtimeSnapshot.rows[0].pin.bytes = 56;
    declared.runtimeSnapshot.rows[0].io = io(56);
    declared.runtimeSnapshot.job.inputBytes = 86;
    declared.runtimeSnapshot.io = { reservedInputs: 2, reservedBytes: 86,
      reservedReadBytes: 172, actualReadBytes: 172 };
    for (const key of ['strict', 'profile']) declared.runtimeSnapshot.rows[0][key] = refusal(300000, {
      kind: 'LibraryInputsSize', site: 'coff_sections_member', context: { ...Object.fromEntries(CONTEXT.map(k => [k, null])),
        sections: 300000, directiveBytes: 0, tokenCount: 0, actual: 300000, limit: 65536 } });
    runtimeSections(declared); assert.equal(declared.runtimeSnapshot.job.sections, 600007);
    const d = pack(declared), unavailable = bind(d);
    assert.equal(unavailable.status, 'metadata_unavailable'); assert.equal(unavailable.runtimeMetadataAvailable, false);
    assert.equal(unavailable.requiresFreshAdmission, true); assert.equal(unavailable.qualified, false);
    const oldParsed = fixture(); oldParsed.runtimeSnapshot.rows[0].strict = parsed('strict-v1', 4);
    runtimeSections(oldParsed); const p = pack(oldParsed); eq(bind(p), expected(p));
  });
  add('E11', () => {
    for (const change of [f => f.runtimeSnapshot.kind = 'other', f => f.runtimeSnapshot.extra = 1,
      f => f.runtimeSnapshot.version = 1, f => f.runtimeSnapshot.purpose = 'build_authority',
      f => f.runtimeSnapshot.captureComplete = false, f => f.runtimeSnapshot.status = 'stopped',
      f => f.runtimeSnapshot.critical = 'private-error', f => f.runtimeSnapshot.linkQualification = true,
      f => f.runtimeSnapshot.proofs.extra = H, f => f.runtimeSnapshot.proofs.parser = 'A'.repeat(64),
      f => f.runtimeSnapshot.rows[0].profile.summary.profileId = V1,
      f => delete f.runtimeSnapshot.rows[0].profile.summary.deviations.nulArchivePaddingMembers,
      f => f.runtimeSnapshot.rows[0].profile.summary.deviations.extra = 0,
      f => f.runtimeSnapshot.rows[0].profile.summary.deviations.nulArchivePaddingMembers = 65537,
      f => f.runtimeSnapshot.rows[0].profile.summary.metadataSha256 = 'not-a-digest',
      f => f.runtimeSnapshot.rows[0].profile.summary.objects = 65537,
      f => f.runtimeSnapshot.rows[0].profile.summary.defaultLibraries = ['z.lib', 'a.lib'],
      f => f.runtimeSnapshot.rows[0].profile.summary.defaultLibraries = ['a.lib', 'a.lib'],
      f => f.runtimeSnapshot.rows[0].profile.summary.defaultLibraries = ['../unsafe.lib'],
      f => f.runtimeSnapshot.rows[0].profile = { status: 'failed', summary: null, error: null },
      f => f.runtimeSnapshot.rows[0].profile = null,
      f => f.runtimeSnapshot.rows[0].strict.error.kind = 'private-error',
      f => f.runtimeSnapshot.rows[0].strict.error.site = 'private/path',
      f => f.runtimeSnapshot.rows[0].strict.error.context.extra = 1,
      f => f.runtimeSnapshot.rows[0].strict.error.context.sections = -1,
      f => f.runtimeSnapshot.rows[0].strict.error.context.limit = '65536']) invalid(change);
    invalid(f => { f.runtimeSnapshot.rows[0].strict = parsed('strict-v1', 1);
      f.runtimeSnapshot.rows[0].strict.summary.deviations.nulArchivePaddingMembers = 0; runtimeSections(f); });
    invalid(f => { f.runtimeSnapshot.rows[0].profile.summary.sections = 262145; runtimeSections(f); });
    invalid(f => { f.runtimeSnapshot.rows[0].profile.summary.defaultLibraries = Array.from({ length: 33 }, (_, i) => 'n' + String(i).padStart(2, '0') + '.lib'); });
  });
  add('E12', () => {
    for (const root of ['dependencyRoot', 'runtimeRoot']) {
      for (const key of ['passed', 'knownClosed', 'noAutomaticRetry']) invalid(f => f[root][key] = false);
      for (const flag of ['qualified', 'linkQualification', 'closureComplete']) invalid(f => f[root][flag] = true);
      invalid(f => f[root].kind = 'unrelated_root'); invalid(f => f[root].sourceRevision = 'a'.repeat(39));
      invalid(f => f[root].process = H + '\n'); invalid(f => f[root].result = { value: H });
      const f = fixture(); pack(f); f[root].snapshot = OTHER;
      const p = pack(f, true); throws(() => bind(p));
    }
    for (const change of [f => f.dependencyRoot.settled = false, f => f.dependencyRoot.approvedPacketSpent = false,
      f => f.runtimeRoot.grantSpent = false]) invalid(change);
    const historical = fixture(); historical.dependencyRoot.noApp = true;
    historical.runtimeRoot.retainedPriorFailure = { passed: false, immutable: true };
    const p = pack(historical); eq(bind(p), expected(p)); // historical extras stay bound, not stripped before SHA
  });
  add('E13', () => {
    for (const index of [0, 1]) {
      const f = fixture(); f.runtimeSnapshot.rows[index].profile = refusal(0); runtimeSections(f);
      const p = pack(f), value = bind(p);
      eq(value, { ...expected(p, 'metadata_unavailable'), runtimeMetadataAvailable: false });
      assert.equal(value.knownNamesCovered, true); eq(value.providedSlots, [18, 33, 34]);
    }
  });
  add('E14', () => {
    for (const mode of ['strict', 'profile']) {
      const f = fixture(); f.runtimeSnapshot.rows[0][mode] = parsed(mode === 'strict' ? 'strict-v1' : V2, 3, ['extra.lib']);
      runtimeSections(f); const p = pack(f), value = bind(p);
      eq(value, expected(p, 'unsupported_runtime_dependencies'));
      assert(!value.knownNames.includes('extra.lib')); assert(!Object.hasOwn(value, 'facts'));
      assert.equal(value.qualified, false); assert.equal(value.closureComplete, false);
    }
  });
  add('E15', () => {
    const f = fixture(); graph(f, ['kernel32.lib', 'ucrt.lib', 'vcruntime.lib', 'zz-unresolved.lib']);
    const p = pack(f), value = bind(p);
    eq(value.knownNames, f.dependencySnapshot.facts.libraryNames); eq(value.providedSlots, [18, 33, 34, null]);
    eq(value.unresolvedNameIds, [3]); assert.equal(value.knownNamesCovered, false);
    assert.equal(value.status, 'known_names_unresolved'); assert.equal(value.counts.historicalReferences, 4);
    f.runtimeSnapshot.rows[0].profile.summary.defaultLibraries = ['extra.lib'];
    const unsupported = bind(pack(f)); assert.equal(unsupported.status, 'unsupported_runtime_dependencies');
    eq(unsupported.unresolvedNameIds, [3]); assert.equal(unsupported.knownNamesCovered, false);
    f.runtimeSnapshot.rows[1].profile = refusal(0); runtimeSections(f);
    const unavailable = bind(pack(f)); assert.equal(unavailable.status, 'metadata_unavailable');
    assert.equal(unavailable.runtimeMetadataAvailable, false); eq(unavailable.unresolvedNameIds, [3]);
  });
  add('E16', () => {
    const p = pack(), before = Object.fromEntries(INPUT.map(key => [key, Buffer.from(p.input[key])])), binder = create(p.anchors);
    const first = binder.bind(p.input), saved = clone(first), second = binder.bind(p.input);
    eq(first, second); assert.notEqual(first, second); assert.notEqual(first.anchors, second.anchors); deepFrozen(first);
    assert.throws(() => first.knownNames.push('bad.lib'), TypeError);
    for (const key of INPUT) assert(p.input[key].equals(before[key]));
    p.input.runtimeRoot.fill(32); eq(first, saved); throws(() => binder.bind(p.input));
    p.input.runtimeRoot = before.runtimeRoot; eq(binder.bind(p.input), saved);
    const encoded = JSON.stringify(first); assert(Buffer.byteLength(encoded) <= 12288);
    for (const privateText of ['synthetic-root', 'synthetic-leaf', 'coff_relocation_pointer',
      'rootIdentity', 'leafIdentity', 'metadataSha256', 'process', 'sourceRevision', 'libraryIds', '/DEFAULTLIB:']) {
      assert(!encoded.includes(privateText));
    }
    keys(first.counts, ['historicalInputs', 'runtimeInputs', 'historicalReferences']);
    eq(first.profiles.map(x => x.profileId), [V1, V2]); assert.equal(first.requiresFreshAdmission, true);
  });

  eq(cases.map(([id]) => id), Array.from({ length: 16 }, (_, i) => 'E' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: 'worker_prelink_evidence_v2_first', executed: 16,
    passed: 16 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
