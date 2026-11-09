// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { lstat, open, realpath } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { inspectLibraryInputs } from './library_inputs.mjs';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactHeldOutputsV1';
const MAX_BYTES = 64 * 1024 * 1024;
const CHUNK = 64 * 1024;
const DEADLINE = 4000;
const U64 = (1n << 64n) - 1n;
const I64 = 1n << 63n;
const ARCHIVE = Buffer.from('!<arch>\n', 'ascii');
const STOP = Symbol('held output stopped');
const DATA = Symbol('malformed held output data');
const REQUEST = ['index', 'candidate', 'role', 'rootIdentity', 'fileIdentity', 'bytes'];
const ADAPTER = ['identifyRoot', 'identifyFile', 'openRead', 'now'];
const FILE = ['identity', 'ordinary', 'bytes', 'links', 'modified', 'changed'];
const NAMED_FILE = [...FILE, 'real'];
const STAGE_ROLES = [
  ['object'],
  ['object', 'executable', 'manifest'],
  ['object', 'executable', 'manifest', 'preEmbedCopy']
];
const aborted = Object.getOwnPropertyDescriptor(AbortSignal.prototype, 'aborted').get;
const followSignal = AbortSignal.any;
const listen = EventTarget.prototype.addEventListener;
const unlisten = EventTarget.prototype.removeEventListener;

function data(value, names) {
  if (value === null || typeof value !== 'object' ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(value))) throw DATA;
  const keys = Reflect.ownKeys(value);
  if (keys.length !== names.length || keys.some(key => !names.includes(key))) throw DATA;
  const copy = Object.create(null);
  for (const name of names) {
    const d = Object.getOwnPropertyDescriptor(value, name);
    if (!d?.enumerable || !Object.hasOwn(d, 'value')) throw DATA;
    copy[name] = d.value;
  }
  return copy;
}

function ownMethod(handle, name) {
  try {
    const d = Object.getOwnPropertyDescriptor(handle, name);
    if (!d || !Object.hasOwn(d, 'value') || typeof d.value !== 'function') return null;
    const method = d.value;
    return (...args) => Reflect.apply(method, handle, args);
  } catch {
    return null;
  }
}

function decimal(value, signed = false) {
  if (typeof value !== 'string' || value.length === 0 || value.length > 20 ||
      !/^-?[0-9]+$/.test(value) || /[^0-9-]/.test(value)) return null;
  const n = BigInt(value);
  if (n.toString() !== value || n < (signed ? -I64 : 0n) || n > (signed ? I64 - 1n : U64)) return null;
  return n;
}

function identity(value) {
  if (typeof value !== 'string' || value.length > 41) return null;
  const parts = value.split(':');
  if (parts.length !== 2) return null;
  const [device, inode] = parts.map(part => decimal(part));
  return device !== null && inode !== null && inode > 0n ? device : null;
}

function plan(recipe) {
  const candidates = new Map(recipe.candidates.map(candidate => [candidate.id, candidate]));
  function row(index, candidate, role) {
    const item = candidates.get(candidate);
    return { index, candidate, role, root: item.outputRoot, file: item[role] };
  }
  const rows = recipe.steps.flatMap(step => STAGE_ROLES[step.index % 3].map(role =>
    row(step.index, step.candidate, role)));
  for (const candidate of recipe.candidates) {
    for (const role of ['object', 'executable']) rows.push(row(6, candidate.id, role));
  }
  return rows;
}

function requestOf(value, row) {
  const request = data(value, REQUEST);
  const rootDevice = identity(request.rootIdentity);
  const fileDevice = identity(request.fileIdentity);
  const max = row.role === 'manifest' ? CHUNK : MAX_BYTES;
  if (request.index !== row.index || request.candidate !== row.candidate || request.role !== row.role ||
      rootDevice === null || fileDevice !== rootDevice || request.rootIdentity === request.fileIdentity ||
      !Number.isSafeInteger(request.bytes) || request.bytes < 1 || request.bytes > max) throw DATA;
  return request;
}

function parseObject(bytes) {
  if (bytes.subarray(0, ARCHIVE.length).equals(ARCHIVE)) throw DATA;
  const result = inspectLibraryInputs(bytes);
  if (result.objects !== 1 || result.imports !== 0 ||
      result.directives.length + result.defaultLibraries.length > 64) throw DATA;
  const metadata = {
    directives: Object.freeze([...result.directives]),
    defaultLibraries: Object.freeze([...result.defaultLibraries])
  };
  if (Buffer.byteLength(JSON.stringify(metadata), 'utf8') > 8192) throw DATA;
  return Object.freeze(metadata);
}

const counters = () => ({ reservedReadBytes: 0n, actualReadBytes: 0n, opened: 0, closed: 0, verifiedScans: 0 });
function ioView(io) {
  return Object.freeze({ ...io, reservedReadBytes: io.reservedReadBytes.toString(),
    actualReadBytes: io.actualReadBytes.toString() });
}

function createReader(options, adapter, installGuard = () => {}) {
  let rows, callbacks;
  try {
    const { config } = data(options, ['config']);
    callbacks = data(adapter, ADAPTER);
    if (!ADAPTER.every(name => typeof callbacks[name] === 'function')) throw DATA;
    rows = plan(planWorkerArtifactComparisonV1(config));
  } catch {
    throw Error(PREFIX + 'Input');
  }
  const { identifyRoot, identifyFile, openRead, now } = callbacks;
  let cursor = 0, pending = null, stop = null, lastNow = null;
  let sourceSignal = null, follower = null;
  let anyUnknownClosure = false, anyIoUncertain = false;
  const total = counters();

  function cancel() {
    if (cursor < rows.length) stop ??= 'CANCELLED';
  }
  function observeAbort() {
    if (follower !== null && aborted.call(follower)) cancel();
  }
  function snapshot() {
    observeAbort();
    return Object.freeze({
      version: 1, kind: 'worker_artifact_held_outputs_snapshot_v1',
      next: stop === null && cursor < rows.length ? cursor : null, pending, completed: cursor,
      stop, io: ioView(total), unknownClosure: anyUnknownClosure, ioUncertain: anyIoUncertain
    });
  }

  async function readNext(...args) {
    if (pending !== null) throw Error(PREFIX + 'Busy');
    observeAbort();
    if (stop !== null || cursor === rows.length) throw Error(PREFIX + 'Stopped');

    const row = rows[cursor], io = counters();
    let request = null, close = null, watching = false, began = null;
    let unknownClosure = false, ioUncertain = false;
    let file = null, metadata = null;
    pending = cursor;

    function add(key, amount = 1) {
      io[key] += amount;
      total[key] += amount;
    }
    function fail(code) {
      stop ??= code;
      throw STOP;
    }
    function live() {
      observeAbort();
      if (stop !== null) throw STOP;
      let tick;
      try { tick = now(); } catch { fail('CLOCK'); }
      if (stop !== null) throw STOP;
      if (!Number.isFinite(tick) || tick < 0 || (lastNow !== null && tick < lastNow)) fail('CLOCK');
      lastNow = tick;
      began ??= tick;
      if (tick - began >= DEADLINE) fail('DEADLINE');
    }
    function cleanupObservation() {
      try { live(); } catch { /* Preserve the latched cause and still close. */ }
    }
    function markUnknownClosure() {
      unknownClosure = true;
      anyUnknownClosure = true;
    }
    function markUncertainIo() {
      ioUncertain = true;
      anyIoUncertain = true;
    }

    async function offer(fn, ...values) {
      live();
      const result = await fn(...values);
      live();
      return result;
    }
    function rootFact(value) {
      try {
        const root = data(value, ['identity', 'ordinary', 'real']);
        if (root.identity !== request.rootIdentity || root.ordinary !== true || root.real !== true) throw DATA;
      } catch {
        fail('IDENTITY');
      }
    }
    function fileFact(value, named) {
      try {
        const result = data(value, named ? NAMED_FILE : FILE);
        if (result.identity !== request.fileIdentity || result.ordinary !== true || result.links !== 1 ||
            result.bytes !== request.bytes || decimal(result.modified, true) === null ||
            decimal(result.changed, true) === null || (named && result.real !== true)) throw DATA;
        return result;
      } catch {
        fail('IDENTITY');
      }
    }
    function sameFingerprint(value, original) {
      if (!FILE.every(key => value[key] === original[key])) fail('IDENTITY');
    }

    async function readBytes(read, buffer, length, position, eof) {
      live();
      let count;
      try {
        count = await read(buffer, 0, length, position);
      } catch (error) {
        if (error === STOP) throw STOP;
        markUncertainIo();
        fail('IO');
      }
      const known = Number.isSafeInteger(count) && count >= 0;
      if (known && count > 0) add('actualReadBytes', BigInt(count));
      const bounded = known && count <= length;
      if (!bounded) markUncertainIo();
      live();
      if (!bounded) fail('IO');
      if (eof ? count !== 0 : count === 0) fail('CONTENT');
      return count;
    }

    async function scan(stat, read, original, scratch, object) {
      sameFingerprint(fileFact(await offer(stat), false), original);
      const hash = createHash('sha256');
      for (let position = 0; position < request.bytes;) {
        const length = Math.min(scratch.length, request.bytes - position);
        const count = await readBytes(read, scratch, length, position, false);
        hash.update(scratch.subarray(0, count));
        if (object !== null) scratch.copy(object, position, 0, count);
        position += count;
      }
      await readBytes(read, scratch, 1, request.bytes, true);
      sameFingerprint(fileFact(await offer(stat), false), original);
      add('verifiedScans');
      return hash.digest('hex');
    }

    try {
      try {
        if (args.length !== 2 || (sourceSignal !== null && args[1] !== sourceSignal)) throw DATA;
        aborted.call(args[1]);
        const captured = requestOf(args[0], row);
        if (sourceSignal === null) {
          follower = followSignal([args[1]]);
          sourceSignal = args[1];
        }
        request = captured;
      } catch {
        fail('REQUEST');
      }
      listen.call(follower, 'abort', cancel, { once: true });
      watching = true;
      installGuard(live);
      live();
      add('reservedReadBytes', BigInt(request.bytes) * 2n + 2n);

      rootFact(await offer(identifyRoot, row.root));
      const original = fileFact(await offer(identifyFile, row.file), true);
      live();
      let handle;
      try {
        handle = await openRead(row.file);
      } catch (error) {
        if (error === STOP) throw STOP;
        markUnknownClosure();
        fail('IO');
      }
      close = ownMethod(handle, 'close');
      if (close === null) markUnknownClosure();
      else add('opened');
      live();
      const stat = ownMethod(handle, 'stat'), read = ownMethod(handle, 'read');
      if (close === null || stat === null || read === null) fail('IO');

      const scratch = Buffer.alloc(Math.min(CHUNK, request.bytes));
      const compile = row.index === 0 || row.index === 3;
      const object = compile ? Buffer.alloc(request.bytes) : null;
      const first = await scan(stat, read, original, scratch, object);
      const second = await scan(stat, read, original, scratch, null);
      if (first !== second) fail('CONTENT');
      rootFact(await offer(identifyRoot, row.root));
      sameFingerprint(fileFact(await offer(identifyFile, row.file), true), original);

      if (compile) {
        live();
        try { metadata = parseObject(object); } catch { fail('COFF'); }
        live();
      }
      file = Object.freeze({ sha256: first, bytes: request.bytes });
    } catch {
      stop ??= 'IO';
    } finally {
      if (close !== null) {
        cleanupObservation();
        try {
          if (await close() !== undefined) throw DATA;
          add('closed');
        } catch {
          markUnknownClosure();
          stop ??= 'CLOSE';
        }
        cleanupObservation();
      }
      installGuard(null);
      if (watching) unlisten.call(follower, 'abort', cancel);
      pending = null;
    }

    const ok = stop === null;
    if (ok) cursor++;
    return Object.freeze({
      version: 1, kind: 'worker_artifact_held_output_v1',
      index: request?.index ?? null, candidate: request?.candidate ?? null, role: request?.role ?? null,
      ok, code: stop, file: ok ? file : null, metadata: ok ? metadata : null, io: ioView(io),
      unknownClosure, ioUncertain
    });
  }
  return Object.freeze({ readNext, snapshot });
}

const normalize = path => path.replaceAll('\\', '/').replace(/[A-Z]/g, char => char.toLowerCase());
const physicalIdentity = stat => stat.dev.toString() + ':' + stat.ino.toString();

function nativeFile(stat) {
  return {
    identity: physicalIdentity(stat), ordinary: stat.isFile() && !stat.isSymbolicLink(),
    bytes: Number(stat.size), links: Number(stat.nlink),
    modified: stat.mtimeNs.toString(), changed: stat.ctimeNs.toString()
  };
}

function windowsAdapter(guard) {
  return {
    now: () => performance.now(),
    async identifyRoot(path) {
      guard();
      const stat = await lstat(path, { bigint: true });
      guard();
      const ordinary = stat.isDirectory() && !stat.isSymbolicLink();
      const real = ordinary && normalize(await realpath(path)) === normalize(path);
      return { identity: physicalIdentity(stat), ordinary, real };
    },
    async identifyFile(path) {
      guard();
      const stat = await lstat(path, { bigint: true });
      guard();
      const fact = nativeFile(stat);
      const real = fact.ordinary && fact.links === 1 && normalize(await realpath(path)) === normalize(path);
      return { ...fact, real };
    },
    async openRead(path) {
      guard();
      const handle = await open(path, 'r');
      // The core captures the close method before checking the late result.
      return {
        async stat() { return nativeFile(await handle.stat({ bigint: true })); },
        async read(buffer, offset, length, position) {
          return (await handle.read(buffer, offset, length, position)).bytesRead;
        },
        close: () => handle.close()
      };
    }
  };
}

export function createWorkerArtifactHeldOutputsV1(spec) {
  if (process.platform !== 'win32') throw Error(PREFIX + 'Platform');
  let activeGuard = null;
  const guard = () => {
    if (activeGuard === null) throw STOP;
    activeGuard();
  };
  return createReader(spec, windowsAdapter(guard), value => { activeGuard = value; });
}

export function createWorkerArtifactHeldOutputsV1ForTesting(spec, adapter) {
  return createReader(spec, adapter);
}
