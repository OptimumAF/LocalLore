// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only error-site observation. No filesystem/process/environment API.
// This does not change the accepted archive parser or qualify a build input.
import { createHash } from 'node:crypto';

const MAX = 285588;
const SHA = '7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66';
const IO_KEYS = ['reservedInputs', 'reservedBytes', 'reservedReadBytes',
  'actualReadBytes', 'opened', 'closed', 'verifiedPasses'];
const PROOF_KEYS = ['module', 'first', 'parentFirst', 'reader', 'supervisor',
  'roster', 'predecessorSnapshot', 'predecessorProcess', 'predecessorResult',
  'predecessorRootReview', 'descriptor'];
const HEADER_KEYS = ['index', 'offset', 'bytes', 'bodyStart', 'bodyEnd',
  'paddingRequired', 'paddingOffset', 'paddingByte'];
const TARGET_KEYS = ['memberIndex', 'memberOffset', 'memberBytes', 'bodyStart',
  'bodyEnd', 'paddingRequired', 'paddingOffset', 'paddingByte', 'nameHex', 'sizeHex', 'endHex'];
const REPORT_KEYS = ['version', 'kind', 'purpose', 'qualified', 'linkQualification',
  'closureComplete', 'captureComplete', 'status', 'selfchecks', 'proofs', 'input',
  'io', 'observation', 'priorRefusal', 'matchesPriorRefusal', 'critical'];
const INPUT_KEYS = ['name', 'rootIndex', 'sourceSlot', 'bytes', 'expectedSha256',
  'rootIdentity', 'leafIdentity'];
const FRAME_CODES = ['PaddingSignature', 'PaddingHeader', 'PaddingSize',
  'PaddingBounds', 'PaddingPrefix', 'PaddingTarget'];
const STOP_CODES = ['PaddingPin', 'PaddingType', 'PaddingIdentity', 'PaddingRead',
  'PaddingHash', 'PaddingStopped', 'PaddingClose', 'PaddingSource', ...FRAME_CODES];

function frozen(value) {
  if (value !== null && typeof value === 'object') {
    for (const child of Object.values(value)) frozen(child);
    Object.freeze(value);
  }
  return value;
}
export const PADDING_OBSERVATION_PROFILE = frozen({
  id: 'ucrt-padding-observation-v1', version: 1, purpose: 'build_input_error_site_only',
  limits: { inputBytesInclusive: MAX, headerCount: 5, chunkBytes: 65536, scans: 2,
    selectedReadBytes: 571176, reportBytes: 8192, identityBytes: 256 }
});

class PaddingObservationError extends Error {
  constructor(code, io = null) {
    super(code); this.name = 'PaddingObservationError'; this.code = code;
    this.io = io === null ? null : Object.freeze({ ...io });
  }
}
function fail(code) { throw new PaddingObservationError(code); }
function requireThat(ok, code) { if (!ok) fail(code); }
const uint = value => Number.isSafeInteger(value) && value >= 0;
const token = value => typeof value === 'string' && /^[A-Za-z0-9_.:-]{1,256}$/.test(value);
const digest = value => typeof value === 'string' && /^[0-9a-f]{64}$/.test(value);
const hash = buffer => createHash('sha256').update(buffer).digest('hex');

// Read descriptors before values: invalid accessors are never invoked.
function record(value, keys, code) {
  try {
    requireThat(value !== null && typeof value === 'object', code);
    const prototype = Object.getPrototypeOf(value);
    requireThat(prototype === Object.prototype || prototype === null, code);
    const own = Reflect.ownKeys(value);
    requireThat(own.length === keys.length && own.every(key =>
      typeof key === 'string' && keys.includes(key)), code);
    const result = {};
    for (const key of keys) {
      const d = Object.getOwnPropertyDescriptor(value, key);
      requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code);
      result[key] = d.value;
    }
    return result;
  } catch { fail(code); }
}
function dense(value, length, code) {
  try {
    requireThat(Array.isArray(value) && value.length === length, code);
    const keys = Reflect.ownKeys(value);
    requireThat(keys.length === length + 1 && keys.includes('length'), code);
    const copy = [];
    for (let i = 0; i < length; i++) {
      const d = Object.getOwnPropertyDescriptor(value, String(i));
      requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code);
      copy.push(d.value);
    }
    return copy;
  } catch { fail(code); }
}
function methods(value, keys, code) {
  const result = record(value, keys, code);
  requireThat(keys.every(key => typeof result[key] === 'function'), code);
  return result;
}
function range(buffer, at, bytes) {
  requireThat(uint(at) && uint(bytes) && at <= buffer.length &&
    bytes <= buffer.length - at, 'PaddingBounds');
}
function decimal(text, code) {
  const trimmed = text.trimEnd();
  requireThat(/^[0-9]+$/.test(trimmed), code);
  const n = Number(trimmed);
  requireThat(uint(n), code);
  return n;
}

export function observeArchivePaddingV1(buffer, target) {
  requireThat(Buffer.isBuffer(buffer), 'PaddingType');
  const t = record(target, ['memberIndex', 'memberOffset'], 'PaddingType');
  requireThat(uint(t.memberIndex) && t.memberIndex < 5 && uint(t.memberOffset) &&
    t.memberOffset >= 8 && t.memberOffset % 2 === 0, 'PaddingType');
  requireThat(buffer.length >= 8 && buffer.length <= MAX, 'PaddingBounds');
  requireThat(buffer.subarray(0, 8).equals(Buffer.from('!<arch>\n')), 'PaddingSignature');
  const headers = [];
  let at = 8;
  for (let index = 0; index <= t.memberIndex; index++) {
    // A valid target offset may not identify an earlier or different member.
    requireThat(index === t.memberIndex ? at === t.memberOffset : at < t.memberOffset,
      'PaddingTarget');
    range(buffer, at, 60);
    requireThat(buffer[at + 58] === 96 && buffer[at + 59] === 10, 'PaddingHeader');
    for (let i = 0; i < 58; i++) {
      requireThat(buffer[at + i] >= 32 && buffer[at + i] <= 126, 'PaddingHeader');
    }
    const bytes = decimal(buffer.toString('ascii', at + 48, at + 58), 'PaddingSize');
    const bodyStart = at + 60;
    range(buffer, bodyStart, bytes);
    const bodyEnd = bodyStart + bytes, paddingRequired = bytes % 2 === 1;
    if (paddingRequired) range(buffer, bodyEnd, 1);
    const paddingOffset = paddingRequired ? bodyEnd : null;
    const paddingByte = paddingRequired ? buffer[bodyEnd] : null;
    headers.push({ index, offset: at, bytes, bodyStart, bodyEnd,
      paddingRequired, paddingOffset, paddingByte });
    if (index === t.memberIndex) {
      return frozen({ headers, target: { memberIndex: index, memberOffset: at,
        memberBytes: bytes, bodyStart, bodyEnd, paddingRequired, paddingOffset,
        paddingByte, nameHex: buffer.toString('hex', at, at + 16),
        sizeHex: buffer.toString('hex', at + 48, at + 58), endHex: '600a' } });
    }
    requireThat(!paddingRequired || paddingByte === 10, 'PaddingPrefix');
    at = bodyEnd + (paddingRequired ? 1 : 0);
  }
  fail('PaddingTarget');
}

export async function readPinnedArchiveV1(expected, adapter) {
  const io = { reservedInputs: 0, reservedBytes: 0, reservedReadBytes: 0,
    actualReadBytes: 0, opened: false, closed: false, verifiedPasses: 0 };
  let firstCode = null, buffer, wrapper, close = null;
  try {
    const pin = record(expected, ['bytes', 'sha256', 'rootIdentity', 'leafIdentity'], 'PaddingPin');
    requireThat(uint(pin.bytes) && pin.bytes > 0 && pin.bytes <= MAX && digest(pin.sha256) &&
      token(pin.rootIdentity) && token(pin.leafIdentity), 'PaddingPin');
    const callbacks = methods(adapter, ['isLive', 'identify', 'open'], 'PaddingType');
    const live = () => {
      let value;
      try { value = callbacks.isLive.call(adapter); } catch { fail('PaddingStopped'); }
      requireThat(value === true, 'PaddingStopped');
    };
    const call = async (fn, receiver, code, ...args) => {
      live();
      let result;
      try { result = await fn.call(receiver, ...args); } catch { fail(code); }
      live();
      return result;
    };
    const identify = async () => {
      const found = record(await call(callbacks.identify, adapter, 'PaddingIdentity'),
        ['bytes', 'rootIdentity', 'leafIdentity'], 'PaddingIdentity');
      requireThat(found.bytes === pin.bytes && found.rootIdentity === pin.rootIdentity &&
        found.leafIdentity === pin.leafIdentity, 'PaddingIdentity');
    };
    io.reservedInputs = 1; io.reservedBytes = pin.bytes; io.reservedReadBytes = 2 * pin.bytes;
    await identify();
    live();
    try { wrapper = await callbacks.open.call(adapter, 'r'); } catch { fail('PaddingRead'); }
    if (wrapper !== null && (typeof wrapper === 'object' || typeof wrapper === 'function')) {
      io.opened = true;
      // Cleanup is discovered without invoking a possibly hostile accessor.
      try {
        const d = Object.getOwnPropertyDescriptor(wrapper, 'close');
        if (d && Object.hasOwn(d, 'value') && typeof d.value === 'function') close = d.value;
      } catch { fail('PaddingRead'); }
    }
    live();
    requireThat(io.opened, 'PaddingRead');
    const held = methods(wrapper, ['stat', 'read', 'close'], 'PaddingRead');
    const stat = async () => {
      const found = record(await call(held.stat, wrapper, 'PaddingIdentity'),
        ['bytes', 'leafIdentity'], 'PaddingIdentity');
      requireThat(found.bytes === pin.bytes && found.leafIdentity === pin.leafIdentity,
        'PaddingIdentity');
    };
    await stat();
    buffer = Buffer.alloc(pin.bytes);
    const scratch = Buffer.alloc(Math.min(65536, pin.bytes));
    for (let pass = 0; pass < 2; pass++) {
      let position = 0;
      const scan = createHash('sha256');
      while (position < pin.bytes) {
        const destination = pass === 0 ? buffer : scratch;
        const offset = pass === 0 ? position : 0;
        const length = Math.min(65536, pin.bytes - position);
        live();
        let raw;
        try { raw = await held.read.call(wrapper, destination, offset, length, position); }
        catch { fail('PaddingRead'); }
        const count = record(raw, ['bytesRead'], 'PaddingRead').bytesRead;
        requireThat(uint(count) && count > 0 && count <= length, 'PaddingRead');
        io.actualReadBytes += count; // Known returned work survives a late stop.
        live();
        scan.update(destination.subarray(offset, offset + count));
        position += count;
      }
      requireThat(scan.digest('hex') === pin.sha256, 'PaddingHash');
      io.verifiedPasses++;
      await stat();
    }
    // Always close before final path identity and retained-buffer verification.
    const successClose = close; close = null;
    try { await successClose.call(wrapper); io.closed = true; }
    catch { fail('PaddingClose'); }
    await identify();
    requireThat(hash(buffer) === pin.sha256, 'PaddingHash');
    return Object.freeze({ buffer, io: Object.freeze({ ...io }) });
  } catch (error) {
    firstCode = error instanceof PaddingObservationError ? error.code : 'PaddingRead';
  } finally {
    if (io.opened && !io.closed && close !== null) {
      // One attempt only, including malformed wrappers and stopped operations.
      const cleanup = close; close = null;
      try { await cleanup.call(wrapper); io.closed = true; }
      catch { firstCode ??= 'PaddingClose'; }
    }
  }
  throw new PaddingObservationError(firstCode ?? 'PaddingRead', io);
}

function validateIO(value, code) {
  const io = record(value, IO_KEYS, code);
  for (const key of IO_KEYS.filter(k => k !== 'opened' && k !== 'closed')) {
    requireThat(uint(io[key]), code);
  }
  requireThat(typeof io.opened === 'boolean' && typeof io.closed === 'boolean' &&
    io.reservedInputs <= 1 && io.verifiedPasses <= 2, code);
  if (io.reservedInputs === 0) {
    requireThat(io.reservedBytes === 0 && io.reservedReadBytes === 0 &&
      io.actualReadBytes === 0 && io.verifiedPasses === 0 && !io.opened && !io.closed, code);
  } else {
    requireThat(io.reservedBytes === MAX && io.reservedReadBytes === 2 * MAX &&
      io.actualReadBytes <= 2 * MAX && io.actualReadBytes >= io.verifiedPasses * MAX &&
      (!io.closed || io.opened) && (io.opened ||
        (io.actualReadBytes === 0 && io.verifiedPasses === 0 && !io.closed)), code);
  }
  return io;
}
const fullIO = io => io.reservedInputs === 1 && io.opened && io.closed &&
  io.verifiedPasses === 2 && io.actualReadBytes === 2 * MAX;

function validateObservation(value, code) {
  const o = record(value, ['headers', 'target'], code);
  const headers = dense(o.headers, 5, code), target = record(o.target, TARGET_KEYS, code);
  let at = 8, last;
  for (let i = 0; i < 5; i++) {
    const h = record(headers[i], HEADER_KEYS, code);
    for (const key of ['index', 'offset', 'bytes', 'bodyStart', 'bodyEnd']) {
      requireThat(uint(h[key]) && h[key] <= MAX, code);
    }
    requireThat(h.index === i && h.offset === at && h.offset % 2 === 0 &&
      h.bodyStart === h.offset + 60 && h.bodyEnd === h.bodyStart + h.bytes &&
      typeof h.paddingRequired === 'boolean' && h.paddingRequired === (h.bytes % 2 === 1), code);
    if (h.paddingRequired) {
      requireThat(h.paddingOffset === h.bodyEnd && h.bodyEnd < MAX &&
        uint(h.paddingByte) && h.paddingByte <= 255 && (i === 4 || h.paddingByte === 10), code);
    } else requireThat(h.paddingOffset === null && h.paddingByte === null, code);
    at = h.bodyEnd + (h.paddingRequired ? 1 : 0); last = h;
  }
  for (const [a, b] of [['memberIndex', 'index'], ['memberOffset', 'offset'],
    ['memberBytes', 'bytes'], ['bodyStart', 'bodyStart'], ['bodyEnd', 'bodyEnd'],
    ['paddingRequired', 'paddingRequired'], ['paddingOffset', 'paddingOffset'],
    ['paddingByte', 'paddingByte']]) requireThat(target[a] === last[b], code);
  requireThat(target.memberIndex === 4 && target.memberOffset === 98452 &&
    typeof target.nameHex === 'string' && /^[0-9a-f]{32}$/.test(target.nameHex) &&
    typeof target.sizeHex === 'string' && /^[0-9a-f]{20}$/.test(target.sizeHex) &&
    target.endHex === '600a', code);
  const name = Buffer.from(target.nameHex, 'hex'), size = Buffer.from(target.sizeHex, 'hex');
  requireThat(name.every(b => b >= 32 && b <= 126) &&
    size.every(b => b >= 32 && b <= 126) &&
    decimal(size.toString('ascii'), code) === target.memberBytes, code);
  return target;
}

export function encodePaddingReportV1(report) {
  const code = 'PaddingReport';
  try {
    const r = record(report, REPORT_KEYS, code);
    requireThat(r.version === 1 && r.kind === 'ucrt_padding_observation_v1' &&
      r.purpose === 'build_input_error_site_only' && r.qualified === false &&
      r.linkQualification === false && r.closureComplete === false, code);
    const s = record(r.selfchecks, ['version', 'kind', 'executed', 'passed', 'failed', 'failed_case_ids'], code);
    requireThat(s.version === 1 && s.kind === 'ucrt_padding_first_v1' && s.executed === 24 &&
      s.passed === 24 && s.failed === 0, code);
    dense(s.failed_case_ids, 0, code);
    const proofs = record(r.proofs, PROOF_KEYS, code);
    requireThat(PROOF_KEYS.every(key => digest(proofs[key])), code);
    const pin = record(r.input, INPUT_KEYS, code);
    requireThat(pin.name === 'ucrt.lib' && pin.rootIndex === 3 && pin.sourceSlot === 33 &&
      pin.bytes === MAX && pin.expectedSha256 === SHA &&
      token(pin.rootIdentity) && token(pin.leafIdentity), code);
    const prior = record(r.priorRefusal, ['kind', 'site', 'memberIndex', 'memberOffset'], code);
    requireThat(prior.kind === 'LibraryInputsFormat' && prior.site === 'archive_padding_byte' &&
      prior.memberIndex === 4 && prior.memberOffset === 98452, code);
    const io = validateIO(r.io, code);
    if (r.status === 'complete') {
      requireThat(r.captureComplete === true && r.critical === null && fullIO(io), code);
      const target = validateObservation(r.observation, code);
      requireThat(r.matchesPriorRefusal === (target.paddingRequired && target.paddingByte !== 10), code);
    } else {
      requireThat(r.status === 'stopped' && r.captureComplete === false &&
        r.observation === null && r.matchesPriorRefusal === null &&
        typeof r.critical === 'string' && STOP_CODES.includes(r.critical), code);
      if (r.critical === 'PaddingPin') requireThat(io.reservedInputs === 0, code);
      if (FRAME_CODES.includes(r.critical)) requireThat(fullIO(io), code);
      if (r.critical === 'PaddingType') requireThat(io.reservedInputs === 0 || fullIO(io), code);
      if (r.critical === 'PaddingClose') requireThat(io.opened && !io.closed &&
        io.verifiedPasses === 2 && io.actualReadBytes === 2 * MAX, code);
      if (r.critical === 'PaddingHash') requireThat(io.opened && io.actualReadBytes >= MAX, code);
      if (r.critical === 'PaddingIdentity' || r.critical === 'PaddingRead') {
        requireThat(io.reservedInputs === 1, code);
      }
    }
    const wire = JSON.stringify(report) + '\n';
    requireThat(Buffer.byteLength(wire, 'utf8') <= 8192, code);
    return wire;
  } catch { fail(code); }
}
