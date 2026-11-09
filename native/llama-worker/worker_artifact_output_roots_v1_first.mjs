// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST for contract 92a531d7. All cases use in-memory ports.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const INPUT = 'WorkerArtifactOutputRootsV1Input';
const STATE = 'WorkerArtifactOutputRootsV1State';
const BUSY = 'WorkerArtifactOutputRootsV1Busy';
const API = ['createWorkerArtifactOutputRootsV1', 'createWorkerArtifactOutputRootsV1ForTesting'];
const METHODS = ['prepare', 'recheck', 'cancel', 'close', 'snapshot'];
const SNAP = ['version', 'kind', 'qualified', 'state', 'pending', 'stop',
  'rechecks', 'withinBudget', 'observedBytes', 'roots'];
const ROOT = ['candidate', 'creation', 'identity', 'marker', 'markerClosure',
  'directoryClosure', 'complete', 'files'];
const MARKER = '.locallore-output-owner-v1';
const MAX = 67108864;
const U64 = (1n << 64n) - 1n;
const OUTPUTS = ['object', 'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'];
const eq = (actual, expected) => assert.deepEqual(actual, expected);
const keys = (value, wanted) => eq(Object.keys(value).sort(), [...wanted].sort());

function frozen(value) {
  if (value && typeof value === 'object') {
    assert(Object.isFrozen(value));
    for (const child of Object.values(value)) frozen(child);
  }
}
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
function config() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b', targetRoot: 'D:/synthetic/target',
    sdkUmRoot: 'C:/synthetic-sdk/um' };
}
function fixture(create) {
  const spec = { config: config(), attemptSha256: 'a'.repeat(64), parentIdentity: '5:1', maxBytes: MAX };
  const recipe = planWorkerArtifactComparisonV1(spec.config);
  const digest = createHash('sha256').update(JSON.stringify(recipe)).digest('hex');
  const roots = recipe.candidates.map((candidate, index) => ({
    candidate: candidate.id, path: candidate.outputRoot, identity: '5:' + (index + 2),
    markerIdentity: '5:' + (index + 10), markerPath: candidate.outputRoot + '/' + MARKER,
    markerBytes: Buffer.from(['locallore-worker-artifact-owner-v1', spec.attemptSha256, digest, candidate.id, ''].join('\n')),
    outputPaths: OUTPUTS.map(key => candidate[key])
  }));
  const [a, b] = roots;
  const nodes = new Map([[spec.config.targetRoot, { identity: '5:1', kind: 'directory' }]]);
  const calls = [];
  const f = { spec, roots, a, b, nodes, calls, clock: 0, hooks: new Map(),
    maxMarkerWrite: Infinity, maxMarkerRead: Infinity, callableHandles: false };
  function port(key, path, normal, extra = {}) {
    const call = { key, path, ...extra };
    calls.push(call);
    const hook = f.hooks.get(key);
    return hook ? hook(normal, call) : normal();
  }
  function fact(path) {
    const node = nodes.get(path);
    assert(node, 'unexpected mock path');
    return { identity: node.identity, bytes: node.bytes ?? BigInt(node.content?.length ?? 0),
      ordinary: node.ordinary ?? true };
  }
  function handle(entries) {
    const owner = f.callableHandles ? function () {} : Object.create(null);
    for (const [name, run] of Object.entries(entries)) {
      Object.defineProperty(owner, name, { configurable: true, value: function (...args) {
        assert.equal(this, owner);
        return run(...args);
      } });
    }
    return owner;
  }
  const adapter = {
    identify(path, kind) {
      return port('identify', path, () => ({ ...fact(path), real: true,
        ordinary: nodes.get(path).kind === kind && fact(path).ordinary }), { kind });
    },
    mkdir(path) {
      return port('mkdir', path, () => {
        const root = roots.find(item => item.path === path);
        assert(root);
        if (nodes.has(path)) return 'exists';
        nodes.set(path, { identity: root.identity, kind: 'directory' });
        return 'created';
      });
    },
    openMarker(path) {
      return port('openMarker', path, () => {
        const root = roots.find(item => item.markerPath === path);
        assert(root);
        assert(nodes.has(root.path));
        assert(!nodes.has(path), 'mock exclusive create');
        const node = { identity: root.markerIdentity, kind: 'file', content: Buffer.alloc(0) };
        nodes.set(path, node);
        return handle({
          identity: () => port('markerStat', path, () => ({ identity: node.identity,
            ordinary: node.ordinary ?? true, bytes: BigInt(node.content.length) })),
          read: (buffer, offset, length, position) => port('markerRead', path, () => {
            const end = Math.min(node.content.length, position + length, position + f.maxMarkerRead);
            return end <= position ? 0 : node.content.copy(buffer, offset, position, end);
          }, { offset, length, position }),
          write: (buffer, offset, length, position) => port('markerWrite', path, () => {
            assert.equal(position, node.content.length);
            const part = buffer.subarray(offset, offset + Math.min(f.maxMarkerWrite, length));
            node.content = Buffer.concat([node.content, part]);
            return part.length;
          }, { offset, length, position, buffer }),
          sync: () => port('markerSync', path, () => {}),
          close: () => port('markerClose', path, () => {})
        });
      });
    },
    openDirectory(path) {
      return port('openDirectory', path, () => {
        assert(nodes.get(path)?.kind === 'directory');
        const prefix = path + '/';
        const names = [...nodes.keys()].filter(name => name.startsWith(prefix) && !name.slice(prefix.length).includes('/'));
        let index = 0;
        return handle({
          read: () => port('directoryRead', path, () => {
            const name = names[index++];
            return name === undefined ? null : { name: name.slice(prefix.length), ordinary: nodes.get(name).kind === 'file' };
          }),
          close: () => port('directoryClose', path, () => {})
        });
      });
    },
    now: () => f.clock
  };
  f.adapter = adapter;
  f.create = () => create(spec, adapter);
  f.file = (root, index, bytes = 1n, identity = '5:' + (20 + index + (root === b ? 10 : 0))) => {
    const path = root.outputPaths[index];
    nodes.set(path, { identity, bytes, kind: 'file' });
    return path;
  };
  return f;
}
function only(f, key) { return f.calls.filter(call => call.key === key).map(call => call.path); }
function stopped(result, code) {
  assert.equal(result.state, 'Stopped');
  if (code !== undefined) assert.equal(result.stop, code);
  else assert.equal(typeof result.stop, 'string');
  assert.equal(result.pending, null);
  assert.equal(result.withinBudget, false);
}
async function ready(lease) {
  const snapshot = await lease.prepare();
  assert.equal(snapshot.state, 'Ready');
  assert.equal(snapshot.pending, null);
  assert.equal(snapshot.stop, null);
  assert.equal(snapshot.withinBudget, true);
  return snapshot;
}
function shape(result) {
  keys(result, SNAP);
  assert.equal(result.version, 1);
  assert.equal(result.kind, 'worker_artifact_output_roots_v1');
  assert.equal(result.qualified, false);
  eq(result.roots.map(row => row.candidate), ['A', 'B']);
  for (const row of result.roots) {
    keys(row, ROOT);
    for (const fact of row.files) keys(fact, ['name', 'identity', 'bytes']);
  }
  frozen(result);
}
function markerFiles(root) {
  return [{ name: MARKER, identity: root.markerIdentity, bytes: String(root.markerBytes.length) }];
}
function trapError() {
  let inspections = 0;
  const value = new Proxy({}, { get() { inspections++; throw Error('private path'); },
    getPrototypeOf() { inspections++; throw Error('private path'); } });
  return { value, count: () => inspections };
}

export async function runWorkerArtifactOutputRootsSelfchecksV1(api) {
  const create = api.createWorkerArtifactOutputRootsV1ForTesting;
  const cases = [];
  const add = (id, run) => cases.push([id, run]);

  add('R01', async () => {
    keys(api, API);
    for (const name of API) assert.equal(typeof api[name], 'function');
    const f = fixture(create);
    const lease = f.create();
    keys(lease, METHODS);
    assert(Object.isFrozen(lease));
    shape(lease.snapshot());
    eq(lease.snapshot(), { version: 1, kind: 'worker_artifact_output_roots_v1', qualified: false,
      state: 'New', pending: null, stop: null, rechecks: 0, withinBudget: false, observedBytes: '0',
      roots: ['A', 'B'].map(candidate => ({ candidate, creation: 'unattempted', identity: null,
        marker: 'unattempted', markerClosure: 'none', directoryClosure: 'none', complete: false, files: [] })) });
    for (const invalid of [
      { maxBytes: 0 }, { maxBytes: MAX + 1 }, { maxBytes: 1.5 },
      { attemptSha256: '0'.repeat(64) }, { attemptSha256: 'A'.repeat(64) },
      { attemptSha256: 'a'.repeat(64) + '\n' }, { parentIdentity: '01:1' },
      { parentIdentity: '1:0' }, { parentIdentity: '1:1\n' }, { parentIdentity: '1:' + (U64 + 1n) },
      { config: { ...f.spec.config, targetRoot: 'C:/synthetic/target' } }, { extra: true },
      { [Symbol('extra')]: true }
    ]) assert.throws(() => create({ ...f.spec, ...invalid }, f.adapter), { message: INPUT });
    let getters = 0;
    const bad = { ...f.adapter, get now() { getters++; return () => 0; } };
    assert.throws(() => create(f.spec, bad), { message: INPUT });
    assert.equal(getters, 0);
    await assert.rejects(lease.recheck(), { message: STATE });
    await assert.rejects(lease.prepare('path'), { message: STATE });
    await assert.rejects(lease.close('path'), { message: STATE });
    assert.throws(() => lease.snapshot('path'), { message: STATE });
    assert.throws(() => lease.cancel('path'), { message: STATE });
    assert.equal((await lease.close()).state, 'Closed');
    eq(lease.cancel(), lease.snapshot());
    eq(f.calls, []);
  });

  add('R02', async () => {
    const f = fixture(create);
    f.maxMarkerWrite = 13;
    f.maxMarkerRead = 11;
    f.callableHandles = true;
    const lease = f.create();
    f.adapter.identify = () => { throw Error('adapter method changed after construction'); };
    const result = await ready(lease);
    shape(result);
    eq(only(f, 'mkdir'), [f.a.path, f.b.path]);
    eq(only(f, 'openMarker'), [f.a.markerPath, f.b.markerPath]);
    eq(only(f, 'markerSync'), [f.a.markerPath, f.b.markerPath]);
    eq(only(f, 'directoryRead'), [f.a.path, f.a.path, f.b.path, f.b.path]);
    eq(only(f, 'directoryClose'), [f.a.path, f.b.path]);
    eq(only(f, 'markerClose'), []);
    for (const [index, root] of f.roots.entries()) {
      eq(result.roots[index], { candidate: root.candidate, creation: 'created', identity: root.identity,
        marker: 'created', markerClosure: 'open', directoryClosure: 'closed', complete: true,
        files: markerFiles(root) });
      eq(f.nodes.get(root.markerPath).content, root.markerBytes);
      const reads = f.calls.filter(call => call.key === 'markerRead' && call.path === root.markerPath);
      assert(reads.some(call => call.position === root.markerBytes.length && call.length === 1));
    }
    assert.equal(result.observedBytes, String(f.a.markerBytes.length + f.b.markerBytes.length));
    assert(!JSON.stringify(result).includes('D:/synthetic'));
    assert(!JSON.stringify(result).includes(f.spec.attemptSha256));
    const closed = await lease.close();
    eq(only(f, 'markerClose'), [f.b.markerPath, f.a.markerPath]);
    assert.equal(closed.withinBudget, false);
    assert.equal(closed.observedBytes, result.observedBytes);
    eq(await lease.close(), closed);
    eq(only(f, 'markerClose'), [f.b.markerPath, f.a.markerPath]);
  });

  add('R03', async () => {
    const f = fixture(create);
    const lease = f.create();
    const original = await ready(lease);
    f.calls.length = 0;
    for (const root of f.roots) {
      for (let index = OUTPUTS.length - 1; index >= 0; index--) f.file(root, index, BigInt(index + 1));
    }
    const result = await lease.recheck();
    shape(result);
    assert.equal(result.state, 'Ready');
    assert.equal(result.rechecks, 1);
    assert.equal(result.withinBudget, true);
    assert.equal(result.observedBytes, String(BigInt(original.observedBytes) + 56n));
    eq(result.roots.map(row => row.files.length), [8, 8]);
    eq(only(f, 'directoryRead'), [...Array(9).fill(f.a.path), ...Array(9).fill(f.b.path)]);
    for (const [index, root] of f.roots.entries()) {
      eq(result.roots[index].files, [...markerFiles(root), ...root.outputPaths.map((path, i) => ({
        name: path.slice(root.path.length + 1), identity: f.nodes.get(path).identity, bytes: String(i + 1)
      }))]);
    }
    for (const key of ['mkdir', 'openMarker', 'markerWrite', 'markerSync', 'markerClose']) eq(only(f, key), []);
    await lease.close();
  });

  add('R04', async () => {
    for (const index of [0, 1]) {
      const f = fixture(create);
      const present = f.roots[index];
      const foreign = { identity: '5:40', kind: 'directory' };
      f.nodes.set(present.path, foreign);
      const lease = f.create();
      const result = await lease.prepare();
      stopped(result, 'Exists');
      assert.equal(result.roots[index].creation, 'exists');
      assert.equal(result.roots[index].identity, null);
      assert.equal(f.nodes.get(present.path), foreign);
      eq(only(f, 'mkdir'), f.roots.slice(0, index + 1).map(root => root.path));
      eq(only(f, 'openMarker'), f.roots.slice(0, index).map(root => root.markerPath));
      if (index === 1) {
        assert.equal(result.roots[0].creation, 'created');
        eq(f.nodes.get(f.a.markerPath).content, f.a.markerBytes);
      }
      await assert.rejects(lease.prepare(), { message: STATE });
      await lease.close();
      assert.equal(f.nodes.get(present.path), foreign);
    }
    const f = fixture(create);
    const error = trapError();
    f.hooks.set('mkdir', normal => { normal(); throw error.value; });
    const lease = f.create();
    const result = await lease.prepare();
    stopped(result, 'IO');
    assert.equal(result.roots[0].creation, 'unknown');
    assert(f.nodes.has(f.a.path));
    eq(only(f, 'mkdir'), [f.a.path]);
    eq(only(f, 'openMarker'), []);
    assert.equal(error.count(), 0);
    await lease.close();
  });

  add('R05', async () => {
    for (const change of [
      (f, fact, call) => call.path === f.spec.config.targetRoot ? { ...fact, real: false } : fact,
      (f, fact, call) => call.path === f.a.path ? { ...fact, ordinary: false } : fact,
      (f, fact, call) => call.path === f.a.path ? { ...fact, identity: '6:2' } : fact,
      (f, fact, call) => call.path === f.a.path ? { ...fact, identity: f.spec.parentIdentity } : fact,
      (f, fact, call) => call.path === f.a.markerPath ? { ...fact, identity: '5:61' } : fact,
      (f, fact, call) => call.path === f.b.path ? { ...fact, identity: f.a.markerIdentity } : fact
    ]) {
      const f = fixture(create);
      f.hooks.set('identify', (normal, call) => change(f, normal(), call));
      const lease = f.create();
      stopped(await lease.prepare(), 'Identity');
      eq(only(f, 'openDirectory'), []);
      await lease.close();
    }
    const f = fixture(create);
    f.hooks.set('mkdir', normal => {
      const result = normal();
      f.nodes.get(f.spec.config.targetRoot).identity = '5:99';
      return result;
    });
    const lease = f.create();
    const result = await lease.prepare();
    stopped(result, 'Identity');
    assert.equal(result.roots[0].creation, 'created');
    eq(only(f, 'openMarker'), []);
    await lease.close();
  });

  add('R06', async () => {
    for (const [key, change] of [
      ['markerWrite', () => 0],
      ['markerWrite', (normal, call) => call.length + 1],
      ['markerRead', () => 0],
      ['markerRead', (normal, call) => call.length + 1],
      ['markerRead', (normal, call) => call.position > 0 ? 1 : normal()],
      ['markerWrite', (normal, call) => { call.buffer.fill(0); return normal(); }],
      ['markerStat', normal => ({ ...normal(), bytes: 1n })]
    ]) {
      const f = fixture(create);
      f.hooks.set(key, change);
      const lease = f.create();
      const result = await lease.prepare();
      stopped(result);
      assert.equal(result.roots[0].marker, 'created');
      assert.equal(result.roots[0].markerClosure, 'open');
      eq(only(f, 'openMarker'), [f.a.markerPath]);
      assert(f.nodes.has(f.a.markerPath));
      await lease.close();
      eq(only(f, 'markerClose'), [f.a.markerPath]);
      assert(f.nodes.has(f.a.markerPath));
    }
    const f = fixture(create);
    const lease = f.create();
    await ready(lease);
    f.nodes.get(f.a.markerPath).content[0] ^= 1;
    const result = await lease.recheck();
    stopped(result, 'Marker');
    assert.equal(result.roots[0].complete, false);
    assert.equal(result.roots[0].markerClosure, 'open');
    await lease.close();
  });

  add('R07', async () => {
    const f = fixture(create);
    const lease = f.create();
    f.hooks.set('mkdir', (normal, call) => {
      const result = normal();
      if (call.path === f.b.path) f.file(f.a, 0);
      return result;
    });
    const result = await lease.prepare();
    stopped(result, 'Roster');
    assert.equal(result.roots[0].complete, false);
    assert(f.nodes.has(f.a.outputPaths[0]));
    await lease.close();

    for (const entry of [
      { name: '../escape', ordinary: true }, { name: 'locallore-author-worker.exp', ordinary: true },
      { name: 'MAIN.CPP.OBJ', ordinary: true }, { name: 'main.cpp.obj', ordinary: false },
      { name: 'main.cpp.obj', ordinary: true, extra: 1 }, 'main.cpp.obj'
    ]) {
      const test = fixture(create);
      const active = test.create();
      await ready(active);
      test.calls.length = 0;
      test.hooks.set('directoryRead', () => entry);
      const refused = await active.recheck();
      stopped(refused, 'Roster');
      assert.equal(refused.roots[0].complete, false);
      assert.equal(refused.roots[0].directoryClosure, 'closed');
      eq(only(test, 'identify').filter(path => ![test.spec.config.targetRoot, test.a.path, test.a.markerPath].includes(path)), []);
      eq(only(test, 'directoryRead'), [test.a.path]);
      await active.close();
    }
  });

  add('R08', async () => {
    for (const [setup, code] of [
      [f => f.hooks.set('directoryRead', () => null), 'Roster'],
      [f => f.hooks.set('directoryRead', () => ({ name: MARKER, ordinary: true })), 'Roster'],
      [f => { f.file(f.a, 0, 1n, f.b.markerIdentity); }, 'Identity'],
      [f => { f.file(f.a, 0, 1n, f.b.identity); }, 'Identity'],
      [f => { f.file(f.a, 0); f.file(f.b, 0, 1n, '5:20'); }, 'Identity'],
      [f => { f.file(f.a, 0, 1n, '6:20'); }, 'Identity'],
      [f => { const path = f.file(f.a, 0); f.nodes.get(path).ordinary = false; }, 'Identity']
    ]) {
      const f = fixture(create);
      const lease = f.create();
      await ready(lease);
      setup(f);
      const result = await lease.recheck();
      stopped(result, code);
      assert(result.roots.some(root => !root.complete));
      await lease.close();
    }
  });

  add('R09', async () => {
    const f = fixture(create);
    f.spec.maxBytes = f.a.markerBytes.length + f.b.markerBytes.length - 1;
    const lease = f.create();
    stopped(await lease.prepare(), 'Budget');
    eq(f.calls, []);
    await lease.close();
    const g = fixture(create);
    const exact = g.create();
    const initial = await ready(exact);
    g.file(g.a, 0, BigInt(MAX) - BigInt(initial.observedBytes));
    const edge = await exact.recheck();
    assert.equal(edge.withinBudget, true);
    assert.equal(edge.observedBytes, String(MAX));
    g.file(g.a, 0, U64);
    const overflow = await exact.recheck();
    stopped(overflow, 'Budget');
    assert.equal(overflow.observedBytes, String(BigInt(g.a.markerBytes.length) + U64));
    assert.equal(overflow.roots[0].files.at(-1).bytes, String(U64));
    assert.equal(overflow.roots[0].complete, false);
    assert.equal(overflow.roots[1].complete, false);
    eq(overflow.roots[1].files, []);
    const closed = await exact.close();
    assert.equal(closed.observedBytes, overflow.observedBytes);
  });

  add('R10', async () => {
    for (const failure of [false, true]) {
      const f = fixture(create);
      const lease = f.create();
      await ready(lease);
      f.calls.length = 0;
      const error = trapError();
      if (failure) f.hooks.set('directoryRead', () => { throw error.value; });
      f.hooks.set('directoryClose', () => { throw error.value; });
      const result = await lease.recheck();
      stopped(result, failure ? 'IO' : 'Closure');
      assert.equal(result.roots[0].directoryClosure, 'unknown');
      assert.equal(result.roots[0].markerClosure, 'open');
      assert.equal(result.roots[0].complete, false);
      eq(only(f, 'directoryClose'), [f.a.path]);
      await lease.close();
      eq(only(f, 'directoryClose'), [f.a.path]);
      eq(only(f, 'markerClose'), [f.b.markerPath, f.a.markerPath]);
      assert.equal(error.count(), 0);
      assert(!JSON.stringify(result).includes('private path'));
    }
  });

  add('R11', async () => {
    for (const key of ['openMarker', 'openDirectory']) {
      const f = fixture(create);
      f.hooks.set(key, normal => {
        const handle = normal();
        delete handle.read;
        return handle;
      });
      const lease = f.create();
      const result = await lease.prepare();
      stopped(result);
      if (key === 'openMarker') eq(only(f, 'markerClose'), []);
      else eq(only(f, 'directoryClose'), [f.a.path]);
      const closed = await lease.close();
      assert.equal(closed.roots[0].markerClosure, 'closed');
      eq(only(f, 'markerClose'), key === 'openMarker' ? [f.a.markerPath] : [f.b.markerPath, f.a.markerPath]);
    }
    const f = fixture(create);
    f.hooks.set('openMarker', normal => {
      const handle = normal();
      delete handle.close;
      return handle;
    });
    const lease = f.create();
    const result = await lease.prepare();
    stopped(result);
    assert.equal(result.roots[0].markerClosure, 'unknown');
    assert.equal((await lease.close()).roots[0].markerClosure, 'unknown');
  });

  add('R12', async () => {
    for (const key of ['mkdir', 'openMarker', 'openDirectory']) {
      const f = fixture(create);
      const entered = deferred(), release = deferred();
      f.hooks.set(key, async normal => {
        entered.resolve();
        await release.promise;
        return normal();
      });
      const lease = f.create();
      const preparing = lease.prepare();
      await Promise.race([entered.promise, preparing.then(() => { throw Error('operation settled before hook'); })]);
      assert.equal(lease.snapshot().pending, 'prepare');
      await assert.rejects(lease.prepare(), { message: BUSY });
      await assert.rejects(lease.recheck(), { message: BUSY });
      await assert.rejects(lease.close(), { message: BUSY });
      const cancelled = lease.cancel();
      assert.equal(cancelled.state, 'Stopped');
      assert.equal(cancelled.stop, 'Cancelled');
      assert.equal(cancelled.pending, 'prepare');
      release.resolve();
      const result = await preparing;
      stopped(result, 'Cancelled');
      assert.equal(result.roots[0].creation, 'created');
      if (key === 'mkdir') {
        assert.equal(result.roots[0].marker, 'unattempted');
        eq(only(f, 'openMarker'), []);
      } else {
        assert.equal(result.roots[0].marker, 'created');
        assert.equal(result.roots[0].markerClosure, 'open');
      }
      if (key === 'openDirectory') {
        eq(only(f, 'directoryRead'), []);
        eq(only(f, 'directoryClose'), [f.a.path]);
        assert.equal(result.roots[0].directoryClosure, 'closed');
      }
      await lease.close();
      assert(f.nodes.has(f.a.path));
    }
  });

  add('R13', async () => {
    for (const clock of [3999, 4000, -1, NaN, Infinity, 0]) {
      const f = fixture(create);
      f.clock = clock === 0 ? 1 : 0;
      f.hooks.set('mkdir', normal => {
        const result = normal();
        f.clock = clock;
        return result;
      });
      const lease = f.create();
      const result = await lease.prepare();
      if (clock === 3999) assert.equal(result.withinBudget, true);
      else {
        stopped(result, clock === 4000 ? 'Deadline' : 'Clock');
        assert.equal(result.roots[0].creation, 'created');
        eq(only(f, 'openMarker'), []);
      }
      await lease.close();
    }
    const f = fixture(create);
    const lease = f.create();
    await ready(lease);
    f.hooks.set('directoryClose', normal => { normal(); f.clock = 4000; });
    const result = await lease.recheck();
    stopped(result, 'Deadline');
    assert.equal(result.roots[0].directoryClosure, 'closed');
    assert.equal(result.roots[0].complete, false);
    await lease.close();
  });

  add('R14', async () => {
    const f = fixture(create);
    const lease = f.create();
    await ready(lease);
    const entered = deferred(), release = deferred(), error = trapError();
    f.hooks.set('markerClose', async (normal, call) => {
      if (call.path === f.b.markerPath) {
        entered.resolve();
        await release.promise;
        throw error.value;
      }
      return normal();
    });
    f.clock = NaN;
    const closing = lease.close();
    await Promise.race([entered.promise, closing.then(() => { throw Error('close settled before hook'); })]);
    assert.equal(lease.snapshot().pending, 'close');
    await assert.rejects(lease.close(), { message: BUSY });
    const during = lease.cancel();
    assert.equal(during.state, 'Stopped');
    assert.equal(during.stop, 'Cancelled');
    assert.equal(during.pending, 'close');
    release.resolve();
    const result = await closing;
    assert.equal(result.state, 'Closed');
    assert.equal(result.pending, null);
    assert.equal(result.stop, 'Cancelled');
    assert.equal(result.roots[1].markerClosure, 'unknown');
    assert.equal(result.roots[0].markerClosure, 'closed');
    eq(only(f, 'markerClose'), [f.b.markerPath, f.a.markerPath]);
    eq(await lease.close(), result);
    eq(lease.cancel(), result);
    eq(only(f, 'markerClose'), [f.b.markerPath, f.a.markerPath]);
    assert.equal(error.count(), 0);
  });

  add('R15', async () => {
    const f = fixture(create);
    const lease = f.create();
    await ready(lease);
    for (let index = 1; index <= 32; index++) {
      const result = await lease.recheck();
      assert.equal(result.rechecks, index);
      assert.equal(result.withinBudget, true);
    }
    f.calls.length = 0;
    const limited = await lease.recheck();
    stopped(limited, 'Limit');
    assert.equal(limited.rechecks, 32);
    eq(f.calls, []);
    await assert.rejects(lease.recheck(), { message: STATE });
    await lease.close();
  });

  eq(cases.map(([id]) => id), Array.from({ length: 15 }, (_, i) => 'R' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) {
    try { await run(); }
    catch { failed_case_ids.push(id); }
  }
  return { version: 1, kind: 'worker_artifact_output_roots_first_v1', executed: 15,
    passed: 15 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
