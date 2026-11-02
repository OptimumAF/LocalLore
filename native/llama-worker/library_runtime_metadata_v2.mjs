// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only, fixed-two metadata session. No filesystem/process API.
// Acquisition and binary interpretation belong to the unchanged accepted APIs.
import { createHash } from 'node:crypto';
import { createLibraryMetadataJobV2, MSVC_LIBRARY_METADATA_PROFILE_V2 } from './library_inputs.mjs';
import { readPinnedArchiveV1 } from './library_padding_observation.mjs';

const ID = 'msvc-library-metadata-v2';
const PROOFS = ['module', 'parser', 'heldReader', 'collector', 'first', 'supervisor',
  'runtimeSnapshot', 'runtimeRootReview', 'paddingSnapshot', 'paddingRootReview', 'descriptor'];
const CONTEXT = ['memberIndex', 'memberOffset', 'sectionIndex', 'sections',
  'directiveBytes', 'tokenCount', 'actual', 'limit'];
const DEVIATIONS = ['unknownMachineObjects', 'unusedRelocationPointers', 'terminalNulSections'];
const IO = ['reservedInputs', 'reservedBytes', 'reservedReadBytes', 'actualReadBytes',
  'opened', 'closed', 'verifiedPasses'];
const CATEGORIES = ['Format', 'Unsafe', 'Directive', 'Size', 'Type', 'Profile'].map(x => 'LibraryInputs' + x);
const READ_ERRORS = ['PaddingPin', 'PaddingType', 'PaddingIdentity', 'PaddingRead',
  'PaddingHash', 'PaddingStopped', 'PaddingClose'];
const MAX = [285588, 38478], NAMES = ['ucrt.lib', 'vcruntime.lib'], ROOTS = [3, 1];
const uint = (v, max = Number.MAX_SAFE_INTEGER) => Number.isSafeInteger(v) && v >= 0 && v <= max;
const hex = v => typeof v === 'string' && v.length === 64 && !/[^0-9a-f]/.test(v);
const token = v => typeof v === 'string' && v.length > 0 && v.length <= 256 && !/[^A-Za-z0-9_.:-]/.test(v);
const hash = b => createHash('sha256').update(b).digest('hex');
const size = v => Buffer.byteLength(JSON.stringify(v));
function requireThat(ok, code) { if (!ok) throw Error(code); }
function record(value, keys, code) {
  try {
    requireThat(value !== null && typeof value === 'object' &&
      [Object.prototype, null].includes(Object.getPrototypeOf(value)), code);
    const own = Reflect.ownKeys(value);
    requireThat(own.length === keys.length && own.every(k => typeof k === 'string' && keys.includes(k)), code);
    const out = {};
    for (const key of keys) {
      const d = Object.getOwnPropertyDescriptor(value, key);
      requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code);
      out[key] = d.value;
    }
    return out;
  } catch { throw Error(code); }
}
function freeze(v) {
  if (v !== null && typeof v === 'object') { Object.values(v).forEach(freeze); Object.freeze(v); }
  return v;
}
function copy(v) { return JSON.parse(JSON.stringify(v)); }
function pinData(value, index) {
  const p = record(value, ['bytes', 'sha256', 'rootIdentity', 'leafIdentity'], 'RuntimeMetadataV2Pin');
  requireThat(uint(p.bytes, MAX[index]) && p.bytes > 0 && hex(p.sha256) &&
    token(p.rootIdentity) && token(p.leafIdentity), 'RuntimeMetadataV2Pin');
  return p;
}
function readIO(value, bytes) {
  const io = record(value, IO, 'RuntimeMetadataV2Inspect');
  for (const k of IO.filter(x => x !== 'opened' && x !== 'closed')) {
    requireThat(uint(io[k]), 'RuntimeMetadataV2Inspect');
  }
  requireThat(typeof io.opened === 'boolean' && typeof io.closed === 'boolean' &&
    io.reservedInputs <= 1 && io.verifiedPasses <= 2, 'RuntimeMetadataV2Inspect');
  if (io.reservedInputs === 0) {
    requireThat(io.reservedBytes === 0 && io.reservedReadBytes === 0 && io.actualReadBytes === 0 &&
      io.verifiedPasses === 0 && !io.opened && !io.closed, 'RuntimeMetadataV2Inspect');
  } else {
    requireThat(io.reservedBytes === bytes && io.reservedReadBytes === 2 * bytes &&
      io.actualReadBytes <= 2 * bytes && io.actualReadBytes >= io.verifiedPasses * bytes &&
      (!io.closed || io.opened) && (io.opened ||
        (io.actualReadBytes === 0 && io.verifiedPasses === 0 && !io.closed)), 'RuntimeMetadataV2Inspect');
  }
  return io;
}
function refusal(error) {
  // Only fixed source fields from the directly invoked accepted parser survive.
  // Never emit Error.message outside this closed six-category vocabulary.
  if (!(error instanceof Error) || !CATEGORIES.includes(error.message) ||
      typeof error.site !== 'string' || error.site.length < 1 || error.site.length > 64 ||
      /[^a-z0-9_]/.test(error.site) || !/^[a-z]/.test(error.site)) return null;
  let context;
  try { context = record(error.context, CONTEXT, 'RuntimeMetadataV2Inspect'); } catch { return null; }
  if (!CONTEXT.every(k => context[k] === null || uint(context[k]))) return null;
  return { kind: error.message, site: error.site, context };
}
function dense(value, code) {
  requireThat(Array.isArray(value), code);
  const keys = Reflect.ownKeys(value);
  requireThat(keys.length === value.length + 1 && keys.includes('length'), code);
  return Array.from({ length: value.length }, (_, i) => {
    const d = Object.getOwnPropertyDescriptor(value, String(i));
    requireThat(d !== undefined && d.enumerable && Object.hasOwn(d, 'value'), code);
    return d.value;
  });
}
function parsedSummary(result, mode) {
  const code = 'RuntimeMetadataV2Inspect', limits = MSVC_LIBRARY_METADATA_PROFILE_V2.limits;
  const r = record(result, ['profileId', 'purpose', 'qualified', 'linkQualification',
    'closureComplete', 'metadata', 'sections', 'deviations'], code);
  requireThat(r.profileId === mode && r.purpose === 'build_input_metadata_only' &&
    r.qualified === false && r.linkQualification === false && r.closureComplete === false &&
    uint(r.sections, limits.inputSections), code);
  const m = record(r.metadata, ['objects', 'imports', 'directives', 'defaultLibraries'], code);
  requireThat(uint(m.objects, limits.members) && uint(m.imports, limits.members) &&
    m.objects + m.imports <= limits.members, code);
  const ds = [...DEVIATIONS, ...(mode === ID ? ['nulArchivePaddingMembers'] : [])];
  const d = record(r.deviations, ds, code);
  for (const k of ds) requireThat(uint(d[k], k === 'unknownMachineObjects' ||
    k === 'nulArchivePaddingMembers' ? limits.members : limits.inputSections), code);
  const directives = dense(m.directives, code), libraries = dense(m.defaultLibraries, code);
  requireThat(directives.length <= limits.tokens, code);
  let previous;
  for (const text of directives) {
    requireThat(typeof text === 'string' && text.length <= limits.directiveBytes && !/[^\x20-\x7e]/.test(text) &&
      (previous === undefined || previous < text), code); previous = text;
  }
  requireThat(libraries.length <= 32, 'RuntimeMetadataV2ReportLimit');
  previous = undefined;
  for (const name of libraries) {
    requireThat(typeof name === 'string' && name.length > 0 && name.length <= 259 &&
      name === name.trim() && !name.startsWith('.') && !name.includes('..') && name.endsWith('.lib') &&
      /^[a-z0-9_+ -]+(?:\.[a-z0-9_+ -]+)*$/.test(name) &&
      (previous === undefined || previous < name), code); previous = name;
  }
  // Same metadata order/values as the accepted parser; raw directives stay local.
  return { profileId: mode, objects: m.objects, imports: m.imports, sections: r.sections,
    deviations: d, metadataSha256: hash(Buffer.from(JSON.stringify({ objects: m.objects,
      imports: m.imports, directives, defaultLibraries: libraries }))), defaultLibraries: libraries };
}

export function createRuntimeMetadataObservationV2(proofs) {
  const proof = record(proofs, PROOFS, 'RuntimeMetadataV2Setup');
  requireThat(PROOFS.every(k => hex(proof[k])), 'RuntimeMetadataV2Setup');
  const job = createLibraryMetadataJobV2(ID);
  const rows = NAMES.map((name, i) => ({ slot: 33 + i, name, rootIndex: ROOTS[i],
    status: 'unstarted', pin: null, io: null, strict: null, profile: null }));
  let next = 0, pending = false, critical = null, summaryBytes = 0;
  const stop = code => { critical ??= code; return Error(critical); };
  const wireReport = () => {
    const io = { reservedInputs: 0, reservedBytes: 0, reservedReadBytes: 0, actualReadBytes: 0 };
    for (const row of rows) if (row.io !== null) for (const k of Object.keys(io)) io[k] += row.io[k];
    const complete = critical === null && !pending && next === 2 && rows.every(r => r.status === 'complete');
    return { version: 2, kind: 'fixed_two_runtime_metadata_v2', purpose: 'build_input_metadata_only',
      qualified: false, linkQualification: false, closureComplete: false, captureComplete: complete,
      status: critical !== null ? 'stopped' : pending ? 'pending' : complete ? 'complete' : 'incomplete',
      proofs: proof, job: job.snapshot(), io, rows, critical };
  };
  const snapshot = () => {
    let value = wireReport();
    if (size(value) > 24576) { stop('RuntimeMetadataV2ReportLimit'); value = wireReport(); }
    // Summary admission leaves8192B for this finite fixed control envelope.
    requireThat(size(value) <= 24576, 'RuntimeMetadataV2ReportLimit');
    return freeze(copy(value));
  };
  async function observe(index, pin, adapter) {
    if (critical !== null) throw Error(critical);
    if (!Number.isInteger(index) || index !== next || index < 0 || index > 1 || pending) {
      throw stop('RuntimeMetadataV2Sequence');
    }
    const row = rows[index];
    try { row.pin = pinData(pin, index); }
    catch { row.status = 'failed'; throw stop('RuntimeMetadataV2Pin'); }
    row.status = 'reading'; pending = true;
    try {
      let read;
      try { read = await readPinnedArchiveV1(row.pin, adapter); row.io = readIO(read.io, row.pin.bytes); }
      catch (error) {
        if (error?.name === 'PaddingObservationError' && READ_ERRORS.includes(error.code) && error.io !== null) {
          row.io = readIO(error.io, row.pin.bytes); throw stop(error.code);
        }
        throw stop('RuntimeMetadataV2Inspect');
      }
      // A concurrent sequence refusal cannot cancel accounting or reader cleanup.
      if (critical !== null) throw Error(critical);
      for (const [key, mode] of [['strict', 'strict-v1'], ['profile', ID]]) {
        row[key] = { status: 'failed', summary: null, error: null };
        if (hash(read.buffer) !== row.pin.sha256) throw stop('RuntimeMetadataV2Hash');
        let result, error;
        try { result = job.inspect(read.buffer, mode); } catch (e) { error = e; }
        if (hash(read.buffer) !== row.pin.sha256) throw stop('RuntimeMetadataV2Hash');
        if (error !== undefined) {
          const safe = refusal(error);
          if (safe === null || job.snapshot().stopped) throw stop('RuntimeMetadataV2Inspect');
          row[key] = { status: 'refused', summary: null, error: safe };
        } else {
          const summary = parsedSummary(result, mode), bytes = size(summary);
          if (summaryBytes + bytes > 16384) throw stop('RuntimeMetadataV2ReportLimit');
          summaryBytes += bytes; row[key] = { status: 'parsed', summary, error: null };
        }
      }
      row.status = 'complete'; next++;
    } catch (error) {
      row.status = 'failed';
      const code = error?.message === 'RuntimeMetadataV2ReportLimit' ? error.message :
        critical ?? 'RuntimeMetadataV2Inspect';
      throw stop(code);
    } finally { pending = false; }
    return snapshot();
  }
  return Object.freeze({ observe, snapshot, encode() { return JSON.stringify(snapshot()); } });
}
