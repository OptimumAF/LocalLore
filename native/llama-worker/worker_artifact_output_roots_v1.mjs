// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { lstat, mkdir, open, opendir, realpath } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactOutputRootsV1';
const MARKER = '.locallore-output-owner-v1';
const MAX_BYTES = 67108864;
const U64 = (1n << 64n) - 1n;
const OUTPUTS = ['object', 'executable', 'preEmbedCopy', 'manifest', 'compilerPdb', 'linkerPdb', 'importLibrary'];
const ADAPTER_KEYS = ['identify', 'mkdir', 'openMarker', 'openDirectory', 'now'];
const STOP = Symbol('stopped');

function record(value, keys) {
  try {
    if (value === null || typeof value !== 'object' ||
        ![Object.prototype, null].includes(Object.getPrototypeOf(value))) return null;
    const names = Reflect.ownKeys(value);
    if (names.length !== keys.length || names.some(key => !keys.includes(key))) return null;
    const result = Object.create(null);
    for (const key of keys) {
      const d = Object.getOwnPropertyDescriptor(value, key);
      if (!d?.enumerable || !Object.hasOwn(d, 'value')) return null;
      result[key] = d.value;
    }
    return result;
  } catch {
    return null;
  }
}

function isIdentity(value) {
  if (typeof value !== 'string' || value.length > 41 ||
      !/^(0|[1-9][0-9]{0,19}):([1-9][0-9]{0,19})$/.test(value) || /[^0-9:]/.test(value)) return false;
  return value.split(':').every(part => BigInt(part) <= U64);
}

function ownMethod(handle, name) {
  try {
    const d = Object.getOwnPropertyDescriptor(handle, name);
    if (d && Object.hasOwn(d, 'value') && typeof d.value === 'function') {
      const method = d.value;
      return (...args) => Reflect.apply(method, handle, args);
    }
  } catch {
    // An unobservable close cannot be reported as closed.
  }
  return null;
}

function freeze(value) {
  if (value !== null && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}

function construct(value, adapter, installGuard = () => {}) {
  const spec = record(value, ['config', 'attemptSha256', 'parentIdentity', 'maxBytes']);
  const ports = record(adapter, ADAPTER_KEYS);
  if (!spec || !ports || ADAPTER_KEYS.some(name => typeof ports[name] !== 'function') ||
      typeof spec.attemptSha256 !== 'string' || spec.attemptSha256.length !== 64 ||
      /[^0-9a-f]/.test(spec.attemptSha256) || spec.attemptSha256 === '0'.repeat(64) ||
      !isIdentity(spec.parentIdentity) || !Number.isInteger(spec.maxBytes) ||
      spec.maxBytes < 1 || spec.maxBytes > MAX_BYTES) throw Error(PREFIX + 'Input');
  let recipe;
  try {
    recipe = planWorkerArtifactComparisonV1(spec.config);
  } catch {
    throw Error(PREFIX + 'Input');
  }
  const { identify, mkdir: makeRoot, openMarker, openDirectory, now } = ports;
  const recipeHash = createHash('sha256').update(JSON.stringify(recipe)).digest('hex');
  const [device] = spec.parentIdentity.split(':');
  const maxBytes = BigInt(spec.maxBytes);
  const parentPath = recipe.candidates[0].outputRoot.slice(0, recipe.candidates[0].outputRoot.lastIndexOf('/'));
  const roots = recipe.candidates.map(item => {
    const path = item.outputRoot;
    return {
      candidate: item.id, path, markerPath: path + '/' + MARKER,
      expected: Buffer.from(['locallore-worker-artifact-owner-v1', spec.attemptSha256, recipeHash, item.id, ''].join('\n'), 'ascii'),
      names: [MARKER, ...OUTPUTS.map(key => item[key].slice(path.length + 1))],
      creation: 'unattempted', identity: null, marker: 'unattempted', markerIdentity: null,
      markerClosure: 'none', directoryClosure: 'none', handle: null, complete: false, files: new Map()
    };
  });

  let state = 'New', pending = null, stop = null, rechecks = 0, observed = 0n;
  let started = null, lastClock = null;
  function snapshot(...args) {
    if (args.length) throw Error(PREFIX + 'State');
    return freeze({
      version: 1, kind: 'worker_artifact_output_roots_v1', qualified: false,
      state, pending, stop, rechecks, withinBudget: state === 'Ready' && pending === null &&
        roots.every(root => root.complete),
      observedBytes: observed.toString(),
      roots: roots.map(root => ({
        candidate: root.candidate, creation: root.creation, identity: root.identity, marker: root.marker,
        markerClosure: root.markerClosure, directoryClosure: root.directoryClosure, complete: root.complete,
        files: root.names.filter(name => root.files.has(name)).map(name => ({ ...root.files.get(name) }))
      }))
    });
  }

  function latch(code) {
    if (stop === null) stop = code;
    state = 'Stopped';
  }
  function requireFact(ok, code) {
    if (!ok) {
      latch(code);
      throw STOP;
    }
  }
  function guard() {
    if (stop !== null) throw STOP;
    let tick;
    try { tick = now(); } catch { requireFact(false, 'Clock'); }
    if (stop !== null) throw STOP;
    requireFact(Number.isFinite(tick) && tick >= 0 && (lastClock === null || tick >= lastClock), 'Clock');
    lastClock = tick;
    started ??= tick;
    requireFact(tick - started < 4000, 'Deadline');
  }
  installGuard(guard);
  async function call(fn, ...args) {
    guard();
    const reply = await fn(...args);
    guard();
    return reply;
  }

  const validId = value => isIdentity(value) && value.startsWith(device + ':');
  function parseFact(value, named) {
    const fact = record(value, named ? ['identity', 'bytes', 'ordinary', 'real'] : ['identity', 'bytes', 'ordinary']);
    requireFact(fact && validId(fact.identity) && typeof fact.bytes === 'bigint' &&
      fact.bytes >= 0n && fact.bytes <= U64 && fact.ordinary === true && (!named || fact.real === true), 'Identity');
    return fact;
  }
  const namedFact = async (path, kind) => parseFact(await call(identify, path, kind), true);

  async function checkParent() {
    requireFact((await namedFact(parentPath, 'directory')).identity === spec.parentIdentity, 'Identity');
  }
  async function checkRoot(root) {
    await checkParent();
    requireFact((await namedFact(root.path, 'directory')).identity === root.identity, 'Identity');
  }
  function boundIds() {
    return new Set([spec.parentIdentity, ...roots.flatMap(root => [root.identity, root.markerIdentity])]);
  }

  async function markerFact(root, length) {
    await checkRoot(root);
    const held = parseFact(await call(root.handle.identity), false);
    const named = await namedFact(root.markerPath, 'file');
    requireFact(held.identity === named.identity &&
      (root.markerIdentity === null ? !boundIds().has(held.identity) : root.markerIdentity === held.identity), 'Identity');
    requireFact(held.bytes === BigInt(length) && named.bytes === held.bytes, 'Marker');
    return held.identity;
  }

  async function verifyMarker(root) {
    const length = root.expected.length;
    await markerFact(root, length);
    const received = Buffer.alloc(length + 1);
    for (let offset = 0; offset < length;) {
      const n = await call(root.handle.read, received, offset, length - offset, offset);
      requireFact(Number.isInteger(n) && n > 0 && n <= length - offset, 'Marker');
      offset += n;
    }
    const eof = await call(root.handle.read, received, length, 1, length);
    requireFact(eof === 0 && received.subarray(0, length).equals(root.expected), 'Marker');
    await markerFact(root, length);
  }

  async function createRoot(root) {
    await checkParent();
    guard();
    root.creation = 'unknown';
    const result = await makeRoot(root.path);
    if (result === 'created' || result === 'exists') root.creation = result;
    if (result === 'exists') latch('Exists');
    guard();
    requireFact(result === 'created', 'IO');
    await checkParent();
    const fact = await namedFact(root.path, 'directory');
    requireFact(!boundIds().has(fact.identity), 'Identity');
    root.identity = fact.identity;

    await checkRoot(root);
    guard();
    root.marker = 'unknown';
    root.markerClosure = 'unknown';
    const acquired = await openMarker(root.markerPath);
    root.marker = 'created';
    const close = ownMethod(acquired, 'close');
    root.markerClosure = close ? 'open' : 'unknown';
    root.handle = { close };
    guard();
    requireFact(close, 'Closure');
    for (const key of ['identity', 'read', 'write', 'sync']) {
      root.handle[key] = ownMethod(acquired, key);
      requireFact(root.handle[key], 'IO');
    }

    root.markerIdentity = await markerFact(root, 0);
    const length = root.expected.length;
    for (let offset = 0; offset < length;) {
      const n = await call(root.handle.write, Buffer.from(root.expected), offset, length - offset, offset);
      requireFact(Number.isInteger(n) && n > 0 && n <= length - offset, 'Marker');
      offset += n;
    }
    requireFact(await call(root.handle.sync) === undefined, 'Marker');
    await verifyMarker(root);
  }

  function observeCleanupClock() {
    try { guard(); } catch { /* Closing owned handles must not be skipped. */ }
  }
  async function finishClose(fn) {
    try {
      if (await fn() === undefined) return 'closed';
    } catch { /* Opaque, possibly unsettled closure. */ }
    latch('Closure');
    return 'unknown';
  }

  async function scan(root, initial, seen) {
    await verifyMarker(root);
    let close = null;
    try {
      guard();
      root.directoryClosure = 'unknown';
      const stream = await openDirectory(root.path);
      close = ownMethod(stream, 'close');
      root.directoryClosure = close ? 'open' : 'unknown';
      guard();
      requireFact(close, 'Closure');
      const read = ownMethod(stream, 'read');
      requireFact(read, 'IO');
      let eof = false;
      for (let i = 0; i <= root.names.length; i++) {
        const reply = await call(read);
        if (reply === null) {
          eof = true;
          break;
        }
        const entry = record(reply, ['name', 'ordinary']);
        requireFact(entry && entry.ordinary === true && root.names.includes(entry.name) &&
          !root.files.has(entry.name) && (!initial || entry.name === MARKER), 'Roster');
        await checkRoot(root);
        const fact = await namedFact(root.path + '/' + entry.name, 'file');
        if (entry.name === MARKER) {
          requireFact(fact.identity === root.markerIdentity, 'Identity');
          requireFact(fact.bytes === BigInt(root.expected.length), 'Marker');
        } else {
          requireFact(!seen.has(fact.identity), 'Identity');
          seen.add(fact.identity);
        }
        root.files.set(entry.name, { name: entry.name, identity: fact.identity, bytes: fact.bytes.toString() });
        observed += fact.bytes;
        requireFact(observed <= maxBytes, 'Budget');
      }
      requireFact(eof && root.files.has(MARKER), 'Roster');
    } catch {
      latch('IO');
    } finally {
      if (close) {
        observeCleanupClock();
        root.directoryClosure = await finishClose(close);
        observeCleanupClock();
      }
    }
    guard();
    await verifyMarker(root);
    guard();
    root.complete = true;
  }

  function checkOffer(args) {
    if (args.length) throw Error(PREFIX + 'State');
    if (pending !== null) throw Error(PREFIX + 'Busy');
  }

  async function observe(initial) {
    pending = initial ? 'prepare' : 'recheck';
    started = null;
    observed = 0n;
    for (const root of roots) {
      root.directoryClosure = 'none';
      root.complete = false;
      root.files.clear();
    }
    try {
      if (initial) {
        requireFact(BigInt(roots.reduce((sum, root) => sum + root.expected.length, 0)) <= maxBytes, 'Budget');
        for (const root of roots) await createRoot(root);
      }
      const seen = boundIds();
      for (const root of roots) await scan(root, initial, seen);
      guard();
      state = 'Ready';
    } catch {
      latch('IO');
    } finally {
      pending = null;
    }
    return snapshot();
  }

  return Object.freeze({
    async prepare(...args) {
      checkOffer(args);
      if (state !== 'New') throw Error(PREFIX + 'State');
      return observe(true);
    },
    async recheck(...args) {
      checkOffer(args);
      if (state !== 'Ready') throw Error(PREFIX + 'State');
      if (rechecks === 32) {
        latch('Limit');
        return snapshot();
      }
      rechecks++;
      return observe(false);
    },
    cancel(...args) {
      if (args.length) throw Error(PREFIX + 'State');
      if (state !== 'Closed') latch('Cancelled');
      return snapshot();
    },
    async close(...args) {
      checkOffer(args);
      if (state === 'Closed') return snapshot();
      pending = 'close';
      for (const root of [...roots].reverse()) {
        const fn = root.handle?.close;
        if (fn) {
          root.handle = null;
          root.markerClosure = await finishClose(fn);
        }
      }
      pending = null;
      state = 'Closed';
      return snapshot();
    },
    snapshot
  });
}

const normalize = path => path.replaceAll('\\', '/').replace(/[A-Z]/g, c => c.toLowerCase());
const ordinaryFile = stat => stat.isFile() && !stat.isSymbolicLink() && stat.nlink === 1n;
function statFact(stat, ordinary) {
  const identity = typeof stat.dev === 'bigint' && typeof stat.ino === 'bigint'
    ? stat.dev.toString() + ':' + stat.ino.toString() : '';
  return { identity, bytes: stat.size, ordinary };
}

function windowsAdapter(guard) {
  return {
    now: () => performance.now(),
    async identify(path, kind) {
      guard();
      const s = await lstat(path, { bigint: true });
      guard();
      const fact = statFact(s, kind === 'directory' ? s.isDirectory() && !s.isSymbolicLink() : ordinaryFile(s));
      if (!fact.ordinary || !isIdentity(fact.identity)) return { ...fact, real: false };
      const physical = await realpath(path);
      return { ...fact, real: normalize(physical) === normalize(path) };
    },
    async mkdir(path) {
      guard();
      try {
        await mkdir(path, { recursive: false });
        return 'created';
      } catch (error) {
        // This is a native Node fs rejection, never a test adapter value.
        if (error?.code === 'EEXIST') return 'exists';
        throw error;
      }
    },
    async openMarker(path) {
      guard();
      const handle = await open(path, 'wx+');
      // Return the acquired resource before any post-open liveness check.
      return {
        async identity() {
          const s = await handle.stat({ bigint: true });
          return statFact(s, ordinaryFile(s));
        },
        async read(buffer, offset, length, position) {
          return (await handle.read(buffer, offset, length, position)).bytesRead;
        },
        async write(buffer, offset, length, position) {
          return (await handle.write(buffer, offset, length, position)).bytesWritten;
        },
        sync: () => handle.sync(),
        close: () => handle.close()
      };
    },
    async openDirectory(path) {
      guard();
      const dir = await opendir(path, { recursive: false, bufferSize: 1 });
      return {
        async read() {
          const entry = await dir.read();
          return entry === null ? null : { name: entry.name, ordinary: entry.isFile() && !entry.isSymbolicLink() };
        },
        close: () => dir.close()
      };
    }
  };
}

export function createWorkerArtifactOutputRootsV1(spec) {
  if (process.platform !== 'win32') throw Error(PREFIX + 'Platform');
  let guard;
  return construct(spec, windowsAdapter(() => guard()), value => { guard = value; });
}

export function createWorkerArtifactOutputRootsV1ForTesting(spec, adapter) {
  return construct(spec, adapter);
}
