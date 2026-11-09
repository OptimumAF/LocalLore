// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { addAbortListener } from 'node:events';
import { lstat, open, realpath } from 'node:fs/promises';
import { win32 } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createWorkerArtifactCompileHostV1 } from './worker_artifact_compile_host_v1.mjs';
import { createWorkerArtifactCompileObservationV1 } from './worker_artifact_compile_observation_v1.mjs';
import { createWorkerArtifactCompileSupervisorV1 } from './worker_artifact_compile_supervisor_v1.mjs';
import { createWorkerArtifactHeldOutputsV1 } from './worker_artifact_held_outputs_v1.mjs';
import { createWorkerArtifactOutputRootsV1 } from './worker_artifact_output_roots_v1.mjs';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const CONFIG = ['compiler', 'linker', 'manifestTool', 'workerRoot', 'upstreamA', 'upstreamB',
  'buildA', 'buildB', 'targetRoot', 'sdkUmRoot'];
const AUTHORITY = ['attempt', 'baseline', 'closure', 'grant'];
const ENV = ['windows', 'path', 'include', 'temp'];
const PROFILE = ['config', 'authority', 'environment', 'node', 'helper', 'entry', 'evidenceRoot',
  'outputParentIdentity', 'outputMaxBytes', 'spend', 'writerPolicy', 'namespace'];
const READY = ['version', 'kind', 'scope', 'spend', 'writerPolicy', 'namespace', 'evidenceId',
  'tempId', 'parentPid', 'nodePid', 'jobFlags', 'parentInJob', 'activeProcesses', 'pins'];
const ENTRY_MAX = 2 * 1024 * 1024;
const READY_MAX = 4096;
const U64 = (1n << 64n) - 1n;
const ENTRY = 'worker_artifact_compile_attempt_v1.mjs';
const HELPER = 'locallore-compile-host-v1.exe';
const NODE = 'node.exe';

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const jsonSha = value => sha(JSON.stringify(value));
const int = (value, lo, hi) => Number.isSafeInteger(value) && value >= lo && value <= hi;
const digest = value => typeof value === 'string' && value.length === 64 &&
  !/[^0-9a-f]/.test(value) && value !== '0'.repeat(64);

function requireAttempt(ok) {
  if (!ok) throw Error('WorkerArtifactCompileAttemptV1');
}

function data(value, fields) {
  requireAttempt(value !== null && typeof value === 'object' &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value)));
  const keys = Reflect.ownKeys(value);
  requireAttempt(keys.length === fields.length && keys.every(key => fields.includes(key)));
  return Object.fromEntries(fields.map(key => {
    const field = Object.getOwnPropertyDescriptor(value, key);
    requireAttempt(field?.enumerable && Object.hasOwn(field, 'value'));
    return [key, field.value];
  }));
}

function decimal(value, positive = false) {
  return /^(?:0|[1-9][0-9]{0,19})$/.test(value) && !/[^0-9]/.test(value) &&
    (!positive || value !== '0') && BigInt(value) <= U64;
}

function identity(value, native) {
  requireAttempt(typeof value === 'string' && value.length <= 53);
  const parts = value.split(':');
  requireAttempt(parts.length === 2 && decimal(parts[0]));
  requireAttempt(native ? parts[1].length === 32 && !/[^0-9a-f]/.test(parts[1]) &&
    parts[1] !== '0'.repeat(32) : decimal(parts[1], true));
  return parts[0];
}

function path(value, project) {
  requireAttempt(typeof value === 'string' && Buffer.byteLength(value) <= 1024 &&
    Buffer.from(value).toString('utf8') === value &&
    (project ? value.startsWith('D:/') : /^[CD]:\//.test(value)) &&
    value.slice(3).split('/').every(part => part.length > 0 && Buffer.byteLength(part) <= 255 &&
      !/[\x00-\x1f\x7f:"\\*?<>|;,=&#\x60]/.test(part) && !/[ .]$/.test(part) &&
      !/^(?:con|prn|aux|nul|conin\$|conout\$|(?:com|lpt)[1-9¹²³])$/i.test(part.split('.')[0].trimEnd())));
  return value;
}

const comparable = value => value.replaceAll('\\', '/').toLowerCase();
const samePath = (left, right) => typeof left === 'string' && comparable(left) === comparable(right);

function disjoint(left, right) {
  const a = comparable(left), b = comparable(right);
  return a !== b && !a.startsWith(b + '/') && !b.startsWith(a + '/');
}

function pin(value, leaf, cap) {
  const fact = data(value, ['path', 'bytes', 'sha256']);
  requireAttempt(path(fact.path, true).endsWith('/' + leaf) &&
    int(fact.bytes, 1, cap) && digest(fact.sha256));
  return Object.freeze(fact);
}

function setup(value) {
  const input = data(value, PROFILE);
  const config = Object.freeze(data(input.config, CONFIG));
  const authority = Object.freeze(data(input.authority, AUTHORITY));
  const environment = Object.freeze(data(input.environment, ENV));
  const recipe = planWorkerArtifactComparisonV1(config);
  requireAttempt([...Object.values(authority), input.spend, input.writerPolicy, input.namespace].every(digest));
  const node = pin(input.node, NODE, 128 * 1024 * 1024);
  const helper = pin(input.helper, HELPER, 8 * 1024 * 1024);
  const entry = path(input.entry, true), evidenceRoot = path(input.evidenceRoot, true);
  const temp = path(environment.temp, true);
  path(environment.windows, false);
  requireAttempt(entry.endsWith('/' + ENTRY) &&
    [environment.path, environment.include].every(value => typeof value === 'string' && value.length <= 16384 &&
      value.split(';').every(part => path(part, false))) &&
    int(input.outputMaxBytes, 334, 67108864));
  identity(input.outputParentIdentity, false);
  const writable = [evidenceRoot, temp, config.targetRoot];
  requireAttempt(writable.every((root, i) => writable.slice(i + 1).every(other => disjoint(root, other))) &&
    writable.every(root => [node.path, entry, helper.path]
      .every(file => disjoint(root, file.slice(0, file.lastIndexOf('/'))))));
  const profile = Object.freeze({ config, authority, environment, node, helper, entry, evidenceRoot,
    outputParentIdentity: input.outputParentIdentity, outputMaxBytes: input.outputMaxBytes,
    spend: input.spend, writerPolicy: input.writerPolicy, namespace: input.namespace });
  const context = Object.freeze({ attempt: authority.attempt, recipe: jsonSha(recipe),
    baseline: authority.baseline, closure: authority.closure, grant: authority.grant });
  return { profile, context, scope: jsonSha({ version: 1, kind: 'compile_attempt_scope_v1', profile, context }) };
}

// The enclosing owner binds this digest to its retained plan before building the sealed entry.
export function workerArtifactCompileAttemptScopeV1(profile) {
  return setup(profile).scope;
}

function verifyReady(text, prepared, observed) {
  const { profile, context, scope } = prepared;
  const { pid, ppid, entryBytes, entrySha256 } = data(observed, ['pid', 'ppid', 'entryBytes', 'entrySha256']);
  requireAttempt(int(pid, 1, 2147483647) && int(ppid, 1, 2147483647) && pid !== ppid &&
    int(entryBytes, 1, ENTRY_MAX) && digest(entrySha256) &&
    typeof text === 'string' && Buffer.byteLength(text) <= READY_MAX);
  const ready = data(JSON.parse(text), READY);
  requireAttempt(ready.version === 1 && ready.kind === 'compile_parent_ready_v1' &&
    ready.scope === scope && ready.spend === profile.spend && ready.writerPolicy === profile.writerPolicy &&
    ready.namespace === profile.namespace && ready.nodePid === pid && ready.parentPid === ppid &&
    ready.jobFlags === 0x2000 && typeof ready.parentInJob === 'boolean' && ready.activeProcesses === 1 &&
    Array.isArray(ready.pins) && ready.pins.length === 3);
  const expected = [profile.node, { bytes: entryBytes, sha256: entrySha256 }, profile.helper];
  const pins = ready.pins.map((value, index) => {
    const pin = data(value, ['id', 'sha256', 'bytes']);
    requireAttempt(pin.sha256 === expected[index].sha256 && pin.bytes === expected[index].bytes);
    return Object.freeze(pin);
  });
  const ids = [ready.evidenceId, ready.tempId, ...pins.map(pin => pin.id)];
  const volumes = ids.map(id => identity(id, true));
  requireAttempt(new Set(ids).size === ids.length && volumes.every(volume => volume === volumes[0]));
  ready.pins = Object.freeze(pins);
  requireAttempt(JSON.stringify(ready) === text);
  const readyHash = sha(text);
  return Object.freeze({ scope, context, readyHash, ready: Object.freeze(ready), profile });
}

export function verifyWorkerArtifactCompileParentReadyV1(text, profile, observed) {
  return verifyReady(text, setup(profile), observed);
}

const statOptions = { bigint: true };
const localIdentity = stat => stat.dev.toString() + ':' + stat.ino.toString();
const stamp = stat => [stat.dev, stat.ino, stat.size, stat.mtimeNs, stat.ctimeNs, stat.mode].join(':');

async function named(file, directory) {
  const stat = await lstat(file, statOptions);
  requireAttempt(stat.ino > 0n && !stat.isSymbolicLink() &&
    (directory ? stat.isDirectory() : stat.isFile() && stat.nlink === 1n) &&
    samePath(await realpath(file), file));
  return stat;
}

async function readPinned(file, maximum, signal) {
  requireAttempt(!signal.aborted);
  const expected = await named(file, false);
  requireAttempt(expected.size > 0n && expected.size <= BigInt(maximum) && !signal.aborted);
  const bytes = Buffer.alloc(Number(expected.size));
  const handle = await open(file, 'r');
  try {
    const initial = await handle.stat(statOptions);
    requireAttempt(initial.isFile() && initial.nlink === 1n && stamp(initial) === stamp(expected));
    for (let offset = 0; offset < bytes.length;) {
      requireAttempt(!signal.aborted);
      const wanted = Math.min(bytes.length - offset, 65536);
      const { bytesRead } = await handle.read(bytes, offset, wanted, offset);
      requireAttempt(int(bytesRead, 1, wanted));
      offset += bytesRead;
    }
    const extra = await handle.read(Buffer.alloc(1), 0, 1, bytes.length);
    requireAttempt(extra.bytesRead === 0 && stamp(await handle.stat(statOptions)) === stamp(expected));
  } finally {
    await handle.close();
  }
  requireAttempt(!signal.aborted && stamp(await named(file, false)) === stamp(expected));
  return bytes;
}

let used = false;

// Only the sealed bootstrap calls this entry. Importing it performs no I/O.
export async function runWorkerArtifactCompileAttemptV1(profile, owner, sourceSignal) {
  requireAttempt(!used);
  used = true;
  const prepared = setup(profile);
  const { profile: pinned, context } = prepared;
  const { check, excludeWriters } = data(owner, ['check', 'excludeWriters']);
  const signal = AbortSignal.any([sourceSignal]);
  requireAttempt(typeof check === 'function' && typeof excludeWriters === 'function' &&
    process.platform === 'win32' && process.arch === 'x64' && process.versions.node === '24.22.1' &&
    process.argv.length === 2 && process.execArgv.length === 0 &&
    !process.env.NODE_OPTIONS && !process.env.NODE_V8_COVERAGE &&
    samePath(process.execPath, pinned.node.path) && samePath(process.argv[1], pinned.entry) &&
    samePath(fileURLToPath(import.meta.url), pinned.entry) &&
    samePath(process.env.SystemRoot, pinned.environment.windows) &&
    samePath(process.env.TEMP, pinned.environment.temp) && samePath(process.env.TMP, pinned.environment.temp));
  const readyPath = win32.join(pinned.evidenceRoot, 'parent-ready.json');
  requireAttempt(samePath(process.env.LOCALLORE_COMPILE_PARENT_READY, readyPath));
  const evidenceIdentity = localIdentity(await named(pinned.evidenceRoot, true));
  const ready = await readPinned(readyPath, READY_MAX, signal);
  const ownEntry = await readPinned(pinned.entry, ENTRY_MAX, signal);
  const text = new TextDecoder('utf-8', { fatal: true, ignoreBOM: true }).decode(ready);
  const admitted = verifyReady(text, prepared, { pid: process.pid, ppid: process.ppid,
    entryBytes: ownEntry.length, entrySha256: sha(ownEntry) });
  requireAttempt(localIdentity(await named(pinned.evidenceRoot, true)) === evidenceIdentity &&
    localIdentity(await named(pinned.config.targetRoot, true)) === pinned.outputParentIdentity);

  const supervisor = createWorkerArtifactCompileSupervisorV1({
    context, hostHash: pinned.helper.sha256, hostDirectory: pinned.helper.path.slice(0, pinned.helper.path.lastIndexOf('/')),
    evidenceRoot: pinned.evidenceRoot, windows: pinned.environment.windows, temp: pinned.environment.temp,
    admission: { job: admitted.readyHash, spend: pinned.spend, writerPolicy: pinned.writerPolicy,
      namespace: pinned.namespace, hostLease: admitted.readyHash }
  });
  const host = createWorkerArtifactCompileHostV1({
    config: pinned.config, authority: pinned.authority, environment: pinned.environment, hostHash: pinned.helper.sha256,
    ports: { authorize: supervisor.authorize, transport: supervisor.transport, retain: supervisor.retain,
      excludeWriters: request => excludeWriters(request, admitted) }
  });
  const outputRoots = createWorkerArtifactOutputRootsV1({ config: pinned.config,
    attemptSha256: pinned.authority.attempt, parentIdentity: pinned.outputParentIdentity, maxBytes: pinned.outputMaxBytes });
  const outputReader = createWorkerArtifactHeldOutputsV1({ config: pinned.config });
  const observation = createWorkerArtifactCompileObservationV1({ config: pinned.config, authority: pinned.authority,
    outputRoots, outputReader,
    ports: { check: async (request, guardSignal) => {
      const lease = request.when === 'admit' ? null : outputRoots.snapshot();
      const receipt = await check(request, guardSignal, admitted, lease);
      await supervisor.recordCheck(request.when, receipt);
      requireAttempt(!guardSignal.aborted);
      return receipt;
    },
      journal: supervisor.journal, launch: host.launch }
  });

  const cancel = addAbortListener(signal, () => observation.cancel());
  try {
    if (signal.aborted) observation.cancel();
    const { report, retained } = await observation.run();
    return Object.freeze({ version: 1, kind: 'compile_attempt_result_v1', scope: admitted.scope,
      parentReady: admitted.readyHash, report, retained });
  } finally {
    cancel[Symbol.dispose]();
  }
}
