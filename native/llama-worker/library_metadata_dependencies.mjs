// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development metadata projection only. No binary parser, resolver or authority.
import { createHash } from 'node:crypto';
import { MSVC_LIBRARY_METADATA_PROFILE } from './library_inputs.mjs';

const INVALID = 'LibraryMetadataDependencyFactsInvalid';
const ID = 'msvc-library-metadata-v1';
const ROW_BYTES = 1048576, TOTAL_BYTES = 8388608;
const digest = text => createHash('sha256').update(text).digest('hex');
const uint = (value, maximum) => Number.isSafeInteger(value) && value >= 0 && value <= maximum;
const hex = value => typeof value === 'string' && /^[a-f0-9]{64}$/.test(value);
const requireThat = value => { if (!value) throw Error(INVALID); };
function keys(value, names) {
  return value !== null && typeof value === 'object' && !Array.isArray(value) &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value)) &&
    Object.keys(value).sort().join(',') === [...names].sort().join(',');
}
function canonicalName(value) {
  return typeof value === 'string' && value.length > 0 && value.length <= 259 &&
    value === value.trim() && !value.startsWith('.') && !value.includes('..') &&
    value.endsWith('.lib') && /^[a-z0-9_+ -]+(?:\.[a-z0-9_+ -]+)*$/.test(value);
}
function freeze(value) {
  if (value && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}
function validateResult(value, pin, aggregate) {
  requireThat(keys(value, ['profileId', 'purpose', 'qualified', 'linkQualification',
    'closureComplete', 'metadata', 'sections', 'deviations']));
  requireThat(value.profileId === ID && value.purpose === 'build_input_metadata_only' &&
    value.qualified === false && value.linkQualification === false &&
    value.closureComplete === false && uint(value.sections, 262144));
  const m = value.metadata, d = value.deviations;
  requireThat(keys(m, ['objects', 'imports', 'directives', 'defaultLibraries']) &&
    uint(m.objects, 65536) && uint(m.imports, 65536) && m.objects + m.imports <= 65536);
  requireThat(keys(d, ['unknownMachineObjects', 'unusedRelocationPointers', 'terminalNulSections']) &&
    uint(d.unknownMachineObjects, 65536) && uint(d.unusedRelocationPointers, 262144) &&
    uint(d.terminalNulSections, 262144));
  requireThat(Array.isArray(m.directives) && m.directives.length <= 65536 &&
    Array.isArray(m.defaultLibraries) && m.defaultLibraries.length <= 32 &&
    m.defaultLibraries.length === pin.libraryCount);

  // Count bounded strings before constructing/hash-processing the whole object.
  // These extra projection limits never change accepted helper/job semantics.
  let stringBytes = 0;
  for (const [values, names] of [[m.directives, false], [m.defaultLibraries, true]]) {
    let previous;
    for (const text of values) {
      requireThat(typeof text === 'string' && (previous === undefined || previous < text));
      if (names) requireThat(canonicalName(text));
      else requireThat(text.length <= 65536 && /^[\x20-\x7e]*$/.test(text));
      stringBytes += Buffer.byteLength(JSON.stringify(text));
      requireThat(stringBytes <= ROW_BYTES && aggregate.bytes + stringBytes <= TOTAL_BYTES);
      previous = text;
    }
  }
  const serialized = JSON.stringify(m);
  const bytes = Buffer.byteLength(serialized);
  requireThat(bytes <= ROW_BYTES && aggregate.bytes + bytes <= TOTAL_BYTES);
  requireThat(digest(serialized) === pin.metadataSha256);
  aggregate.bytes += bytes;
  return m.defaultLibraries;
}

export function projectLibraryMetadataDependenciesV1(pins, observations, catalog) {
  try {
    const descriptor = MSVC_LIBRARY_METADATA_PROFILE;
    requireThat(descriptor.id === ID && descriptor.version === 1 &&
      descriptor.purpose === 'build_input_metadata_only' && Object.isFrozen(descriptor) &&
      Object.isFrozen(descriptor.limits));
    requireThat(Array.isArray(pins) && pins.length === 32 &&
      Array.isArray(observations) && observations.length === 32 &&
      Array.isArray(catalog) && catalog.length === 15);
    const available = new Map();
    for (let i = 0; i < 15; i++) {
      const row = catalog[i];
      requireThat(keys(row, ['slot', 'name']) && row.slot === i + 18 &&
        canonicalName(row.name) && !available.has(row.name));
      available.set(row.name, row.slot);
    }
    const aggregate = { bytes: 0 }, names = new Set(), perRow = [];
    for (let i = 0; i < 32; i++) {
      const pin = pins[i], observation = observations[i];
      requireThat(keys(pin, ['slot', 'metadataSha256', 'libraryCount']) &&
        pin.slot === i + 1 && hex(pin.metadataSha256) && uint(pin.libraryCount, 32));
      requireThat(keys(observation, ['slot', 'result']) && observation.slot === i + 1);
      const libraries = validateResult(observation.result, pin, aggregate);
      const copy = [...libraries];
      for (const name of copy) { names.add(name); requireThat(names.size <= 32); }
      perRow.push(copy);
    }
    const libraryNames = [...names].sort();
    const indices = new Map(libraryNames.map((name, i) => [name, i]));
    const providedSlots = libraryNames.map(name => available.get(name) ?? null);
    const unresolvedNameIds = providedSlots.flatMap((slot, i) => slot === null ? [i] : []);
    const rows = perRow.map((libraries, i) => ({ slot: i + 1,
      libraryIds: libraries.map(name => indices.get(name)) }));
    const report = { version: 1, kind: 'msvc_library_dependency_facts_v1', profileId: ID,
      purpose: 'build_input_metadata_only', qualified: false, linkQualification: false,
      closureComplete: false, captureComplete: true, status: 'metadata_facts_complete',
      pinsSha256: digest(JSON.stringify(pins)), catalogSha256: digest(JSON.stringify(catalog)),
      libraryNames, providedSlots, rows, unresolvedNameIds,
      allReferencesInProvidedCatalog: unresolvedNameIds.length === 0 };
    requireThat(rows.every(row => Buffer.byteLength(JSON.stringify(row)) <= 128));
    requireThat(Buffer.byteLength(JSON.stringify({ ...report, rows: [], libraryNames: [] })) <= 2048);
    requireThat(Buffer.byteLength(JSON.stringify(report) + '\n') <= 16384);
    return freeze(report);
  } catch {
    throw Error(INVALID);
  }
}
