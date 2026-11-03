// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only cohort32 file port. Runtime-v2, parsers and native admission stay separate.
// FIRST ec5f4ae6 (24 mock + two separately admitted Windows-file groups) froze BEFORE producer.
import { lstat, realpath, open } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';

const INVALID = 'WorkerArtifactWindowsInputsV1Invalid', LIMIT = 'WorkerArtifactWindowsInputsV1Limit';
const PIN = ['slot', 'kind', 'path', 'root', 'bytes', 'sha256', 'rootIdentity', 'leafIdentity'];
const IO = ['reservedInputs', 'reservedBytes', 'reservedReadBytes', 'actualReadBytes',
  'openAttempts', 'opened', 'closeAttempts', 'closed', 'verifiedScans', 'unknownClosures'];
const MAX_INPUT = 268435456, MAX_BYTES = 536870912, MAX_READ = 1073741824, CHUNK = 65536;
const bytes = value => Buffer.byteLength(value, 'utf8');
const sha = value => createHash('sha256').update(value).digest('hex');
const digest = value => sha(JSON.stringify(value));
const integer = value => Number.isSafeInteger(value) && value >= 0;
const hex = value => typeof value === 'string' && value.length === 64 && !/[^a-f0-9]/.test(value);
const token = value => typeof value === 'string' && value.length > 0 && value.length <= 256 && !/[^A-Za-z0-9_.:-]/.test(value);
const fold = value => value.replace(/[A-Z]/g, c => String.fromCharCode(c.charCodeAt(0) + 32));
const norm = value => fold(value.replaceAll('\\', '/'));
const clone = value => JSON.parse(JSON.stringify(value));
const emptyIO = () => Object.fromEntries(IO.map(key => [key, 0]));
class InputFault extends Error {
  constructor(code) { super(code); this.code = code; }
}
const fault = code => { throw new InputFault(code); };
function requireThat(value, code) { if (!value) fault(code); }
function data(value, names, code) {
  try {
    requireThat(value !== null && typeof value === 'object' &&
      [Object.prototype, null].includes(Object.getPrototypeOf(value)), code);
    const keys = Reflect.ownKeys(value);
    requireThat(keys.length === names.length && keys.every(key => typeof key === 'string' && names.includes(key)), code);
    const copy = {};
    for (const name of names) {
      const d = Object.getOwnPropertyDescriptor(value, name);
      requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code);
      copy[name] = d.value;
    }
    return copy;
  } catch { fault(code); }
}
function freeze(value) {
  if (value !== null && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}
function pathValue(value, project) {
  requireThat(typeof value === 'string', INVALID);
  requireThat(bytes(value) <= 1024, LIMIT);
  requireThat(/^[CD]:\//.test(value) && (!project || value.startsWith('D:/')), INVALID);
  const tail = value.slice(3);
  requireThat(!/[^\x20-\x7e]/.test(tail) && !/["\\:*?=,;#<>|&]/.test(tail) &&
    !tail.includes(String.fromCharCode(96)), INVALID);
  for (const part of tail.split('/')) {
    requireThat(bytes(part) <= 255, LIMIT);
    requireThat(part.length > 0 && part !== '.' && part !== '..' && !/[ .]$/.test(part), INVALID);
    const stem = fold(part.split('.')[0].replace(/ +$/, ''));
    requireThat(!/^(con|prn|aux|nul|com[1-9]|lpt[1-9])$/.test(stem), INVALID);
  }
}
function capturePins(spec) {
  const { pins } = data(spec, ['pins'], INVALID);
  requireThat(Array.isArray(pins), INVALID);
  const length = Object.getOwnPropertyDescriptor(pins, 'length')?.value;
  requireThat(integer(length) && length > 0, INVALID);
  requireThat(length <= 32, LIMIT);
  const keys = Reflect.ownKeys(pins);
  requireThat(keys.length === length + 1 && keys.includes('length'), INVALID);
  const captured = [], seen = new Set(); let total = 0;
  for (let i = 0; i < length; i++) {
    const d = Object.getOwnPropertyDescriptor(pins, String(i));
    requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), INVALID);
    const p = data(d.value, PIN, INVALID), project = i < 17;
    requireThat(p.slot === i + 1 && p.kind === (project ? 'project' : 'sdk'), INVALID);
    pathValue(p.path, project); pathValue(p.root, project);
    requireThat(fold(p.path).startsWith(fold(p.root) + '/') && !seen.has(fold(p.path)), INVALID);
    seen.add(fold(p.path));
    requireThat(integer(p.bytes) && p.bytes > 0 && hex(p.sha256) && token(p.rootIdentity) && token(p.leafIdentity), INVALID);
    requireThat(p.bytes < MAX_INPUT, LIMIT);
    total += p.bytes;
    requireThat(total <= MAX_BYTES && 2 * total <= MAX_READ, LIMIT);
    captured.push(freeze(p));
  }
  return Object.freeze(captured);
}
function captureAdapter(adapter) {
  const result = data(adapter, ['identify', 'open', 'now'], INVALID);
  requireThat(Object.values(result).every(value => typeof value === 'function'), INVALID);
  return result;
}
const signature = st => [st.dev, st.ino, st.size, st.mtimeNs, st.ctimeNs].map(String).join(':');

// Concrete Node filesystem path. It is cooperative identity observation, not
// share-mode locking, all-reparse auditing, alias uniqueness or full admit authority.
function nativeAdapter(guard) {
  async function ordinary(path, directory) {
    guard();
    const st = await lstat(path, { bigint: true }); guard();
    requireThat(!st.isSymbolicLink() && (directory ? st.isDirectory() : st.isFile()), 'IdentityFailure');
    const resolved = await realpath(path); guard();
    requireThat(norm(resolved) === norm(path), 'IdentityFailure');
    return st;
  }
  return {
    now: () => performance.now(),
    async identify(pin) {
      const root = await ordinary(pin.root, true), leaf = await ordinary(pin.path, false);
      requireThat(signature(root) === pin.rootIdentity && signature(leaf) === pin.leafIdentity &&
        leaf.size === BigInt(pin.bytes), 'IdentityFailure');
      return { path: pin.path, root: signature(root), leaf: signature(leaf), bytes: pin.bytes };
    },
    async open(pin, mode) {
      guard(); requireThat(mode === 'r', 'InputFailure');
      const handle = await open(pin.path, 'r');
      // Return the owned handle before any post-await guard can reject it.
      return Object.freeze({
        async stat() {
          guard(); const st = await handle.stat({ bigint: true }); guard();
          requireThat(st.isFile() && st.size === BigInt(pin.bytes), 'IdentityFailure');
          return { leaf: signature(st), bytes: Number(st.size) };
        },
        async read(buffer, offset, length, position) {
          guard();
          requireThat(Buffer.isBuffer(buffer) && integer(offset) && integer(length) && length > 0 &&
            length <= CHUNK && integer(position) && offset + length <= buffer.length &&
            position + length <= pin.bytes, 'InputFailure');
          const value = await handle.read(buffer, offset, length, position);
          // Core must charge known returned bytes BEFORE checking a late stop.
          return { bytesRead: value.bytesRead };
        },
        async close() { await handle.close(); } // Never skip cleanup because stopped/expired.
      });
    }
  };
}

function createReader(spec, supplied, production) {
  const pins = capturePins(spec);
  let live;
  const callbacks = production ? captureAdapter(nativeAdapter(() => live())) : captureAdapter(supplied);
  const identify = callbacks.identify, readOpen = callbacks.open, now = callbacks.now;
  let began;
  try { began = now(); } catch { fault(INVALID); }
  requireThat(typeof began === 'number' && Number.isFinite(began) && began >= 0, INVALID);
  let lastTime = began, critical = null, cancelled = false, cursor = 0, pendingIndex = null, lastProof = null;
  const totals = emptyIO();
  const latch = code => { critical ??= code; return critical; };
  const fail = code => fault(latch(code));
  live = () => {
    if (critical !== null) fault(critical);
    let time; try { time = now(); } catch { fail('InputFailure'); }
    if (typeof time !== 'number' || !Number.isFinite(time) || time < 0 || time < lastTime) fail('InputFailure');
    lastTime = time;
    if (time - began > 60000) fail('InputDeadline');
    if (critical !== null) fault(critical);
  };
  function snapshot() {
    return freeze({ version: 1, kind: 'worker_artifact_windows_inputs_snapshot_v1',
      purpose: 'bounded_build_input_read_only',
      status: pendingIndex !== null ? 'pending' : critical !== null ? 'stopped' : cursor === pins.length ? 'complete' : 'ready',
      pinCount: pins.length, nextIndex: cursor, pendingIndex, completedInputs: cursor,
      io: { ...totals }, lastProof: lastProof === null ? null : clone(lastProof), critical, cancelRequested: cancelled,
      qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true });
  }
  function cancel() {
    if (critical !== null || cursor === pins.length) return false;
    cancelled = true; latch('InputCancelled'); return true;
  }
  async function readNext() {
    if (critical !== null) throw Error(critical);
    if (pendingIndex !== null) throw Error(latch('InputSequence'));
    if (cursor === pins.length) throw Error('InputSequence');
    if (arguments.length !== 0) throw Error(latch('InputSequence'));
    const pin = pins[cursor], io = emptyIO(), add = (key, n = 1) => { io[key] += n; totals[key] += n; };
    pendingIndex = cursor;
    add('reservedInputs'); add('reservedBytes', pin.bytes); add('reservedReadBytes', 2 * pin.bytes);
    let close = null, rawHandle = null, buffer = null, before = null;
    const saveFailure = error => latch(error instanceof InputFault ? error.code : 'InputFailure');
    function identity(value) {
      const found = data(value, ['path', 'root', 'leaf', 'bytes'], 'IdentityFailure');
      requireThat(found.path === pin.path && found.root === pin.rootIdentity && found.leaf === pin.leafIdentity &&
        found.bytes === pin.bytes, 'IdentityFailure');
      return found;
    }
    try {
      try {
        live();
        before = identity(await identify(pin)); live();
        add('openAttempts');
        rawHandle = await readOpen(pin, 'r');
        if (rawHandle !== null && (typeof rawHandle === 'object' || typeof rawHandle === 'function')) {
          add('opened');
          // Capture safe cleanup before liveness or any other method validation.
          const d = Object.getOwnPropertyDescriptor(rawHandle, 'close');
          if (d && Object.hasOwn(d, 'value') && typeof d.value === 'function') close = d.value;
        }
        live();
        const held = data(rawHandle, ['stat', 'read', 'close'], 'InputFailure');
        requireThat(Object.values(held).every(value => typeof value === 'function'), 'InputFailure');
        const heldStat = async () => {
          live(); const found = data(await held.stat.call(rawHandle), ['leaf', 'bytes'], 'IdentityFailure'); live();
          requireThat(found.leaf === before.leaf && found.bytes === before.bytes, 'IdentityFailure');
        };
        await heldStat();
        buffer = Buffer.alloc(pin.bytes);
        const scratch = Buffer.alloc(CHUNK);
        for (const output of [buffer, null]) {
          const hash = createHash('sha256'); let at = 0;
          while (at < pin.bytes) {
            live();
            const length = Math.min(CHUNK, pin.bytes - at), target = output ?? scratch, offset = output ? at : 0;
            requireThat(totals.actualReadBytes + length <= totals.reservedReadBytes &&
              totals.actualReadBytes + length <= MAX_READ, 'InputFailure');
            const result = data(await held.read.call(rawHandle, target, offset, length, at), ['bytesRead'], 'InputFailure');
            requireThat(integer(result.bytesRead) && result.bytesRead > 0 && result.bytesRead <= length, 'InputFailure');
            add('actualReadBytes', result.bytesRead);
            live();
            hash.update(target.subarray(offset, offset + result.bytesRead)); at += result.bytesRead;
          }
          requireThat(hash.digest('hex') === pin.sha256, 'IdentityFailure'); add('verifiedScans');
          await heldStat();
          const after = identity(await identify(pin)); live();
          requireThat(JSON.stringify(before) === JSON.stringify(after), 'IdentityFailure');
        }
      } catch (error) { saveFailure(error); }
      finally {
        if (close !== null) {
          add('closeAttempts');
          try { await close.call(rawHandle); add('closed'); } catch { latch('InputFailure'); }
        }
        if (io.openAttempts !== 0 && io.closed !== 1) { add('unknownClosures'); latch('InputFailure'); }
      }
      if (critical !== null) fault(critical);
      live();
      requireThat(sha(buffer) === pin.sha256, 'IdentityFailure');
      const proof = freeze({ version: 1, kind: 'worker_artifact_windows_input_v1', slot: pin.slot, role: pin.kind,
        bytes: pin.bytes, sha256: pin.sha256, pinHash: digest(pin),
        identityHash: digest({ root: before.root, leaf: before.leaf, bytes: before.bytes }), io: { ...io },
        qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true });
      cursor++; lastProof = proof;
      return Object.freeze({ buffer, proof });
    } catch (error) { saveFailure(error); throw Error(critical); }
    finally { pendingIndex = null; }
  }
  return Object.freeze({ readNext, cancel, snapshot });
}

export function createWorkerArtifactWindowsInputsV1(spec) {
  if (arguments.length !== 1 || process.platform !== 'win32') throw Error(INVALID);
  try { return createReader(spec, null, true); } catch (error) {
    throw Error(error instanceof InputFault ? error.code : INVALID);
  }
}
export function createWorkerArtifactWindowsInputsV1ForTesting(spec, adapter) {
  if (arguments.length !== 2) throw Error(INVALID);
  try { return createReader(spec, adapter, false); } catch (error) {
    throw Error(error instanceof InputFault ? error.code : INVALID);
  }
}
