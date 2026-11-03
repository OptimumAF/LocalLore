// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Pure experimental argument DATA; no launch, file, environment or admission API.
const INVALID = 'WorkerArtifactRecipeV1Invalid', LIMIT = 'WorkerArtifactRecipeV1Limit';
const CONFIG = ['compiler', 'linker', 'manifestTool', 'workerRoot', 'upstreamA', 'upstreamB',
  'buildA', 'buildB', 'targetRoot', 'sdkUmRoot'];
const PROJECT = ['workerRoot', 'upstreamA', 'upstreamB', 'buildA', 'buildB', 'targetRoot'];
const TOOLS = ['compiler', 'linker', 'manifestTool'];
const INCLUDES = ['common/.', 'vendor/nlohmann/..', 'vendor/sheredom/..', 'src/../include', 'ggml/src/../include'];
const ARCHIVES = ['llama/common/llama-common.lib', 'llama/src/llama.lib', 'llama/ggml/src/ggml.lib',
  'llama/ggml/src/ggml-cpu.lib', 'llama/ggml/src/ggml-base.lib',
  'llama/common/llama-common-base.lib', 'llama/vendor/cpp-httplib/cpp-httplib.lib'];
const SDK = ['kernel32.lib', 'user32.lib', 'gdi32.lib', 'winspool.lib', 'shell32.lib',
  'ole32.lib', 'oleaut32.lib', 'uuid.lib', 'comdlg32.lib', 'advapi32.lib'];
const FORBIDDEN = [34, 92, 58, 42, 63, 61, 44, 59, 35, 96, 60, 62, 124, 38];
const bytes = v => Buffer.byteLength(v, 'utf8');
const check = (v, code = INVALID) => { if (!v) throw Error(code); };
const fold = v => v.replace(/[A-Z]/g, c => String.fromCharCode(c.charCodeAt(0) + 32));
const contains = (root, path) => fold(root) === fold(path) || fold(path).startsWith(fold(root) + '/');
const overlaps = (a, b) => contains(a, b) || contains(b, a);
function configData(value) {
  try {
    check(value !== null && typeof value === 'object' &&
      [Object.prototype, null].includes(Object.getPrototypeOf(value)));
    const keys = Reflect.ownKeys(value);
    check(keys.length === CONFIG.length && keys.every(k => typeof k === 'string' && CONFIG.includes(k)));
    const copy = {};
    for (const key of CONFIG) {
      const d = Object.getOwnPropertyDescriptor(value, key);
      check(d !== undefined && d.enumerable && Object.hasOwn(d, 'value') && typeof d.value === 'string');
      copy[key] = d.value;
    }
    return copy;
  } catch { throw Error(INVALID); }
}
function pathData(path, project, leaf = null) {
  check(bytes(path) <= 1024, LIMIT);
  check(/^[CD]:\//.test(path) && (!project || path.startsWith('D:/')));
  const tail = path.slice(3);
  for (const char of tail) {
    const code = char.charCodeAt(0); check(code >= 32 && code !== 127 && !FORBIDDEN.includes(code));
  }
  const parts = tail.split('/');
  for (const part of parts) {
    check(bytes(part) <= 255, LIMIT);
    check(part.length > 0 && part !== '.' && part !== '..' && !part.endsWith(' ') && !part.endsWith('.'));
    const base = fold(part.split('.')[0].replace(/ +$/, ''));
    check(!/^(?:con|prn|aux|nul|(?:com|lpt)[1-9¹²³])$/.test(base));
  }
  if (leaf !== null) check(parts[parts.length - 1] === leaf);
}
function freeze(value) {
  if (value !== null && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}
function candidate(config, id) {
  const outputRoot = config.targetRoot + '/worker-author-b2-candidate-' + id.toLowerCase();
  return { id, upstreamRoot: config['upstream' + id], dependencyBuildRoot: config['build' + id], outputRoot,
    object: outputRoot + '/main.cpp.obj', executable: outputRoot + '/locallore-author-worker.exe',
    preEmbedCopy: outputRoot + '/locallore-author-worker.pre-embed.exe',
    manifest: outputRoot + '/locallore-author-worker.exe.manifest', compilerPdb: outputRoot + '/compile.pdb',
    linkerPdb: outputRoot + '/link.pdb', importLibrary: outputRoot + '/locallore-author-worker.lib' };
}
function compileArgs(config, c) {
  const maps = [[config.workerRoot, 'X:\\locallore\\worker'], [c.upstreamRoot, 'X:\\locallore\\llama'],
    [c.outputRoot, 'X:\\locallore\\build']].flatMap(([source, virtual]) =>
    ['/pathmap:' + source + '=' + virtual, '/pathmap:' + source.replaceAll('/', '\\') + '=' + virtual]);
  return ['/nologo', '/TP', '-DGGML_USE_CPU', '/DLOCALLORE_INITIAL_WORLD_EXPERIMENTAL_V1=1',
    ...INCLUDES.map(p => '-I' + c.upstreamRoot + '/' + p), '/DWIN32', '/D_WINDOWS', '/EHsc', '/O2',
    '/Ob2', '/DNDEBUG', '-MD', '/Brepro', '/experimental:deterministic', ...maps, '-std:c++17', '/showIncludes',
    '/Fo' + c.object, '/Fd' + c.compilerPdb, '/FS', '-c', 'main.cpp'];
}
function linkArgs(config, c) {
  return ['/nologo', c.object, '/out:' + c.executable, '/implib:' + c.importLibrary, '/pdb:' + c.linkerPdb,
    '/version:0.0', '/machine:x64', '/INCREMENTAL:NO', '/subsystem:console', '/Brepro', '/MANIFEST',
    '/MANIFESTFILE:' + c.manifest, ...ARCHIVES.map(p => c.dependencyBuildRoot + '/' + p),
    ...SDK.map(p => config.sdkUmRoot + '/' + p)];
}

export function planWorkerArtifactComparisonV1(value) {
  const c = configData(value);
  for (const key of PROJECT) pathData(c[key], true);
  for (const [key, leaf] of [['compiler', 'cl.exe'], ['linker', 'link.exe'], ['manifestTool', 'mt.exe']]) pathData(c[key], false, leaf);
  pathData(c.sdkUmRoot, false);
  for (let i = 0; i < PROJECT.length; i++) {
    for (let j = i + 1; j < PROJECT.length; j++) check(!overlaps(c[PROJECT[i]], c[PROJECT[j]]));
    check(!overlaps(c[PROJECT[i]], c.sdkUmRoot));
    for (const key of TOOLS) check(!contains(c[PROJECT[i]], c[key]));
  }
  const candidates = ['A', 'B'].map(id => candidate(c, id)), steps = [];
  for (const item of candidates) {
    steps.push({ index: steps.length, candidate: item.id, stage: 'compile', tool: c.compiler, cwd: c.workerRoot,
      args: compileArgs(c, item), requiresPreEmbedCopy: false });
    steps.push({ index: steps.length, candidate: item.id, stage: 'link', tool: c.linker, cwd: c.workerRoot,
      args: linkArgs(c, item), requiresPreEmbedCopy: false });
    steps.push({ index: steps.length, candidate: item.id, stage: 'manifest', tool: c.manifestTool, cwd: c.workerRoot,
      args: ['/nologo', '/manifest', item.manifest, '/outputresource:' + item.executable + ';#1'], requiresPreEmbedCopy: true });
  }
  for (const step of steps) check(step.args.reduce((sum, arg) => sum + bytes(arg) + 3, 0) <= 24576, LIMIT);
  const output = { version: 1, kind: 'worker_artifact_recipe_v1', purpose: 'experimental_worker_artifact_only',
    qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true,
    normalWorkerUnchangedRequired: true, candidates, steps };
  check(bytes(JSON.stringify(output)) <= 65536, LIMIT);
  return freeze(output);
}
