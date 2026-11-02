// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST against D04_MSVC_RUNTIME_RESOLUTION_CONTRACT_2026-11-01.
// SOURCE-ONLY / UNRUN. No producer import, top-level suite execution, filesystem,
// environment, process, SDK lookup/read, network or source evaluation.
// Fake guards exercise the adapter contract; actual directory enumeration,
// case-insensitive .LIB detection and physical paths require source review.
// Tiny buffers only. Two exclusive<256MiB files cannot reach512MiB/1GiB; these
// inherited ceilings are not claimed as dynamically reached by these fixtures.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createLibraryMetadataJob } from './library_inputs.mjs';

const ID = 'msvc-library-metadata-v1', KIND = 'fixed_two_runtime_first_v1';
const NAMES = ['ucrt.lib', 'vcruntime.lib'], PRIOR = ['kernel32.lib', 'msvcprt.lib',
  'msvcrt.lib', 'oldnames.lib', 'ucrt.lib', 'uuid.lib', 'vcomp.lib', 'vcruntime.lib', 'ws2_32.lib'];
const OLD_SLOTS = [18, 28, 29, 30, null, 25, 31, null, 32];
const CATALOG = ['kernel32.lib', 'user32.lib', 'gdi32.lib', 'winspool.lib', 'shell32.lib',
  'ole32.lib', 'oleaut32.lib', 'uuid.lib', 'comdlg32.lib', 'advapi32.lib', 'msvcprt.lib',
  'msvcrt.lib', 'oldnames.lib', 'vcomp.lib', 'ws2_32.lib'];
// Synthetic opaque identities only; production must bind original retained pins.
const ROOTS = ['root-0', 'root-1', 'root-2', 'root-3', 'root-4'];
const PROOF_KEYS = ['reader', 'supervisor', 'helper', 'first', 'roster', 'diagnostic',
  'cohortSnapshot', 'dependencySnapshot', 'dependencyProcess', 'dependencyResult',
  'dependencyReview', 'descriptor', 'codebook', 'priorPins', 'priorCatalog'];
const eq = (a, b) => assert.deepEqual(a, b);
const clone = v => JSON.parse(JSON.stringify(v));
const sha = b => createHash('sha256').update(b).digest('hex');
const digest = v => sha(Buffer.from(JSON.stringify(v)));
const job = () => createLibraryMetadataJob(ID);
const context = () => ({ cwdIdentity: 'cwd-1', cwdLibraryCount: 0, rootIdentities: [...ROOTS] });
function state() {
  return { ready: true, stopped: false, pending: false, nextIndex: 0, searchContext: null,
    probes: [], resolved: [], reservedInputs: 0, reservedBytes: 0,
    reservedReadBytes: 0, actualReadBytes: 0, opened: [] };
}
function deferred() { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; }
function object(machine = 0x8664) { const b = Buffer.alloc(20); b.writeUInt16LE(machine); return b; }
function declared() {
  const b = Buffer.alloc(56); b.writeUInt16LE(0xffff, 2); b.writeUInt16LE(2, 4); b.writeUInt16LE(0x8664, 6);
  Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex').copy(b, 12); b.writeUInt32LE(0xffffffff, 44); return b;
}
function libraryObject(libraries = []) {
  if (!libraries.length) return { buffer: object(), metadata: { objects: 1, imports: 0, directives: [], defaultLibraries: [] }, sections: 0 };
  const tokens = libraries.map(name => '/DEFAULTLIB:' + (name.length > 255 ? name.slice(0, -4) : name)).sort();
  const raw = Buffer.from(tokens.join(' ')), b = Buffer.alloc(60 + raw.length);
  b.writeUInt16LE(0x8664); b.writeUInt16LE(1, 2); b.write('.drectve', 20);
  b.writeUInt32LE(raw.length, 36); b.writeUInt32LE(60, 40); b.writeUInt32LE(0x200, 56); raw.copy(b, 60);
  return { buffer: b, metadata: { objects: 1, imports: 0, directives: tokens, defaultLibraries: [...libraries] }, sections: 1 };
}
function encoded(info, unknown = 0) {
  const m = info.metadata; return [0, m.objects, m.imports, m.directives.length,
    m.defaultLibraries.length, info.sections, unknown, 0, 0, digest(m)];
}
function refusal(api) { return [1, 0, api.codebook.sites.indexOf('coff_header_range'), null, null, null, 0, 0, 0, null, null]; }
async function throws(fn, code) {
  let e; try { await fn(); } catch (error) { e = error; }
  assert(e instanceof Error, 'Expected fixed runtime refusal'); assert.equal(e.message, code); return e;
}
function fake(options = {}) {
  const bytes = options.buffers ?? [object(), object()], found = options.found ?? [[0], [0]], calls = [], reads = [], closes = [0, 0];
  let guards = 0, identifies = 0, stats = 0, readCount = 0;
  const expected = (index, rootIndex) => ({ index, rootIndex, bytes: options.sizes?.[index] ?? bytes[index].length,
    rootIdentity: ROOTS[rootIndex], leafIdentity: 'leaf-' + index });
  const adapter = {
    async guardSearch() {
      calls.push(['guard']); guards++;
      if (options.guardThrow) throw Error('synthetic-guard');
      let c = context(); if (options.guard) c = options.guard(c, guards); return c;
    },
    async probe(index, rootIndex) {
      calls.push(['probe', index, rootIndex]);
      if (options.probeThrow) throw Object.assign(Error('synthetic-probe'), { code: options.probeThrow });
      const value = found[index].includes(rootIndex) ? expected(index, rootIndex) : null;
      return options.probe ? options.probe(value, index, rootIndex) : value;
    },
    async identify(candidate) {
      calls.push(['identify', candidate.index]); identifies++;
      let v = expected(candidate.index, candidate.rootIndex);
      if (options.identity) v = options.identity(v, identifies); return v;
    },
    async open(candidate, mode) {
      calls.push(['open', candidate.index, mode]); assert.equal(mode, 'r');
      if (options.openThrow) throw Error('synthetic-open');
      const index = candidate.index;
      return {
        async stat() {
          calls.push(['stat', index]); stats++;
          let v = { leafIdentity: 'leaf-' + index, bytes: bytes[index].length };
          if (options.stat) v = options.stat(v, stats); return v;
        },
        async read(output, offset, length, position) {
          calls.push(['read', index]); reads.push({ output, offset, length, position }); readCount++;
          assert(length > 0 && length <= 65536 && position >= 0 && position + length <= bytes[index].length);
          if (options.readThrow) throw Error('synthetic-read');
          if (options.zero) return { bytesRead: 0 }; if (options.over) return { bytesRead: length + 1 };
          const n = Math.min(length, options.short ?? length);
          bytes[index].copy(output, offset, position, position + n);
          if (options.corruptSecond && readCount === 2) output[offset] ^= 1;
          return { bytesRead: n };
        },
        async close() { calls.push(['close', index]); closes[index]++; if (options.closeThrow) throw Error('synthetic-close'); }
      };
    }
  };
  return { adapter, bytes, calls, reads, closes, expected };
}
async function acquire(api, options = {}, index = 0) {
  const s = state(), f = fake(options);
  if (index === 1) { assert.equal(await api.resolveFixedLibraryV1(0, s, f.adapter), null); }
  const candidate = await api.resolveFixedLibraryV1(index, s, f.adapter);
  const input = await api.readDiscoveredLibraryV1(candidate, s, f.adapter);
  return { s, f, candidate, input };
}
function row(index, outcome = 'not_reached') {
  return { slot: index + 33, name: NAMES[index], priorNameId: index === 0 ? 4 : 7,
    requestedBySlot: 29, outcome, candidate: null, pin: null, strict: null, profile: null };
}
function report(api, outcomes = ['selected', 'selected'], libraries = [[], []]) {
  const requests = outcomes.map((outcome, index) => {
    const r = row(index, outcome); if (outcome !== 'selected') return r;
    const info = libraryObject(libraries[index]);
    r.candidate = { index, rootIndex: 0, bytes: info.buffer.length, rootIdentity: ROOTS[0], leafIdentity: 'leaf-' + index };
    r.pin = { slot: index + 33, name: NAMES[index], rootIndex: 0, bytes: info.buffer.length,
      sha256: sha(info.buffer), rootIdentity: ROOTS[0], leafIdentity: 'leaf-' + index };
    r.strict = encoded(info); r.profile = encoded(info); return r;
  });
  const selected = requests.filter(r => r.pin), bytes = selected.reduce((n, r) => n + r.pin.bytes, 0);
  const probes = requests.flatMap((r, index) => r.outcome === 'missing'
    ? Array.from({ length: 5 }, (_, rootIndex) => ({ index, rootIndex, outcome: 'missing' }))
    : [{ index, rootIndex: 0, outcome: 'selected' }]);
  const union = [...new Set([...PRIOR, ...requests.flatMap((r, i) => r.profile ? libraries[i] : [])])].sort();
  const slots = union.map(name => {
    const old = CATALOG.indexOf(name), known = old >= 0 ? old + 18 : null;
    const fresh = requests.find(r => r.pin && r.name === name); return known ?? fresh?.slot ?? null;
  });
  return { version: 1, kind: 'fixed_two_runtime_metadata_v1', purpose: 'build_input_metadata_only',
    qualified: false, linkQualification: false, closureComplete: false, captureComplete: true, status: 'complete',
    selfchecks: { version: 1, kind: KIND, executed: 24, passed: 24, failed: 0, failed_case_ids: [] },
    proofs: { ...api.proofs }, search: { context: context(), probes, finalVerified: true },
    job: { profileId: ID, inputCount: selected.length, inputBytes: bytes, attempts: selected.length * 2,
      sections: requests.reduce((n, r) => n + (r.strict?.[5] ?? 0) + (r.profile?.[5] ?? 0), 0), stopped: false },
    io: { reservedInputs: selected.length, reservedBytes: bytes, reservedReadBytes: 2 * bytes, actualReadBytes: 2 * bytes },
    requests, facts: { libraryNames: union, providedSlots: slots, priorNameIds: PRIOR.map(name => union.indexOf(name)),
      rows: requests.map((r, i) => ({ slot: r.slot, libraryIds: r.profile ? libraries[i].map(name => union.indexOf(name)) : null })),
      bothProfileMetadataAvailable: selected.length === 2, allKnownNamesProvided: slots.every(slot => slot !== null) }, critical: null };
}
function stopped(api, critical = 'InputFailure') {
  const r = report(api, ['missing', 'missing']); r.captureComplete = false; r.status = 'stopped'; r.critical = critical;
  r.search = { context: null, probes: [], finalVerified: false }; r.requests = [row(0), row(1)]; r.facts = null; return r;
}
function globalJobStoppedReport(api) {
  // Independently encode the real declared-count global-stop path from the
  // accepted helper: input sections advance, but the refused job charge does not.
  const bytes = declared(), r = stopped(api, 'JobStopped'), selected = report(api).requests[0];
  r.search.context = context(); r.search.probes = [{ index: 0, rootIndex: 0, outcome: 'selected' }];
  r.requests[0] = clone(selected); r.requests[0].candidate.bytes = bytes.length;
  r.requests[0].pin.bytes = bytes.length; r.requests[0].pin.sha256 = sha(bytes);
  r.requests[0].strict = [1, 3, api.codebook.sites.indexOf('metadata_job_sections'),
    null, null, null, 4294967295, 0, 0, 4294967295, 2097152];
  r.requests[0].profile = null;
  r.job = { profileId: ID, inputCount: 1, inputBytes: 56, attempts: 1, sections: 0, stopped: true };
  r.io = { reservedInputs: 1, reservedBytes: 56, reservedReadBytes: 112, actualReadBytes: 112 };
  return r;
}
function acceptedReport(api, r) {
  const text = api.encodeFixedTwoReportV1(r); assert.equal(typeof text, 'string'); assert(text.endsWith('\n') && !text.endsWith('\n\n'));
  eq(JSON.parse(text), r); assert(Buffer.byteLength(text) <= 24576);
  assert.equal(text, JSON.stringify(r) + '\n', 'Whole report must be canonical JSON plus one LF');
  assert(Buffer.byteLength(JSON.stringify({ ...r, facts: null }) + '\n') <= 12288);
  if (r.facts) assert(Buffer.byteLength(JSON.stringify(r.facts) + '\n') <= 12288);
}

export async function runFixedTwoRuntimeSelfchecksV1(api) {
  if (!api || ['resolveFixedLibraryV1', 'readDiscoveredLibraryV1', 'inspectDiscoveredPairV1', 'encodeFixedTwoReportV1'].some(k => typeof api[k] !== 'function') || !api.codebook || !api.proofs) {
    throw Error('UNRUN_SETUP: fixed two runtime API unavailable');
  }
  const cases = [], add = (id, run) => cases.push([id, run]);

  add('R01', async () => {
    for (const [index, change, code] of [[0, s => s.ready = false, 'InputFailure'], [1, () => {}, 'RequestOrder'],
      [2, () => {}, 'RequestOrder'], ['0', () => {}, 'RequestOrder']]) {
      const s = state(), f = fake(); change(s); await throws(() => api.resolveFixedLibraryV1(index, s, f.adapter), code); eq(f.calls, []); assert.equal(s.stopped, true);
    }
  });
  add('R02', async () => {
    const s = state(), f = fake({ found: [[1, 3], []] }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
    eq(c, f.expected(0, 1)); assert(Object.isFrozen(c)); assert(!Object.hasOwn(c, 'sha256'));
    eq(f.calls.filter(x => x[0] === 'probe'), [['probe', 0, 0], ['probe', 0, 1]]);
    eq(s.probes, [{ index: 0, rootIndex: 0, outcome: 'missing' }, { index: 0, rootIndex: 1, outcome: 'selected' }]);
  });
  add('R03', async () => {
    const s = state(), f = fake({ found: [[], []] });
    assert.equal(await api.resolveFixedLibraryV1(0, s, f.adapter), null); assert.equal(await api.resolveFixedLibraryV1(1, s, f.adapter), null);
    eq(s.resolved, [null, null]); assert.equal(s.probes.length, 10); eq(f.calls.filter(x => x[0] === 'probe'), [0, 1].flatMap(i => Array.from({ length: 5 }, (_, r) => ['probe', i, r])));
    assert(!f.calls.some(x => x[0] === 'open')); eq([s.reservedInputs, s.actualReadBytes], [0, 0]);
  });
  add('R04', async () => {
    // Adapter refusals/malformed identities represent unsafe first entries;
    // production filesystem type/reparse checks remain a source-review duty.
    for (const options of [{ probeThrow: 'EACCES' }, { probeThrow: 'ENOENT' },
      { probe: v => v && { ...v, extra: false } }, { probe: v => v && { ...v, bytes: -1 } }]) {
      const s = state(), f = fake({ ...options, found: [[0, 1], []] });
      await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'SearchFailure');
      eq(f.calls.filter(x => x[0] === 'probe'), [['probe', 0, 0]]); assert.equal(s.probes[0].outcome, 'failed'); assert.equal(s.stopped, true);
    }
  });
  add('R05', async () => {
    // One unrelated shadow and multiple shadows both refuse at this seam;
    // casing and whole-directory enumeration are not executed by these fakes.
    for (const count of [1, 2]) {
      const s = state(), f = fake({ guard: c => ({ ...c, cwdLibraryCount: count }) });
      await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'SearchFailure'); assert(!f.calls.some(x => x[0] === 'probe'));
    }
    const s = state(), f = fake({ guardThrow: true }); await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'SearchFailure'); eq(f.calls, [['guard']]);
  });
  add('R06', async () => {
    for (const change of [c => ({ ...c, extra: 1 }), c => ({ ...c, rootIdentities: c.rootIdentities.slice(1) }),
      c => ({ ...c, cwdIdentity: 'bad\nidentity' }), c => ({ ...c, cwdIdentity: '\u00e9' }), c => ({ ...c, cwdIdentity: 'a'.repeat(257) })]) {
      const s = state(), f = fake({ guard: change }); await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'SearchFailure'); assert(!f.calls.some(x => x[0] === 'probe'));
    }
    for (const field of ['root', 'cwd']) {
      const s = state(), f = fake({ found: [[], []], guard: (c, n) => { if (n > 1) { if (field === 'root') c.rootIdentities[0] = 'changed'; else c.cwdIdentity = 'changed'; } return c; } });
      await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'IdentityFailure'); assert.equal(s.probes.length, 5); assert.equal(s.resolved.length, 0);
    }
  });
  add('R07', async () => {
    const s = state(), f = fake({ guardThrow: true }); await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'SearchFailure');
    const before = f.calls.length; s.ready = true; s.stopped = false; s.pending = false; s.nextIndex = 0;
    await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'SearchFailure'); assert.equal(f.calls.length, before);
    const reached = deferred(), release = deferred(), t = state(), g = fake(), original = g.adapter.probe;
    g.adapter.probe = async (...args) => { const v = await original(...args); reached.resolve(); await release.promise; return v; };
    const active = api.resolveFixedLibraryV1(0, t, g.adapter); void active.catch(() => {});
    const didReach = await Promise.race([reached.promise.then(() => true), active.then(() => false, () => false)]); let failure;
    try { if (didReach) { const other = fake(); await throws(() => api.resolveFixedLibraryV1(1, t, other.adapter), 'InputFailure'); eq(other.calls, []); } } catch (e) { failure = e; } finally { release.resolve(); }
    await throws(() => active, 'InputFailure'); assert(didReach); eq(t.probes, [{ index: 0, rootIndex: 0, outcome: 'selected' }]); if (failure) throw failure;
  });
  add('R08', async () => {
    for (const acquired of [false, true]) {
      const s = state(), f = fake(), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
      if (acquired) await api.readDiscoveredLibraryV1(c, s, f.adapter);
      const before = f.calls.length; await throws(() => api.resolveFixedLibraryV1(1, s, f.adapter), 'RequestOrder'); assert.equal(f.calls.length, before);
    }
    const a = await acquire(api, { found: [[0], []] }); const j = job(); const p = api.inspectDiscoveredPairV1(j, a.input.buffer, 33); assert.equal(p.stopped, false);
    assert.equal(await api.resolveFixedLibraryV1(1, a.s, a.f.adapter), null); const before = a.f.calls.length;
    await throws(() => api.resolveFixedLibraryV1(2, a.s, a.f.adapter), 'RequestOrder'); assert.equal(a.f.calls.length, before);
  });

  add('I01', async () => {
    const a = await acquire(api); eq(Object.keys(a.input).sort(), ['buffer', 'pin']); eq(a.input.buffer, a.f.bytes[0]); assert.notEqual(a.input.buffer, a.f.bytes[0]);
    eq(a.input.pin, { slot: 33, name: NAMES[0], rootIndex: 0, bytes: 20, sha256: sha(a.f.bytes[0]), rootIdentity: ROOTS[0], leafIdentity: 'leaf-0' });
    assert(Object.isFrozen(a.input.pin)); eq([a.s.reservedInputs, a.s.reservedBytes, a.s.reservedReadBytes, a.s.actualReadBytes], [1, 20, 40, 40]); assert.equal(a.s.opened.length, 1); assert.equal(a.f.closes[0], 1);
  });
  add('I02', async () => {
    const short = await acquire(api, { short: 3 }); assert(short.f.reads.length > 2); assert.equal(short.s.actualReadBytes, 40);
    const a = await acquire(api, { buffers: [Buffer.alloc(65537, 1), object()] });
    assert.equal(a.s.actualReadBytes, 131074); assert(a.f.reads.length >= 4); assert(a.f.reads.every(r => r.length <= 65536));
    assert.equal(a.f.reads.filter(r => r.position === 0).length, 2); assert(a.f.reads.some(r => r.position === 0 && r.output !== a.f.reads[0].output));
  });
  add('I03', async () => {
    const s = state(), f = fake({ corruptSecond: true }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
    await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'IdentityFailure'); assert.equal(f.closes[0], 1); assert.equal(s.opened.length, 0); assert.equal(s.actualReadBytes, 40);
  });
  add('I04', async () => {
    for (const change of [v => ({ ...v, rootIdentity: 'changed' }), v => ({ ...v, leafIdentity: 'changed' }), v => ({ ...v, bytes: v.bytes + 1 })]) {
      const s = state(), f = fake({ identity: (v, n) => n > 1 ? change(v) : v }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
      await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'IdentityFailure'); assert.equal(f.closes[0], 1);
    }
    for (const at of [1, 2, 3]) {
      const s = state(), f = fake({ stat: (v, n) => n === at ? { ...v, leafIdentity: 'changed' } : v }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
      await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'IdentityFailure'); assert.equal(f.closes[0], 1);
    }
    for (const change of [v => ({ ...v, rootIdentity: 'changed' }), v => ({ ...v, leafIdentity: 'changed' }), v => ({ ...v, bytes: v.bytes + 1 })]) {
      const s = state(), f = fake({ identity: (v, n) => n === 1 ? change(v) : v }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
      await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'IdentityFailure');
      assert(!f.calls.some(call => call[0] === 'open')); assert.equal(f.closes[0], 0);
      eq([s.reservedInputs, s.reservedBytes, s.reservedReadBytes, s.actualReadBytes, s.opened.length], [1, 20, 40, 0, 0]);
    }
    const s = state(), f = fake({ stat: (v, n) => n === 1 ? { ...v, bytes: v.bytes + 1 } : v }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
    await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'IdentityFailure');
    assert(!f.calls.some(call => call[0] === 'read')); assert.equal(f.closes[0], 1); assert.equal(s.actualReadBytes, 0); assert.equal(s.opened.length, 0);
  });
  add('I05', async () => {
    for (const option of ['zero', 'over', 'readThrow']) {
      const s = state(), f = fake({ [option]: true }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
      await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'InputFailure'); assert.equal(f.closes[0], 1); assert.equal(s.actualReadBytes, 0);
    }
    const s = state(), f = fake(), c = await api.resolveFixedLibraryV1(0, s, f.adapter), reached = deferred(), release = deferred(), open = f.adapter.open;
    f.adapter.open = async (...args) => { const h = await open(...args), read = h.read; h.read = async (...q) => { const r = await read(...q); reached.resolve(); await release.promise; return r; }; return h; };
    const active = api.readDiscoveredLibraryV1(c, s, f.adapter); void active.catch(() => {});
    const didReach = await Promise.race([reached.promise.then(() => true), active.then(() => false, () => false)]); let failure;
    try { if (didReach) { const other = fake(); await throws(() => api.readDiscoveredLibraryV1(c, s, other.adapter), 'InputFailure'); eq(other.calls, []); } } catch (e) { failure = e; } finally { release.resolve(); }
    await throws(() => active, 'InputFailure'); assert(didReach); assert.equal(s.actualReadBytes, 20); assert.equal(f.closes[0], 1); if (failure) throw failure;
    const failedState = state(), failedAdapter = fake({ openThrow: true }), candidate = await api.resolveFixedLibraryV1(0, failedState, failedAdapter.adapter);
    await throws(() => api.readDiscoveredLibraryV1(candidate, failedState, failedAdapter.adapter), 'InputFailure');
    eq([failedState.reservedInputs, failedState.reservedBytes, failedState.reservedReadBytes, failedState.actualReadBytes], [1, 20, 40, 0]);
    assert.equal(failedAdapter.closes[0], 0); assert.equal(failedState.opened.length, 0); assert.equal(failedState.stopped, true);
    failedState.ready = true; failedState.stopped = false; failedState.pending = false;
    const untouched = fake();
    await throws(() => api.resolveFixedLibraryV1(1, failedState, untouched.adapter), 'InputFailure'); eq(untouched.calls, []);
    await throws(() => api.readDiscoveredLibraryV1(candidate, failedState, untouched.adapter), 'InputFailure'); eq(untouched.calls, []);
  });
  add('I06', async () => {
    for (const identity of [false, true]) {
      const s = state(), f = fake({ closeThrow: true, ...(identity ? { stat: (v, n) => n > 1 ? { ...v, leafIdentity: 'changed' } : v } : {}) }), c = await api.resolveFixedLibraryV1(0, s, f.adapter);
      await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), identity ? 'IdentityFailure' : 'InputFailure'); assert.equal(f.closes[0], 1); assert.equal(s.stopped, true); assert.equal(s.opened.length, 0);
    }
  });
  add('I07', async () => {
    // No fictitious prior job/reservation and no huge allocation. These are
    // pre-open exclusive-size limits and invalid fresh-counter controls.
    for (const bytes of [0, 268435456]) {
      const s = state(), f = fake({ sizes: [bytes, 20] }), c = await api.resolveFixedLibraryV1(0, s, f.adapter), before = f.calls.length;
      await throws(() => api.readDiscoveredLibraryV1(c, s, f.adapter), 'InputLimit'); assert.equal(f.calls.length, before); eq([s.reservedInputs, s.reservedBytes, s.actualReadBytes], [0, 0, 0]);
    }
    for (const change of [s => s.reservedInputs = 1, s => { s.reservedBytes = 1; s.reservedReadBytes = 2; }, s => s.actualReadBytes = 1]) {
      const s = state(), f = fake(); change(s); await throws(() => api.resolveFixedLibraryV1(0, s, f.adapter), 'InputFailure'); eq(f.calls, []);
    }
    const a = await acquire(api); eq([a.s.reservedInputs, a.s.reservedBytes, a.s.reservedReadBytes, a.s.actualReadBytes], [1, 20, 40, 40]);
  });
  add('I08', async () => {
    const s = state(), f = fake(), c = await api.resolveFixedLibraryV1(0, s, f.adapter), before = f.calls.length;
    await throws(() => api.readDiscoveredLibraryV1({ ...c }, s, f.adapter), 'RequestOrder'); assert.equal(f.calls.length, before);
    const a = await acquire(api), count = a.f.calls.length;
    await throws(() => api.readDiscoveredLibraryV1(a.candidate, a.s, a.f.adapter), 'RequestOrder'); assert.equal(a.f.calls.length, count);
    const left = state(), right = state(), g = fake(), owned = await api.resolveFixedLibraryV1(0, left, g.adapter), untouched = fake();
    await throws(() => api.readDiscoveredLibraryV1(owned, right, untouched.adapter), 'RequestOrder'); eq(untouched.calls, []);
    const b = await acquire(api), j = job(); assert.equal(api.inspectDiscoveredPairV1(j, b.input.buffer, 33).stopped, false);
    const next = await api.resolveFixedLibraryV1(1, b.s, b.f.adapter), second = await api.readDiscoveredLibraryV1(next, b.s, b.f.adapter);
    assert.notEqual(second.buffer, b.input.buffer); eq(second.buffer, b.input.buffer); assert.equal(api.inspectDiscoveredPairV1(j, second.buffer, 34).stopped, false);
    eq([j.snapshot().inputCount, j.snapshot().attempts, b.s.reservedInputs, b.s.actualReadBytes], [2, 4, 2, 80]);
  });

  add('P01', async () => {
    const a = await acquire(api), actual = job(), calls = [], j = { inspect(buffer, mode) { calls.push([buffer, mode]); return actual.inspect(buffer, mode); }, snapshot: () => actual.snapshot() };
    const r = api.inspectDiscoveredPairV1(j, a.input.buffer, 33), info = libraryObject();
    eq(Object.keys(r).sort(), ['critical', 'profileResult', 'row', 'stopped']); eq(r.row, { slot: 33, strict: encoded(info), profile: encoded(info) });
    assert.equal(r.stopped, false); assert.equal(r.critical, null); eq(r.profileResult.metadata, info.metadata); assert.equal(r.profileResult.profileId, ID); eq([j.snapshot().inputCount, j.snapshot().attempts], [1, 2]);
    eq(calls.map(c => c[1]), ['strict-v1', ID]); assert(calls.every(c => c[0] === a.input.buffer));
    const b = await acquire(api, { found: [[], [0]] }, 1); const second = api.inspectDiscoveredPairV1(job(), b.input.buffer, 34); assert.equal(second.row.slot, 34); assert.equal(second.stopped, false);
  });
  add('P02', async () => {
    const a = await acquire(api, { buffers: [object(0), object()] }), j = job(), r = api.inspectDiscoveredPairV1(j, a.input.buffer, 33);
    assert.equal(r.row.strict[0], 1); assert.equal(r.row.profile[0], 0); assert.equal(r.row.profile[6], 1); assert.equal(r.stopped, false);
    const b = await acquire(api, { buffers: [Buffer.alloc(1), object()], found: [[0], []] }), k = job(), refusalPair = api.inspectDiscoveredPairV1(k, b.input.buffer, 33);
    eq([refusalPair.row.strict[0], refusalPair.row.profile[0], refusalPair.profileResult, refusalPair.stopped], [1, 1, null, false]); assert.equal(k.snapshot().attempts, 2);
    assert.equal(await api.resolveFixedLibraryV1(1, b.s, b.f.adapter), null);
    const info = libraryObject(['unresolved-new.lib']), c = await acquire(api, { buffers: [info.buffer, object()] }), count = c.f.calls.length;
    const named = api.inspectDiscoveredPairV1(job(), c.input.buffer, 33); eq(named.profileResult.metadata.defaultLibraries, ['unresolved-new.lib']); assert.equal(c.f.calls.length, count);
  });
  add('P03', async () => {
    const a = await acquire(api, { buffers: [declared(), object()] }), j = job(), r = api.inspectDiscoveredPairV1(j, a.input.buffer, 33);
    eq([r.stopped, r.critical, r.row.strict[0], r.row.profile, r.profileResult], [true, 'JobStopped', 1, null, null]); eq([j.snapshot().attempts, j.snapshot().sections, j.snapshot().stopped], [1, 0, true]);
    const before = a.f.calls.length; await throws(() => api.resolveFixedLibraryV1(1, a.s, a.f.adapter), 'JobStopped'); assert.equal(a.f.calls.length, before);
    for (const type of ['throw', 'result', 'snapshot']) {
      const b = await acquire(api), real = job(); let calls = 0;
      const fakeJob = { inspect(buffer, mode) { calls++; const value = real.inspect(buffer, mode); if (type === 'throw') throw Error('private-error'); return type === 'result' ? { bad: true } : value; }, snapshot() { return type === 'snapshot' ? { stopped: false } : real.snapshot(); } };
      const unknown = api.inspectDiscoveredPairV1(fakeJob, b.input.buffer, 33); eq([unknown.stopped, unknown.critical, unknown.profileResult, calls], [true, 'UnknownInspection', null, 1]);
      const n = b.f.calls.length; await throws(() => api.resolveFixedLibraryV1(1, b.s, b.f.adapter), 'UnknownInspection'); assert.equal(b.f.calls.length, n);
    }
  });
  add('P04', async () => {
    const a = await acquire(api), j = job(); api.inspectDiscoveredPairV1(j, a.input.buffer, 33);
    const repeat = api.inspectDiscoveredPairV1(j, a.input.buffer, 33); eq([repeat.stopped, repeat.critical], [true, 'RequestOrder']); assert.equal(j.snapshot().attempts, 2);
    for (const replacement of [false, true]) {
      const b = await acquire(api), first = job(); api.inspectDiscoveredPairV1(first, b.input.buffer, 33);
      const c = await api.resolveFixedLibraryV1(1, b.s, b.f.adapter), input = await api.readDiscoveredLibraryV1(c, b.s, b.f.adapter);
      const other = replacement ? job() : first, r = api.inspectDiscoveredPairV1(other, input.buffer, replacement ? 34 : 33);
      eq([r.stopped, r.critical], [true, 'RequestOrder']); assert.equal(first.snapshot().attempts, 2); if (replacement) assert.equal(other.snapshot().attempts, 0);
    }
    const b = await acquire(api), actual = job(), mutator = { inspect(buffer, mode) { const value = actual.inspect(buffer, mode); if (mode === ID) buffer[4] ^= 1; return value; }, snapshot: () => actual.snapshot() };
    const changed = api.inspectDiscoveredPairV1(mutator, b.input.buffer, 33); eq([changed.stopped, changed.critical, changed.profileResult], [true, 'BufferMutation', null]); assert.equal(actual.snapshot().attempts, 2);
    const c = await acquire(api), real = job(); let reentry;
    const nested = { inspect(buffer, mode) { const value = real.inspect(buffer, mode); if (mode === 'strict-v1') { reentry = api.resolveFixedLibraryV1(1, c.s, c.f.adapter); void reentry.catch(() => {}); } return value; }, snapshot: () => real.snapshot() };
    const before = c.f.calls.length, interrupted = api.inspectDiscoveredPairV1(nested, c.input.buffer, 33);
    await throws(() => reentry, 'RequestOrder'); eq([interrupted.stopped, interrupted.critical, interrupted.row.strict[0], interrupted.row.profile], [true, 'RequestOrder', 0, null]); assert.equal(real.snapshot().attempts, 1); assert.equal(c.f.calls.length, before);
    const orphanJob = job(); let orphanInspectCalls = 0, orphanSnapshotCalls = 0;
    const orphanSpy = {
      inspect(buffer, mode) { orphanInspectCalls++; return orphanJob.inspect(buffer, mode); },
      snapshot() { orphanSnapshotCalls++; return orphanJob.snapshot(); }
    };
    const orphan = api.inspectDiscoveredPairV1(orphanSpy, object(), 33);
    eq([orphan.stopped, orphan.critical, orphan.profileResult, orphan.row.strict, orphan.row.profile], [true, 'RequestOrder', null, null, null]);
    eq([orphanInspectCalls, orphanSnapshotCalls], [0, 0]);
    const orphanSnapshot = orphanJob.snapshot(); eq([orphanSnapshot.inputCount, orphanSnapshot.attempts], [0, 0]);
  });

  add('S01', () => {
    eq(Object.keys(api.proofs).sort(), [...PROOF_KEYS].sort()); assert(Object.values(api.proofs).every(v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v)));
    assert.equal(api.proofs.helper, '9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53'); assert.equal(api.proofs.dependencySnapshot, '47b15b415307185f21eb0c06842c26cfc9021f8cb2454830b474b32a203e5391');
    const r = report(api); acceptedReport(api, r); eq([r.job.inputCount, r.job.attempts, r.io.actualReadBytes], [2, 4, 80]);
    for (const flag of ['qualified', 'linkQualification', 'closureComplete']) { const bad = clone(r); bad[flag] = true; assert.throws(() => api.encodeFixedTwoReportV1(bad), { message: 'ReportFailure' }); }
  });
  add('S02', () => {
    acceptedReport(api, report(api, ['missing', 'missing'])); acceptedReport(api, report(api, ['missing', 'selected']));
    const pre = stopped(api, 'SearchFailure'); pre.requests[0].outcome = 'incomplete'; acceptedReport(api, pre);
    const postMissing = stopped(api, 'IdentityFailure'); postMissing.search.context = context(); postMissing.search.probes = Array.from({ length: 5 }, (_, rootIndex) => ({ index: 0, rootIndex, outcome: 'missing' })); postMissing.requests[0].outcome = 'incomplete'; acceptedReport(api, postMissing);
    const late = stopped(api); late.search.context = context(); late.search.probes = [{ index: 0, rootIndex: 0, outcome: 'selected' }]; late.requests[0].outcome = 'incomplete'; acceptedReport(api, late);
    const unread = stopped(api, 'InputLimit'); unread.search.context = context(); unread.search.probes = [{ index: 0, rootIndex: 0, outcome: 'selected' }]; unread.requests[0].outcome = 'selected'; unread.requests[0].candidate = { index: 0, rootIndex: 0, bytes: 268435456, rootIdentity: ROOTS[0], leafIdentity: 'leaf-0' }; acceptedReport(api, unread);
    const partial = stopped(api); partial.search.context = context(); partial.search.probes = [{ index: 0, rootIndex: 0, outcome: 'selected' }]; partial.requests[0] = row(0, 'selected'); partial.requests[0].candidate = { index: 0, rootIndex: 0, bytes: 20, rootIdentity: ROOTS[0], leafIdentity: 'leaf-0' }; partial.io = { reservedInputs: 1, reservedBytes: 20, reservedReadBytes: 40, actualReadBytes: 10 }; acceptedReport(api, partial);
    const prefix = stopped(api, 'RequestOrder'), full = report(api); prefix.search.context = context(); prefix.search.probes = [{ index: 0, rootIndex: 0, outcome: 'selected' }]; prefix.requests[0] = clone(full.requests[0]); prefix.requests[0].profile = null; prefix.job = { profileId: ID, inputCount: 1, inputBytes: 20, attempts: 1, sections: 0, stopped: false }; prefix.io = { reservedInputs: 1, reservedBytes: 20, reservedReadBytes: 40, actualReadBytes: 40 }; acceptedReport(api, prefix);
    const unknown = clone(prefix); unknown.critical = 'UnknownInspection'; unknown.requests[0].strict = null; acceptedReport(api, unknown);
    const unknownProfile = clone(prefix); unknownProfile.critical = 'UnknownInspection'; unknownProfile.job.attempts = 2; acceptedReport(api, unknownProfile);
    const globalStop = globalJobStoppedReport(api); acceptedReport(api, globalStop);
    eq([globalStop.requests[0].candidate.bytes, globalStop.requests[0].strict[6], globalStop.job.sections, globalStop.job.attempts], [56, 4294967295, 0, 1]);
  });
  add('S03', () => {
    for (const change of [r => r.extra = 1, r => r.selfchecks.passed = 23, r => r.proofs.roster = '0'.repeat(64),
      r => r.search.context.rootIdentities[0] = 'changed', r => r.search.probes.push({ index: 0, rootIndex: 1, outcome: 'missing' }),
      r => r.job.attempts = 3, r => r.job.sections = 1, r => r.io.actualReadBytes--,
      r => r.requests[1].slot = 33, r => r.requests[0].pin.sha256 = 'bad', r => r.requests[0].profile[9] = 'A'.repeat(64),
      r => delete r.requests[1], r => delete r.facts.providedSlots[4], r => r.job.attempts = true]) {
      const r = report(api); change(r); assert.throws(() => api.encodeFixedTwoReportV1(r), { message: 'ReportFailure' });
    }
    const phantom = stopped(api); phantom.job.inputCount = 1; phantom.job.inputBytes = 20; phantom.job.attempts = 4; assert.throws(() => api.encodeFixedTwoReportV1(phantom), { message: 'ReportFailure' });
    const badStop = stopped(api, 'JobStopped'); assert.throws(() => api.encodeFixedTwoReportV1(badStop), { message: 'ReportFailure' });
    const nullable = report(api, ['missing', 'missing']); delete nullable.facts.providedSlots[4]; assert.throws(() => api.encodeFixedTwoReportV1(nullable), { message: 'ReportFailure' });
    const strictPrefix = stopped(api, 'RequestOrder'), full = report(api);
    strictPrefix.search.context = context(); strictPrefix.search.probes = [{ index: 0, rootIndex: 0, outcome: 'selected' }];
    strictPrefix.requests[0] = clone(full.requests[0]); strictPrefix.requests[0].profile = null;
    strictPrefix.job = { profileId: ID, inputCount: 1, inputBytes: 20, attempts: 1, sections: 0, stopped: false };
    strictPrefix.io = { reservedInputs: 1, reservedBytes: 20, reservedReadBytes: 40, actualReadBytes: 40 };
    const outsidePair = clone(strictPrefix); outsidePair.critical = 'InputFailure';
    assert.throws(() => api.encodeFixedTwoReportV1(outsidePair), { message: 'ReportFailure' });
    const unknownStrict = clone(strictPrefix); unknownStrict.critical = 'UnknownInspection'; unknownStrict.requests[0].strict = null; unknownStrict.job.attempts = 2;
    assert.throws(() => api.encodeFixedTwoReportV1(unknownStrict), { message: 'ReportFailure' });
    const unknownProfile = clone(strictPrefix); unknownProfile.critical = 'UnknownInspection';
    assert.throws(() => api.encodeFixedTwoReportV1(unknownProfile), { message: 'ReportFailure' });
    for (const change of [r => r.job.stopped = true, r => r.job.sections = 1]) {
      const zeroAttempt = stopped(api); change(zeroAttempt); assert.throws(() => api.encodeFixedTwoReportV1(zeroAttempt), { message: 'ReportFailure' });
    }
    for (const change of [r => r.job.stopped = false, r => r.critical = 'InputFailure',
      r => r.requests[0].strict[1] = 0, r => r.requests[0].strict[2] = api.codebook.sites.indexOf('coff_header_range'),
      r => r.requests[0].strict[9] = 2097152, r => r.requests[0].strict[10] = 65536]) {
      const invalidStop = globalJobStoppedReport(api); change(invalidStop); assert.throws(() => api.encodeFixedTwoReportV1(invalidStop), { message: 'ReportFailure' });
    }
  });
  add('S04', () => {
    const r = report(api); eq(r.facts.priorNameIds, Array.from({ length: 9 }, (_, i) => i)); assert.equal(r.facts.allKnownNamesProvided, true); assert.equal(r.facts.bothProfileMetadataAvailable, true);
    const unavailable = report(api); for (const request of unavailable.requests) { request.candidate.bytes = 1; request.pin.bytes = 1; request.pin.sha256 = sha(Buffer.alloc(1)); request.strict = refusal(api); request.profile = refusal(api); }
    unavailable.job.inputBytes = 2; unavailable.io = { reservedInputs: 2, reservedBytes: 2, reservedReadBytes: 4, actualReadBytes: 4 }; unavailable.facts.rows.forEach(row => row.libraryIds = null); unavailable.facts.bothProfileMetadataAvailable = false; acceptedReport(api, unavailable); assert.equal(unavailable.facts.allKnownNamesProvided, true);
    const missing = report(api, ['missing', 'missing']); eq(missing.facts.providedSlots, OLD_SLOTS); assert.equal(missing.facts.bothProfileMetadataAvailable, false); assert.equal(missing.facts.allKnownNamesProvided, false);
    const known = report(api, ['selected', 'selected'], [['user32.lib'], []]); acceptedReport(api, known); assert.equal(known.facts.providedSlots[known.facts.libraryNames.indexOf('user32.lib')], 19);
    const long = n => Array.from({ length: n }, (_, i) => String(i).padStart(2, '0') + '-' + 'a'.repeat(252) + '.lib');
    const full = report(api, ['selected', 'selected'], [long(23), []]); assert.equal(full.facts.libraryNames.length, 32); acceptedReport(api, full);
    const over = report(api, ['selected', 'selected'], [long(24), []]); assert.equal(over.facts.libraryNames.length, 33); assert.throws(() => api.encodeFixedTwoReportV1(over), { message: 'ReportLimit' });
    const rowMaximum = report(api, ['selected', 'selected'], [[...PRIOR, ...long(23)].sort(), []]);
    eq([rowMaximum.requests[0].profile[4], rowMaximum.facts.rows[0].libraryIds.length, rowMaximum.facts.libraryNames.length], [32, 32, 32]); acceptedReport(api, rowMaximum);
    const tooLong = report(api, ['selected', 'selected'], [['a'.repeat(256) + '.lib'], []]);
    assert.equal(tooLong.facts.libraryNames.find(name => name.length > 259).length, 260);
    assert.throws(() => api.encodeFixedTwoReportV1(tooLong), { message: 'ReportLimit' });
    // A 33-name row also exceeds the exact-union limit; do not claim isolated bounds.
    const rowOver = report(api, ['selected', 'selected'], [[...PRIOR, ...long(24)].sort(), []]);
    assert.equal(rowOver.requests[0].profile[4], 33); assert.throws(() => api.encodeFixedTwoReportV1(rowOver), { message: 'ReportLimit' });
    for (const change of [x => x.facts.priorNameIds[0] = 1, x => x.facts.providedSlots[4] = null,
      x => x.facts.rows[0].libraryIds = null, x => x.facts.allKnownNamesProvided = false,
      x => x.facts.libraryNames[0] = '../unsafe.lib', x => x.facts.libraryNames.push('unused.lib')]) {
      const bad = report(api); change(bad); assert.throws(() => api.encodeFixedTwoReportV1(bad), { message: 'ReportFailure' });
    }
    const padding = report(api); padding.facts.libraryNames.push('zz-unused.lib'); padding.facts.providedSlots.push(null); padding.facts.allKnownNamesProvided = false;
    assert.throws(() => api.encodeFixedTwoReportV1(padding), { message: 'ReportFailure' });
  });

  const expected = [['R', 8], ['I', 8], ['P', 4], ['S', 4]].flatMap(([prefix, n]) => Array.from({ length: n }, (_, i) => prefix + String(i + 1).padStart(2, '0')));
  assert.deepEqual(cases.map(([id]) => id), expected, 'Frozen runtime FIRST roster');
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: KIND, executed: cases.length, passed: cases.length - failed_case_ids.length,
    failed: failed_case_ids.length, failed_case_ids };
}
