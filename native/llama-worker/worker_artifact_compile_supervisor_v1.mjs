// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { spawn } from 'node:child_process';
import { createHash } from 'node:crypto';
import { addAbortListener } from 'node:events';
import { lstat, open, realpath } from 'node:fs/promises';
import { win32 } from 'node:path';

const EXECUTABLE = 'locallore-compile-host-v1.exe';
const REQUEST = 65548;
const RESPONSE = 69712;
const STDERR = 4096;
const IMAGE = 8 * 1024 * 1024;
const RUN_MS = 132000;
const DRAIN_MS = 5000;
const CAPS = Object.freeze({ 'START.json': 4096, 'OFFER.json': 4096, 'request.bin': REQUEST,
  'response.bin': RESPONSE, 'stderr.bin': STDERR, 'transport.json': 4096, 'CAPTURE.json': 4096,
  'terminal.json': 16384 });
const CONTEXT = ['attempt', 'recipe', 'baseline', 'closure', 'grant'];
const rawHash = bytes => createHash('sha256').update(bytes).digest('hex');
const json = data => Buffer.from(JSON.stringify(data));
const int = (value, lo, hi) => Number.isSafeInteger(value) && value >= lo && value <= hi;
const hash = value => typeof value === 'string' && value.length === 64 &&
  !/[^0-9a-f]/.test(value) && value !== '0'.repeat(64);

function requireSupervisor(ok) {
  if (!ok) throw Error('WorkerArtifactCompileSupervisorV1');
}

function data(value, keys) {
  requireSupervisor(value !== null && typeof value === 'object' &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value)));
  const own = Reflect.ownKeys(value);
  requireSupervisor(own.length === keys.length && own.every(key => keys.includes(key)));
  return Object.fromEntries(keys.map(key => {
    const field = Object.getOwnPropertyDescriptor(value, key);
    requireSupervisor(field?.enumerable && Object.hasOwn(field, 'value'));
    return [key, field.value];
  }));
}

function sameContext(value, context) {
  const supplied = data(value, CONTEXT);
  return CONTEXT.every(key => supplied[key] === context[key]);
}

function nativePath(value, project) {
  requireSupervisor(typeof value === 'string' && value.length < 1024 &&
    (project ? value.startsWith('D:/') : /^[CD]:\//.test(value)));
  const components = value.slice(3).split('/');
  requireSupervisor(components.every(part => part.length > 0 && part.length <= 255 &&
    !/[\x00-\x1f\x7f:"\\*?<>|;]/.test(part) && !/[ .]$/.test(part) &&
    !/^(?:con|prn|aux|nul|conin\$|conout\$|(?:com|lpt)[1-9¹²³])$/i.test(part.split('.')[0].trimEnd())));
  return win32.normalize(value);
}

const statOptions = { bigint: true };
const samePath = (left, right) => win32.normalize(left).toLowerCase() === win32.normalize(right).toLowerCase();
const identity = stat => {
  requireSupervisor(stat.ino > 0n && !stat.isSymbolicLink());
  return stat.dev.toString() + ':' + stat.ino.toString();
};
const stamp = stat => [identity(stat), stat.size, stat.mtimeNs, stat.ctimeNs, stat.mode].join(':');

async function ordinary(path, directory) {
  const entry = await lstat(path, statOptions);
  requireSupervisor((directory ? entry.isDirectory() : entry.isFile() && entry.nlink === 1n) &&
    !entry.isSymbolicLink() && samePath(await realpath(path), path));
  return entry;
}

async function requireAbsent(path) {
  try {
    await lstat(path);
  } catch (error) {
    if (error?.code === 'ENOENT') return;
    throw error;
  }
  requireSupervisor(false);
}

async function checkImage(path, expectedHash) {
  // Pinned libuv can append these suffixes if the absolute image is absent.
  await requireAbsent(path + '.com');
  await requireAbsent(path + '.exe');
  const named = await ordinary(path, false);
  requireSupervisor(named.size > 0n && named.size <= BigInt(IMAGE));
  const file = await open(path, 'r');
  try {
    const initial = await file.stat(statOptions);
    requireSupervisor(initial.isFile() && initial.nlink === 1n && stamp(initial) === stamp(named));
    const sha = createHash('sha256'), block = Buffer.alloc(65536);
    const size = Number(named.size);
    for (let position = 0; position < size;) {
      const want = Math.min(block.length, size - position);
      const { bytesRead } = await file.read(block, 0, want, position);
      requireSupervisor(int(bytesRead, 1, want));
      sha.update(block.subarray(0, bytesRead));
      position += bytesRead;
    }
    requireSupervisor((await file.read(block, 0, 1, size)).bytesRead === 0 &&
      stamp(await file.stat(statOptions)) === stamp(named) && sha.digest('hex') === expectedHash);
  } finally {
    await file.close();
  }
  requireSupervisor(stamp(await ordinary(path, false)) === stamp(named));
  return stamp(named);
}

async function verifyBytes(file, bytes) {
  const actual = Buffer.alloc(bytes.length + 1);
  for (let position = 0; position < bytes.length;) {
    const { bytesRead } = await file.read(actual, position, bytes.length - position, position);
    requireSupervisor(int(bytesRead, 1, bytes.length - position));
    position += bytesRead;
  }
  requireSupervisor((await file.read(actual, bytes.length, 1, bytes.length)).bytesRead === 0 &&
    actual.subarray(0, bytes.length).equals(bytes));
}

function createJournal(root) {
  let rootIdentity = null;
  const stamps = new Map();
  async function checkRoot() {
    const actual = identity(await ordinary(root, true));
    rootIdentity ??= actual;
    requireSupervisor(actual === rootIdentity);
  }

  async function verifyNamed(path, expected, bytes) {
    const file = await open(path, 'r');
    try {
      requireSupervisor(stamp(await file.stat(statOptions)) === expected);
      await verifyBytes(file, bytes);
      requireSupervisor(stamp(await file.stat(statOptions)) === expected);
    } finally {
      await file.close();
    }
    await checkRoot();
    requireSupervisor(stamp(await ordinary(path, false)) === expected);
  }

  async function save(name, bytes) {
    requireSupervisor(Object.hasOwn(CAPS, name) && bytes.length <= CAPS[name]);
    await checkRoot();
    const path = win32.join(root, name);
    const file = await open(path, 'wx+');
    let writtenIdentity;
    try {
      const initial = await file.stat(statOptions);
      requireSupervisor(initial.isFile() && initial.nlink === 1n && initial.size === 0n);
      for (let position = 0; position < bytes.length;) {
        const { bytesWritten } = await file.write(bytes, position, bytes.length - position, position);
        requireSupervisor(int(bytesWritten, 1, bytes.length - position));
        position += bytesWritten;
      }
      await file.sync();
      await verifyBytes(file, bytes);
      const final = await file.stat(statOptions);
      requireSupervisor(final.isFile() && final.nlink === 1n && identity(final) === identity(initial) &&
        final.size === BigInt(bytes.length));
      writtenIdentity = identity(final);
    } finally {
      await file.close();
    }
    await checkRoot();
    const named = await ordinary(path, false);
    requireSupervisor(identity(named) === writtenIdentity && named.size === BigInt(bytes.length));
    // Windows can finalize last-write timestamps only after the writer closes.
    const finalStamp = stamp(named);
    await verifyNamed(path, finalStamp, bytes);
    stamps.set(name, finalStamp);
    return rawHash(bytes);
  }

  async function verify(name, bytes) {
    const expected = stamps.get(name);
    requireSupervisor(expected !== undefined && bytes.length <= CAPS[name]);
    await checkRoot();
    const path = win32.join(root, name);
    requireSupervisor(stamp(await ordinary(path, false)) === expected);
    await verifyNamed(path, expected, bytes);
  }

  return { save, verify };
}

const blankProcess = () => ({ pid: null, closed: false, stdinClosed: false, stdoutClosed: false,
  stderrClosed: false, exitCode: null, sentBytes: null, sentHash: null, elapsedMs: 0,
  stop: 'preflight', cancelled: false, killAttempted: false, killAccepted: false,
  response: Buffer.alloc(0), stderr: Buffer.alloc(0) });

function runHelper(path, env, request, requestHash, signal) {
  return new Promise(resolve => {
    const result = blankProcess();
    const started = performance.now(), deadline = started + RUN_MS, drain = deadline + DRAIN_MS;
    let child;
    try {
      child = spawn(path, [], { cwd: win32.dirname(path), env, shell: false, detached: false,
        windowsHide: true, stdio: ['pipe', 'pipe', 'pipe'] });
    } catch {
      result.stop = 'spawn';
      result.elapsedMs = Math.floor(performance.now() - started);
      resolve(result);
      return;
    }
    result.stop = null;
    let settled = false, childClosed = false, matchingClose = false, exited = false;
    let exitSignal = null, exit = null;
    const input = child.stdin;
    let inputClosed = !input;
    const streams = [{ socket: child.stdout, buffer: Buffer.alloc(RESPONSE), size: 0, eof: false, closed: !child.stdout },
      { socket: child.stderr, buffer: Buffer.alloc(STDERR), size: 0, eof: false, closed: !child.stderr }];

    function abortInput() {
      if (input && !input.destroyed) input.destroy();
    }
    function kill() {
      if (result.pid === null || exited || result.killAttempted) return;
      result.killAttempted = true;
      try { result.killAccepted = child.kill('SIGKILL'); } catch { /* Leave closure unproven. */ }
    }
    function stop(reason) {
      if (settled) return;
      result.stop ??= reason;
      abortInput();
      kill();
    }
    function sample() {
      if (performance.now() >= deadline) stop('deadline');
    }
    function finish() {
      if (settled) return;
      sample();
      settled = true;
      clearTimeout(runTimer);
      clearTimeout(drainTimer);
      abortListener[Symbol.dispose]();
      result.elapsedMs = Math.floor(performance.now() - started);
      if (result.elapsedMs >= RUN_MS) result.stop ??= 'deadline';
      result.closed = exited && matchingClose && result.pid !== null;
      result.stdinClosed = Boolean(input) && inputClosed;
      result.stdoutClosed = streams[0].eof && streams[0].closed;
      result.stderrClosed = streams[1].eof && streams[1].closed;
      result.response = streams[0].buffer.subarray(0, streams[0].size);
      result.stderr = streams[1].buffer.subarray(0, streams[1].size);
      abortInput();
      for (const stream of streams) if (stream.socket && !stream.closed) stream.socket.destroy();
      resolve(result);
    }
    function maybeFinish() {
      if (childClosed && inputClosed && streams.every(stream => stream.closed)) finish();
    }
    const runTimer = setTimeout(() => stop('deadline'), Math.max(0, Math.ceil(deadline - performance.now())));
    const drainTimer = setTimeout(finish, Math.max(0, Math.ceil(drain - performance.now())));
    const abortListener = addAbortListener(signal, () => {
      if (settled) return;
      result.cancelled = true;
      abortInput();
    });

    child.once('spawn', () => {
      if (settled) return;
      if (!int(child.pid, 1, 2147483647)) {
        stop('spawn');
        return;
      }
      result.pid = child.pid;
      sample();
      if (result.stop !== null) {
        kill();
        return;
      }
      if (signal.aborted) {
        result.cancelled = true;
        abortInput();
        return;
      }
      if (!input || rawHash(request) !== requestHash) {
        stop('send');
        return;
      }
      input.write(request, error => {
        if (settled) return;
        sample();
        if (!error) {
          result.sentBytes = request.length;
          result.sentHash = requestHash;
        } else if (!result.cancelled) {
          stop('send');
        }
      });
    });
    child.on('error', () => stop(result.pid === null ? 'spawn' : 'io'));
    child.once('exit', (code, signalName) => {
      if (settled) return;
      exited = true;
      exit = code;
      exitSignal = signalName;
      result.exitCode = int(code, -2147483648, 4294967295) ? code | 0 : null;
      sample();
      abortInput();
    });
    child.once('close', (code, signalName) => {
      if (settled) return;
      childClosed = true;
      matchingClose = exited && code === exit && signalName === exitSignal;
      if (!matchingClose) stop('closure');
      sample();
      maybeFinish();
    });
    input?.on('error', () => stop('io'));
    input?.once('close', hadError => {
      if (hadError) stop('io');
      inputClosed = true;
      maybeFinish();
    });

    for (const stream of streams) {
      stream.socket?.on('error', () => stop('io'));
      stream.socket?.on('data', bytes => {
        if (settled) return;
        sample();
        const copy = Math.min(bytes.length, stream.buffer.length - stream.size);
        bytes.copy(stream.buffer, stream.size, 0, copy);
        stream.size += copy;
        if (copy !== bytes.length) {
          stop('overflow');
          stream.socket.destroy();
        }
      });
      stream.socket?.once('end', () => { if (!settled) stream.eof = true; });
      stream.socket?.once('close', hadError => {
        if (hadError) stop('io');
        stream.closed = true;
        maybeFinish();
      });
    }
  });
}

export function createWorkerArtifactCompileSupervisorV1(options) {
  const spec = data(options, ['context', 'hostHash', 'hostDirectory', 'evidenceRoot', 'windows', 'temp', 'admission']);
  const context = Object.freeze(data(spec.context, CONTEXT));
  const admitted = Object.freeze(data(spec.admission, ['job', 'spend', 'writerPolicy', 'namespace', 'hostLease']));
  requireSupervisor(process.platform === 'win32' && process.arch === 'x64' &&
    process.versions.node === '24.22.1' && process.execArgv.length === 0 &&
    !process.env.NODE_OPTIONS && !process.env.NODE_V8_COVERAGE &&
    [...Object.values(context), ...Object.values(admitted), spec.hostHash].every(hash));
  const host = win32.join(nativePath(spec.hostDirectory, true), EXECUTABLE);
  const root = nativePath(spec.evidenceRoot, true);
  const windows = nativePath(spec.windows, false), temp = nativePath(spec.temp, true);
  const env = Object.freeze({ HOMEDRIVE: 'D:', HOMEPATH: temp.slice(2), LOGONSERVER: '',
    PATH: win32.join(windows, 'System32'), SYSTEMDRIVE: windows.slice(0, 2), SYSTEMROOT: windows,
    TEMP: temp, TMP: temp, USERDOMAIN: '', USERNAME: '', USERPROFILE: temp, WINDIR: windows,
    NODE_OPTIONS: '', NODE_V8_COVERAGE: '' });
  const { save, verify } = createJournal(root);
  let startOffered = false, terminalOffered = false, offerUsed = false, offerPending = false;
  let journalPending = false, startBytes = null;
  let start = null, offer = null, transportUsed = false, transportPending = false, capture = null;
  let retainUsed = false, retainPending = false;

  function scopeOf(value) {
    const supplied = data(value, ['context', 'requestHash', 'hostHash']);
    requireSupervisor(sameContext(supplied.context, context) && hash(supplied.requestHash) &&
      supplied.hostHash === spec.hostHash);
    return Object.freeze({ context, requestHash: supplied.requestHash, hostHash: spec.hostHash });
  }

  async function journal(value) {
    requireSupervisor(!terminalOffered && !journalPending && !offerPending &&
      !transportPending && !retainPending);
    const fields = value?.kind === 'worker_artifact_compile_observation_start_v1'
      ? ['version', 'kind', 'context', 'preflight', 'runCount']
      : ['version', 'kind', 'context', 'status', 'code', 'started', 'offered', 'checks', 'process',
        'output', 'writerUnknown', 'objectUnknown', 'leaseClosed', 'linkAllowed', 'qualified'];
    const record = data(value, fields);
    requireSupervisor(record.version === 1 && sameContext(record.context, context) &&
      !terminalOffered && !journalPending && !offerPending && !transportPending && !retainPending);
    const starting = record.kind === 'worker_artifact_compile_observation_start_v1';
    if (starting) {
      requireSupervisor(!startOffered && record.runCount === 1 && hash(record.preflight));
      startOffered = true;
    } else {
      requireSupervisor(record.kind === 'worker_artifact_compile_observation_v1' &&
        record.linkAllowed === false && record.qualified === false);
      terminalOffered = true;
    }
    journalPending = true;
    try {
      // #408 hashes the original record's key order.
      const bytes = json(value);
      const sha256 = await save(starting ? 'START.json' : 'terminal.json', bytes);
      if (starting) {
        start = sha256;
        startBytes = bytes;
      }
      return JSON.stringify({ version: 1, kind: 'worker_artifact_compile_journal_ack_v1', sha256, stored: true });
    } finally {
      journalPending = false;
    }
  }

  async function authorize(value) {
    const scope = scopeOf(value);
    requireSupervisor(!terminalOffered && !offerUsed && !journalPending && start !== null);
    offerUsed = true;
    offerPending = true;
    try {
      await verify('START.json', startBytes);
      const proof = { kind: 'compile_host_authorized_v1', scope, spend: admitted.spend,
        start, writerPolicy: admitted.writerPolicy };
      const bytes = json(proof);
      const authorization = await save('OFFER.json', bytes);
      offer = Object.freeze({ scope, authorization, bytes });
      return bytes.toString('utf8');
    } finally {
      offerPending = false;
    }
  }

  async function transport(value) {
    const requestData = data(value, ['scope', 'authorization', 'request', 'signal']);
    const scope = scopeOf(requestData.scope);
    const signal = AbortSignal.any([requestData.signal]);
    requireSupervisor(!transportUsed && !terminalOffered && offer !== null &&
      scope.requestHash === offer.scope.requestHash && requestData.authorization === offer.authorization &&
      Buffer.isBuffer(requestData.request) && int(requestData.request.length, 12, REQUEST));
    const request = Buffer.from(requestData.request);
    requireSupervisor(rawHash(request) === scope.requestHash && !transportUsed && !terminalOffered);
    transportUsed = true;
    transportPending = true;
    try {
      await verify('START.json', startBytes);
      await verify('OFFER.json', offer.bytes);
      requireSupervisor(await save('request.bin', request) === scope.requestHash);
      let outcome = blankProcess(), before = null, after = null;
      if (!signal.aborted) {
        try { before = await checkImage(host, spec.hostHash); } catch { /* No launch without the pin. */ }
        if (before !== null && !signal.aborted) {
          outcome = await runHelper(host, env, request, scope.requestHash, signal);
        }
      }
      if (outcome.stop === 'preflight' && signal.aborted) {
        outcome.stop = 'cancelled';
        outcome.cancelled = true;
      }
      const { response, stderr, pid, closed, stdinClosed, stdoutClosed, stderrClosed, exitCode,
        sentBytes, sentHash, ...lifecycle } = outcome;
      let rawSaved = true;
      for (const [name, bytes] of [['response.bin', response], ['stderr.bin', stderr]]) {
        try { await save(name, bytes); } catch { rawSaved = false; }
      }
      if (pid !== null) {
        try { after = await checkImage(host, spec.hostHash); } catch { /* Drift leaves the image unproven. */ }
      }
      const image = before !== null && before === after && pid !== null ? spec.hostHash : null;
      const accepted = rawSaved && image !== null && lifecycle.stop === null && closed &&
        stdinClosed && stdoutClosed && stderrClosed && exitCode === 0 && !stderr.length &&
        sentBytes === request.length && sentHash === scope.requestHash;
      const facts = { image, pid, closed, stdinClosed, stdoutClosed, stderrClosed, exitCode, sentBytes, sentHash, accepted };
      const record = { kind: 'compile_supervisor_transport_v1', scope, authorization: offer.authorization,
        admitted, facts, lifecycle, before, after, environment: rawHash(json(env)), requestBytes: request.length,
        responseBytes: response.length, responseHash: rawHash(response), stderrBytes: stderr.length, stderrHash: rawHash(stderr) };
      const transportBytes = json(record);
      const observation = await save('transport.json', transportBytes);
      requireSupervisor(rawSaved);
      capture = { request, response, stderr, transportBytes, observation, facts, scope };
      return Object.freeze({ ...facts, observation, response: Buffer.from(response), stderr: Buffer.from(stderr) });
    } finally {
      transportPending = false;
    }
  }

  async function retain(value) {
    const supplied = data(value, ['record', 'request', 'response', 'stderr']);
    requireSupervisor(!retainUsed && !terminalOffered && capture !== null &&
      ['request', 'response', 'stderr'].every(key => Buffer.isBuffer(supplied[key]) && supplied[key].equals(capture[key])));
    const record = data(supplied.record, ['kind', 'scope', 'authorization', 'facts',
      'responseHash', 'responseBytes', 'stderrHash', 'stderrBytes']);
    const scope = scopeOf(record.scope);
    const actual = data(record.facts, [...Object.keys(capture.facts), 'observation']);
    requireSupervisor(record.kind === 'compile_host_capture_v1' && scope.requestHash === capture.scope.requestHash &&
      record.authorization === offer.authorization && actual.observation === capture.observation &&
      Object.keys(capture.facts).every(key => actual[key] === capture.facts[key]) &&
      record.responseHash === rawHash(capture.response) && record.responseBytes === capture.response.length &&
      record.stderrHash === rawHash(capture.stderr) && record.stderrBytes === capture.stderr.length);
    retainUsed = true;
    retainPending = true;
    try {
      const bytes = json(supplied.record);
      await verify('request.bin', capture.request);
      await verify('response.bin', capture.response);
      await verify('stderr.bin', capture.stderr);
      await verify('transport.json', capture.transportBytes);
      requireSupervisor(bytes.length <= 4096);
      const recordHash = await save('CAPTURE.json', bytes);
      return JSON.stringify({ kind: 'compile_host_retained_v1', recordHash, stored: true });
    } finally {
      retainPending = false;
    }
  }

  return Object.freeze({ journal, authorize, transport, retain });
}
