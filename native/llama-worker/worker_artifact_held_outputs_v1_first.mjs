// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST for contract 560a2ac1. No top-level checks or filesystem ports.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { inspectLibraryInputs } from './library_inputs.mjs';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactHeldOutputsV1';
const API = ['createWorkerArtifactHeldOutputsV1', 'createWorkerArtifactHeldOutputsV1ForTesting'];
const CAP = 67108864, CHUNK = 65536;
const RESULT = ['version', 'kind', 'index', 'candidate', 'role', 'ok', 'code',
  'file', 'metadata', 'io', 'unknownClosure', 'ioUncertain'];
const SNAPSHOT = ['version', 'kind', 'next', 'pending', 'completed', 'stop',
  'io', 'unknownClosure', 'ioUncertain'];
const IO = ['reservedReadBytes', 'actualReadBytes', 'opened', 'closed', 'verifiedScans'];
const SEQUENCE = [
  [0, 'A', 'object'],
  [1, 'A', 'object'], [1, 'A', 'executable'], [1, 'A', 'manifest'],
  [2, 'A', 'object'], [2, 'A', 'executable'], [2, 'A', 'manifest'], [2, 'A', 'preEmbedCopy'],
  [3, 'B', 'object'],
  [4, 'B', 'object'], [4, 'B', 'executable'], [4, 'B', 'manifest'],
  [5, 'B', 'object'], [5, 'B', 'executable'], [5, 'B', 'manifest'], [5, 'B', 'preEmbedCopy'],
  [6, 'A', 'object'], [6, 'A', 'executable'], [6, 'B', 'object'], [6, 'B', 'executable']
];
const METADATA = { directives: ['/DEFAULTLIB:runtime'], defaultLibraries: ['runtime.lib'] };
const eq = (actual, expected) => assert.deepEqual(actual, expected);
const keys = (value, wanted) => eq(Object.keys(value).sort(), [...wanted].sort());
const sha = value => createHash('sha256').update(value).digest('hex');

function frozen(value) {
  if (value && typeof value === 'object') {
    assert(!Buffer.isBuffer(value));
    assert(Object.isFrozen(value));
    for (const child of Object.values(value)) frozen(child);
  }
}
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
async function until(predicate) {
  for (let tick = 0; tick < 512; tick++) {
    if (predicate()) return;
    await Promise.resolve();
  }
  assert.fail('expected pending transition');
}
function opaque() {
  let inspected = 0;
  const trap = () => { inspected++; throw Error('synthetic private detail'); };
  return { value: new Proxy({}, { get: trap, getPrototypeOf: trap }), count: () => inspected };
}
function config() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b', targetRoot: 'D:/synthetic/target',
    sdkUmRoot: 'C:/synthetic-sdk/um' };
}
function object(directives = '/DEFAULTLIB:runtime', big = false) {
  const text = Buffer.from(directives, 'ascii');
  const header = big ? 56 : 20;
  const bytes = Buffer.alloc(header + 40 + text.length);
  if (big) {
    bytes.writeUInt16LE(0xffff, 2);
    bytes.writeUInt16LE(2, 4);
    bytes.writeUInt16LE(0x8664, 6);
    Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex').copy(bytes, 12);
    bytes.writeUInt32LE(1, 44);
  } else {
    bytes.writeUInt16LE(0x8664);
    bytes.writeUInt16LE(1, 2);
  }
  bytes.write('.drectve', header, 8, 'ascii');
  bytes.writeUInt32LE(text.length, header + 16);
  bytes.writeUInt32LE(header + 40, header + 20);
  bytes.writeUInt32LE(0x200, header + 36);
  text.copy(bytes, header + 40);
  return bytes;
}
function archive(body) {
  const member = 'm.obj/'.padEnd(16) + '0'.padEnd(12) + ''.padEnd(6) + ''.padEnd(6) +
    '100644'.padEnd(8) + String(body.length).padEnd(10) + '\x60\n';
  assert.equal(member.length, 60);
  return Buffer.concat([Buffer.from('!<arch>\n' + member, 'ascii'), body, Buffer.alloc(body.length % 2, 10)]);
}
function imported() {
  const payload = Buffer.from('aa\0b\0', 'ascii'), header = Buffer.alloc(20);
  header.writeUInt16LE(0xffff, 2);
  header.writeUInt16LE(0x8664, 6);
  header.writeUInt32LE(payload.length, 12);
  header.writeUInt16LE(4, 18);
  return Buffer.concat([header, payload]);
}

function fixture(create) {
  const cfg = config(), recipe = planWorkerArtifactComparisonV1(cfg);
  const roots = new Map(), files = new Map(), trace = [], hooks = new Map();
  const roles = ['object', 'executable', 'manifest', 'preEmbedCopy'];
  for (const [index, candidate] of recipe.candidates.entries()) {
    roots.set(candidate.outputRoot, { identity: '11:' + (2 + index), ordinary: true, real: true });
    for (const [offset, role] of roles.entries()) {
      files.set(candidate[role], { identity: '11:' + (20 + 10 * index + offset), ordinary: true,
        real: true, links: 1, modified: '9223372036854775807', changed: '-9223372036854775808',
        content: role === 'object' ? object() : Buffer.from(candidate.id + ' synthetic ' + role) });
    }
  }
  const f = { cfg, trace, hooks, clock: 0, shortRead: Infinity, controller: new AbortController() };
  function port(key, normal, details = {}) {
    const entry = { key, ...details };
    trace.push(entry);
    return hooks.has(key) ? hooks.get(key)(normal, entry) : normal();
  }
  function named(file) {
    const { content, ...fact } = file;
    return { ...fact, bytes: content.length };
  }
  const adapter = {
    identifyRoot(path) {
      return port('root', () => {
        assert(roots.has(path));
        return { ...roots.get(path) };
      }, { path });
    },
    identifyFile(path) {
      return port('file', () => {
        assert(files.has(path));
        return named(files.get(path));
      }, { path });
    },
    openRead(path) {
      return port('open', () => {
        const file = files.get(path);
        assert(file);
        return {
          stat() {
            return port('stat', () => {
              const { real, ...fact } = named(file);
              return fact;
            }, { path });
          },
          read(buffer, offset, length, position) {
            return port('read', () => {
              assert(Buffer.isBuffer(buffer));
              assert(length > 0 && length <= CHUNK);
              if (position >= file.content.length) return 0;
              const end = Math.min(file.content.length, position + length, position + f.shortRead);
              return file.content.copy(buffer, offset, position, end);
            }, { path, buffer, offset, length, position });
          },
          close() { return port('close', () => {}, { path }); }
        };
      }, { path });
    },
    now() { return hooks.has('now') ? hooks.get('now')() : f.clock; }
  };
  f.adapter = adapter;
  f.create = () => create({ config: cfg }, adapter);
  f.select = (ordinal = 0) => {
    const [index, candidate, role] = SEQUENCE[ordinal];
    const row = recipe.candidates[candidate === 'A' ? 0 : 1];
    const path = row[role], root = row.outputRoot, file = files.get(path);
    return { path, root, file, request: { index, candidate, role, rootIdentity: roots.get(root).identity,
      fileIdentity: file.identity, bytes: file.content.length } };
  };
  return f;
}
const calls = (f, key) => f.trace.filter(entry => entry.key === key);
const io = (changes = {}) => ({ reservedReadBytes: '0', actualReadBytes: '0',
  opened: 0, closed: 0, verifiedScans: 0, ...changes });
const reserve = bytes => String(2 * bytes + 2);
const full = bytes => io({ reservedReadBytes: reserve(bytes), actualReadBytes: String(2 * bytes),
  opened: 1, closed: 1, verifiedScans: 2 });

function checkSnapshot(reader, expected) {
  const result = reader.snapshot();
  keys(result, SNAPSHOT);
  keys(result.io, IO);
  frozen(result);
  eq(result, { version: 1, kind: 'worker_artifact_held_outputs_snapshot_v1',
    next: 0, pending: null, completed: 0, stop: null, io: io(),
    unknownClosure: false, ioUncertain: false, ...expected });
  return result;
}
function checkResult(result, request, fields) {
  keys(result, RESULT);
  keys(result.io, IO);
  frozen(result);
  eq(result, { version: 1, kind: 'worker_artifact_held_output_v1',
    index: request?.index ?? null, candidate: request?.candidate ?? null, role: request?.role ?? null,
    ok: false, code: null, file: null, metadata: null, io: io(),
    unknownClosure: false, ioUncertain: false, ...fields });
  assert(!JSON.stringify(result).includes('D:/synthetic'));
}
async function through(f, reader, ordinal) {
  for (let index = 0; index < ordinal; index++) {
    const result = await reader.readNext(f.select(index).request, f.controller.signal);
    assert.equal(result.ok, true);
  }
}
async function terminal(reader, request, signal) {
  await assert.rejects(reader.readNext(request, signal), { message: PREFIX + 'Stopped' });
}

export async function runWorkerArtifactHeldOutputsSelfchecksV1(api) {
  const create = api.createWorkerArtifactHeldOutputsV1ForTesting;
  const cases = [];
  const add = (id, run) => cases.push([id, run]);

  add('H01', () => {
    keys(api, API);
    for (const name of API) assert.equal(typeof api[name], 'function');
    const f = fixture(create), reader = f.create();
    keys(reader, ['readNext', 'snapshot']);
    assert(Object.isFrozen(reader));
    checkSnapshot(reader, {});
    for (const [spec, adapter] of [
      [null, f.adapter], [{ config: f.cfg, extra: true }, f.adapter],
      [{ config: { ...f.cfg, targetRoot: 'C:/synthetic' } }, f.adapter],
      [{ config: f.cfg }, { ...f.adapter, openRead: false }],
      [{ config: f.cfg }, { ...f.adapter, extra: true }],
      [{ config: f.cfg }, Object.create(f.adapter)]
    ]) assert.throws(() => create(spec, adapter), { message: PREFIX + 'Input' });
    let getters = 0;
    const bad = { ...f.adapter, get now() { getters++; return () => 0; } };
    assert.throws(() => create({ config: f.cfg }, bad), { message: PREFIX + 'Input' });
    assert.equal(getters, 0);
    eq(f.trace, []);
  });

  add('H02', async () => {
    const f = fixture(create), reader = f.create();
    f.adapter.openRead = () => { throw Error('adapter changed after setup'); };
    let reserved = 0, actual = 0;
    for (let ordinal = 0; ordinal < SEQUENCE.length; ordinal++) {
      const { request, file, path, root } = f.select(ordinal);
      f.trace.length = 0;
      checkResult(await reader.readNext(request, f.controller.signal), request, { ok: true,
        file: { sha256: sha(file.content), bytes: request.bytes },
        metadata: request.index === 0 || request.index === 3 ? METADATA : null, io: full(request.bytes) });
      eq(calls(f, 'open').map(call => call.path), [path]);
      eq(calls(f, 'close').map(call => call.path), [path]);
      eq(calls(f, 'root').map(call => call.path), [root, root]);
      eq(calls(f, 'file').map(call => call.path), [path, path]);
      eq(calls(f, 'read').map(call => [call.path, call.position, call.length]), [
        [path, 0, request.bytes], [path, request.bytes, 1],
        [path, 0, request.bytes], [path, request.bytes, 1]
      ]);
      reserved += 2 * request.bytes + 2;
      actual += 2 * request.bytes;
      const completed = ordinal + 1;
      checkSnapshot(reader, { next: completed < 20 ? completed : null, completed,
        io: io({ reservedReadBytes: String(reserved), actualReadBytes: String(actual),
          opened: completed, closed: completed, verifiedScans: completed * 2 }) });
    }
    await terminal(reader, f.select().request, f.controller.signal);
    assert.equal(calls(f, 'open').length, 1);
  });

  add('H03', async () => {
    const classic = object(), big = object('/DEFAULTLIB:runtime', true), oneMember = archive(classic);
    const imports = imported();
    eq(inspectLibraryInputs(classic), { objects: 1, imports: 0, ...METADATA });
    eq(inspectLibraryInputs(big), { objects: 1, imports: 0, ...METADATA });
    eq(inspectLibraryInputs(oneMember), { objects: 1, imports: 0, ...METADATA });
    eq(inspectLibraryInputs(imports), { objects: 0, imports: 1, directives: [], defaultLibraries: [] });
    const wrongMachine = object();
    wrongMachine.writeUInt16LE(0x14c);
    const many = count => object(Array.from({ length: count }, (_, index) => '/DEFAULTLIB:lib' + index).join(' '));
    const byteHeavy = object('/ALTERNATENAME:' + 'a'.repeat(8200));
    assert.equal(inspectLibraryInputs(many(33)).defaultLibraries.length, 33);
    assert(Buffer.byteLength(JSON.stringify(inspectLibraryInputs(byteHeavy))) > 8192);
    for (const [payload, accepts] of [
      [big, true], [many(32), true], [oneMember, false], [imports, false], [wrongMachine, false],
      [object('/LIBPATH:escape'), false], [Buffer.alloc(4), false], [many(33), false], [byteHeavy, false]
    ]) {
      const f = fixture(create), reader = f.create();
      f.select().file.content = payload;
      const { request } = f.select();
      const result = await reader.readNext(request, f.controller.signal);
      if (accepts) {
        const { directives, defaultLibraries } = inspectLibraryInputs(payload);
        checkResult(result, request, { ok: true, file: { sha256: sha(payload), bytes: payload.length },
          metadata: { directives, defaultLibraries }, io: full(payload.length) });
      } else {
        checkResult(result, request, { code: 'COFF', io: full(payload.length) });
        await terminal(reader, request, f.controller.signal);
      }
      assert.equal(calls(f, 'open').length, 1);
      assert.equal(calls(f, 'close').length, 1);
    }
  });

  add('H04', async () => {
    for (const change of [
      { index: 1 }, { candidate: 'B' }, { role: 'executable' }, { extra: true }, { bytes: 0 },
      { bytes: CAP + 1 }, { bytes: 1.5 }, { fileIdentity: '11:2' }, { rootIdentity: '12:2' },
      { rootIdentity: '011:2' }, { fileIdentity: '11:0' }, { fileIdentity: '11:20\n' },
      { fileIdentity: '11:18446744073709551616' }
    ]) {
      const f = fixture(create), reader = f.create();
      const result = await reader.readNext({ ...f.select().request, ...change }, f.controller.signal);
      checkResult(result, null, { code: 'REQUEST' });
      checkSnapshot(reader, { next: null, stop: 'REQUEST' });
      eq(f.trace, []);
    }
    for (const signal of [null, undefined, { aborted: false, addEventListener() {} }]) {
      const f = fixture(create), reader = f.create();
      checkResult(await reader.readNext(f.select().request, signal), null, { code: 'REQUEST' });
      eq(f.trace, []);
    }
    const f = fixture(create), reader = f.create();
    let getters = 0;
    const bad = { ...f.select().request, get bytes() { getters++; return 20; } };
    checkResult(await reader.readNext(bad, f.controller.signal), null, { code: 'REQUEST' });
    assert.equal(getters, 0);
    const mismatch = fixture(create), held = mismatch.create();
    await through(mismatch, held, 1);
    mismatch.trace.length = 0;
    checkResult(await held.readNext(mismatch.select(1).request, new AbortController().signal), null, { code: 'REQUEST' });
    eq(mismatch.trace, []);

    for (const length of [65536, 65537]) {
      const manifest = fixture(create), stage = manifest.create();
      await through(manifest, stage, 3);
      manifest.trace.length = 0;
      manifest.select(3).file.content = Buffer.alloc(length, 0x61);
      const { request, file } = manifest.select(3);
      const result = await stage.readNext(request, manifest.controller.signal);
      if (length === 65536) {
        checkResult(result, request, { ok: true, file: { sha256: sha(file.content), bytes: length }, io: full(length) });
      } else {
        checkResult(result, null, { code: 'REQUEST' });
        eq(manifest.trace, []);
      }
    }
  });

  add('H05', async () => {
    for (const [key, edit] of [
      ['root', { ordinary: false }], ['root', { real: false }], ['root', { identity: '11:99' }],
      ['file', { ordinary: false }], ['file', { real: false }], ['file', { links: 2 }],
      ['file', { identity: '11:99' }], ['file', { bytes: 1 }], ['file', { modified: '01' }],
      ['file', { changed: '-0' }], ['file', { changed: '-9223372036854775809' }]
    ]) {
      const f = fixture(create), reader = f.create();
      f.hooks.set(key, normal => ({ ...normal(), ...edit }));
      const { request } = f.select();
      checkResult(await reader.readNext(request, f.controller.signal), request,
        { code: 'IDENTITY', io: io({ reservedReadBytes: reserve(request.bytes) }) });
      eq(calls(f, 'open'), []);
    }
    for (const at of [1, 2]) {
      const f = fixture(create), reader = f.create();
      let stats = 0;
      f.hooks.set('stat', normal => ++stats === at ? { ...normal(), changed: '-2' } : normal());
      const { request } = f.select();
      checkResult(await reader.readNext(request, f.controller.signal), request, { code: 'IDENTITY',
        io: io({ reservedReadBytes: reserve(request.bytes), opened: 1, closed: 1,
          actualReadBytes: at === 1 ? '0' : String(request.bytes) }) });
      assert.equal(calls(f, 'read').length, at === 1 ? 0 : 2);
    }
    for (const key of ['root', 'file']) {
      const f = fixture(create), reader = f.create();
      let read = 0;
      f.hooks.set(key, normal => ++read === 1 ? normal() : { ...normal(), identity: '11:99' });
      const { request } = f.select();
      checkResult(await reader.readNext(request, f.controller.signal), request,
        { code: 'IDENTITY', io: full(request.bytes) });
    }
  });

  add('H06', async () => {
    const f = fixture(create), reader = f.create();
    await through(f, reader, 2);
    f.trace.length = 0;
    f.shortRead = 10000;
    f.select(2).file.content = Buffer.alloc(70001, 0x61);
    const { request, file } = f.select(2);
    checkResult(await reader.readNext(request, f.controller.signal), request,
      { ok: true, file: { sha256: sha(file.content), bytes: request.bytes }, io: full(request.bytes) });
    const oneScan = [0, 10000, 20000, 30000, 40000, 50000, 60000, 70000, 70001];
    eq(calls(f, 'read').map(call => call.position), [...oneScan, ...oneScan]);
    assert(calls(f, 'read').every(call => call.length <= CHUNK));
    eq(calls(f, 'read').filter(call => call.position === request.bytes).map(call => call.length), [1, 1]);
    assert.equal(calls(f, 'open').length, 1);
    assert.equal(calls(f, 'close').length, 1);
  });

  add('H07', async () => {
    const f = fixture(create), reader = f.create();
    let scans = 0;
    f.hooks.set('read', (normal, call) => {
      const n = normal();
      if (call.position === 0 && ++scans === 2) call.buffer[call.offset] ^= 1;
      return n;
    });
    const { request } = f.select();
    checkResult(await reader.readNext(request, f.controller.signal), request,
      { code: 'CONTENT', io: full(request.bytes) });
    assert.equal(scans, 2);
    checkSnapshot(reader, { next: null, stop: 'CONTENT', io: full(request.bytes) });
  });

  add('H08', async () => {
    for (const count of [0, -1, NaN, Infinity, 1.5, '1', Number.MAX_SAFE_INTEGER]) {
      const f = fixture(create), reader = f.create();
      f.hooks.set('read', () => count);
      const { request } = f.select();
      checkResult(await reader.readNext(request, f.controller.signal), request,
        { code: count === 0 ? 'CONTENT' : 'IO', ioUncertain: count !== 0,
          io: io({ reservedReadBytes: reserve(request.bytes), opened: 1, closed: 1,
            actualReadBytes: count === Number.MAX_SAFE_INTEGER ? String(count) : '0' }) });
      assert.equal(calls(f, 'read').length, 1);
    }
    const f = fixture(create), reader = f.create();
    const { request } = f.select();
    f.hooks.set('read', (normal, call) => call.position === request.bytes ? 1 : normal());
    checkResult(await reader.readNext(request, f.controller.signal), request, { code: 'CONTENT',
      io: io({ reservedReadBytes: reserve(request.bytes), actualReadBytes: String(request.bytes + 1),
        opened: 1, closed: 1 }) });
    assert.equal(calls(f, 'read').length, 2);
  });

  add('H09', async () => {
    const f = fixture(create), reader = f.create();
    f.controller.abort();
    f.hooks.set('now', () => NaN);
    checkResult(await reader.readNext(f.select().request, f.controller.signal), f.select().request, { code: 'CANCELLED' });
    checkSnapshot(reader, { next: null, stop: 'CANCELLED' });
    eq(f.trace, []);

    const between = fixture(create), active = between.create();
    await through(between, active, 1);
    between.trace.length = 0;
    between.controller.abort();
    const { bytes } = between.select().request;
    checkSnapshot(active, { next: null, completed: 1, stop: 'CANCELLED', io: full(bytes) });
    await terminal(active, between.select(1).request, between.controller.signal);
    eq(between.trace, []);
  });

  add('H10', async () => {
    for (const [begin, later, code] of [[0, 3999, null], [0, 4000, 'DEADLINE'],
      [0, NaN, 'CLOCK'], [0, Infinity, 'CLOCK'], [1, 0, 'CLOCK'], [0, -1, 'CLOCK']]) {
      const f = fixture(create), reader = f.create();
      f.clock = begin;
      f.hooks.set('root', normal => { f.clock = later; return normal(); });
      const { request, file } = f.select();
      const result = await reader.readNext(request, f.controller.signal);
      if (code === null) {
        checkResult(result, request, { ok: true, file: { sha256: sha(file.content), bytes: request.bytes },
          metadata: METADATA, io: full(request.bytes) });
      } else {
        checkResult(result, request, { code, io: io({ reservedReadBytes: reserve(request.bytes) }) });
        eq(calls(f, 'open'), []);
      }
    }
    const f = fixture(create), reader = f.create();
    await through(f, reader, 1);
    f.clock = 3999;
    assert.equal((await reader.readNext(f.select(1).request, f.controller.signal)).ok, true);
    f.trace.length = 0;
    f.clock = 3998;
    const { request } = f.select(2);
    checkResult(await reader.readNext(request, f.controller.signal), request, { code: 'CLOCK' });
    eq(f.trace, []);
  });

  add('H11', async () => {
    const f = fixture(create), reader = f.create(), hold = deferred();
    let entered = false, blocked = 0, sharedLater = 0;
    f.controller.signal.addEventListener('abort', event => {
      blocked++;
      event.stopImmediatePropagation();
    }, { once: true });
    f.controller.signal.addEventListener('abort', () => { sharedLater++; }, { once: true });
    f.hooks.set('open', async normal => {
      entered = true;
      await hold.promise;
      const held = normal(), wrapper = function () {};
      Object.defineProperty(wrapper, 'close', { value: held.close });
      return wrapper;
    });
    const { request } = f.select();
    const operation = reader.readNext(request, f.controller.signal);
    operation.catch(() => {});
    try {
      await until(() => entered);
      await assert.rejects(reader.readNext(request, f.controller.signal), { message: PREFIX + 'Busy' });
      f.controller.abort();
      assert.equal(blocked, 1);
      assert.equal(sharedLater, 0);
      checkSnapshot(reader, { next: null, pending: 0, stop: 'CANCELLED',
        io: io({ reservedReadBytes: reserve(request.bytes) }) });
      hold.resolve();
      checkResult(await operation, request, { code: 'CANCELLED',
        io: io({ reservedReadBytes: reserve(request.bytes), opened: 1, closed: 1 }) });
      assert.equal(calls(f, 'open').length, 1);
      assert.equal(calls(f, 'close').length, 1);
      eq(calls(f, 'stat'), []);
      eq(calls(f, 'read'), []);
    } finally {
      hold.resolve();
    }
  });

  add('H12', async () => {
    for (const valid of [true, false]) {
      const f = fixture(create), reader = f.create(), hold = deferred();
      f.shortRead = 7;
      let entered = false;
      const { request } = f.select();
      f.hooks.set('read', async normal => {
        entered = true;
        await hold.promise;
        return valid ? normal() : Number.MAX_SAFE_INTEGER;
      });
      const operation = reader.readNext(request, f.controller.signal);
      operation.catch(() => {});
      try {
        await until(() => entered);
        f.clock = NaN;
        f.controller.abort();
        checkSnapshot(reader, { next: null, pending: 0, stop: 'CANCELLED',
          io: io({ reservedReadBytes: reserve(request.bytes), opened: 1 }) });
        hold.resolve();
        checkResult(await operation, request, { code: 'CANCELLED', ioUncertain: !valid,
          io: io({ reservedReadBytes: reserve(request.bytes),
            actualReadBytes: valid ? '7' : String(Number.MAX_SAFE_INTEGER), opened: 1, closed: 1 }) });
        assert.equal(calls(f, 'read').length, 1);
        assert.equal(calls(f, 'close').length, 1);
      } finally {
        hold.resolve();
      }
    }
  });

  add('H13', async () => {
    for (const action of ['root', 'open', 'read', 'close']) {
      const f = fixture(create), reader = f.create(), error = opaque();
      f.hooks.set(action, () => { throw error.value; });
      const { request } = f.select();
      const evidence = action === 'close' ? { ...full(request.bytes), closed: 0 } :
        io({ reservedReadBytes: reserve(request.bytes), ...(action === 'read' ? { opened: 1, closed: 1 } : {}) });
      checkResult(await reader.readNext(request, f.controller.signal), request, {
        code: action === 'close' ? 'CLOSE' : 'IO', io: evidence,
        unknownClosure: action === 'close' || action === 'open', ioUncertain: action === 'read' });
      assert.equal(error.count(), 0);
    }
    const f = fixture(create), reader = f.create();
    f.hooks.set('close', normal => { normal(); f.clock = 4000; });
    const { request } = f.select();
    checkResult(await reader.readNext(request, f.controller.signal), request,
      { code: 'DEADLINE', io: full(request.bytes) });
  });

  add('H14', async () => {
    for (const primary of ['CANCELLED', 'IDENTITY']) {
      const f = fixture(create), reader = f.create(), hold = deferred(), error = opaque();
      let entered = false;
      if (primary === 'IDENTITY') f.hooks.set('stat', normal => ({ ...normal(), links: 2 }));
      f.hooks.set('close', async () => {
        entered = true;
        await hold.promise;
        throw error.value;
      });
      const { request } = f.select(), operation = reader.readNext(request, f.controller.signal);
      operation.catch(() => {});
      try {
        await until(() => entered);
        f.controller.abort();
        const evidence = primary === 'IDENTITY' ? io({ reservedReadBytes: reserve(request.bytes), opened: 1 }) :
          { ...full(request.bytes), closed: 0 };
        checkSnapshot(reader, { next: null, pending: 0, stop: primary, io: evidence });
        await assert.rejects(reader.readNext(request, f.controller.signal), { message: PREFIX + 'Busy' });
        hold.resolve();
        checkResult(await operation, request, { code: primary, unknownClosure: true, io: evidence });
        await terminal(reader, request, f.controller.signal);
        assert.equal(calls(f, 'close').length, 1);
        assert.equal(error.count(), 0);
      } finally {
        hold.resolve();
      }
    }
    for (const method of ['read', 'close']) {
      const f = fixture(create), reader = f.create(), closeKnown = method !== 'close';
      f.hooks.set('open', normal => {
        const held = normal();
        delete held[method];
        return held;
      });
      const { request } = f.select();
      checkResult(await reader.readNext(request, f.controller.signal), request, { code: 'IO', unknownClosure: !closeKnown,
        io: io({ reservedReadBytes: reserve(request.bytes), opened: Number(closeKnown), closed: Number(closeKnown) }) });
      assert.equal(calls(f, 'close').length, Number(closeKnown));
    }
  });

  eq(cases.map(([id]) => id), Array.from({ length: 14 }, (_, index) => 'H' + String(index + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) {
    try { await run(); }
    catch { failed_case_ids.push(id); }
  }
  return { version: 1, kind: 'worker_artifact_held_outputs_first_v1', executed: 14,
    passed: 14 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
