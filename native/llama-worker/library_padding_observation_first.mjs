// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST against contract969901e9. SOURCE ONLY / ALL24 UNRUN.
// No producer import, top-level suite, filesystem, environment, timer or child.
// These are synthetic byte fixtures and fake handles, never SDK observations.
import { createHash } from 'node:crypto';

const MAX = 285588;
const INPUT_SHA = '7ef4eac926bf597d2f243f16cdfed7e0db22cb3ca34a1d7e088a84c994a03d66';
const IO_KEYS = ['reservedInputs', 'reservedBytes', 'reservedReadBytes',
  'actualReadBytes', 'opened', 'closed', 'verifiedPasses'];
const PROOF_KEYS = ['module', 'first', 'parentFirst', 'reader', 'supervisor',
  'roster', 'predecessorSnapshot', 'predecessorProcess', 'predecessorResult',
  'predecessorRootReview', 'descriptor'];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const copy = value => JSON.parse(JSON.stringify(value));
function check(value) { if (!value) throw Error('PaddingFirstAssertion'); }
function same(a, b) {
  const ordered = value => Array.isArray(value) ? value.map(ordered) :
    value !== null && typeof value === 'object' ? Object.fromEntries(
      Object.keys(value).sort().map(key => [key, ordered(value[key])])) : value;
  check(JSON.stringify(ordered(a)) === JSON.stringify(ordered(b)));
}
function ownKeys(value, expected) {
  same(Object.keys(value).sort(), [...expected].sort());
}
function errorShape(error, code) {
  check(error?.name === 'PaddingObservationError' && error.message === code &&
    error.code === code && Object.hasOwn(error, 'io'));
  check(error.io === null || Object.isFrozen(error.io));
  if (error.io !== null) ownKeys(error.io, IO_KEYS);
  return error;
}
function rejects(fn, code) {
  let error;
  try { fn(); } catch (caught) { error = caught; }
  check(error !== undefined);
  return errorShape(error, code);
}
async function rejectsAsync(fn, code) {
  let error;
  try { await fn(); } catch (caught) { error = caught; }
  check(error !== undefined);
  return errorShape(error, code);
}
function deepFrozen(value) {
  if (value !== null && typeof value === 'object') {
    check(!Buffer.isBuffer(value) && Object.isFrozen(value));
    for (const child of Object.values(value)) deepFrozen(child);
  }
}

// Construct headers directly from fixed sizes, not by invoking/copying a parser.
// Body fill is deliberately meaningless; only framing/padding is under test.
function archive(sizes, padValues = [], tail = 0) {
  const length = 8 + sizes.reduce((n, size) => n + 60 + size + size % 2, 0) + tail;
  const buffer = Buffer.alloc(length, 0xd3);
  Buffer.from('!<arch>\n').copy(buffer);
  const headers = [];
  let at = 8;
  for (let index = 0; index < sizes.length; index++) {
    const bytes = sizes[index];
    buffer.fill(32, at, at + 60);
    buffer.write('synthetic/', at, 'ascii');
    buffer.write('0', at + 16, 'ascii');
    buffer.write('0', at + 28, 'ascii');
    buffer.write('0', at + 34, 'ascii');
    buffer.write('100644', at + 40, 'ascii');
    buffer.write(String(bytes).padEnd(10, ' '), at + 48, 'ascii');
    buffer[at + 58] = 0x60; buffer[at + 59] = 10;
    const bodyStart = at + 60, bodyEnd = bodyStart + bytes;
    buffer.fill(65, bodyStart, bodyEnd);
    const paddingRequired = bytes % 2 === 1;
    const paddingOffset = paddingRequired ? bodyEnd : null;
    const paddingByte = paddingRequired ? (padValues[index] ?? 10) : null;
    if (paddingRequired) buffer[bodyEnd] = paddingByte;
    headers.push({ index, offset: at, bytes, bodyStart, bodyEnd,
      paddingRequired, paddingOffset, paddingByte });
    at = bodyEnd + (paddingRequired ? 1 : 0);
  }
  return { buffer, headers };
}
function expectedObservation(fixture, index) {
  const final = fixture.headers[index], b = fixture.buffer, at = final.offset;
  return { headers: fixture.headers.slice(0, index + 1).map(h => ({ ...h })),
    target: { memberIndex: index, memberOffset: at, memberBytes: final.bytes,
      bodyStart: final.bodyStart, bodyEnd: final.bodyEnd,
      paddingRequired: final.paddingRequired, paddingOffset: final.paddingOffset,
      paddingByte: final.paddingByte, nameHex: b.subarray(at, at + 16).toString('hex'),
      sizeHex: b.subarray(at + 48, at + 58).toString('hex'), endHex: '600a' } };
}
function target(fixture, index = 0) {
  return { memberIndex: index, memberOffset: fixture.headers[index].offset };
}
function observed(api, fixture, index = 0) {
  const before = Buffer.from(fixture.buffer);
  const result = api.observeArchivePaddingV1(fixture.buffer, target(fixture, index));
  same(result, expectedObservation(fixture, index));
  check(fixture.buffer.equals(before));
  deepFrozen(result);
  return result;
}
function zeroIO() {
  return { reservedInputs: 0, reservedBytes: 0, reservedReadBytes: 0,
    actualReadBytes: 0, opened: false, closed: false, verifiedPasses: 0 };
}
function fullIO(bytes = MAX) {
  return { reservedInputs: 1, reservedBytes: bytes, reservedReadBytes: 2 * bytes,
    actualReadBytes: 2 * bytes, opened: true, closed: true, verifiedPasses: 2 };
}

// Hook closures exist only in this in-memory fake. The API sees exactly its
// three adapter methods and three own data-property wrapper methods.
function readerFixture(data = Buffer.alloc(20, 65)) {
  const original = { bytes: data.length, sha256: hash(data),
    rootIdentity: 'synthetic-root-3', leafIdentity: 'synthetic-leaf-33' };
  const expected = { ...original };
  const state = { live: true, liveCalls: 0, identifies: 0, opens: 0,
    stats: 0, reads: 0, closes: 0, requests: [], firstBuffer: null };
  const hooks = {};
  const wrapper = {
    async stat() {
      state.stats++;
      const normal = () => ({ bytes: original.bytes, leafIdentity: original.leafIdentity });
      return hooks.stat ? hooks.stat(state.stats, normal) : normal();
    },
    async read(buffer, offset, length, position) {
      state.reads++;
      check(Buffer.isBuffer(buffer) && Number.isInteger(length) && length > 0 &&
        length <= 65536 && offset >= 0 && offset + length <= buffer.length &&
        position >= 0 && position + length <= original.bytes);
      state.requests.push({ offset, length, position });
      state.firstBuffer ??= buffer;
      const normal = (maximum = length) => {
        const bytesRead = Math.min(length, maximum);
        data.copy(buffer, offset, position, position + bytesRead);
        return { bytesRead };
      };
      return hooks.read ? hooks.read({ buffer, offset, length, position,
        call: state.reads }, normal) : normal();
    },
    async close() {
      state.closes++;
      if (hooks.close) return hooks.close();
    }
  };
  const adapter = Object.freeze({
    isLive() { state.liveCalls++; return hooks.live ? hooks.live() : state.live; },
    async identify() {
      state.identifies++;
      const normal = () => ({ bytes: original.bytes, rootIdentity: original.rootIdentity,
        leafIdentity: original.leafIdentity });
      return hooks.identify ? hooks.identify(state.identifies, normal) : normal();
    },
    async open(mode) {
      check(mode === 'r'); state.opens++;
      return hooks.open ? hooks.open(wrapper) : wrapper;
    }
  });
  return { data, original, expected, state, hooks, adapter };
}
async function readSuccess(api, f) {
  const result = await api.readPinnedArchiveV1(f.expected, f.adapter);
  ownKeys(result, ['buffer', 'io']);
  check(Object.isFrozen(result) && Object.isFrozen(result.io) &&
    Buffer.isBuffer(result.buffer) && result.buffer.equals(f.data));
  same(result.io, fullIO(f.original.bytes));
  check(f.state.opens === 1 && f.state.closes === 1 && f.state.identifies >= 2);
  return result;
}
function fixedArchive(bytes = 1, pad = 0) {
  // Four independently chosen even bodies place header4 at98452:
  // 8 + (60+98204) + 60 + 60 + 60 =98452.
  const prefix = archive([98204, 0, 0, 0, bytes], [10, 10, 10, 10, pad]);
  check(prefix.headers[4].offset === 98452 && prefix.buffer.length <= MAX);
  const buffer = Buffer.alloc(MAX, 0xd3);
  prefix.buffer.copy(buffer);
  return { buffer, headers: prefix.headers };
}
function reportFixture(api, bytes = 1, pad = 0) {
  const fixture = fixedArchive(bytes, pad);
  const observation = observed(api, fixture, 4);
  // This EXPECTED pin is schema DATA. The fake archive is not the pinned SDK
  // payload; its synthetic identities are deliberately not real machine IDs.
  return { version: 1, kind: 'ucrt_padding_observation_v1',
    purpose: 'build_input_error_site_only', qualified: false,
    linkQualification: false, closureComplete: false, captureComplete: true,
    status: 'complete', selfchecks: { version: 1, kind: 'ucrt_padding_first_v1',
      executed: 24, passed: 24, failed: 0, failed_case_ids: [] },
    proofs: copy(api.proofs), input: { name: 'ucrt.lib', rootIndex: 3,
      sourceSlot: 33, bytes: MAX, expectedSha256: INPUT_SHA,
      rootIdentity: 'synthetic-root-3', leafIdentity: 'synthetic-leaf-33' },
    io: fullIO(), observation,
    priorRefusal: { kind: 'LibraryInputsFormat', site: 'archive_padding_byte',
      memberIndex: 4, memberOffset: 98452 },
    matchesPriorRefusal: bytes % 2 === 1 && pad !== 10, critical: null };
}
function encodeSuccess(api, report) {
  const before = JSON.stringify(report);
  const result = api.encodePaddingReportV1(report);
  check(typeof result === 'string' && result.endsWith('\n') &&
    !result.endsWith('\n\n') && Buffer.byteLength(result) <= 8192 &&
    JSON.stringify(report) === before);
  const decoded = JSON.parse(result);
  check(JSON.stringify(decoded) + '\n' === result);
  same(decoded, report);
  return result;
}
function stopped(api, code, io) {
  return { ...reportFixture(api), captureComplete: false, status: 'stopped',
    io, observation: null, matchesPriorRefusal: null, critical: code };
}

export async function runPaddingObservationSelfchecksV1(api) {
  if (!api || typeof api.observeArchivePaddingV1 !== 'function' ||
    typeof api.readPinnedArchiveV1 !== 'function' ||
    typeof api.encodePaddingReportV1 !== 'function' || !api.descriptor || !api.proofs) {
    throw Error('UNRUN_SETUP:PaddingObservationAPI');
  }
  const cases = [], add = (id, body) => cases.push([id, body]);

  add('F01', () => {
    ownKeys(api, ['observeArchivePaddingV1', 'readPinnedArchiveV1',
      'encodePaddingReportV1', 'descriptor', 'proofs']);
    check(Object.isFrozen(api)); deepFrozen(api.descriptor);
    ownKeys(api.descriptor, ['id', 'version', 'purpose', 'limits']);
    ownKeys(api.descriptor.limits, ['inputBytesInclusive', 'headerCount',
      'chunkBytes', 'scans', 'selectedReadBytes', 'reportBytes', 'identityBytes']);
    same(api.descriptor, { id: 'ucrt-padding-observation-v1', version: 1,
      purpose: 'build_input_error_site_only', limits: { inputBytesInclusive: MAX,
        headerCount: 5, chunkBytes: 65536, scans: 2, selectedReadBytes: 571176,
        reportBytes: 8192, identityBytes: 256 } });
    const result = observed(api, archive([3], [0]));
    check(result.target.paddingRequired && result.target.paddingByte === 0);
    ownKeys(result, ['headers', 'target']);
  });
  add('F02', () => {
    const result = observed(api, archive([3], [10]));
    check(result.target.paddingRequired && result.target.paddingByte === 10);
  });
  add('F03', () => {
    for (const byte of [9, 13, 32, 127, 255]) {
      const result = observed(api, archive([1], [byte]));
      check(result.target.paddingByte === byte);
    }
  });
  add('F04', () => {
    for (const value of [null, '', {}, new Uint8Array(8)]) {
      rejects(() => api.observeArchivePaddingV1(value,
        { memberIndex: 0, memberOffset: 8 }), 'PaddingType');
    }
    rejects(() => api.observeArchivePaddingV1(Buffer.alloc(MAX + 1),
      { memberIndex: 0, memberOffset: 8 }), 'PaddingBounds');
    rejects(() => api.observeArchivePaddingV1(Buffer.alloc(7),
      { memberIndex: 0, memberOffset: 8 }), 'PaddingBounds');
    rejects(() => api.observeArchivePaddingV1(Buffer.alloc(8),
      { memberIndex: 0, memberOffset: 8 }), 'PaddingSignature');
  });
  add('F05', () => {
    for (const position of [8, 24, 55, 65, 66, 67]) {
      const f = archive([0]); f.buffer[position] = 0;
      rejects(() => api.observeArchivePaddingV1(f.buffer, target(f)), 'PaddingHeader');
    }
    const f = archive([0]);
    rejects(() => api.observeArchivePaddingV1(f.buffer.subarray(0, 67), target(f)),
      'PaddingBounds');
  });
  add('F06', () => {
    for (const text of ['+1', '-1', ' 1', '1x', '', '1 2']) {
      const f = archive([1]); f.buffer.fill(32, 56, 66);
      f.buffer.write(text, 56, 'ascii');
      rejects(() => api.observeArchivePaddingV1(f.buffer, target(f)), 'PaddingSize');
    }
    const f = archive([3]); f.buffer.write('0000000003', 56, 'ascii');
    observed(api, f);
  });
  add('F07', () => {
    const f = archive([4]);
    rejects(() => api.observeArchivePaddingV1(f.buffer.subarray(0, 71), target(f)),
      'PaddingBounds');
    f.buffer.write('9999999999', 56, 'ascii');
    // Ten decimal digits are numerically safe; it is the absent body that fails.
    rejects(() => api.observeArchivePaddingV1(f.buffer, target(f)), 'PaddingBounds');
  });
  add('F08', () => {
    const f = archive([1]);
    rejects(() => api.observeArchivePaddingV1(f.buffer.subarray(0, 69), target(f)),
      'PaddingBounds');
    const chain = archive([0, 1]);
    rejects(() => api.observeArchivePaddingV1(chain.buffer.subarray(0, 129), target(chain, 1)),
      'PaddingBounds');
  });
  add('F09', () => {
    const f = archive([0, 0]);
    for (const value of [null, {}, { memberIndex: 5, memberOffset: 8 },
      { memberIndex: -1, memberOffset: 8 }, { memberIndex: 0.5, memberOffset: 8 },
      { memberIndex: 0, memberOffset: 9 }, { memberIndex: 0, memberOffset: 6 },
      { memberIndex: 0, memberOffset: 8, extra: 1 }]) {
      rejects(() => api.observeArchivePaddingV1(f.buffer, value), 'PaddingType');
    }
    rejects(() => api.observeArchivePaddingV1(f.buffer,
      { memberIndex: 1, memberOffset: 8 }), 'PaddingTarget');
    rejects(() => api.observeArchivePaddingV1(f.buffer,
      { memberIndex: 0, memberOffset: 68 }), 'PaddingTarget');
    let touched = 0;
    const accessor = { memberIndex: 0 };
    Object.defineProperty(accessor, 'memberOffset', { enumerable: true,
      get() { touched++; return 8; } });
    rejects(() => api.observeArchivePaddingV1(f.buffer, accessor), 'PaddingType');
    check(touched === 0);
    const symbolic = target(f); symbolic[Symbol('extra')] = 1;
    rejects(() => api.observeArchivePaddingV1(f.buffer, symbolic), 'PaddingType');
  });
  add('F10', () => {
    const good = archive([1, 2, 3], [10, 10, 255]);
    observed(api, good, 2);
    const bad = archive([1, 2, 3], [0, 10, 255]);
    rejects(() => api.observeArchivePaddingV1(bad.buffer, target(bad, 2)), 'PaddingPrefix');
  });
  add('F11', () => {
    const f = archive([0, 2], [], 20), result = observed(api, f, 1);
    check(!result.target.paddingRequired && result.target.paddingOffset === null &&
      result.target.paddingByte === null);
    const five = archive([0, 1, 0, 2, 0]);
    check(observed(api, five, 4).headers.length === 5);
  });
  add('F12', () => {
    const f = archive([1], [255], 120), before = Buffer.from(f.buffer);
    const result = observed(api, f), saved = JSON.stringify(result);
    check(f.buffer.equals(before));
    f.buffer.fill(0); // Returned facts contain no caller Buffer alias.
    check(JSON.stringify(result) === saved);
    check(!Reflect.set(result.target, 'paddingByte', 10));
    check(!Reflect.set(result.headers, '0', {}));
    const suffix = archive([0], [], 120);
    suffix.buffer.fill(0xff, 68); observed(api, suffix);
  });

  add('I01', async () => {
    const ordinary = await readSuccess(api, readerFixture());
    const first = ordinary.buffer[0]; ordinary.buffer[0] = first ^ 1;
    check(ordinary.buffer[0] === (first ^ 1)); ordinary.buffer[0] = first;
    const f = readerFixture(Buffer.alloc(70001, 65));
    f.hooks.read = (_request, normal) => normal(997);
    const result = await readSuccess(api, f);
    check(result.io.actualReadBytes === 140002 && f.state.reads > 2);
    check(f.state.requests.filter(r => r.position === 0).length === 2);
  });
  add('I02', async () => {
    for (const value of [0, MAX + 1, 1.5, true]) {
      const f = readerFixture(); f.expected.bytes = value;
      const error = await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingPin');
      if (error.io !== null) same(error.io, zeroIO());
      check(f.state.identifies === 0 && f.state.opens === 0 && f.state.reads === 0);
    }
    for (const change of [p => { p.sha256 = 'G'.repeat(64); },
      p => { p.rootIdentity = 'x'.repeat(257); }, p => { p.extra = 1; }]) {
      const f = readerFixture(); change(f.expected);
      await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingPin');
      check(f.state.identifies === 0 && f.state.opens === 0);
    }
    for (const change of [p => { p.sha256 += '\n'; },
      p => { p.rootIdentity += '\n'; }, p => { p.rootIdentity += '\r'; },
      p => { p.leafIdentity += '\n'; }, p => { p.leafIdentity += '\r'; }]) {
      const f = readerFixture(); change(f.expected);
      const error = await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingPin');
      if (error.io !== null) same(error.io, zeroIO());
      check(f.state.identifies === 0 && f.state.opens === 0 &&
        f.state.reads === 0 && f.state.closes === 0);
    }
    const accessor = readerFixture(); let touched = 0;
    Object.defineProperty(accessor.expected, 'bytes', { enumerable: true,
      get() { touched++; return 20; } });
    await rejectsAsync(() => api.readPinnedArchiveV1(accessor.expected, accessor.adapter), 'PaddingPin');
    check(touched === 0 && accessor.state.identifies === 0 && accessor.state.opens === 0);
    const beforeIdentify = readerFixture();
    beforeIdentify.hooks.identify = () => { throw Error('private callback text'); };
    const error = await rejectsAsync(() => api.readPinnedArchiveV1(
      beforeIdentify.expected, beforeIdentify.adapter), 'PaddingIdentity');
    same(error.io, { ...zeroIO(), reservedInputs: 1, reservedBytes: 20, reservedReadBytes: 40 });
    const max = readerFixture(Buffer.alloc(MAX, 65));
    check((await readSuccess(api, max)).io.actualReadBytes === 571176);
  });
  add('I03', async () => {
    const path = readerFixture();
    path.hooks.identify = (_n, normal) => ({ ...normal(), rootIdentity: 'different' });
    const e = await rejectsAsync(() => api.readPinnedArchiveV1(path.expected, path.adapter), 'PaddingIdentity');
    check(e.io.reservedInputs === 1 && !e.io.opened && path.state.opens === 0);
    const held = readerFixture();
    held.hooks.stat = (_n, normal) => ({ ...normal(), bytes: 21 });
    const h = await rejectsAsync(() => api.readPinnedArchiveV1(held.expected, held.adapter), 'PaddingIdentity');
    check(h.io.opened && h.io.closed && held.state.closes === 1 && held.state.reads === 0);
    const final = readerFixture();
    final.hooks.identify = (n, normal) => ({ ...normal(),
      leafIdentity: n === 1 ? final.original.leafIdentity : 'changed' });
    await rejectsAsync(() => api.readPinnedArchiveV1(final.expected, final.adapter), 'PaddingIdentity');
    check(final.state.closes === 1);
    const stat = readerFixture();
    stat.hooks.stat = (n, normal) => n === 1 ? normal() : ({ ...normal(), leafIdentity: 'changed' });
    await rejectsAsync(() => api.readPinnedArchiveV1(stat.expected, stat.adapter), 'PaddingIdentity');
    check(stat.state.closes === 1);
  });
  add('I04', async () => {
    for (const value of [0, -1, 0.5, true, 21, NaN]) {
      const f = readerFixture(); f.hooks.read = () => ({ bytesRead: value });
      const error = await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingRead');
      check(error.io.actualReadBytes === 0 && error.io.verifiedPasses === 0 &&
        error.io.opened && error.io.closed && f.state.closes === 1);
    }
    for (const result of [null, {}, { bytesRead: 20, extra: 1 }]) {
      const f = readerFixture(); f.hooks.read = () => result;
      await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingRead');
      check(f.state.closes === 1);
    }
    const f = readerFixture(); let touched = 0;
    f.hooks.read = () => Object.defineProperty({}, 'bytesRead', { enumerable: true,
      get() { touched++; return 20; } });
    await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingRead');
    check(touched === 0 && f.state.closes === 1);
  });
  add('I05', async () => {
    const first = readerFixture(); first.expected.sha256 = '0'.repeat(64);
    const a = await rejectsAsync(() => api.readPinnedArchiveV1(first.expected, first.adapter), 'PaddingHash');
    check(a.io.actualReadBytes === 20 && a.io.verifiedPasses === 0 && first.state.closes === 1);
    const second = readerFixture();
    second.hooks.read = (request, normal) => {
      const result = normal();
      if (request.call === 2) request.buffer[request.offset] ^= 1;
      return result;
    };
    const b = await rejectsAsync(() => api.readPinnedArchiveV1(second.expected, second.adapter), 'PaddingHash');
    check(b.io.actualReadBytes === 40 && b.io.verifiedPasses === 1);
    const late = readerFixture();
    late.hooks.identify = (n, normal) => {
      if (n > 1) late.state.firstBuffer[0] = late.data[0] ^ 1;
      return normal();
    };
    await rejectsAsync(() => api.readPinnedArchiveV1(late.expected, late.adapter), 'PaddingHash');
    check(late.state.closes === 1);
    const mutation = readerFixture();
    mutation.hooks.identify = (_n, normal) => {
      mutation.expected.bytes = 1; mutation.expected.sha256 = '0'.repeat(64);
      mutation.expected.rootIdentity = 'retargeted'; mutation.expected.leafIdentity = 'retargeted';
      return normal();
    };
    await readSuccess(api, mutation); // Primitive expectations were copied first.
  });
  add('I06', async () => {
    for (const value of [false, 1, null]) {
      const f = readerFixture(); f.hooks.live = () => value;
      const error = await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingStopped');
      check(error.io === null || (!error.io.opened && error.io.actualReadBytes === 0));
      check(f.state.opens === 0 && f.state.closes === 0);
    }
    const thrown = readerFixture(); thrown.hooks.live = () => { throw Error('private callback text'); };
    await rejectsAsync(() => api.readPinnedArchiveV1(thrown.expected, thrown.adapter), 'PaddingStopped');
    const lateOpen = readerFixture();
    lateOpen.hooks.open = wrapper => { lateOpen.state.live = false; return wrapper; };
    const e = await rejectsAsync(() => api.readPinnedArchiveV1(lateOpen.expected, lateOpen.adapter), 'PaddingStopped');
    check(e.io.opened && e.io.closed && e.io.actualReadBytes === 0 && lateOpen.state.closes === 1);
  });
  add('I07', async () => {
    const f = readerFixture();
    let release, reached;
    const held = new Promise(resolve => { release = resolve; });
    const ready = new Promise(resolve => { reached = resolve; });
    f.hooks.read = async (_request, normal) => {
      const result = normal(); reached(); await held; return result;
    };
    const pending = api.readPinnedArchiveV1(f.expected, f.adapter);
    // Attach rejection handling immediately, including a defective early exit.
    const settled = pending.then(value => ({ value }), error => ({ error }));
    const boundary = await Promise.race([ready.then(() => 'read'), settled.then(() => 'settled')]);
    let outcome;
    try { f.state.live = false; }
    finally { release(); outcome = await settled; }
    check(boundary === 'read' && outcome.error !== undefined);
    const error = errorShape(outcome.error, 'PaddingStopped');
    check(error.io.actualReadBytes === 20 && error.io.verifiedPasses === 0 &&
      error.io.opened && error.io.closed && f.state.reads === 1 && f.state.closes === 1);
  });
  add('I08', async () => {
    const stat = readerFixture();
    stat.hooks.stat = () => { throw Error('private first identity'); };
    stat.hooks.close = () => { throw Error('private later close'); };
    const a = await rejectsAsync(() => api.readPinnedArchiveV1(stat.expected, stat.adapter), 'PaddingIdentity');
    check(a.io.opened && !a.io.closed && stat.state.closes === 1);
    const read = readerFixture(); read.hooks.read = () => { throw Error('private read'); };
    read.hooks.close = () => { throw Error('private close'); };
    const b = await rejectsAsync(() => api.readPinnedArchiveV1(read.expected, read.adapter), 'PaddingRead');
    check(b.io.opened && !b.io.closed && b.io.actualReadBytes === 0 && b.io.verifiedPasses === 0);
    check(read.state.closes === 1);
    const close = readerFixture(); close.hooks.close = () => { throw Error('private close'); };
    const c = await rejectsAsync(() => api.readPinnedArchiveV1(close.expected, close.adapter), 'PaddingClose');
    same(c.io, { ...fullIO(20), closed: false }); check(close.state.closes === 1);
    const open = readerFixture(); open.hooks.open = () => { throw Error('private open'); };
    const o = await rejectsAsync(() => api.readPinnedArchiveV1(open.expected, open.adapter), 'PaddingRead');
    check(!o.io.opened && !o.io.closed && open.state.closes === 0);
    const malformed = readerFixture();
    malformed.hooks.open = wrapper => ({ stat: wrapper.stat, close: wrapper.close });
    const m = await rejectsAsync(() => api.readPinnedArchiveV1(malformed.expected, malformed.adapter), 'PaddingRead');
    check(m.io.opened && m.io.closed && malformed.state.closes === 1);
    const absentClose = readerFixture();
    absentClose.hooks.open = wrapper => ({ stat: wrapper.stat, read: wrapper.read });
    const n = await rejectsAsync(() => api.readPinnedArchiveV1(absentClose.expected, absentClose.adapter), 'PaddingRead');
    check(n.io.opened && !n.io.closed && absentClose.state.closes === 0);
    const accessor = readerFixture(); let touched = 0;
    accessor.hooks.open = wrapper => Object.defineProperty({ stat: wrapper.stat, read: wrapper.read },
      'close', { enumerable: true, get() { touched++; return wrapper.close; } });
    const x = await rejectsAsync(() => api.readPinnedArchiveV1(accessor.expected, accessor.adapter), 'PaddingRead');
    check(x.io.opened && !x.io.closed && touched === 0);
    for (const change of [wrapper => ({ ...wrapper, extra: 1 }),
      wrapper => Object.assign(Object.create({ foreign: true }), wrapper)]) {
      const f = readerFixture(); f.hooks.open = change;
      const error = await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingRead');
      check(error.io.opened && error.io.closed && f.state.closes === 1);
    }
    const invalidAdapter = readerFixture();
    const aType = await rejectsAsync(() => api.readPinnedArchiveV1(invalidAdapter.expected,
      { ...invalidAdapter.adapter, extra: 1 }), 'PaddingType');
    check(aType.io === null || aType.io.reservedInputs === 0);
    check(invalidAdapter.state.identifies === 0 && invalidAdapter.state.opens === 0);
    for (const value of [null, 1]) {
      const f = readerFixture(); f.hooks.open = () => value;
      const error = await rejectsAsync(() => api.readPinnedArchiveV1(f.expected, f.adapter), 'PaddingRead');
      check(!error.io.opened && !error.io.closed && f.state.closes === 0);
    }
  });

  add('E01', () => {
    ownKeys(api.proofs, PROOF_KEYS);
    for (const [bytes, pad, correlation] of [[1, 0, true], [1, 10, false], [2, 255, false]]) {
      const report = reportFixture(api, bytes, pad);
      check(report.matchesPriorRefusal === correlation);
      encodeSuccess(api, report);
    }
    // Shape-only encoder is not the parent proof/pin authenticator.
    const synthetic = reportFixture(api);
    synthetic.input.rootIdentity = 'other-synthetic-root';
    synthetic.input.leafIdentity = 'other-synthetic-leaf';
    synthetic.proofs.module = 'a'.repeat(64);
    encodeSuccess(api, synthetic);
  });
  add('E02', () => {
    const base = reportFixture(api);
    const changes = [
      r => { r.extra = 1; }, r => { delete r.critical; },
      r => { r.version = true; }, r => { r.input.bytes = '285588'; },
      r => { r.io.verifiedPasses = 1.5; }, r => { r.captureComplete = 'true'; },
      r => { r.input.bytes = 285587; }, r => { r.input.rootIndex = 2; },
      r => { r.input.sourceSlot = 34; }, r => { r.input.name = 'vcruntime.lib'; },
      r => { r.input.expectedSha256 = '0'.repeat(64); },
      r => { r.input.rootIdentity = 'bad/path'; }, r => { r.input.leafIdentity = 'x'.repeat(257); },
      r => { r.input.rootIdentity += '\n'; }, r => { r.input.rootIdentity += '\r'; },
      r => { r.input.leafIdentity += '\n'; }, r => { r.input.leafIdentity += '\r'; },
      r => { r.proofs.module += '\n'; },
      r => { r.proofs.module = 'A'.repeat(64); }, r => { r.proofs.extra = 'a'.repeat(64); },
      r => { delete r.proofs.first; }, r => { r.selfchecks.executed = 23; },
      r => { r.selfchecks.passed = '24'; }, r => { r.selfchecks.failed_case_ids = ['F01']; },
      r => { r.selfchecks.kind = 'different'; }, r => { r.qualified = true; },
      r => { r.linkQualification = 'false'; }, r => { r.closureComplete = new Boolean(false); },
      r => { r.matchesPriorRefusal = false; }, r => { r.priorRefusal.memberIndex = 3; },
      r => { r.observation.target.memberOffset = 98454; },
      r => { r.observation.headers[0].offset = 10; },
      r => { r.observation.headers[1].bodyStart++; },
      r => { r.observation.headers[4].paddingByte = 10; },
      r => { r.observation.target.sizeHex = '20'.repeat(10); },
      r => { r.observation.target.nameHex = '00'.repeat(16); },
      r => { r.observation.target.nameHex += '\n'; },
      r => { r.observation.target.sizeHex += '\r'; },
      r => { r.observation.target.endHex = '600A'; },
      r => { delete r.observation.headers[2]; },
      r => { r.observation.headers.extra = 1; },
      r => { r.input = Object.assign(Object.create({ foreign: true }), r.input); }
    ];
    for (const change of changes) {
      const r = copy(base); change(r);
      rejects(() => api.encodePaddingReportV1(r), 'PaddingReport');
    }
    const wrongMember = copy(base), small = archive([1], [0]);
    wrongMember.observation = observed(api, small);
    rejects(() => api.encodePaddingReportV1(wrongMember), 'PaddingReport');
    const symbol = copy(base); symbol.io[Symbol('extra')] = 1;
    rejects(() => api.encodePaddingReportV1(symbol), 'PaddingReport');
    const accessor = copy(base); let touched = 0;
    Object.defineProperty(accessor.io, 'actualReadBytes', { enumerable: true,
      get() { touched++; return 571176; } });
    rejects(() => api.encodePaddingReportV1(accessor), 'PaddingReport');
    check(touched === 0);
    const nullPrototype = copy(base);
    nullPrototype.input = Object.assign(Object.create(null), nullPrototype.input);
    encodeSuccess(api, nullPrototype);
  });
  add('E03', () => {
    const reserved = { ...zeroIO(), reservedInputs: 1, reservedBytes: MAX,
      reservedReadBytes: 571176 };
    const controls = [
      ['PaddingPin', zeroIO()], ['PaddingType', zeroIO()],
      ['PaddingRead', { ...reserved }], ['PaddingIdentity', { ...reserved }],
      ['PaddingRead', { ...reserved, opened: true, closed: true, actualReadBytes: 12 }],
      ['PaddingHash', { ...reserved, opened: true, closed: true, actualReadBytes: MAX }],
      ['PaddingClose', { ...fullIO(), closed: false }],
      ['PaddingStopped', { ...reserved, opened: true, closed: true, actualReadBytes: 20 }],
      ['PaddingSource', zeroIO()], ['PaddingSource', fullIO()],
      ...['PaddingSignature', 'PaddingHeader', 'PaddingSize', 'PaddingBounds',
        'PaddingPrefix', 'PaddingTarget', 'PaddingType'].map(code => [code, fullIO()])
    ];
    for (const [code, io] of controls) encodeSuccess(api, stopped(api, code, io));
    const invalid = [
      ['PaddingPin', reserved], ['PaddingClose', fullIO()],
      ['PaddingClose', { ...fullIO(), closed: false, verifiedPasses: 1 }],
      ['PaddingHash', { ...reserved, opened: true, actualReadBytes: MAX - 1 }],
      ['PaddingHeader', zeroIO()], ['PaddingType', { ...reserved, opened: true }],
      ['PaddingReport', zeroIO()],
      ['PaddingRead', { ...reserved, actualReadBytes: 1 }],
      ['PaddingRead', { ...reserved, verifiedPasses: 1 }],
      ['PaddingRead', { ...reserved, closed: true }],
      ['PaddingStopped', { ...zeroIO(), opened: true }],
      ['PaddingSource', { ...reserved, opened: true, actualReadBytes: 571177 }],
      ['PaddingSource', { ...reserved, opened: true, actualReadBytes: MAX - 1, verifiedPasses: 1 }]
    ];
    for (const [code, io] of invalid) {
      rejects(() => api.encodePaddingReportV1(stopped(api, code, io)), 'PaddingReport');
    }
    const corr = stopped(api, 'PaddingSource', zeroIO()); corr.matchesPriorRefusal = false;
    rejects(() => api.encodePaddingReportV1(corr), 'PaddingReport');
    const obs = stopped(api, 'PaddingSource', zeroIO()); obs.observation = reportFixture(api).observation;
    rejects(() => api.encodePaddingReportV1(obs), 'PaddingReport');
  });
  add('E04', () => {
    // Reachable extrema: inclusive input, longest permitted identity tokens,
    // target body through the very last byte (even) or last pad byte (odd).
    for (const bytes of [187075, 187076]) {
      const r = reportFixture(api, bytes, 255);
      r.input.rootIdentity = 'r'.repeat(256); r.input.leafIdentity = 'l'.repeat(256);
      check(r.observation.target.bodyEnd + (bytes % 2) === MAX);
      encodeSuccess(api, r);
    }
    const r = reportFixture(api); r.input.leafIdentity = 'l'.repeat(257);
    rejects(() => api.encodePaddingReportV1(r), 'PaddingReport');
    // A closed fixed-five-header report has no valid arbitrary padding field.
    // This oversized negative also violates exact keys; do not claim that it
    // dynamically isolates the8192B limit. Parent FIRST owns raw UTF8/LF tests.
    const over = reportFixture(api); over.extra = 'x'.repeat(8193);
    rejects(() => api.encodePaddingReportV1(over), 'PaddingReport');
    rejects(() => api.encodePaddingReportV1(JSON.stringify(reportFixture(api)) + '\r\n'), 'PaddingReport');
    const original = reportFixture(api), originalTarget = JSON.stringify(original.observation.target);
    const beyond = copy(original); beyond.observation.target.bodyEnd = MAX + 1;
    check(beyond.observation.target.bodyEnd === MAX + 1 &&
      Object.isFrozen(original.observation.target) &&
      JSON.stringify(original.observation.target) === originalTarget);
    rejects(() => api.encodePaddingReportV1(beyond), 'PaddingReport');
  });

  const ids = [...Array.from({ length: 12 }, (_, i) => 'F' + String(i + 1).padStart(2, '0')),
    ...Array.from({ length: 8 }, (_, i) => 'I' + String(i + 1).padStart(2, '0')),
    ...Array.from({ length: 4 }, (_, i) => 'E' + String(i + 1).padStart(2, '0'))];
  check(cases.length === 24 && cases.every(([id], i) => id === ids[i]));
  const failed_case_ids = [];
  for (const [id, body] of cases) {
    try { await body(); } catch { failed_case_ids.push(id); }
  }
  return { version: 1, kind: 'ucrt_padding_first_v1', executed: 24,
    passed: 24 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
