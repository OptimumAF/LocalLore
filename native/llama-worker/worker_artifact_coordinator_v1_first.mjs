// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST, contract87e79c51, frozen BEFORE producer. ALL20 UNRUN.
// Synthetic ports/manual clock only: no filesystem/process/environment/SDK,
// real timers, native child, producer helper, source evaluation or top-level run.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const PORTS = ['admit', 'launchStep', 'inspectOutputs', 'prepareManifest', 'recheck', 'compare', 'record'];
const CHECKS = ['source', 'headers', 'tools', 'inputs', 'physicalRoots', 'environment', 'searchOrder',
  'noShadow', 'ownership', 'exclusiveOutputs', 'storage', 'reserve', 'authority', 'normalWorker'];
const REPORT = ['version', 'kind', 'status', 'code', 'firstCode', 'attempt', 'recipe', 'baseline', 'closure',
  'attempted', 'completed', 'receipts', 'unknownClosure', 'qualified', 'linkQualification', 'closureComplete',
  'requiresFreshAdmission', 'normalWorkerUnchangedRequired', 'processTreeContained'];
const H = 'a'.repeat(64), B = 'b'.repeat(64), C = 'c'.repeat(64), DIFFERENT = 'd'.repeat(64);
const EMPTY_SHA = 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855';
const eq = (a, b) => assert.deepEqual(a, b);
const clone = value => JSON.parse(JSON.stringify(value));
const wire = value => JSON.stringify(value);
const sha = value => createHash('sha256').update(wire(value)).digest('hex');
const bytes = value => Buffer.byteLength(value, 'utf8');
const keys = (value, wanted) => eq(Object.keys(value).sort(), [...wanted].sort());
const checks = () => Object.fromEntries(CHECKS.map(key => [key, true]));
function frozen(value) {
  if (value !== null && typeof value === 'object') {
    assert(Object.isFrozen(value)); Object.values(value).forEach(frozen);
  }
}
function config() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b',
    targetRoot: 'D:/synthetic/target', sdkUmRoot: 'C:/synthetic-sdk/um' };
}
// Independent literal recipe expectation. Never invoke the accepted planner or
// coordinator to construct expected arguments, call traces or receipt data.
function recipe(c) {
  const candidates = ['A', 'B'].map(id => {
    const outputRoot = c.targetRoot + '/worker-author-b2-candidate-' + id.toLowerCase();
    return { id, upstreamRoot: c['upstream' + id], dependencyBuildRoot: c['build' + id], outputRoot,
      object: outputRoot + '/main.cpp.obj', executable: outputRoot + '/locallore-author-worker.exe',
      preEmbedCopy: outputRoot + '/locallore-author-worker.pre-embed.exe',
      manifest: outputRoot + '/locallore-author-worker.exe.manifest', compilerPdb: outputRoot + '/compile.pdb',
      linkerPdb: outputRoot + '/link.pdb', importLibrary: outputRoot + '/locallore-author-worker.lib' };
  });
  const includes = ['common/.', 'vendor/nlohmann/..', 'vendor/sheredom/..', 'src/../include', 'ggml/src/../include'];
  const archives = ['llama/common/llama-common.lib', 'llama/src/llama.lib', 'llama/ggml/src/ggml.lib',
    'llama/ggml/src/ggml-cpu.lib', 'llama/ggml/src/ggml-base.lib',
    'llama/common/llama-common-base.lib', 'llama/vendor/cpp-httplib/cpp-httplib.lib'];
  const sdk = ['kernel32.lib', 'user32.lib', 'gdi32.lib', 'winspool.lib', 'shell32.lib',
    'ole32.lib', 'oleaut32.lib', 'uuid.lib', 'comdlg32.lib', 'advapi32.lib'];
  const steps = candidates.flatMap((p, i) => {
    const maps = [[c.workerRoot, 'X:\\locallore\\worker'], [p.upstreamRoot, 'X:\\locallore\\llama'],
      [p.outputRoot, 'X:\\locallore\\build']].flatMap(([source, target]) =>
      ['/pathmap:' + source + '=' + target, '/pathmap:' + source.replaceAll('/', '\\') + '=' + target]);
    const compile = ['/nologo', '/TP', '-DGGML_USE_CPU', '/DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1',
      ...includes.map(path => '-I' + p.upstreamRoot + '/' + path), '/DWIN32', '/D_WINDOWS', '/EHsc', '/O2',
      '/Ob2', '/DNDEBUG', '-MD', '/Brepro', '/experimental:deterministic', ...maps, '-std:c++17',
      '/showIncludes', '/Fo' + p.object, '/Fd' + p.compilerPdb, '/FS', '-c', 'main.cpp'];
    const link = ['/nologo', p.object, '/out:' + p.executable, '/implib:' + p.importLibrary,
      '/pdb:' + p.linkerPdb, '/version:0.0', '/machine:x64', '/INCREMENTAL:NO', '/subsystem:console',
      '/Brepro', '/MANIFEST', '/MANIFESTFILE:' + p.manifest, ...archives.map(path => p.dependencyBuildRoot + '/' + path),
      ...sdk.map(path => c.sdkUmRoot + '/' + path)];
    return [
      { index: i * 3, candidate: p.id, stage: 'compile', tool: c.compiler, cwd: c.workerRoot,
        args: compile, requiresPreEmbedCopy: false },
      { index: i * 3 + 1, candidate: p.id, stage: 'link', tool: c.linker, cwd: c.workerRoot,
        args: link, requiresPreEmbedCopy: false },
      { index: i * 3 + 2, candidate: p.id, stage: 'manifest', tool: c.manifestTool, cwd: c.workerRoot,
        args: ['/nologo', '/manifest', p.manifest, '/outputresource:' + p.executable + ';#1'], requiresPreEmbedCopy: true }
    ];
  });
  return { version: 1, kind: 'worker_artifact_recipe_v1', purpose: 'experimental_worker_artifact_only',
    qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true,
    normalWorkerUnchangedRequired: true, candidates, steps };
}
function policy(index) {
  const manifest = index % 3 === 2;
  return { timeoutMs: manifest ? 30000 : 120000,
    stdoutCap: manifest ? 4096 : index % 3 === 0 ? 65536 : 16384, stderrCap: 4096, drainMs: 5000 };
}
function trace() {
  const calls = ['admit'];
  for (let index = 0; index < 6; index++) {
    calls.push('recheck:' + index + ':before');
    if (index % 3 === 2) calls.push('prepareManifest:' + index, 'recheck:' + index + ':manifest');
    calls.push('launchStep:' + index, 'inspectOutputs:' + index, 'recheck:' + index + ':after');
  }
  return [...calls, 'compare:6', 'record'];
}
function label(name, request) {
  if (name === 'admit' || name === 'record') return name;
  return name + ':' + request.index + (name === 'recheck' ? ':' + request.when : '');
}
function deferred() {
  let resolve, reject; const promise = new Promise((yes, no) => { resolve = yes; reject = no; });
  return { promise, resolve, reject };
}
async function until(predicate) {
  for (let i = 0; i < 2048; i++) { if (predicate()) return; await Promise.resolve(); }
  throw Error('FIRST finite microtask settlement bound');
}
async function flush() { for (let i = 0; i < 32; i++) await Promise.resolve(); }
function manualClock() {
  const pending = new Map(), events = [], hooks = {}; let sequence = 0;
  const clock = {
    set(callback, ms) {
      assert.equal(typeof callback, 'function'); assert(Number.isSafeInteger(ms) && ms > 0);
      if (hooks.set) hooks.set(callback, ms);
      const token = Object.freeze({ id: ++sequence }); pending.set(token, { callback, ms });
      events.push({ type: 'set', token, ms }); return token;
    },
    clear(token) { if (hooks.clear) hooks.clear(token); pending.delete(token); events.push({ type: 'clear', token }); }
  };
  return { clock, pending, events, hooks,
    fire(token) { const operation = pending.get(token); assert(operation); pending.delete(token); operation.callback(); },
    find(ms) { return [...pending].find(([, value]) => value.ms === ms)?.[0]; } };
}
function fact(character, count) { return { sha256: character.repeat(64), bytes: count }; }
function fixture(create) {
  const c = config(), expectedRecipe = recipe(c), recipeHash = sha(expectedRecipe);
  const context = { attempt: H, recipe: recipeHash, baseline: B, closure: C };
  const timer = manualClock(), hooks = {}, calls = [];
  const facts = Object.fromEntries(['A', 'B'].map(id => [id, { object: fact('1', 100),
    linked: fact('2', 200), final: fact('3', 220), manifest: fact('4', 80) }]));
  const f = { config: c, recipe: expectedRecipe, recipeHash, context, timer, hooks, calls, facts, ports: null, coordinator: null };
  const common = kind => ({ version: 1, kind, ...context });
  f.receipt = (name, request) => {
    if (name === 'admit') return { ...common('worker_artifact_admission_v1'), runCount: 1, checks: checks() };
    if (name === 'record') return { version: 1, kind: 'worker_artifact_record_v1', retained: true, report: sha(request) };
    if (name === 'compare') return { ...common('worker_artifact_compare_v1'), index: 6,
      ordinary: true, withinBudget: true, objectEqual: true, executableEqual: true };
    const index = request.index, candidate = facts[index < 3 ? 'A' : 'B'];
    if (name === 'recheck') return { ...common('worker_artifact_recheck_v1'), index, when: request.when, checks: checks() };
    if (name === 'launchStep') return { ...common('worker_artifact_process_v1'), index, pid: index + 1,
      closed: true, unknown: false, exitCode: 0, timedOut: false, overflow: false, killAttempted: false,
      ioError: false, elapsedMs: 1, stdoutBytes: 0, stderrBytes: 0,
      stdoutHash: EMPTY_SHA, stderrHash: EMPTY_SHA, processTreeContained: false };
    if (name === 'prepareManifest') return { ...common('worker_artifact_manifest_v1'), index,
      ordinary: true, exclusive: true, equal: true, withinBudget: true, manifest: clone(candidate.manifest),
      preEmbed: clone(candidate.linked), copy: clone(candidate.linked) };
    assert.equal(name, 'inspectOutputs');
    return { ...common('worker_artifact_outputs_v1'), index, owned: true, ordinary: true,
      rosterComplete: true, withinBudget: true, directivesValidated: true, resolutionComplete: true,
      object: clone(candidate.object), executable: index % 3 === 0 ? null :
        clone(index % 3 === 1 ? candidate.linked : candidate.final),
      manifest: index % 3 === 0 ? null : clone(candidate.manifest) };
  };
  function request(name, value) {
    assert(Object.isFrozen(value));
    if (name === 'record') { keys(value, REPORT); frozen(value); return; }
    assert.equal(value.version, 1);
    if (name === 'admit') {
      keys(value, ['version', 'recipe', 'recipeHash']); eq(value.recipe, expectedRecipe);
      assert.equal(value.recipeHash, recipeHash); frozen(value); return;
    }
    eq(value.context, context); frozen(value.context);
    if (name === 'compare') {
      keys(value, ['version', 'context', 'index', 'candidates']); assert.equal(value.index, 6);
      eq(value.candidates, ['A', 'B'].map(id => ({ id, object: facts[id].object, executable: facts[id].final })));
      frozen(value); return;
    }
    const step = expectedRecipe.steps[value.index]; eq(value.step, step); frozen(value.step);
    if (name === 'recheck') {
      keys(value, ['version', 'context', 'index', 'step', 'when']); assert(['before', 'manifest', 'after'].includes(value.when)); frozen(value);
    } else if (name === 'launchStep') {
      keys(value, ['version', 'context', 'index', 'step', 'policy', 'signal']); eq(value.policy, policy(value.index)); frozen(value.policy);
      assert(value.signal instanceof AbortSignal); assert.equal(typeof value.signal.aborted, 'boolean');
    } else if (name === 'inspectOutputs') {
      keys(value, ['version', 'context', 'index', 'step', 'stage']); assert.equal(value.stage, step.stage); frozen(value);
    } else {
      assert.equal(name, 'prepareManifest'); keys(value, ['version', 'context', 'index', 'step', 'linked']);
      const candidate = facts[value.index < 3 ? 'A' : 'B'];
      eq(value.linked, { executable: candidate.linked, manifest: candidate.manifest }); frozen(value);
    }
  }
  f.ports = Object.fromEntries(PORTS.map(name => [name, value => {
    request(name, value); const entry = { name, request: value, label: label(name, value) }; calls.push(entry);
    const receipt = f.receipt(name, value);
    return hooks[name] ? hooks[name](value, receipt) : wire(receipt);
  }]));
  f.coordinator = create({ config: c, ports: f.ports, clock: timer.clock }); return f;
}
function state(f, value, code = null, attempted = 6, completed = 6, unknown = false, admitted = true, retained = true, firstCode = null) {
  keys(value, ['report', 'retained']); frozen(value); assert.equal(value.retained, retained);
  const r = value.report; keys(r, REPORT); assert.equal(r.version, 1); assert.equal(r.kind, 'worker_artifact_coordinator_report_v1');
  assert.equal(r.status, code === null ? 'passed' : code === 'CANCELLED' ? 'cancelled' : 'failed');
  eq([r.code, r.firstCode, r.attempted, r.completed, r.unknownClosure], [code, firstCode, attempted, completed, unknown]);
  eq([r.attempt, r.recipe, r.baseline, r.closure], [admitted ? H : null, f.recipeHash, admitted ? B : null, admitted ? C : null]);
  for (const flag of ['qualified', 'linkQualification', 'closureComplete', 'processTreeContained']) assert.equal(r[flag], false);
  assert.equal(r.requiresFreshAdmission, true); assert.equal(r.normalWorkerUnchangedRequired, true);
  assert(bytes(wire(r)) <= 131072); r.receipts.forEach(receipt => { frozen(receipt); assert(bytes(wire(receipt)) <= 4096); });
  // Serialized synthetic fixture data, not a heap/RSS measurement.
  assert(bytes(wire(f.calls)) + bytes(wire(r)) + bytes(wire(f.recipe)) < 256 * 1024);
  return r;
}
function selected(f, name) { return f.calls.filter(entry => entry.name === name); }
async function run(f) { return f.coordinator.run(); }
function mutateReceipt(f, name, change, index = null, when = null) {
  f.hooks[name] = (request, receipt) => {
    if ((index === null || request.index === index) && (when === null || request.when === when)) change(receipt, request);
    return wire(receipt);
  };
}

export async function runWorkerArtifactCoordinatorSelfchecksV1(api) {
  if (!api || typeof api.createWorkerArtifactCoordinatorV1 !== 'function' || Object.keys(api).length !== 1) {
    throw Error('UNRUN_SETUP: worker artifact coordinator v1 factory unavailable');
  }
  const create = api.createWorkerArtifactCoordinatorV1, cases = [], add = (id, body) => cases.push([id, body]);

  add('C01', () => {
    const f = fixture(create); keys(f.coordinator, ['run', 'cancel']); assert(Object.isFrozen(f.coordinator));
    const setup = () => ({ config: config(), ports: { ...f.ports }, clock: { ...f.timer.clock } });
    const invalid = value => assert.throws(() => create(value), { message: 'WorkerArtifactCoordinatorV1Invalid' });
    for (const bad of [null, [], {}, Object.create(setup()), { ...setup(), extra: 1 }]) invalid(bad);
    for (const key of ['config', 'ports', 'clock']) { const missing = setup(); delete missing[key]; invalid(missing); }
    for (const member of ['ports', 'clock']) {
      const names = member === 'ports' ? PORTS : ['set', 'clear'];
      for (const wrong of [null, [], Object.create(setup()[member])]) { const bad = setup(); bad[member] = wrong; invalid(bad); }
      for (const key of names) { const bad = setup(); bad[member][key] = 1; invalid(bad); }
      const extra = setup(); extra[member].extra = () => {}; invalid(extra);
      let touched = 0; const accessor = setup(); Object.defineProperty(accessor[member], names[0],
        { enumerable: true, get() { touched++; return () => {}; } }); invalid(accessor); assert.equal(touched, 0);
      const symbol = setup(); symbol[member][Symbol('extra')] = () => {}; invalid(symbol);
    }
    let touched = 0; const accessor = setup(); Object.defineProperty(accessor, 'ports',
      { enumerable: true, get() { touched++; return f.ports; } }); invalid(accessor); assert.equal(touched, 0);
    const symbol = setup(); symbol[Symbol('extra')] = 1; invalid(symbol);
    const plain = setup(), nullPrototype = Object.assign(Object.create(null), plain);
    nullPrototype.ports = Object.assign(Object.create(null), plain.ports);
    nullPrototype.clock = Object.assign(Object.create(null), plain.clock);
    keys(create(nullPrototype), ['run', 'cancel']);
    const badConfig = setup(); badConfig.config.workerRoot = 'C:/synthetic/worker';
    assert.throws(() => create(badConfig), { message: 'WorkerArtifactRecipeV1Invalid' });
    const oversized = setup(); oversized.config.workerRoot = 'D:/' + 'x'.repeat(256);
    assert.throws(() => create(oversized), { message: 'WorkerArtifactRecipeV1Limit' });
    assert.equal(f.calls.length, 0); assert.equal(f.timer.events.length, 0);
  });
  add('C02', async () => {
    const f = fixture(create), result = await run(f), r = state(f, result);
    eq(f.calls.map(x => x.label), trace()); assert.equal(r.receipts.length, 30);
    eq(r.receipts, f.calls.slice(0, -1).map(entry => f.receipt(entry.name, entry.request)));
    eq(selected(f, 'launchStep').map(x => x.request.index), [0, 1, 2, 3, 4, 5]);
    eq(selected(f, 'launchStep').map(x => x.request.policy), [0, 1, 2, 3, 4, 5].map(policy));
    eq(selected(f, 'prepareManifest').map(x => x.request.index), [2, 5]);
    assert.equal(selected(f, 'record').length, 1); assert.equal(f.timer.pending.size, 0);
  });
  add('C03', async () => {
    for (const key of CHECKS) {
      const f = fixture(create); mutateReceipt(f, 'admit', r => { r.checks[key] = false; });
      const r = state(f, await run(f), 'ADMISSION', 0, 0, false, false);
      eq(f.calls.map(x => x.label), ['admit', 'record']); assert.equal(r.receipts.length, 1);
      assert.equal(r.receipts[0].checks[key], false); assert.equal(selected(f, 'launchStep').length, 0);
    }
  });
  add('C04', async () => {
    for (const key of CHECKS) for (const [index, when, attempted, completed] of [[0, 'before', 0, 0], [0, 'after', 1, 0], [2, 'manifest', 2, 2]]) {
      const f = fixture(create); mutateReceipt(f, 'recheck', r => { r.checks[key] = false; }, index, when);
      const r = state(f, await run(f), 'RECHECK', attempted, completed);
      const terminal = 'recheck:' + index + ':' + when, expected = trace().slice(0, trace().indexOf(terminal) + 1);
      eq(f.calls.map(x => x.label), [...expected, 'record']); assert.equal(r.receipts.at(-1).checks[key], false);
    }
  });
  add('C05', async () => {
    for (const id of [0, 3]) for (const key of ['directivesValidated', 'resolutionComplete']) {
      const f = fixture(create); mutateReceipt(f, 'inspectOutputs', r => { r[key] = false; }, id);
      const r = state(f, await run(f), 'OUTPUT', id + 1, id);
      assert.equal(r.receipts.at(-1)[key], false); assert(!selected(f, 'launchStep').some(x => x.request.index === id + 1));
    }
  });
  add('C06', async () => {
    for (const index of [0, 1, 2]) for (const change of [r => { r.exitCode = 7; }, r => { r.exitCode = null; },
      r => { r.timedOut = true; }, r => { r.overflow = true; }, r => { r.killAttempted = true; }]) {
      const f = fixture(create); mutateReceipt(f, 'launchStep', change, index);
      state(f, await run(f), 'PROCESS', index + 1, index); assert.equal(selected(f, 'inspectOutputs').length, index);
      assert.equal(selected(f, 'launchStep').length, index + 1); assert.equal(selected(f, 'record').length, 1);
    }
  });
  add('C07', async () => {
    for (const change of [r => { r.closed = false; }, r => { r.unknown = true; }, r => { r.ioError = true; },
      r => { r.closed = false; r.timedOut = true; r.overflow = true; }]) {
      const f = fixture(create); mutateReceipt(f, 'launchStep', change, 0);
      state(f, await run(f), 'CLOSURE', 1, 0, true); assert.equal(selected(f, 'inspectOutputs').length, 0);
    }
    for (const reply of [() => { throw Error('private launch exception'); }, () => Promise.reject(Error('private launch rejection'))]) {
      const f = fixture(create); f.hooks.launchStep = reply;
      const r = state(f, await run(f), 'PORT_ERROR', 1, 0, true);
      assert.equal(r.receipts.length, 2); assert(!wire(r).includes('private launch'));
    }
  });
  add('C08', async () => {
    for (const key of ['ordinary', 'exclusive', 'equal', 'withinBudget']) {
      const f = fixture(create); mutateReceipt(f, 'prepareManifest', r => { r[key] = false; }, 2);
      state(f, await run(f), 'MANIFEST', 2, 2); eq(selected(f, 'launchStep').map(x => x.request.index), [0, 1]);
    }
    for (const key of ['manifest', 'preEmbed', 'copy']) {
      const f = fixture(create); mutateReceipt(f, 'prepareManifest', r => { r[key].sha256 = DIFFERENT; }, 2);
      state(f, await run(f), 'MANIFEST', 2, 2);
      const absent = fixture(create); mutateReceipt(absent, 'prepareManifest', r => { r[key] = null; }, 2);
      state(absent, await run(absent), 'RECEIPT', 2, 2);
    }
    const changed = fixture(create); mutateReceipt(changed, 'inspectOutputs', r => { r.manifest.bytes++; }, 2);
    state(changed, await run(changed), 'OUTPUT', 3, 2);
  });
  add('C09', async () => {
    const variants = [r => ({ ...r, index: 1 }), r => ({ ...r, recipe: DIFFERENT }), r => ({ ...r, baseline: DIFFERENT }),
      r => ({ ...r, attempt: DIFFERENT }), r => ({ ...r, closure: DIFFERENT }),
      r => ({ ...r, kind: 'private_wrong_kind' }), r => ({ ...r, extra: true }), r => { const x = { ...r }; delete x.pid; return x; }];
    for (const change of variants) {
      const f = fixture(create); f.hooks.launchStep = (_, r) => wire(change(r));
      const result = state(f, await run(f), 'RECEIPT', 1, 0, true); assert.equal(result.receipts.length, 2);
    }
    for (const reply of [r => r, r => new String(wire(r)), r => wire(r) + '\n', r => ' ' + wire(r),
      r => wire(r).replace('"index":0', '"index":0.0'), () => '"' + 'x'.repeat(4096) + '"', () => '{']) {
      const f = fixture(create); f.hooks.launchStep = (_, r) => reply(r);
      const result = state(f, await run(f), 'RECEIPT', 1, 0, true); assert(!wire(result).includes('private_wrong_kind'));
    }
    const wrong = fixture(create); mutateReceipt(wrong, 'recheck', r => { r.when = 'after'; }, 0, 'before');
    state(wrong, await run(wrong), 'RECEIPT', 0, 0);
  });
  add('C10', async () => {
    for (const key of ['owned', 'ordinary', 'rosterComplete', 'withinBudget', 'directivesValidated', 'resolutionComplete']) {
      const f = fixture(create); mutateReceipt(f, 'inspectOutputs', r => { r[key] = false; }, 0);
      const result = state(f, await run(f), 'OUTPUT', 1, 0); assert.equal(result.receipts.at(-1)[key], false);
    }
    const drift = fixture(create); mutateReceipt(drift, 'inspectOutputs', r => { r.object.bytes++; }, 1);
    state(drift, await run(drift), 'OUTPUT', 2, 1);
    const absent = fixture(create); mutateReceipt(absent, 'inspectOutputs', r => { r.object = null; }, 0);
    state(absent, await run(absent), 'RECEIPT', 1, 0);
  });
  add('C11', async () => {
    for (const part of ['object', 'final']) for (const key of ['sha256', 'bytes']) {
      const f = fixture(create); f.facts.B[part][key] = key === 'sha256' ? DIFFERENT : f.facts.B[part].bytes + 1;
      state(f, await run(f), 'COMPARE'); assert.equal(selected(f, 'launchStep').length, 6);
    }
    for (const key of ['ordinary', 'withinBudget', 'objectEqual', 'executableEqual']) {
      const f = fixture(create); mutateReceipt(f, 'compare', r => { r[key] = false; });
      state(f, await run(f), 'COMPARE');
    }
  });
  add('C12', async () => {
    const before = fixture(create); assert.equal(before.coordinator.cancel(), true); assert.equal(before.coordinator.cancel(), false);
    state(before, await run(before), 'CANCELLED', 0, 0, false, false); eq(before.calls.map(x => x.label), ['record']);
    for (let boundary = 0; boundary < trace().length - 1; boundary++) {
      const f = fixture(create);
      for (const name of PORTS.filter(x => x !== 'record')) f.hooks[name] = (_, receipt) => {
        if (f.calls.length - 1 === boundary) { assert.equal(f.coordinator.cancel(), true); assert.equal(f.coordinator.cancel(), false); }
        return wire(receipt);
      };
      const prefix = trace().slice(0, boundary + 1);
      const attempted = prefix.filter(x => x.startsWith('launchStep:')).length;
      const completed = prefix.filter(x => x.startsWith('recheck:') && x.endsWith(':after')).length;
      state(f, await run(f), 'CANCELLED', attempted, completed);
      eq(f.calls.map(x => x.label), [...prefix, 'record']); assert.equal(f.coordinator.cancel(), false);
    }
  });
  add('C13', async () => {
    for (const outcome of ['zero', 'kill', 'nonzero', 'timeout', 'unknown']) {
      const f = fixture(create), held = deferred(); let launch;
      f.hooks.launchStep = (request, receipt) => { launch = { request, receipt }; return held.promise; };
      const pending = run(f); await until(() => launch !== undefined); assert.equal(launch.request.signal.aborted, false);
      assert.equal(f.coordinator.cancel(), true); assert.equal(launch.request.signal.aborted, true);
      if (outcome === 'kill') { launch.receipt.killAttempted = true; launch.receipt.exitCode = -1; }
      if (outcome === 'nonzero') launch.receipt.exitCode = null;
      if (outcome === 'timeout') launch.receipt.timedOut = true;
      if (outcome === 'unknown') launch.receipt.unknown = true;
      held.resolve(wire(launch.receipt));
      const code = outcome === 'timeout' ? 'PROCESS' : outcome === 'unknown' ? 'CLOSURE' : 'CANCELLED';
      state(f, await pending, code, 1, 0, outcome === 'unknown'); assert.equal(selected(f, 'launchStep').length, 1);
      assert.equal(selected(f, 'inspectOutputs').length, 0);
    }
  });
  add('C14', async () => {
    for (const which of ['admit-deadline', 'admit-grace', 'launch-deadline', 'launch-grace', 'launch-original-first']) {
      const f = fixture(create), held = deferred(); const launch = which.startsWith('launch'); let receipt;
      f.hooks[launch ? 'launchStep' : 'admit'] = (_, value) => { receipt = value; return held.promise; };
      const pending = run(f); await until(() => receipt !== undefined);
      const original = f.timer.find(launch ? 125000 : 5000); assert(original);
      const cancellation = which.endsWith('grace') || which === 'launch-original-first';
      if (cancellation) assert.equal(f.coordinator.cancel(), true);
      const token = which.endsWith('grace') ? [...f.timer.pending.keys()].find(x => x !== original) : original; assert(token);
      f.timer.fire(token);
      const grace = which.endsWith('grace'), code = grace ? (launch ? 'CLOSURE' : 'CANCELLED') : 'PORT_TIMEOUT';
      const result = await pending, saved = clone(result); state(f, result, code, launch ? 1 : 0, 0, launch, launch);
      if (which === 'launch-original-first') held.reject(Error('private late rejection')); else held.resolve(wire(receipt));
      await flush(); eq(result, saved); assert.equal(selected(f, 'record').length, 1);
      assert.equal(selected(f, 'launchStep').length, launch ? 1 : 0);
    }
    const setup = fixture(create); setup.timer.hooks.set = (_, ms) => { if (ms === 125000) { setup.timer.hooks.set = null; throw Error('clock setup'); } };
    state(setup, await run(setup), 'PORT_ERROR', 0, 0); assert.equal(selected(setup, 'launchStep').length, 0);
    const beforeAdmission = fixture(create); beforeAdmission.timer.hooks.set = () => {
      beforeAdmission.timer.hooks.set = null; throw Error('first clock setup');
    };
    state(beforeAdmission, await run(beforeAdmission), 'PORT_ERROR', 0, 0, false, false);
    eq(beforeAdmission.calls.map(entry => entry.label), ['record']);
    const clear = fixture(create); clear.timer.hooks.clear = token => {
      if (clear.timer.pending.get(token)?.ms === 125000) { clear.timer.hooks.clear = null; throw Error('clock clear'); }
    };
    state(clear, await run(clear), 'PORT_ERROR', 1, 0, true); assert.equal(selected(clear, 'inspectOutputs').length, 0);
  });
  add('C15', async () => {
    const f = fixture(create), held = deferred(); let admission;
    f.hooks.admit = (_, receipt) => { admission = receipt; return held.promise; };
    const first = run(f); const second = run(f);
    await assert.rejects(second, { message: 'WorkerArtifactCoordinatorV1Used' }); await until(() => admission !== undefined);
    assert.equal(f.calls.length, 1); assert.equal(selected(f, 'record').length, 0);
    assert.equal(f.coordinator.cancel(), true); held.resolve(wire(admission));
    state(f, await first, 'CANCELLED', 0, 0);
    await assert.rejects(run(f), { message: 'WorkerArtifactCoordinatorV1Used' }); assert.equal(selected(f, 'record').length, 1);
  });
  add('C16', async () => {
    const f = fixture(create), oldRecipe = clone(f.recipe);
    for (const name of PORTS) f.ports[name] = () => { throw Error('caller replaced port'); };
    f.timer.clock.set = () => { throw Error('caller replaced set'); }; f.timer.clock.clear = () => { throw Error('caller replaced clear'); };
    f.config.workerRoot = 'D:/synthetic/caller-changed';
    const result = await run(f); state(f, result); eq(f.recipe, oldRecipe);
    eq(selected(f, 'admit')[0].request.recipe, oldRecipe);
    for (const entry of f.calls) {
      assert(Object.isFrozen(entry.request));
      if (entry.name === 'launchStep') { frozen(entry.request.context); frozen(entry.request.step); frozen(entry.request.policy); }
      else frozen(entry.request);
    }
    const saved = clone(result); assert.throws(() => result.report.receipts.push({}), TypeError);
    f.facts.A.object.bytes = 1; eq(result, saved); assert.equal(f.coordinator.cancel(), false);
  });
  add('C17', async () => {
    const simultaneous = fixture(create); simultaneous.hooks.recheck = (_, receipt) => {
      receipt.checks.reserve = false; simultaneous.coordinator.cancel(); return wire(receipt);
    };
    state(simultaneous, await run(simultaneous), 'RECHECK', 0, 0);
    for (const how of ['throw', 'reject', 'wrong-hash', 'not-retained', 'malformed', 'timeout', 'clock-clear']) {
      const f = fixture(create); mutateReceipt(f, 'launchStep', r => { r.exitCode = 1; }, 0);
      const held = deferred();
      f.hooks.record = (_, receipt) => {
        assert.equal(f.coordinator.cancel(), false); // terminal choice already selected, even while record is pending
        if (how === 'throw') throw Error('private record failure');
        if (how === 'reject') return Promise.reject(Error('private record rejection'));
        if (how === 'wrong-hash') receipt.report = DIFFERENT;
        if (how === 'not-retained') receipt.retained = false;
        if (how === 'malformed') return '{';
        if (how === 'timeout') return held.promise;
        if (how === 'clock-clear') f.timer.hooks.clear = () => { f.timer.hooks.clear = null; throw Error('record clear'); };
        return wire(receipt);
      };
      const pending = run(f); if (how === 'timeout') { await until(() => selected(f, 'record').length === 1); f.timer.fire(f.timer.find(5000)); }
      const result = await pending; state(f, result, 'EVIDENCE', 1, 0, false, true, false, 'PROCESS');
      assert.equal(selected(f, 'record').length, 1); assert(!wire(result).includes('private record'));
      if (how === 'timeout') { held.resolve(wire({ version: 1, kind: 'worker_artifact_record_v1', retained: true, report: H })); await flush(); }
    }
    const precancel = fixture(create); precancel.coordinator.cancel();
    precancel.timer.hooks.set = () => { throw Error('record setup'); };
    state(precancel, await run(precancel), 'EVIDENCE', 0, 0, false, false, false, 'CANCELLED');
    assert.equal(selected(precancel, 'record').length, 0);
    const passedButNotRetained = fixture(create); mutateReceipt(passedButNotRetained, 'record', receipt => { receipt.retained = false; });
    state(passedButNotRetained, await run(passedButNotRetained), 'EVIDENCE', 6, 6, false, true, false, null);
    assert.equal(selected(passedButNotRetained, 'record').length, 1);
  });
  add('C18', async () => {
    const inclusive = fixture(create); mutateReceipt(inclusive, 'launchStep', (r, request) => {
      r.pid = 2147483647; r.elapsedMs = policy(request.index).timeoutMs + 5000;
      r.stdoutBytes = policy(request.index).stdoutCap; r.stderrBytes = 4096; r.stdoutHash = H; r.stderrHash = B;
    });
    for (const candidate of Object.values(inclusive.facts)) {
      candidate.object.bytes = 67108864; candidate.linked.bytes = 67108864; candidate.final.bytes = 67108864; candidate.manifest.bytes = 65536;
    }
    state(inclusive, await run(inclusive));
    const minimum = fixture(create); for (const candidate of Object.values(minimum.facts)) for (const value of Object.values(candidate)) value.bytes = 1;
    state(minimum, await run(minimum));
    for (const index of [0, 1, 2]) for (const change of [r => { r.pid = 0; }, r => { r.pid = 2147483648; },
      r => { r.elapsedMs = -1; }, r => { r.elapsedMs = policy(index).timeoutMs + 5001; },
      r => { r.stdoutBytes = policy(index).stdoutCap + 1; }, r => { r.stderrBytes = 4097; },
      r => { r.exitCode = 2147483648; }, r => { r.exitCode = -2147483649; },
      r => { r.stdoutHash = H + '\n'; }, r => { r.closed = 1; }, r => { r.processTreeContained = true; }]) {
      const f = fixture(create); mutateReceipt(f, 'launchStep', change, index);
      state(f, await run(f), 'RECEIPT', index + 1, index, true);
    }
    for (const exitCode of [-2147483648, 2147483647]) {
      const f = fixture(create); mutateReceipt(f, 'launchStep', r => { r.exitCode = exitCode; }, 0);
      state(f, await run(f), 'PROCESS', 1, 0);
    }
    for (const [index, key, count] of [[0, 'object', 0], [0, 'object', 67108865], [1, 'manifest', 65537]]) {
      const f = fixture(create); mutateReceipt(f, 'inspectOutputs', r => { r[key].bytes = count; }, index);
      state(f, await run(f), 'RECEIPT', index + 1, index);
    }
    for (const change of [r => { r.attempt = '0'.repeat(64); }, r => { r.runCount = 2; }, r => { r.checks.source = 1; }]) {
      const f = fixture(create); mutateReceipt(f, 'admit', change); state(f, await run(f), 'RECEIPT', 0, 0, false, false);
    }
  });
  add('C19', async () => {
    const f = fixture(create), result = await run(f), r = state(f, result);
    assert.equal(f.coordinator.cancel(), false); keys(f.coordinator, ['run', 'cancel']);
    for (const key of ['adopt', 'author', 'release', 'nativeQualified', 'model', 'normalWorker', 'retry']) assert(!Object.hasOwn(r, key));
    assert.equal(r.requiresFreshAdmission, true); assert.equal(r.normalWorkerUnchangedRequired, true);
    assert.equal(r.processTreeContained, false); assert.equal(r.closureComplete, false);
    assert(!wire(r).includes('private launch')); assert(!wire(r).includes('synthetic-tools'));
  });
  add('C20', async () => {
    const f = fixture(create), result = await run(f), r = state(f, result);
    eq(f.calls.map(x => x.label), trace()); assert.equal(f.calls.length, 31); assert.equal(r.receipts.length, 30);
    assert.equal(selected(f, 'launchStep').length, 6); assert(f.calls.every(entry => PORTS.includes(entry.name)));
    assert(!r.receipts.some(receipt => receipt.kind === 'worker_artifact_record_v1'));
    r.receipts.forEach(receipt => assert(bytes(wire(receipt)) <= 4096));
    const metadata = { ...r, receipts: [] }; assert(bytes(wire(metadata)) < 2048);
    assert(30 * 4096 + 2048 <= 131072); assert(bytes(wire(r)) <= 131072);
    eq(selected(f, 'record')[0].request, r);
    assert.equal(f.receipt('record', r).report, sha(r));
    assert.equal(f.timer.pending.size, 0);
    eq(f.timer.events.filter(event => event.type === 'set').map(event => event.ms),
      f.calls.map(entry => entry.name === 'launchStep' ? policy(entry.request.index).timeoutMs + 5000 : 5000));
  });

  eq(cases.map(([id]) => id), Array.from({ length: 20 }, (_, i) => 'C' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, body] of cases) { try { await body(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: 'worker_artifact_coordinator_first_v1', executed: 20,
    passed: 20 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
