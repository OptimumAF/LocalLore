// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Buffer-only, conservative ALL-member metadata; never the selected link closure.
// Layouts: Microsoft PE/COFF; SDK10.0.19041 winnt.h BIGOBJ/SYMBOL_EX/IMPORT.
// https://learn.microsoft.com/en-us/windows/win32/debug/pe-format
// No PE images, anonymous CLR/LTCG objects, relocation overflow or GNU archives.
const MAX_BYTES = 256 * 1024 * 1024;
const MAX_ITEMS = 65536;
const MAX_DIRECTIVES = 1024 * 1024;
const BIGOBJ_ID = Buffer.from('c7a1bad1eebaa94baf20faf66aa4dcb8', 'hex');
const MAGIC = Buffer.from('!<arch>\n');
function fail(site, category = 'Format', actual = null, limit = null) {
  const safe = value => Number.isSafeInteger(value) && value >= 0 ? value : null;
  const error = new Error(`LibraryInputs${category}`);
  error.site = site; // Fixed source ID only; no byte-derived text.
  // Zero-based indexes; memberOffset is its archive HEADER offset, not a path.
  error.context = { memberIndex: null, memberOffset: null, sectionIndex: null,
    sections: null, directiveBytes: null, tokenCount: null, actual: safe(actual), limit: safe(limit) };
  throw error;
}
function range(b, offset, size, site) {
  if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(size) ||
      offset < 0 || size < 0 || offset > b.length || size > b.length - offset) fail(site);
}
function ascii(b, site) {
  for (const byte of b) if (byte < 32 || byte > 126) fail(site);
  return b.toString('ascii');
}
// Bound metadata names without scanning a whole member per reference.
function nameEnd(b, offset, site) {
  const end = b.subarray(offset, Math.min(b.length, offset + 4097)).indexOf(0);
  if (end <= 0) fail(site);
  return offset + end;
}
function decimal(text, site) {
  if (!/^[0-9]+$/.test(text)) fail(site);
  const value = Number(text);
  if (!Number.isSafeInteger(value)) fail(site);
  return value;
}
function libraryName(name) {
  if (!name || name.length > 255 || name !== name.trim() || name.startsWith('.') ||
      name.includes('..') || !/^[A-Za-z0-9_+ -]+(?:\.[A-Za-z0-9_+ -]+)*$/.test(name)) fail('defaultlib_name', 'Unsafe');
  const lower = name.toLowerCase();
  if (lower.includes('.') && !lower.endsWith('.lib')) fail('defaultlib_extension', 'Unsafe');
  return lower.endsWith('.lib') ? lower : `${lower}.lib`;
}
function directiveTokens(bytes) {
  // Optional BOM, then ASCII only.
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) bytes = bytes.subarray(3);
  const text = ascii(bytes, 'directive_encoding'); // Reject controls, including NUL/tab/newline.
  const result = [];
  let i = 0;
  while (i < text.length) {
    if (text[i] === ' ') { ++i; continue; }
    let token = '', quoted = false;
    while (i < text.length && (quoted || text[i] !== ' ')) {
      if (text[i] === '\\') {
        const start = i;
        while (text[i] === '\\') ++i;
        const count = i - start;
        if (text[i] !== '"') { token += '\\'.repeat(count); continue; }
        token += '\\'.repeat(Math.floor(count / 2));
        if (count % 2) { token += '"'; ++i; continue; }
      }
      if (text[i] === '"') {
        if (quoted && text[i + 1] === '"') { token += '"'; i += 2; }
        else { quoted = !quoted; ++i; }
      } else { token += text[i++]; }
    }
    if (quoted || !/^[-/][A-Za-z][A-Za-z0-9_-]*(?::.*)?$/.test(token)) fail('directive_token', 'Directive');
    result.push(token);
    if (result.length > MAX_ITEMS) fail('directive_tokens_section', 'Size', result.length, MAX_ITEMS);
  }
  return result;
}
function importObject(b) {
  range(b, 0, 20, 'import_header_range');
  const bits = b.readUInt16LE(18), type = bits & 3, nameType = (bits >>> 2) & 7;
  if (b.readUInt16LE(4) !== 0) fail('import_version');
  if (b.readUInt16LE(6) !== 0x8664) fail('import_machine');
  if (type > 2) fail('import_type');
  if (nameType > 4) fail('import_name_type');
  if ((bits >>> 5) !== 0) fail('import_reserved');
  if (b.readUInt32LE(12) !== b.length - 20) fail('import_data_size');
  let offset = 20;
  for (let i = 0; i < (nameType === 4 ? 3 : 2); ++i) {
    const end = nameEnd(b, offset, 'import_name_end');
    ascii(b.subarray(offset, end), 'import_name_encoding');
    offset = end + 1;
  }
  if (offset !== b.length) fail('import_trailing_data');
}
function object(b, state) {
  state.sectionIndex = null;
  if (b.length >= MAX_BYTES) fail('object_bytes', 'Size', b.length, MAX_BYTES);
  range(b, 0, 20, 'coff_header_range');
  let header = 20, count, symbolOffset, symbols, symbolSize = 18;
  if (b.readUInt16LE(0) === 0 && b.readUInt16LE(2) === 0xffff) {
    if (b.readUInt16LE(4) === 0) { importObject(b); ++state.imports; return; }
    range(b, 0, 56, 'bigobj_header_range');
    if (b.readUInt16LE(4) < 2) fail('bigobj_version');
    if (b.readUInt16LE(6) !== 0x8664) fail('bigobj_machine');
    if (!b.subarray(12, 28).equals(BIGOBJ_ID)) fail('bigobj_class_id');
    if (b.readUInt32LE(28) !== 0 || b.readUInt32LE(32) !== 0 ||
        b.readUInt32LE(36) !== 0 || b.readUInt32LE(40) !== 0) fail('bigobj_metadata');
    header = 56; symbolSize = 20;
    count = b.readUInt32LE(44); symbolOffset = b.readUInt32LE(48); symbols = b.readUInt32LE(52);
  } else {
    if (b.readUInt16LE(0) !== 0x8664) fail('coff_machine');
    if (b.readUInt16LE(16) !== 0) fail('coff_optional_header');
    if (b.readUInt16LE(18) & 0x2002) fail('coff_image_flags');
    count = b.readUInt16LE(2); symbolOffset = b.readUInt32LE(8); symbols = b.readUInt32LE(12);
  }
  state.sections += count;
  if (state.sections > MAX_ITEMS) fail(count > MAX_ITEMS ? 'coff_sections_member' : 'coff_sections_total',
    'Size', count > MAX_ITEMS ? count : state.sections, MAX_ITEMS);
  const tableEnd = header + count * 40;
  range(b, header, count * 40, 'coff_section_table_range');
  const intervals = [];
  function area(offset, size, site) {
    range(b, offset, size, site);
    if (offset < tableEnd) fail('coff_area_before_headers');
    if (size) intervals.push([offset, offset + size]);
  }
  let strings = null;
  if (!symbolOffset) { if (symbols) fail('coff_symbol_pointer'); }
  else {
    const start = symbolOffset + symbols * symbolSize;
    range(b, start, 4, 'coff_string_table_header');
    const length = b.readUInt32LE(start);
    if (length < 4) fail('coff_string_table_size');
    area(symbolOffset, symbols * symbolSize + length, 'coff_symbol_string_range');
    strings = b.subarray(start, start + length);
  }
  function sectionName(offset) {
    const raw = b.subarray(offset, offset + 8), nul = raw.indexOf(0);
    if (nul >= 0 && raw.subarray(nul).some(byte => byte !== 0)) fail('section_name_padding');
    let name = ascii(nul < 0 ? raw : raw.subarray(0, nul), 'section_name_encoding');
    if (name.startsWith('/')) {
      const index = decimal(name.slice(1), 'section_alias_decimal');
      if (!strings || index < 4 || index >= strings.length || (index > 4 && strings[index - 1] !== 0)) fail('section_alias_offset');
      const end = nameEnd(strings, index, 'section_alias_end');
      name = ascii(strings.subarray(index, end), 'section_alias_encoding');
    }
    if (!name) fail('section_name_empty');
    return name;
  }
  for (let n = 0; n < count; ++n) {
    state.sectionIndex = n;
    const at = header + n * 40, name = sectionName(at);
    const size = b.readUInt32LE(at + 16), pointer = b.readUInt32LE(at + 20);
    const reloc = b.readUInt32LE(at + 24), lines = b.readUInt32LE(at + 28);
    const relocCount = b.readUInt16LE(at + 32), lineCount = b.readUInt16LE(at + 34);
    const flags = b.readUInt32LE(at + 36);
    if (flags & 0x01000000) fail('coff_relocation_overflow'); // Still unsupported.
    if (pointer) area(pointer, size, 'coff_raw_range');
    else if (size && !(flags & 0x80)) fail('coff_raw_pointer'); // .bss has no file bytes.
    if (relocCount) area(reloc, relocCount * 10, 'coff_relocation_range'); else if (reloc) fail('coff_relocation_pointer');
    if (lineCount) area(lines, lineCount * 6, 'coff_line_range'); else if (lines) fail('coff_line_pointer');
    if (name === '.drectve') {
      if (!(flags & 0x200) || reloc || lines || relocCount || lineCount || (size && !pointer)) fail('directive_section');
      state.directiveBytes += size;
      if (state.directiveBytes > MAX_DIRECTIVES) fail(size > MAX_DIRECTIVES ? 'directive_bytes_section' : 'directive_bytes_total',
        'Size', size > MAX_DIRECTIVES ? size : state.directiveBytes, MAX_DIRECTIVES);
      for (const token of directiveTokens(b.subarray(pointer, pointer + size))) {
        const colon = token.indexOf(':'), option = (colon < 0 ? token.slice(1) : token.slice(1, colon)).toLowerCase();
        if (option === 'libpath' || option === 'nodefaultlib') fail('directive_library_policy', 'Unsafe');
        if (option === 'defaultlib') {
          if (colon < 0) fail('defaultlib_attribute', 'Directive');
          state.defaultLibraries.add(libraryName(token.slice(colon + 1)));
        }
        state.directives.add(token);
        if (++state.tokenCount > MAX_ITEMS) fail('directive_tokens_total', 'Size', state.tokenCount, MAX_ITEMS);
      }
    }
  }
  intervals.sort((a, c) => a[0] - c[0]);
  for (let i = 1; i < intervals.length; ++i) if (intervals[i][0] < intervals[i - 1][1]) fail('coff_areas_overlap');
  ++state.objects;
}
function archive(b, state) {
  let at = 8, longnames = null, longnameLocation = null, indexes = 0;
  const members = [];
  while (at < b.length) {
    state.memberIndex = members.length; state.memberOffset = at; state.sectionIndex = null;
    if (members.length >= MAX_ITEMS) fail('archive_members', 'Size', members.length, MAX_ITEMS);
    range(b, at, 60, 'archive_header_range');
    const h = b.subarray(at, at + 60);
    if (h[58] !== 0x60 || h[59] !== 10) fail('archive_header_end');
    ascii(h.subarray(0, 58), 'archive_header_encoding');
    const name = h.subarray(0, 16).toString('ascii').trimEnd();
    const sizeText = h.subarray(48, 58).toString('ascii').trimEnd();
    const size = decimal(sizeText, 'archive_member_size_decimal');
    if (size >= MAX_BYTES) fail('archive_member_bytes', 'Size', size, MAX_BYTES);
    range(b, at + 60, size, 'archive_body_range');
    const body = b.subarray(at + 60, at + 60 + size);
    members.push({ name, body, index: members.length, offset: at });
    if (name === '//') {
      if (longnames) fail('archive_longname_duplicate');
      longnames = body; longnameLocation = { index: members.length - 1, offset: at };
    }
    if (name === '/' && ++indexes > 2) fail('archive_index_count');
    at += 60 + size;
    if (at % 2) { range(b, at, 1, 'archive_padding_range'); if (b[at++] !== 10) fail('archive_padding_byte'); }
  }
  const names = new Map();
  if (longnames) {
    state.memberIndex = longnameLocation.index; state.memberOffset = longnameLocation.offset;
    for (let p = 0; p < longnames.length;) {
      if (names.size >= MAX_ITEMS) fail('archive_longname_entries', 'Size', names.size, MAX_ITEMS);
      const end = nameEnd(longnames, p, 'archive_longname_end');
      names.set(p, ascii(longnames.subarray(p, end), 'archive_longname_encoding'));
      p = end + 1;
    }
  }
  for (const { name, body, index, offset } of members) {
    state.memberIndex = index; state.memberOffset = offset; state.sectionIndex = null;
    // Index payloads are envelope-checked, not interpreted as symbol authority.
    if (name === '/' || name === '//') continue;
    if (name.startsWith('/')) {
      if (!names.has(decimal(name.slice(1), 'archive_name_decimal'))) fail('archive_longname_reference');
    } else if (!name.endsWith('/') || name.length < 2) fail('archive_member_name');
    object(body, state); // Unknown members are never silently skipped.
  }
}
export function inspectLibraryInputs(buffer) {
  if (!Buffer.isBuffer(buffer)) fail('input_type', 'Type');
  if (buffer.length >= MAX_BYTES) fail('input_bytes', 'Size', buffer.length, MAX_BYTES);
  const state = { objects: 0, imports: 0, sections: 0, directiveBytes: 0, tokenCount: 0,
    directives: new Set(), defaultLibraries: new Set(), memberIndex: null, memberOffset: null, sectionIndex: null };
  try {
    if (buffer.length >= 8 && buffer.subarray(0, 8).equals(MAGIC)) archive(buffer, state);
    else object(buffer, state);
  } catch (error) {
    if (error instanceof Error && error.context && typeof error.site === 'string') {
      for (const key of ['memberIndex', 'memberOffset', 'sectionIndex', 'sections', 'directiveBytes', 'tokenCount']) {
        error.context[key] = state[key];
      }
    }
    throw error;
  }
  return { objects: state.objects, imports: state.imports,
    directives: [...state.directives].sort(), defaultLibraries: [...state.defaultLibraries].sort() };
}
