// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent FIRST against contractc86eb0ec; SOURCE ONLY /18 groups UNRUN.
// No producer/project imports, top-level suite, files, env, child or SDK data.
// Synthetic Buffers below establish metadata behavior, never native/link acceptance.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const V1 = 'msvc-library-metadata-v1', V2 = 'msvc-library-metadata-v2', STRICT = 'strict-v1';
const KIND = 'library_archive_alignment_v2_first_v1';
const LIMITS = { inputBytesExclusive: 268435456, memberBytesExclusive: 268435456,
  memberSections: 65536, inputSections: 262144, jobSections: 2097152,
  jobInputs: 32, jobInputBytes: 536870912, jobFileReadBytes: 1073741824,
  members: 65536, longnames: 65536, tokens: 65536, directiveBytes: 1048576,
  nameBytes: 4096, libraryNameBytes: 255 };
const ZERO = { unknownMachineObjects: 0, unusedRelocationPointers: 0, terminalNulSections: 0 };
const CONTEXT = ['actual', 'directiveBytes', 'limit', 'memberIndex', 'memberOffset',
  'sectionIndex', 'sections', 'tokenCount'];
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const jsonCopy = value => JSON.parse(JSON.stringify(value));
const eq = (a, b) => assert.deepEqual(a, b);
function keys(value, expected) { eq(Object.keys(value).sort(), [...expected].sort()); }
function refused(action, message, site, actual, limit) {
  let error;
  try { action(); } catch (caught) { error = caught; }
  assert(error instanceof Error, 'Expected finite refusal');
  assert(['LibraryInputsFormat', 'LibraryInputsUnsafe', 'LibraryInputsDirective',
    'LibraryInputsSize', 'LibraryInputsType', 'LibraryInputsProfile'].includes(error.message));
  assert(typeof error.site === 'string' && error.site.length >= 1 && error.site.length <= 64 &&
    /^[a-z]/.test(error.site) && !/[^a-z0-9_]/.test(error.site));
  keys(error.context, CONTEXT);
  assert(Object.values(error.context).every(v => v === null || Number.isSafeInteger(v) && v >= 0));
  if (message !== undefined) assert.equal(error.message, message);
  if (site !== undefined) assert.equal(error.site, site);
  if (actual !== undefined) assert.equal(error.context.actual, actual);
  if (limit !== undefined) assert.equal(error.context.limit, limit);
  return error;
}
function unchanged(bytes, before) { assert.equal(hash(bytes), before, 'Input bytes changed'); }
function snapshot(job, id, inputCount = 0, inputBytes = 0, attempts = 0, sections = 0, stopped = false) {
  const result = job.snapshot();
  eq(result, { profileId: id, inputCount, inputBytes, attempts, sections, stopped });
  assert(Object.isFrozen(result));
  return result;
}
function result(value, mode, metadata, sections = 0, changes = {}) {
  keys(value, ['profileId', 'purpose', 'qualified', 'linkQualification', 'closureComplete',
    'metadata', 'sections', 'deviations']);
  assert.equal(value.profileId, mode);
  assert.equal(value.purpose, 'build_input_metadata_only');
  assert.equal(value.qualified, false); assert.equal(value.linkQualification, false);
  assert.equal(value.closureComplete, false);
  eq(value.metadata, metadata); assert.equal(value.sections, sections);
  eq(value.deviations, mode === V2 ? { ...ZERO, nulArchivePaddingMembers: 0, ...changes } :
    { ...ZERO, ...changes });
  return value;
}
function coff(count = 0, big = false) {
  const header = big ? 56 : 20, bytes = Buffer.alloc(header + 40 * count);
  if (big) {
    bytes.writeUInt16LE(0xffff, 2); bytes.writeUInt16LE(2, 4); bytes.writeUInt16LE(0x8664, 6);
    Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex').copy(bytes, 12);
    bytes.writeUInt32LE(count, 44);
  } else { bytes.writeUInt16LE(0x8664); bytes.writeUInt16LE(count, 2); }
  for (let n = 0; n < count; n++) {
    bytes.write('.text', header + n * 40, 'ascii');
    bytes.writeUInt32LE(0x40, header + n * 40 + 36);
  }
  return bytes;
}
function section(payload, name = '.drectve', flags = 0x200) {
  const data = Buffer.isBuffer(payload) ? payload : Buffer.from(payload, 'utf8');
  const bytes = Buffer.alloc(60 + data.length);
  coff(1).copy(bytes);
  bytes.fill(0, 20, 28); bytes.write(name, 20, 8, 'ascii');
  bytes.writeUInt32LE(data.length, 36); bytes.writeUInt32LE(60, 40);
  bytes.writeUInt32LE(flags, 56); data.copy(bytes, 60);
  return bytes;
}
function imported(exportAs = false) {
  //20-byte short-import header plus5 or7 valid name bytes: genuinely odd body.
  const data = Buffer.from(exportAs ? 'aa\0b\0c\0' : 'aa\0b\0', 'ascii');
  const bytes = Buffer.alloc(20 + data.length);
  bytes.writeUInt16LE(0xffff, 2); bytes.writeUInt16LE(0x8664, 6);
  bytes.writeUInt32LE(data.length, 12); bytes.writeUInt16LE((exportAs ? 4 : 1) << 2, 18);
  data.copy(bytes, 20); return bytes;
}
function memberHeader(name, length) {
  const text = name.padEnd(16, ' ') + '0'.padEnd(12, ' ') + ''.padEnd(6, ' ') +
    ''.padEnd(6, ' ') + '100644'.padEnd(8, ' ') + String(length).padEnd(10, ' ') + '`\n';
  assert.equal(text.length, 60); return Buffer.from(text, 'ascii');
}
function archive(rows) {
  const bytes = Buffer.alloc(8 + rows.reduce((n, row) => n + 60 + row.body.length + row.body.length % 2, 0));
  bytes.write('!<arch>\n', 0, 'ascii'); let at = 8;
  for (const row of rows) {
    memberHeader(row.name ?? 'm.obj/', row.body.length).copy(bytes, at);
    row.body.copy(bytes, at + 60); at += 60 + row.body.length;
    if (row.body.length % 2) bytes[at++] = row.pad ?? 10;
  }
  return bytes;
}
function one(pad = 10) { return archive([{ body: imported(), pad }]); }
function manyImports(count, pad) {
  // At65536 members this is5636104B, with a25B structurally valid import body.
  const body = imported(), header = memberHeader('m.obj/', body.length);
  const width = 60 + body.length + 1, bytes = Buffer.alloc(8 + count * width);
  bytes.write('!<arch>\n', 0, 'ascii');
  for (let n = 0; n < count; n++) {
    const at = 8 + n * width;
    header.copy(bytes, at); body.copy(bytes, at + 60); bytes[at + width - 1] = pad;
  }
  return bytes;
}
const IMPORT = { objects: 0, imports: 1, directives: [], defaultLibraries: [] };
const EMPTY = { objects: 1, imports: 0, directives: [], defaultLibraries: [] };

export async function runLibraryArchiveAlignmentV2SelfchecksV1(api) {
  if (!api || typeof api.inspectLibraryInputs !== 'function' ||
    typeof api.createLibraryMetadataJob !== 'function' ||
    typeof api.createLibraryMetadataJobV2 !== 'function' ||
    typeof api.projectLibraryMetadataDependenciesV1 !== 'function' ||
    !api.MSVC_LIBRARY_METADATA_PROFILE || !api.MSVC_LIBRARY_METADATA_PROFILE_V2) {
    throw Error('SETUP_UNRUN:LibraryArchiveAlignmentV2API');
  }
  const old = () => api.createLibraryMetadataJob(V1);
  const fresh = (...extra) => api.createLibraryMetadataJobV2(V2, ...extra);
  const parse = bytes => fresh().inspect(bytes, V2);
  const cases = [], add = (id, body) => cases.push([id, body]);

  add('A01', () => {
    eq(api.MSVC_LIBRARY_METADATA_PROFILE, { id: V1, version: 1,
      purpose: 'build_input_metadata_only', limits: LIMITS });
    eq(api.MSVC_LIBRARY_METADATA_PROFILE_V2, { id: V2, version: 2,
      purpose: 'build_input_metadata_only', limits: LIMITS });
    for (const descriptor of [api.MSVC_LIBRARY_METADATA_PROFILE, api.MSVC_LIBRARY_METADATA_PROFILE_V2]) {
      assert.equal(Object.getPrototypeOf(descriptor), Object.prototype);
      assert.equal(Object.getPrototypeOf(descriptor.limits), Object.prototype);
      assert(Object.isFrozen(descriptor) && Object.isFrozen(descriptor.limits));
      keys(descriptor, ['id', 'version', 'purpose', 'limits']);
    }
    const job = fresh(); keys(job, ['inspect', 'snapshot']); assert(Object.isFrozen(job));
    const a = snapshot(job, V2), b = snapshot(job, V2);
    assert.notEqual(a, b);
    const value = result(job.inspect(coff(), V2), V2, EMPTY);
    assert(!Object.isFrozen(value) && !Object.isFrozen(value.metadata) && !Object.isFrozen(value.deviations));
    snapshot(job, V2, 1, 20, 1);
  });
  add('A02', () => {
    let coercions = 0;
    const coercible = { toString() { coercions++; return V2; },
      valueOf() { coercions++; return V2; }, [Symbol.toPrimitive]() { coercions++; return V2; } };
    for (const id of [undefined, null, true, 2, V1, STRICT, new String(V2), { id: V2 },
      coercible, ' ' + V2, V2 + '\n', V2.toUpperCase()]) {
      refused(() => api.createLibraryMetadataJobV2(id), 'LibraryInputsProfile', 'metadata_profile');
    }
    assert.equal(coercions, 0);
    refused(() => api.createLibraryMetadataJob(V2), 'LibraryInputsProfile', 'metadata_profile');
    const oldMode = old();
    refused(() => oldMode.inspect(one(10), V2), 'LibraryInputsProfile', 'metadata_profile');
    snapshot(oldMode, V1, 0, 0, 0, 0, true);
    const job = fresh({ limits: { members: 1, inputSections: 0 }, allowNul: false });
    const two = archive([{ body: section(Buffer.from([65]), '.text', 0x40), pad: 0 },
      { body: imported(), pad: 0 }]);
    result(job.inspect(two, V2), V2,
      { objects: 1, imports: 1, directives: [], defaultLibraries: [] }, 1,
      { nulArchivePaddingMembers: 2 });
    const legacy = api.createLibraryMetadataJob(V1, { allowNul: true }, V2);
    refused(() => legacy.inspect(one(0), V1), 'LibraryInputsFormat', 'archive_padding_byte');
    for (const mode of [undefined, null, V1, new String(V2), { mode: V2 }, coercible, V2 + '\r']) {
      const bad = fresh();
      refused(() => bad.inspect(one(), mode), 'LibraryInputsProfile', 'metadata_profile');
      snapshot(bad, V2, 0, 0, 0, 0, true);
    }
    assert.equal(coercions, 0);
  });
  add('A03', () => {
    const bytes = one(10), before = hash(bytes);
    eq(api.inspectLibraryInputs(bytes), IMPORT);
    result(old().inspect(bytes, STRICT), STRICT, IMPORT);
    result(old().inspect(bytes, V1), V1, IMPORT);
    result(fresh().inspect(bytes, STRICT), STRICT, IMPORT);
    result(parse(bytes), V2, IMPORT);
    unchanged(bytes, before);
  });
  add('A04', () => {
    const bytes = one(0), before = hash(bytes);
    refused(() => api.inspectLibraryInputs(bytes, V2), 'LibraryInputsFormat', 'archive_padding_byte');
    for (const [create, id, mode] of [[old, V1, STRICT], [old, V1, V1], [fresh, V2, STRICT]]) {
      const job = create();
      const error = refused(() => job.inspect(bytes, mode, { allowNul: true }),
        'LibraryInputsFormat', 'archive_padding_byte');
      assert.equal(error.context.memberIndex, 0); assert.equal(error.context.memberOffset, 8);
      assert.equal(error.context.sections, 0);
      snapshot(job, id, 1, bytes.length, 1);
    }
    result(parse(bytes), V2, IMPORT, 0, { nulArchivePaddingMembers: 1 });
    unchanged(bytes, before);
  });
  add('A05', () => {
    for (let byte = 0; byte <= 255; byte++) {
      if (byte === 0 || byte === 10) continue;
      const bytes = one(byte), before = hash(bytes), job = fresh();
      const error = refused(() => job.inspect(bytes, V2), 'LibraryInputsFormat', 'archive_padding_byte');
      assert.equal(error.context.memberIndex, 0); assert.equal(error.context.memberOffset, 8);
      assert.equal(error.context.sections, 0);
      snapshot(job, V2, 1, bytes.length, 1);
      unchanged(bytes, before);
    }
  });
  add('A06', () => {
    const full = one(0);
    for (const bytes of [full.subarray(0, full.length - 1), full.subarray(0, 67)]) {
      refused(() => parse(bytes), 'LibraryInputsFormat');
    }
    const trailer = Buffer.from(full); trailer[66] = 0;
    refused(() => parse(trailer), 'LibraryInputsFormat', 'archive_header_end');
    const decimal = Buffer.from(full); decimal.fill(32, 56, 66); decimal.write('+25', 56, 'ascii');
    refused(() => parse(decimal), 'LibraryInputsFormat', 'archive_member_size_decimal');
    const magic = Buffer.from(full); magic[0] = 0;
    refused(() => parse(magic), 'LibraryInputsFormat');
    const overBody = Buffer.from(full); overBody.write('9999999999', 56, 'ascii');
    refused(() => parse(overBody), 'LibraryInputsSize', 'archive_member_bytes');
  });
  add('A07', () => {
    const even = coff();
    result(parse(archive([{ body: even }, { body: imported(), pad: 0 }])), V2,
      { objects: 1, imports: 1, directives: [], defaultLibraries: [] }, 0,
      { nulArchivePaddingMembers: 1 });
    const first = archive([{ body: even }]), next = one(10).subarray(8);
    // A stray byte is not padding after an even member; do not scan ahead.
    refused(() => parse(Buffer.concat([first, Buffer.from([0]), next])), 'LibraryInputsFormat');
    refused(() => parse(Buffer.concat([one(0), Buffer.from([0])])),
      'LibraryInputsFormat', 'archive_header_range');
    const missingPadThenHeader = Buffer.concat([one(0).subarray(0, 93), next]);
    refused(() => parse(missingPadThenHeader), 'LibraryInputsFormat', 'archive_padding_byte');
  });
  add('A08', () => {
    const rows = [{ name: '/', body: Buffer.from([0]), pad: 0 },
      { name: '//', body: Buffer.from('name\0', 'ascii'), pad: 0 },
      { name: '/0', body: imported(), pad: 0 }];
    const bytes = archive(rows), before = hash(bytes);
    result(parse(bytes), V2, IMPORT, 0, { nulArchivePaddingMembers: 3 });
    const lf = archive(rows.map(row => ({ ...row, pad: 10 })));
    result(parse(lf), V2, IMPORT);
    eq(api.inspectLibraryInputs(lf), IMPORT);
    // The body contains import and longname NULs too; only alignment contributes.
    assert.equal(parse(bytes).deviations.nulArchivePaddingMembers, 3);
    unchanged(bytes, before);
    const mixed = archive([{ body: imported(), pad: 10 }, { body: imported(), pad: 0 },
      { body: imported(), pad: 10 }, { body: imported(), pad: 0 }]);
    result(parse(mixed), V2, { ...IMPORT, imports: 4 }, 0, { nulArchivePaddingMembers: 2 });
  });
  add('A09', () => {
    const bad = coff(); bad.writeUInt16LE(0x14c);
    refused(() => parse(archive([{ body: imported(), pad: 0 }, { body: bad }])),
      'LibraryInputsFormat', 'coff_machine');
    refused(() => parse(archive([{ body: imported(), pad: 0 },
      { name: 'unknown', body: coff() }])), 'LibraryInputsFormat', 'archive_member_name');
    refused(() => parse(archive([{ name: '//', body: Buffer.from('name\0'), pad: 0 },
      { name: '/1', body: imported(), pad: 0 }])), 'LibraryInputsFormat', 'archive_longname_reference');
    const late = archive([{ body: imported(), pad: 0 }, { body: imported(), pad: 0 }]);
    late[94 + 58] = 0;
    refused(() => parse(late), 'LibraryInputsFormat', 'archive_header_end');
  });
  add('A10', () => {
    const bytes = one(0), before = hash(bytes), job = fresh();
    const a = result(job.inspect(bytes, V2), V2, IMPORT, 0, { nulArchivePaddingMembers: 1 });
    const state = job.snapshot(), descriptor = JSON.stringify(api.MSVC_LIBRARY_METADATA_PROFILE_V2);
    a.profileId = 'not-authority'; a.sections = 999;
    a.metadata.imports = 999; a.metadata.directives.push('/INCLUDE:caller');
    a.metadata.defaultLibraries.push('caller.lib'); a.deviations.nulArchivePaddingMembers = 99;
    eq(job.snapshot(), state); assert.equal(JSON.stringify(api.MSVC_LIBRARY_METADATA_PROFILE_V2), descriptor);
    const b = result(job.inspect(Buffer.from(bytes), V2), V2, IMPORT, 0, { nulArchivePaddingMembers: 1 });
    assert.notEqual(a, b); assert.notEqual(a.metadata, b.metadata); assert.notEqual(a.deviations, b.deviations);
    assert(!Object.isFrozen(b.metadata.directives) && !Object.isFrozen(b.metadata.defaultLibraries));
    unchanged(bytes, before);
    // A caller may change its own Buffer between attempts; inspect the current
    // bytes in the other mode, rather than returning a cached v2 success object.
    const changing = one(0), isolated = fresh();
    result(isolated.inspect(changing, V2), V2, IMPORT, 0, { nulArchivePaddingMembers: 1 });
    changing[changing.length - 1] = 10;
    result(isolated.inspect(changing, STRICT), STRICT, IMPORT);
    snapshot(isolated, V2, 1, changing.length, 2);
  });
  add('A11', () => {
    const compatible = coff(1); compatible.writeUInt16LE(0);
    compatible.writeUInt32LE(60, 44); // Zero-width unused relocation pointer at memberEnd.
    const before = hash(compatible);
    result(parse(compatible), V2, EMPTY, 1,
      { unknownMachineObjects: 1, unusedRelocationPointers: 1 });
    result(old().inspect(compatible, V1), V1, EMPTY, 1,
      { unknownMachineObjects: 1, unusedRelocationPointers: 1 });
    refused(() => fresh().inspect(compatible, STRICT), 'LibraryInputsFormat', 'coff_machine');
    const terminal = section('/DEFAULTLIB:a\0');
    result(parse(terminal), V2, { ...EMPTY, directives: ['/DEFAULTLIB:a'], defaultLibraries: ['a.lib'] },
      1, { terminalNulSections: 1 });
    const oddTerminal = section('/INCLUDE:a\0');
    assert.equal(oddTerminal.length % 2, 1);
    result(parse(archive([{ body: oddTerminal, pad: 0 }])), V2,
      { ...EMPTY, directives: ['/INCLUDE:a'] }, 1,
      { terminalNulSections: 1, nulArchivePaddingMembers: 1 });
    const tooEarly = Buffer.from(compatible); tooEarly.writeUInt32LE(59, 44);
    refused(() => parse(tooEarly), 'LibraryInputsFormat', 'coff_relocation_pointer');
    const overflow = coff(1); overflow.writeUInt32LE(0x01000040, 56);
    refused(() => parse(overflow), 'LibraryInputsFormat', 'coff_relocation_overflow');
    const directivePointer = section('/INCLUDE:a'); directivePointer.writeUInt32LE(60, 44);
    refused(() => parse(directivePointer), 'LibraryInputsFormat', 'coff_relocation_pointer');
    unchanged(compatible, before);
  });
  add('A12', () => {
    result(parse(coff(0, true)), V2, EMPTY);
    result(parse(archive([{ body: imported(true), pad: 0 }])), V2, IMPORT, 0,
      { nulArchivePaddingMembers: 1 });
    const big = coff(0, true); big.writeUInt16LE(3, 4);
    result(parse(big), V2, EMPTY);
    const badGuid = Buffer.from(big); badGuid[12] ^= 1;
    refused(() => parse(badGuid), 'LibraryInputsFormat', 'bigobj_class_id');
    const clr = Buffer.from(big); clr.writeUInt32LE(1, 28);
    refused(() => parse(clr), 'LibraryInputsFormat', 'bigobj_metadata');
    const badMachine = coff(); badMachine.writeUInt16LE(0x14c);
    refused(() => parse(badMachine), 'LibraryInputsFormat', 'coff_machine');
    const bigUnknownMachine = coff(0, true); bigUnknownMachine.writeUInt16LE(0, 6);
    refused(() => parse(bigUnknownMachine), 'LibraryInputsFormat', 'bigobj_machine');
    const importUnknownMachine = imported(); importUnknownMachine.writeUInt16LE(0, 6);
    refused(() => parse(importUnknownMachine), 'LibraryInputsFormat', 'import_machine');
    const optional = coff(); optional.writeUInt16LE(1, 16);
    refused(() => parse(optional), 'LibraryInputsFormat', 'coff_optional_header');
    const namePadding = coff(1); namePadding[26] = 88;
    refused(() => parse(namePadding), 'LibraryInputsFormat', 'section_name_padding');
    for (const payload of ['/LIBPATH:C:\\synthetic', '/NODEFAULTLIB', '/DEFAULTLIB:C:\\synthetic']) {
      refused(() => parse(section(payload)), 'LibraryInputsUnsafe');
    }
    for (const payload of [' /DEFAULTLIB:a\0hidden', '/DEFAULTLIB:a\0\0', '/INCLUDE:"open']) {
      refused(() => parse(section(payload)));
    }
    result(parse(section('/DEFAULTLIB:B /DEFAULTLIB:a /INCLUDE:z /INCLUDE:z')), V2,
      { ...EMPTY, directives: ['/DEFAULTLIB:B', '/DEFAULTLIB:a', '/INCLUDE:z'],
        defaultLibraries: ['a.lib', 'b.lib'] }, 1);
    refused(() => parse(Buffer.from('!<thin>\n')), 'LibraryInputsFormat');
  });
  add('A13', () => {
    const first = section(Buffer.from([65]), '.text', 0x40);
    const nul = archive([{ body: first, pad: 10 }, { body: imported(), pad: 0 }]);
    const standalone = refused(() => api.inspectLibraryInputs(nul),
      'LibraryInputsFormat', 'archive_padding_byte');
    assert.equal(standalone.context.sections, 0);
    for (const mode of [STRICT, V1]) {
      const legacy = old();
      const failure = refused(() => legacy.inspect(nul, mode),
        'LibraryInputsFormat', 'archive_padding_byte');
      assert.equal(failure.context.sections, 0);
      snapshot(legacy, V1, 1, nul.length, 1, 0);
    }
    const strict = fresh();
    const error = refused(() => strict.inspect(nul, STRICT), 'LibraryInputsFormat', 'archive_padding_byte');
    assert.equal(error.context.sections, 0);
    snapshot(strict, V2, 1, nul.length, 1, 0);
    result(strict.inspect(nul, V2), V2,
      { objects: 1, imports: 1, directives: [], defaultLibraries: [] }, 1,
      { nulArchivePaddingMembers: 1 });
    snapshot(strict, V2, 1, nul.length, 2, 1);
    const badPad = archive([{ body: first, pad: 0 }, { body: imported(), pad: 9 }]);
    const envelope = fresh();
    refused(() => envelope.inspect(badPad, V2), 'LibraryInputsFormat', 'archive_padding_byte');
    snapshot(envelope, V2, 1, badPad.length, 1, 0);
    const bad = coff(); bad.writeUInt16LE(0x14c);
    const laterBody = archive([{ body: first, pad: 0 }, { body: bad }]);
    const bodies = fresh();
    const failure = refused(() => bodies.inspect(laterBody, V2), 'LibraryInputsFormat', 'coff_machine');
    assert.equal(failure.context.sections, 1); assert.equal(failure.context.memberIndex, 1);
    snapshot(bodies, V2, 1, laterBody.length, 1, 1);

    // Declared/input section limits are reached through real bounded section
    // tables. All three live fixtures total <24MiB, not a fake counter hook.
    const member = coff(65536, true);
    const atCap = archive(Array.from({ length: 4 }, () => ({ body: member })));
    const cap = fresh();
    result(cap.inspect(atCap, V2), V2, { ...EMPTY, objects: 4 }, 262144);
    snapshot(cap, V2, 1, atCap.length, 1, 262144);
    const extra = archive([...Array.from({ length: 4 }, () => ({ body: member })), { body: coff(1) }]);
    const beyond = fresh();
    refused(() => beyond.inspect(extra, V2), 'LibraryInputsSize', 'coff_sections_total', 262145, 262144);
    // Job section work is retained even though the ordinary input cap refused.
    snapshot(beyond, V2, 1, extra.length, 1, 262145, false);
  });
  add('A14', () => {
    for (const modes of [[STRICT, V2], [V2, STRICT]]) {
      const bytes = one(10), job = fresh();
      for (const mode of modes) result(job.inspect(bytes, mode), mode, IMPORT);
      const before = snapshot(job, V2, 1, bytes.length, 2);
      refused(() => job.inspect(bytes, modes[0]), 'LibraryInputsProfile', 'metadata_repeat_attempt');
      snapshot(job, V2, 1, bytes.length, 2, 0, true);
      const stopped = job.snapshot();
      const failure = refused(() => job.inspect(null, { mode: 'other' }), 'LibraryInputsProfile', 'metadata_job_stopped');
      assert(Object.values(failure.context).every(value => value === null));
      eq(job.snapshot(), stopped); assert.equal(before.stopped, false);
    }
    const nul = one(0), mixed = fresh();
    result(mixed.inspect(nul, V2), V2, IMPORT, 0, { nulArchivePaddingMembers: 1 });
    refused(() => mixed.inspect(nul, STRICT), 'LibraryInputsFormat', 'archive_padding_byte');
    snapshot(mixed, V2, 1, nul.length, 2);

    //32 independent entry objects share one2.6MiB valid BIGOBJ backing. Their
    // logical input charges are independent; this is not a32-body allocation.
    const sectionBody = coff(65536, true), job = fresh(), entries = [];
    for (let n = 0; n < 32; n++) {
      const entry = sectionBody.subarray(0); entries.push(entry);
      result(job.inspect(entry, V2), V2, EMPTY, 65536);
    }
    snapshot(job, V2, 32, sectionBody.length * 32, 32, 2097152);
    refused(() => job.inspect(entries[0], STRICT), 'LibraryInputsSize',
      'metadata_job_sections', 2162688, 2097152);
    snapshot(job, V2, 32, sectionBody.length * 32, 33, 2097152, true);
  });
  add('A15', () => {
    const bytes = one(0), copy = Buffer.from(bytes), view = bytes.subarray(0), job = fresh();
    for (const entry of [bytes, copy, view]) {
      result(job.inspect(entry, V2), V2, IMPORT, 0, { nulArchivePaddingMembers: 1 });
    }
    snapshot(job, V2, 3, bytes.length * 3, 3);
    const invalid = fresh();
    refused(() => invalid.inspect(null, V2), 'LibraryInputsType', 'input_type');
    snapshot(invalid, V2);
    result(invalid.inspect(coff(), V2), V2, EMPTY);
    const limited = fresh();
    for (let n = 0; n < 32; n++) limited.inspect(bytes.subarray(0), V2);
    snapshot(limited, V2, 32, 32 * bytes.length, 32);
    refused(() => limited.inspect(bytes.subarray(0), V2), 'LibraryInputsSize', 'metadata_job_inputs', 33, 32);
    snapshot(limited, V2, 32, 32 * bytes.length, 32, 0, true);
    const before = limited.snapshot();
    refused(() => limited.inspect(coff(), V2), 'LibraryInputsProfile', 'metadata_job_stopped');
    eq(limited.snapshot(), before);
  });
  add('A16', () => {
    // At most32MiB of NEW fixture Buffers/text is live here. Each distinct view
    // charges its logical length, regardless of equal bytes/shared backing.
    // The512MiB job boundary is not a512MiB RAM/filesystem experiment. The
    // original94 groups retain their separate real256MiB input-bound oracle.
    const length = 32 * 1024 * 1024 - 4096;
    const backing = Buffer.alloc(length); coff().copy(backing);
    const before = hash(backing), job = fresh();
    for (let n = 0; n < 16; n++) result(job.inspect(backing.subarray(0), V2), V2, EMPTY);
    snapshot(job, V2, 16, 536805376, 16);
    //16 accepted charges leave65536 bytes. A65537-byte entry is exactly+1.
    refused(() => job.inspect(backing.subarray(0, 65537), V2), 'LibraryInputsSize',
      'metadata_job_bytes', 536870913, 536870912);
    snapshot(job, V2, 16, 536805376, 16, 0, true);
    const stopped = job.snapshot();
    refused(() => job.inspect(backing, STRICT), 'LibraryInputsProfile', 'metadata_job_stopped');
    eq(job.snapshot(), stopped); unchanged(backing, before);
  });
  add('A17', () => {
    // Three complete buffers ~16.2MiB; no SDK data or256MiB allocation. Each
    // member is a valid odd short import, not a dummy zero-size count entry.
    const lf = manyImports(65536, 10), nul = manyImports(65536, 0), over = manyImports(65537, 0);
    assert.equal(lf.length, 5636104);
    const before = hash(nul);
    eq(api.inspectLibraryInputs(lf), { ...IMPORT, imports: 65536 });
    result(parse(nul), V2, { ...IMPORT, imports: 65536 }, 0,
      { nulArchivePaddingMembers: 65536 });
    const job = fresh();
    // Existing cap reports already accepted envelope-member count65536 at the
    // next header, not the total requested count65537. Preserve that context.
    const error = refused(() => job.inspect(over, V2), 'LibraryInputsSize', 'archive_members', 65536, 65536);
    assert.equal(error.context.memberIndex, 65536);
    assert.equal(error.context.memberOffset, 5636104);
    snapshot(job, V2, 1, over.length, 1, 0, false);
    unchanged(nul, before);
  });
  add('A18', () => {
    const legacy = old(), observations = [], pins = [];
    for (let i = 0; i < 32; i++) {
      const value = result(legacy.inspect(coff(), V1), V1, EMPTY);
      observations.push({ slot: i + 1, result: value });
      pins.push({ slot: i + 1, metadataSha256: hash(Buffer.from(JSON.stringify(value.metadata))), libraryCount: 0 });
    }
    const catalog = Array.from({ length: 15 }, (_, i) => ({ slot: i + 18,
      name: 'known-' + String(i).padStart(2, '0') + '.lib' }));
    const project = api.projectLibraryMetadataDependenciesV1;
    const facts = project(pins, observations, catalog); // VALID complete baseline first.
    assert.equal(facts.kind, 'msvc_library_dependency_facts_v1');
    assert.equal(facts.qualified, false); assert.equal(facts.linkQualification, false);
    assert.equal(facts.closureComplete, false); assert.equal(facts.captureComplete, true);
    eq(facts.libraryNames, []); assert.equal(facts.rows.length, 32);
    const actualV2 = result(parse(coff()), V2, EMPTY);
    for (const forged of [false, true]) {
      const changed = jsonCopy(observations), inserted = jsonCopy(actualV2);
      if (forged) inserted.profileId = V1; // Fourth key still identifies v2 shape.
      changed[12].result = inserted;
      let error;
      try { project(pins, changed, catalog); } catch (caught) { error = caught; }
      assert(error instanceof Error);
      assert.equal(error.message, 'LibraryMetadataDependencyFactsInvalid');
    }
    // The genuine old result/projection remains accepted after both refusals.
    eq(project(pins, observations, catalog), facts);
    keys(observations[0].result.deviations, Object.keys(ZERO));
    snapshot(legacy, V1, 32, 640, 32);
  });

  assert.equal(cases.length, 18);
  assert(cases.every(([id], i) => id === 'A' + String(i + 1).padStart(2, '0')));
  const failed_case_ids = [];
  for (const [id, body] of cases) {
    try { await body(); } catch { failed_case_ids.push(id); }
  }
  return { version: 1, kind: KIND, executed: 18,
    passed: 18 - failed_case_ids.length, failed: failed_case_ids.length, failed_case_ids };
}
