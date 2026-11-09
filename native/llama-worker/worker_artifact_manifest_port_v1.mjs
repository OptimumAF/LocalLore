// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactManifestPortV1';
const CONTEXT = ['attempt', 'recipe', 'baseline', 'closure'];
const OUTPUTS = ['object', 'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'];
const COPY_FAILURES = ['INPUT', 'CLOCK', 'DEADLINE', 'CANCELLED', 'IO', 'IDENTITY', 'CONTENT', 'CLOSE'];
const LEASE_FAILURES = ['Cancelled', 'Deadline', 'Clock', 'Limit', 'Exists', 'Identity', 'Marker', 'Roster', 'Budget', 'IO', 'Closure'];
const LEASE_FIELDS = ['version', 'kind', 'qualified', 'state', 'pending', 'stop', 'rechecks', 'withinBudget', 'observedBytes', 'roots'];
const ROOT_FIELDS = ['candidate', 'creation', 'identity', 'marker', 'markerClosure', 'directoryClosure', 'complete', 'files'];
const COPY_FIELDS = ['version', 'kind', 'candidate', 'ok', 'code', 'executable', 'manifest', 'copy', 'io', 'unknownClosure', 'ioUncertain',
  'qualified', 'linkQualification', 'closureComplete', 'requiresFreshAdmission', 'normalWorkerUnchangedRequired'];
const IO_FIELDS = ['reservedCopies', 'reservedReadBytes', 'reservedWriteBytes', 'actualReadBytes', 'actualWriteBytes',
  'openAttempts', 'opened', 'closeAttempts', 'closed', 'unknownClosures', 'verifiedScans'];
const MARKER = '.locallore-output-owner-v1';
const MAX = 67108864;
const U64 = (1n << 64n) - 1n;
const STOP = Symbol('manifest port stopped');
const BAD_DATA = Symbol('malformed manifest data');
const signalAborted = Object.getOwnPropertyDescriptor(AbortSignal.prototype, 'aborted').get;
const followSignals = AbortSignal.any;
const addListener = EventTarget.prototype.addEventListener;
const removeListener = EventTarget.prototype.removeEventListener;

function record(value, names) {
  if (value === null || typeof value !== 'object' ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(value))) throw BAD_DATA;
  const keys = Reflect.ownKeys(value);
  if (keys.length !== names.length || keys.some(key => !names.includes(key))) throw BAD_DATA;
  const copy = Object.create(null);
  for (const name of names) {
    const d = Object.getOwnPropertyDescriptor(value, name);
    if (!d?.enumerable || !Object.hasOwn(d, 'value')) throw BAD_DATA;
    copy[name] = d.value;
  }
  return copy;
}

function method(owner, name) {
  const d = Object.getOwnPropertyDescriptor(owner, name);
  if (!d || !Object.hasOwn(d, 'value') || typeof d.value !== 'function') throw BAD_DATA;
  const fn = d.value;
  return (...args) => Reflect.apply(fn, owner, args);
}

function boundedArray(value, min, max) {
  if (!Array.isArray(value)) throw BAD_DATA;
  const length = Object.getOwnPropertyDescriptor(value, 'length')?.value;
  if (!Number.isInteger(length) || length < min || length > max ||
      Reflect.ownKeys(value).length !== length + 1) throw BAD_DATA;
  const entries = [];
  for (let i = 0; i < length; i++) {
    const entry = Object.getOwnPropertyDescriptor(value, String(i));
    if (!entry?.enumerable || !Object.hasOwn(entry, 'value')) throw BAD_DATA;
    entries.push(entry.value);
  }
  return entries;
}

const digest = value => typeof value === 'string' && value.length === 64 &&
  !/[^a-f0-9]/.test(value) && value !== '0'.repeat(64);
const within = (value, max) => Number.isSafeInteger(value) && value >= 1 && value <= max;
const equal = (left, right) => left.sha256 === right.sha256 && left.bytes === right.bytes;
const sha = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');

function fact(value, maximum = MAX) {
  const f = record(value, ['sha256', 'bytes']);
  if (!digest(f.sha256) || !within(f.bytes, maximum)) throw BAD_DATA;
  return Object.freeze({ sha256: f.sha256, bytes: f.bytes });
}

function matchesStep(value, expected) {
  const step = record(value, Object.keys(expected));
  for (const [key, item] of Object.entries(expected)) {
    if (key !== 'args' && step[key] !== item) return false;
  }
  const args = step.args;
  if (!Array.isArray(args) || args.length !== expected.args.length ||
      Reflect.ownKeys(args).length !== args.length + 1) return false;
  return expected.args.every((item, index) => {
    const entry = Object.getOwnPropertyDescriptor(args, String(index));
    return entry?.enumerable && Object.hasOwn(entry, 'value') && entry.value === item;
  });
}

function decimal(text, maximum = U64) {
  if (typeof text !== 'string' || text.length < 1 || text.length > 20 || /[^0-9]/.test(text)) return null;
  const value = BigInt(text);
  return value <= maximum && value.toString() === text ? value : null;
}

function identity(text) {
  if (typeof text !== 'string' || text.length > 41) return false;
  const parts = text.split(':');
  if (parts.length !== 2) return false;
  const [device, file] = parts.map(decimal);
  return device !== null && file !== null && file > 0n;
}

function leaseSnapshot(value) {
  const view = record(value, LEASE_FIELDS);
  const ready = view.state === 'Ready';
  const stopped = view.state === 'Stopped';
  const total = decimal(view.observedBytes, U64 + BigInt(MAX));
  if (view.version !== 1 || view.kind !== 'worker_artifact_output_roots_v1' ||
      view.qualified !== false || view.pending !== null ||
      (!ready && !stopped) || view.withinBudget !== ready ||
      (ready ? view.stop !== null : !LEASE_FAILURES.includes(view.stop)) ||
      !within(view.rechecks, 32) || total === null) throw BAD_DATA;
  let observed = 0n;
  const roots = boundedArray(view.roots, 2, 2).map((value, index) => {
    const root = record(value, ROOT_FIELDS);
    if (root.candidate !== (index === 0 ? 'A' : 'B') || root.creation !== 'created' ||
        !identity(root.identity) || root.marker !== 'created' ||
        !['open', 'unknown'].includes(root.markerClosure) ||
        !['none', 'closed', 'unknown'].includes(root.directoryClosure) ||
        typeof root.complete !== 'boolean' ||
        (root.complete && root.directoryClosure !== 'closed') ||
        (ready && (!root.complete || root.markerClosure !== 'open'))) throw BAD_DATA;
    const files = boundedArray(root.files, 0, 8).map(value => {
      const row = record(value, ['name', 'identity', 'bytes']);
      const bytes = decimal(row.bytes);
      if (typeof row.name !== 'string' || row.name.length < 1 || row.name.length > 255 ||
          !identity(row.identity) || bytes === null) throw BAD_DATA;
      observed += bytes;
      return { name: row.name, identity: row.identity, bytes };
    });
    return { ...root, files };
  });
  if (observed !== total) throw BAD_DATA;
  return { ready, roots, total };
}

function copySnapshot(value) {
  const proof = record(value, COPY_FIELDS);
  const io = record(proof.io, IO_FIELDS);
  if (proof.version !== 1 || proof.kind !== 'worker_artifact_preembed_copy_v1' ||
      proof.qualified !== false || proof.linkQualification !== false || proof.closureComplete !== false ||
      proof.requiresFreshAdmission !== true || proof.normalWorkerUnchangedRequired !== true ||
      typeof proof.ok !== 'boolean' || typeof proof.unknownClosure !== 'boolean' ||
      typeof proof.ioUncertain !== 'boolean') throw BAD_DATA;
  for (const key of IO_FIELDS) {
    const value = io[key];
    if (Number.isSafeInteger(value) && value >= 0) continue;
    if (key === 'actualReadBytes' || key === 'actualWriteBytes') {
      const exact = decimal(value);
      if (exact !== null && exact > BigInt(Number.MAX_SAFE_INTEGER)) continue;
    }
    throw BAD_DATA;
  }
  if (proof.unknownClosure !== (io.unknownClosures > 0) || io.opened > io.openAttempts ||
      io.closeAttempts > io.opened || io.closed > io.closeAttempts ||
      (!proof.unknownClosure && io.closed !== io.openAttempts)) throw BAD_DATA;
  if (!proof.ioUncertain) {
    const extraProbe = !proof.ok && io.reservedCopies === 1 && io.reservedReadBytes > 0 && io.opened > 0 ? 1n : 0n;
    if (BigInt(io.actualWriteBytes) > BigInt(io.reservedWriteBytes) ||
        BigInt(io.actualReadBytes) > BigInt(io.reservedReadBytes) + extraProbe) throw BAD_DATA;
  }
  return { ...proof, io };
}

function setup(value) {
  try {
    const spec = record(value, ['config', 'context', 'outputRoots', 'preembedCopy', 'maxBytes']);
    const recipe = planWorkerArtifactComparisonV1(spec.config);
    const context = record(spec.context, CONTEXT);
    if (!within(spec.maxBytes, MAX) || !CONTEXT.every(key => digest(context[key])) ||
        context.recipe !== sha(recipe)) throw STOP;
    return {
      recipe, context: Object.freeze(context), maxBytes: BigInt(spec.maxBytes),
      recheck: method(spec.outputRoots, 'recheck'), cancelRoots: method(spec.outputRoots, 'cancel'),
      copyNext: method(spec.preembedCopy, 'copyNext'), cancelCopy: method(spec.preembedCopy, 'cancel')
    };
  } catch {
    throw Error(PREFIX + 'Input');
  }
}

export function createWorkerArtifactManifestPortV1(options) {
  const { recipe, context, maxBytes, recheck, cancelRoots, copyNext, cancelCopy } = setup(options);
  const leaves = recipe.candidates.map(candidate => Object.fromEntries(OUTPUTS.map(key =>
    [key, candidate[key].slice(candidate.outputRoot.length + 1)])));
  let active = null, pending = null, stop = null, completed = 0, copyCode = null, uncertain = false;
  let sharedSignal = null;

  function snapshot() {
    return Object.freeze({
      version: 1, kind: 'worker_artifact_manifest_port_snapshot_v1', pending,
      next: stop === null && completed < 2 ? 2 + completed * 3 : null,
      completed, stop, copyCode, uncertain
    });
  }
  async function drain() {
    const offered = active;
    if (offered) {
      try { await offered; } catch { /* The snapshot retains the stop and uncertainty. */ }
    }
    return snapshot();
  }
  function latch(code) {
    if (code === 'UNCERTAIN') uncertain = true;
    stop ??= code;
  }
  function requireThat(condition, code) {
    if (!condition) {
      latch(code);
      throw STOP;
    }
  }

  function readRoster(value) {
    const view = leaseSnapshot(value);
    for (const root of view.roots) {
      requireThat(root.markerClosure !== 'unknown' && root.directoryClosure !== 'unknown', 'UNCERTAIN');
    }
    requireThat(view.ready, 'ROSTER');

    const identities = new Set();
    function unique(id) {
      requireThat(!identities.has(id), 'ROSTER');
      identities.add(id);
    }
    for (const root of view.roots) unique(root.identity);

    const roots = view.roots.map((root, index) => {
      const names = [MARKER, ...Object.values(leaves[index])];
      const files = new Map();
      for (const row of root.files) {
        requireThat(names.includes(row.name) && !files.has(row.name), 'ROSTER');
        unique(row.identity);
        files.set(row.name, row);
      }
      requireThat((files.get(MARKER)?.bytes ?? 0n) > 0n, 'ROSTER');
      return { identity: root.identity, files };
    });
    return { roots, total: view.total };
  }

  function checkCopy(value, request) {
    const proof = copySnapshot(value);
    const { io } = proof;
    requireThat(proof.candidate === request.candidate || (!proof.ok && proof.candidate === null), 'UNCERTAIN');
    if (proof.ok) {
      const readBytes = 4 * request.linked.executable.bytes + 2 * request.linked.manifest.bytes;
      const writeBytes = request.linked.executable.bytes;
      requireThat(proof.code === null && equal(fact(proof.executable), request.linked.executable) &&
        equal(fact(proof.manifest, 65536), request.linked.manifest) &&
        equal(fact(proof.copy), request.linked.executable) && io.reservedCopies === 1 &&
        io.reservedReadBytes === readBytes && io.actualReadBytes === readBytes &&
        io.reservedWriteBytes === writeBytes && io.actualWriteBytes === writeBytes &&
        io.openAttempts === 3 && io.opened === 3 && io.closeAttempts === 3 && io.closed === 3 &&
        io.verifiedScans === 6, 'UNCERTAIN');
    } else {
      requireThat(COPY_FAILURES.includes(proof.code) && proof.executable === null &&
        proof.manifest === null && proof.copy === null, 'UNCERTAIN');
      copyCode = proof.code;
    }
    requireThat(!proof.unknownClosure && !proof.ioUncertain, 'UNCERTAIN');
    requireThat(proof.ok, 'COPY');
  }

  async function prepare(index, linked, signal) {
    let follower = null, stoppedHelpers = false;
    function abort() {
      latch('CANCELLED');
      if (stoppedHelpers) return;
      stoppedHelpers = true;
      for (const cancel of [cancelRoots, cancelCopy]) {
        try { cancel(); } catch { latch('UNCERTAIN'); }
      }
    }
    function live() {
      if (signalAborted.call(follower)) abort();
      if (stop !== null) throw STOP;
    }
    async function observe(read, inspect) {
      live();
      let value;
      try {
        value = await read();
      } catch {
        requireThat(false, 'UNCERTAIN');
      }
      // Inspect cleanup evidence before discarding a reply that arrived after abort.
      let result;
      try {
        result = inspect(value);
      } catch (error) {
        if (error !== STOP) latch('UNCERTAIN');
        throw STOP;
      }
      live();
      return result;
    }

    try {
      follower = followSignals([signal]);
      addListener.call(follower, 'abort', abort, { once: true });
      live();
      const before = await observe(recheck, readRoster);
      const names = leaves[index];
      const root = before.roots[index];
      const other = before.roots[1 - index].files;
      const object = root.files.get(names.object);
      const exe = root.files.get(names.executable);
      const manifest = root.files.get(names.manifest);
      requireThat(object?.bytes > 0n && exe?.bytes === BigInt(linked.executable.bytes) &&
        manifest?.bytes === BigInt(linked.manifest.bytes) && !root.files.has(names.preEmbedCopy) &&
        (index === 0 ? other.size === 1 : other.has(leaves[0].preEmbedCopy)), 'ROSTER');
      const projected = before.total + BigInt(linked.executable.bytes);
      requireThat(projected <= maxBytes, 'BUDGET');

      pending = 'copy';
      const request = Object.freeze({
        candidate: recipe.candidates[index].id, rootIdentity: root.identity,
        executableIdentity: exe.identity, manifestIdentity: manifest.identity, linked
      });
      await observe(() => copyNext(request), proof => checkCopy(proof, request));

      pending = 'after';
      const after = await observe(recheck, readRoster);
      for (const [i, old] of before.roots.entries()) {
        const next = after.roots[i];
        requireThat(next.identity === old.identity && next.files.size === old.files.size + Number(i === index), 'ROSTER');
        for (const [name, file] of old.files) {
          const row = next.files.get(name);
          requireThat(row?.identity === file.identity && row.bytes === file.bytes, 'ROSTER');
        }
      }
      requireThat(after.roots[index].files.get(names.preEmbedCopy)?.bytes === BigInt(linked.executable.bytes) &&
        after.total === projected, 'ROSTER');
      live();
      const receipt = JSON.stringify({
        version: 1, kind: 'worker_artifact_manifest_v1', ...context, index: 2 + 3 * index,
        ordinary: true, exclusive: true, equal: true, withinBudget: true,
        manifest: linked.manifest, preEmbed: linked.executable, copy: linked.executable
      });
      completed++;
      return receipt;
    } catch {
      if (stop === null) latch('UNCERTAIN');
      throw Error(PREFIX + 'Stopped');
    } finally {
      if (follower !== null) removeListener.call(follower, 'abort', abort);
      pending = null;
      active = null;
    }
  }

  async function prepareManifest(request, signal) {
    if (active) throw Error(PREFIX + 'Busy');
    if (stop !== null) throw Error(PREFIX + 'Stopped');
    const index = completed;
    let linked;
    try {
      signalAborted.call(signal); // Check the genuine AbortSignal brand without reading a caller getter.
      const r = record(request, ['version', 'context', 'index', 'step', 'linked']);
      const expected = recipe.steps[2 + 3 * index];
      const actualContext = record(r.context, CONTEXT);
      if (!expected || r.version !== 1 || r.index !== expected.index ||
          !CONTEXT.every(key => actualContext[key] === context[key]) || !matchesStep(r.step, expected) ||
          (sharedSignal !== null && sharedSignal !== signal)) throw STOP;
      const facts = record(r.linked, ['executable', 'manifest']);
      linked = Object.freeze({ executable: fact(facts.executable), manifest: fact(facts.manifest, 65536) });
    } catch {
      latch('REQUEST');
      throw Error(PREFIX + 'Stopped');
    }
    sharedSignal = signal;
    pending = 'before';
    active = Promise.resolve().then(() => prepare(index, linked, signal));
    return active;
  }

  return Object.freeze({ prepareManifest, snapshot, drain });
}
