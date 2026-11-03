// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Pure development evidence binding; NEVER build/link/execution authority.
import { createHash } from 'node:crypto';

const INVALID = 'WorkerPrelinkEvidenceV2Invalid', LIMIT = 'WorkerPrelinkEvidenceV2Limit';
const INPUT = ['dependencySnapshot', 'runtimeSnapshot', 'catalog', 'dependencyRoot', 'runtimeRoot'];
const CAPS = [24576, 24576, 8192, 4096, 4096];
const V1 = 'msvc-library-metadata-v1', V2 = 'msvc-library-metadata-v2';
const CONTEXT = ['memberIndex', 'memberOffset', 'sectionIndex', 'sections', 'directiveBytes', 'tokenCount', 'actual', 'limit'];
const DEVIATIONS = ['unknownMachineObjects', 'unusedRelocationPointers', 'terminalNulSections'];
const OUTER_PROOFS = ['reader', 'supervisor', 'helper', 'cohortFirst', 'projection', 'projectionFirst',
  'observerFirst', 'roster', 'diagnostic', 'cohortSnapshot', 'codebook', 'descriptor', 'pins', 'catalog'];
const RUNTIME_PROOFS = ['module', 'parser', 'heldReader', 'collector', 'first', 'supervisor',
  'runtimeSnapshot', 'runtimeRootReview', 'paddingSnapshot', 'paddingRootReview', 'descriptor'];
const COUPLINGS = [['reader', 'reader'], ['supervisor', 'supervisor'], ['helper', 'helper'],
  ['first', 'cohortFirst'], ['roster', 'roster'], ['descriptor', 'descriptor'], ['codebook', 'codebook']];
const CATEGORIES = ['Format', 'Unsafe', 'Directive', 'Size', 'Type', 'Profile'].map(x => 'LibraryInputs' + x);
const uint = (v, n = Number.MAX_SAFE_INTEGER) => Number.isSafeInteger(v) && v >= 0 && v <= n;
const hex = (v, length = 64) => typeof v === 'string' && v.length === length && !/[^0-9a-f]/.test(v);
const token = v => typeof v === 'string' && v.length > 0 && v.length <= 256 && !/[^A-Za-z0-9_.:-]/.test(v);
const hash = b => createHash('sha256').update(b).digest('hex');
const digest = v => hash(Buffer.from(JSON.stringify(v)));
const check = (v, code = INVALID) => { if (!v) throw Error(code); };
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
function plain(v) { return v !== null && typeof v === 'object' && [Object.prototype, null].includes(Object.getPrototypeOf(v)); }
function record(v, keys, code = INVALID) {
  try {
    check(plain(v), code);
    const own = Reflect.ownKeys(v);
    check(own.length === keys.length && own.every(k => typeof k === 'string' && keys.includes(k)), code);
    const out = {};
    for (const k of keys) {
      const d = Object.getOwnPropertyDescriptor(v, k);
      check(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code); out[k] = d.value;
    }
    return out;
  } catch { throw Error(code); }
}
function array(v, max, exact = null) {
  check(Array.isArray(v) && v.length <= max && (exact === null || v.length === exact));
  const own = Reflect.ownKeys(v); check(own.length === v.length + 1 && own.includes('length'));
  return Array.from({ length: v.length }, (_, i) => {
    const d = Object.getOwnPropertyDescriptor(v, String(i)); check(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'));
    return d.value;
  });
}
function freeze(v) { if (v !== null && typeof v === 'object') { Object.values(v).forEach(freeze); Object.freeze(v); } return v; }
function falseFlags(v) { check(v.qualified === false && v.linkQualification === false && v.closureComplete === false); }
function complete(v) { falseFlags(v); check(v.captureComplete === true && v.status === 'complete' && v.critical === null); }
function proofs(v, keys) { const p = record(v, keys); check(keys.every(k => hex(p[k]))); return p; }
function gate(v, kind, count) {
  const s = record(v, ['version', 'kind', 'executed', 'passed', 'failed', 'failed_case_ids']);
  check(s.version === 1 && s.kind === kind && s.executed === count && s.passed === count && s.failed === 0);
  array(s.failed_case_ids, 0, 0);
}
function canonicalName(v) {
  return typeof v === 'string' && v.length > 0 && v.length <= 259 && v === v.trim() &&
    !v.startsWith('.') && !v.includes('..') && v.endsWith('.lib') && /^[a-z0-9_+ -]+(?:\.[a-z0-9_+ -]+)*$/.test(v);
}
function names(v, maximum = 32) {
  const list = array(v, maximum); let previous;
  for (const name of list) { check(canonicalName(name) && (previous === undefined || previous < name)); previous = name; }
  return list;
}
function job(v, profileId, count, attempts) {
  const j = record(v, ['profileId', 'inputCount', 'inputBytes', 'attempts', 'sections', 'stopped']);
  check(j.profileId === profileId && j.inputCount === count && j.attempts === attempts &&
    uint(j.inputBytes, 536870912) && j.inputBytes > 0 && uint(j.sections, 2097152) && j.stopped === false);
  return j;
}
function aggregateIO(v, count, bytes) {
  const io = record(v, ['reservedInputs', 'reservedBytes', 'reservedReadBytes', 'actualReadBytes']);
  check(io.reservedInputs === count && io.reservedBytes === bytes && io.reservedReadBytes === 2 * bytes && io.actualReadBytes === 2 * bytes);
}
function encoded(v, profile) {
  const a = array(v, 11);
  if (a[0] === 0) {
    check(a.length === 10 && uint(a[1], 65536) && uint(a[2], 65536) && a[1] + a[2] <= 65536 &&
      uint(a[3], 65536) && uint(a[4], 32) && uint(a[5], 262144) && uint(a[6], 65536) &&
      uint(a[7], 262144) && uint(a[8], 262144) && hex(a[9]));
  } else {
    check(!profile && a[0] === 1 && a.length === 11 && uint(a[1], 5) && uint(a[2], 87));
    check(a.slice(3).every(x => x === null || uint(x)));
  }
  return a;
}
function dependency(v, catalog, catalogHash) {
  const d = record(v, ['version', 'kind', 'qualified', 'linkQualification', 'closureComplete',
    'captureComplete', 'status', 'selfchecks', 'proofs', 'cohort', 'facts', 'critical']);
  complete(d); check(d.version === 1 && d.kind === 'msvc_dependency_observation_v1');
  const p = proofs(d.proofs, OUTER_PROOFS), g = record(d.selfchecks, ['cohort', 'projection', 'observer']);
  gate(g.cohort, 'msvc_profile_cohort_first_v1', 52); gate(g.projection, 'library_metadata_dependency_first_v1', 32);
  gate(g.observer, 'library_metadata_dependency_observer_first_v1', 15);
  const c = record(d.cohort, ['version', 'kind', 'profileId', 'purpose', 'qualified', 'linkQualification',
    'closureComplete', 'captureComplete', 'status', 'selfchecks', 'proofs', 'job', 'io', 'rows', 'strictRefusals', 'profileParsed', 'critical']);
  complete(c); check(c.version === 1 && c.kind === 'msvc_profile_cohort_v1' && c.profileId === V1 && c.purpose === 'build_input_metadata_only');
  gate(c.selfchecks, 'msvc_profile_cohort_first_v1', 52);
  const cp = proofs(c.proofs, COUPLINGS.map(x => x[0])); for (const [inner, outer] of COUPLINGS) check(cp[inner] === p[outer]);
  const j = job(c.job, V1, 32, 64); aggregateIO(c.io, 32, j.inputBytes);
  const cohortRows = array(c.rows, 32, 32), pins = []; let refused = 0;
  for (let i = 0; i < 32; i++) {
    const row = record(cohortRows[i], ['slot', 'strict', 'profile']); check(row.slot === i + 1);
    const strict = encoded(row.strict, false), profile = encoded(row.profile, true);
    if (strict[0] === 1) refused++;
    pins.push({ slot: row.slot, metadataSha256: profile[9], libraryCount: profile[4] });
  }
  check(c.strictRefusals === refused && c.profileParsed === 32);
  const f = record(d.facts, ['version', 'kind', 'profileId', 'purpose', 'qualified', 'linkQualification',
    'closureComplete', 'captureComplete', 'status', 'pinsSha256', 'catalogSha256', 'libraryNames', 'providedSlots',
    'rows', 'unresolvedNameIds', 'allReferencesInProvidedCatalog']);
  falseFlags(f); check(f.version === 1 && f.kind === 'msvc_library_dependency_facts_v1' && f.profileId === V1 &&
    f.purpose === 'build_input_metadata_only' && f.captureComplete === true && f.status === 'metadata_facts_complete' &&
    hex(f.pinsSha256) && f.pinsSha256 === p.pins && f.pinsSha256 === digest(pins) &&
    hex(f.catalogSha256) && f.catalogSha256 === p.catalog && f.catalogSha256 === catalogHash);
  const known = names(f.libraryNames), rows = array(f.rows, 32, 32), used = new Set(); let references = 0;
  for (let i = 0; i < 32; i++) {
    const row = record(rows[i], ['slot', 'libraryIds']); check(row.slot === i + 1);
    const ids = array(row.libraryIds, 32); check(ids.length === pins[i].libraryCount);
    let previous = -1;
    for (const id of ids) { check(uint(id) && id < known.length && id > previous); previous = id; used.add(id); }
    references += ids.length;
  }
  check(used.size === known.length);
  const provided = known.map(name => catalog.get(name) ?? null), unresolved = provided.flatMap((v, i) => v === null ? [i] : []);
  check(same(array(f.providedSlots, 32, known.length), provided) && same(array(f.unresolvedNameIds, 32), unresolved) &&
    f.allReferencesInProvidedCatalog === (unresolved.length === 0));
  return { known, references };
}
function mode(v, profileId) {
  const m = record(v, ['status', 'summary', 'error']);
  if (m.status === 'refused') {
    check(m.summary === null);
    const e = record(m.error, ['kind', 'site', 'context']), context = record(e.context, CONTEXT);
    check(CATEGORIES.includes(e.kind) && typeof e.site === 'string' && e.site.length > 0 && e.site.length <= 64 &&
      /^[a-z]/.test(e.site) && !/[^a-z0-9_]/.test(e.site) && CONTEXT.every(k => context[k] === null || uint(context[k])));
    return { parsed: false, sections: context.sections ?? 0, names: [] };
  }
  check(m.status === 'parsed' && m.error === null);
  const s = record(m.summary, ['profileId', 'objects', 'imports', 'sections', 'deviations', 'metadataSha256', 'defaultLibraries']);
  check(s.profileId === profileId && uint(s.objects, 65536) && uint(s.imports, 65536) && s.objects + s.imports <= 65536 &&
    uint(s.sections, 262144) && hex(s.metadataSha256));
  const ds = [...DEVIATIONS, ...(profileId === V2 ? ['nulArchivePaddingMembers'] : [])], dev = record(s.deviations, ds);
  for (const k of ds) check(uint(dev[k], k === 'unknownMachineObjects' || k === 'nulArchivePaddingMembers' ? 65536 : 262144));
  return { parsed: true, sections: s.sections, names: names(s.defaultLibraries) };
}
function runtime(v) {
  const r = record(v, ['version', 'kind', 'purpose', 'qualified', 'linkQualification', 'closureComplete',
    'captureComplete', 'status', 'proofs', 'job', 'io', 'rows', 'critical']);
  complete(r); check(r.version === 2 && r.kind === 'fixed_two_runtime_metadata_v2' && r.purpose === 'build_input_metadata_only');
  proofs(r.proofs, RUNTIME_PROOFS);
  const j = job(r.job, V2, 2, 4), rows = array(r.rows, 2, 2);
  let bytes = 0, sections = 0, available = true, unsupported = false;
  for (let i = 0; i < 2; i++) {
    const row = record(rows[i], ['slot', 'name', 'rootIndex', 'status', 'pin', 'io', 'strict', 'profile']);
    check(row.slot === 33 + i && row.name === ['ucrt.lib', 'vcruntime.lib'][i] && row.rootIndex === [3, 1][i] && row.status === 'complete');
    const p = record(row.pin, ['bytes', 'sha256', 'rootIdentity', 'leafIdentity']);
    check(uint(p.bytes, [285588, 38478][i]) && p.bytes > 0 && hex(p.sha256) && token(p.rootIdentity) && token(p.leafIdentity));
    const io = record(row.io, ['reservedInputs', 'reservedBytes', 'reservedReadBytes', 'actualReadBytes', 'opened', 'closed', 'verifiedPasses']);
    check(io.reservedInputs === 1 && io.reservedBytes === p.bytes && io.reservedReadBytes === 2 * p.bytes &&
      io.actualReadBytes === 2 * p.bytes && io.opened === true && io.closed === true && io.verifiedPasses === 2);
    const strict = mode(row.strict, 'strict-v1'), profile = mode(row.profile, V2);
    bytes += p.bytes; sections += strict.sections + profile.sections;
    available = available && profile.parsed; unsupported = unsupported || strict.names.length > 0 || profile.names.length > 0;
  }
  check(j.inputBytes === bytes && j.sections === sections); aggregateIO(r.io, 2, bytes);
  return { available, unsupported };
}
function root(v, dependencyRoot, snapshot) {
  check(plain(v) && v.version === 1 && v.kind === (dependencyRoot ?
    'b2_msvc_dependency_observation_root_review_v1' : 'runtime_metadata_v2_root_review_v1'));
  falseFlags(v); check(v.passed === true && v.knownClosed === true && v.noAutomaticRetry === true &&
    hex(v.sourceRevision, 40) && hex(v.process) && hex(v.result) && v.snapshot === snapshot);
  check(dependencyRoot ? v.settled === true && v.approvedPacketSpent === true : v.grantSpent === true);
}

export function createWorkerPrelinkEvidenceV2(anchors) {
  const expected = record(anchors, INPUT, 'WorkerPrelinkEvidenceV2Setup');
  check(INPUT.every(k => hex(expected[k])), 'WorkerPrelinkEvidenceV2Setup');
  // Setup failures have their own closed code; no caller-owned references survive.
  function bind(input) {
    try {
      const supplied = record(input, INPUT), buffers = {};
      for (let i = 0; i < INPUT.length; i++) {
        const k = INPUT[i], b = supplied[k]; check(Buffer.isBuffer(b) && b.length > 0); check(b.length <= CAPS[i], LIMIT);
        buffers[k] = Buffer.from(b); check(hash(buffers[k]) === expected[k]);
      }
      const data = {};
      for (const k of INPUT) {
        const b = buffers[k]; check(!(b.length >= 3 && b[0] === 0xef && b[1] === 0xbb && b[2] === 0xbf));
        data[k] = JSON.parse(new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(b));
      }
      const catalogRows = array(data.catalog, 15, 15), catalog = new Map(), canonical = [];
      for (let i = 0; i < 15; i++) {
        const row = record(catalogRows[i], ['slot', 'name']);
        check(row.slot === 18 + i && canonicalName(row.name) && !catalog.has(row.name) &&
          row.name !== 'ucrt.lib' && row.name !== 'vcruntime.lib');
        catalog.set(row.name, row.slot); canonical.push({ slot: row.slot, name: row.name });
      }
      const historical = dependency(data.dependencySnapshot, catalog, digest(canonical));
      const observed = runtime(data.runtimeSnapshot);
      root(data.dependencyRoot, true, expected.dependencySnapshot); root(data.runtimeRoot, false, expected.runtimeSnapshot);
      catalog.set('ucrt.lib', 33); catalog.set('vcruntime.lib', 34);
      const knownNames = historical.known, providedSlots = knownNames.map(name => catalog.get(name) ?? null);
      const unresolvedNameIds = providedSlots.flatMap((v, i) => v === null ? [i] : []), knownNamesCovered = unresolvedNameIds.length === 0;
      const status = !observed.available ? 'metadata_unavailable' : observed.unsupported ? 'unsupported_runtime_dependencies' :
        knownNamesCovered ? 'metadata_available_known_names_covered' : 'known_names_unresolved';
      const result = { version: 2, kind: 'worker_prelink_evidence_v2', purpose: 'build_input_metadata_only',
        qualified: false, linkQualification: false, closureComplete: false, status, anchors: { ...expected },
        profiles: [{ firstSlot: 1, lastSlot: 32, profileId: V1 }, { firstSlot: 33, lastSlot: 34, profileId: V2 }],
        counts: { historicalInputs: 32, runtimeInputs: 2, historicalReferences: historical.references },
        knownNames, providedSlots, unresolvedNameIds, runtimeMetadataAvailable: observed.available, knownNamesCovered, requiresFreshAdmission: true };
      check(Buffer.byteLength(JSON.stringify(result)) <= 12288, LIMIT); return freeze(result);
    } catch (error) { throw Error(error?.message === LIMIT ? LIMIT : INVALID); }
  }
  return Object.freeze({ bind });
}
