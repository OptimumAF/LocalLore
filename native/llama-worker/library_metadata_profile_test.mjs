// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST against D04_MSVC_METADATA_PROFILE_CONTRACT_2026-11-01.
// SOURCE-ONLY / UNRUN. 94 fixed groups; no SDK/data-file I/O, children or model.
// The real exclusive-input boundary needs ONE 256MiB backing allocation.
// Distinct subarray objects deliberately share that backing while each charges
// its full logical entry length. The 512MiB job boundary is NOT a 512MiB RAM or
// filesystem experiment. Actual read-byte enforcement belongs to the collector.
import assert from 'node:assert/strict';

const KIND = 'library_metadata_profile_synthetic_v1';
const ID = 'msvc-library-metadata-v1', STRICT = 'strict-v1';
const MAX = 268435456, JOB_BYTES = 536870912, JOB_SECTIONS = 2097152;
const EMPTY = { objects: 1, imports: 0, directives: [], defaultLibraries: [] };
const ZERO = { unknownMachineObjects: 0, unusedRelocationPointers: 0, terminalNulSections: 0 };
const CONTEXT = ['actual', 'directiveBytes', 'limit', 'memberIndex', 'memberOffset', 'sectionIndex', 'sections', 'tokenCount'];
const LIMITS = { inputBytesExclusive: MAX, memberBytesExclusive: MAX,
  memberSections: 65536, inputSections: 262144, jobSections: JOB_SECTIONS,
  jobInputs: 32, jobInputBytes: JOB_BYTES, jobFileReadBytes: 1073741824,
  members: 65536, longnames: 65536, tokens: 65536, directiveBytes: 1048576,
  nameBytes: 4096, libraryNameBytes: 255 };
const GUID = Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex');
const eq = (actual, expected) => assert.deepEqual(actual, expected);
const keys = value => Object.keys(value).sort();
const mutate = (bytes, action) => { const copy = Buffer.from(bytes); action(copy); return copy; };

function object(count = 0, big = count > 65535, machine = 0x8664) {
  const header = big ? 56 : 20, b = Buffer.alloc(header + count * 40);
  if (big) {
    b.writeUInt16LE(0xffff, 2); b.writeUInt16LE(2, 4); b.writeUInt16LE(machine, 6);
    GUID.copy(b, 12); b.writeUInt32LE(count, 44);
  } else { b.writeUInt16LE(machine); b.writeUInt16LE(count, 2); }
  for (let n = 0; n < count; n++) {
    const at = header + n * 40; b.write('.text', at, 'ascii'); b.writeUInt32LE(0x40, at + 36);
  }
  return b;
}
function declared(count) { const b = object(0, true); b.writeUInt32LE(count, 44); return b; }
function directives(payloads) {
  const data = payloads.map(p => Buffer.isBuffer(p) ? p : Buffer.from(p, 'utf8'));
  const tableEnd = 20 + 40 * data.length;
  const b = Buffer.alloc(tableEnd + data.reduce((sum, p) => sum + p.length, 0));
  b.writeUInt16LE(0x8664); b.writeUInt16LE(data.length, 2);
  let rawAt = tableEnd;
  data.forEach((p, n) => {
    const at = 20 + 40 * n; b.write('.drectve', at, 'ascii');
    b.writeUInt32LE(p.length, at + 16); b.writeUInt32LE(rawAt, at + 20);
    b.writeUInt32LE(0x200, at + 36); p.copy(b, rawAt); rawAt += p.length;
  });
  return b;
}
function directive(payload, alias = false) {
  const b = directives([payload]);
  if (!alias) return b;
  const strings = Buffer.alloc(13); strings.writeUInt32LE(13); strings.write('.drectve\0', 4, 'ascii');
  const result = Buffer.concat([b, strings]); result.fill(0, 20, 28); result.write('/4', 20, 'ascii');
  result.writeUInt32LE(b.length, 8); return result;
}
function imported(type = 1) {
  const data = Buffer.from('symbol\0fixed.dll\0' + (type === 4 ? 'exported\0' : ''), 'ascii');
  const b = Buffer.alloc(20 + data.length); b.writeUInt16LE(0xffff, 2);
  b.writeUInt16LE(0x8664, 6); b.writeUInt32LE(data.length, 12);
  b.writeUInt16LE(type << 2, 18); data.copy(b, 20); return b;
}
function archive(entries) {
  const rows = entries.map(row => Buffer.isBuffer(row) ? ['m.obj/', row] : row);
  const b = Buffer.alloc(8 + rows.reduce((sum, [, body]) => sum + 60 + body.length + body.length % 2, 0), 32);
  b.write('!<arch>\n', 0, 'ascii'); let at = 8;
  for (const [name, body] of rows) {
    const header = name.padEnd(16) + '0'.padEnd(12) + ''.padEnd(6) + ''.padEnd(6)
      + '100644'.padEnd(8) + String(body.length).padEnd(10) + '`\n';
    assert.equal(header.length, 60); b.write(header, at, 'ascii'); body.copy(b, at + 60);
    at += 60 + body.length; if (at % 2) b[at++] = 10;
  }
  return b;
}
function relocation(pointer = 60, count = 0, options = {}) {
  const b = Buffer.alloc(options.bytes ?? 60); object(1).copy(b);
  if (options.poison) b.fill(255, 60);
  if (options.directive) { b.fill(0, 20, 28); b.write('.drectve', 20, 'ascii'); }
  b.writeUInt32LE(options.rawBytes ?? 0, 36); b.writeUInt32LE(options.rawAt ?? 0, 40);
  b.writeUInt32LE(pointer, 44); b.writeUInt32LE(options.lineAt ?? 0, 48);
  b.writeUInt16LE(count, 52); b.writeUInt16LE(options.lineCount ?? 0, 54);
  b.writeUInt32LE(options.flags ?? (options.directive ? 0x200 : 0x40), 56);
  return b;
}
let backing;
function byteBacking() {
  if (!backing) { backing = Buffer.alloc(MAX); backing.writeUInt16LE(0x14c); }
  return backing;
}
let sectionMember;
function many() { return sectionMember ??= object(65536, true); }
function aggregate(extra = false) { return archive(extra ? [many(), many(), many(), many(), object(1)] : [many(), many(), many(), many()]); }
function errorOf(action, message, site, actual, limit) {
  let e; try { action(); } catch (caught) { e = caught; }
  assert(e instanceof Error, 'Expected bounded refusal');
  if (message) assert.equal(e.message, message);
  if (site) assert.equal(e.site, site);
  assert.match(e.message, /^LibraryInputs(?:Format|Unsafe|Directive|Size|Type|Profile)$/);
  assert.match(e.site, /^[a-z][a-z0-9_]{0,63}$/);
  eq(keys(e.context), CONTEXT);
  assert(Object.values(e.context).every(v => v === null || Number.isSafeInteger(v) && v >= 0));
  if (actual !== undefined) assert.equal(e.context.actual, actual);
  if (limit !== undefined) assert.equal(e.context.limit, limit);
  return e;
}
function emptyContext(e) { assert(Object.values(e.context).every(v => v === null)); }
function textRefusal(action) {
  // New-profile text failures retain the existing finite lexical/encoding
  // categories; the contract does not choose a new-profile site for each one.
  const e = errorOf(action); assert(['LibraryInputsFormat', 'LibraryInputsDirective'].includes(e.message));
}
function success(result, mode, metadata = EMPTY, sections = 0, changes = {}) {
  eq(keys(result), ['closureComplete', 'deviations', 'linkQualification', 'metadata', 'profileId', 'purpose', 'qualified', 'sections']);
  assert.equal(result.profileId, mode); assert.equal(result.purpose, 'build_input_metadata_only');
  assert.equal(result.qualified, false); assert.equal(result.linkQualification, false); assert.equal(result.closureComplete, false);
  eq(result.metadata, metadata); assert.equal(result.sections, sections); eq(result.deviations, { ...ZERO, ...changes });
  return result;
}

function run(api) {
  const create = api.createLibraryMetadataJob, inspect = api.inspectLibraryInputs;
  const profile = bytes => create(ID).inspect(bytes, ID);
  const snap = (job, inputCount = 0, inputBytes = 0, attempts = 0, sections = 0, stopped = false) => {
    const s = job.snapshot(); eq(s, { profileId: ID, inputCount, inputBytes, attempts, sections, stopped });
    assert(Object.isFrozen(s)); return s;
  };
  const stopped = (job, before) => {
    const e = errorOf(() => job.inspect(object(), ID), 'LibraryInputsProfile', 'metadata_job_stopped');
    emptyContext(e); eq(job.snapshot(), before);
    emptyContext(errorOf(() => job.inspect(null, 'other'), 'LibraryInputsProfile', 'metadata_job_stopped'));
    eq(job.snapshot(), before);
  };
  const cases = [], add = (id, action) => cases.push([id, action]);

  add('F01', () => {
    const d = api.MSVC_LIBRARY_METADATA_PROFILE;
    eq(d, { id: ID, version: 1, purpose: 'build_input_metadata_only', limits: LIMITS });
    assert.equal(Object.getPrototypeOf(d), Object.prototype); assert.equal(Object.getPrototypeOf(d.limits), Object.prototype);
    assert(Object.isFrozen(d)); assert(Object.isFrozen(d.limits));
  });
  add('F02', () => {
    const d = api.MSVC_LIBRARY_METADATA_PROFILE;
    assert.throws(() => { d.limits.inputSections = 999999; });
    assert.throws(() => Object.defineProperty(d, 'purpose', { value: 'generation' }));
    assert.equal(d.limits.inputSections, 262144);
  });
  add('F03', () => {
    for (const id of [undefined, null, STRICT, 'msvc-library-metadata-v2', ID.toUpperCase(), ID + ' ', ID + '\0', 1, new String(ID), { id: ID }])
      emptyContext(errorOf(() => create(id), 'LibraryInputsProfile', 'metadata_profile'));
  });
  add('F04', () => {
    let coerced = 0; const selector = { toString() { coerced++; return ID; } };
    errorOf(() => create(selector), 'LibraryInputsProfile', 'metadata_profile'); assert.equal(coerced, 0);
  });
  add('F05', () => {
    const job = create(ID); eq(keys(job), ['inspect', 'snapshot']); assert(Object.isFrozen(job));
    assert.equal(typeof job.inspect, 'function'); assert.equal(typeof job.snapshot, 'function');
    assert.throws(() => { job.reset = () => {}; });
  });
  add('F06', () => { const job = create(ID); const a = snap(job), b = snap(job); assert.notEqual(a, b); assert.throws(() => { a.sections = 7; }); snap(job); });
  add('F07', () => {
    const job = create(ID); let coerced = 0;
    errorOf(() => job.inspect(object(), { toString() { coerced++; return ID; } }), 'LibraryInputsProfile', 'metadata_profile');
    assert.equal(coerced, 0); stopped(job, snap(job, 0, 0, 0, 0, true));
  });
  add('F08', () => {
    const job = create(ID); errorOf(() => job.inspect(object()), 'LibraryInputsProfile', 'metadata_profile'); snap(job, 0, 0, 0, 0, true);
    const other = create(ID); errorOf(() => other.inspect(object(), ID.toUpperCase()), 'LibraryInputsProfile', 'metadata_profile'); snap(other, 0, 0, 0, 0, true);
  });
  add('F09', () => { const job = create(ID); success(job.inspect(object(), STRICT), STRICT); success(job.inspect(object(), ID), ID); });
  add('F10', () => {
    const job = create(ID, { jobInputs: 1, inputSections: 0 });
    success(job.inspect(object(), ID, { limits: { jobInputs: 1 } }), ID);
    success(job.inspect(object(), STRICT), STRICT); snap(job, 2, 40, 2);
  });

  add('S01', () => eq(inspect(object()), EMPTY));
  add('S02', () => eq(inspect(object(), ID, { limits: LIMITS }), EMPTY));
  add('S03', () => errorOf(() => inspect(object(0, false, 0), ID), 'LibraryInputsFormat', 'coff_machine'));
  add('S04', () => errorOf(() => inspect(relocation(), { profile: ID }), 'LibraryInputsFormat', 'coff_relocation_pointer'));
  add('S05', () => errorOf(() => inspect(directive('/X:y\0'), ID), 'LibraryInputsFormat', 'directive_encoding'));
  add('S06', () => {
    const b = archive([many(), object(1)]);
    errorOf(() => inspect(b, ID), 'LibraryInputsSize', 'coff_sections_total', 65537, 65536);
  });

  add('J01', () => { const job = create(ID); snap(job); eq(job.snapshot({ reset: true }), job.snapshot()); });
  add('J02', () => { const job = create(ID), b = object(); success(job.inspect(b, STRICT), STRICT); success(job.inspect(b, ID), ID); snap(job, 1, b.length, 2); });
  add('J03', () => {
    const job = create(ID), b = object(), view = b.subarray(0);
    assert.notEqual(b, view); assert.equal(b.buffer, view.buffer);
    job.inspect(b, ID); job.inspect(view, ID); snap(job, 2, 40, 2);
  });
  add('J04', () => {
    const job = create(ID); errorOf(() => job.inspect(new Uint8Array(20), ID), 'LibraryInputsType'); snap(job);
    success(job.inspect(object(), ID), ID); snap(job, 1, 20, 1);
  });
  add('J05', () => {
    errorOf(() => inspect(byteBacking()), 'LibraryInputsSize', 'input_bytes', MAX, MAX);
    const job = create(ID); errorOf(() => job.inspect(byteBacking(), ID), 'LibraryInputsSize', undefined, MAX, MAX); snap(job);
    success(job.inspect(object(), ID), ID); snap(job, 1, 20, 1);
  });
  add('J06', () => {
    const job = create(ID), b = byteBacking().subarray(0, MAX - 1);
    errorOf(() => job.inspect(b, ID), 'LibraryInputsFormat', 'coff_machine'); snap(job, 1, MAX - 1, 1);
  });
  add('J07', () => {
    const job = create(ID), b = byteBacking();
    errorOf(() => job.inspect(b.subarray(0, MAX - 1), ID), 'LibraryInputsFormat');
    errorOf(() => job.inspect(b.subarray(0, MAX - 1), ID), 'LibraryInputsFormat');
    errorOf(() => job.inspect(Buffer.alloc(2), ID), 'LibraryInputsFormat');
    snap(job, 3, JOB_BYTES, 3);
    errorOf(() => job.inspect(Buffer.alloc(1), ID), 'LibraryInputsSize', 'metadata_job_bytes', JOB_BYTES + 1, JOB_BYTES);
    stopped(job, snap(job, 3, JOB_BYTES, 3, 0, true));
  });
  add('J08', () => {
    const job = create(ID, { jobInputs: 999 }), b = object(0, false, 0x14c);
    for (let n = 0; n < 32; n++) errorOf(() => job.inspect(b.subarray(0), ID), 'LibraryInputsFormat');
    snap(job, 32, 640, 32);
    errorOf(() => job.inspect(b.subarray(0), ID), 'LibraryInputsSize', 'metadata_job_inputs', 33, 32);
    stopped(job, snap(job, 32, 640, 32, 0, true));
  });
  add('J09', () => {
    const job = create(ID); errorOf(() => job.inspect(null, 'other'), 'LibraryInputsProfile', 'metadata_profile');
    stopped(job, snap(job, 0, 0, 0, 0, true));
  });
  add('J10', () => {
    const job = create(ID), b = object(); job.inspect(b, STRICT);
    errorOf(() => job.inspect(b, STRICT), 'LibraryInputsProfile', 'metadata_repeat_attempt');
    stopped(job, snap(job, 1, 20, 1, 0, true));
  });
  add('J11', () => {
    const job = create(ID), b = object(0, false, 0x14c); errorOf(() => job.inspect(b, ID), 'LibraryInputsFormat');
    errorOf(() => job.inspect(object(), 'other', { mode: ID }), 'LibraryInputsProfile', 'metadata_profile');
    snap(job, 1, 20, 1, 0, true);
  });
  add('J12', () => {
    const job = create(ID), b = mutate(object(7), x => x.writeUInt32LE(0xfffffff0, 40));
    errorOf(() => job.inspect(b, STRICT), 'LibraryInputsFormat'); snap(job, 1, b.length, 1, 7);
    errorOf(() => job.inspect(b, ID), 'LibraryInputsFormat'); snap(job, 1, b.length, 2, 14);
    job.inspect(object(1), ID); snap(job, 2, b.length + 60, 3, 15);
  });
  add('J13', () => {
    const job = create(ID), b = declared(65537);
    errorOf(() => job.inspect(b, ID), 'LibraryInputsSize', undefined, 65537, 65536); snap(job, 1, 56, 1, 65537);
    job.inspect(object(), ID); snap(job, 2, 76, 2, 65537);
  });
  add('J14', () => {
    const job = create(ID); errorOf(() => job.inspect(object(), null), 'LibraryInputsProfile', 'metadata_profile');
    const s = snap(job, 0, 0, 0, 0, true); eq(job.snapshot({ reset: true }), s); stopped(job, s);
  });
  add('J15', () => {
    const a = create(ID), b = create(ID), input = object(); a.inspect(input, ID); b.inspect(input, ID);
    errorOf(() => a.inspect(input, ID), 'LibraryInputsProfile'); b.inspect(input, STRICT);
    snap(a, 1, 20, 1, 0, true); snap(b, 1, 20, 2);
  });
  add('J16', () => {
    let called = 0; const job = create(ID, () => called++);
    success(job.inspect(object(), ID, () => called++), ID); assert.equal(called, 0); snap(job, 1, 20, 1);
  });

  add('C01', () => { const b = many(); eq(inspect(b), EMPTY); success(profile(b), ID, EMPTY, 65536); });
  add('C02', () => { const b = object(65537, true); errorOf(() => profile(b), 'LibraryInputsSize', undefined, 65537, 65536); });
  add('C03', () => { const b = aggregate(); success(profile(b), ID, { ...EMPTY, objects: 4 }, 262144); });
  add('C04', () => {
    const job = create(ID), b = aggregate(true);
    errorOf(() => job.inspect(b, ID), 'LibraryInputsSize', undefined, 262145, 262144);
    snap(job, 1, b.length, 1, 262145); job.inspect(object(), ID); snap(job, 2, b.length + 20, 2, 262145);
  });
  add('C05', () => {
    const job = create(ID), b = archive([many(), object(1)]);
    errorOf(() => job.inspect(b, STRICT), 'LibraryInputsSize', 'coff_sections_total', 65537, 65536);
    snap(job, 1, b.length, 1, 65537);
    success(job.inspect(b, ID), ID, { ...EMPTY, objects: 2 }, 65537); snap(job, 1, b.length, 2, 131074);
  });
  add('C06', () => { const job = create(ID), b = object(100); job.inspect(b, STRICT); job.inspect(b, ID); snap(job, 1, b.length, 2, 200); });
  add('C07', () => {
    const job = create(ID), b = aggregate();
    for (let n = 0; n < 8; n++) success(job.inspect(b.subarray(0), ID), ID, { ...EMPTY, objects: 4 }, 262144);
    snap(job, 8, b.length * 8, 8, JOB_SECTIONS);
    errorOf(() => job.inspect(object(1), ID), 'LibraryInputsSize', 'metadata_job_sections', JOB_SECTIONS + 1, JOB_SECTIONS);
    stopped(job, snap(job, 9, b.length * 8 + 60, 9, JOB_SECTIONS, true));
  });
  add('C08', () => {
    // Valid BIGOBJ headers reserve declared work before the deliberately absent
    // table is rejected. Neither refusal nor switching modes refunds that work.
    const job = create(ID), b = declared(65536);
    for (let n = 0; n < 16; n++) {
      const view = b.subarray(0);
      errorOf(() => job.inspect(view, STRICT), 'LibraryInputsFormat');
      errorOf(() => job.inspect(view, ID), 'LibraryInputsFormat');
    }
    snap(job, 16, 16 * 56, 32, JOB_SECTIONS);
    errorOf(() => job.inspect(declared(65537), ID), 'LibraryInputsSize', 'metadata_job_sections', JOB_SECTIONS + 65537, JOB_SECTIONS);
    stopped(job, snap(job, 17, 17 * 56, 33, JOB_SECTIONS, true));
  });
  add('C09', () => {
    const member = size => {
      const b = archive([object()]); b.write(String(size).padEnd(10), 56, 'ascii'); return b;
    };
    errorOf(() => profile(member(MAX - 1)), 'LibraryInputsFormat', 'archive_body_range');
    errorOf(() => profile(member(MAX)), 'LibraryInputsSize', undefined, MAX, MAX);
    errorOf(() => profile(member(MAX + 1)), 'LibraryInputsSize', undefined, MAX + 1, MAX);
  });
  add('C10', () => {
    const job = create(ID);
    for (let n = 0; n < 32; n++) errorOf(() => job.inspect(Buffer.alloc(0), ID), 'LibraryInputsFormat');
    snap(job, 32, 0, 32);
    errorOf(() => job.inspect(Buffer.alloc(0), ID), 'LibraryInputsSize', 'metadata_job_inputs', 33, 32);
    snap(job, 32, 0, 32, 0, true);
  });

  add('R01', () => success(profile(relocation()), ID, EMPTY, 1, { unusedRelocationPointers: 1 }));
  add('R02', () => success(profile(relocation(65, 0, { bytes: 80, poison: true })), ID, EMPTY, 1, { unusedRelocationPointers: 1 }));
  add('R03', () => success(profile(relocation(0)), ID, EMPTY, 1));
  add('R04', () => errorOf(() => profile(relocation(59)), 'LibraryInputsFormat'));
  add('R05', () => errorOf(() => profile(relocation(61)), 'LibraryInputsFormat'));
  add('R06', () => success(profile(relocation(60, 1, { bytes: 70 })), ID, EMPTY, 1));
  add('R07', () => errorOf(() => profile(relocation(60, 1, { bytes: 69 })), 'LibraryInputsFormat', 'coff_relocation_range'));
  add('R08', () => errorOf(() => profile(relocation(60, 1, { bytes: 70, rawAt: 60, rawBytes: 4 })), 'LibraryInputsFormat', 'coff_areas_overlap'));
  add('R09', () => errorOf(() => profile(relocation(60, 0, { flags: 0x01000040 })), 'LibraryInputsFormat', 'coff_relocation_overflow'));
  add('R10', () => {
    errorOf(() => profile(relocation(60, 0, { directive: true })), 'LibraryInputsFormat');
    const alias = directive('/X:y', true); alias.writeUInt32LE(60, 44);
    errorOf(() => profile(alias), 'LibraryInputsFormat');
  });
  add('R11', () => errorOf(() => profile(relocation(60, 0, { lineAt: 60 })), 'LibraryInputsFormat', 'coff_line_pointer'));
  add('R12', () => {
    const b = relocation(60, 0, { bytes: 64, rawAt: 60, rawBytes: 4, poison: true }), before = Buffer.from(b);
    success(profile(b), ID, EMPTY, 1, { unusedRelocationPointers: 1 }); eq(b, before);
  });

  add('H01', () => success(profile(object(0, false, 0)), ID, EMPTY, 0, { unknownMachineObjects: 1 }));
  add('H02', () => {
    const b = object(1, false, 0), before = Buffer.from(b);
    success(profile(b), ID, EMPTY, 1, { unknownMachineObjects: 1 }); eq(b, before); assert.equal(b.readUInt16LE(0), 0);
  });
  add('H03', () => errorOf(() => profile(mutate(object(1, false, 0), b => { b.writeUInt32LE(1, 36); b.writeUInt32LE(61, 40); })), 'LibraryInputsFormat', 'coff_raw_range'));
  add('H04', () => errorOf(() => profile(mutate(directive('/LIBPATH:x'), b => b.writeUInt16LE(0))), 'LibraryInputsUnsafe'));
  add('H05', () => errorOf(() => profile(object(0, false, 0x14c)), 'LibraryInputsFormat', 'coff_machine'));
  add('H06', () => errorOf(() => profile(object(0, true, 0)), 'LibraryInputsFormat', 'bigobj_machine'));
  add('H07', () => {
    success(profile(imported()), ID, { ...EMPTY, objects: 0, imports: 1 });
    errorOf(() => profile(mutate(imported(), b => b.writeUInt16LE(0, 6))), 'LibraryInputsFormat', 'import_machine');
  });
  add('H08', () => {
    errorOf(() => profile(mutate(object(0, false, 0), b => b.writeUInt16LE(1, 16))), 'LibraryInputsFormat', 'coff_optional_header');
    errorOf(() => profile(mutate(object(0, false, 0), b => b.writeUInt16LE(2, 18))), 'LibraryInputsFormat', 'coff_image_flags');
  });
  add('H09', () => {
    success(profile(object(0, true)), ID);
    success(profile(mutate(object(0, true), b => b.writeUInt16LE(3, 4))), ID);
    errorOf(() => profile(mutate(object(0, true), b => b.writeUInt16LE(1, 4))), 'LibraryInputsFormat', 'bigobj_version');
  });
  add('H10', () => {
    errorOf(() => profile(mutate(object(0, true), b => b[12] ^= 1)), 'LibraryInputsFormat', 'bigobj_class_id');
    errorOf(() => profile(mutate(object(0, true), b => b.writeUInt32LE(1, 32))), 'LibraryInputsFormat', 'bigobj_metadata');
    errorOf(() => profile(Buffer.from('!<thin>\nunsupported-body')), 'LibraryInputsFormat');
  });
  add('H11', () => {
    success(profile(imported(4)), ID, { ...EMPTY, objects: 0, imports: 1 });
    for (const bits of [3, 5 << 2, 32]) errorOf(() => profile(mutate(imported(), b => b.writeUInt16LE(bits, 18))), 'LibraryInputsFormat');
    errorOf(() => profile(imported(4).subarray(0, 25)), 'LibraryInputsFormat');
  });
  add('H12', () => success(profile(archive([object(1, false, 0), imported(), object(2, true)])), ID,
    { ...EMPTY, objects: 2, imports: 1 }, 3, { unknownMachineObjects: 1 }));

  add('T01', () => {
    const b = directive('/DEFAULTLIB:MSVCRT\0'), before = Buffer.from(b);
    success(profile(b), ID, { ...EMPTY, directives: ['/DEFAULTLIB:MSVCRT'], defaultLibraries: ['msvcrt.lib'] }, 1, { terminalNulSections: 1 });
    eq(b, before);
  });
  add('T02', () => success(profile(directive(Buffer.concat([Buffer.from([239, 187, 191]), Buffer.from('/DEFAULTLIB:"Name Lib.lib"\0')]))), ID,
    { ...EMPTY, directives: ['/DEFAULTLIB:Name Lib.lib'], defaultLibraries: ['name lib.lib'] }, 1, { terminalNulSections: 1 }));
  add('T03', () => {
    textRefusal(() => profile(directive('\0')));
    textRefusal(() => profile(directive(Buffer.from([239, 187, 191, 0]))));
  });
  add('T04', () => {
    success(profile(directive('   \0')), ID, EMPTY, 1, { terminalNulSections: 1 });
    success(profile(directive(Buffer.from([239, 187, 191, 32, 0]))), ID, EMPTY, 1, { terminalNulSections: 1 });
  });
  add('T05', () => textRefusal(() => profile(directive('/X:a\0b'))));
  add('T06', () => textRefusal(() => profile(directive('/X:a\0\0'))));
  add('T07', () => textRefusal(() => profile(directive('/DEFAULTLIB:safe\0/LIBPATH:evil'))));
  add('T08', () => {
    textRefusal(() => profile(directive('/X:"a\0')));
    errorOf(() => profile(directive('/X:"a')), 'LibraryInputsDirective', 'directive_token');
  });
  add('T09', () => textRefusal(() => profile(directive('/X:"a\0"'))));
  add('T10', () => {
    textRefusal(() => profile(directive('/X:\u00e9\0')));
    textRefusal(() => profile(directive(Buffer.from([239, 187, 191, 47, 88, 58, 255, 0]))));
  });
  add('T11', () => { for (const c of ['\t', '\r', '\n', '\x7f']) textRefusal(() => profile(directive('/X:a' + c + '\0'))); });
  add('T12', () => {
    success(profile(directive('/X:"a""b"\0')), ID, { ...EMPTY, directives: ['/X:a"b'] }, 1, { terminalNulSections: 1 });
    success(profile(directive('/X:"say \\"ok\\""\0')), ID, { ...EMPTY, directives: ['/X:say "ok"'] }, 1, { terminalNulSections: 1 });
  });
  add('T13', () => {
    const text = '/X:y' + ' '.repeat(1048576 - 5) + '\0';
    success(profile(directive(text)), ID, { ...EMPTY, directives: ['/X:y'] }, 1, { terminalNulSections: 1 });
  });
  add('T14', () => {
    const text = '/X:y' + ' '.repeat(1048576 - 4) + '\0';
    errorOf(() => profile(directive(text)), 'LibraryInputsSize', undefined, 1048577, 1048576);
  });
  add('T15', () => {
    const text = '/X:y' + ' '.repeat(524288 - 5) + '\0';
    success(profile(directives([text, text])), ID, { ...EMPTY, directives: ['/X:y'] }, 2, { terminalNulSections: 2 });
  });
  add('T16', () => {
    const a = '/X:y' + ' '.repeat(524288 - 5) + '\0', b = a + ' ';
    // The second section exceeds the aggregate budget BEFORE text parsing.
    errorOf(() => profile(directives([a, b])), 'LibraryInputsSize', undefined, 1048577, 1048576);
  });

  add('D01', () => {
    for (const name of ['C:\\fixed.lib', '../fixed.lib', '\\\\fixed\\share.lib', 'fixed:stream.lib', '.hidden.lib', 'fixed.exe'])
      errorOf(() => profile(directive('/DEFAULTLIB:' + name)), 'LibraryInputsUnsafe');
  });
  add('D02', () => {
    for (const token of ['/LIBPATH:x', '-libpath:x', '/NODEFAULTLIB', '-NoDefaultLib:msvcrt']) errorOf(() => profile(directive(token)), 'LibraryInputsUnsafe');
    const job = create(ID), bad = directive('/LIBPATH:x'); errorOf(() => job.inspect(bad, ID), 'LibraryInputsUnsafe');
    success(job.inspect(object(), ID), ID); snap(job, 2, bad.length + 20, 2, 1);
  });
  add('D03', () => { for (const token of ['@fixed.rsp', 'unprefixed']) errorOf(() => profile(directive(token)), 'LibraryInputsDirective'); });
  add('D04', () => {
    errorOf(() => profile(archive([['//', Buffer.from('long.obj\0')], ['/1', object()]])), 'LibraryInputsFormat');
    errorOf(() => profile(mutate(archive([directive(' ')]), b => b[b.length - 1] = 32)), 'LibraryInputsFormat');
  });
  add('D05', () => {
    success(profile(directive('/X:y\0', true)), ID, { ...EMPTY, directives: ['/X:y'] }, 1, { terminalNulSections: 1 });
    errorOf(() => profile(mutate(directive('/X:y', true), b => b.write('/5', 20, 'ascii'))), 'LibraryInputsFormat', 'section_alias_offset');
  });
  add('D06', () => {
    const b = directive('/X:y', true);
    errorOf(() => profile(mutate(b, x => x.writeUInt32LE(0xffffffff, 8))), 'LibraryInputsFormat');
    errorOf(() => profile(mutate(b, x => {
      // A non-directive raw interval overlaps the valid symbol/string interval;
      // no earlier directive-encoding failure masks the overlap oracle.
      x.fill(0, 20, 28); x.write('.text', 20, 'ascii'); x.writeUInt32LE(x.readUInt32LE(8), 40);
    })), 'LibraryInputsFormat', 'coff_areas_overlap');
  });
  add('D07', () => {
    errorOf(() => profile(archive([Buffer.from('unknown-layout-body-long')])), 'LibraryInputsFormat');
    errorOf(() => profile(archive([['/<HYBRIDMAP>/', Buffer.alloc(4)]])), 'LibraryInputsFormat');
  });
  add('D08', () => {
    success(profile(archive([['//', Buffer.from('a'.repeat(4096) + '\0')]])), ID, { ...EMPTY, objects: 0 });
    errorOf(() => profile(archive([['//', Buffer.from('a'.repeat(4097) + '\0')]])), 'LibraryInputsFormat');
  });
  add('D09', () => {
    const name = 'a'.repeat(251) + '.lib';
    success(profile(directive('/DEFAULTLIB:' + name)), ID, { ...EMPTY, directives: ['/DEFAULTLIB:' + name], defaultLibraries: [name] }, 1);
    errorOf(() => profile(directive('/DEFAULTLIB:' + 'a'.repeat(252) + '.lib')), 'LibraryInputsUnsafe');
  });
  add('D10', () => {
    success(profile(directive('/X:y '.repeat(65536))), ID, { ...EMPTY, directives: ['/X:y'] }, 1);
    errorOf(() => profile(directive('/X:y '.repeat(65537))), 'LibraryInputsSize', undefined, 65537, 65536);
  });
  add('D11', () => {
    const b = object(); success(profile(archive(Array(65536).fill(b))), ID, { ...EMPTY, objects: 65536 });
    errorOf(() => profile(archive(Array(65537).fill(b))), 'LibraryInputsSize');
  });
  add('D12', () => {
    success(profile(archive([['//', Buffer.from('a\0'.repeat(65536))]])), ID, { ...EMPTY, objects: 0 });
    errorOf(() => profile(archive([['//', Buffer.from('a\0'.repeat(65537))]])), 'LibraryInputsSize');
  });

  const roster = [['F', 10], ['S', 6], ['J', 16], ['C', 10], ['R', 12], ['H', 12], ['T', 16], ['D', 12]]
    .flatMap(([prefix, count]) => Array.from({ length: count }, (_, i) => prefix + String(i + 1).padStart(2, '0')));
  assert.deepEqual(cases.map(([id]) => id), roster, 'Authored roster');
  let passed = 0; const failed_case_ids = [];
  for (const [id, action] of cases) { try { action(); passed++; } catch { failed_case_ids.push(id); } }
  console.log(JSON.stringify({ version: 1, kind: KIND, executed: cases.length, passed,
    failed: cases.length - passed, failed_case_ids }));
  process.exitCode = failed_case_ids.length ? 1 : 0;
}

let api;
try { api = await import('./library_inputs.mjs'); } catch { api = null; }
if (!api || typeof api.inspectLibraryInputs !== 'function' || typeof api.createLibraryMetadataJob !== 'function'
    || api.MSVC_LIBRARY_METADATA_PROFILE === undefined) {
  console.error('UNRUN_SETUP: library metadata API unavailable');
  console.log(JSON.stringify({ version: 1, kind: KIND, executed: 0, passed: 0, failed: 0, failed_case_ids: [] }));
  process.exitCode = 2;
} else run(api);
