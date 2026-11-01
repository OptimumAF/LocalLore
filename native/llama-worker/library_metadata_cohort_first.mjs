// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST, source-only/UNRUN. No top-level execution, filesystem,
// process, console, SDK adapter, source evaluation or input qualification.
// Only runFixedProfileCohortSelfchecksV1 is exported. Fake reads below exercise
// the actual private held-input function; pairing uses the accepted real job.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createLibraryMetadataJob, MSVC_LIBRARY_METADATA_PROFILE } from './library_inputs.mjs';

const ID = 'msvc-library-metadata-v1', KIND = 'msvc_profile_cohort_first_v1';
const CONTEXT = ['memberIndex', 'memberOffset', 'sectionIndex', 'sections', 'directiveBytes', 'tokenCount', 'actual', 'limit'];
const KINDS = ['Format', 'Unsafe', 'Directive', 'Size', 'Type', 'Profile'].map(s => 'LibraryInputs' + s);
const H = 'a'.repeat(64), INPUT = 359493030, READ = 718986060;
const sha = b => createHash('sha256').update(b).digest('hex');
const digest = v => sha(Buffer.from(JSON.stringify(v)));
const clone = v => JSON.parse(JSON.stringify(v));
const eq = (a, b) => assert.deepEqual(a, b);
const job = () => createLibraryMetadataJob(ID);
function object(machine = 0x8664) { const b = Buffer.alloc(20); b.writeUInt16LE(machine); return b; }
function directive(text) {
  const p = Buffer.from(text), b = Buffer.alloc(60 + p.length);
  b.writeUInt16LE(0x8664); b.writeUInt16LE(1, 2); b.write('.drectve', 20);
  b.writeUInt32LE(p.length, 36); b.writeUInt32LE(60, 40); b.writeUInt32LE(0x200, 56); p.copy(b, 60); return b;
}
function declared(count) {
  const b = Buffer.alloc(56); b.writeUInt16LE(0xffff, 2); b.writeUInt16LE(2, 4); b.writeUInt16LE(0x8664, 6);
  Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex').copy(b, 12); b.writeUInt32LE(count, 44); return b;
}
function baseline(b, slot = 1) {
  // Independent fixture expectations; never call the proposed pair to derive them.
  const directives = b.length > 20 ? ['/DEFAULTLIB:alpha'] : [];
  return { slot, objects: 1, imports: 0, directiveUniqueCount: directives.length,
    directiveArraySha256: digest(directives), defaultLibraries: directives.length ? ['alpha.lib'] : [] };
}
const refusal = (error = 'LibraryInputsFormat', extra = {}) => ({ slot: 1, error, ...extra });
const emptyContext = () => Object.fromEntries(CONTEXT.map(k => [k, null]));
function state(overrides = {}) {
  return { ready: true, stopped: false, pending: false, reservedInputs: 0, reservedBytes: 0,
    reservedReadBytes: 0, actualReadBytes: 0, opened: [], ...overrides };
}
function fixture(options = {}) {
  const bytes = options.bytes ?? object(), pin = { slot: 1, alias: 'synthetic', path: 'D:/synthetic/input.obj',
    bytes: bytes.length, sha256: sha(bytes) }, calls = [], requests = [], stats = { closes: 0 };
  const identity = { path: pin.path, root: 'root-1', leaf: 'leaf-1', bytes: bytes.length };
  let identifyCount = 0, statCount = 0, readCount = 0;
  const adapter = {
    async identify(p) {
      calls.push('identify'); assert.equal(p, pin); identifyCount++;
      if (options.identifyThrow) throw Error('synthetic');
      return { ...identity, ...(options.identifyChange && identifyCount > 1 ? options.identifyChange : {}) };
    },
    async open(p, mode) {
      calls.push('open'); assert.equal(p, pin); assert.equal(mode, 'r');
      if (options.openThrow) throw Error('synthetic');
      return {
        async stat() {
          calls.push('stat'); statCount++;
          return { leaf: identity.leaf, bytes: identity.bytes, ...(options.statChange && statCount >= (options.statAt ?? 2) ? options.statChange : {}) };
        },
        async read(target, offset, length, position) {
          calls.push('read'); readCount++; requests.push({ target, offset, length, position });
          assert(length > 0 && length <= 65536); assert(position >= 0 && position + length <= bytes.length);
          if (options.block) await options.block;
          if (options.readThrow) throw Error('synthetic');
          if (options.zero) return { bytesRead: 0 };
          if (options.over) return { bytesRead: length + 1 };
          const n = Math.min(length, options.short ?? length);
          bytes.copy(target, offset, position, position + n);
          if (options.corrupt && readCount === 1 || options.secondCorrupt && readCount === 2) target[offset] ^= 1;
          return { bytesRead: n };
        },
        async close() { calls.push('close'); stats.closes++; if (options.closeThrow) throw Error('synthetic'); }
      };
    }
  };
  return { pin, adapter, calls, requests, stats, bytes, identity };
}
async function rejected(fn) { let error; try { await fn(); } catch (e) { error = e; } assert(error instanceof Error, 'Expected finite refusal'); return error; }
function parsed(api, sections = 0) { return [0, 1, 0, 0, 0, sections, 0, 0, 0, digest({ objects: 1, imports: 0, directives: [], defaultLibraries: [] })]; }
function refused(api, kind = 0, site = 'coff_machine') { return [1, kind, api.codebook.sites.indexOf(site), ...CONTEXT.map(() => null)]; }
function report(api, complete = true) {
  const pins = api.validateFixedRoster(api.fixtureRoster()), rows = complete ? pins.map((p, i) => ({ slot: i + 1,
    strict: i === 3 || i === 4 || i === 10 || i === 11 ? refused(api, 3, 'coff_sections_total') : i >= 17 ? refused(api) : parsed(api),
    profile: parsed(api) })) : [{ slot: 1, strict: parsed(api), profile: null }];
  return { version: 1, kind: 'msvc_profile_cohort_v1', profileId: ID, purpose: 'build_input_metadata_only',
    qualified: false, linkQualification: false, closureComplete: false, captureComplete: complete,
    status: complete ? 'complete' : 'stopped', selfchecks: { version: 1, kind: KIND, executed: 52, passed: 52, failed: 0, failed_case_ids: [] },
    proofs: { reader: H, helper: api.codebook.helperSha256, first: H, supervisor: H,
      roster: '62eb0ab9ff6296b13d4a8cebd49a69ffe95444f75da6ac29971c4cf7729a6dbc',
      descriptor: digest(MSVC_LIBRARY_METADATA_PROFILE), codebook: api.codebook.sha256 },
    job: { profileId: ID, inputCount: complete ? 32 : 1, inputBytes: complete ? INPUT : pins[0].bytes,
      attempts: complete ? 64 : 1, sections: 0, stopped: false },
    io: { reservedInputs: complete ? 32 : 1, reservedBytes: complete ? INPUT : pins[0].bytes,
      reservedReadBytes: complete ? READ : 2 * pins[0].bytes, actualReadBytes: complete ? READ : 2 * pins[0].bytes },
    rows, strictRefusals: complete ? 19 : 0, profileParsed: complete ? 32 : 0, critical: complete ? null : 'BaselineMismatch' };
}

export async function runFixedProfileCohortSelfchecksV1(api) {
  if (!api || ['inspectPair', 'readPinnedInput', 'validateFixedRoster', 'encodeReport', 'fixtureRoster'].some(k => typeof api[k] !== 'function') || !api.codebook) {
    throw Error('UNRUN_SETUP: fixed cohort API unavailable');
  }
  const cases = [], add = (id, run) => cases.push([id, run]);
  const roster = () => api.fixtureRoster(), validated = () => api.validateFixedRoster(roster());
  const pair = (j, b, base = baseline(b)) => api.inspectPair(j, b, base);
  const noCalls = async (s, f = fixture()) => { await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); eq(f.calls, []); assert.equal(s.stopped, true); };
  const badRoster = async mutate => { const r = roster(); mutate(r); await rejected(() => api.validateFixedRoster(r)); };

  add('R01', () => { const rows = validated(); assert.equal(rows.length, 32); eq(rows.map(r => r.slot), Array.from({ length: 32 }, (_, i) => i + 1)); assert.equal(rows.reduce((n, r) => n + r.bytes, 0), INPUT); assert.equal(Math.max(...rows.map(r => r.bytes)), 92584312); });
  add('R02', () => { const a = roster(), b = roster(); a.fixedInputs[0].alias = 'changed'; assert.equal(b.fixedInputs[0].alias, 'main-first'); assert.notEqual(a.fixedInputs, b.fixedInputs); });
  add('R03', () => badRoster(r => r.fixedInputs.pop()));
  add('R04', () => badRoster(r => r.sdkInputs.push(clone(r.sdkInputs[0]))));
  add('R05', () => badRoster(r => [r.fixedInputs[0], r.fixedInputs[1]] = [r.fixedInputs[1], r.fixedInputs[0]]));
  add('R06', () => badRoster(r => r.fixedInputs[0].alias = 'main-b'));
  add('R07', async () => { await badRoster(r => r.fixedInputs[0].path += '.replacement'); await badRoster(r => r.sdkInputs[0].rootIndex = 1); });
  add('R08', async () => { await badRoster(r => r.fixedInputs[0].bytes++); await badRoster(r => r.fixedInputs[0].sha256 = '0'.repeat(64)); });
  add('R09', async () => { await badRoster(r => r.sdkInputs[0].requestedName = 'replacement.lib'); await badRoster(r => r.search.roots.reverse()); });
  add('R10', async () => { await badRoster(r => r.fixedInputs[0].directiveArraySha256 = H); await badRoster(r => r.errors[0].code = 'LibraryInputsFormat'); await badRoster(r => r.inputBytesDecimal = '359493031'); await badRoster(r => r.fixedInputs[0].unexpected = 1); });

  add('G01', () => noCalls(state({ ready: false })));
  add('G02', () => noCalls(state({ stopped: true })));
  add('G03', async () => { const s = state({ ready: false }), f = fixture(); await noCalls(s, f); s.ready = true; s.stopped = false; await noCalls(s, f); });
  add('G04', () => noCalls(state({ pending: true })));
  add('G05', async () => { const s = state(), f = fixture({ openThrow: true }); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); const n = f.calls.length; s.stopped = false; await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.calls.length, n); });
  add('G06', async () => { const s = state(), a = fixture({ identifyThrow: true }), b = fixture(); await rejected(() => api.readPinnedInput(a.pin, s, a.adapter)); s.ready = true; s.stopped = false; await rejected(() => api.readPinnedInput(b.pin, s, b.adapter)); eq(b.calls, []); assert.equal(s.reservedInputs, 1); assert.equal(s.reservedReadBytes, 40); });

  add('I01', async () => { const f = fixture(), s = state(), r = await api.readPinnedInput(f.pin, s, f.adapter); eq(r.buffer, f.bytes); assert.notEqual(r.buffer, f.bytes); eq(r.identity, f.identity); assert.equal(s.actualReadBytes, 40); assert.equal(s.reservedReadBytes, 40); assert.equal(s.opened.length, 1); assert.equal(f.stats.closes, 1); assert.equal(s.pending, false); assert.equal(s.stopped, false); });
  add('I02', async () => { const f = fixture({ short: 3 }), s = state(); await api.readPinnedInput(f.pin, s, f.adapter); assert.equal(s.actualReadBytes, 40); assert(f.requests.length > 2); assert.equal(f.requests.filter(r => r.position === 0).length, 2); assert.equal(f.stats.closes, 1); });
  add('I03', async () => { const bytes = Buffer.alloc(65537, 1), f = fixture({ bytes }), s = state(); const r = await api.readPinnedInput(f.pin, s, f.adapter); eq(r.buffer, bytes); assert.equal(s.actualReadBytes, 131074); assert(f.requests.length >= 4); assert.equal(f.requests.filter(q => q.position === 0).length, 2); const first = f.requests[0].target; assert(f.requests.some(q => q.position === 0 && q.target !== first)); });
  add('I04', async () => { const f = fixture({ zero: true }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(s.actualReadBytes, 0); assert.equal(f.stats.closes, 1); assert.equal(s.reservedReadBytes, 40); assert.equal(s.stopped, true); });
  add('I05', async () => { const f = fixture({ over: true }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(s.actualReadBytes, 0); assert.equal(f.stats.closes, 1); assert.equal(s.stopped, true); });
  add('I06', async () => { for (const options of [{ corrupt: true }, { secondCorrupt: true }]) { const f = fixture(options), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.stats.closes, 1); assert.equal(s.stopped, true); assert.equal(s.reservedInputs, 1); } });
  add('I07', async () => { for (const statAt of [2, 3]) { const f = fixture({ statChange: { leaf: 'changed' }, statAt }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.stats.closes, 1); assert.equal(s.stopped, true); } });
  add('I08', async () => { const f = fixture({ statChange: { bytes: 21 }, statAt: 1 }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.requests.length, 0); assert.equal(f.stats.closes, 1); });
  add('I09', async () => { const f = fixture({ identifyChange: { root: 'changed' } }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.stats.closes, 1); assert.equal(s.stopped, true); });
  add('I10', async () => { const f = fixture({ identifyChange: { path: 'D:/synthetic/alias.obj' } }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.stats.closes, 1); });
  add('I11', async () => { const f = fixture({ closeThrow: true }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.stats.closes, 1); assert.equal(s.stopped, true); assert.equal(s.actualReadBytes, 40); });
  add('I12', async () => { const f = fixture({ readThrow: true }), s = state(); await rejected(() => api.readPinnedInput(f.pin, s, f.adapter)); assert.equal(f.stats.closes, 1); assert.equal(s.pending, false); assert.equal(s.stopped, true); });
  add('I13', async () => { const f = fixture(), s = state({ reservedInputs: 31, reservedBytes: 536870892, reservedReadBytes: 1073741784, actualReadBytes: 1073741784 }); await api.readPinnedInput(f.pin, s, f.adapter); eq([s.reservedInputs, s.reservedBytes, s.reservedReadBytes, s.actualReadBytes], [32, 536870912, 1073741824, 1073741824]); });
  // Entry-byte and two-scan-reservation ceilings are coupled (512MiB*2=1GiB).
  add('I14', async () => { for (const overrides of [{ reservedInputs: 32 }, { reservedInputs: 31, reservedBytes: 536870893, reservedReadBytes: 1073741786 }]) { const f = fixture(), s = state(overrides); await noCalls(s, f); eq([s.reservedInputs, s.reservedBytes, s.reservedReadBytes], [overrides.reservedInputs ?? 0, overrides.reservedBytes ?? 0, overrides.reservedReadBytes ?? 0]); } const f = fixture(); f.pin.bytes = 268435456; await noCalls(state(), f); });
  add('I15', async () => { for (const overrides of [{ actualReadBytes: 1 }, { reservedInputs: 0.5 }, { reservedReadBytes: 1 }]) await noCalls(state(overrides)); const f = fixture({ short: 3 }), s = state(), readOpen = f.adapter.open; f.adapter.open = async (...args) => { const h = await readOpen(...args), read = h.read; h.read = async (...q) => { assert(s.actualReadBytes + q[2] <= 1073741824); assert(s.actualReadBytes + q[2] <= s.reservedReadBytes); return read(...q); }; return h; }; await api.readPinnedInput(f.pin, s, f.adapter); assert.equal(s.actualReadBytes, 40); });
  add('I16', async () => {
    let release; const block = new Promise(resolve => { release = resolve; });
    const f = fixture({ block }), s = state();
    const pending = api.readPinnedInput(f.pin, s, f.adapter); void pending.catch(() => {});
    let error; try { s.pending = false; const other = fixture(); await rejected(() => api.readPinnedInput(other.pin, s, other.adapter)); eq(other.calls, []); } catch (e) { error = e; } finally { release(); }
    await rejected(() => pending); assert.equal(f.stats.closes, f.calls.includes('open') ? 1 : 0); assert.equal(s.stopped, true); if (error) throw error;
  });

  add('P01', () => { const b = object(), j = job(), r = pair(j, b); eq(r.row, { slot: 1, strict: parsed(api), profile: parsed(api) }); assert.equal(r.stopped, false); assert.equal(r.critical, null); eq([j.snapshot().attempts, j.snapshot().inputCount], [2, 1]); });
  add('P02', () => { const b = object(0), j = job(), r = pair(j, b, refusal('LibraryInputsFormat', { site: 'coff_machine', context: { ...emptyContext(), sections: 0, directiveBytes: 0, tokenCount: 0 } })); assert.equal(r.row.strict[0], 1); eq(r.row.profile.slice(0, 9), [0, 1, 0, 0, 0, 0, 1, 0, 0]); assert.equal(r.stopped, false); assert.equal(j.snapshot().attempts, 2); });
  add('P03', () => { const b = directive('/DEFAULTLIB:alpha\0'), j = job(), r = pair(j, b, refusal()); assert.equal(r.row.strict[0], 1); assert.equal(r.row.profile[0], 0); assert.equal(r.row.profile[8], 1); assert.equal(r.row.profile[4], 1); assert.equal(j.snapshot().sections, 2); });
  add('P04', () => { const j = job(), b = Buffer.alloc(1), r = pair(j, b, refusal()); eq([r.row.strict[0], r.row.profile[0], r.stopped, r.critical], [1, 1, false, null]); const next = object(), good = pair(j, next, baseline(next, 2)); assert.equal(good.row.profile[0], 0); assert.equal(j.snapshot().attempts, 4); });
  add('P05', () => { const b = object(), j = job(), r = pair(j, b, { ...baseline(b), objects: 2 }); assert.equal(r.row.profile, null); eq([r.stopped, r.critical, j.snapshot().attempts], [true, 'BaselineMismatch', 1]); const again = pair(j, object(), baseline(b, 2)); assert.equal(again.row.profile, null); assert.equal(j.snapshot().attempts, 1); });
  add('P06', () => { const b = directive('/DEFAULTLIB:alpha'), j = job(), r = pair(j, b, { ...baseline(b), directiveArraySha256: H }); eq([r.critical, r.row.profile, j.snapshot().attempts], ['BaselineMismatch', null, 1]); });
  add('P07', () => { const b = directive('/DEFAULTLIB:alpha'), j = job(), r = pair(j, b, { ...baseline(b), defaultLibraries: ['replacement.lib'] }); assert.equal(r.critical, 'BaselineMismatch'); assert.equal(j.snapshot().attempts, 1); });
  add('P08', () => { let calls = 0; const fake = { inspect() { calls++; throw Error('untrusted payload'); }, snapshot: () => ({ stopped: false }) }; const r = pair(fake, object()); eq([r.critical, r.stopped, r.row.profile, calls], ['UnknownInspection', true, null, 1]); pair(fake, object()); assert.equal(calls, 1); });
  add('P09', () => { const b = declared(0xffffffff), j = job(), r = pair(j, b, refusal('LibraryInputsSize')); eq([r.critical, r.stopped, r.row.profile], ['JobStopped', true, null]); eq([j.snapshot().attempts, j.snapshot().sections, j.snapshot().stopped], [1, 0, true]); const near = job(); let e; try { near.inspect(declared(2097151), 'strict-v1'); } catch (error) { e = error; } assert.equal(e?.site, 'coff_sections_member'); const one = Buffer.alloc(60); object().copy(one); one.writeUInt16LE(1, 2); one.write('.text', 20); one.writeUInt32LE(0x40, 56); const second = pair(near, one, baseline(object())); eq([second.row.strict[0], second.row.strict[5], second.row.profile[0], second.critical], [0, 1, 1, 'JobStopped']); eq([near.snapshot().attempts, near.snapshot().sections, near.snapshot().stopped], [3, 2097152, true]); });
  add('P10', () => { const b = object(), j = job(); pair(j, b); const r = pair(j, b, baseline(b, 2)); assert.equal(r.row.profile, null); assert.equal(r.stopped, true); assert.equal(j.snapshot().attempts, 2); const wrong = job(), bad = pair(wrong, object(), baseline(b, 2)); assert.equal(bad.critical, 'CohortOrder'); assert.equal(wrong.snapshot().attempts, 0); pair(wrong, object(), baseline(b)); assert.equal(wrong.snapshot().attempts, 0); const duplicate = job(); pair(duplicate, object()); const again = pair(duplicate, object()); assert.equal(again.critical, 'CohortOrder'); assert.equal(duplicate.snapshot().attempts, 2); });
  add('P11', () => { let calls = 0; const fake = { inspect() { calls++; const e = Error('LibraryInputsFormat'); e.site = 'unknown_untrusted_site'; e.context = emptyContext(); throw e; }, snapshot: () => ({ stopped: false }) }; const r = pair(fake, object(), refusal()); assert.equal(r.critical, 'UnknownInspection'); assert.equal(r.row.profile, null); assert.equal(calls, 1); });
  add('P12', () => { const b = object(0); for (const extra of [{ site: 'coff_header_range' }, { site: 'coff_machine', context: { ...emptyContext(), sections: 9 } }]) { const j = job(), r = pair(j, b, refusal('LibraryInputsFormat', extra)); assert.equal(r.critical, 'BaselineMismatch'); assert.equal(j.snapshot().attempts, 1); } });

  add('S01', () => { const c = api.codebook; eq(Object.keys(c).sort(), ['contexts', 'descriptorSha256', 'helperSha256', 'kinds', 'sha256', 'sites']); eq(c.kinds, KINDS); eq(c.contexts, CONTEXT); assert.equal(c.sites.length, 88); eq(c.sites, [...new Set(c.sites)].sort()); assert(c.sites.every(s => /^[a-z][a-z0-9_]{0,63}$/.test(s))); assert(Object.isFrozen(c) && Object.isFrozen(c.sites) && Object.isFrozen(c.kinds) && Object.isFrozen(c.contexts)); assert.equal(c.sha256, digest({ kinds: c.kinds, sites: c.sites, contexts: c.contexts })); assert.equal(c.helperSha256, '9972c0eb4d8cf936f252b090a8f0794b0d6b5328a2245b8720cdec32d5fafa53'); assert.equal(c.descriptorSha256, digest(MSVC_LIBRARY_METADATA_PROFILE)); });
  add('S02', () => { const r = report(api), encoded = api.encodeReport(r); assert.equal(typeof encoded, 'string'); assert(encoded.endsWith('\n') && !encoded.endsWith('\n\n')); eq(JSON.parse(encoded), r); assert(Buffer.byteLength(encoded) <= 16384); assert(r.rows.every(row => Buffer.byteLength(JSON.stringify(row)) <= 432)); const envelope = { ...r, rows: [] }; assert(Buffer.byteLength(JSON.stringify(envelope)) <= 2048); });
  add('S03', async () => { for (const key of ['qualified', 'linkQualification', 'closureComplete']) { const r = report(api); r[key] = true; await rejected(() => api.encodeReport(r)); } const r = report(api); r.profileId = 'unknown'; await rejected(() => api.encodeReport(r)); });
  add('S04', async () => { const r = report(api); r.raw = 'forbidden'; await rejected(() => api.encodeReport(r)); const q = report(api); q.rows[0].path = 'D:/payload'; await rejected(() => api.encodeReport(q)); const p = report(api); p.selfchecks.passed = 51; await rejected(() => api.encodeReport(p)); });
  add('S05', async () => { for (const change of [a => a.push(1), a => a[9] = 'invalid', a => a[6] = -1]) { const r = report(api); change(r.rows[0].strict); await rejected(() => api.encodeReport(r)); } for (const change of [a => a[2] = 88, a => a[3] = 4297064448, a => a[4] = '0']) { const r = report(api); change(r.rows[3].strict); await rejected(() => api.encodeReport(r)); } });
  add('S06', async () => { const partial = report(api, false); eq(JSON.parse(api.encodeReport(partial)), partial); const readFailed = report(api, false); readFailed.rows = []; readFailed.job.inputCount = 0; readFailed.job.inputBytes = 0; readFailed.job.attempts = 0; readFailed.io.actualReadBytes = 0; readFailed.critical = 'InputFailure'; eq(JSON.parse(api.encodeReport(readFailed)), readFailed); const r = report(api); [r.rows[0], r.rows[1]] = [r.rows[1], r.rows[0]]; await rejected(() => api.encodeReport(r)); const q = report(api, false); q.rows[0].profile = parsed(api); await rejected(() => api.encodeReport(q));
    const phantomInput = clone(readFailed); phantomInput.job.inputCount = 1; phantomInput.job.attempts = 64; await rejected(() => api.encodeReport(phantomInput));
    const phantomAttempt = clone(readFailed); phantomAttempt.job.attempts = 1; await rejected(() => api.encodeReport(phantomAttempt));
    const extraAttempt = clone(partial); extraAttempt.job.attempts = 2; await rejected(() => api.encodeReport(extraAttempt));
    const missingInput = clone(partial); missingInput.job.inputCount = 0; await rejected(() => api.encodeReport(missingInput));
    const parsedStop = clone(partial); parsedStop.critical = 'JobStopped'; parsedStop.job.stopped = true; parsedStop.job.attempts = 2; parsedStop.rows[0].profile = parsed(api); parsedStop.profileParsed = 1; await rejected(() => api.encodeReport(parsedStop));
  });
  // Oversize negatives also violate closed schema/count bounds: no arbitrary
  // padding capability exists to isolate unreachable valid-size +1 cases.
  add('S07', async () => { const r = report(api); r.rows[0].strict[9] = 'x'.repeat(433); assert(Buffer.byteLength(JSON.stringify(r.rows[0])) > 432); await rejected(() => api.encodeReport(r)); const q = report(api); q.proofs.first = 'x'.repeat(2049); assert(Buffer.byteLength(JSON.stringify({ ...q, rows: [] })) > 2048); await rejected(() => api.encodeReport(q)); const p = report(api); p.rows = Array(200).fill(p.rows[0]); assert(Buffer.byteLength(JSON.stringify(p) + '\n') > 16384); await rejected(() => api.encodeReport(p)); });
  add('S08', async () => { for (const mutate of [r => r.job.attempts = 63, r => r.io.actualReadBytes--, r => r.job.stopped = true, r => r.strictRefusals--, r => r.profileParsed--, r => r.critical = 'UntrustedMessage', r => r.rows[31].profile = null]) { const r = report(api); mutate(r); await rejected(() => api.encodeReport(r)); } });

  const expected = [['R', 10], ['G', 6], ['I', 16], ['P', 12], ['S', 8]].flatMap(([prefix, n]) => Array.from({ length: n }, (_, i) => prefix + String(i + 1).padStart(2, '0')));
  assert.deepEqual(cases.map(([id]) => id), expected, 'Frozen FIRST roster');
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: KIND, executed: cases.length, passed: cases.length - failed_case_ids.length,
    failed: failed_case_ids.length, failed_case_ids };
}
