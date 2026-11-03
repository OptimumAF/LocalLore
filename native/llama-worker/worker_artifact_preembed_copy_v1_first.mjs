// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST, contract58b1e0a9, frozen BEFORE producer. ALL20 UNRUN.
// In-memory files/manual clock only. No fs/process/SDK/production factory call,
// real timer, source evaluation, fixture creation or top-level test execution.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const INVALID = 'WorkerArtifactPreembedCopyV1Invalid', BUSY = 'WorkerArtifactPreembedCopyV1Busy', USED = 'WorkerArtifactPreembedCopyV1Used';
const API = ['createWorkerArtifactPreembedCopyV1', 'createWorkerArtifactPreembedCopyV1ForTesting'];
const IO = ['reservedCopies', 'reservedReadBytes', 'reservedWriteBytes', 'actualReadBytes', 'actualWriteBytes',
  'openAttempts', 'opened', 'closeAttempts', 'closed', 'unknownClosures', 'verifiedScans'];
const PROOF = ['version', 'kind', 'candidate', 'ok', 'code', 'executable', 'manifest', 'copy', 'io',
  'unknownClosure', 'ioUncertain', 'qualified', 'linkQualification', 'closureComplete',
  'requiresFreshAdmission', 'normalWorkerUnchangedRequired'];
const SNAP = ['version', 'kind', 'nextCandidate', 'busy', 'stopped', 'io', 'unknownClosure', 'ioUncertain',
  'qualified', 'linkQualification', 'closureComplete', 'requiresFreshAdmission', 'normalWorkerUnchangedRequired'];
const eq = (a, b) => assert.deepEqual(a, b);
const clone = value => JSON.parse(JSON.stringify(value));
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const keys = (value, wanted) => eq(Object.keys(value).sort(), [...wanted].sort());
const io = (changes = {}) => ({ ...Object.fromEntries(IO.map(key => [key, 0])), ...changes });
function reserve(e, m) { return io({ reservedCopies: 1, reservedReadBytes: 4 * e + 2 * m, reservedWriteBytes: e }); }
function full(e, m) { return { ...reserve(e, m), actualReadBytes: 4 * e + 2 * m, actualWriteBytes: e,
  openAttempts: 3, opened: 3, closeAttempts: 3, closed: 3, verifiedScans: 6 }; }
function plus(a, b) {
  return Object.fromEntries(IO.map(key => {
    const n = BigInt(a[key]) + BigInt(b[key]); return [key, n <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(n) : n.toString()];
  }));
}
function frozen(value) {
  if (value !== null && typeof value === 'object') { assert(Object.isFrozen(value)); assert(!Buffer.isBuffer(value)); Object.values(value).forEach(frozen); }
}
function config() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b', targetRoot: 'D:/synthetic/target', sdkUmRoot: 'C:/synthetic-sdk/um' };
}
function deferred() { let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; }); return { promise, resolve, reject }; }
async function until(predicate) {
  for (let i = 0; i < 2048; i++) { if (predicate()) return; await Promise.resolve(); }
  throw Error('FIRST finite microtask bound');
}

function fixture(create) {
  const c = config(), recipe = planWorkerArtifactComparisonV1(c), files = new Map(), roots = new Map(), calls = [], hooks = {};
  const f = { config: c, spec: { config: c }, recipe, files, roots, calls, hooks, requests: {}, handles: [],
    time: 0, nowCalls: 0, helper: null, adapter: null, after: null };
  for (const candidate of recipe.candidates) {
    const id = candidate.id, executable = Buffer.from('linked-executable-' + id), manifest = Buffer.from('<manifest-' + id + '/>');
    roots.set(candidate.outputRoot, { tag: id + ':root', identity: 'root-' + id, ordinary: true, real: true });
    files.set(candidate.executable, { tag: id + ':source', identity: 'source-' + id, data: executable, ordinary: true, real: true });
    files.set(candidate.manifest, { tag: id + ':manifest', identity: 'manifest-' + id, data: manifest, ordinary: true, real: true });
    f.requests[id] = { candidate: id, rootIdentity: 'root-' + id, executableIdentity: 'source-' + id,
      manifestIdentity: 'manifest-' + id, linked: { executable: { sha256: sha(executable), bytes: executable.length },
        manifest: { sha256: sha(manifest), bytes: manifest.length } } };
  }
  function invoke(method, tag, args, normal) {
    const entry = { method, tag, args }; calls.push(entry);
    const value = hooks[method] ? hooks[method](tag, args, normal, entry) : normal();
    if (f.after) f.after(entry, value); return value;
  }
  function file(path) { const found = files.get(path); if (!found) throw Error('mock missing file'); return found; }
  function wrapper(path, current, mode) {
    const handle = { tag: current.tag, mode, closeCalls: 0, closed: false, counts: { identity: 0, read: 0, write: 0, sync: 0 } };
    f.handles.push(handle);
    return {
      async identity() {
        assert.equal(arguments.length, 0); handle.counts.identity++;
        return invoke('stat', current.tag, { call: handle.counts.identity }, () => ({ identity: current.identity, bytes: current.data.length, ordinary: current.ordinary }));
      },
      async read(buffer, offset, length, position) {
        handle.counts.read++; assert(Buffer.isBuffer(buffer)); assert(length > 0 && length <= 65536 && offset >= 0 && offset + length <= buffer.length);
        assert(Number.isSafeInteger(position) && position >= 0);
        return invoke('read', current.tag, { buffer, offset, length, position, call: handle.counts.read }, (maximum = length) => {
          const n = Math.min(length, maximum, Math.max(0, current.data.length - position));
          current.data.copy(buffer, offset, position, position + n); return n;
        });
      },
      async write(buffer, offset, length, position) {
        handle.counts.write++; assert.equal(mode, 'wx+'); assert(Buffer.isBuffer(buffer));
        assert(length > 0 && length <= 65536 && offset >= 0 && offset + length <= buffer.length);
        return invoke('write', current.tag, { buffer, offset, length, position, call: handle.counts.write }, (maximum = length) => {
          const n = Math.min(length, maximum), grown = Buffer.alloc(Math.max(current.data.length, position + n));
          current.data.copy(grown); buffer.copy(grown, position, offset, offset + n); current.data = grown; return n;
        });
      },
      async sync() { assert.equal(arguments.length, 0); handle.counts.sync++; return invoke('sync', current.tag, {}, () => undefined); },
      async close() {
        assert.equal(arguments.length, 0); handle.closeCalls++;
        return invoke('close', current.tag, {}, () => { handle.closed = true; return undefined; });
      }
    };
  }
  f.adapter = {
    async identify(path, kind) {
      const current = kind === 'directory' ? roots.get(path) : files.get(path);
      assert(current, 'closed recipe paths only'); assert.equal(kind, roots.has(path) ? 'directory' : 'file');
      return invoke('identify', current.tag, { path, kind }, () => ({ identity: current.identity, ordinary: current.ordinary, real: current.real }));
    },
    async open(path, mode) {
      const candidate = recipe.candidates.find(x => [x.executable, x.manifest, x.preEmbedCopy].includes(path)); assert(candidate);
      const isCopy = path === candidate.preEmbedCopy; assert.equal(mode, isCopy ? 'wx+' : 'r');
      const tag = candidate.id + (isCopy ? ':copy' : path === candidate.executable ? ':source' : ':manifest');
      return invoke('open', tag, { path, mode }, () => {
        if (isCopy) {
          if (files.has(path)) throw Error('EEXIST mock retained');
          files.set(path, { tag, identity: 'copy-' + candidate.id, data: Buffer.alloc(0), ordinary: true, real: true });
        }
        return wrapper(path, file(path), mode);
      });
    },
    now() { f.nowCalls++; return hooks.now ? hooks.now() : f.time; }
  };
  f.helper = create(f.spec, f.adapter); return f;
}
function source(f, id = 'A') { return f.files.get(f.recipe.candidates[id === 'A' ? 0 : 1].executable); }
function manifest(f, id = 'A') { return f.files.get(f.recipe.candidates[id === 'A' ? 0 : 1].manifest); }
function copy(f, id = 'A') { return f.files.get(f.recipe.candidates[id === 'A' ? 0 : 1].preEmbedCopy); }
function label(entry) {
  if (entry.method === 'open') return 'open:' + entry.tag + ':' + entry.args.mode;
  if (entry.method === 'read' || entry.method === 'write') return entry.method + ':' + entry.tag + ':' + entry.args.position + ':' + entry.args.length;
  return entry.method + ':' + entry.tag;
}
function trace(id, e, m) {
  const root = 'identify:' + id + ':root', s = 'identify:' + id + ':source', mf = 'identify:' + id + ':manifest', cp = 'identify:' + id + ':copy';
  const sr = 'read:' + id + ':source:', mr = 'read:' + id + ':manifest:', cr = 'read:' + id + ':copy:';
  return [root, 'open:' + id + ':source:r', 'stat:' + id + ':source', sr + '0:' + e, sr + e + ':1', 'stat:' + id + ':source', s, root,
    'open:' + id + ':manifest:r', 'stat:' + id + ':manifest', mr + '0:' + m, mr + m + ':1', 'stat:' + id + ':manifest', root, s, mf,
    'open:' + id + ':copy:wx+', 'stat:' + id + ':copy', sr + '0:' + e, 'write:' + id + ':copy:0:' + e, sr + e + ':1',
    'stat:' + id + ':source', 'sync:' + id + ':copy', 'stat:' + id + ':source', 'stat:' + id + ':manifest', root, s, mf, cp,
    mr + '0:' + m, mr + m + ':1', 'stat:' + id + ':manifest', 'stat:' + id + ':copy', cr + '0:' + e, cr + e + ':1',
    'stat:' + id + ':copy', cr + '0:' + e, cr + e + ':1', 'stat:' + id + ':copy', root, s, mf, cp,
    'close:' + id + ':copy', 'close:' + id + ':manifest', 'close:' + id + ':source'];
}
function proof(f, value, code = null, candidate = 'A', uncertain = false) {
  keys(value, PROOF); frozen(value); assert.equal(value.version, 1); assert.equal(value.kind, 'worker_artifact_preembed_copy_v1');
  eq([value.candidate, value.ok, value.code, value.ioUncertain], [candidate, code === null, code, uncertain]);
  keys(value.io, IO); assert.equal(value.unknownClosure, value.io.unknownClosures > 0);
  if (code === null) {
    eq(value.executable, f.requests[candidate].linked.executable); eq(value.copy, value.executable);
    eq(value.manifest, f.requests[candidate].linked.manifest);
  } else eq([value.executable, value.manifest, value.copy], [null, null, null]);
  for (const key of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(value[key], false);
  assert.equal(value.requiresFreshAdmission, true); assert.equal(value.normalWorkerUnchangedRequired, true);
  assert(Buffer.byteLength(JSON.stringify(value)) < 4096); return value;
}
function snapshot(f, expectedIO, next, stopped = false, busy = false, uncertain = false) {
  const s = f.helper.snapshot(); keys(s, SNAP); frozen(s); assert.equal(s.version, 1);
  assert.equal(s.kind, 'worker_artifact_preembed_copy_snapshot_v1');
  eq([s.nextCandidate, s.busy, s.stopped, s.ioUncertain], [next, busy, stopped, uncertain]); eq(s.io, expectedIO);
  assert.equal(s.unknownClosure, s.io.unknownClosures > 0);
  for (const key of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(s[key], false);
  assert.equal(s.requiresFreshAdmission, true); assert.equal(s.normalWorkerUnchangedRequired, true); return s;
}
async function used(f) {
  const before = clone(f.helper.snapshot()), calls = f.calls.length;
  await assert.rejects(() => f.helper.copyNext(f.requests.B), { message: USED }); eq(f.helper.snapshot(), before);
  assert.equal(f.calls.length, calls); assert.equal(f.helper.cancel(), false);
}

export async function runWorkerArtifactPreembedCopySelfchecksV1(api) {
  if (!api || Object.keys(api).length !== 2 || API.some(key => typeof api[key] !== 'function')) throw Error('UNRUN_SETUP: preembed factories unavailable');
  const create = api.createWorkerArtifactPreembedCopyV1ForTesting, cases = [], add = (id, run) => cases.push([id, run]);
  // Production factory is deliberately never invoked by this mock runner.
  add('P01', () => {
    const f = fixture(create); keys(f.helper, ['copyNext', 'cancel', 'snapshot']); assert(Object.isFrozen(f.helper)); assert.equal(f.nowCalls, 0);
    for (const bad of [null, [], {}, Object.create(f.spec), { ...f.spec, extra: 1 }]) assert.throws(() => create(bad, f.adapter), { message: INVALID });
    for (const bad of [null, [], { ...f.adapter, extra() {} }, { ...f.adapter, open: 1 }, Object.create(f.adapter)]) assert.throws(() => create(f.spec, bad), { message: INVALID });
    let touched = 0; const getter = { ...f.adapter }; Object.defineProperty(getter, 'now', { enumerable: true, get() { touched++; return () => 0; } });
    assert.throws(() => create(f.spec, getter), { message: INVALID }); assert.equal(touched, 0);
    const symbol = { ...f.spec }; symbol[Symbol('extra')] = 1; assert.throws(() => create(symbol, f.adapter), { message: INVALID });
    assert.throws(() => create({ config: { ...config(), workerRoot: 'C:/bad' } }, f.adapter), { message: 'WorkerArtifactRecipeV1Invalid' });
    assert.throws(() => create({ config: { ...config(), workerRoot: 'D:/' + 'x'.repeat(256) } }, f.adapter), { message: 'WorkerArtifactRecipeV1Limit' });
    const empty = Object.assign(Object.create(null), f.spec); keys(create(empty, Object.assign(Object.create(null), f.adapter)), ['copyNext', 'cancel', 'snapshot']);
    eq(f.calls, []); assert.equal(f.nowCalls, 0);
  });
  add('P02', async () => {
    const f = fixture(create), a = proof(f, await f.helper.copyNext(f.requests.A));
    const e = f.requests.A.linked.executable.bytes, m = f.requests.A.linked.manifest.bytes;
    eq(a.io, full(e, m)); eq(f.calls.map(label), trace('A', e, m)); assert(copy(f).data.equals(source(f).data));
    const first = clone(a), b = proof(f, await f.helper.copyNext(f.requests.B), null, 'B');
    eq(b.io, full(f.requests.B.linked.executable.bytes, f.requests.B.linked.manifest.bytes));
    eq(f.calls.map(label), [...trace('A', e, m), ...trace('B', f.requests.B.linked.executable.bytes, f.requests.B.linked.manifest.bytes)]);
    snapshot(f, plus(a.io, b.io), null); eq(a, first); assert(f.handles.every(h => h.closeCalls === 1 && h.closed)); await used(f);
  });
  add('P03', async () => {
    for (const part of ['executable', 'manifest']) {
      const f = fixture(create); f.requests.A.linked[part].sha256 = 'a'.repeat(64);
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'CONTENT'); assert(!copy(f));
      assert.equal(p.io.verifiedScans, part === 'executable' ? 0 : 1);
      assert(!f.calls.some(entry => entry.method === 'open' && entry.tag === 'A:copy'));
    }
  });
  add('P04', async () => {
    for (const [tag, field, value] of [['A:root', 'ordinary', false], ['A:root', 'real', false], ['A:root', 'identity', 'different'],
      ['A:source', 'ordinary', false], ['A:source', 'real', false], ['A:source', 'identity', 'different'],
      ['A:manifest', 'ordinary', false], ['A:manifest', 'real', false]]) {
      const f = fixture(create); f.hooks.identify = (at, _, normal) => ({ ...normal(), ...(at === tag ? { [field]: value } : {}) });
      proof(f, await f.helper.copyNext(f.requests.A), 'IDENTITY');
    }
    const alias = fixture(create); alias.hooks.open = (tag, _, normal) => { const result = normal(); if (tag === 'A:copy') copy(alias).identity = source(alias).identity; return result; };
    proof(alias, await alias.helper.copyNext(alias.requests.A), 'IDENTITY'); assert(copy(alias));
    const inode = fixture(create); inode.hooks.stat = (tag, _, normal) => ({ ...normal(), ...(tag === 'A:source' ? { ordinary: false } : {}) });
    proof(inode, await inode.helper.copyNext(inode.requests.A), 'IDENTITY'); // ordinary seam includes nlink policy, not a real hardlink test
  });
  add('P05', async () => {
    for (const part of ['source', 'manifest']) {
      const size = fixture(create), target = part === 'source' ? source(size) : manifest(size);
      target.data = Buffer.concat([target.data, Buffer.from('x')]);
      proof(size, await size.helper.copyNext(size.requests.A), 'IDENTITY'); assert(!copy(size));
    }
    const changed = fixture(create); changed.hooks.open = (tag, _, normal) => { const result = normal(); if (tag === 'A:copy') source(changed).data[0] ^= 1; return result; };
    const p = proof(changed, await changed.helper.copyNext(changed.requests.A), 'CONTENT');
    assert(copy(changed).data.length > 0); assert(copy(changed).data.equals(source(changed).data));
    assert.equal(p.io.verifiedScans, 2); assert.equal(p.io.actualWriteBytes, changed.requests.A.linked.executable.bytes);
    assert(!changed.calls.some(entry => entry.method === 'sync')); await used(changed);
    const swap = fixture(create); swap.hooks.stat = (tag, args, normal) => ({ ...normal(),
      ...(tag === 'A:copy' && args.call === 3 ? { identity: 'different-inode' } : {}) });
    proof(swap, await swap.helper.copyNext(swap.requests.A), 'IDENTITY'); assert(copy(swap).data.equals(source(swap).data));
  });
  add('P06', async () => {
    const f = fixture(create), path = f.recipe.candidates[0].preEmbedCopy, retained = Buffer.from('previous retained output');
    f.files.set(path, { tag: 'A:copy', identity: 'prior-copy', data: Buffer.from(retained), ordinary: true, real: true });
    const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO'); assert(copy(f).data.equals(retained));
    eq([p.io.openAttempts, p.io.opened, p.io.closed, p.io.unknownClosures], [3, 2, 2, 1]);
    assert.equal(f.calls.filter(entry => entry.method === 'open' && entry.tag === 'A:copy').length, 1); await used(f);
  });
  add('P07', async () => {
    const f = fixture(create); f.hooks.read = (_, __, normal) => normal(3);
    f.hooks.write = (_, __, normal) => normal(1);
    const p = proof(f, await f.helper.copyNext(f.requests.A)); eq(p.io, full(f.requests.A.linked.executable.bytes, f.requests.A.linked.manifest.bytes));
    assert(copy(f).data.equals(source(f).data));
    const bufferCalls = f.calls.filter(entry => entry.method === 'read' || entry.method === 'write');
    assert(bufferCalls.every(entry => entry.args.buffer === bufferCalls[0].args.buffer && entry.args.buffer.length === 65536));
    for (const entry of f.calls.filter(x => x.method === 'read' && x.args.length === 1)) assert(entry.args.position > 0);
    assert(f.calls.filter(entry => entry.method === 'write').length > 1);
    const eof = fixture(create); eof.hooks.read = (tag, args, normal) => tag === 'A:source' && args.call === 2 ? 1 : normal();
    const failure = proof(eof, await eof.helper.copyNext(eof.requests.A), 'CONTENT'); assert.equal(failure.io.actualReadBytes, eof.requests.A.linked.executable.bytes + 1);
  });
  add('P08', async () => {
    for (const method of ['read', 'write']) for (const value of [0, -1, NaN, 1.5, Infinity]) {
      const f = fixture(create); f.hooks[method] = () => value;
      const uncertain = method === 'write' || value !== 0; const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO', 'A', uncertain);
      assert.equal(method === 'write' ? p.io.actualWriteBytes : p.io.actualReadBytes, 0);
    }
    for (const method of ['read', 'write']) {
      const f = fixture(create); f.hooks[method] = (_, args) => args.length + 1;
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO', 'A', true);
      assert.equal(method === 'write' ? p.io.actualWriteBytes : p.io.actualReadBytes, f.requests.A.linked.executable.bytes + 1);
    }
    for (const method of ['read', 'write']) {
      const f = fixture(create); let calls = 0;
      if (method === 'write') f.hooks.read = (_, __, normal) => normal(1);
      f.hooks[method] = (_, __, normal) => ++calls === 1 ? normal(1) : Number.MAX_SAFE_INTEGER;
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO', 'A', true);
      assert.equal(method === 'write' ? p.io.actualWriteBytes : p.io.actualReadBytes, '9007199254740992');
      assert.equal(method === 'write' ? f.helper.snapshot().io.actualWriteBytes : f.helper.snapshot().io.actualReadBytes, '9007199254740992');
    }
    const eof = fixture(create); eof.hooks.read = (tag, args, normal) => tag === 'A:source' && args.call === 2 ? 2 : normal();
    proof(eof, await eof.helper.copyNext(eof.requests.A), 'IO', 'A', true);
  });
  add('P09', async () => {
    const sync = fixture(create); sync.hooks.sync = () => { throw Error('private sync'); };
    const p = proof(sync, await sync.helper.copyNext(sync.requests.A), 'IO'); assert.equal(p.io.verifiedScans, 3);
    assert(copy(sync).data.equals(source(sync).data));
    for (const at of [1, 3]) {
      const f = fixture(create); f.hooks.read = (tag, args, normal) => { const n = normal(); if (tag === 'A:copy' && args.call === at && n > 0) args.buffer[args.offset] ^= 1; return n; };
      const r = proof(f, await f.helper.copyNext(f.requests.A), 'CONTENT'); assert.equal(r.io.verifiedScans, at === 1 ? 4 : 5);
      assert(copy(f).data.equals(source(f).data)); assert.equal(r.io.actualWriteBytes, f.requests.A.linked.executable.bytes);
    }
    const read = fixture(create); read.hooks.read = (tag, _, normal) => { if (tag === 'A:copy') throw Error('private readback'); return normal(); };
    proof(read, await read.helper.copyNext(read.requests.A), 'IO', 'A', true); assert(copy(read).data.length > 0);
  });
  add('P10', async () => {
    for (const tag of ['A:source', 'A:manifest', 'A:copy']) {
      const f = fixture(create); f.hooks.open = (at, _, normal) => { if (at === tag) throw Error('private open'); return normal(); };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO'); assert.equal(p.io.unknownClosures, 1);
      assert(f.handles.every(handle => handle.closeCalls === 1));
    }
    for (const field of ['identity', 'read', 'write', 'sync']) {
      let touched = 0; const f = fixture(create); f.hooks.open = (tag, _, normal) => {
        const result = normal(); if (tag === 'A:source') Object.defineProperty(result, field, { enumerable: true, get() { touched++; return () => {}; } }); return result;
      };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO'); assert.equal(touched, 0); assert.equal(p.io.closed, 1); assert.equal(p.io.unknownClosures, 0);
    }
    for (const absent of [true, false]) {
      let touched = 0; const f = fixture(create); f.hooks.open = (tag, _, normal) => {
        const result = normal(); if (tag === 'A:copy') { delete result.close; if (!absent) Object.defineProperty(result, 'close', { enumerable: true, get() { touched++; return () => {}; } }); } return result;
      };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO'); assert.equal(touched, 0);
      eq([p.io.opened, p.io.closeAttempts, p.io.closed, p.io.unknownClosures], [2, 2, 2, 1]);
    }
    // Additive calibration AFTER initial producer0b767133, BEFORE targeted
    // fixes: safe cleanup capture is broader than full-handle validation.
    for (const shape of ['nonenumerable-close', 'function-wrapper']) {
      const f = fixture(create); f.hooks.open = (tag, _, normal) => {
        const handle = normal(); if (tag !== 'A:source') return handle;
        if (shape === 'function-wrapper') return Object.defineProperty(function invalidWrapper() {}, 'close',
          { value: handle.close, enumerable: true });
        Object.defineProperty(handle, 'close', { value: handle.close, enumerable: false }); return handle;
      };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO');
      eq([p.io.openAttempts, p.io.opened, p.io.closeAttempts, p.io.closed, p.io.unknownClosures], [1, 1, 1, 1, 0]);
      assert.equal(p.io.verifiedScans, 0); assert(f.handles.every(handle => handle.closeCalls === 1 && handle.closed));
    }
  });
  add('P11', async () => {
    for (const tag of ['A:copy', 'A:manifest', 'A:source']) {
      const f = fixture(create); f.hooks.close = (at, _, normal) => { if (at === tag) throw Error('private close'); return normal(); };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'CLOSE');
      eq(f.calls.filter(x => x.method === 'close').map(x => x.tag), ['A:copy', 'A:manifest', 'A:source']);
      eq([p.io.closeAttempts, p.io.closed, p.io.unknownClosures], [3, 2, 1]); assert(f.handles.every(h => h.closeCalls === 1)); await used(f);
    }
    const prior = fixture(create); prior.hooks.open = (tag, _, normal) => { const h = normal(); if (tag === 'A:copy') source(prior).data[0] ^= 1; return h; };
    prior.hooks.close = () => { prior.time = 60001; throw Error('later cleanup'); };
    const p = proof(prior, await prior.helper.copyNext(prior.requests.A), 'CONTENT'); assert.equal(p.io.unknownClosures, 3);
    // Observe the first live failure at each successful close, without letting
    // a later close failure replace it or skip remaining reverse cleanup.
    for (const cause of ['DEADLINE', 'CANCELLED', 'CLOCK']) {
      const f = fixture(create); f.hooks.close = (tag, _, normal) => {
        if (tag === 'A:manifest') throw Error('later manifest close');
        const result = normal();
        if (tag === 'A:copy') {
          if (cause === 'DEADLINE') f.time = 60001;
          if (cause === 'CANCELLED') assert.equal(f.helper.cancel(), true);
          if (cause === 'CLOCK') f.hooks.now = () => NaN;
        }
        return result;
      };
      const failure = proof(f, await f.helper.copyNext(f.requests.A), cause);
      eq(f.calls.filter(entry => entry.method === 'close').map(entry => entry.tag), ['A:copy', 'A:manifest', 'A:source']);
      eq([failure.io.closeAttempts, failure.io.closed, failure.io.unknownClosures, failure.io.verifiedScans], [3, 2, 1, 6]);
      assert(f.handles.every(handle => handle.closeCalls === 1)); assert.equal(failure.unknownClosure, true); await used(f);
    }
  });
  add('P12', async () => {
    const idle = fixture(create); assert.equal(idle.helper.cancel(), true); assert.equal(idle.helper.cancel(), false);
    proof(idle, await idle.helper.copyNext(idle.requests.A), 'CANCELLED', null); eq(idle.calls, []); snapshot(idle, io(), null, true); await used(idle);
    let touched = 0; const noInput = fixture(create); noInput.helper.cancel();
    const getter = Object.defineProperty({}, 'candidate', { enumerable: true, get() { touched++; return 'A'; } });
    proof(noInput, await noInput.helper.copyNext(getter), 'CANCELLED', null); assert.equal(touched, 0); eq(noInput.calls, []);
    const template = fixture(create), count = trace('A', template.requests.A.linked.executable.bytes, template.requests.A.linked.manifest.bytes).length;
    for (let boundary = 0; boundary < count; boundary++) {
      const f = fixture(create); f.after = () => { if (f.calls.length - 1 === boundary) assert.equal(f.helper.cancel(), true); };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'CANCELLED');
      assert(f.calls.slice(boundary + 1).every(entry => entry.method === 'close'));
      assert.equal(p.io.closed, p.io.opened); assert.equal(p.io.unknownClosures, 0);
    }
    for (const method of ['read', 'write']) {
      const f = fixture(create), held = deferred(); let returned;
      f.hooks[method] = (_, __, normal) => { returned = () => normal(2); return held.promise; };
      const pending = f.helper.copyNext(f.requests.A); await until(() => returned !== undefined);
      f.helper.cancel(); held.resolve(returned()); const p = proof(f, await pending, 'CANCELLED');
      assert.equal(method === 'write' ? p.io.actualWriteBytes : p.io.actualReadBytes, 2);
    }
    const between = fixture(create), a = proof(between, await between.helper.copyNext(between.requests.A)); between.helper.cancel();
    const stopped = proof(between, await between.helper.copyNext(between.requests.B), 'CANCELLED', null); eq(stopped.io, io()); snapshot(between, a.io, null, true); await used(between);
  });
  add('P13', async () => {
    const inclusive = fixture(create); inclusive.after = () => { inclusive.time = 60000; }; proof(inclusive, await inclusive.helper.copyNext(inclusive.requests.A));
    for (const value of [-1, NaN, Infinity, '0']) {
      const f = fixture(create); f.time = value; const p = proof(f, await f.helper.copyNext(f.requests.A), 'CLOCK');
      eq(p.io, reserve(f.requests.A.linked.executable.bytes, f.requests.A.linked.manifest.bytes)); eq(f.calls, []);
    }
    const thrown = fixture(create); thrown.hooks.now = () => { throw Error('private clock'); };
    proof(thrown, await thrown.helper.copyNext(thrown.requests.A), 'CLOCK'); eq(thrown.calls, []);
    for (const method of ['read', 'write']) {
      const f = fixture(create); f.hooks[method] = (_, __, normal) => { const n = normal(); f.time = 60001; return n; };
      const p = proof(f, await f.helper.copyNext(f.requests.A), 'DEADLINE');
      assert.equal(method === 'write' ? p.io.actualWriteBytes : p.io.actualReadBytes, f.requests.A.linked.executable.bytes);
    }
    const backwards = fixture(create); backwards.time = 10; proof(backwards, await backwards.helper.copyNext(backwards.requests.A));
    backwards.time = 9; const failed = proof(backwards, await backwards.helper.copyNext(backwards.requests.B), 'CLOCK', 'B');
    eq(failed.io, reserve(backwards.requests.B.linked.executable.bytes, backwards.requests.B.linked.manifest.bytes));
    const fresh = fixture(create); fresh.time = 0.5; fresh.after = () => { fresh.time = 60000.5; };
    proof(fresh, await fresh.helper.copyNext(fresh.requests.A)); fresh.after = () => { fresh.time = 120000.5; };
    proof(fresh, await fresh.helper.copyNext(fresh.requests.B), null, 'B');
    const lateClose = fixture(create); lateClose.hooks.close = (_, __, normal) => { const value = normal(); lateClose.time = 60001; return value; };
    const ended = proof(lateClose, await lateClose.helper.copyNext(lateClose.requests.A), 'DEADLINE');
    assert.equal(ended.io.closed, 3); assert.equal(ended.io.unknownClosures, 0);
  });
  add('P14', async () => {
    const f = fixture(create), held = deferred(); let value;
    f.hooks.identify = (_, __, normal) => { value = normal(); return held.promise; };
    const pending = f.helper.copyNext(f.requests.A); await until(() => value !== undefined); const before = clone(f.helper.snapshot());
    await assert.rejects(() => f.helper.copyNext(), { message: BUSY }); eq(f.helper.snapshot(), before);
    delete f.hooks.identify; held.resolve(value); proof(f, await pending);
    const duplicate = proof(f, await f.helper.copyNext(f.requests.A), 'INPUT', null); eq(duplicate.io, io()); await used(f);
    const done = fixture(create); await done.helper.copyNext(done.requests.A); await done.helper.copyNext(done.requests.B); await used(done);
  });
  add('P15', async () => {
    // Factory capture must already be complete BEFORE the first copyNext.
    const immediate = fixture(create); immediate.config.targetRoot = 'D:/caller/changed-before-copy';
    immediate.adapter.identify = () => { throw Error('replaced before copy'); };
    immediate.adapter.open = () => { throw Error('replaced before copy'); };
    immediate.adapter.now = () => { throw Error('replaced before copy'); };
    proof(immediate, await immediate.helper.copyNext(immediate.requests.A));
    eq(immediate.calls.map(label), trace('A', immediate.requests.A.linked.executable.bytes, immediate.requests.A.linked.manifest.bytes));
    const f = fixture(create), original = clone(f.requests.A), held = deferred(); let release;
    f.hooks.identify = (_, __, normal) => { release = () => normal(); return held.promise; };
    const pending = f.helper.copyNext(f.requests.A); await until(() => release !== undefined);
    f.requests.A.linked.executable.sha256 = 'a'.repeat(64); f.requests.A.rootIdentity = 'changed';
    f.config.targetRoot = 'D:/caller/changed'; f.adapter.open = () => { throw Error('replaced'); }; f.adapter.now = () => { throw Error('replaced'); };
    f.adapter.identify = () => { throw Error('replaced'); };
    delete f.hooks.identify; held.resolve(release()); const result = await pending;
    const expected = f.requests.A; f.requests.A = original; proof(f, result); f.requests.A = expected;
    const saved = clone(result); assert.throws(() => { result.copy.bytes = 0; }, TypeError);
    const s = f.helper.snapshot(); assert.throws(() => { s.io.actualWriteBytes = 0; }, TypeError); eq(result, saved);
  });
  add('P16', async () => {
    const maxE = 67108864, maxM = 65536; assert.equal(2 * (4 * maxE + 2 * maxM), 537133056); assert.equal(2 * maxE, 134217728);
    const f = fixture(create); f.requests.A.linked.executable.bytes = maxE; f.requests.A.linked.manifest.bytes = maxM;
    f.hooks.identify = (_, __, normal) => ({ ...normal(), ordinary: false });
    const p = proof(f, await f.helper.copyNext(f.requests.A), 'IDENTITY'); eq(p.io, reserve(maxE, maxM));
    assert.equal(f.handles.length, 0); assert(!copy(f)); // declared reservation only, no64MiB allocation/read
  });
  add('P17', async () => {
    const makeBad = [r => null, r => ({ ...r, candidate: 'B' }), r => ({ ...r, extra: true }),
      r => ({ ...r, executableIdentity: r.manifestIdentity }), r => ({ ...r, rootIdentity: 1 }),
      r => ({ ...r, linked: { ...r.linked, executable: { sha256: '0'.repeat(64), bytes: 1 } } }),
      r => ({ ...r, linked: { ...r.linked, manifest: { sha256: r.linked.manifest.sha256, bytes: 65537 } } }),
      r => ({ ...r, linked: { ...r.linked, executable: { ...r.linked.executable, bytes: 67108865 } } }),
      r => ({ ...r, linked: { ...r.linked, executable: { ...r.linked.executable, bytes: 0 } } }),
      r => ({ ...r, linked: { ...r.linked, manifest: { ...r.linked.manifest, bytes: 0 } } })];
    for (const change of makeBad) {
      const f = fixture(create); const p = proof(f, await f.helper.copyNext(change(clone(f.requests.A))), 'INPUT', null);
      eq(p.io, io()); eq(f.calls, []); assert.equal(f.nowCalls, 0); await used(f);
    }
    // Additional post-producer/pre-fix source calibration: JavaScript's $
    // anchor must not make a65-character digest ending in newline valid.
    for (const part of ['executable', 'manifest']) for (const digest of ['a'.repeat(64) + '\n', '0'.repeat(64) + '\n']) {
      const f = fixture(create), request = clone(f.requests.A); request.linked[part].sha256 = digest;
      const p = proof(f, await f.helper.copyNext(request), 'INPUT', null);
      eq(p.io, io()); eq(f.calls, []); assert.equal(f.nowCalls, 0); await used(f);
    }
    let touched = 0; const f = fixture(create), bad = { ...f.requests.A }; Object.defineProperty(bad, 'candidate',
      { enumerable: true, get() { touched++; return 'A'; } }); proof(f, await f.helper.copyNext(bad), 'INPUT', null); assert.equal(touched, 0);
    const extra = fixture(create); proof(extra, await extra.helper.copyNext(extra.requests.A, 'extra'), 'INPUT', null); eq(extra.calls, []);
    const missing = fixture(create); proof(missing, await missing.helper.copyNext(), 'INPUT', null); eq(missing.calls, []);
  });
  add('P18', async () => {
    const f = fixture(create); proof(f, await f.helper.copyNext(f.requests.A)); keys(f.adapter, ['identify', 'open', 'now']);
    const allowed = new Set(['identify', 'open', 'stat', 'read', 'write', 'sync', 'close']); assert(f.calls.every(entry => allowed.has(entry.method)));
    assert(f.calls.filter(entry => entry.method === 'open').every(entry => entry.args.mode === (entry.tag.endsWith(':copy') ? 'wx+' : 'r')));
    assert(f.calls.filter(entry => entry.method === 'write').every(entry => entry.tag === 'A:copy'));
    assert.equal(typeof api.createWorkerArtifactPreembedCopyV1, 'function'); // presence only; NEVER invoked by this file
  });
  add('P19', async () => {
    const f = fixture(create), a = proof(f, await f.helper.copyNext(f.requests.A)); snapshot(f, a.io, 'B');
    f.hooks.sync = () => { throw Error('B sync refusal'); };
    const b = proof(f, await f.helper.copyNext(f.requests.B), 'IO', 'B'); snapshot(f, plus(a.io, b.io), null, true);
    assert.equal(b.io.verifiedScans, 3); assert(copy(f, 'B').data.equals(source(f, 'B').data)); await used(f);
  });
  add('P20', async () => {
    for (const failure of [false, true]) {
      const f = fixture(create); if (failure) f.hooks.identify = () => { throw Error('private path/error'); };
      const p = proof(f, await f.helper.copyNext(f.requests.A), failure ? 'IO' : null);
      const s = f.helper.snapshot(); frozen(s); keys(s, SNAP); const text = JSON.stringify({ proof: p, snapshot: s });
      assert(Buffer.byteLength(text) < 8192);
      for (const needle of ['D:/', 'C:/', 'root-A', 'source-A', 'manifest-A', 'private path/error', 'worker_artifact_manifest_v1']) assert(!text.includes(needle));
      for (const key of ['adopt', 'author', 'receipt', 'mt', 'delete', 'record', 'retry']) assert(!Object.hasOwn(p, key));
      assert.equal(p.qualified, false); assert.equal(p.linkQualification, false); assert.equal(p.closureComplete, false);
    }
    // A thrown foreign value is opaque. Looking through its prototype or
    // reading properties can itself throw; generic I/O failure needs neither.
    let touched = 0; const f = fixture(create), opaque = new Proxy(Object.create(null), {
      getPrototypeOf() { touched++; throw Error('opaque private prototype'); },
      get() { touched++; throw Error('opaque private property'); }
    });
    f.hooks.identify = () => { throw opaque; };
    const p = proof(f, await f.helper.copyNext(f.requests.A), 'IO');
    eq(p.io, reserve(f.requests.A.linked.executable.bytes, f.requests.A.linked.manifest.bytes));
    snapshot(f, p.io, null, true); assert.equal(touched, 0); assert.equal(f.handles.length, 0);
    assert(!f.calls.some(entry => entry.method === 'close')); assert(!JSON.stringify(p).includes('opaque private')); await used(f);
  });

  eq(cases.map(([id]) => id), Array.from({ length: 20 }, (_, i) => 'P' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: 'worker_artifact_preembed_copy_first_v1', executed: 20,
    passed: 20 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
