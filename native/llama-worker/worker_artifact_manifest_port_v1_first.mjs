// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST for contract 189e880d. All ports and files are synthetic.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { createWorkerArtifactCoordinatorV1 } from './worker_artifact_coordinator_v1.mjs';
import { createWorkerArtifactOutputRootsV1ForTesting } from './worker_artifact_output_roots_v1.mjs';
import { createWorkerArtifactPreembedCopyV1ForTesting } from './worker_artifact_preembed_copy_v1.mjs';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const INPUT = 'WorkerArtifactManifestPortV1Input';
const STOPPED = 'WorkerArtifactManifestPortV1Stopped';
const BUSY = 'WorkerArtifactManifestPortV1Busy';
const CAP = 67108864;
const MARKER = '.locallore-output-owner-v1';
const CHECKS = ['source', 'headers', 'tools', 'inputs', 'physicalRoots', 'environment', 'searchOrder',
  'noShadow', 'ownership', 'exclusiveOutputs', 'storage', 'reserve', 'authority', 'normalWorker'];
const SNAPSHOT = ['version', 'kind', 'pending', 'next', 'completed', 'stop', 'copyCode', 'uncertain'];
const OUTPUTS = ['object', 'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'];
const MANIFEST_KIND = 'worker_artifact_manifest_v1';
const eq = (actual, expected) => assert.deepEqual(actual, expected);
const keys = (value, names) => eq(Object.keys(value).sort(), [...names].sort());
const wire = value => JSON.stringify(value);
const hash = value => createHash('sha256').update(value).digest('hex');
const checks = () => Object.fromEntries(CHECKS.map(key => [key, true]));
const fileFact = content => ({ sha256: hash(content), bytes: content.length });
const clone = value => JSON.parse(wire(value));

function assertFrozen(value) {
  if (value && typeof value === 'object') {
    assert(Object.isFrozen(value));
    for (const child of Object.values(value)) assertFrozen(child);
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
  assert.fail('expected synthetic transition did not occur');
}
function manualClock() {
  const live = new Map(), durations = [];
  let next = 1;
  return {
    live, durations,
    ports: {
      set(run, ms) {
        const token = next++;
        live.set(token, { run, ms });
        durations.push(ms);
        return token;
      },
      clear(token) { live.delete(token); }
    },
    fire(ms) {
      const [token, entry] = [...live].find(([, value]) => value.ms === ms) ?? [];
      assert(entry);
      live.delete(token);
      entry.run();
    }
  };
}
function config() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b', targetRoot: 'D:/synthetic/target',
    sdkUmRoot: 'C:/synthetic-sdk/um' };
}
function opaque() {
  let inspected = 0;
  const trap = () => { inspected++; throw Error('synthetic private detail'); };
  return { value: new Proxy({}, { get: trap, getPrototypeOf: trap }), count: () => inspected };
}

function fixture(create, maxBytes = CAP, actualHelpers = false) {
  const cfg = config(), recipe = planWorkerArtifactComparisonV1(cfg);
  const context = { attempt: 'a'.repeat(64), recipe: hash(wire(recipe)),
    baseline: 'b'.repeat(64), closure: 'c'.repeat(64) };
  const parentIdentity = '11:1';
  const markerContent = id => Buffer.from(
    ['locallore-worker-artifact-owner-v1', context.attempt, context.recipe, id, ''].join('\n'));
  const content = {
    object: Buffer.from('same synthetic object'),
    executable: Buffer.from('same synthetic linked worker'),
    manifest: Buffer.from('same synthetic manifest'),
    final: Buffer.from('same synthetic embedded worker')
  };
  const facts = Object.fromEntries(Object.entries(content).map(([key, data]) => [key, fileFact(data)]));
  const nodes = new Map([[cfg.targetRoot, { identity: parentIdentity, kind: 'directory' }]]);
  const trace = [], copyOpens = [], offers = [], launched = [];
  const clock = manualClock();
  const f = { cfg, recipe, context, facts, trace, copyOpens, offers, launched, clock, recorded: null,
    recheckHook: null, copyHook: null, onLeaseCancel: null, onCopyCancel: null, lease: null };
  const roots = recipe.candidates.map((candidate, index) => ({
    ...candidate, identity: '11:' + (index + 2), markerPath: candidate.outputRoot + '/' + MARKER,
    markerIdentity: '11:' + (index + 10)
  }));
  function addFile(index, role, data = content[role]) {
    const path = roots[index][role];
    assert(path && Buffer.isBuffer(data));
    nodes.set(path, { identity: '11:' + (30 + 10 * index + OUTPUTS.indexOf(role)),
      kind: 'file', content: Buffer.from(data) });
    return path;
  }
  function entry(path, kind) {
    const node = nodes.get(path);
    assert(node && node.kind === kind, 'only fixed in-memory paths are accessible');
    return node;
  }
  function held(node, big) {
    return {
      identity: () => ({ identity: node.identity,
        bytes: big ? BigInt(node.content.length) : node.content.length, ordinary: true }),
      read(buffer, offset, length, position) {
        if (position >= node.content.length) return 0;
        return node.content.copy(buffer, offset, position, Math.min(position + length, node.content.length));
      },
      write(buffer, offset, length, position) {
        assert.equal(node.content.length, position);
        node.content = Buffer.concat([node.content, buffer.subarray(offset, offset + length)]);
        return length;
      },
      sync() {},
      close() {}
    };
  }
  function mkdir(path) {
    const root = roots.find(candidate => candidate.outputRoot === path);
    assert(root);
    if (nodes.has(path)) return 'exists';
    nodes.set(path, { identity: root.identity, kind: 'directory' });
    return 'created';
  }
  function marker(path) {
    const root = roots.find(candidate => candidate.markerPath === path);
    assert(root && !nodes.has(path));
    const node = { identity: root.markerIdentity, kind: 'file', content: Buffer.alloc(0) };
    nodes.set(path, node);
    return held(node, true);
  }
  function list(path) {
    const root = roots.find(candidate => candidate.outputRoot === path);
    assert(root);
    const names = [root.markerPath, ...OUTPUTS.map(role => root[role])].filter(name => nodes.has(name));
    return names.map(name => name.slice(path.length + 1));
  }
  const lease = actualHelpers ? createWorkerArtifactOutputRootsV1ForTesting(
    { config: cfg, attemptSha256: context.attempt, parentIdentity, maxBytes: CAP }, {
      identify(path, kind) {
        const node = entry(path, kind);
        return { identity: node.identity, bytes: BigInt(node.content?.length ?? 0), ordinary: true, real: true };
      },
      mkdir,
      openMarker: marker,
      openDirectory(path) {
        const entries = list(path);
        return { read: () => entries.length ? { name: entries.shift(), ordinary: true } : null, close() {} };
      },
      now: () => 0
    }) : null;
  const copy = actualHelpers ? createWorkerArtifactPreembedCopyV1ForTesting({ config: cfg }, {
    identify(path, kind) {
      return { identity: entry(path, kind).identity, ordinary: true, real: true };
    },
    open(path, mode) {
      copyOpens.push({ path, mode });
      if (mode === 'wx+') {
        const index = roots.findIndex(candidate => candidate.preEmbedCopy === path);
        assert(index >= 0 && !nodes.has(path));
        addFile(index, 'preEmbedCopy', Buffer.alloc(0));
      } else {
        assert.equal(mode, 'r');
        assert(roots.some(candidate => path === candidate.executable || path === candidate.manifest));
      }
      return held(entry(path, 'file'), false);
    },
    now: () => 0
  }) : null;
  if (!lease) {
    for (const root of roots) {
      mkdir(root.outputRoot);
      marker(root.markerPath);
      nodes.get(root.markerPath).content = markerContent(root.id);
    }
  }
  function files(root) {
    return list(root.outputRoot).map(name => {
      const node = nodes.get(root.outputRoot + '/' + name);
      return { name, identity: node.identity, bytes: String(node.content.length) };
    });
  }
  let rechecks = 0;
  function mockRoster() {
    const rows = roots.map(root => ({
      candidate: root.id, creation: 'created', identity: root.identity, marker: 'created',
      markerClosure: 'open', directoryClosure: 'closed', complete: true, files: files(root)
    }));
    return { version: 1, kind: 'worker_artifact_output_roots_v1', qualified: false,
      state: 'Ready', pending: null, stop: null, rechecks, withinBudget: true,
      observedBytes: rows.flatMap(row => row.files).reduce((sum, row) => sum + BigInt(row.bytes), 0n).toString(),
      roots: rows };
  }
  function proof(request, code = null, unknownClosure = false, ioUncertain = false) {
    const ok = code === null, cleanupOnly = code === 'CLOSE';
    const { executable, manifest } = request.linked;
    const wrote = ok || cleanupOnly;
    return { version: 1, kind: 'worker_artifact_preembed_copy_v1', candidate: request.candidate, ok, code,
      executable: ok ? clone(executable) : null, manifest: ok ? clone(manifest) : null,
      copy: ok ? clone(executable) : null,
      io: { reservedCopies: 1, reservedReadBytes: 4 * executable.bytes + 2 * manifest.bytes,
        reservedWriteBytes: executable.bytes, actualReadBytes: wrote ? 4 * executable.bytes + 2 * manifest.bytes : 0,
        actualWriteBytes: wrote ? executable.bytes : 0, openAttempts: wrote ? 3 : 0, opened: wrote ? 3 : 0,
        closeAttempts: wrote ? 3 : 0, closed: wrote ? (unknownClosure ? 2 : 3) : 0,
        unknownClosures: unknownClosure ? 1 : 0, verifiedScans: wrote ? 6 : 0 },
      unknownClosure, ioUncertain, qualified: false, linkQualification: false, closureComplete: false,
      requiresFreshAdmission: true, normalWorkerUnchangedRequired: true };
  }
  const outputRoots = {
    recheck() {
      trace.push(['roster', f.port.snapshot().pending]);
      rechecks++;
      const normal = () => lease ? lease.recheck() : mockRoster();
      return f.recheckHook ? f.recheckHook(normal, rechecks) : normal();
    },
    cancel() {
      trace.push(['cancel-roots']);
      if (f.onLeaseCancel) return f.onLeaseCancel();
      return lease?.cancel();
    }
  };
  const preembedCopy = {
    copyNext(request) {
      trace.push(['copy', request.candidate, f.port.snapshot().pending]);
      const index = request.candidate === 'A' ? 0 : 1, root = roots[index];
      eq(request, { candidate: root.id, rootIdentity: root.identity,
        executableIdentity: nodes.get(root.executable).identity, manifestIdentity: nodes.get(root.manifest).identity,
        linked: { executable: facts.executable, manifest: facts.manifest } });
      const normal = () => {
        if (copy) return copy.copyNext(request);
        assert(!nodes.has(root.preEmbedCopy));
        addFile(index, 'preEmbedCopy', content.executable);
        return proof(request);
      };
      return f.copyHook ? f.copyHook(normal, request) : normal();
    },
    cancel() {
      trace.push(['cancel-copy']);
      if (f.onCopyCancel) return f.onCopyCancel();
      return copy?.cancel() ?? true;
    }
  };
  const spec = { config: cfg, context, outputRoots, preembedCopy, maxBytes };
  f.port = create(spec);
  f.spec = spec;
  f.lease = lease;
  f.roots = roots;
  f.addFile = addFile;
  f.proof = proof;
  f.mockRoster = mockRoster;
  f.link = index => {
    addFile(index, 'object');
    addFile(index, 'executable');
    addFile(index, 'manifest');
  };
  f.request = (index = 2) => ({ version: 1, context: clone(context), index, step: clone(recipe.steps[index]),
    linked: { executable: clone(facts.executable), manifest: clone(facts.manifest) } });
  f.expectedReceipt = index => ({ version: 1, kind: MANIFEST_KIND, ...context, index,
    ordinary: true, exclusive: true, equal: true, withinBudget: true,
    manifest: facts.manifest, preEmbed: facts.executable, copy: facts.executable });
  f.exactCopyBudget = 2 * markerContent('A').length + facts.object.bytes +
    facts.executable.bytes + facts.manifest.bytes + facts.executable.bytes;
  function receipt(kind, fields) { return wire({ version: 1, kind: 'worker_artifact_' + kind + '_v1', ...context, ...fields }); }
  f.coordinator = createWorkerArtifactCoordinatorV1({ config: cfg, clock: clock.ports, ports: {
    admit(request) {
      eq(request.recipe, recipe);
      assert.equal(request.recipeHash, context.recipe);
      return receipt('admission', { runCount: 1, checks: checks() });
    },
    recheck({ index, when }) {
      trace.push(['coordinator-check', index, when]);
      return receipt('recheck', { index, when, checks: checks() });
    },
    async prepareManifest(request, signal) {
      offers.push({ index: request.index, signal });
      trace.push(['prepare-manifest', request.index]);
      assertFrozen(request);
      const result = await f.port.prepareManifest(request, signal);
      eq(JSON.parse(result), f.expectedReceipt(request.index));
      assert.equal(wire(JSON.parse(result)), result);
      return result;
    },
    launchStep(request) {
      const { index, signal, step } = request, candidate = index < 3 ? 0 : 1;
      eq(step, recipe.steps[index]);
      launched.push({ index, signal });
      trace.push(['launch', index]);
      if (step.stage === 'compile') addFile(candidate, 'object');
      else if (step.stage === 'link') f.link(candidate);
      else {
        eq(nodes.get(roots[candidate].preEmbedCopy)?.content, content.executable);
        nodes.get(roots[candidate].executable).content = Buffer.from(content.final);
      }
      const empty = hash('');
      return receipt('process', { index, pid: index + 100, closed: true, unknown: false, exitCode: 0,
        timedOut: false, overflow: false, killAttempted: false, ioError: false, elapsedMs: 0,
        stdoutBytes: 0, stderrBytes: 0, stdoutHash: empty, stderrHash: empty, processTreeContained: false });
    },
    inspectOutputs({ index, stage }) {
      return receipt('outputs', { index, owned: true, ordinary: true, rosterComplete: true, withinBudget: true,
        directivesValidated: true, resolutionComplete: true, object: facts.object,
        executable: stage === 'compile' ? null : stage === 'link' ? facts.executable : facts.final,
        manifest: stage === 'compile' ? null : facts.manifest });
    },
    compare({ index }) {
      return receipt('compare', { index, ordinary: true, withinBudget: true, objectEqual: true, executableEqual: true });
    },
    record(report) {
      f.recorded = { report, lease: f.port.snapshot() };
      trace.push(['record', report.code]);
      return wire({ version: 1, kind: 'worker_artifact_record_v1', retained: true, report: hash(wire(report)) });
    }
  } });
  return f;
}

function snapshot(port, values) {
  const snap = port.snapshot();
  keys(snap, SNAPSHOT);
  assertFrozen(snap);
  eq(snap, { version: 1, kind: 'worker_artifact_manifest_port_snapshot_v1', pending: null,
    next: 2, completed: 0, stop: null, copyCode: null, uncertain: false, ...values });
  assert(!wire(snap).includes('synthetic'));
  return snap;
}
async function refused(port, operation, expected) {
  await assert.rejects(operation, { message: STOPPED });
  const result = snapshot(port, { next: null, ...expected });
  eq(await port.drain(), result);
  return result;
}
const actions = (f, key) => f.trace.filter(item => item[0] === key);
function closeStop(value, unknown) {
  const [a, b] = value.roots;
  const observedBytes = a.files.reduce((sum, row) => sum + BigInt(row.bytes), 0n).toString();
  return { ...value, state: 'Stopped', stop: 'IO', withinBudget: false, observedBytes,
    roots: [a, { ...b, complete: false, files: [], directoryClosure: unknown ? 'unknown' : 'closed' }] };
}

export async function runWorkerArtifactManifestPortSelfchecksV1(api) {
  const create = api.createWorkerArtifactManifestPortV1;
  const cases = [];
  const add = (id, run) => cases.push([id, run]);

  add('M01', async () => {
    keys(api, ['createWorkerArtifactManifestPortV1']);
    const f = fixture(create);
    keys(f.port, ['prepareManifest', 'snapshot', 'drain']);
    assert(Object.isFrozen(f.port));
    const initial = snapshot(f.port, {});
    eq(await f.port.drain(), initial);
    for (const change of [
      { maxBytes: 0 }, { maxBytes: CAP + 1 }, { maxBytes: 1.5 },
      { context: { ...f.context, recipe: 'f'.repeat(64) } },
      { context: { ...f.context, attempt: '0'.repeat(64) } },
      { context: { ...f.context, closure: 'c'.repeat(64) + '\n' } },
      { context: { ...f.context, extra: true } },
      { outputRoots: Object.create(f.spec.outputRoots) },
      { preembedCopy: { ...f.spec.preembedCopy, copyNext: null } }
    ]) assert.throws(() => create({ ...f.spec, ...change }), { message: INPUT });
    let read = 0;
    const bad = { ...f.spec.outputRoots, get recheck() { read++; return () => {}; } };
    assert.throws(() => create({ ...f.spec, outputRoots: bad }), { message: INPUT });
    assert.equal(read, 0);
    eq(f.trace, []);
  });

  add('M02', async () => {
    const f = fixture(create, CAP, true);
    f.spec.outputRoots.recheck = () => { throw Error('lease method changed after setup'); };
    f.spec.preembedCopy.copyNext = () => { throw Error('copy method changed after setup'); };
    assert.equal((await f.lease.prepare()).withinBudget, true);
    const result = await f.coordinator.run();
    assert.equal(result.retained, true);
    assert.equal(result.report.status, 'passed');
    assert.equal(result.report.attempted, 6);
    assert.equal(result.report.completed, 6);
    assert.equal(result.report.qualified, false);
    eq(result.report.receipts.filter(value => value.kind === MANIFEST_KIND),
      [f.expectedReceipt(2), f.expectedReceipt(5)]);
    eq(f.launched.map(item => item.index), [0, 1, 2, 3, 4, 5]);
    eq(f.offers.map(item => item.index), [2, 5]);
    for (const item of [...f.launched, ...f.offers]) assert.equal(item.signal, f.offers[0].signal);
    assert(f.offers[0].signal instanceof AbortSignal);
    assert.equal(f.offers[0].signal.aborted, false);
    eq(f.copyOpens, f.roots.flatMap(root => [
      { path: root.executable, mode: 'r' }, { path: root.manifest, mode: 'r' }, { path: root.preEmbedCopy, mode: 'wx+' }
    ]));
    eq(f.trace.filter(item => ['roster', 'copy', 'prepare-manifest'].includes(item[0])), [
      ['prepare-manifest', 2], ['roster', 'before'], ['copy', 'A', 'copy'], ['roster', 'after'],
      ['prepare-manifest', 5], ['roster', 'before'], ['copy', 'B', 'copy'], ['roster', 'after']
    ]);
    for (const index of [2, 5]) {
      const manifestCheck = f.trace.findIndex(item => item[0] === 'coordinator-check' && item[1] === index && item[2] === 'manifest');
      const launch = f.trace.findIndex(item => item[0] === 'launch' && item[1] === index);
      assert(manifestCheck >= 0 && launch > manifestCheck);
    }
    eq(await f.port.drain(), snapshot(f.port, { next: null, completed: 2 }));
    assert.equal(f.clock.live.size, 0);
    assert.equal((await f.lease.close()).state, 'Closed');
  });

  add('M03', async () => {
    for (const [change, signal] of [
      [request => ({ ...request, extra: true }), new AbortController().signal],
      [request => ({ ...request, context: { ...request.context, attempt: 'd'.repeat(64) } }), new AbortController().signal],
      [request => ({ ...request, step: { ...request.step, args: [...request.step.args, '/wrong'] } }), new AbortController().signal],
      [request => ({ ...request, linked: { ...request.linked, executable: { sha256: '0'.repeat(64), bytes: 1 } } }), new AbortController().signal],
      [request => request, { aborted: false, addEventListener() {}, removeEventListener() {} }],
      [request => request, undefined]
    ]) {
      const f = fixture(create);
      await refused(f.port, f.port.prepareManifest(change(f.request()), signal), { stop: 'REQUEST' });
      eq(f.trace, []);
    }
    const wrongOrder = fixture(create), signal = new AbortController().signal;
    await refused(wrongOrder.port, wrongOrder.port.prepareManifest(wrongOrder.request(5), signal), { stop: 'REQUEST' });
    eq(wrongOrder.trace, []);
    for (const repeat of [true, false]) {
      const f = fixture(create);
      f.link(0);
      const a = await f.port.prepareManifest(f.request(), signal);
      eq(JSON.parse(a), f.expectedReceipt(2));
      snapshot(f.port, { next: 5, completed: 1 });
      f.link(1);
      const supplied = repeat ? signal : new AbortController().signal;
      await refused(f.port, f.port.prepareManifest(f.request(repeat ? 2 : 5), supplied),
        { completed: 1, stop: 'REQUEST' });
      eq(actions(f, 'copy'), [['copy', 'A', 'copy']]);
      eq(actions(f, 'roster'), [['roster', 'before'], ['roster', 'after']]);
    }
  });

  add('M04', async () => {
    for (const change of [
      f => { f.addFile(0, 'object', Buffer.alloc(0)); },
      f => { f.addFile(0, 'executable', Buffer.from('wrong length')); },
      f => { f.addFile(0, 'manifest', Buffer.from('wrong length')); },
      f => { f.addFile(0, 'preEmbedCopy', Buffer.from('foreign copy')); },
      f => { f.addFile(1, 'object'); }
    ]) {
      const f = fixture(create);
      f.link(0);
      change(f);
      await refused(f.port, f.port.prepareManifest(f.request(), new AbortController().signal), { stop: 'ROSTER' });
      eq(actions(f, 'roster'), [['roster', 'before']]);
      eq(actions(f, 'copy'), []);
    }
    const f = fixture(create);
    const signal = new AbortController().signal;
    f.link(0);
    await f.port.prepareManifest(f.request(), signal);
    f.link(1);
    f.recheckHook = normal => {
      const value = normal(), files = value.roots[0].files;
      const position = files.findIndex(row => row.name.endsWith('.pre-embed.exe'));
      const [removed] = files.splice(position, 1);
      value.observedBytes = (BigInt(value.observedBytes) - BigInt(removed.bytes)).toString();
      return value;
    };
    await refused(f.port, f.port.prepareManifest(f.request(5), signal), { completed: 1, stop: 'ROSTER' });
    eq(actions(f, 'copy'), [['copy', 'A', 'copy']]);
  });

  add('M05', async () => {
    const reference = fixture(create);
    for (const limit of [reference.exactCopyBudget, reference.exactCopyBudget - 1]) {
      const f = fixture(create, limit);
      f.link(0);
      const operation = f.port.prepareManifest(f.request(), new AbortController().signal);
      if (limit === reference.exactCopyBudget) {
        eq(JSON.parse(await operation), f.expectedReceipt(2));
        snapshot(f.port, { next: 5, completed: 1 });
      } else {
        await refused(f.port, operation, { stop: 'BUDGET' });
        eq(actions(f, 'copy'), []);
      }
    }
    const f = fixture(create);
    f.link(0);
    f.recheckHook = normal => {
      const value = normal();
      value.observedBytes = (BigInt(value.observedBytes) + 1n).toString();
      return value;
    };
    const operation = f.port.prepareManifest(f.request(), new AbortController().signal);
    await assert.rejects(operation, { message: STOPPED });
    assert.notEqual(f.port.snapshot().stop, null);
    eq(actions(f, 'copy'), []);
  });

  add('M06', async () => {
    for (const change of [
      value => { value.roots[0].identity = '11:70'; },
      value => { value.roots[1].identity = '11:71'; },
      value => { value.roots[0].files[1].identity = '11:72'; },
      value => { value.roots[1].files[0].identity = '11:73'; },
      value => {
        const file = value.roots[0].files[1];
        file.bytes = (BigInt(file.bytes) + 1n).toString();
        value.observedBytes = (BigInt(value.observedBytes) + 1n).toString();
      },
      value => {
        const copy = value.roots[0].files.find(row => row.name.endsWith('.pre-embed.exe'));
        copy.bytes = (BigInt(copy.bytes) - 1n).toString();
        value.observedBytes = (BigInt(value.observedBytes) - 1n).toString();
      }
    ]) {
      const f = fixture(create);
      f.link(0);
      f.recheckHook = (normal, number) => {
        const value = normal();
        if (number === 2) change(value);
        return value;
      };
      await refused(f.port, f.port.prepareManifest(f.request(), new AbortController().signal), { stop: 'ROSTER' });
      eq(actions(f, 'roster'), [['roster', 'before'], ['roster', 'after']]);
      eq(actions(f, 'copy'), [['copy', 'A', 'copy']]);
    }
    const f = fixture(create);
    f.link(0);
    f.recheckHook = (normal, number) => {
      if (number === 2) f.addFile(1, 'object');
      return normal();
    };
    await refused(f.port, f.port.prepareManifest(f.request(), new AbortController().signal), { stop: 'ROSTER' });
    eq(actions(f, 'copy'), [['copy', 'A', 'copy']]);
  });

  add('M07', async () => {
    for (const kind of ['before', 'copy', 'after']) {
      const f = fixture(create), error = opaque();
      f.link(0);
      if (kind === 'copy') f.copyHook = () => { throw error.value; };
      else f.recheckHook = (normal, number) => {
        if (number === (kind === 'before' ? 1 : 2)) throw error.value;
        return normal();
      };
      await refused(f.port, f.port.prepareManifest(f.request(), new AbortController().signal),
        { stop: 'UNCERTAIN', uncertain: true });
      assert.equal(error.count(), 0);
      assert.equal(actions(f, 'copy').length, kind === 'before' ? 0 : 1);
    }
    for (const edit of [
      proof => ({ ...proof, candidate: 'B' }),
      proof => ({ ...proof, copy: { ...proof.copy, sha256: 'd'.repeat(64) } }),
      proof => ({ ...proof, ioUncertain: 'false' }),
      () => null
    ]) {
      const f = fixture(create);
      f.link(0);
      f.copyHook = normal => edit(normal());
      await refused(f.port, f.port.prepareManifest(f.request(), new AbortController().signal),
        { stop: 'UNCERTAIN', uncertain: true });
      eq(actions(f, 'roster'), [['roster', 'before']]);
    }
    const clean = fixture(create);
    clean.link(0);
    clean.copyHook = (normal, request) => clean.proof(request, 'IDENTITY');
    await refused(clean.port, clean.port.prepareManifest(clean.request(), new AbortController().signal),
      { stop: 'COPY', copyCode: 'IDENTITY' });
  });

  add('M08', async () => {
    const f = fixture(create), controller = new AbortController(), thrown = opaque();
    f.link(0);
    f.onLeaseCancel = () => { throw thrown.value; };
    controller.abort();
    await assert.rejects(f.port.prepareManifest(f.request(), controller.signal), { message: STOPPED });
    const result = f.port.snapshot();
    assert.equal(result.stop, 'CANCELLED');
    assert.equal(result.next, null);
    assert.equal(result.pending, null);
    assert.equal(result.completed, 0);
    eq(actions(f, 'cancel-roots'), [['cancel-roots']]);
    eq(actions(f, 'cancel-copy'), [['cancel-copy']]);
    eq(actions(f, 'roster'), []);
    eq(actions(f, 'copy'), []);
    eq(await f.port.drain(), result);
    assert.equal(thrown.count(), 0);
  });

  add('M09', async () => {
    for (const phase of ['before', 'copy', 'after']) {
      const f = fixture(create), controller = new AbortController(), hold = deferred();
      f.link(0);
      let entered = false;
      const pause = async normal => {
        entered = true;
        await hold.promise;
        return normal();
      };
      if (phase === 'copy') f.copyHook = pause;
      else f.recheckHook = (normal, number) => number === (phase === 'before' ? 1 : 2) ? pause(normal) : normal();
      const operation = f.port.prepareManifest(f.request(), controller.signal);
      const finished = assert.rejects(operation, { message: STOPPED });
      finished.catch(() => {});
      try {
        await until(() => entered);
        snapshot(f.port, { pending: phase });
        await assert.rejects(f.port.prepareManifest(f.request(), controller.signal), { message: BUSY });
        controller.abort();
        snapshot(f.port, { next: null, pending: phase, stop: 'CANCELLED' });
        let drained = false;
        const drain = f.port.drain().then(result => { drained = true; return result; });
        await Promise.resolve();
        assert.equal(drained, false);
        hold.resolve();
        await finished;
        eq(await drain, snapshot(f.port, { next: null, stop: 'CANCELLED' }));
      } finally {
        hold.resolve();
      }
      eq(actions(f, 'cancel-roots'), [['cancel-roots']]);
      eq(actions(f, 'cancel-copy'), [['cancel-copy']]);
      assert.equal(actions(f, 'roster').length, phase === 'after' ? 2 : 1);
      assert.equal(actions(f, 'copy').length, phase === 'before' ? 0 : 1);
    }
  });

  add('M10', async () => {
    const f = fixture(create), hold = deferred();
    let entered = false;
    f.copyHook = async (normal, request) => {
      entered = true;
      await hold.promise;
      normal();
      return f.proof(request, 'CLOSE', true);
    };
    const running = f.coordinator.run();
    try {
      await until(() => entered);
      snapshot(f.port, { pending: 'copy' });
      eq([...f.clock.live.values()].map(entry => entry.ms), [5000]);
      f.clock.fire(5000);
      const outcome = await running;
      assert.equal(outcome.retained, true);
      assert.equal(outcome.report.status, 'failed');
      assert.equal(outcome.report.code, 'PORT_TIMEOUT');
      assert.equal(outcome.report.attempted, 2);
      assert.equal(outcome.report.completed, 2);
      assert.equal(outcome.report.unknownClosure, false);
      assert.equal(f.recorded.lease.pending, 'copy');
      assert.equal(f.recorded.lease.stop, 'CANCELLED');
      assert.equal(f.offers[0].signal.aborted, true);
      eq(f.launched.map(item => item.index), [0, 1]);
      assert.equal(outcome.report.receipts.some(value => value.kind === MANIFEST_KIND), false);
      let drained = false;
      const drain = f.port.drain().then(value => { drained = true; return value; });
      await Promise.resolve();
      assert.equal(drained, false);
      hold.resolve();
      eq(await drain, snapshot(f.port, { next: null, stop: 'CANCELLED', copyCode: 'CLOSE', uncertain: true }));
      eq(actions(f, 'roster'), [['roster', 'before']]);
      eq(actions(f, 'record'), [['record', 'PORT_TIMEOUT']]);
      assert.equal(f.clock.live.size, 0);
    } finally {
      hold.resolve();
    }
  });

  add('M11', async () => {
    const f = fixture(create), hold = deferred();
    let entered = false;
    f.copyHook = async (normal, request) => {
      entered = true;
      await hold.promise;
      return f.proof(request, 'CANCELLED');
    };
    const running = f.coordinator.run();
    try {
      await until(() => entered);
      assert.equal(f.coordinator.cancel(), true);
      assert.equal(f.coordinator.cancel(), false);
      eq([...f.clock.live.values()].map(entry => entry.ms), [5000, 5000]);
      snapshot(f.port, { next: null, pending: 'copy', stop: 'CANCELLED' });
      hold.resolve();
      const result = await running;
      assert.equal(result.retained, true);
      assert.equal(result.report.code, 'PORT_ERROR');
      assert.equal(result.report.unknownClosure, false);
      eq(f.launched.map(item => item.index), [0, 1]);
      eq(await f.port.drain(), snapshot(f.port, { next: null, stop: 'CANCELLED', copyCode: 'CANCELLED' }));
      eq(actions(f, 'cancel-roots'), [['cancel-roots']]);
      eq(actions(f, 'cancel-copy'), [['cancel-copy']]);
      assert.equal(f.clock.live.size, 0);
    } finally {
      hold.resolve();
    }
  });

  add('M12', async () => {
    for (const unknown of [false, true]) {
      const f = fixture(create);
      f.link(0);
      f.recheckHook = normal => closeStop(normal(), unknown);
      const operation = f.port.prepareManifest(f.request(), new AbortController().signal);
      await assert.rejects(operation, { message: STOPPED });
      const state = f.port.snapshot();
      assert.equal(state.uncertain, unknown);
      assert.equal(state.pending, null);
      assert.equal(state.next, null);
      assert.equal(state.completed, 0);
      eq(actions(f, 'copy'), []);
    }
    const f = fixture(create), controller = new AbortController(), hold = deferred();
    f.link(0);
    let entered = false;
    f.recheckHook = async normal => {
      entered = true;
      await hold.promise;
      return closeStop(normal(), true);
    };
    const stopped = assert.rejects(f.port.prepareManifest(f.request(), controller.signal), { message: STOPPED });
    stopped.catch(() => {});
    try {
      await until(() => entered);
      controller.abort();
      hold.resolve();
      await stopped;
      eq(await f.port.drain(), snapshot(f.port, { next: null, stop: 'CANCELLED', uncertain: true }));
    } finally {
      hold.resolve();
    }
    eq(actions(f, 'copy'), []);
  });

  eq(cases.map(([id]) => id), Array.from({ length: 12 }, (_, index) => 'M' + String(index + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) {
    try { await run(); }
    catch { failed_case_ids.push(id); }
  }
  return { version: 1, kind: 'worker_artifact_manifest_port_first_v1', executed: 12,
    passed: 12 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
