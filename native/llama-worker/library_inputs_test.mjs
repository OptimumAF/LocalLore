// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Synthetic Buffers; no file/env/tool/model access. SOURCE-ONLY / UNRUN.
// Full256MiB cap source-only; small count/range fixtures exercise other bounds.
import { inspectLibraryInputs as inspect } from './library_inputs.mjs';

let executed = 0, passed = 0;
const failed = [];
function test(id, action) {
  ++executed;
  try { if (action()) { ++passed; return; } } catch { /* Never print payloads. */ }
  failed.push(id);
}
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const empty = { objects: 1, imports: 0, directives: [], defaultLibraries: [] };
function rejects(bytes) {
  try { inspect(bytes); } catch (error) { return error instanceof Error && /^LibraryInputs/.test(error.message); }
  return false;
}
function changed(bytes, action) { const copy = Buffer.from(bytes); action(copy); return copy; }
const guid = Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex');
function coff(sections = [], big = false, alias = false, symbols = 0) {
  const header = big ? 56 : 20, symbolSize = big ? 20 : 18;
  const tableEnd = header + 40 * sections.length;
  const rawSize = sections.reduce((sum, section) => sum + section.data.length, 0);
  const strings = alias || symbols ? Buffer.alloc(alias ? 13 : 4) : null;
  if (strings) { strings.writeUInt32LE(strings.length); if (alias) strings.write('.drectve\0', 4, 'ascii'); }
  const b = Buffer.alloc(tableEnd + rawSize + (strings ? symbols * symbolSize + strings.length : 0));
  if (big) {
    b.writeUInt16LE(0xffff, 2); b.writeUInt16LE(2, 4); b.writeUInt16LE(0x8664, 6); guid.copy(b, 12);
    b.writeUInt32LE(sections.length, 44);
  } else { b.writeUInt16LE(0x8664); b.writeUInt16LE(sections.length, 2); }
  if (strings) {
    b.writeUInt32LE(tableEnd + rawSize, big ? 48 : 8); b.writeUInt32LE(symbols, big ? 52 : 12);
    strings.copy(b, tableEnd + rawSize + symbols * symbolSize);
  }
  let position = tableEnd;
  sections.forEach((section, index) => {
    const at = header + index * 40;
    b.write(alias && index === 0 ? '/4' : section.name, at, 8, 'ascii');
    b.writeUInt32LE(section.data.length, at + 16); b.writeUInt32LE(position, at + 20);
    b.writeUInt32LE(section.flags ?? 0x200, at + 36);
    section.data.copy(b, position); position += section.data.length;
  });
  return b;
}
const section = (text, name = '.drectve', flags = 0x200) => ({ name, flags,
  data: Buffer.isBuffer(text) ? text : Buffer.from(text, 'utf8') });
const directive = (text, big = false, alias = false, symbols = 0) => coff([section(text)], big, alias, symbols);
function imported(nameType = 1) {
  const data = Buffer.from(`symbol\0library.dll\0${nameType === 4 ? 'exported\0' : ''}`, 'ascii');
  const b = Buffer.alloc(20 + data.length);
  b.writeUInt16LE(0xffff, 2); b.writeUInt16LE(0x8664, 6);
  b.writeUInt32LE(data.length, 12); b.writeUInt16LE(nameType << 2, 18); data.copy(b, 20);
  return b;
}
function archive(rows) {
  const parts = [Buffer.from('!<arch>\n')];
  for (const [name, body] of rows) {
    const header = name.padEnd(16) + '0'.padEnd(12) + ''.padEnd(6) + ''.padEnd(6)
      + '100644'.padEnd(8) + String(body.length).padEnd(10) + '`\n';
    parts.push(Buffer.from(header, 'ascii'), body);
    if (body.length % 2) parts.push(Buffer.from('\n'));
  }
  return Buffer.concat(parts);
}

test('S01', () => same(inspect(coff()), empty));
test('S02', () => same(inspect(coff([section('data', '.text', 0x40)])), empty));
test('S03', () => same(inspect(directive(' /DEFAULTLIB:MSVCRT /DEFAULTLIB:msvcrt.lib /INCLUDE:symbol /INCLUDE:symbol ')), {
  objects: 1, imports: 0, directives: ['/DEFAULTLIB:MSVCRT', '/DEFAULTLIB:msvcrt.lib', '/INCLUDE:symbol'],
  defaultLibraries: ['msvcrt.lib'] }));
test('S04', () => same(inspect(directive('-defaultlib:"Space Name.LIB" "/UNKNOWN:two words"')).defaultLibraries, ['space name.lib']));
test('S05', () => same(inspect(directive(Buffer.from([0xef, 0xbb, 0xbf, ...Buffer.from('/DEFAULTLIB:ucrt')]))).defaultLibraries, ['ucrt.lib']));
test('S06', () => same(inspect(directive('/DEFAULTLIB:OLDNAMES', true)).defaultLibraries, ['oldnames.lib']));
test('S07', () => same(inspect(directive('/DEFAULTLIB:alias', false, true, 1)).defaultLibraries, ['alias.lib']));
test('S08', () => same(inspect(directive('/DEFAULTLIB:bigalias', true, true, 1)).defaultLibraries, ['bigalias.lib']));
test('S09', () => same(inspect(imported()), { objects: 0, imports: 1, directives: [], defaultLibraries: [] }));
test('S10', () => inspect(imported(4)).imports === 1);
test('S11', () => same(inspect(archive([])), { ...empty, objects: 0 }));
test('S12', () => same(inspect(archive([['one.obj/', directive('/DEFAULTLIB:z')], ['two.obj/', imported()]])), {
  objects: 1, imports: 1, directives: ['/DEFAULTLIB:z'], defaultLibraries: ['z.lib'] }));
test('S13', () => inspect(archive([['/', Buffer.alloc(4)], ['/', Buffer.alloc(8)], ['//', Buffer.from('directory/long-object.obj\0')],
  ['/0', coff()], ['odd.obj/', directive(' ')]] )).objects === 2);
test('S14', () => same(inspect(directive('/X:one /X:one /X:two')).directives, ['/X:one', '/X:two']));
test('S15', () => same(inspect(directive('/X:"say \\"ok\\""')).directives, ['/X:say "ok"']));
test('S16', () => same(inspect(directive('/X:"a""b"')).directives, ['/X:a"b']));
test('S17', () => same(inspect(directive('')), empty));
test('S18', () => same(inspect(changed(coff([section('x', '.bss', 0x80)]), b => b.writeUInt32LE(0, 40))), empty));

test('R01', () => rejects(new Uint8Array(20)) && rejects(null));
test('R02', () => rejects(Buffer.alloc(19)));
// Mutated field controls: input, field offset, value, width (default DWORD).
const invalidFields = [
  ['R03', coff(), 0, 0x14c, 16], ['R04', coff(), 16, 1, 16],
  ['R05', coff(), 18, 2, 16], ['R06', coff(), 2, 1, 16],
  ['R07', directive('/X:y'), 40, 0xfffffff0], ['R08', directive('/X:y'), 36, 0xffffffff],
  ['R09', directive('/X:y'), 40, 20], ['R10', directive('/X:y'), 56, 0],
  ['R11', directive('/X:y'), 52, 1, 16], ['R12', directive('/X:y'), 54, 1, 16],
  ['R13', directive('/X:y'), 56, 0x01000200],
  ['R15', directive('/X:y', true), 4, 1, 16], ['R16', directive('/X:y', true), 36, 1],
  ['R17', coff([], true), 44, 65537],
  ['R18', directive('/X:y', false, true), 8, 0xffffffff],
  ['R19', directive('/X:y', true, true), 52, 0xffffffff],
  ['R22', coff([section('x'), section('y')]), 80, 100],
  ['R23', imported(), 6, 0x14c, 16], ['R24', imported(), 12, 1],
  ['R25', imported(), 18, 3, 16], ['R26', imported(), 18, 5 << 2, 16],
  ['R27', imported(), 18, 32, 16], ['R29', imported(), 18, 4 << 2, 16],
];
for (const [id, bytes, at, value, width = 32] of invalidFields) test(id, () => rejects(changed(bytes,
  b => width === 16 ? b.writeUInt16LE(value, at) : b.writeUInt32LE(value, at))));
test('R14', () => rejects(changed(directive('/X:y', true), b => b[12] ^= 1)));
test('R20', () => rejects(changed(directive('/X:y', false, true), b => b.write('/5', 20, 2, 'ascii'))));
test('R21', () => rejects(changed(directive('/X:y', false, true), b => b[b.length - 1] = 120)));
test('R28', () => rejects(changed(imported(), b => b[b.length - 1] = 120)));
test('R30', () => rejects(Buffer.concat([imported(), Buffer.from([0])])));

for (const [i, text] of [
  '/DEFAULTLIB:"unterminated', '/DEFAULTLIB:C:\\foo.lib', '/DEFAULTLIB:../foo.lib',
  '/DEFAULTLIB:.hidden.lib', '/DEFAULTLIB:foo..lib', '/DEFAULTLIB:foo.exe',
  '/DEFAULTLIB:', '/DEFAULTLIB', '/LIBPATH:somewhere', '-NoDefaultLib:msvcrt',
  '/X:y\n', '/X:y\t', '/X:y\0', '/X:\u00e9', 'unprefixed', '@response',
].entries()) test(`D${String(i + 1).padStart(2, '0')}`, () => rejects(directive(text)));
test('A01', () => rejects(Buffer.from('!<arch>\npartial')));
test('A02', () => rejects(changed(archive([['x/', coff()]]), b => b[66] = 0)));
test('A03', () => rejects(changed(archive([['x/', coff()]]), b => b.write('9999999999', 56, 10, 'ascii'))));
test('A04', () => rejects(changed(archive([['x/', directive(' ')]]), b => b[b.length - 1] = 32)));
test('A05', () => rejects(archive([['bad/', Buffer.from('unknown')]])));
test('A06', () => rejects(archive([['/SYM64/', Buffer.alloc(4)]])));
test('A07', () => rejects(archive([['//', Buffer.from('long.obj\0')], ['/1', coff()]])));
test('A08', () => rejects(archive([['/0', coff()]])));
test('A09', () => rejects(archive([['//', Buffer.from('long.obj/\n')], ['/0', coff()]])));
test('A10', () => rejects(archive([['//', Buffer.alloc(0)], ['//', Buffer.alloc(0)]])));
test('A11', () => rejects(archive([['/', Buffer.alloc(0)], ['/', Buffer.alloc(0)], ['/', Buffer.alloc(0)]])));
test('A12', () => rejects(changed(archive([['x/', coff()]]), b => b.write('268435456 ', 56, 10, 'ascii'))));
test('B01', () => inspect(directive(' '.repeat(1024 * 1024))).objects === 1);
test('B02', () => rejects(directive(' '.repeat(1024 * 1024 + 1))));
test('B03', () => rejects(archive([['x/', directive(' '.repeat(524288))], ['y/', directive(' '.repeat(524289))]])));
test('B04', () => rejects(directive('/X:y '.repeat(65537))));
test('B05', () => {
  const large = coff(Array.from({ length: 22000 }, () => section('', '.text', 0x40)));
  return rejects(archive([['a/', large], ['b/', large], ['c/', large]]));
});
test('B06', () => rejects(archive([['//', Buffer.from('a\0'.repeat(65537))]])));
test('B07', () => rejects(archive([['//', Buffer.from('a'.repeat(4097) + '\0')]])));
test('B08', () => inspect(archive([['//', Buffer.from('a'.repeat(4096) + '\0')]])).objects === 0);
test('A13', () => inspect(changed(archive([['x/', coff()]]), b => b.write('0000000020', 56, 10, 'ascii'))).objects === 1);

// Additive source-only diagnostic cases; the original85 predicates above stay intact.
function refusal(bytes, message, site, fields = {}) {
  const keys = ['memberIndex', 'memberOffset', 'sectionIndex', 'sections', 'directiveBytes', 'tokenCount', 'actual', 'limit'];
  let previous = null;
  for (let repeat = 0; repeat < 2; ++repeat) {
    let error;
    try { inspect(bytes); return false; } catch (caught) { error = caught; }
    if (!(error instanceof Error) || error.message !== message || error.site !== site ||
        !/^[a-z][a-z0-9_]{0,63}$/.test(error.site) || !error.context ||
        !same(Object.keys(error.context).sort(), [...keys].sort())) return false;
    if (Object.values(error.context).some(value => value !== null &&
        (!Number.isSafeInteger(value) || value < 0))) return false;
    for (const [key, value] of Object.entries(fields)) if (error.context[key] !== value) return false;
    if (previous && !same(previous, error.context)) return false;
    previous = error.context;
  }
  return true;
}
test('Z01', () => refusal(null, 'LibraryInputsType', 'input_type', {
  memberIndex: null, sections: null, tokenCount: null, actual: null, limit: null }));
test('Z02', () => refusal(Buffer.alloc(19), 'LibraryInputsFormat', 'coff_header_range', {
  memberIndex: null, sectionIndex: null, sections: 0, directiveBytes: 0, tokenCount: 0 }));
test('Z03', () => refusal(changed(coff(), b => b.writeUInt16LE(0x14c)), 'LibraryInputsFormat', 'coff_machine'));
test('Z04', () => refusal(changed(directive('/X:y', true), b => b[12] ^= 1), 'LibraryInputsFormat', 'bigobj_class_id'));
test('Z05', () => refusal(changed(imported(), b => b.writeUInt16LE(3, 18)), 'LibraryInputsFormat', 'import_type'));
test('Z06', () => refusal(changed(imported(), b => b.writeUInt32LE(1, 12)), 'LibraryInputsFormat', 'import_data_size'));
test('Z07', () => refusal(changed(imported(), b => b[b.length - 1] = 120), 'LibraryInputsFormat', 'import_name_end'));
test('Z08', () => refusal(changed(archive([['x/', coff()]]), b => b[66] = 0), 'LibraryInputsFormat', 'archive_header_end', {
  memberIndex: 0, memberOffset: 8, sectionIndex: null }));
test('Z09', () => refusal(archive([['//', Buffer.from('long.obj\0')], ['/1', coff()]]),
  'LibraryInputsFormat', 'archive_longname_reference', { memberIndex: 1 }));
test('Z10', () => refusal(archive([['//', Buffer.from('long.obj/\n')], ['/0', coff()]]),
  'LibraryInputsFormat', 'archive_longname_end', { memberIndex: 0, memberOffset: 8 }));
test('Z11', () => refusal(changed(directive('/X:y', false, true), b => b.write('/5', 20, 2, 'ascii')),
  'LibraryInputsFormat', 'section_alias_offset', { sectionIndex: 0 }));
test('Z12', () => refusal(archive([['x/', changed(directive('/X:y'), b => b.writeUInt32LE(0xfffffff0, 40))]]),
  'LibraryInputsFormat', 'coff_raw_range', { memberIndex: 0, memberOffset: 8, sectionIndex: 0, sections: 1 }));
test('Z13', () => refusal(changed(coff([], true), b => b.writeUInt32LE(65537, 44)),
  'LibraryInputsSize', 'coff_sections_member', { sections: 65537, sectionIndex: null, actual: 65537, limit: 65536 }));
test('Z14', () => {
  const large = coff(Array.from({ length: 22000 }, () => section('', '.text', 0x40)));
  return refusal(archive([['a/', large], ['b/', large], ['c/', large]]), 'LibraryInputsSize', 'coff_sections_total', {
    memberIndex: 2, sectionIndex: null, sections: 66000, actual: 66000, limit: 65536 });
});
test('Z15', () => refusal(directive(' '.repeat(1048577)), 'LibraryInputsSize', 'directive_bytes_section', {
  sectionIndex: 0, directiveBytes: 1048577, actual: 1048577, limit: 1048576 }));
test('Z16', () => refusal(archive([['a/', directive(' '.repeat(524288))], ['b/', directive(' '.repeat(524289))]]),
  'LibraryInputsSize', 'directive_bytes_total', { memberIndex: 1, directiveBytes: 1048577, actual: 1048577, limit: 1048576 }));
test('Z17', () => refusal(directive('/X:y '.repeat(65537)), 'LibraryInputsSize', 'directive_tokens_section', {
  sectionIndex: 0, tokenCount: 0, actual: 65537, limit: 65536 }));
test('Z18', () => refusal(archive([['a/', directive('/X:y '.repeat(32768))], ['b/', directive('/X:y '.repeat(32769))]]),
  'LibraryInputsSize', 'directive_tokens_total', { memberIndex: 1, tokenCount: 65537, actual: 65537, limit: 65536 }));
test('Z19', () => refusal(changed(archive([['x/', coff()]]), b => b.write('268435456 ', 56, 10, 'ascii')),
  'LibraryInputsSize', 'archive_member_bytes', { memberIndex: 0, memberOffset: 8, actual: 268435456, limit: 268435456 }));
test('Z20', () => refusal(archive([['//', Buffer.from('a\0'.repeat(65537))]]), 'LibraryInputsSize', 'archive_longname_entries', {
  memberIndex: 0, actual: 65536, limit: 65536 }));
test('Z21', () => refusal(archive([['//', Buffer.from('a'.repeat(4097) + '\0')]]), 'LibraryInputsFormat', 'archive_longname_end'));
test('Z22', () => refusal(directive('/DEFAULTLIB:C:\\synthetic.lib'), 'LibraryInputsUnsafe', 'defaultlib_name'));
test('Z23', () => refusal(directive('/DEFAULTLIB:"unterminated'), 'LibraryInputsDirective', 'directive_token'));
test('Z24', () => refusal(directive('/X:\u00e9'), 'LibraryInputsFormat', 'directive_encoding'));
test('Z25', () => refusal(changed(directive('/X:y'), b => b.fill(0, 20, 28)), 'LibraryInputsFormat', 'section_name_empty'));
test('Z26', () => refusal(changed(archive([['x/', coff()]]), b => b.write('99999999  ', 56, 10, 'ascii')),
  'LibraryInputsFormat', 'archive_body_range'));
test('Z27', () => refusal(Buffer.alloc(19), 'LibraryInputsFormat', 'coff_header_range', { sections: 0, tokenCount: 0 })
  && same(inspect(coff()), empty));

// Fixed summary and finite IDs only; no parsed directive or exception is printed.
console.log(JSON.stringify({ version: 1, kind: 'library_inputs_synthetic_v1', executed,
  passed, failed: executed - passed, failed_case_ids: failed }));
process.exitCode = failed.length ? 1 : 0;
