// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST frozen before producer. Contract5400edc6. ALL20 UNRUN.
// Synthetic Buffers/fake handles only; no top-level execution, filesystem,
// SDK, environment, process, timer, console, source evaluation or network.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createLibraryMetadataJob, createLibraryMetadataJobV2 } from './library_inputs.mjs';
import { projectLibraryMetadataDependenciesV1 } from './library_metadata_dependencies.mjs';

const V1 = 'msvc-library-metadata-v1', V2 = 'msvc-library-metadata-v2';
const PROOFS = ['module', 'parser', 'heldReader', 'collector', 'first', 'supervisor',
  'runtimeSnapshot', 'runtimeRootReview', 'paddingSnapshot', 'paddingRootReview', 'descriptor'];
const REPORT = ['version', 'kind', 'purpose', 'qualified', 'linkQualification',
  'closureComplete', 'captureComplete', 'status', 'proofs', 'job', 'io', 'rows', 'critical'];
const ROW = ['slot', 'name', 'rootIndex', 'status', 'pin', 'io', 'strict', 'profile'];
const CONTEXT = ['memberIndex', 'memberOffset', 'sectionIndex', 'sections',
  'directiveBytes', 'tokenCount', 'actual', 'limit'];
const ZERO = { unknownMachineObjects: 0, unusedRelocationPointers: 0, terminalNulSections: 0 };
const EMPTY = { objects: 1, imports: 0, directives: [], defaultLibraries: [] };
const eq = (a, b) => assert.deepEqual(a, b);
const clone = x => JSON.parse(JSON.stringify(x));
const sha = b => createHash('sha256').update(b).digest('hex');
const digest = x => sha(Buffer.from(JSON.stringify(x)));
const proofs = () => Object.fromEntries(PROOFS.map((key, i) => [key, (i % 10).toString().repeat(64)]));
function keys(value, wanted) { eq(Object.keys(value).sort(), [...wanted].sort()); }
function frozen(value) {
  if (value !== null && typeof value === 'object') {
    assert(Object.isFrozen(value)); assert(!Buffer.isBuffer(value));
    Object.values(value).forEach(frozen);
  }
}
function throws(fn, message) { assert.throws(fn, { message }); }
async function rejects(fn, message) { await assert.rejects(fn, { message }); }
function coff(bytes = 20, machine = 0x8664) {
  const b = Buffer.alloc(bytes); b.writeUInt16LE(machine); return b;
}
function directive(text) {
  const p = Buffer.from(text), b = Buffer.alloc(60 + p.length);
  b.writeUInt16LE(0x8664); b.writeUInt16LE(1, 2); b.write('.drectve', 20);
  b.writeUInt32LE(p.length, 36); b.writeUInt32LE(60, 40); b.writeUInt32LE(0x200, 56);
  p.copy(b, 60); return b;
}
function archive(body, padding = 10) {
  const h = Buffer.alloc(60, 32); h.write('synthetic/', 0, 'ascii');
  h.write('0', 16); h.write('0', 28); h.write('0', 34); h.write('100644', 40);
  h.write(String(body.length).padEnd(10, ' '), 48); h[58] = 96; h[59] = 10;
  return Buffer.concat([Buffer.from('!<arch>\n'), h, body,
    body.length % 2 ? Buffer.from([padding]) : Buffer.alloc(0)]);
}
function metadata(names, directives) {
  return { objects: 1, imports: 0, directives: [...directives].sort(), defaultLibraries: [...names].sort() };
}
function summary(mode, m = EMPTY, sections = 0, deviations = {}) {
  return { profileId: mode, objects: m.objects, imports: m.imports, sections,
    deviations: { ...ZERO, ...(mode === V2 ? { nulArchivePaddingMembers: 0 } : {}), ...deviations },
    metadataSha256: digest(m), defaultLibraries: [...m.defaultLibraries] };
}
function parsed(mode, m = EMPTY, sections = 0, deviations = {}) {
  return { status: 'parsed', summary: summary(mode, m, sections, deviations), error: null };
}
function refused(kind, site, overrides = {}) {
  return { status: 'refused', summary: null, error: { kind, site,
    context: { ...Object.fromEntries(CONTEXT.map(k => [k, null])), ...overrides } } };
}
const failed = () => ({ status: 'failed', summary: null, error: null });
function fullIO(bytes) {
  return { reservedInputs: 1, reservedBytes: bytes, reservedReadBytes: 2 * bytes,
    actualReadBytes: 2 * bytes, opened: true, closed: true, verifiedPasses: 2 };
}
function stateIO(report, inputs, bytes, read = 2 * bytes) {
  eq(report.io, { reservedInputs: inputs, reservedBytes: bytes,
    reservedReadBytes: 2 * bytes, actualReadBytes: read });
}
function job(report, inputs = 0, bytes = 0, attempts = 0, sections = 0) {
  eq(report.job, { profileId: V2, inputCount: inputs, inputBytes: bytes,
    attempts, sections, stopped: false });
}
function structure(r) {
  keys(r, REPORT); eq(Object.keys(r), REPORT); assert.equal(r.version, 2);
  assert.equal(r.kind, 'fixed_two_runtime_metadata_v2');
  assert.equal(r.purpose, 'build_input_metadata_only');
  for (const k of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(r[k], false);
  eq(r.rows.map(x => [x.slot, x.name, x.rootIndex]), [[33, 'ucrt.lib', 3], [34, 'vcruntime.lib', 1]]);
  r.rows.forEach(row => keys(row, ROW)); keys(r.proofs, PROOFS); frozen(r);
  assert(Buffer.byteLength(JSON.stringify(r)) <= 24576);
  return r;
}
function complete(r) {
  structure(r); assert.equal(r.status, 'complete'); assert.equal(r.captureComplete, true);
  assert.equal(r.critical, null); eq(r.rows.map(x => x.status), ['complete', 'complete']);
  return r;
}
function stopped(r, code) {
  structure(r); assert.equal(r.status, 'stopped'); assert.equal(r.captureComplete, false);
  assert.equal(r.critical, code); return r;
}

// Hooks belong only to FIRST's in-memory fake; session receives exactly three
// adapter callbacks and the accepted reader's three held-wrapper callbacks.
function fixture(data = coff()) {
  const original = { bytes: data.length, sha256: sha(data), rootIdentity: 'synthetic-root',
    leafIdentity: 'synthetic-leaf' }, pin = { ...original }, hooks = {};
  const state = { live: true, liveCalls: 0, identifies: 0, opens: 0, stats: 0,
    reads: 0, closes: 0, requests: [], firstBuffer: null };
  const wrapper = {
    async stat() {
      state.stats++; const normal = () => ({ bytes: original.bytes, leafIdentity: original.leafIdentity });
      return hooks.stat ? hooks.stat(state.stats, normal) : normal();
    },
    async read(buffer, offset, length, position) {
      state.reads++; assert(Buffer.isBuffer(buffer));
      assert(Number.isSafeInteger(length) && length > 0 && length <= 65536);
      assert(offset >= 0 && offset + length <= buffer.length && position >= 0 && position + length <= data.length);
      state.requests.push({ buffer, offset, length, position }); state.firstBuffer ??= buffer;
      const normal = (maximum = length) => {
        const bytesRead = Math.min(length, maximum); data.copy(buffer, offset, position, position + bytesRead);
        return { bytesRead };
      };
      return hooks.read ? hooks.read({ buffer, offset, length, position, call: state.reads }, normal) : normal();
    },
    async close() { state.closes++; if (hooks.close) return hooks.close(); }
  };
  const adapter = {
    isLive() { state.liveCalls++; return hooks.live ? hooks.live() : state.live; },
    async identify() {
      state.identifies++; const normal = () => ({ bytes: original.bytes,
        rootIdentity: original.rootIdentity, leafIdentity: original.leafIdentity });
      return hooks.identify ? hooks.identify(state.identifies, normal) : normal();
    },
    async open(mode) { assert.equal(mode, 'r'); state.opens++; return hooks.open ? hooks.open(wrapper) : wrapper; }
  };
  return { data, pin, original, hooks, state, adapter, wrapper };
}
function barrier() {
  let release, entered;
  const wait = new Promise(resolve => { release = resolve; });
  const ready = new Promise(resolve => { entered = resolve; });
  return { wait, ready, release, entered };
}
async function both(session, first = fixture(), second = fixture()) {
  await session.observe(0, first.pin, first.adapter);
  return complete(await session.observe(1, second.pin, second.adapter));
}
function namesText(count, long = false) {
  const names = Array.from({ length: count }, (_, i) =>
    'n' + String(i).padStart(2, '0') + (long ? 'x'.repeat(252) : ''));
  return { names: names.map(n => n + '.lib'), text: names.map(n => '/DEFAULTLIB:' + n).join(' ') };
}

export async function runRuntimeMetadataV2Selfchecks(api) {
  if (!api || typeof api.createRuntimeMetadataObservationV2 !== 'function' ||
      Object.keys(api).length !== 1) throw Error('UNRUN_SETUP: runtime metadata v2 factory unavailable');
  const factory = api.createRuntimeMetadataObservationV2;
  const fresh = () => factory(proofs()), cases = [];
  const add = (id, run) => cases.push([id, run]);

  add('T01', () => {
    const p = proofs(), s = factory(p); keys(s, ['observe', 'snapshot', 'encode']); assert(Object.isFrozen(s));
    p.module = 'f'.repeat(64); eq(s.snapshot().proofs, proofs());
    for (const bad of [undefined, null, [], {}, { ...proofs(), extra: 'a'.repeat(64) },
      { ...proofs(), parser: new String('a'.repeat(64)) }, { ...proofs(), parser: 'A'.repeat(64) },
      { ...proofs(), first: '0'.repeat(64) + '\n' }, Object.create(proofs())]) {
      throws(() => factory(bad), 'RuntimeMetadataV2Setup');
    }
    let touched = 0; const accessor = proofs();
    Object.defineProperty(accessor, 'module', { enumerable: true, get() { touched++; return 'a'.repeat(64); } });
    throws(() => factory(accessor), 'RuntimeMetadataV2Setup'); assert.equal(touched, 0);
    const symbol = proofs(); symbol[Symbol('extra')] = 1; throws(() => factory(symbol), 'RuntimeMetadataV2Setup');
  });
  add('T02', () => {
    const s = fresh(), r = structure(s.snapshot()); eq(r.proofs, proofs());
    assert.equal(r.status, 'incomplete'); assert.equal(r.captureComplete, false); assert.equal(r.critical, null);
    job(r); stateIO(r, 0, 0);
    for (const row of r.rows) eq([row.status, row.pin, row.io, row.strict, row.profile], ['unstarted', null, null, null, null]);
    assert.equal(s.encode(), JSON.stringify(r)); eq(JSON.parse(s.encode()), r);
    assert.notEqual(s.snapshot(), r); assert.notEqual(s.snapshot().rows, r.rows);
  });
  add('T03', async () => {
    const s = fresh(), text = '/DEFAULTLIB:a', data = archive(directive(text), 10);
    assert.equal(directive(text).length % 2, 1); const a = fixture(data), b = fixture();
    const r = await both(s, a, b), m = metadata(['a.lib'], [text]);
    eq(r.rows[0].strict, parsed('strict-v1', m, 1)); eq(r.rows[0].profile, parsed(V2, m, 1));
    eq(r.rows[1].strict, parsed('strict-v1')); eq(r.rows[1].profile, parsed(V2));
    job(r, 2, data.length + 20, 4, 2); stateIO(r, 2, data.length + 20);
    eq(r.rows.map(x => x.io), [fullIO(data.length), fullIO(20)]);
    assert.equal(a.state.opens, 1); assert.equal(a.state.closes, 1); assert.equal(b.state.closes, 1);
  });
  add('T04', async () => {
    const s = fresh(), text = '/DEFAULTLIB:a', f = fixture(archive(directive(text), 0));
    const r = await s.observe(0, f.pin, f.adapter); structure(r);
    eq(r.rows[0].strict, refused('LibraryInputsFormat', 'archive_padding_byte',
      { memberIndex: 0, memberOffset: 8, sections: 0, directiveBytes: 0, tokenCount: 0 }));
    eq(r.rows[0].profile, parsed(V2, metadata(['a.lib'], [text]), 1, { nulArchivePaddingMembers: 1 }));
    keys(r.rows[0].profile.summary.deviations, [...Object.keys(ZERO), 'nulArchivePaddingMembers']);
    job(r, 1, f.data.length, 2, 1); eq(f.data[f.data.length - 1], 0);
    const b = fixture(); complete(await s.observe(1, b.pin, b.adapter));
  });
  add('T05', async () => {
    const s = fresh(), a = fixture(coff(20, 0x1337)), b = fixture(coff(20, 0x1337));
    const r = await both(s, a, b), error = refused('LibraryInputsFormat', 'coff_machine',
      { sections: 0, directiveBytes: 0, tokenCount: 0 });
    for (const row of r.rows) { eq(row.strict, error); eq(row.profile, error); }
    job(r, 2, 40, 4, 0); assert.equal(r.captureComplete, true);
    // Refused table validation still charges declared work in BOTH attempts.
    const declared = coff(); declared.writeUInt16LE(2, 2);
    const charged = fresh(), c = fixture(declared);
    const partial = await charged.observe(0, c.pin, c.adapter);
    const table = refused('LibraryInputsFormat', 'coff_section_table_range',
      { sections: 2, directiveBytes: 0, tokenCount: 0 });
    eq(partial.rows[0].strict, table); eq(partial.rows[0].profile, table); job(partial, 1, 20, 2, 4);
    const d = fixture(); job(complete(await charged.observe(1, d.pin, d.adapter)), 2, 40, 4, 4);
  });
  add('T06', async () => {
    for (const index of [1, -1, 2, '0', new Number(0), 0.5]) {
      const s = fresh(), f = fixture(); await rejects(() => s.observe(index, f.pin, f.adapter), 'RuntimeMetadataV2Sequence');
      stopped(s.snapshot(), 'RuntimeMetadataV2Sequence'); assert.equal(f.state.liveCalls + f.state.opens + f.state.identifies, 0);
      await rejects(() => s.observe(0, f.pin, f.adapter), 'RuntimeMetadataV2Sequence'); job(s.snapshot());
    }
    const repeat = fresh(), f = fixture(); await repeat.observe(0, f.pin, f.adapter);
    await rejects(() => repeat.observe(0, f.pin, f.adapter), 'RuntimeMetadataV2Sequence');
    assert.equal(f.state.opens, 1); job(repeat.snapshot(), 1, 20, 2);
    const done = fresh(); await both(done);
    await rejects(() => done.observe(2, f.pin, f.adapter), 'RuntimeMetadataV2Sequence');
    stopped(done.snapshot(), 'RuntimeMetadataV2Sequence'); job(done.snapshot(), 2, 40, 4);
  });
  add('T07', async () => {
    const s = fresh(), f = fixture(), other = fixture(), gate = barrier();
    f.hooks.read = async (_, normal) => { if (f.state.reads === 1) { gate.entered(); await gate.wait; } return normal(); };
    const first = s.observe(0, f.pin, f.adapter); await gate.ready;
    const firstSettled = first.catch(error => error);
    try {
      await rejects(() => s.observe(1, other.pin, other.adapter), 'RuntimeMetadataV2Sequence');
      stopped(s.snapshot(), 'RuntimeMetadataV2Sequence'); assert.equal(other.state.opens + other.state.identifies, 0);
    } finally { gate.release(); }
    const error = await firstSettled; assert(error instanceof Error); assert.equal(error.message, 'RuntimeMetadataV2Sequence');
    const r = stopped(s.snapshot(), 'RuntimeMetadataV2Sequence'); eq(r.rows[0].io, fullIO(20));
    eq([r.rows[0].strict, r.rows[0].profile], [null, null]); stateIO(r, 1, 20); job(r);
    assert.equal(f.state.closes, 1); await rejects(() => s.observe(1, other.pin, other.adapter), 'RuntimeMetadataV2Sequence');
  });
  add('T08', async () => {
    const bads = [p => ({ ...p, bytes: 0 }), p => ({ ...p, bytes: 285589 }), p => ({ ...p, bytes: '20' }),
      p => ({ ...p, sha256: 'a'.repeat(63) }), p => ({ ...p, sha256: 'a'.repeat(64) + '\n' }),
      p => ({ ...p, bytes: new Number(20) }), p => ({ ...p, sha256: new String(p.sha256) }),
      p => ({ ...p, rootIdentity: 'bad/path' }), p => ({ ...p, leafIdentity: 'x'.repeat(257) }),
      p => ({ ...p, extra: 1 }), p => Object.create(p), p => Object.assign([], p)];
    for (const change of bads) {
      const s = fresh(), f = fixture(); await rejects(() => s.observe(0, change(f.pin), f.adapter), 'RuntimeMetadataV2Pin');
      assert.equal(f.state.liveCalls + f.state.identifies + f.state.opens, 0); job(s.snapshot());
      stopped(s.snapshot(), 'RuntimeMetadataV2Pin'); eq(s.snapshot().rows[0].pin, null);
    }
    let touched = 0; const s = fresh(), f = fixture(), p = { ...f.pin };
    Object.defineProperty(p, 'bytes', { enumerable: true, get() { touched++; return 20; } });
    await rejects(() => s.observe(0, p, f.adapter), 'RuntimeMetadataV2Pin'); assert.equal(touched, 0);
    const ceiling = fresh(), a = fixture(); await ceiling.observe(0, a.pin, a.adapter);
    const b = fixture(coff(38479)); await rejects(() => ceiling.observe(1, b.pin, b.adapter), 'RuntimeMetadataV2Pin');
    assert.equal(b.state.opens + b.state.identifies, 0);
  });
  add('T09', async () => {
    for (const pass of [1, 2]) {
      const s = fresh(), f = fixture();
      f.hooks.read = ({ buffer, offset, call }, normal) => { const got = normal(); if (call === pass) buffer[offset] ^= 1; return got; };
      await rejects(() => s.observe(0, f.pin, f.adapter), 'PaddingHash');
      const r = stopped(s.snapshot(), 'PaddingHash'); assert.equal(r.rows[0].io.actualReadBytes, pass * 20);
      assert.equal(r.rows[0].io.verifiedPasses, pass - 1); assert.equal(f.state.closes, 1);
      eq([r.rows[0].strict, r.rows[0].profile], [null, null]); job(r);
    }
    const late = fresh(), f = fixture();
    f.hooks.close = () => { f.state.firstBuffer[0] ^= 1; };
    await rejects(() => late.observe(0, f.pin, f.adapter), 'PaddingHash');
    const r = stopped(late.snapshot(), 'PaddingHash');
    eq(r.rows[0].io, fullIO(20)); job(r); assert.equal(f.state.closes, 1);
  });
  add('T10', async () => {
    const s = fresh(), f = fixture(coff(140000));
    f.hooks.read = (_, normal) => normal(7001);
    const r = await s.observe(0, f.pin, f.adapter); structure(r); eq(r.rows[0].io, fullIO(140000));
    eq(r.rows[0].strict, parsed('strict-v1')); eq(r.rows[0].profile, parsed(V2));
    assert(f.state.requests.length > 6); assert(f.state.requests.every(x => x.length <= 65536));
    const second = f.state.requests.findIndex((x, i) => i > 0 && x.position === 0); assert(second > 0);
    assert.notEqual(f.state.requests[0].buffer, f.state.requests[second].buffer);
    assert.equal(f.state.requests[second].offset, 0); job(r, 1, 140000, 2); assert.equal(f.state.closes, 1);
  });
  add('T11', async () => {
    const changes = [f => { f.hooks.identify = (_, normal) => ({ ...normal(), rootIdentity: 'other-root' }); },
      f => { f.hooks.stat = (call, normal) => ({ ...normal(), ...(call === 2 ? { leafIdentity: 'other-leaf' } : {}) }); },
      f => { f.hooks.stat = (_, normal) => ({ ...normal(), bytes: 21 }); },
      f => { f.hooks.identify = (call, normal) => ({ ...normal(), ...(call === 2 ? { leafIdentity: 'other-leaf' } : {}) }); }];
    for (const change of changes) {
      const s = fresh(), f = fixture(); change(f); await rejects(() => s.observe(0, f.pin, f.adapter), 'PaddingIdentity');
      const r = stopped(s.snapshot(), 'PaddingIdentity'); job(r); assert.equal(r.rows[0].strict, null);
      assert.equal(f.state.closes, f.state.opens); assert(r.rows[0].io.actualReadBytes <= 40);
    }
  });
  add('T12', async () => {
    for (const read of [() => ({ bytesRead: 0 }), ({ length }) => ({ bytesRead: length + 1 }),
      () => { throw Error('private fake payload'); }]) {
      const s = fresh(), f = fixture(); f.hooks.read = read;
      await rejects(() => s.observe(0, f.pin, f.adapter), 'PaddingRead');
      const r = stopped(s.snapshot(), 'PaddingRead'); assert.equal(r.rows[0].io.actualReadBytes, 0);
      assert.equal(f.state.closes, 1); assert(!s.encode().includes('private fake payload')); job(r);
    }
  });
  add('T13', async () => {
    const only = fresh(), a = fixture(); a.hooks.close = () => { throw Error('close-secret'); };
    await rejects(() => only.observe(0, a.pin, a.adapter), 'PaddingClose');
    let r = stopped(only.snapshot(), 'PaddingClose'); assert.equal(a.state.closes, 1);
    assert.equal(r.rows[0].io.closed, false); assert.equal(r.rows[0].io.verifiedPasses, 2); job(r);
    const prior = fresh(), b = fixture();
    b.hooks.read = ({ buffer, offset }, normal) => { const got = normal(); buffer[offset] ^= 1; return got; };
    b.hooks.close = () => { throw Error('later-close-secret'); };
    await rejects(() => prior.observe(0, b.pin, b.adapter), 'PaddingHash'); r = stopped(prior.snapshot(), 'PaddingHash');
    assert.equal(b.state.closes, 1); assert.equal(r.rows[0].io.closed, false); assert(!prior.encode().includes('close-secret'));
  });
  add('T14', async () => {
    const s = fresh(), f = fixture();
    f.hooks.read = (_, normal) => { const got = normal(3); f.state.live = false; return got; };
    await rejects(() => s.observe(0, f.pin, f.adapter), 'PaddingStopped');
    const r = stopped(s.snapshot(), 'PaddingStopped'); assert.equal(r.rows[0].io.actualReadBytes, 3);
    assert.equal(r.rows[0].io.verifiedPasses, 0); assert.equal(r.rows[0].io.closed, true);
    assert.equal(f.state.closes, 1); stateIO(r, 1, 20, 3); job(r);
  });
  add('T15', async () => {
    const s = fresh(), f = fixture(), expected = { ...f.pin };
    f.hooks.read = (_, normal) => { f.pin.sha256 = 'f'.repeat(64); f.pin.rootIdentity = 'caller-changed'; return normal(); };
    const r = await s.observe(0, f.pin, f.adapter); eq(r.rows[0].pin, expected);
    const prior = clone(r); assert.throws(() => { r.rows[0].profile.summary.defaultLibraries.push('bad.lib'); }, TypeError);
    const edited = clone(r); edited.rows[0].profile.summary.deviations.nulArchivePaddingMembers = 9;
    edited.job.inputCount = 0; edited.proofs.module = 'e'.repeat(64); eq(s.snapshot(), prior);
    const b = fixture(); complete(await s.observe(1, b.pin, b.adapter));
    eq(r, prior); eq(s.snapshot().rows[0], r.rows[0]); assert.notEqual(s.snapshot().rows[0], r.rows[0]);
  });
  add('T16', async () => {
    const s = fresh(), text = '/DEFAULTLIB:Zulu /DEFAULTLIB:alpha /DEFAULTLIB:Zulu', f = fixture(directive(text));
    const r = await s.observe(0, f.pin, f.adapter), m = metadata(['alpha.lib', 'zulu.lib'],
      ['/DEFAULTLIB:Zulu', '/DEFAULTLIB:alpha']);
    eq(r.rows[0].strict, parsed('strict-v1', m, 1)); eq(r.rows[0].profile, parsed(V2, m, 1));
    for (const text of ['/DEFAULTLIB', '.drectve', 'synthetic-root/']) assert(!s.encode().includes(text));
    assert.equal(r.rows[0].profile.summary.metadataSha256, digest(m));
    keys(r.rows[0].profile.summary, ['profileId', 'objects', 'imports', 'sections',
      'deviations', 'metadataSha256', 'defaultLibraries']);
    // Additive post-producer review regression; original427-line FIRST above
    // was frozen before producer. Raw accepted directive text is hashed, never
    // copied into this bounded report or limited to an invented64KiB/token.
    const longToken = '/X:' + 'x'.repeat(70000), large = fixture(directive(longToken));
    assert(longToken.length > 65536 && large.data.length <= 285588);
    const longSession = fresh(), longReport = structure(await longSession.observe(0, large.pin, large.adapter));
    const longMetadata = metadata([], [longToken]);
    eq(longReport.rows[0].strict, parsed('strict-v1', longMetadata, 1));
    eq(longReport.rows[0].profile, parsed(V2, longMetadata, 1));
    job(longReport, 1, large.data.length, 2, 2); stateIO(longReport, 1, large.data.length);
    assert(!longSession.encode().includes(longToken));
    assert(!longSession.encode().includes('x'.repeat(65537)));
  });
  add('T17', async () => {
    const n32 = namesText(32), ok = fresh(), a = fixture(directive(n32.text));
    const accepted = await ok.observe(0, a.pin, a.adapter);
    eq(accepted.rows[0].strict.summary.defaultLibraries, n32.names);
    eq(accepted.rows[0].profile.summary.defaultLibraries, n32.names);
    const n33 = namesText(33), over = fresh(), b = fixture(directive(n33.text));
    await rejects(() => over.observe(0, b.pin, b.adapter), 'RuntimeMetadataV2ReportLimit');
    const refused = stopped(over.snapshot(), 'RuntimeMetadataV2ReportLimit');
    eq(refused.rows[0].strict, failed()); eq(refused.rows[0].profile, null); job(refused, 1, b.data.length, 1, 1);
    assert(!over.encode().includes('n32.lib')); // no truncated32-name success
    const long = namesText(32, true), bounded = fresh(), c = fixture(directive(long.text));
    assert(long.names.every(n => n.length === 259));
    const expectedStrict = parsed('strict-v1', metadata(long.names, long.text.split(' ')), 1);
    assert(Buffer.byteLength(JSON.stringify(expectedStrict.summary)) <= 16384);
    assert(Buffer.byteLength(JSON.stringify(expectedStrict.summary)) * 2 > 16384);
    await rejects(() => bounded.observe(0, c.pin, c.adapter), 'RuntimeMetadataV2ReportLimit');
    const r = stopped(bounded.snapshot(), 'RuntimeMetadataV2ReportLimit');
    eq(r.rows[0].strict, expectedStrict); eq(r.rows[0].profile, failed());
    assert.equal(r.rows[0].strict.summary.defaultLibraries.length, 32); job(r, 1, c.data.length, 2, 2);
    assert(Buffer.byteLength(bounded.encode()) <= 24576);
  });
  add('T18', async () => {
    const s = fresh(), f = fixture(), gate = barrier();
    f.hooks.read = async (_, normal) => { if (f.state.reads === 1) { gate.entered(); await gate.wait; } return normal(); };
    const pending = s.observe(0, f.pin, f.adapter); await gate.ready;
    try {
      const r = structure(s.snapshot()); assert.equal(r.status, 'pending'); assert.equal(r.captureComplete, false);
      eq([r.rows[0].status, r.rows[0].io, r.rows[0].strict, r.rows[0].profile], ['reading', null, null, null]);
      eq(r.rows[0].pin, f.original); stateIO(r, 0, 0); job(r); assert.equal(s.encode(), JSON.stringify(r));
    } finally { gate.release(); }
    const partial = await pending; assert.equal(partial.status, 'incomplete'); assert.equal(partial.rows[0].status, 'complete');
    eq([partial.rows[1].status, partial.rows[1].pin, partial.rows[1].io, partial.rows[1].strict, partial.rows[1].profile],
      ['unstarted', null, null, null, null]);
    const b = fixture(); complete(await s.observe(1, b.pin, b.adapter));
  });
  add('T19', async () => {
    for (const change of [f => ({ ...f.adapter, extra: () => {} }), f => ({ ...f.adapter, identify: 1 }),
      f => Object.create(f.adapter)]) {
      const s = fresh(), f = fixture(); await rejects(() => s.observe(0, f.pin, change(f)), 'PaddingType');
      const r = stopped(s.snapshot(), 'PaddingType'); assert.equal(f.state.opens, 0); job(r);
    }
    const s = fresh(), f = fixture(); f.hooks.open = () => { throw Error('secret-os-error'); };
    await rejects(() => s.observe(0, f.pin, f.adapter), 'PaddingRead');
    stopped(s.snapshot(), 'PaddingRead'); assert(!s.encode().includes('secret-os-error'));
    let touched = 0; const bad = fresh(), g = fixture();
    g.hooks.open = wrapper => {
      const changed = { ...wrapper }; Object.defineProperty(changed, 'read', { enumerable: true,
        get() { touched++; return wrapper.read; } }); return changed;
    };
    await rejects(() => bad.observe(0, g.pin, g.adapter), 'PaddingRead');
    assert.equal(touched, 0); assert.equal(g.state.closes, 1); stopped(bad.snapshot(), 'PaddingRead');
  });
  add('T20', async () => {
    const done = fresh(), completeReport = await both(done);
    const failedSession = fresh(), f = fixture(); f.hooks.read = () => ({ bytesRead: 0 });
    await rejects(() => failedSession.observe(0, f.pin, f.adapter), 'PaddingRead');
    for (const r of [fresh().snapshot(), completeReport, failedSession.snapshot()]) {
      structure(r); assert.equal(Object.keys(r).length, REPORT.length);
      assert(!Object.hasOwn(r, 'facts')); assert(!Object.hasOwn(r, 'allKnownNamesProvided'));
      eq(JSON.parse(JSON.stringify(r)), r);
    }
    // Actual complete valid-v1 baseline BEFORE testing v2 isolation.
    const legacy = createLibraryMetadataJob(V1), pins = [], observations = [];
    for (let i = 0; i < 32; i++) {
      const result = legacy.inspect(coff(), V1); observations.push({ slot: i + 1, result });
      pins.push({ slot: i + 1, metadataSha256: digest(EMPTY), libraryCount: 0 });
    }
    const catalog = Array.from({ length: 15 }, (_, i) => ({ slot: i + 18,
      name: 'known-' + String(i).padStart(2, '0') + '.lib' }));
    const baseline = projectLibraryMetadataDependenciesV1(pins, observations, catalog);
    assert.equal(baseline.captureComplete, true); assert.equal(baseline.kind, 'msvc_library_dependency_facts_v1');
    const v2 = createLibraryMetadataJobV2(V2).inspect(coff(), V2);
    for (const relabel of [false, true]) {
      const edited = clone(observations), inserted = clone(v2); if (relabel) inserted.profileId = V1;
      edited[12].result = inserted;
      throws(() => projectLibraryMetadataDependenciesV1(pins, edited, catalog), 'LibraryMetadataDependencyFactsInvalid');
    }
    eq(projectLibraryMetadataDependenciesV1(pins, observations, catalog), baseline);
  });

  eq(cases.map(([id]) => id), Array.from({ length: 20 }, (_, i) => 'T' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: 'runtime_metadata_v2_first', executed: 20,
    passed: 20 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
