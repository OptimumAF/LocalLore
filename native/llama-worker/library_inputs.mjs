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
function fail(category = 'Format') { throw new Error(`LibraryInputs${category}`); }
function range(b, offset, size) {
  if (!Number.isSafeInteger(offset) || !Number.isSafeInteger(size) ||
      offset < 0 || size < 0 || offset > b.length || size > b.length - offset) fail();
}
function ascii(b) {
  for (const byte of b) if (byte < 32 || byte > 126) fail();
  return b.toString('ascii');
}
// Bound metadata names without scanning a whole member per reference.
function nameEnd(b, offset) {
  const end = b.subarray(offset, Math.min(b.length, offset + 4097)).indexOf(0);
  if (end <= 0) fail();
  return offset + end;
}
function decimal(text) {
  if (!/^[0-9]+$/.test(text)) fail();
  const value = Number(text);
  if (!Number.isSafeInteger(value)) fail();
  return value;
}
function libraryName(name) {
  if (!name || name.length > 255 || name !== name.trim() || name.startsWith('.') ||
      name.includes('..') || !/^[A-Za-z0-9_+ -]+(?:\.[A-Za-z0-9_+ -]+)*$/.test(name)) fail('Unsafe');
  const lower = name.toLowerCase();
  if (lower.includes('.') && !lower.endsWith('.lib')) fail('Unsafe');
  return lower.endsWith('.lib') ? lower : `${lower}.lib`;
}
function directiveTokens(bytes) {
  // Optional BOM, then ASCII only.
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) bytes = bytes.subarray(3);
  const text = ascii(bytes); // Reject all controls, including NUL, tab and newline.
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
    if (quoted || !/^[-/][A-Za-z][A-Za-z0-9_-]*(?::.*)?$/.test(token)) fail('Directive');
    result.push(token);
    if (result.length > MAX_ITEMS) fail('Size');
  }
  return result;
}
function importObject(b) {
  range(b, 0, 20);
  const bits = b.readUInt16LE(18), type = bits & 3, nameType = (bits >>> 2) & 7;
  if (b.readUInt16LE(4) !== 0 || b.readUInt16LE(6) !== 0x8664 ||
      type > 2 || nameType > 4 || (bits >>> 5) !== 0 || b.readUInt32LE(12) !== b.length - 20) fail();
  let offset = 20;
  for (let i = 0; i < (nameType === 4 ? 3 : 2); ++i) {
    const end = nameEnd(b, offset);
    ascii(b.subarray(offset, end));
    offset = end + 1;
  }
  if (offset !== b.length) fail();
}
function object(b, state) {
  if (b.length >= MAX_BYTES) fail('Size');
  range(b, 0, 20);
  let header = 20, count, symbolOffset, symbols, symbolSize = 18;
  if (b.readUInt16LE(0) === 0 && b.readUInt16LE(2) === 0xffff) {
    if (b.readUInt16LE(4) === 0) { importObject(b); ++state.imports; return; }
    range(b, 0, 56);
    if (b.readUInt16LE(4) < 2 || b.readUInt16LE(6) !== 0x8664 ||
        !b.subarray(12, 28).equals(BIGOBJ_ID) || b.readUInt32LE(28) !== 0 ||
        b.readUInt32LE(32) !== 0 || b.readUInt32LE(36) !== 0 || b.readUInt32LE(40) !== 0) fail();
    header = 56; symbolSize = 20;
    count = b.readUInt32LE(44); symbolOffset = b.readUInt32LE(48); symbols = b.readUInt32LE(52);
  } else {
    if (b.readUInt16LE(0) !== 0x8664 || b.readUInt16LE(16) !== 0 || (b.readUInt16LE(18) & 0x2002)) fail();
    count = b.readUInt16LE(2); symbolOffset = b.readUInt32LE(8); symbols = b.readUInt32LE(12);
  }
  state.sections += count;
  if (state.sections > MAX_ITEMS) fail('Size');
  const tableEnd = header + count * 40;
  range(b, header, count * 40);
  const intervals = [];
  function area(offset, size) {
    range(b, offset, size);
    if (offset < tableEnd) fail();
    if (size) intervals.push([offset, offset + size]);
  }
  let strings = null;
  if (!symbolOffset) { if (symbols) fail(); }
  else {
    const start = symbolOffset + symbols * symbolSize;
    range(b, start, 4);
    const length = b.readUInt32LE(start);
    if (length < 4) fail();
    area(symbolOffset, symbols * symbolSize + length);
    strings = b.subarray(start, start + length);
  }
  function sectionName(offset) {
    const raw = b.subarray(offset, offset + 8), nul = raw.indexOf(0);
    if (nul >= 0 && raw.subarray(nul).some(byte => byte !== 0)) fail();
    let name = ascii(nul < 0 ? raw : raw.subarray(0, nul));
    if (name.startsWith('/')) {
      const index = decimal(name.slice(1));
      if (!strings || index < 4 || index >= strings.length || (index > 4 && strings[index - 1] !== 0)) fail();
      const end = nameEnd(strings, index);
      name = ascii(strings.subarray(index, end));
    }
    if (!name) fail();
    return name;
  }
  for (let n = 0; n < count; ++n) {
    const at = header + n * 40, name = sectionName(at);
    const size = b.readUInt32LE(at + 16), pointer = b.readUInt32LE(at + 20);
    const reloc = b.readUInt32LE(at + 24), lines = b.readUInt32LE(at + 28);
    const relocCount = b.readUInt16LE(at + 32), lineCount = b.readUInt16LE(at + 34);
    const flags = b.readUInt32LE(at + 36);
    if (flags & 0x01000000) fail(); // Conservative: relocation-overflow encoding unsupported.
    if (pointer) area(pointer, size);
    else if (size && !(flags & 0x80)) fail(); // .bss has no file bytes.
    if (relocCount) area(reloc, relocCount * 10); else if (reloc) fail();
    if (lineCount) area(lines, lineCount * 6); else if (lines) fail();
    if (name === '.drectve') {
      if (!(flags & 0x200) || reloc || lines || relocCount || lineCount || (size && !pointer)) fail();
      state.directiveBytes += size;
      if (state.directiveBytes > MAX_DIRECTIVES) fail('Size');
      for (const token of directiveTokens(b.subarray(pointer, pointer + size))) {
        const colon = token.indexOf(':'), option = (colon < 0 ? token.slice(1) : token.slice(1, colon)).toLowerCase();
        if (option === 'libpath' || option === 'nodefaultlib') fail('Unsafe');
        if (option === 'defaultlib') {
          if (colon < 0) fail('Directive');
          state.defaultLibraries.add(libraryName(token.slice(colon + 1)));
        }
        state.directives.add(token);
        if (++state.tokenCount > MAX_ITEMS) fail('Size');
      }
    }
  }
  intervals.sort((a, c) => a[0] - c[0]);
  for (let i = 1; i < intervals.length; ++i) if (intervals[i][0] < intervals[i - 1][1]) fail();
  ++state.objects;
}
function archive(b, state) {
  let at = 8, longnames = null, indexes = 0;
  const members = [];
  while (at < b.length) {
    if (members.length >= MAX_ITEMS) fail('Size');
    range(b, at, 60);
    const h = b.subarray(at, at + 60);
    if (h[58] !== 0x60 || h[59] !== 10) fail();
    ascii(h.subarray(0, 58));
    const name = h.subarray(0, 16).toString('ascii').trimEnd();
    const sizeText = h.subarray(48, 58).toString('ascii').trimEnd();
    const size = decimal(sizeText);
    if (size >= MAX_BYTES) fail('Size');
    range(b, at + 60, size);
    const body = b.subarray(at + 60, at + 60 + size);
    members.push({ name, body });
    if (name === '//') { if (longnames) fail(); longnames = body; }
    if (name === '/' && ++indexes > 2) fail();
    at += 60 + size;
    if (at % 2) { range(b, at, 1); if (b[at++] !== 10) fail(); }
  }
  const names = new Map();
  if (longnames) {
    for (let p = 0; p < longnames.length;) {
      if (names.size >= MAX_ITEMS) fail('Size');
      const end = nameEnd(longnames, p);
      names.set(p, ascii(longnames.subarray(p, end)));
      p = end + 1;
    }
  }
  for (const { name, body } of members) {
    // Index payloads are envelope-checked, not interpreted as symbol authority.
    if (name === '/' || name === '//') continue;
    if (name.startsWith('/')) {
      if (!names.has(decimal(name.slice(1)))) fail();
    } else if (!name.endsWith('/') || name.length < 2) fail();
    object(body, state); // Unknown members are never silently skipped.
  }
}
export function inspectLibraryInputs(buffer) {
  if (!Buffer.isBuffer(buffer)) fail('Type');
  if (buffer.length >= MAX_BYTES) fail('Size');
  const state = { objects: 0, imports: 0, sections: 0, directiveBytes: 0, tokenCount: 0,
    directives: new Set(), defaultLibraries: new Set() };
  if (buffer.length >= 8 && buffer.subarray(0, 8).equals(MAGIC)) archive(buffer, state);
  else object(buffer, state);
  return { objects: state.objects, imports: state.imports,
    directives: [...state.directives].sort(), defaultLibraries: [...state.defaultLibraries].sort() };
}
