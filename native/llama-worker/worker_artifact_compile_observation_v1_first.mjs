// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST for contract f3cf4e8f. All tool and filesystem ports are in memory.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createWorkerArtifactOutputRootsV1ForTesting } from './worker_artifact_output_roots_v1.mjs';
import { createWorkerArtifactHeldOutputsV1ForTesting } from './worker_artifact_held_outputs_v1.mjs';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactCompileObservationV1';
const SNAP = ['version', 'kind', 'phase', 'started', 'offered', 'cancelled', 'writerUnknown', 'objectUnknown', 'stop'];
const REPORT = ['version', 'kind', 'context', 'status', 'code', 'started', 'offered', 'checks',
  'process', 'output', 'writerUnknown', 'objectUnknown', 'leaseClosed', 'linkAllowed', 'qualified'];
const STABLE = ['source', 'headers', 'tool', 'environment', 'normal', 'temp'];
const POLICY = { timeoutMs: 120000, drainMs: 5000, stdoutCap: 65536, stderrCap: 4096 };
const MARKER = '.locallore-output-owner-v1';
const eq = (actual, expected) => assert.deepEqual(actual, expected);
const keys = (value, wanted) => eq(Object.keys(value).sort(), [...wanted].sort());
const wire = value => JSON.stringify(value);
const sha = value => createHash('sha256').update(value).digest('hex');
const digest = value => sha(wire(value));
const encode = value => typeof value === 'string' ? value : wire(value);
const clone = value => JSON.parse(wire(value));

function frozen(value, omitSignal = false) {
  if (value && typeof value === 'object') {
    assert(Object.isFrozen(value));
    for (const [key, child] of Object.entries(value)) {
      if (!omitSignal || key !== 'signal') frozen(child, omitSignal);
    }
  }
}
function deferred() {
  let resolve;
  const promise = new Promise(done => { resolve = done; });
  return { promise, resolve };
}
async function until(predicate) {
  for (let tick = 0; tick < 2048; tick++) {
    if (predicate()) return;
    await Promise.resolve();
  }
  assert.fail('expected pending transition');
}
function opaque() {
  let inspected = 0;
  const trap = () => { inspected++; throw Error('synthetic private failure'); };
  return { value: new Proxy({}, { get: trap, getPrototypeOf: trap }), count: () => inspected };
}
function config() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b', targetRoot: 'D:/synthetic/target',
    sdkUmRoot: 'C:/synthetic-sdk/um' };
}

function fixture(create, pdb = false) {
  const cfg = config(), recipe = planWorkerArtifactComparisonV1(cfg);
  const authority = { attempt: sha('attempt'), baseline: sha('baseline'), closure: sha('closure'), grant: sha('grant') };
  const context = { attempt: authority.attempt, recipe: digest(recipe), baseline: authority.baseline,
    closure: authority.closure, grant: authority.grant };
  const stable = Object.fromEntries(STABLE.map(key => [key, sha(key)]));
  const object = Buffer.alloc(20);
  object.writeUInt16LE(0x8664);
  const roots = recipe.candidates.map((candidate, index) => ({
    ...candidate, identity: '11:' + (index + 2), marker: candidate.outputRoot + '/' + MARKER,
    markerIdentity: '11:' + (index + 10)
  }));
  const trace = [], journals = [], issued = {};
  const nodes = new Map([[cfg.targetRoot, { kind: 'directory', identity: '11:1' }]]);
  const f = { cfg, recipe, authority, context, object, roots, trace, journals, issued,
    signal: null, before: null, after: null, writer: null, output: null };
  const [a] = roots;
  function nodeAt(path, kind) {
    const node = nodes.get(path);
    assert(node && node.kind === kind);
    return node;
  }
  function list(path) {
    assert(roots.some(root => root.outputRoot === path));
    const prefix = path + '/';
    return [...nodes.keys()].filter(name => name.startsWith(prefix))
      .map(name => name.slice(prefix.length));
  }
  function fileFact(node, big) {
    return { identity: node.identity, ordinary: true,
      bytes: big ? BigInt(node.content.length) : node.content.length };
  }
  function read(node, buffer, offset, length, position) {
    if (position >= node.content.length) return 0;
    return node.content.copy(buffer, offset, position, Math.min(node.content.length, position + length));
  }
  function signalFor(signal) {
    assert(signal instanceof AbortSignal);
    f.signal ??= signal;
    assert.equal(signal, f.signal);
  }
  f.addFile = (candidate, role, content = Buffer.from('extra')) => {
    const row = roots[candidate], path = row[role];
    const offset = ['object', 'compilerPdb', 'executable', 'manifest', 'preEmbedCopy'].indexOf(role);
    assert(path && offset >= 0);
    nodes.set(path, { kind: 'file', identity: '11:' + (20 + 10 * candidate + offset), content: Buffer.from(content) });
  };
  const lease = createWorkerArtifactOutputRootsV1ForTesting(
    { config: cfg, attemptSha256: authority.attempt, parentIdentity: '11:1', maxBytes: 4096 }, {
      identify(path, kind) {
        const node = nodeAt(path, kind);
        return { identity: node.identity, ordinary: true, real: true, bytes: BigInt(node.content?.length ?? 0) };
      },
      mkdir(path) {
        const root = roots.find(row => row.outputRoot === path);
        assert(root && !nodes.has(path));
        nodes.set(path, { kind: 'directory', identity: root.identity });
        return 'created';
      },
      openMarker(path) {
        const root = roots.find(row => row.marker === path);
        assert(root && !nodes.has(path));
        const node = { kind: 'file', identity: root.markerIdentity, content: Buffer.alloc(0) };
        nodes.set(path, node);
        return {
          identity: () => fileFact(node, true),
          read: (...args) => read(node, ...args),
          write(buffer, offset, length, position) {
            assert.equal(position, node.content.length);
            node.content = Buffer.concat([node.content, buffer.subarray(offset, offset + length)]);
            return length;
          },
          sync() {},
          close() {}
        };
      },
      openDirectory(path) {
        const names = list(path);
        return { read: () => names.length ? { name: names.shift(), ordinary: true } : null, close() {} };
      },
      now: () => 0
    });
  const reader = createWorkerArtifactHeldOutputsV1ForTesting({ config: cfg }, {
    identifyRoot(path) {
      return { identity: nodeAt(path, 'directory').identity, ordinary: true, real: true };
    },
    identifyFile(path) {
      return { ...fileFact(nodeAt(path, 'file'), false), links: 1, modified: '5', changed: '6', real: true };
    },
    openRead(path) {
      assert.equal(path, a.object);
      const node = nodeAt(path, 'file');
      return {
        stat: () => ({ ...fileFact(node, false), links: 1, modified: '5', changed: '6' }),
        read(buffer, offset, length, position) {
          const normal = () => read(node, buffer, offset, length, position);
          return f.objectRead ? f.objectRead(normal, position) : normal();
        },
        close() { return f.objectClose?.(); }
      };
    },
    now: () => 0
  });

  const outputRoots = {
    async prepare() {
      trace.push('lease:prepare');
      const ready = await lease.prepare();
      f.before = f.prepareHook ? f.prepareHook(ready) : ready;
      return f.before;
    },
    async recheck() {
      trace.push('lease:recheck');
      const ready = await lease.recheck();
      f.after = f.rosterHook ? f.rosterHook(ready) : ready;
      return f.after;
    },
    cancel() {
      trace.push('lease:cancel');
      return lease.cancel();
    },
    async close() {
      trace.push('lease:close');
      const closed = await lease.close();
      return f.closeHook ? f.closeHook(closed) : closed;
    }
  };
  const outputReader = {
    async readNext(request, signal) {
      trace.push('reader');
      signalFor(signal);
      eq(clone(request), { index: 0, candidate: 'A', role: 'object', rootIdentity: a.identity,
        fileIdentity: nodeAt(a.object, 'file').identity, bytes: nodeAt(a.object, 'file').content.length });
      assert.equal(f.entry.snapshot().phase, 'read');
      assert.equal(f.entry.snapshot().objectUnknown, true);
      f.output = await reader.readNext(request, signal);
      return f.readerHook ? f.readerHook(f.output) : f.output;
    }
  };
  const ports = {
    check(request, signal) {
      const { when } = request;
      trace.push('check:' + when);
      signalFor(signal);
      eq(clone(request), { version: 1, context, index: 0, when,
        roster: when === 'admit' ? null : digest(when === 'before' ? f.before : f.after) });
      const proof = { version: 1, kind: 'worker_artifact_compile_check_v1', context, when,
        roster: request.roster, ...stable, storage: sha('storage:' + when), reserve: sha('reserve:' + when) };
      issued[when] = digest(proof);
      return encode(f.checkHook ? f.checkHook(proof, when) : proof);
    },
    async launch(request) {
      trace.push('launch');
      keys(request, ['version', 'context', 'index', 'step', 'policy', 'signal']);
      signalFor(request.signal);
      frozen(request, true);
      eq(clone({ ...request, signal: null }), { version: 1, context, index: 0, step: recipe.steps[0],
        policy: POLICY, signal: null });
      assert.equal(f.entry.snapshot().phase, 'launch');
      assert.equal(f.entry.snapshot().offered, true);
      assert.equal(f.entry.snapshot().writerUnknown, true);
      const normal = () => {
        f.addFile(0, 'object', f.invalidObject ? Buffer.alloc(4) : object);
        if (pdb) f.addFile(0, 'compilerPdb');
        const { attempt, recipe, baseline, closure } = context;
        const process = { version: 1, kind: 'worker_artifact_process_v1', attempt, recipe, baseline, closure,
          index: 0, pid: 123, closed: true, unknown: false, exitCode: 0, timedOut: false, overflow: false,
          killAttempted: false, ioError: false, elapsedMs: 11, stdoutBytes: 0, stderrBytes: 0,
          stdoutHash: sha(''), stderrHash: sha(''), processTreeContained: false };
        return { version: 1, kind: 'worker_artifact_compile_writer_v1', process, writersClosed: true,
          writerProof: sha('known synthetic closure') };
      };
      f.writer = f.launchHook ? await f.launchHook(normal) : normal();
      return encode(f.writer);
    },
    async journal(record) {
      const start = record.kind === 'worker_artifact_compile_observation_start_v1';
      trace.push(start ? 'journal:start' : 'journal:terminal');
      journals.push(record);
      frozen(record);
      if (start) eq(clone(record), { version: 1, kind: 'worker_artifact_compile_observation_start_v1',
        context, preflight: issued.admit, runCount: 1 });
      else assert.equal(record.kind, 'worker_artifact_compile_observation_v1');
      const ack = { version: 1, kind: 'worker_artifact_compile_journal_ack_v1', sha256: digest(record), stored: true };
      return encode(f.journalHook ? await f.journalHook(ack, start) : ack);
    }
  };
  f.spec = { config: cfg, authority, outputRoots, outputReader, ports };
  f.entry = create(f.spec);
  return f;
}

function snap(f, fields) {
  const value = f.entry.snapshot();
  keys(value, SNAP);
  frozen(value);
  eq(clone(value), { version: 1, kind: 'worker_artifact_compile_observation_snapshot_v1',
    phase: 'new', started: false, offered: false, cancelled: false,
    writerUnknown: false, objectUnknown: false, stop: null, ...fields });
}
function outcome(f, result, fields, retained = true) {
  keys(result, ['report', 'retained']);
  keys(result.report, REPORT);
  frozen(result);
  const report = { version: 1, kind: 'worker_artifact_compile_observation_v1', context: f.context,
    status: 'stopped', code: null, started: false, offered: false,
    checks: { admit: null, before: null, after: null }, process: null, output: null,
    writerUnknown: false, objectUnknown: false, leaseClosed: false, linkAllowed: false, qualified: false, ...fields };
  eq(clone(result), { report, retained });
  eq(clone(f.journals.at(-1)), report);
  assert(Buffer.byteLength(wire(result.report), 'utf8') <= 16384);
  for (const privateText of ['D:/synthetic', 'C:/synthetic', 'synthetic private failure']) {
    assert(!wire(result).includes(privateText));
  }
}
const beforeChecks = f => ({ admit: f.issued.admit, before: f.issued.before, after: null });
const ranBefore = f => ({ started: true, offered: true, checks: beforeChecks(f) });
const writerSeen = f => ({ ...ranBefore(f), process: f.writer });
const objectSeen = f => ({ ...writerSeen(f), output: f.output });
const used = f => assert.rejects(f.entry.run(), { message: PREFIX + 'Used' });

export async function runWorkerArtifactCompileObservationSelfchecksV1(api) {
  const create = api.createWorkerArtifactCompileObservationV1;
  const cases = [];
  const add = (id, run) => cases.push([id, run]);

  add('C01', async () => {
    keys(api, ['createWorkerArtifactCompileObservationV1']);
    const f = fixture(create);
    keys(f.entry, ['run', 'cancel', 'snapshot']);
    assert(Object.isFrozen(f.entry));
    snap(f, {});
    for (const change of [
      { authority: { ...f.authority, grant: '0'.repeat(64) } },
      { authority: { ...f.authority, extra: true } },
      { config: { ...f.cfg, targetRoot: 'C:/synthetic' } },
      { ports: { ...f.spec.ports, extra: true } },
      { outputRoots: Object.create(f.spec.outputRoots) },
      { outputReader: { readNext: null } }
    ]) assert.throws(() => create({ ...f.spec, ...change }), { message: PREFIX + 'Input' });
    let getterReads = 0;
    const bad = { ...f.spec.ports, get check() { getterReads++; return () => null; } };
    assert.throws(() => create({ ...f.spec, ports: bad }), { message: PREFIX + 'Input' });
    assert.equal(getterReads, 0);
    await assert.rejects(f.entry.run('extra'), { message: PREFIX + 'Input' });
    assert.throws(() => f.entry.cancel('extra'), { message: PREFIX + 'Input' });
    assert.throws(() => f.entry.snapshot('extra'), { message: PREFIX + 'Input' });
    eq(f.trace, []);
    assert.equal(f.entry.cancel(), true);
    assert.equal(f.entry.cancel(), false);
    outcome(f, await f.entry.run(), { code: 'CANCELLED' });
    eq(f.trace, ['journal:terminal']);
    await used(f);
  });

  add('C02', async () => {
    for (const pdb of [false, true]) {
      const f = fixture(create, pdb);
      const result = await f.entry.run();
      outcome(f, result, { ...objectSeen(f), status: 'observed', leaseClosed: true, checks: f.issued });
      eq(f.trace, ['check:admit', 'journal:start', 'lease:prepare', 'check:before', 'launch',
        'lease:recheck', 'reader', 'check:after', 'lease:close', 'journal:terminal']);
      assert.equal(f.before.observedBytes, '334');
      assert.equal(f.after.observedBytes, pdb ? '359' : '354');
      eq(f.output.file, { sha256: sha(f.object), bytes: 20 });
      eq(f.output.metadata, { directives: [], defaultLibraries: [] });
      eq(f.output.io, { reservedReadBytes: '42', actualReadBytes: '40', opened: 1, closed: 1, verifiedScans: 2 });
      snap(f, { phase: 'done', started: true, offered: true });
      assert.equal(f.entry.cancel(), false);
      await used(f);
      assert.equal(f.journals.length, 2);
    }
  });

  add('C03', async () => {
    for (const edit of [
      proof => wire(proof) + '\n',
      proof => ({ ...proof, headers: '0'.repeat(64) }),
      proof => ({ ...proof, context: { ...proof.context, grant: sha('wrong grant') } }),
      proof => ({ ...proof, roster: sha('unexpected roster') })
    ]) {
      const f = fixture(create);
      f.checkHook = edit;
      outcome(f, await f.entry.run(), { code: 'PREFLIGHT' });
      eq(f.trace, ['check:admit', 'journal:terminal']);
    }
    for (const edit of [ack => ({ ...ack, sha256: sha('wrong START hash') }), () => null]) {
      const f = fixture(create);
      f.journalHook = (ack, start) => start ? edit(ack) : ack;
      outcome(f, await f.entry.run(), { code: 'START', checks: { admit: f.issued.admit, before: null, after: null } });
      eq(f.trace, ['check:admit', 'journal:start', 'journal:terminal']);
    }
  });

  add('C04', async () => {
    const invalid = fixture(create);
    invalid.prepareHook = view => {
      const ready = clone(view);
      ready.roots[0].files.push({ name: 'main.cpp.obj', bytes: '1', identity: '11:20' });
      ready.observedBytes = '335';
      return ready;
    };
    outcome(invalid, await invalid.entry.run(), { code: 'LEASE', started: true, leaseClosed: true,
      checks: { admit: invalid.issued.admit, before: null, after: null } });
    eq(invalid.trace, ['check:admit', 'journal:start', 'lease:prepare', 'lease:close', 'journal:terminal']);

    const stale = fixture(create);
    stale.checkHook = (proof, when) => when === 'before' ? { ...proof, source: sha('changed source') } : proof;
    outcome(stale, await stale.entry.run(), { code: 'PREFLIGHT', started: true, leaseClosed: true,
      checks: { admit: stale.issued.admit, before: null, after: null } });
    eq(stale.trace, ['check:admit', 'journal:start', 'lease:prepare', 'check:before', 'lease:close', 'journal:terminal']);
  });

  add('C05', async () => {
    for (const [processEdit, closeWriters, code] of [
      [{ exitCode: 9 }, true, 'PROCESS'], [{ timedOut: true }, true, 'PROCESS'],
      [{ overflow: true }, true, 'PROCESS'], [{ killAttempted: true }, true, 'PROCESS'],
      [{}, false, 'CLOSURE'], [{ unknown: true }, true, 'CLOSURE'],
      [{ closed: false, exitCode: null }, true, 'CLOSURE'], [{ ioError: true }, true, 'CLOSURE']
    ]) {
      const f = fixture(create);
      f.launchHook = normal => {
        const writer = normal();
        Object.assign(writer.process, processEdit);
        writer.writersClosed = closeWriters;
        if (!closeWriters) writer.writerProof = null;
        return writer;
      };
      const known = code === 'PROCESS', result = await f.entry.run();
      outcome(f, result, { ...writerSeen(f), code, writerUnknown: !known, leaseClosed: known });
      assert(!f.trace.includes('reader'));
      assert(!f.trace.includes('lease:recheck'));
      assert.equal(f.trace.includes('lease:close'), known);
    }
    for (const edit of [
      writer => ({ ...writer, writerProof: null }),
      writer => ({ ...writer, process: { ...writer.process, processTreeContained: true } }),
      writer => ({ ...writer, process: { ...writer.process, stdoutBytes: POLICY.stdoutCap + 1 } }),
      writer => ({ ...writer, process: { ...writer.process, attempt: sha('foreign attempt') } })
    ]) {
      const f = fixture(create);
      f.launchHook = normal => edit(normal());
      outcome(f, await f.entry.run(), { ...ranBefore(f), code: 'CLOSURE', writerUnknown: true });
      assert(!f.trace.includes('lease:close'));
    }
    const opaqueWriter = fixture(create), error = opaque();
    opaqueWriter.launchHook = () => { throw error.value; };
    outcome(opaqueWriter, await opaqueWriter.entry.run(), { ...ranBefore(opaqueWriter), code: 'CLOSURE', writerUnknown: true });
    assert.equal(error.count(), 0);
    assert(!opaqueWriter.trace.includes('lease:close'));
  });

  add('C06', async () => {
    for (const extra of [[0, 'executable'], [0, 'manifest'], [0, 'preEmbedCopy'], [1, 'object']]) {
      const f = fixture(create);
      f.launchHook = normal => {
        const writer = normal();
        f.addFile(...extra);
        return writer;
      };
      const result = await f.entry.run();
      outcome(f, result, { ...writerSeen(f), code: 'ROSTER', leaseClosed: true });
      assert(!f.trace.includes('reader'));
    }
    for (const mutate of [
      view => { view.roots[0].identity = '11:91'; },
      view => { view.roots[1].files[0].identity = '11:92'; },
      view => { view.observedBytes = '355'; }
    ]) {
      const f = fixture(create);
      f.rosterHook = view => {
        const changed = clone(view);
        mutate(changed);
        return changed;
      };
      const result = await f.entry.run();
      outcome(f, result, { ...writerSeen(f), code: 'ROSTER', leaseClosed: true });
      assert(!f.trace.includes('reader'));
    }
  });

  add('C07', async () => {
    const coff = fixture(create);
    coff.invalidObject = true;
    const rejected = await coff.entry.run();
    assert.equal(coff.output.code, 'COFF');
    outcome(coff, rejected, { ...objectSeen(coff), code: 'OBJECT', leaseClosed: true });
    assert(!coff.trace.includes('check:after'));

    const unknown = fixture(create), error = opaque();
    unknown.objectClose = () => { throw error.value; };
    const refused = await unknown.entry.run();
    assert.equal(unknown.output.code, 'CLOSE');
    assert.equal(unknown.output.unknownClosure, true);
    outcome(unknown, refused, { ...objectSeen(unknown), code: 'OBJECT', objectUnknown: true });
    assert.equal(error.count(), 0);
    assert(!unknown.trace.includes('lease:close'));

    const malformed = fixture(create);
    malformed.readerHook = proof => ({ ...proof, candidate: 'B' });
    outcome(malformed, await malformed.entry.run(), { ...writerSeen(malformed), code: 'OBJECT', objectUnknown: true });
    assert(!malformed.trace.includes('lease:close'));
  });

  add('C08', async () => {
    const edits = [...STABLE.map(key => proof => ({ ...proof, [key]: sha('stale:' + key) })),
      proof => ({ ...proof, roster: sha('other roster') }),
      proof => ({ ...proof, reserve: '0'.repeat(64) }), () => null];
    for (const edit of edits) {
      const f = fixture(create);
      f.checkHook = (proof, when) => when === 'after' ? edit(proof) : proof;
      const result = await f.entry.run();
      outcome(f, result, { ...objectSeen(f), code: 'POSTFLIGHT', leaseClosed: true });
      assert.equal(f.journals.length, 2);
      assert.equal(f.trace.filter(value => value === 'check:after').length, 1);
    }
  });

  add('C09', async () => {
    for (const known of [true, false]) {
      const f = fixture(create), hold = deferred();
      let entered = false;
      f.launchHook = async normal => {
        entered = true;
        await hold.promise;
        const writer = normal();
        if (!known) {
          writer.writersClosed = false;
          writer.writerProof = null;
        }
        return writer;
      };
      const running = f.entry.run();
      running.catch(() => {});
      try {
        await until(() => entered);
        snap(f, { phase: 'launch', started: true, offered: true, writerUnknown: true });
        await used(f);
        assert.equal(f.entry.cancel(), true);
        assert.equal(f.entry.cancel(), false);
        assert.equal(f.signal.aborted, true);
        snap(f, { phase: 'launch', started: true, offered: true, writerUnknown: true,
          cancelled: true, stop: 'CANCELLED' });
        assert(f.trace.includes('lease:cancel'));
        assert(!f.trace.includes('lease:close'));
        eq(f.journals.map(row => row.kind), ['worker_artifact_compile_observation_start_v1']);
        hold.resolve();
        const result = await running;
        outcome(f, result, { ...writerSeen(f), code: 'CANCELLED', writerUnknown: !known, leaseClosed: known });
        assert(!f.trace.includes('reader'));
        assert.equal(f.trace.includes('lease:close'), known);
      } finally {
        hold.resolve();
      }
    }
  });

  add('C10', async () => {
    for (const known of [true, false]) {
      const f = fixture(create), hold = deferred();
      let entered = false;
      f.objectRead = async normal => {
        entered = true;
        await hold.promise;
        return normal();
      };
      if (!known) f.objectClose = () => { throw Error('synthetic private failure'); };
      const running = f.entry.run();
      running.catch(() => {});
      try {
        await until(() => entered);
        snap(f, { phase: 'read', started: true, offered: true, objectUnknown: true });
        assert.equal(f.entry.cancel(), true);
        assert.equal(f.signal.aborted, true);
        snap(f, { phase: 'read', started: true, offered: true, objectUnknown: true, cancelled: true, stop: 'CANCELLED' });
        assert(!f.trace.includes('lease:close'));
        assert.equal(f.journals.length, 1);
        hold.resolve();
        const result = await running;
        assert.equal(f.output.code, 'CANCELLED');
        assert.equal(f.output.unknownClosure, !known);
        outcome(f, result, { ...objectSeen(f), code: 'CANCELLED', objectUnknown: !known, leaseClosed: known });
        assert(!f.trace.includes('check:after'));
      } finally {
        hold.resolve();
      }
    }
    const f = fixture(create), hold = deferred();
    let entered = false;
    f.journalHook = async (ack, start) => {
      if (start) { entered = true; await hold.promise; }
      return ack;
    };
    const running = f.entry.run();
    running.catch(() => {});
    try {
      await until(() => entered);
      snap(f, { phase: 'start' });
      assert.equal(f.entry.cancel(), true);
      assert.equal(f.signal.aborted, true);
      hold.resolve();
      outcome(f, await running, { code: 'CANCELLED', started: true,
        checks: { admit: f.issued.admit, before: null, after: null } });
      eq(f.trace, ['check:admit', 'journal:start', 'journal:terminal']);
    } finally {
      hold.resolve();
    }
  });

  add('C11', async () => {
    const unretained = fixture(create);
    unretained.journalHook = (ack, start) => start ? ack : { ...ack, stored: false };
    const result = await unretained.entry.run();
    outcome(unretained, result,
      { ...objectSeen(unretained), status: 'observed', leaseClosed: true, checks: unretained.issued }, false);
    await used(unretained);
    assert.equal(unretained.journals.length, 2);

    const closure = fixture(create);
    closure.launchHook = normal => {
      const writer = normal();
      writer.process.exitCode = 9;
      return writer;
    };
    closure.closeHook = view => {
      const changed = clone(view);
      changed.roots[1].markerClosure = 'unknown';
      return changed;
    };
    const stopped = await closure.entry.run();
    outcome(closure, stopped, { ...writerSeen(closure), code: 'PROCESS' });
    assert.equal(closure.trace.filter(value => value === 'lease:close').length, 1);
    await used(closure);
    assert.equal(closure.journals.length, 2);
  });

  eq(cases.map(([id]) => id), Array.from({ length: 11 }, (_, index) => 'C' + String(index + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) {
    try { await run(); }
    catch { failed_case_ids.push(id); }
  }
  return { version: 1, kind: 'worker_artifact_compile_observation_first_v1', executed: 11,
    passed: 11 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
