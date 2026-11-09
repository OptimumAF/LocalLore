// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactManifestPortV1';
const CONTEXT = ['attempt', 'recipe', 'baseline', 'closure'];
const OUTPUTS = ['object', 'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'];
const COPY_FAILURES = ['INPUT', 'CLOCK', 'DEADLINE', 'CANCELLED', 'IO', 'IDENTITY', 'CONTENT', 'CLOSE'];
const MARKER = '.locallore-output-owner-v1';
const MAX = 67108864;
const U64 = (1n << 64n) - 1n;
const STOP = Symbol('manifest port stopped');
const BAD_DATA = Symbol('malformed manifest data');
const signalAborted = Object.getOwnPropertyDescriptor(AbortSignal.prototype, 'aborted').get;
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

function decimal(text) {
  if (typeof text !== 'string' || text.length < 1 || text.length > 20 || /[^0-9]/.test(text)) return null;
  const value = BigInt(text);
  return value <= U64 && value.toString() === text ? value : null;
}

function identity(text) {
  if (typeof text !== 'string' || text.length > 41) return false;
  const parts = text.split(':');
  if (parts.length !== 2) return false;
  const [device, file] = parts.map(decimal);
  return device !== null && file !== null && file > 0n;
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
    requireThat(value?.version === 1 && value.kind === 'worker_artifact_output_roots_v1' &&
      value.qualified === false && value.pending === null && Array.isArray(value.roots) &&
      value.roots.length === 2, 'UNCERTAIN');
    for (const root of value.roots) {
      requireThat(root && ['none', 'open', 'closed', 'unknown'].includes(root.markerClosure) &&
        ['none', 'open', 'closed', 'unknown'].includes(root.directoryClosure), 'UNCERTAIN');
      requireThat(root.markerClosure !== 'unknown' && root.directoryClosure !== 'unknown', 'UNCERTAIN');
    }
    requireThat(value.state === 'Ready' && value.stop === null && value.withinBudget === true, 'ROSTER');

    const identities = new Set();
    function unique(id) {
      requireThat(identity(id) && !identities.has(id), 'ROSTER');
      identities.add(id);
    }
    for (const root of value.roots) unique(root.identity);

    let total = 0n;
    const roots = value.roots.map((root, index) => {
      const names = [MARKER, ...Object.values(leaves[index])];
      requireThat(root.candidate === recipe.candidates[index].id && root.creation === 'created' &&
        root.marker === 'created' && root.complete === true && root.markerClosure === 'open' &&
        root.directoryClosure === 'closed' && Array.isArray(root.files) && root.files.length <= names.length, 'ROSTER');
      const files = new Map();
      for (const row of root.files) {
        requireThat(row && names.includes(row.name) && !files.has(row.name), 'ROSTER');
        const bytes = decimal(row.bytes);
        requireThat(bytes !== null, 'ROSTER');
        unique(row.identity);
        total += bytes;
        files.set(row.name, { identity: row.identity, bytes });
      }
      requireThat((files.get(MARKER)?.bytes ?? 0n) > 0n, 'ROSTER');
      return { identity: root.identity, files };
    });
    requireThat(total.toString() === value.observedBytes, 'ROSTER');
    return { roots, total };
  }

  function checkCopy(proof, request) {
    requireThat(proof?.version === 1 && proof.kind === 'worker_artifact_preembed_copy_v1' &&
      proof.qualified === false && typeof proof.ok === 'boolean' &&
      typeof proof.unknownClosure === 'boolean' && typeof proof.ioUncertain === 'boolean' &&
      (proof.candidate === request.candidate || (!proof.ok && proof.candidate === null)), 'UNCERTAIN');
    if (proof.ok) {
      requireThat(proof.code === null && equal(fact(proof.executable), request.linked.executable) &&
        equal(fact(proof.manifest, 65536), request.linked.manifest) &&
        equal(fact(proof.copy), request.linked.executable), 'UNCERTAIN');
    } else {
      requireThat(COPY_FAILURES.includes(proof.code) && proof.executable === null &&
        proof.manifest === null && proof.copy === null, 'UNCERTAIN');
      copyCode = proof.code;
    }
    requireThat(!proof.unknownClosure && !proof.ioUncertain, 'UNCERTAIN');
    requireThat(proof.ok, 'COPY');
  }

  async function prepare(index, linked, signal) {
    let listening = false, stoppedHelpers = false;
    function abort() {
      latch('CANCELLED');
      if (stoppedHelpers) return;
      stoppedHelpers = true;
      for (const cancel of [cancelRoots, cancelCopy]) {
        try { cancel(); } catch { latch('UNCERTAIN'); }
      }
    }
    function live() {
      if (signalAborted.call(signal)) abort();
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
      addListener.call(signal, 'abort', abort, { once: true });
      listening = true;
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
      if (listening) removeListener.call(signal, 'abort', abort);
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
