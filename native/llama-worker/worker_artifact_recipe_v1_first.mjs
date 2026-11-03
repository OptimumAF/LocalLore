// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST, contractfa9a2e3a, frozen BEFORE producer. ALL16 UNRUN.
// Synthetic lexical path/argv DATA only; no filesystem, process, environment,
// native tool, source import/evaluation, hashing, callback or top-level suite.
import assert from 'node:assert/strict';

const INVALID = 'WorkerArtifactRecipeV1Invalid', LIMIT = 'WorkerArtifactRecipeV1Limit';
const CONFIG = ['compiler', 'linker', 'manifestTool', 'workerRoot', 'upstreamA', 'upstreamB',
  'buildA', 'buildB', 'targetRoot', 'sdkUmRoot'];
const PROJECT = ['workerRoot', 'upstreamA', 'upstreamB', 'buildA', 'buildB', 'targetRoot'];
const OUTPUT = ['version', 'kind', 'purpose', 'qualified', 'linkQualification', 'closureComplete',
  'requiresFreshAdmission', 'normalWorkerUnchangedRequired', 'candidates', 'steps'];
const CANDIDATE = ['id', 'upstreamRoot', 'dependencyBuildRoot', 'outputRoot', 'object',
  'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'];
const STEP = ['index', 'candidate', 'stage', 'tool', 'cwd', 'args', 'requiresPreEmbedCopy'];
const INCLUDES = ['common/.', 'vendor/nlohmann/..', 'vendor/sheredom/..', 'src/../include', 'ggml/src/../include'];
const ARCHIVES = ['llama/common/llama-common.lib', 'llama/src/llama.lib', 'llama/ggml/src/ggml.lib',
  'llama/ggml/src/ggml-cpu.lib', 'llama/ggml/src/ggml-base.lib',
  'llama/common/llama-common-base.lib', 'llama/vendor/cpp-httplib/cpp-httplib.lib'];
const SDK = ['kernel32.lib', 'user32.lib', 'gdi32.lib', 'winspool.lib', 'shell32.lib',
  'ole32.lib', 'oleaut32.lib', 'uuid.lib', 'comdlg32.lib', 'advapi32.lib'];
const eq = (a, b) => assert.deepEqual(a, b);
const clone = x => JSON.parse(JSON.stringify(x));
const bytes = x => Buffer.byteLength(x, 'utf8');
const argvBytes = args => args.reduce((sum, arg) => sum + bytes(arg) + 3, 0);
function keys(x, wanted) { eq(Object.keys(x), wanted); }
function frozen(x) {
  if (x !== null && typeof x === 'object') { assert(Object.isFrozen(x)); Object.values(x).forEach(frozen); }
}
function fixture() {
  return { compiler: 'C:/synthetic-tools/compiler/cl.exe', linker: 'C:/synthetic-tools/linker/link.exe',
    manifestTool: 'C:/synthetic-tools/manifest/mt.exe', workerRoot: 'D:/synthetic/worker',
    upstreamA: 'D:/synthetic/upstream-a', upstreamB: 'D:/synthetic/upstream-b',
    buildA: 'D:/synthetic/build-a', buildB: 'D:/synthetic/build-b',
    targetRoot: 'D:/synthetic/target', sdkUmRoot: 'C:/synthetic-sdk/um' };
}
function expectedCandidate(config, id) {
  const outputRoot = config.targetRoot + '/worker-author-b2-candidate-' + id.toLowerCase();
  return { id, upstreamRoot: config['upstream' + id], dependencyBuildRoot: config['build' + id], outputRoot,
    object: outputRoot + '/main.cpp.obj', executable: outputRoot + '/locallore-author-worker.exe',
    preEmbedCopy: outputRoot + '/locallore-author-worker.pre-embed.exe',
    manifest: outputRoot + '/locallore-author-worker.exe.manifest',
    compilerPdb: outputRoot + '/compile.pdb', linkerPdb: outputRoot + '/link.pdb',
    importLibrary: outputRoot + '/locallore-author-worker.lib' };
}
function expectedMaps(config, candidate) {
  return [[config.workerRoot, 'X:\\locallore\\worker'], [candidate.upstreamRoot, 'X:\\locallore\\llama'],
    [candidate.outputRoot, 'X:\\locallore\\build']].flatMap(([source, virtual]) =>
    ['/pathmap:' + source + '=' + virtual, '/pathmap:' + source.replaceAll('/', '\\') + '=' + virtual]);
}
function expectedCompile(config, candidate) {
  return ['/nologo', '/TP', '-DGGML_USE_CPU', '/DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1',
    ...INCLUDES.map(p => '-I' + candidate.upstreamRoot + '/' + p),
    '/DWIN32', '/D_WINDOWS', '/EHsc', '/O2', '/Ob2', '/DNDEBUG', '-MD', '/Brepro',
    '/experimental:deterministic', ...expectedMaps(config, candidate), '-std:c++17', '/showIncludes',
    '/Fo' + candidate.object, '/Fd' + candidate.compilerPdb, '/FS', '-c', 'main.cpp'];
}
function expectedLink(config, candidate) {
  return ['/nologo', candidate.object, '/out:' + candidate.executable, '/implib:' + candidate.importLibrary,
    '/pdb:' + candidate.linkerPdb, '/version:0.0', '/machine:x64', '/INCREMENTAL:NO', '/subsystem:console',
    '/Brepro', '/MANIFEST', '/MANIFESTFILE:' + candidate.manifest,
    ...ARCHIVES.map(p => candidate.dependencyBuildRoot + '/' + p), ...SDK.map(p => config.sdkUmRoot + '/' + p)];
}
function expectedManifest(candidate) {
  return ['/nologo', '/manifest', candidate.manifest, '/outputresource:' + candidate.executable + ';#1'];
}
function expected(config) {
  const candidates = ['A', 'B'].map(id => expectedCandidate(config, id));
  return { version: 1, kind: 'worker_artifact_recipe_v1', purpose: 'experimental_worker_artifact_only',
    qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true,
    normalWorkerUnchangedRequired: true, candidates,
    steps: candidates.flatMap((c, i) => [
      { index: i * 3, candidate: c.id, stage: 'compile', tool: config.compiler,
        cwd: config.workerRoot, args: expectedCompile(config, c), requiresPreEmbedCopy: false },
      { index: i * 3 + 1, candidate: c.id, stage: 'link', tool: config.linker,
        cwd: config.workerRoot, args: expectedLink(config, c), requiresPreEmbedCopy: false },
      { index: i * 3 + 2, candidate: c.id, stage: 'manifest', tool: config.manifestTool,
        cwd: config.workerRoot, args: expectedManifest(c), requiresPreEmbedCopy: true }
    ]) };
}
function structure(value) {
  keys(value, OUTPUT); frozen(value); assert.equal(value.version, 1);
  assert.equal(value.kind, 'worker_artifact_recipe_v1'); assert.equal(value.purpose, 'experimental_worker_artifact_only');
  assert.equal(value.candidates.length, 2); value.candidates.forEach(c => keys(c, CANDIDATE));
  assert.equal(value.steps.length, 6); value.steps.forEach(step => {
    keys(step, STEP); assert(Array.isArray(step.args)); assert(step.args.every(arg => typeof arg === 'string'));
    eq(Reflect.ownKeys(step.args), [...Array.from({ length: step.args.length }, (_, i) => String(i)), 'length']);
    assert(argvBytes(step.args) <= 24576);
  });
  assert(bytes(JSON.stringify(value)) <= 65536); return value;
}
function boundedPath(length, marker, leaf = null, drive = 'D') {
  const last = length - 3 - 3 * 255 - (leaf === null ? 3 : 4 + bytes(leaf));
  assert(last > 0 && last <= 255);
  const parts = [marker.repeat(255), 'b'.repeat(255), 'c'.repeat(255), 'd'.repeat(last)];
  if (leaf !== null) parts.push(leaf);
  const result = drive + ':/' + parts.join('/'); assert.equal(bytes(result), length);
  assert(parts.every(p => bytes(p) <= 255)); return result;
}

export async function runWorkerArtifactRecipeSelfchecksV1(api) {
  if (!api || typeof api.planWorkerArtifactComparisonV1 !== 'function' || Object.keys(api).length !== 1) {
    throw Error('UNRUN_SETUP: worker artifact recipe v1 planner unavailable');
  }
  const plan = api.planWorkerArtifactComparisonV1, cases = [], add = (id, run) => cases.push([id, run]);
  const invalid = config => assert.throws(() => plan(config), { message: INVALID });
  const limit = config => assert.throws(() => plan(config), { message: LIMIT });

  add('R01', () => {
    const c = fixture(), value = structure(plan(c)); eq(value, expected(c));
    for (const key of CONFIG) { const absent = fixture(); delete absent[key]; invalid(absent); }
    for (const bad of [null, [], {}, Object.create(c), { ...c, extra: 'x' },
      { ...c, workerRoot: new String(c.workerRoot) }, { ...c, linker: 1 }, { ...c, targetRoot: undefined }]) invalid(bad);
    let touched = 0; const accessor = fixture();
    Object.defineProperty(accessor, 'workerRoot', { enumerable: true, get() { touched++; return c.workerRoot; } });
    invalid(accessor); assert.equal(touched, 0);
    const symbol = fixture(); symbol[Symbol('extra')] = 'x'; invalid(symbol);
    const nonenumerable = fixture(); Object.defineProperty(nonenumerable, 'workerRoot', { value: c.workerRoot, enumerable: false });
    invalid(nonenumerable); eq(plan(Object.assign(Object.create(null), c)), expected(c));
  });
  add('R02', () => {
    for (const key of PROJECT) invalid({ ...fixture(), [key]: 'C:/synthetic/' + key });
    for (const key of CONFIG) {
      const c = fixture(); c[key] = c[key].replace(/^[CD]:/, 'E:'); invalid(c);
      const lower = fixture(); lower[key] = lower[key][0].toLowerCase() + lower[key].slice(1); invalid(lower);
    }
    for (const [key, leaf] of [['compiler', 'cl.exe'], ['linker', 'link.exe'], ['manifestTool', 'mt.exe']]) {
      for (const wrong of [leaf.toUpperCase(), 'cmd.exe', leaf + '.bak', 'other.exe']) invalid({ ...fixture(), [key]: 'C:/synthetic-tools/' + wrong });
      const c = fixture(); c[key] = 'D:/synthetic-tools/' + leaf; eq(plan(c), expected(c));
    }
    const sdk = fixture(); sdk.sdkUmRoot = 'D:/synthetic-sdk/um'; eq(plan(sdk), expected(sdk));
    const unicode = fixture(); unicode.workerRoot = 'D:/synthetic/物語 作成';
    unicode.compiler = 'C:/synthetic-tools/道具 一/cl.exe'; eq(plan(unicode), expected(unicode));
  });
  add('R03', () => {
    for (const path of ['D:/', 'D:', 'D:relative', '//server/share', '\\\\server\\share', '\\\\?\\D:\\tree',
      'D:\\synthetic\\worker', 'D:/synthetic/', 'D:/synthetic//worker', 'D:/synthetic/./worker',
      'D:/synthetic/../worker', 'D:/synthetic/worker.', 'D:/synthetic/worker ',
      'D:/synthetic/data:stream', 'D:/synthetic/a"b', 'D:/synthetic/a?b', 'D:/synthetic/a*b',
      'D:/synthetic/a=b', 'D:/synthetic/a,b', 'D:/synthetic/a;b', 'D:/synthetic/a#b', 'D:/synthetic/a`b',
      'D:/synthetic/a<b', 'D:/synthetic/a>b', 'D:/synthetic/a|b', 'D:/synthetic/a&b',
      'D:/synthetic/a\u0000b', 'D:/synthetic/a\nb', 'D:/synthetic/a\tb',
      'D:/synthetic/a\rb', 'D:/synthetic/a\u001fb', 'D:/synthetic/a\u007fb']) {
      invalid({ ...fixture(), workerRoot: path });
    }
    for (const stem of ['CON', 'prn', 'Aux', 'nul', ...['com', 'lpt'].flatMap(prefix =>
      [...Array.from({ length: 9 }, (_, i) => String(i + 1)), '¹', '²', '³'].map(n => prefix + n))]) {
      for (const suffix of ['', '.txt', ' .suffix']) invalid({ ...fixture(), workerRoot: 'D:/synthetic/' + stem + suffix + '/leaf' });
      invalid({ ...fixture(), compiler: 'C:/synthetic-tools/' + stem + '.suffix/cl.exe' });
    }
    for (const allowed of ['conformance', 'auxiliary', 'com0', 'com10', 'lpt0', 'com⁴']) {
      const c = fixture(); c.workerRoot = 'D:/synthetic/' + allowed; eq(plan(c), expected(c));
    }
  });
  add('R04', () => {
    for (const first of PROJECT) for (const second of PROJECT) if (first !== second) {
      const equal = fixture(); equal[first] = 'D:/Synthetic/Tree'; equal[second] = 'D:/synthetic/tree'; invalid(equal);
      const nested = fixture(); nested[first] = 'D:/Synthetic/Tree'; nested[second] = 'D:/synthetic/tree/child'; invalid(nested);
    }
    for (const key of PROJECT) {
      const inside = fixture(); inside.sdkUmRoot = inside[key] + '/sdk'; invalid(inside);
      const outside = fixture(); outside.sdkUmRoot = 'D:/synthetic'; invalid(outside);
      for (const [tool, leaf] of [['compiler', 'cl.exe'], ['linker', 'link.exe'], ['manifestTool', 'mt.exe']]) {
        const c = fixture(); c[tool] = c[key] + '/tools/' + leaf; invalid(c);
      }
    }
    const peers = fixture(); peers.workerRoot = 'D:/tree'; peers.upstreamA = 'D:/tree-other'; eq(plan(peers), expected(peers));
    const unicode = fixture(); unicode.workerRoot = 'D:/tree/É'; unicode.upstreamA = 'D:/tree/é';
    eq(plan(unicode), expected(unicode)); // lexical ASCII folding, NOT filesystem alias qualification
    const normalization = fixture(); normalization.workerRoot = 'D:/tree/é'; normalization.upstreamA = 'D:/tree/e\u0301';
    eq(plan(normalization), expected(normalization));
  });
  add('R05', () => {
    const c = fixture(), result = structure(plan(c)); eq(result, expected(c));
    eq(result.candidates.map(x => x.id), ['A', 'B']);
    eq(result.steps.map(x => [x.index, x.candidate, x.stage]),
      [[0, 'A', 'compile'], [1, 'A', 'link'], [2, 'A', 'manifest'], [3, 'B', 'compile'], [4, 'B', 'link'], [5, 'B', 'manifest']]);
    result.steps.forEach(step => assert.equal(step.cwd, c.workerRoot));
    eq(result.steps.map(x => x.requiresPreEmbedCopy), [false, false, true, false, false, true]);
  });
  add('R06', () => {
    const c = fixture(), result = plan(c);
    for (const i of [0, 3]) {
      const step = result.steps[i], candidate = result.candidates[i / 3];
      assert.equal(step.tool, c.compiler); assert.equal(step.args.length, 31);
      eq(step.args, expectedCompile(c, candidate));
      eq(step.args.slice(0, 4), ['/nologo', '/TP', '-DGGML_USE_CPU', '/DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1']);
      eq(step.args.slice(-7), ['-std:c++17', '/showIncludes', '/Fo' + candidate.object,
        '/Fd' + candidate.compilerPdb, '/FS', '-c', 'main.cpp']);
    }
  });
  add('R07', () => {
    const c = fixture(); c.upstreamA = 'D:/synthetic/上流 A'; c.upstreamB = 'D:/synthetic/上流 B';
    const result = plan(c);
    for (const i of [0, 3]) {
      const root = result.candidates[i / 3].upstreamRoot;
      eq(result.steps[i].args.slice(4, 9), INCLUDES.map(p => '-I' + root + '/' + p));
      assert(result.steps[i].args[4].endsWith('/common/.'));
      assert(result.steps[i].args[5].endsWith('/vendor/nlohmann/..'));
      assert(result.steps[i].args[7].endsWith('/src/../include'));
      assert(result.steps[i].args[8].endsWith('/ggml/src/../include'));
    }
    eq(result, expected(c));
  });
  add('R08', () => {
    const c = fixture(), result = plan(c);
    for (const i of [1, 4]) {
      const candidate = result.candidates[(i - 1) / 3], step = result.steps[i];
      assert.equal(step.args.length, 29); assert.equal(step.tool, c.linker);
      eq(step.args.slice(12, 19), ARCHIVES.map(p => candidate.dependencyBuildRoot + '/' + p));
      eq(step.args.slice(19), SDK.map(p => c.sdkUmRoot + '/' + p)); eq(step.args, expectedLink(c, candidate));
      assert(!step.args.some(arg => arg.startsWith(result.candidates[1 - (i - 1) / 3].dependencyBuildRoot + '/')));
    }
  });
  add('R09', () => {
    const c = fixture(), result = plan(c);
    for (const i of [1, 4]) {
      const candidate = result.candidates[(i - 1) / 3];
      eq(result.steps[i].args.slice(0, 12), ['/nologo', candidate.object, '/out:' + candidate.executable,
        '/implib:' + candidate.importLibrary, '/pdb:' + candidate.linkerPdb, '/version:0.0', '/machine:x64',
        '/INCREMENTAL:NO', '/subsystem:console', '/Brepro', '/MANIFEST', '/MANIFESTFILE:' + candidate.manifest]);
      for (const prefix of ['/NODEFAULTLIB', '/LINKREPRO', '/MANIFEST:NO', '/MANIFEST:EMBED', '/MANIFEST:UAC']) {
        assert(!result.steps[i].args.some(arg => arg.toUpperCase().startsWith(prefix.toUpperCase())));
      }
    }
  });
  add('R10', () => {
    const c = fixture(), result = plan(c);
    for (const i of [2, 5]) {
      const candidate = result.candidates[(i - 2) / 3], step = result.steps[i];
      eq(step.args, ['/nologo', '/manifest', candidate.manifest, '/outputresource:' + candidate.executable + ';#1']);
      assert.equal(step.args.length, 4); assert.equal(step.tool, c.manifestTool); assert.equal(step.requiresPreEmbedCopy, true);
      assert.equal(step.args.filter(arg => arg.includes(';#1')).length, 1);
      assert(!step.args.some(arg => arg.includes('"')));
    }
    eq(result.steps.map(x => x.stage), ['compile', 'link', 'manifest', 'compile', 'link', 'manifest']);
    assert(!result.steps.some(step => /(?:^|\/)rc\.exe$/i.test(step.tool)));
  });
  add('R11', () => {
    const c = fixture(), result = plan(c), all = [];
    result.candidates.forEach((candidate, i) => {
      eq(candidate, expectedCandidate(c, ['A', 'B'][i]));
      const paths = ['object', 'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'].map(key => candidate[key]);
      assert.equal(new Set(paths).size, 7); paths.forEach(p => assert(p.startsWith(candidate.outputRoot + '/'))); all.push(...paths);
      assert.notEqual(candidate.executable, candidate.preEmbedCopy);
      assert(!result.steps.some(step => step.args.includes(candidate.preEmbedCopy)));
      assert.equal(result.steps[i * 3 + 2].requiresPreEmbedCopy, true);
    });
    assert.equal(new Set(all).size, 14); assert.notEqual(result.candidates[0].outputRoot, result.candidates[1].outputRoot);
  });
  add('R12', () => {
    const leaves = { compiler: 'cl.exe', linker: 'link.exe', manifestTool: 'mt.exe' };
    for (let i = 0; i < CONFIG.length; i++) {
      const key = CONFIG[i], leaf = leaves[key] ?? null, drive = PROJECT.includes(key) ? 'D' : 'C';
      const positive = fixture(); positive[key] = boundedPath(1024, String.fromCharCode(97 + i), leaf, drive);
      const wanted = expected(positive); assert(wanted.steps.every(step => argvBytes(step.args) <= 24576));
      assert(bytes(JSON.stringify(wanted)) <= 65536); eq(structure(plan(positive)), wanted);
      const over = fixture(); over[key] = boundedPath(1025, String.fromCharCode(97 + i), leaf, drive); limit(over);
    }
    for (const component of ['u'.repeat(255), 'é'.repeat(127) + 'u']) {
      assert.equal(bytes(component), 255); const c = fixture(); c.workerRoot = 'D:/' + component;
      eq(plan(c), expected(c));
    }
    for (const component of ['u'.repeat(256), 'é'.repeat(128)]) {
      assert.equal(bytes(component), 256); limit({ ...fixture(), workerRoot: 'D:/' + component });
    }
    const maximal = fixture();
    [...PROJECT, 'sdkUmRoot'].forEach((key, i) => { maximal[key] = boundedPath(1024, String.fromCharCode(97 + i), null,
      key === 'sdkUmRoot' ? 'C' : 'D'); });
    const oversized = expected(maximal), encoded = JSON.stringify(oversized);
    assert(oversized.steps.every(step => argvBytes(step.args) <= 24576));
    assert(bytes(encoded) > 65536); assert(bytes(encoded) + bytes(JSON.stringify(maximal)) < 128 * 1024);
    limit(maximal); // whole-output bound, not silently dropped arguments
  });
  add('R13', () => {
    const c = fixture(); c.workerRoot = 'D:/synthetic/作成 一'; c.upstreamA = 'D:/synthetic/上流 一';
    const result = plan(c);
    for (const i of [0, 3]) {
      const candidate = result.candidates[i / 3]; eq(result.steps[i].args.slice(18, 24), expectedMaps(c, candidate));
      eq(result.steps[i].args.slice(18, 24).map(arg => arg.slice(arg.indexOf('=') + 1)),
        ['X:\\locallore\\worker', 'X:\\locallore\\worker', 'X:\\locallore\\llama', 'X:\\locallore\\llama',
          'X:\\locallore\\build', 'X:\\locallore\\build']);
      assert(result.steps[i].args[18].includes(c.workerRoot));
      assert(result.steps[i].args[19].includes(c.workerRoot.replaceAll('/', '\\')));
      assert(!result.steps[i].args.some(arg => arg.includes('"')));
    }
  });
  add('R14', () => {
    const c = fixture(), before = clone(c), first = plan(c), saved = clone(first), second = plan(c);
    eq(c, before); eq(first, second); assert.notEqual(first, second); assert.notEqual(first.candidates, second.candidates);
    frozen(first); assert.throws(() => first.steps[0].args.push('/arbitrary'), TypeError);
    assert.throws(() => { first.candidates[0].object = 'D:/other.obj'; }, TypeError);
    c.workerRoot = 'D:/synthetic/later-worker'; eq(first, saved); eq(plan(c), expected(c));
    const ordinary = plan(Object.freeze(fixture())); eq(ordinary, expected(fixture()));
  });
  add('R15', () => {
    for (const extra of ['args', 'flags', 'mode', 'command', 'shell', 'source', 'output', 'copy', 'runner']) {
      invalid({ ...fixture(), [extra]: ['anything'] });
    }
    for (const compiler of ['C:/synthetic-tools/cl.exe /arbitrary', 'C:/synthetic-tools/cmd.exe',
      'C:/synthetic-tools/@response.rsp', 'C:/synthetic-tools/cl.exe;anything']) invalid({ ...fixture(), compiler });
    const result = plan(fixture());
    assert(result.steps.every(step => step.args.every(arg => !arg.startsWith('@'))));
    assert(!JSON.stringify(result).includes('cmd.exe')); assert(!JSON.stringify(result).includes('cmake.exe'));
    assert(!JSON.stringify(result).includes('ninja.exe')); assert(!Object.hasOwn(result, 'execute'));
  });
  add('R16', () => {
    const c = fixture(), result = plan(c);
    for (const key of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(result[key], false);
    assert.equal(result.requiresFreshAdmission, true); assert.equal(result.normalWorkerUnchangedRequired, true);
    for (const candidate of result.candidates) {
      assert(candidate.outputRoot.startsWith(c.targetRoot + '/worker-author-b2-candidate-'));
      assert(candidate.executable.endsWith('/locallore-author-worker.exe'));
      assert(!Object.hasOwn(candidate, 'profile')); assert(!Object.hasOwn(candidate, 'normalWorker'));
      assert.notEqual(candidate.outputRoot, c.workerRoot); assert.notEqual(candidate.outputRoot, candidate.dependencyBuildRoot);
    }
    eq(result, expected(c)); assert(!Object.hasOwn(result, 'adopt')); assert(!Object.hasOwn(result, 'release'));
    assert(result.steps.every(step => step.cwd === c.workerRoot));
  });

  eq(cases.map(([id]) => id), Array.from({ length: 16 }, (_, i) => 'R' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, run] of cases) { try { await run(); } catch { failed_case_ids.push(id); } }
  return { version: 1, kind: 'worker_artifact_recipe_first_v1', executed: 16,
    passed: 16 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
