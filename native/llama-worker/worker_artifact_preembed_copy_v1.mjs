// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only exclusive pre-embed preservation. FIRST af49159f preceded producer.
// No admission, coordinator wiring, native launch, adoption or qualification.
import { lstat, realpath, open as fsOpen } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { performance } from 'node:perf_hooks';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const INVALID = 'WorkerArtifactPreembedCopyV1Invalid', BUSY = 'WorkerArtifactPreembedCopyV1Busy';
const USED = 'WorkerArtifactPreembedCopyV1Used', MAX = 67108864, CHUNK = 65536;
const MAX_SAFE = BigInt(Number.MAX_SAFE_INTEGER);
const IO = ['reservedCopies', 'reservedReadBytes', 'reservedWriteBytes', 'actualReadBytes', 'actualWriteBytes',
  'openAttempts', 'opened', 'closeAttempts', 'closed', 'unknownClosures', 'verifiedScans'];
const QUALIFICATION = Object.freeze({ qualified: false, linkQualification: false, closureComplete: false,
  requiresFreshAdmission: true, normalWorkerUnchangedRequired: true });
class CopyFault extends Error { constructor(code) { super(code); this.code = code; } }
const fail = code => { throw new CopyFault(code); };
const requireThat = (value, code) => { if (!value) fail(code); };
const integer = value => Number.isSafeInteger(value) && value >= 0;
const token = value => typeof value === 'string' && value.length > 0 && value.length <= 256 && !/[^A-Za-z0-9_.:-]/.test(value);
const hash = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value) && value !== '0'.repeat(64);
const clone = value => JSON.parse(JSON.stringify(value));
function freeze(value) {
  if (value !== null && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}
function data(value, names, code) {
  try {
    requireThat(value !== null && typeof value === 'object' &&
      [Object.prototype, null].includes(Object.getPrototypeOf(value)), code);
    const keys = Reflect.ownKeys(value);
    requireThat(keys.length === names.length && keys.every(k => typeof k === 'string' && names.includes(k)), code);
    const result = {};
    for (const key of names) {
      const d = Object.getOwnPropertyDescriptor(value, key);
      requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code);
      result[key] = d.value;
    }
    return result;
  } catch { fail(code); }
}
function recipeOf(spec) {
  let config;
  try { ({ config } = data(spec, ['config'], INVALID)); } catch { throw Error(INVALID); }
  return planWorkerArtifactComparisonV1(config);
}
function adapterOf(adapter) {
  try {
    const out = data(adapter, ['identify', 'open', 'now'], INVALID);
    requireThat(Object.values(out).every(value => typeof value === 'function'), INVALID);
    return out;
  } catch { throw Error(INVALID); }
}
function requestOf(value, expected) {
  const r = data(value, ['candidate', 'rootIdentity', 'executableIdentity', 'manifestIdentity', 'linked'], 'INPUT');
  requireThat(r.candidate === expected && token(r.rootIdentity) && token(r.executableIdentity) &&
    token(r.manifestIdentity) && r.executableIdentity !== r.manifestIdentity, 'INPUT');
  const linked = data(r.linked, ['executable', 'manifest'], 'INPUT');
  const executable = data(linked.executable, ['sha256', 'bytes'], 'INPUT');
  const manifest = data(linked.manifest, ['sha256', 'bytes'], 'INPUT');
  for (const [fact, limit] of [[executable, MAX], [manifest, 65536]]) {
    requireThat(hash(fact.sha256) && integer(fact.bytes) && fact.bytes >= 1 && fact.bytes <= limit, 'INPUT');
  }
  return freeze({ ...r, linked: { executable, manifest } });
}
function counters() {
  const io = Object.fromEntries(IO.map(key => [key, 0]));
  io.actualReadBytes = 0n; io.actualWriteBytes = 0n;
  return io;
}
function publicCounters(io) {
  return Object.fromEntries(IO.map(key => {
    const n = io[key];
    return [key, typeof n === 'bigint' ? (n <= MAX_SAFE ? Number(n) : n.toString()) : n];
  }));
}

function core(recipe, adapter) {
  const totals = counters(); let index = 0, busy = false, ended = false, cancelled = false;
  let uncertain = false, lastNow = null;
  function cancel() {
    if (ended || index === 2 || cancelled) return false;
    cancelled = true; return true;
  }
  function snapshot() {
    return freeze({ version: 1, kind: 'worker_artifact_preembed_copy_snapshot_v1',
      nextCandidate: ended || cancelled || index === 2 ? null : recipe.candidates[index].id,
      busy, stopped: ended || cancelled, io: publicCounters(totals),
      unknownClosure: totals.unknownClosures > 0, ioUncertain: uncertain, ...QUALIFICATION });
  }
  async function copyNext(...args) {
    if (busy) throw Error(BUSY);
    if (ended || index === 2) throw Error(USED);
    busy = true;
    const io = counters(), acquired = []; let req = null, code = null, jobUncertain = false, start = null;
    const candidate = recipe.candidates[index];
    function add(key, n = 1) { io[key] += n; totals[key] += n; }
    function markUncertain() { jobUncertain = true; uncertain = true; }
    function time() {
      let value;
      try { value = adapter.now(); } catch { fail('CLOCK'); }
      requireThat(typeof value === 'number' && Number.isFinite(value) && value >= 0 &&
        (lastNow === null || value >= lastNow), 'CLOCK');
      lastNow = value; return value;
    }
    function live() {
      requireThat(!cancelled, 'CANCELLED');
      const now = time(); requireThat(now - start <= 60000, 'DEADLINE');
    }
    async function offer(fn, ...values) {
      live(); const result = await fn(...values); live(); return result;
    }
    async function identify(path, kind, identity) {
      const value = data(await offer(adapter.identify, path, kind), ['identity', 'ordinary', 'real'], 'IDENTITY');
      requireThat(token(value.identity) && value.identity === identity && value.ordinary === true && value.real === true, 'IDENTITY');
    }
    async function stat(handle, identity, expectedBytes) {
      const value = data(await offer(handle.identity), ['identity', 'bytes', 'ordinary'], 'IDENTITY');
      requireThat(token(value.identity) && value.identity === identity && integer(value.bytes) &&
        value.bytes <= MAX && value.bytes === expectedBytes && value.ordinary === true, 'IDENTITY');
      return value.identity;
    }
    async function acquire(path, mode) {
      live(); add('openAttempts'); let value;
      try { value = await adapter.open(path, mode); } catch { add('unknownClosures'); fail('IO'); }
      let close = null;
      // Capture cleanup without reading any getter or validating other fields first.
      try {
        const d = value !== null && typeof value === 'object' ? Object.getOwnPropertyDescriptor(value, 'close') : null;
        if (d && d.enumerable && Object.hasOwn(d, 'value') && typeof d.value === 'function') close = d.value;
      } catch { /* A usable close could not be captured; ownership remains unknown. */ }
      if (close) { acquired.push({ close }); add('opened'); } else add('unknownClosures');
      live();
      requireThat(close !== null, 'IO');
      const methods = data(value, ['identity', 'read', 'write', 'sync', 'close'], 'IO');
      requireThat(Object.values(methods).every(fn => typeof fn === 'function'), 'IO');
      return methods;
    }
    async function byteOperation(fn, field, buffer, offset, length, position, eof = false) {
      live(); let n;
      try { n = await fn(buffer, offset, length, position); } catch { markUncertain(); fail('IO'); }
      if (Number.isSafeInteger(n) && n > 0) {
        add(field, BigInt(n));
        if (io[field] > MAX_SAFE || totals[field] > MAX_SAFE) { markUncertain(); fail('IO'); }
      }
      if (!integer(n) || n > length || (field === 'actualWriteBytes' && n === 0)) {
        markUncertain(); fail('IO');
      }
      live();
      if (eof) requireThat(n === 0, 'CONTENT');
      else requireThat(n > 0, 'IO'); // Known premature EOF is not an uncertain byte return.
      return n;
    }
    async function scan(handle, identity, fact, buffer, destination = null) {
      const digest = createHash('sha256'); let position = 0;
      while (position < fact.bytes) {
        const n = await byteOperation(handle.read, 'actualReadBytes', buffer, 0, Math.min(CHUNK, fact.bytes - position), position);
        digest.update(buffer.subarray(0, n));
        if (destination) {
          let offset = 0;
          while (offset < n) {
            offset += await byteOperation(destination.write, 'actualWriteBytes', buffer, offset, n - offset, position + offset);
          }
        }
        position += n;
      }
      await byteOperation(handle.read, 'actualReadBytes', buffer, 0, 1, fact.bytes, true);
      requireThat(digest.digest('hex') === fact.sha256, 'CONTENT');
      await stat(handle, identity, fact.bytes); add('verifiedScans');
    }
    async function paths(includeCopy, copyIdentity) {
      await identify(candidate.outputRoot, 'directory', req.rootIdentity);
      await identify(candidate.executable, 'file', req.executableIdentity);
      await identify(candidate.manifest, 'file', req.manifestIdentity);
      if (includeCopy) await identify(candidate.preEmbedCopy, 'file', copyIdentity);
    }
    try {
      if (cancelled) fail('CANCELLED');
      requireThat(args.length === 1, 'INPUT');
      req = requestOf(args[0], candidate.id);
      add('reservedCopies');
      add('reservedReadBytes', 4 * req.linked.executable.bytes + 2 * req.linked.manifest.bytes);
      add('reservedWriteBytes', req.linked.executable.bytes);
      start = time();
      const buffer = Buffer.alloc(CHUNK), executableFact = req.linked.executable, manifestFact = req.linked.manifest;
      await identify(candidate.outputRoot, 'directory', req.rootIdentity);
      const executable = await acquire(candidate.executable, 'r');
      await stat(executable, req.executableIdentity, executableFact.bytes);
      await scan(executable, req.executableIdentity, executableFact, buffer);
      await identify(candidate.executable, 'file', req.executableIdentity);
      await identify(candidate.outputRoot, 'directory', req.rootIdentity);
      const manifest = await acquire(candidate.manifest, 'r');
      await stat(manifest, req.manifestIdentity, manifestFact.bytes);
      await scan(manifest, req.manifestIdentity, manifestFact, buffer);
      await paths(false);
      const copy = await acquire(candidate.preEmbedCopy, 'wx+');
      const copyStat = data(await offer(copy.identity), ['identity', 'bytes', 'ordinary'], 'IDENTITY');
      requireThat(token(copyStat.identity) && copyStat.identity !== req.executableIdentity &&
        copyStat.identity !== req.manifestIdentity && copyStat.bytes === 0 && copyStat.ordinary === true, 'IDENTITY');
      const copyIdentity = copyStat.identity;
      await scan(executable, req.executableIdentity, executableFact, buffer, copy);
      requireThat(await offer(copy.sync) === undefined, 'IO');
      await stat(executable, req.executableIdentity, executableFact.bytes);
      await stat(manifest, req.manifestIdentity, manifestFact.bytes);
      await paths(true, copyIdentity);
      await scan(manifest, req.manifestIdentity, manifestFact, buffer);
      await stat(copy, copyIdentity, executableFact.bytes);
      await scan(copy, copyIdentity, executableFact, buffer);
      await scan(copy, copyIdentity, executableFact, buffer);
      await paths(true, copyIdentity);
    } catch (error) {
      code = error instanceof CopyFault ? error.code : 'IO';
    } finally {
      for (let i = acquired.length - 1; i >= 0; i--) {
        add('closeAttempts');
        try {
          requireThat(await acquired[i].close() === undefined, 'CLOSE'); add('closed');
        } catch {
          add('unknownClosures'); if (code === null) code = 'CLOSE';
        }
      }
      if (code === null) { try { live(); } catch (error) { code = error instanceof CopyFault ? error.code : 'IO'; } }
      if (code !== null) ended = true; else index++;
      busy = false;
    }
    return freeze({ version: 1, kind: 'worker_artifact_preembed_copy_v1', candidate: req === null ? null : candidate.id,
      ok: code === null, code, executable: code === null ? clone(req.linked.executable) : null,
      manifest: code === null ? clone(req.linked.manifest) : null, copy: code === null ? clone(req.linked.executable) : null,
      io: publicCounters(io), unknownClosure: io.unknownClosures > 0, ioUncertain: jobUncertain, ...QUALIFICATION });
  }
  return Object.freeze({ copyNext, cancel, snapshot });
}

const normalize = value => value.replaceAll('\\', '/').replace(/[A-Z]/g, c => String.fromCharCode(c.charCodeAt(0) + 32));
function physicalIdentity(stat) {
  return typeof stat.dev === 'bigint' && stat.dev >= 0n && typeof stat.ino === 'bigint' && stat.ino > 0n
    ? stat.dev.toString() + ':' + stat.ino.toString() : '';
}
const ordinaryFile = stat => stat.isFile() && !stat.isSymbolicLink() && stat.nlink === 1n;
function windowsAdapter() {
  return {
    async identify(path, kind) {
      const s = await lstat(path, { bigint: true }), physical = await realpath(path);
      return { identity: physicalIdentity(s), ordinary: kind === 'directory'
        ? s.isDirectory() && !s.isSymbolicLink() : ordinaryFile(s), real: normalize(physical) === normalize(path) };
    },
    async open(path, mode) {
      if (mode === 'r') {
        // Refuse cooperative alias/nonordinary reads before opening their contents.
        const s = await lstat(path, { bigint: true }), physical = await realpath(path);
        if (!physicalIdentity(s) || !ordinaryFile(s) || normalize(physical) !== normalize(path)) throw Error('PreembedUnsafeInput');
      }
      const handle = await fsOpen(path, mode);
      return {
        async identity() {
          const s = await handle.stat({ bigint: true });
          return { identity: physicalIdentity(s), bytes: Number(s.size), ordinary: ordinaryFile(s) };
        },
        async read(buffer, offset, length, position) { return (await handle.read(buffer, offset, length, position)).bytesRead; },
        async write(buffer, offset, length, position) { return (await handle.write(buffer, offset, length, position)).bytesWritten; },
        async sync() { await handle.sync(); },
        async close() { await handle.close(); }
      };
    },
    now: () => performance.now()
  };
}
export function createWorkerArtifactPreembedCopyV1(spec) {
  if (process.platform !== 'win32') throw Error('WorkerArtifactPreembedCopyV1Platform');
  return core(recipeOf(spec), adapterOf(windowsAdapter()));
}
export function createWorkerArtifactPreembedCopyV1ForTesting(spec, adapter) {
  return core(recipeOf(spec), adapterOf(adapter));
}
