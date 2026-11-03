// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST against21f157a8/97012224, BEFORE producer. ALL24 UNRUN.
// Synthetic adapters/manual numbers only. No filesystem, SDK, environment,
// process, real timer, producer helper, source evaluation or top-level suite.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const INVALID = 'WorkerArtifactWindowsInputsV1Invalid', LIMIT = 'WorkerArtifactWindowsInputsV1Limit';
const PIN = ['slot', 'kind', 'path', 'root', 'bytes', 'sha256', 'rootIdentity', 'leafIdentity'];
const IO = ['reservedInputs', 'reservedBytes', 'reservedReadBytes', 'actualReadBytes',
  'openAttempts', 'opened', 'closeAttempts', 'closed', 'verifiedScans', 'unknownClosures'];
const PROOF = ['version', 'kind', 'slot', 'role', 'bytes', 'sha256', 'pinHash', 'identityHash', 'io',
  'qualified', 'linkQualification', 'closureComplete', 'requiresFreshAdmission'];
const SNAP = ['version', 'kind', 'purpose', 'status', 'pinCount', 'nextIndex', 'pendingIndex',
  'completedInputs', 'io', 'lastProof', 'critical', 'cancelRequested', 'qualified', 'linkQualification',
  'closureComplete', 'requiresFreshAdmission'];
const H = 'a'.repeat(64);
const eq = (a, b) => assert.deepEqual(a, b);
const clone = value => JSON.parse(JSON.stringify(value));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const digest = value => sha(Buffer.from(JSON.stringify(value)));
const keys = (value, expected) => eq(Object.keys(value).sort(), [...expected].sort());
const throws = (fn, message = INVALID) => assert.throws(fn, { message });
const rejects = (fn, message) => assert.rejects(fn, { message });
function frozen(value) {
  if (value !== null && typeof value === 'object') {
    assert(Object.isFrozen(value)); assert(!Buffer.isBuffer(value)); Object.values(value).forEach(frozen);
  }
}
function io(overrides = {}) { return { ...Object.fromEntries(IO.map(key => [key, 0])), ...overrides }; }
function reserved(n, overrides = {}) {
  return io({ reservedInputs: 1, reservedBytes: n, reservedReadBytes: 2 * n, ...overrides });
}
function full(n) {
  return reserved(n, { actualReadBytes: 2 * n, openAttempts: 1, opened: 1,
    closeAttempts: 1, closed: 1, verifiedScans: 2 });
}
function expectedProof(pin) {
  return { version: 1, kind: 'worker_artifact_windows_input_v1', slot: pin.slot, role: pin.kind,
    bytes: pin.bytes, sha256: pin.sha256, pinHash: digest(pin), identityHash: digest({ root: pin.rootIdentity,
      leaf: pin.leafIdentity, bytes: pin.bytes }), io: full(pin.bytes), qualified: false,
    linkQualification: false, closureComplete: false, requiresFreshAdmission: true };
}
function pin(slot, data = Buffer.from('synthetic input')) {
  const role = slot <= 17 ? 'project' : 'sdk', root = (role === 'project' ? 'D' : 'C') + ':/synthetic/root-' + slot;
  return { slot, kind: role, path: root + '/input-' + slot + '.obj', root, bytes: data.length,
    sha256: sha(data), rootIdentity: 'synthetic-root-' + slot, leafIdentity: 'synthetic-leaf-' + slot };
}
function barrier() {
  let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
async function until(predicate) {
  for (let i = 0; i < 2048; i++) { if (predicate()) return; await Promise.resolve(); }
  throw Error('FIRST finite microtask bound');
}
function fixture(data = [Buffer.from('synthetic input')]) {
  const pins = data.map((bytes, i) => pin(i + 1, bytes)), expected = clone(pins), hooks = {}, calls = [], stats = data.map(() =>
    ({ identifies: 0, opens: 0, stats: 0, reads: 0, closes: 0, requests: [], firstBuffer: null }));
  const f = { data, pins, expected, spec: { pins }, hooks, calls, stats, time: 0, nowCalls: 0, reader: null, adapter: null };
  const wrappers = expected.map((p, i) => ({
    async stat() {
      assert.equal(arguments.length, 0); stats[i].stats++; calls.push('stat:' + p.slot);
      const normal = () => ({ leaf: p.leafIdentity, bytes: p.bytes });
      return hooks.stat ? hooks.stat(p.slot, stats[i].stats, normal) : normal();
    },
    async read(buffer, offset, length, position) {
      stats[i].reads++; calls.push('read:' + p.slot); assert(Buffer.isBuffer(buffer));
      assert(Number.isSafeInteger(length) && length > 0 && length <= 65536);
      assert(offset >= 0 && offset + length <= buffer.length && position >= 0 && position + length <= p.bytes);
      stats[i].requests.push({ buffer, offset, length, position }); stats[i].firstBuffer ??= buffer;
      const normal = (maximum = length) => {
        const bytesRead = Math.min(length, maximum); data[i].copy(buffer, offset, position, position + bytesRead);
        return { bytesRead };
      };
      return hooks.read ? hooks.read(p.slot, { buffer, offset, length, position, call: stats[i].reads }, normal) : normal();
    },
    async close() { assert.equal(arguments.length, 0); stats[i].closes++; calls.push('close:' + p.slot); if (hooks.close) return hooks.close(p.slot); }
  }));
  f.wrappers = wrappers;
  f.adapter = {
    async identify(p) {
      const i = p.slot - 1; eq(p, expected[i]); assert(Object.isFrozen(p)); stats[i].identifies++; calls.push('identify:' + p.slot);
      const normal = () => ({ path: expected[i].path, root: expected[i].rootIdentity, leaf: expected[i].leafIdentity, bytes: expected[i].bytes });
      return hooks.identify ? hooks.identify(p.slot, stats[i].identifies, normal) : normal();
    },
    async open(p, mode) {
      const i = p.slot - 1; eq(p, expected[i]); assert(Object.isFrozen(p)); assert.equal(mode, 'r');
      stats[i].opens++; calls.push('open:' + p.slot); return hooks.open ? hooks.open(p.slot, wrappers[i]) : wrappers[i];
    },
    now() { f.nowCalls++; return hooks.now ? hooks.now() : f.time; }
  };
  return f;
}
function snap(f, status, expectedIO, next = 0, code = null, pending = null, cancelled = false) {
  const s = f.reader.snapshot(); keys(s, SNAP); eq(Object.keys(s), SNAP); frozen(s);
  assert.equal(s.version, 1); assert.equal(s.kind, 'worker_artifact_windows_inputs_snapshot_v1');
  assert.equal(s.purpose, 'bounded_build_input_read_only');
  eq([s.status, s.pinCount, s.nextIndex, s.completedInputs, s.pendingIndex, s.critical, s.cancelRequested],
    [status, f.pins.length, next, next, pending, code, cancelled]); eq(s.io, expectedIO);
  for (const key of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(s[key], false);
  assert.equal(s.requiresFreshAdmission, true); assert(Buffer.byteLength(JSON.stringify(s)) <= 4096);
  assert(s.io.actualReadBytes <= s.io.reservedReadBytes && s.io.reservedReadBytes === 2 * s.io.reservedBytes);
  assert(s.io.closed <= s.io.closeAttempts && s.io.closeAttempts <= s.io.opened && s.io.opened <= s.io.openAttempts);
  return s;
}
function success(f, result, index = 0) {
  keys(result, ['buffer', 'proof']); assert(Object.isFrozen(result)); assert(Buffer.isBuffer(result.buffer));
  assert(result.buffer.equals(f.data[index])); keys(result.proof, PROOF); eq(Object.keys(result.proof), PROOF);
  eq(result.proof, expectedProof(f.expected[index])); frozen(result.proof);
  assert(Buffer.byteLength(JSON.stringify(result.proof)) <= 2048); return result;
}
async function sticky(f, code) {
  const before = clone(f.reader.snapshot()), calls = f.calls.length, clock = f.nowCalls;
  await rejects(() => f.reader.readNext(), code); eq(f.reader.snapshot(), before);
  assert.equal(f.calls.length, calls); assert.equal(f.nowCalls, clock); assert.equal(f.reader.cancel(), false);
}

export async function runWorkerArtifactWindowsInputsSelfchecksV1(api) {
  if (!api || typeof api.createWorkerArtifactWindowsInputsV1ForTesting !== 'function' || Object.keys(api).length !== 1) {
    throw Error('UNRUN_SETUP: worker artifact Windows inputs test factory unavailable');
  }
  const create = api.createWorkerArtifactWindowsInputsV1ForTesting, cases = [], add = (id, run) => cases.push([id, run]);
  const start = f => { f.reader = create(f.spec, f.adapter); return f; };

  add('W01', () => {
    const f = fixture();
    for (const bad of [null, [], {}, Object.create(f.spec), { ...f.spec, extra: 1 }]) throws(() => create(bad, f.adapter));
    for (const key of PIN) { const p = { ...f.pins[0] }; delete p[key]; throws(() => create({ pins: [p] }, f.adapter)); }
    for (const p of [{ ...f.pins[0], extra: 1 }, Object.create(f.pins[0]),
      { ...f.pins[0], bytes: new Number(f.pins[0].bytes) }, { ...f.pins[0], sha256: new String(H) },
      { ...f.pins[0], rootIdentity: 'x'.repeat(257) }, { ...f.pins[0], sha256: H + '\n' }]) throws(() => create({ pins: [p] }, f.adapter));
    for (const bad of [null, [], Object.create(f.adapter), { ...f.adapter, extra() {} }, { ...f.adapter, open: 1 }]) throws(() => create(f.spec, bad));
    let touched = 0; const accessor = { ...f.pins[0] };
    Object.defineProperty(accessor, 'path', { enumerable: true, get() { touched++; return f.pins[0].path; } });
    throws(() => create({ pins: [accessor] }, f.adapter)); assert.equal(touched, 0);
    const method = { ...f.adapter }; Object.defineProperty(method, 'now', { enumerable: true, get() { touched++; return () => 0; } });
    throws(() => create(f.spec, method)); assert.equal(touched, 0);
    const symbol = { ...f.pins[0] }; symbol[Symbol('x')] = 1; throws(() => create({ pins: [symbol] }, f.adapter));
    assert.equal(f.nowCalls, 0); eq(f.calls, []); // validate descriptors BEFORE initial clock
  });
  add('W02', async () => {
    const f = fixture(), original = clone(f.expected[0]); start(f);
    f.pins[0].path = 'D:/caller/replaced'; f.pins[0].sha256 = H;
    f.adapter.identify = () => { throw Error('replaced'); }; f.adapter.open = () => { throw Error('replaced'); };
    f.adapter.now = () => { throw Error('replaced'); };
    const result = success(f, await f.reader.readNext()); eq(result.proof, expectedProof(original));
    const many = fixture(Array.from({ length: 18 }, () => Buffer.from('x')));
    keys(create(many.spec, many.adapter), ['readNext', 'cancel', 'snapshot']);
    for (const changed of [p => ({ ...p, slot: 18 }), p => ({ ...p, kind: 'sdk' }), p => ({ ...p, slot: '1' })]) {
      const g = fixture(); throws(() => create({ pins: [changed(g.pins[0])] }, g.adapter)); assert.equal(g.nowCalls, 0);
    }
    const sparse = fixture(); sparse.spec.pins.length = 2; throws(() => create(sparse.spec, sparse.adapter));
    const extra = fixture(); extra.spec.pins.extra = 1; throws(() => create(extra.spec, extra.adapter));
    const nullSpec = Object.assign(Object.create(null), { pins: [Object.assign(Object.create(null), original)] });
    keys(create(nullSpec, Object.assign(Object.create(null), fixture().adapter)), ['readNext', 'cancel', 'snapshot']);
  });
  add('W03', () => {
    for (const path of ['C:/synthetic/project', 'D:/', 'd:/synthetic/x', 'D:\\synthetic\\x', '//server/share',
      'D:/synthetic/../x', 'D:/synthetic//x', 'D:/synthetic/x/', 'D:/synthetic/x.', 'D:/synthetic/x ',
      'D:/synthetic/a:b', 'D:/synthetic/a?b', 'D:/synthetic/a*b', 'D:/synthetic/a=b', 'D:/synthetic/a,b',
      'D:/synthetic/a;b', 'D:/synthetic/a#b', 'D:/synthetic/a`b', 'D:/synthetic/a&b', 'D:/synthetic/a|b',
      'D:/synthetic/a<b', 'D:/synthetic/a>b', 'D:/synthetic/a"b', 'D:/synthetic/a\u0000b',
      'D:/synthetic/a\u007fb', 'D:/synthetic/物語', 'D:/synthetic/com¹/x']) {
      const f = fixture(); f.pins[0].path = path; throws(() => create(f.spec, f.adapter)); assert.equal(f.nowCalls, 0);
    }
    for (const name of ['con', 'PRN.suffix', 'aux .txt', 'NUL', ...['com', 'lpt'].flatMap(prefix =>
      Array.from({ length: 9 }, (_, i) => prefix + (i + 1) + '.txt'))]) {
      const f = fixture(); f.pins[0].path = f.pins[0].root + '/' + name; throws(() => create(f.spec, f.adapter));
    }
    const outside = fixture(); outside.pins[0].path = outside.pins[0].root + '-peer/file'; throws(() => create(outside.spec, outside.adapter));
    const duplicate = fixture([Buffer.from('x'), Buffer.from('x')]); duplicate.pins[1].path = duplicate.pins[0].path.toUpperCase().replace('D:', 'D:');
    duplicate.pins[1].root = duplicate.pins[0].root.toUpperCase(); throws(() => create(duplicate.spec, duplicate.adapter));
    const spaces = fixture(); spaces.pins[0].root = 'D:/synthetic/Program Files (x86)/clean build';
    spaces.pins[0].path = spaces.pins[0].root + '/ordinary.obj'; keys(create(spaces.spec, spaces.adapter), ['readNext', 'cancel', 'snapshot']);
  });
  add('W04', async () => {
    const f = start(fixture()), n = f.data[0].length;
    snap(f, 'ready', io()); assert.equal(f.reader.snapshot().lastProof, null);
    const result = success(f, await f.reader.readNext());
    eq(f.calls, ['identify:1', 'open:1', 'stat:1', 'read:1', 'stat:1', 'identify:1', 'read:1', 'stat:1', 'identify:1', 'close:1']);
    eq(snap(f, 'complete', full(n), 1).lastProof, result.proof); assert.equal(f.reader.cancel(), false);
  });
  add('W05', async () => {
    const f = start(fixture([Buffer.from('one'), Buffer.from('second')])), a = success(f, await f.reader.readNext());
    eq(snap(f, 'ready', full(3), 1).lastProof, a.proof);
    const b = success(f, await f.reader.readNext(), 1), total = io({ reservedInputs: 2, reservedBytes: 9,
      reservedReadBytes: 18, actualReadBytes: 18, openAttempts: 2, opened: 2, closeAttempts: 2, closed: 2, verifiedScans: 4 });
    eq(snap(f, 'complete', total, 2).lastProof, b.proof); assert.equal(f.stats[0].closes, 1); assert.equal(f.stats[1].closes, 1);
  });
  add('W06', async () => {
    const f = fixture([Buffer.from('1234567')]); f.hooks.read = (_, __, normal) => normal(3); start(f);
    success(f, await f.reader.readNext());
    eq(f.stats[0].requests.map(r => [r.position, r.length, r.offset]), [[0, 7, 0], [3, 4, 3], [6, 1, 6], [0, 7, 0], [3, 4, 0], [6, 1, 0]]);
    snap(f, 'complete', full(7), 1);
  });
  add('W07', async () => {
    const f = start(fixture([Buffer.alloc(131073, 65)])); success(f, await f.reader.readNext());
    const requests = f.stats[0].requests;
    eq(requests.map(r => [r.position, r.length]), [[0, 65536], [65536, 65536], [131072, 1], [0, 65536], [65536, 65536], [131072, 1]]);
    assert.equal(requests[0].buffer, requests[1].buffer); assert.notEqual(requests[0].buffer, requests[3].buffer);
    assert(requests.slice(3).every(r => r.offset === 0 && r.buffer.length <= 65536)); snap(f, 'complete', full(131073), 1);
  });
  add('W08', async () => {
    const f = fixture(); f.hooks.read = (_, r, normal) => { const got = normal(); r.buffer[r.offset] ^= 1; return got; }; start(f);
    await rejects(() => f.reader.readNext(), 'IdentityFailure');
    snap(f, 'stopped', reserved(f.data[0].length, { actualReadBytes: f.data[0].length, openAttempts: 1,
      opened: 1, closeAttempts: 1, closed: 1 }), 0, 'IdentityFailure'); await sticky(f, 'IdentityFailure');
  });
  add('W09', async () => {
    const f = fixture(); f.hooks.read = (_, r, normal) => { const got = normal(); if (r.call === 2) r.buffer[r.offset] ^= 1; return got; }; start(f);
    await rejects(() => f.reader.readNext(), 'IdentityFailure');
    snap(f, 'stopped', { ...full(f.data[0].length), verifiedScans: 1 }, 0, 'IdentityFailure');
    assert.equal(f.stats[0].reads, 2); assert.equal(f.stats[0].closes, 1);
  });
  add('W10', async () => {
    for (const key of ['root', 'leaf', 'path', 'bytes']) {
      const f = fixture(); f.hooks.identify = (_, __, normal) => ({ ...normal(), [key]: key === 'bytes' ? 1 : 'different' }); start(f);
      await rejects(() => f.reader.readNext(), 'IdentityFailure');
      snap(f, 'stopped', reserved(f.data[0].length), 0, 'IdentityFailure'); assert.equal(f.stats[0].opens, 0);
    }
    for (const at of [2, 3]) for (const key of ['root', 'leaf', 'path']) {
      const f = fixture(); f.hooks.identify = (_, call, normal) => ({ ...normal(), ...(call === at ? { [key]: 'changed' } : {}) }); start(f);
      await rejects(() => f.reader.readNext(), 'IdentityFailure'); assert.equal(f.stats[0].closes, 1);
      assert.equal(f.reader.snapshot().io.verifiedScans, at - 1); assert.equal(f.reader.snapshot().io.unknownClosures, 0);
    }
  });
  add('W11', async () => {
    for (const at of [1, 2, 3]) for (const key of ['leaf', 'bytes']) {
      const f = fixture(); f.hooks.stat = (_, call, normal) => ({ ...normal(), ...(call === at ? { [key]: key === 'bytes' ? 1 : 'different' } : {}) }); start(f);
      await rejects(() => f.reader.readNext(), 'IdentityFailure'); assert.equal(f.stats[0].closes, 1);
      assert.equal(f.reader.snapshot().io.verifiedScans, at - 1); assert.equal(f.reader.snapshot().io.closed, 1);
    }
    const f = fixture(); f.hooks.stat = (_, __, normal) => ({ ...normal(), type: 'directory' }); start(f);
    await rejects(() => f.reader.readNext(), 'IdentityFailure'); assert.equal(f.stats[0].reads, 0); assert.equal(f.stats[0].closes, 1);
  });
  add('W12', async () => {
    const variants = [() => ({ bytesRead: 0 }), (_, r) => ({ bytesRead: r.length + 1 }), () => ({ bytesRead: -1 }),
      () => ({ bytesRead: '1' }), () => ({ bytesRead: 1.5 }), () => ({ bytesRead: 1, extra: true }), () => null];
    for (const hook of variants) {
      const f = fixture(); f.hooks.read = hook; start(f); await rejects(() => f.reader.readNext(), 'InputFailure');
      assert.equal(f.reader.snapshot().io.actualReadBytes, 0); assert.equal(f.stats[0].closes, 1);
    }
    let touched = 0; const f = fixture(); f.hooks.read = () => Object.defineProperty({}, 'bytesRead',
      { enumerable: true, get() { touched++; return 1; } }); start(f);
    await rejects(() => f.reader.readNext(), 'InputFailure'); assert.equal(touched, 0); assert.equal(f.reader.snapshot().io.actualReadBytes, 0);
  });
  add('W13', async () => {
    for (const name of ['identify', 'open', 'stat', 'read']) {
      const f = fixture(); f.hooks[name] = () => { throw Error('private OS payload'); }; start(f);
      await rejects(() => f.reader.readNext(), 'InputFailure'); const s = f.reader.snapshot();
      assert(!JSON.stringify(s).includes('private OS payload'));
      assert.equal(s.io.unknownClosures, name === 'open' ? 1 : 0);
      assert.equal(f.stats[0].closes, name === 'stat' || name === 'read' ? 1 : 0); await sticky(f, 'InputFailure');
    }
  });
  add('W14', async () => {
    const f = fixture(); f.hooks.close = () => { throw Error('private close'); }; start(f);
    await rejects(() => f.reader.readNext(), 'InputFailure');
    snap(f, 'stopped', { ...full(f.data[0].length), closed: 0, unknownClosures: 1 }, 0, 'InputFailure');
    assert.equal(f.stats[0].closes, 1); await sticky(f, 'InputFailure');
  });
  add('W15', async () => {
    for (const first of ['IdentityFailure', 'InputFailure', 'InputCancelled', 'InputDeadline']) {
      const f = fixture();
      f.hooks.read = (_, r, normal) => {
        if (first === 'InputFailure') throw Error('private read');
        const got = normal(3);
        if (first === 'IdentityFailure') r.buffer[r.offset] ^= 1;
        if (first === 'InputCancelled') f.reader.cancel();
        if (first === 'InputDeadline') f.time = 60001;
        return got;
      };
      f.hooks.close = () => { throw Error('later close'); }; start(f);
      await rejects(() => f.reader.readNext(), first); assert.equal(f.stats[0].closes, 1);
      assert.equal(f.reader.snapshot().io.unknownClosures, 1); await sticky(f, first);
    }
  });
  add('W16', async () => {
    for (const method of ['stat', 'read']) {
      let touched = 0; const f = fixture(); f.hooks.open = (_, wrapper) => {
        const result = { ...wrapper }; Object.defineProperty(result, method, { enumerable: true, get() { touched++; return wrapper[method]; } }); return result;
      }; start(f); await rejects(() => f.reader.readNext(), 'InputFailure');
      assert.equal(touched, 0); assert.equal(f.stats[0].closes, 1); assert.equal(f.reader.snapshot().io.unknownClosures, 0);
    }
    for (const missing of [true, false]) {
      let touched = 0; const f = fixture(); f.hooks.open = (_, wrapper) => {
        const result = { stat: wrapper.stat, read: wrapper.read };
        if (!missing) Object.defineProperty(result, 'close', { enumerable: true, get() { touched++; return wrapper.close; } }); return result;
      }; start(f); await rejects(() => f.reader.readNext(), 'InputFailure');
      assert.equal(touched, 0); assert.equal(f.stats[0].closes, 0); assert.equal(f.reader.snapshot().io.opened, 1);
      assert.equal(f.reader.snapshot().io.unknownClosures, 1); await sticky(f, 'InputFailure');
    }
    const fn = fixture(); fn.hooks.open = (_, wrapper) => Object.assign(function invalidWrapper() {}, { close: wrapper.close }); start(fn);
    await rejects(() => fn.reader.readNext(), 'InputFailure'); assert.equal(fn.stats[0].closes, 1);
    for (const handle of [null, undefined, 42]) {
      const f = fixture(); f.hooks.open = () => handle; start(f);
      await rejects(() => f.reader.readNext(), 'InputFailure');
      const s = f.reader.snapshot(); assert.equal(s.io.openAttempts, 1); assert.equal(s.io.opened, 0);
      assert.equal(s.io.closeAttempts, 0); assert.equal(s.io.closed, 0); assert.equal(s.io.unknownClosures, 1);
    }
    const late = fixture(); late.hooks.open = (_, wrapper) => { late.reader.cancel(); return wrapper; }; start(late);
    await rejects(() => late.reader.readNext(), 'InputCancelled'); assert.equal(late.stats[0].closes, 1); assert.equal(late.stats[0].stats, 0);
  });
  add('W17', async () => {
    const before = start(fixture()); assert.equal(before.reader.cancel(), true); assert.equal(before.reader.cancel(), false);
    await rejects(() => before.reader.readNext(), 'InputCancelled'); snap(before, 'stopped', io(), 0, 'InputCancelled', null, true); eq(before.calls, []);
    for (const operation of ['identify', 'open', 'read']) {
      const f = fixture(), held = barrier(); let normal;
      if (operation === 'identify') f.hooks.identify = (_, __, fn) => { normal = fn; return held.promise; };
      if (operation === 'open') f.hooks.open = (_, wrapper) => { normal = () => wrapper; return held.promise; };
      if (operation === 'read') f.hooks.read = (_, __, fn) => { normal = () => fn(3); return held.promise; };
      start(f); const pending = f.reader.readNext(), settled = pending.catch(error => error); await until(() => normal !== undefined);
      assert.equal(f.reader.cancel(), true); const mid = f.reader.snapshot(); assert.equal(mid.status, 'pending'); assert.equal(mid.pendingIndex, 0);
      assert.equal(mid.critical, 'InputCancelled'); assert.equal(mid.io.unknownClosures, 0);
      held.resolve(normal()); const error = await settled; assert.equal(error.message, 'InputCancelled');
      const n = f.data[0].length, actual = operation === 'read' ? 3 : 0, opened = operation === 'identify' ? 0 : 1;
      snap(f, 'stopped', reserved(n, { actualReadBytes: actual, openAttempts: opened, opened,
        closeAttempts: opened, closed: opened }), 0, 'InputCancelled', null, true);
      assert.equal(f.stats[0].closes, opened); await sticky(f, 'InputCancelled');
    }
  });
  add('W18', async () => {
    const f = fixture(), held = barrier(); let finish;
    f.hooks.read = (_, __, normal) => { finish = () => normal(3); return held.promise; }; start(f);
    const pending = f.reader.readNext(), settled = pending.catch(error => error); await until(() => finish !== undefined);
    const calls = f.calls.length; await rejects(() => f.reader.readNext(), 'InputSequence'); assert.equal(f.calls.length, calls);
    assert.equal(f.reader.snapshot().status, 'pending'); assert.equal(f.reader.snapshot().critical, 'InputSequence');
    held.resolve(finish()); assert.equal((await settled).message, 'InputSequence');
    snap(f, 'stopped', reserved(f.data[0].length, { actualReadBytes: 3, openAttempts: 1, opened: 1, closeAttempts: 1, closed: 1 }), 0, 'InputSequence');
    await sticky(f, 'InputSequence');
  });
  add('W19', async () => {
    const f = fixture(); f.hooks.close = () => { f.stats[0].firstBuffer[0] ^= 1; }; start(f);
    await rejects(() => f.reader.readNext(), 'IdentityFailure'); snap(f, 'stopped', full(f.data[0].length), 0, 'IdentityFailure');
    assert.equal(f.reader.snapshot().lastProof, null);
    const g = start(fixture()), result = success(g, await g.reader.readNext()), saved = clone(result.proof);
    result.buffer[0] ^= 1; assert.notEqual(sha(result.buffer), result.proof.sha256); eq(result.proof, saved);
    assert.notEqual(result.buffer, g.data[0]); assert.equal(sha(g.data[0]), saved.sha256);
  });
  add('W20', async () => {
    const f = start(fixture()), result = success(f, await f.reader.readNext()), s = snap(f, 'complete', full(f.data[0].length), 1);
    frozen(result.proof); frozen(s); const encoded = JSON.stringify({ proof: result.proof, snapshot: s });
    for (const text of [f.expected[0].path, f.expected[0].root, f.expected[0].rootIdentity, f.expected[0].leafIdentity,
      'rootIdentity', 'leafIdentity', '"path"', '"root"']) assert(!encoded.includes(text));
    assert.throws(() => { s.io.actualReadBytes = 0; }, TypeError); const changed = clone(s); changed.io.actualReadBytes = 0;
    eq(f.reader.snapshot(), s); assert.notEqual(f.reader.snapshot(), s); assert.notEqual(f.reader.snapshot().io, s.io);
  });
  add('W21', async () => {
    for (const argument of ['D:/other/file', 0, {}, undefined]) {
      const f = start(fixture()); await rejects(() => f.reader.readNext(argument), 'InputSequence');
      snap(f, 'stopped', io(), 0, 'InputSequence'); eq(f.calls, []); await sticky(f, 'InputSequence');
    }
    const f = start(fixture()); success(f, await f.reader.readNext()); const before = clone(f.reader.snapshot()), calls = f.calls.length, clock = f.nowCalls;
    await rejects(() => f.reader.readNext(), 'InputSequence'); eq(f.reader.snapshot(), before);
    assert.equal(f.calls.length, calls); assert.equal(f.nowCalls, clock); keys(f.reader, ['readNext', 'cancel', 'snapshot']);
    assert.equal(f.reader.cancel(), false); assert(!Object.hasOwn(f.reader, 'reset')); assert(!Object.hasOwn(f.reader, 'retry'));
  });
  add('W22', () => {
    const f = fixture(); f.spec.pins[0].bytes = 268435455; keys(create(f.spec, f.adapter), ['readNext', 'cancel', 'snapshot']); eq(f.calls, []);
    const over = fixture(); over.pins[0].bytes = 268435456; throws(() => create(over.spec, over.adapter), LIMIT); assert.equal(over.nowCalls, 0);
    const zero = fixture(); zero.pins[0].bytes = 0; throws(() => create(zero.spec, zero.adapter));
    for (const bytes of [-1, 1.5, Infinity]) { const bad = fixture(); bad.pins[0].bytes = bytes; throws(() => create(bad.spec, bad.adapter)); }
    const fullCount = fixture(Array.from({ length: 32 }, () => Buffer.from('x'))); keys(create(fullCount.spec, fullCount.adapter), ['readNext', 'cancel', 'snapshot']);
    const extra = fixture(Array.from({ length: 33 }, () => Buffer.from('x'))); throws(() => create(extra.spec, extra.adapter), LIMIT);
    const empty = fixture([]); throws(() => create(empty.spec, empty.adapter));
    const path = fixture(); path.pins[0].root = 'D:/' + ['a'.repeat(255), 'b'.repeat(255), 'c'.repeat(255)].join('/');
    path.pins[0].path = path.pins[0].root + '/' + 'd'.repeat(253); assert.equal(path.pins[0].path.length, 1024);
    keys(create(path.spec, path.adapter), ['readNext', 'cancel', 'snapshot']);
    path.pins[0].path += 'd'; throws(() => create(path.spec, path.adapter), LIMIT);
    const component = fixture(); component.pins[0].path = component.pins[0].root + '/' + 'u'.repeat(255);
    keys(create(component.spec, component.adapter), ['readNext', 'cancel', 'snapshot']);
    component.pins[0].path += 'u'; throws(() => create(component.spec, component.adapter), LIMIT);
    // Constructor DATA checks only: never readNext or allocate an input-sized Buffer here.
  });
  add('W23', () => {
    const f = fixture([Buffer.from('x'), Buffer.from('x'), Buffer.from('x')]);
    [268435455, 268435455, 2].forEach((count, i) => { f.pins[i].bytes = count; });
    const r = create(f.spec, f.adapter); assert.equal(f.pins.reduce((n, p) => n + p.bytes, 0), 536870912);
    assert.equal(2 * f.pins.reduce((n, p) => n + p.bytes, 0), 1073741824); eq(r.snapshot().io, io()); eq(f.calls, []);
    f.pins[2].bytes = 3; throws(() => create(f.spec, f.adapter), LIMIT);
    // These are coupled DECLARED ceilings. No512MiB/1GiB read/allocation is performed.
  });
  add('W24', async () => {
    for (const initial of [-1, NaN, Infinity, '0', null]) {
      const f = fixture(); f.time = initial; throws(() => create(f.spec, f.adapter)); eq(f.calls, []);
    }
    const inclusive = fixture(); inclusive.time = 0.25; start(inclusive); inclusive.time = 60000.25;
    success(inclusive, await inclusive.reader.readNext()); snap(inclusive, 'complete', full(inclusive.data[0].length), 1);
    const expired = start(fixture()); expired.time = 60001; await rejects(() => expired.reader.readNext(), 'InputDeadline');
    snap(expired, 'stopped', reserved(expired.data[0].length), 0, 'InputDeadline'); eq(expired.calls, []);
    for (const late of [-1, 9, NaN, Infinity, '1']) {
      const f = fixture(); f.time = 10; start(f); f.time = late; await rejects(() => f.reader.readNext(), 'InputFailure'); eq(f.calls, []);
    }
    const initialThrow = fixture(); initialThrow.hooks.now = () => { throw Error('private initial clock'); };
    throws(() => create(initialThrow.spec, initialThrow.adapter)); eq(initialThrow.calls, []);
    const thrown = start(fixture()); thrown.hooks.now = () => { throw Error('private clock'); };
    await rejects(() => thrown.reader.readNext(), 'InputFailure'); eq(thrown.calls, []);
    const lateRead = fixture(); lateRead.hooks.read = (_, __, normal) => { const got = normal(3); lateRead.time = 60001; return got; }; start(lateRead);
    await rejects(() => lateRead.reader.readNext(), 'InputDeadline');
    snap(lateRead, 'stopped', reserved(lateRead.data[0].length, { actualReadBytes: 3, openAttempts: 1, opened: 1,
      closeAttempts: 1, closed: 1 }), 0, 'InputDeadline');
    for (const cause of ['InputDeadline', 'InputCancelled']) {
      const f = fixture(); f.hooks.close = () => { f.stats[0].firstBuffer[0] ^= 1;
        if (cause === 'InputDeadline') f.time = 60001; else f.reader.cancel(); }; start(f);
      await rejects(() => f.reader.readNext(), cause); snap(f, 'stopped', full(f.data[0].length), 0, cause, null, cause === 'InputCancelled');
      assert.equal(f.stats[0].closes, 1); // final live check precedes final hash, with no repeated close
    }
    const shared = start(fixture([Buffer.from('a'), Buffer.from('bc')])); shared.time = 59999;
    success(shared, await shared.reader.readNext()); shared.time = 60001;
    await rejects(() => shared.reader.readNext(), 'InputDeadline');
    snap(shared, 'stopped', { ...full(1), reservedInputs: 2, reservedBytes: 3, reservedReadBytes: 6 }, 1, 'InputDeadline');
    assert.equal(shared.stats[1].identifies, 0); // one job clock, not a new60s allowance per input
  });

  eq(cases.map(([id]) => id), Array.from({ length: 24 }, (_, i) => 'W' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: 'worker_artifact_windows_inputs_first_v1', executed: 24,
    passed: 24 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
