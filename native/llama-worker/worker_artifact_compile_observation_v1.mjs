// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PREFIX = 'WorkerArtifactCompileObservationV1';
const INVALID = Symbol('invalid compile observation data');
const STOP = Symbol('compile observation stopped');
const MAX = 67108864;
const U64 = (1n << 64n) - 1n;
const MARKER = '.locallore-output-owner-v1';
const POLICY = Object.freeze({ timeoutMs: 120000, drainMs: 5000, stdoutCap: 65536, stderrCap: 4096 });
const AUTHORITY = ['attempt', 'baseline', 'closure', 'grant'];
const CONTEXT = ['attempt', 'recipe', 'baseline', 'closure', 'grant'];
const STABLE = ['source', 'headers', 'tool', 'environment', 'normal', 'temp'];
const CHECK_FIELDS = ['version', 'kind', 'context', 'when', 'roster', ...STABLE, 'storage', 'reserve'];
const PROCESS_CONTEXT = ['attempt', 'recipe', 'baseline', 'closure'];
const PROCESS_FLAGS = ['closed', 'unknown', 'timedOut', 'overflow', 'killAttempted', 'ioError', 'processTreeContained'];
const PROCESS = ['version', 'kind', ...PROCESS_CONTEXT, 'index', 'pid', 'exitCode', 'elapsedMs',
  'stdoutBytes', 'stderrBytes', 'stdoutHash', 'stderrHash', ...PROCESS_FLAGS];
const READER = ['version', 'kind', 'index', 'candidate', 'role', 'ok', 'code', 'file', 'metadata',
  'io', 'unknownClosure', 'ioUncertain'];
const READER_CODES = ['REQUEST', 'CANCELLED', 'DEADLINE', 'CLOCK', 'IDENTITY', 'CONTENT', 'COFF', 'IO', 'CLOSE'];
const LEASE_FIELDS = ['version', 'kind', 'qualified', 'state', 'pending', 'stop', 'rechecks', 'withinBudget', 'observedBytes', 'roots'];
const ROOT_FIELDS = ['candidate', 'creation', 'identity', 'marker', 'markerClosure', 'directoryClosure', 'complete', 'files'];
const LEASE_CODES = ['Cancelled', 'Deadline', 'Clock', 'Limit', 'Exists', 'Identity', 'Marker', 'Roster', 'Budget', 'IO', 'Closure'];
const CLOSURES = ['none', 'open', 'closed', 'unknown'];

function requireData(ok) {
  if (!ok) throw INVALID;
}

function data(value, names) {
  requireData(value !== null && typeof value === 'object' &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value)));
  const keys = Reflect.ownKeys(value);
  requireData(keys.length === names.length && keys.every(key => names.includes(key)));
  const copy = {};
  for (const key of keys) {
    const d = Object.getOwnPropertyDescriptor(value, key);
    requireData(d?.enumerable && Object.hasOwn(d, 'value'));
    copy[key] = d.value;
  }
  return copy;
}

function method(owner, name) {
  const d = Object.getOwnPropertyDescriptor(owner, name);
  requireData(d && Object.hasOwn(d, 'value') && typeof d.value === 'function');
  const fn = d.value;
  return (...args) => Reflect.apply(fn, owner, args);
}

function array(value, maximum) {
  requireData(Array.isArray(value));
  const length = Object.getOwnPropertyDescriptor(value, 'length')?.value;
  requireData(Number.isSafeInteger(length) && length >= 0 && length <= maximum &&
    Reflect.ownKeys(value).length === length + 1);
  const result = [];
  for (let i = 0; i < length; i++) {
    const entry = Object.getOwnPropertyDescriptor(value, String(i));
    requireData(entry?.enumerable && Object.hasOwn(entry, 'value'));
    result.push(entry.value);
  }
  return result;
}

function freeze(value) {
  if (value !== null && typeof value === 'object') {
    Object.values(value).forEach(freeze);
    Object.freeze(value);
  }
  return value;
}

const sha = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const hex = value => typeof value === 'string' && value.length === 64 && !/[^a-f0-9]/.test(value);
const digest = value => hex(value) && value !== '0'.repeat(64);
const integer = (value, min, max) => Number.isSafeInteger(value) && value >= min && value <= max;
const bool = value => typeof value === 'boolean';

function wire(text, fields) {
  requireData(typeof text === 'string' && Buffer.byteLength(text, 'utf8') <= 4096);
  const parsed = JSON.parse(text);
  requireData(JSON.stringify(parsed) === text);
  return data(parsed, fields);
}

function decimal(value, max = U64) {
  requireData(typeof value === 'string' && value.length >= 1 && value.length <= 20 && !/[^0-9]/.test(value));
  const n = BigInt(value);
  requireData(n.toString() === value && n <= max);
  return n;
}

function deviceOf(token) {
  requireData(typeof token === 'string' && token.length <= 41);
  const parts = token.split(':');
  requireData(parts.length === 2);
  const device = decimal(parts[0]), inode = decimal(parts[1]);
  requireData(inode > 0n);
  return device;
}

function leaseView(value) {
  const view = data(value, LEASE_FIELDS);
  requireData(view.version === 1 && view.kind === 'worker_artifact_output_roots_v1' &&
    view.qualified === false && view.pending === null && integer(view.rechecks, 0, 32) &&
    (view.stop === null || LEASE_CODES.includes(view.stop)) && bool(view.withinBudget));
  decimal(view.observedBytes, U64 + BigInt(MAX));
  view.roots = array(view.roots, 2).map((value, index) => {
    const root = data(value, ROOT_FIELDS);
    requireData(root.candidate === (index === 0 ? 'A' : 'B') &&
      ['unattempted', 'unknown', 'created', 'exists'].includes(root.creation) &&
      ['unattempted', 'unknown', 'created'].includes(root.marker) &&
      CLOSURES.includes(root.markerClosure) && CLOSURES.includes(root.directoryClosure) && bool(root.complete));
    if (root.identity !== null) deviceOf(root.identity);
    root.files = array(root.files, 8).map(value => {
      const file = data(value, ['name', 'identity', 'bytes']);
      requireData(typeof file.name === 'string' && file.name.length >= 1 && file.name.length <= 255);
      deviceOf(file.identity);
      decimal(file.bytes);
      return file;
    });
    return root;
  });
  requireData(view.roots.length === 2);
  return view;
}

function markerClosed(value) {
  const view = leaseView(value);
  requireData(view.state === 'Closed' && view.withinBudget === false);
  for (const root of view.roots) {
    requireData((root.marker === 'created' ? root.creation === 'created' && root.identity !== null && root.markerClosure === 'closed' :
      root.marker === 'unattempted' && root.markerClosure === 'none') &&
      (root.directoryClosure === 'none' || root.directoryClosure === 'closed') &&
      (!root.complete || root.directoryClosure === 'closed'));
  }
  return true;
}

function roster(value, candidate, before = null) {
  const view = leaseView(value);
  requireData(view.state === 'Ready' && view.stop === null && view.withinBudget === true &&
    view.rechecks === (before === null ? 0 : 1));
  const objectName = candidate.object.slice(candidate.outputRoot.length + 1);
  const pdbName = candidate.compilerPdb.slice(candidate.outputRoot.length + 1);
  const seen = new Set();
  function unique(identity) {
    requireData(!seen.has(identity));
    seen.add(identity);
  }
  let bytes = 0n, object = null, rootDevice = null;
  for (const [index, root] of view.roots.entries()) {
    requireData(root.creation === 'created' && root.marker === 'created' && root.markerClosure === 'open' &&
      root.directoryClosure === 'closed' && root.complete === true);
    const device = deviceOf(root.identity);
    rootDevice ??= device;
    requireData(device === rootDevice);
    unique(root.identity);
    const active = before !== null && index === 0;
    requireData(active ? root.files.length >= 2 && root.files.length <= 3 : root.files.length === 1);
    if (before !== null) requireData(root.identity === before.view.roots[index].identity);
    const names = new Set();
    for (const file of root.files) {
      requireData((file.name === MARKER || (active && [objectName, pdbName].includes(file.name))) &&
        !names.has(file.name) && deviceOf(file.identity) === device);
      names.add(file.name);
      unique(file.identity);
      const size = decimal(file.bytes, BigInt(MAX));
      bytes += size;
      if (file.name === MARKER) {
        requireData(size === 167n);
        if (before !== null) requireData(file.identity === before.view.roots[index].files[0].identity);
      } else if (file.name === objectName) {
        requireData(size > 0n);
        object = Object.freeze({ index: 0, candidate: 'A', role: 'object',
          rootIdentity: root.identity, fileIdentity: file.identity, bytes: Number(size) });
      }
    }
    requireData(names.has(MARKER));
  }
  requireData(bytes <= BigInt(MAX) && view.observedBytes === bytes.toString() && (before === null || object !== null));
  return { view, digest: sha(view), object };
}

function writerReceipt(text, context) {
  const value = wire(text, ['version', 'kind', 'process', 'writersClosed', 'writerProof']);
  const process = data(value.process, PROCESS);
  requireData(value.version === 1 && value.kind === 'worker_artifact_compile_writer_v1' &&
    bool(value.writersClosed) && (value.writersClosed ? digest(value.writerProof) : value.writerProof === null));
  requireData(process.version === 1 && process.kind === 'worker_artifact_process_v1' && process.index === 0 &&
    PROCESS_CONTEXT.every(key => process[key] === context[key]) && integer(process.pid, 1, 2147483647) &&
    (process.exitCode === null || integer(process.exitCode, -2147483648, 2147483647)) &&
    integer(process.elapsedMs, 0, POLICY.timeoutMs + POLICY.drainMs) &&
    integer(process.stdoutBytes, 0, POLICY.stdoutCap) && integer(process.stderrBytes, 0, POLICY.stderrCap) &&
    hex(process.stdoutHash) && hex(process.stderrHash) &&
    PROCESS_FLAGS.every(key => bool(process[key])) && process.processTreeContained === false);
  value.process = process;
  return freeze(value);
}

function readerReceipt(value, request) {
  const proof = data(value, READER);
  const io = data(proof.io, ['reservedReadBytes', 'actualReadBytes', 'opened', 'closed', 'verifiedScans']);
  const reserved = decimal(io.reservedReadBytes), actual = decimal(io.actualReadBytes);
  const payload = 2n * BigInt(request.bytes);
  requireData(proof.version === 1 && proof.kind === 'worker_artifact_held_output_v1' &&
    proof.index === request.index && proof.candidate === request.candidate && proof.role === request.role &&
    bool(proof.ok) && bool(proof.unknownClosure) && bool(proof.ioUncertain) &&
    integer(io.opened, 0, 1) && integer(io.closed, 0, io.opened) && integer(io.verifiedScans, 0, 2) &&
    (proof.unknownClosure || io.opened === io.closed) &&
    (reserved === payload + 2n ||
      (reserved === 0n && actual === 0n && io.opened === 0 && io.closed === 0 && io.verifiedScans === 0)) &&
    (proof.ioUncertain || actual <= reserved));
  if (proof.ok) {
    const file = data(proof.file, ['sha256', 'bytes']);
    const metadata = data(proof.metadata, ['directives', 'defaultLibraries']);
    metadata.directives = array(metadata.directives, 64);
    metadata.defaultLibraries = array(metadata.defaultLibraries, 64);
    const values = [...metadata.directives, ...metadata.defaultLibraries];
    requireData(proof.code === null && !proof.unknownClosure && !proof.ioUncertain &&
      reserved === payload + 2n && actual === payload && io.opened === 1 && io.closed === 1 && io.verifiedScans === 2 &&
      digest(file.sha256) && file.bytes === request.bytes &&
      values.length <= 64 && values.every(value => typeof value === 'string' && value.length <= 8192) &&
      Buffer.byteLength(JSON.stringify(metadata), 'utf8') <= 8192);
    proof.file = file;
    proof.metadata = metadata;
  } else {
    requireData(READER_CODES.includes(proof.code) && proof.file === null && proof.metadata === null);
  }
  proof.io = io;
  return freeze(proof);
}

function setup(options) {
  try {
    const spec = data(options, ['config', 'authority', 'outputRoots', 'outputReader', 'ports']);
    const authority = data(spec.authority, AUTHORITY);
    requireData(AUTHORITY.every(key => digest(authority[key])));
    const recipe = planWorkerArtifactComparisonV1(spec.config);
    const ports = data(spec.ports, ['check', 'launch', 'journal']);
    requireData(Object.values(ports).every(value => typeof value === 'function'));
    return {
      context: Object.freeze({ attempt: authority.attempt, recipe: sha(recipe), baseline: authority.baseline,
        closure: authority.closure, grant: authority.grant }),
      step: recipe.steps[0], candidate: recipe.candidates[0],
      prepare: method(spec.outputRoots, 'prepare'), recheck: method(spec.outputRoots, 'recheck'),
      cancelLease: method(spec.outputRoots, 'cancel'), close: method(spec.outputRoots, 'close'),
      readNext: method(spec.outputReader, 'readNext'),
      check: method(ports, 'check'), launch: method(ports, 'launch'), journal: method(ports, 'journal')
    };
  } catch {
    throw Error(PREFIX + 'Input');
  }
}

export function createWorkerArtifactCompileObservationV1(options) {
  const { context, step, candidate, prepare, recheck, cancelLease, close, readNext, check, launch, journal } = setup(options);
  const controller = new AbortController();
  const signal = controller.signal;
  let used = false, selectingReport = false, phase = 'new', stop = null, cancelled = false;
  let started = false, leaseOffered = false, offered = false, writerUnknown = false, objectUnknown = false;

  function requireNoArgs(args) {
    if (args.length !== 0) throw Error(PREFIX + 'Input');
  }
  function snapshot(...args) {
    requireNoArgs(args);
    return Object.freeze({
      version: 1, kind: 'worker_artifact_compile_observation_snapshot_v1', phase,
      started, offered, cancelled, writerUnknown, objectUnknown, stop
    });
  }
  function cancel(...args) {
    requireNoArgs(args);
    if (cancelled || selectingReport) return false;
    cancelled = true;
    stop ??= 'CANCELLED';
    try { controller.abort(); } catch { /* Still request lease cancellation and await closure. */ }
    if (leaseOffered) {
      try { cancelLease(); } catch { /* Known closure still requires the final lease receipt. */ }
    }
    return true;
  }
  function live() {
    if (stop !== null) throw STOP;
  }
  function fail(code) {
    stop ??= code;
    throw STOP;
  }
  async function receive(nextPhase, code, offer, validate) {
    live();
    phase = nextPhase;
    try {
      return validate(await offer());
    } catch {
      fail(code);
    }
  }
  function checkProof(text, when, roster, baseline) {
    const proof = wire(text, CHECK_FIELDS);
    const supplied = data(proof.context, CONTEXT);
    requireData(proof.version === 1 && proof.kind === 'worker_artifact_compile_check_v1' &&
      CONTEXT.every(key => supplied[key] === context[key]) && proof.when === when && proof.roster === roster &&
      [...STABLE, 'storage', 'reserve'].every(key => digest(proof[key])) &&
      (baseline === null || STABLE.every(key => proof[key] === baseline[key])));
    return proof;
  }
  function ask(when, roster, baseline) {
    const request = Object.freeze({ version: 1, context, index: 0, when, roster });
    return receive(when, when === 'after' ? 'POSTFLIGHT' : 'PREFLIGHT',
      () => check(request, signal), text => checkProof(text, when, roster, baseline));
  }
  function acknowledged(text, record) {
    const ack = wire(text, ['version', 'kind', 'sha256', 'stored']);
    requireData(ack.version === 1 && ack.kind === 'worker_artifact_compile_journal_ack_v1' &&
      ack.sha256 === sha(record) && ack.stored === true);
    return true;
  }

  async function run(...args) {
    requireNoArgs(args);
    if (used) throw Error(PREFIX + 'Used');
    used = true;
    const checks = { admit: null, before: null, after: null };
    let process = null, output = null, leaseClosed = false;
    try {
      const admit = await ask('admit', null, null);
      checks.admit = sha(admit);
      const start = Object.freeze({ version: 1, kind: 'worker_artifact_compile_observation_start_v1',
        context, preflight: checks.admit, runCount: 1 });
      started = await receive('start', 'START', () => journal(start), text => acknowledged(text, start));

      const before = await receive('prepare', 'LEASE', () => {
        leaseOffered = true;
        return prepare();
      }, value => roster(value, candidate));
      checks.before = sha(await ask('before', before.digest, admit));
      const request = Object.freeze({ version: 1, context, index: 0, step, policy: POLICY, signal });
      process = await receive('launch', 'CLOSURE', () => {
        offered = true;
        writerUnknown = true;
        return launch(request);
      }, text => writerReceipt(text, context));
      const direct = process.process;
      writerUnknown = !(process.writersClosed && direct.closed && !direct.unknown && !direct.ioError);
      if (writerUnknown) fail('CLOSURE');
      if (direct.exitCode !== 0 || direct.timedOut || direct.overflow || direct.killAttempted) fail('PROCESS');

      const after = await receive('roster', 'ROSTER', recheck, value => roster(value, candidate, before));
      output = await receive('read', 'OBJECT', () => {
        objectUnknown = true;
        return readNext(after.object, signal);
      }, value => readerReceipt(value, after.object));
      objectUnknown = output.unknownClosure;
      if (!output.ok) fail('OBJECT');
      checks.after = sha(await ask('after', after.digest, admit));
    } catch {
      stop ??= 'POSTFLIGHT';
    } finally {
      if (leaseOffered && !writerUnknown && !objectUnknown) {
        phase = 'close';
        try {
          leaseClosed = markerClosed(await close());
        } catch {
          stop ??= 'CLOSURE';
        }
      }
    }

    selectingReport = true;
    phase = 'record';
    const report = freeze({
      version: 1, kind: 'worker_artifact_compile_observation_v1', context,
      status: stop === null ? 'observed' : 'stopped', code: stop, started, offered, checks,
      process, output, writerUnknown, objectUnknown, leaseClosed, linkAllowed: false, qualified: false
    });
    let retained = false;
    try {
      requireData(Buffer.byteLength(JSON.stringify(report), 'utf8') <= 16384);
      retained = acknowledged(await journal(report), report);
    } catch { /* Keep the original report when durable retention cannot be attested. */ }
    phase = 'done';
    return Object.freeze({ report, retained });
  }

  return Object.freeze({ run, cancel, snapshot });
}
