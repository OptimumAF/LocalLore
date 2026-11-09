// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const REQUEST_MAGIC = Buffer.from('LLCLV1\r\n');
const REPLY_MAGIC = Buffer.from('LLCLR1\r\n');
const REQUEST_CAP = 65536;
const REPLY_HEADER = 80;
const POLICY = { timeoutMs: 120000, drainMs: 5000, stdoutCap: 65536, stderrCap: 4096 };
const REPLY_CAP = REPLY_HEADER + POLICY.stdoutCap + POLICY.stderrCap;
const AUTHORITY = ['attempt', 'baseline', 'closure', 'grant'];
const ENVIRONMENT = ['windows', 'path', 'include', 'temp'];
const STOP = ['none', 'request', 'cancelled', 'deadline', 'setup', 'io', 'overflow', 'drain'];
const FLAG = ['exitKnown', 'jobKnown', 'member', 'resumed', 'signaled', 'killAttempted', 'killFailed',
  'ioError', 'processHandleClosed', 'handlesClosed', 'outOverflow', 'errOverflow', 'outEof', 'errEof'];
const aborted = Object.getOwnPropertyDescriptor(AbortSignal.prototype, 'aborted').get;

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const digest = value => typeof value === 'string' && value.length === 64 && !/[^0-9a-f]/.test(value) && value !== '0'.repeat(64);
const jsonHash = value => sha(JSON.stringify(value));
const boolean = value => typeof value === 'boolean';
const int = (value, lo, hi) => Number.isSafeInteger(value) && value >= lo && value <= hi;

function requireHost(valid) {
  if (!valid) throw Error('WorkerArtifactCompileHostV1');
}

function data(value, keys) {
  requireHost(value !== null && typeof value === 'object' &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value)));
  const own = Reflect.ownKeys(value);
  requireHost(own.length === keys.length && own.every(key => keys.includes(key)));
  const copy = {};
  for (const key of keys) {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    requireHost(descriptor?.enumerable && Object.hasOwn(descriptor, 'value'));
    copy[key] = descriptor.value;
  }
  return copy;
}

function equal(value, expected) {
  const keys = Object.keys(expected);
  const got = data(value, keys);
  return keys.every(key => got[key] === expected[key]);
}

function sameScope(value, scope) {
  const supplied = data(value, ['context', 'requestHash', 'hostHash']);
  return equal(supplied.context, scope.context) && supplied.requestHash === scope.requestHash &&
    supplied.hostHash === scope.hostHash;
}

function wire(text, keys) {
  requireHost(typeof text === 'string' && Buffer.byteLength(text, 'utf8') <= 4096);
  const parsed = JSON.parse(text);
  requireHost(JSON.stringify(parsed) === text);
  return data(parsed, keys);
}

function stepMatches(value, expected) {
  const { args, ...step } = data(value, Object.keys(expected));
  const { args: expectedArgs, ...expectedStep } = expected;
  requireHost(equal(step, expectedStep) && Array.isArray(args) &&
    Object.getPrototypeOf(args) === Array.prototype &&
    args.length === expectedArgs.length && Reflect.ownKeys(args).length === args.length + 1);
  return expectedArgs.every((arg, index) => {
    const descriptor = Object.getOwnPropertyDescriptor(args, index);
    return descriptor?.enumerable && descriptor.value === arg;
  });
}

function frame(context, step, candidate, env) {
  const values = [step.tool, step.cwd, candidate.upstreamRoot, candidate.outputRoot,
    ...ENVIRONMENT.map(key => env[key]), ...step.args];
  requireHost(step.args.length === 31);
  const strings = [];
  let size = 32;
  for (const value of values) {
    requireHost(typeof value === 'string' && value.length > 0 && value.length <= 16384 && !value.includes('\0'));
    const length = Buffer.byteLength(value, 'utf8');
    size += 2 + length;
    requireHost(length <= 65535 && size <= REQUEST_CAP);
    const entry = Buffer.alloc(2 + length);
    entry.writeUInt16LE(length);
    entry.write(value, 2, length, 'utf8');
    requireHost(entry.toString('utf8', 2) === value);
    strings.push(entry);
  }
  const payload = Buffer.concat(strings);
  const binding = createHash('sha256').update(JSON.stringify(context)).update(payload).digest();
  const header = Buffer.alloc(12);
  REQUEST_MAGIC.copy(header);
  header.writeUInt32LE(size, 8);
  return { request: Buffer.concat([header, binding, payload]), binding };
}

function parseReply(bytes, binding) {
  requireHost(bytes.length >= REPLY_HEADER && bytes.subarray(0, 8).equals(REPLY_MAGIC) &&
    bytes.subarray(8, 40).equals(binding));
  const stop = STOP[bytes.readUInt32LE(40)], pid = bytes.readUInt32LE(44), error = bytes.readUInt32LE(48);
  const exitCode = bytes.readInt32LE(52), active = bytes.readUInt32LE(56), bits = bytes.readUInt32LE(60);
  const elapsedMs = bytes.readBigUInt64LE(64);
  const stdoutBytes = bytes.readUInt32LE(72), stderrBytes = bytes.readUInt32LE(76);
  requireHost(stop !== undefined && bits < (1 << FLAG.length) && stdoutBytes <= POLICY.stdoutCap &&
    stderrBytes <= POLICY.stderrCap && bytes.length === REPLY_HEADER + stdoutBytes + stderrBytes);
  const f = Object.fromEntries(FLAG.map((name, bit) => [name, Boolean(bits & (1 << bit))]));
  const closed = f.signaled && f.exitKnown && f.processHandleClosed;
  const overflow = f.outOverflow || f.errOverflow;
  const owned = closed && f.member && f.jobKnown && active === 0 && f.outEof && f.errEof && f.handlesClosed;
  requireHost((f.exitKnown ? f.signaled : exitCode === 0) && (f.jobKnown || active === 0) &&
    (!f.resumed || f.member) && (!f.killFailed || f.killAttempted) &&
    (!f.outOverflow || (!f.outEof && stdoutBytes === POLICY.stdoutCap)) &&
    (!f.errOverflow || (!f.errEof && stderrBytes === POLICY.stderrCap)) &&
    (pid > 0 || (!f.member && !f.resumed && !f.signaled && !f.jobKnown && !f.processHandleClosed &&
      !f.killAttempted && !stdoutBytes && !stderrBytes && !f.outEof && !f.errEof && !overflow)) &&
    (pid === 0 || !f.handlesClosed || f.processHandleClosed) &&
    (stop !== 'overflow' || overflow) &&
    (stop !== 'io' || f.ioError) &&
    (stop !== 'none' || (pid > 0 && owned && f.resumed && !f.ioError && !overflow && !f.killAttempted && error === 0)));
  return { stop, pid, exitCode: f.exitKnown ? exitCode : null, elapsedMs, stdoutBytes, stderrBytes,
    stdoutHash: sha(bytes.subarray(REPLY_HEADER, REPLY_HEADER + stdoutBytes)),
    stderrHash: sha(bytes.subarray(REPLY_HEADER + stdoutBytes)), closed, overflow, owned,
    killAttempted: f.killAttempted, ioError: f.ioError };
}

function transportRecord(result) {
  const { response, stderr, ...facts } = data(result, ['image', 'observation', 'pid', 'closed', 'stdinClosed',
    'stdoutClosed', 'stderrClosed', 'exitCode', 'response', 'stderr']);
  requireHost((facts.image === null || digest(facts.image)) && digest(facts.observation) &&
    (facts.pid === null || int(facts.pid, 1, 2147483647)) &&
    [facts.closed, facts.stdinClosed, facts.stdoutClosed, facts.stderrClosed].every(boolean) &&
    (facts.exitCode === null || int(facts.exitCode, -2147483648, 2147483647)) &&
    Buffer.isBuffer(response) && response.length <= REPLY_CAP &&
    Buffer.isBuffer(stderr) && stderr.length <= POLICY.stderrCap);
  return { facts: Object.freeze(facts), response: Buffer.from(response), stderr: Buffer.from(stderr) };
}

export function createWorkerArtifactCompileHostV1(options) {
  const spec = data(options, ['config', 'authority', 'environment', 'hostHash', 'ports']);
  const authority = data(spec.authority, AUTHORITY);
  requireHost(AUTHORITY.every(key => digest(authority[key])) && digest(spec.hostHash));
  const recipe = planWorkerArtifactComparisonV1(spec.config);
  const context = Object.freeze({ attempt: authority.attempt, recipe: jsonHash(recipe),
    baseline: authority.baseline, closure: authority.closure, grant: authority.grant });
  const step = recipe.steps[0];
  const { request, binding } = frame(context, step, recipe.candidates[0], data(spec.environment, ENVIRONMENT));
  const scope = Object.freeze({ context, requestHash: sha(request), hostHash: spec.hostHash });
  const ports = data(spec.ports, ['authorize', 'transport', 'retain', 'excludeWriters']);
  requireHost(Object.values(ports).every(port => typeof port === 'function'));
  const { authorize, transport, retain, excludeWriters } = ports;
  let used = false;

  async function launch(...args) {
    requireHost(!used && args.length === 1);
    const offer = data(args[0], ['version', 'context', 'index', 'step', 'policy', 'signal']);
    const { signal } = offer;
    requireHost(offer.version === 1 && offer.index === 0 && equal(offer.context, context) &&
      stepMatches(offer.step, step) && equal(offer.policy, POLICY));
    const isAborted = () => aborted.call(signal);
    const alreadyAborted = isAborted();
    requireHost(!used);
    used = true;
    requireHost(!alreadyAborted);
    const authorized = wire(await authorize(scope), ['kind', 'scope', 'spend', 'start', 'writerPolicy']);
    requireHost(authorized.kind === 'compile_host_authorized_v1' && sameScope(authorized.scope, scope) &&
      [authorized.spend, authorized.start, authorized.writerPolicy].every(digest) && !isAborted());
    const authorization = jsonHash(authorized);

    const { facts, response, stderr } = transportRecord(await transport(Object.freeze({
      scope, authorization, request: Buffer.from(request), signal
    })));
    const record = Object.freeze({ kind: 'compile_host_capture_v1', scope, authorization, facts,
      responseHash: sha(response), responseBytes: response.length,
      stderrHash: sha(stderr), stderrBytes: stderr.length });
    const recordHash = jsonHash(record);
    const kept = wire(await retain(Object.freeze({ record, request: Buffer.from(request),
      response: Buffer.from(response), stderr: Buffer.from(stderr) })), ['kind', 'recordHash', 'stored']);
    requireHost(kept.kind === 'compile_host_retained_v1' && kept.stored === true && kept.recordHash === recordHash);
    requireHost(facts.image === scope.hostHash && facts.pid !== null && facts.closed && facts.stdinClosed &&
      facts.stdoutClosed && facts.stderrClosed && facts.exitCode === 0 && !stderr.length);
    const native = parseReply(response, binding);
    requireHost(int(native.pid, 1, 2147483647) && native.pid !== facts.pid && native.elapsedMs <= BigInt(POLICY.timeoutMs + POLICY.drainMs));

    let writerProof = null;
    const stoppedWithoutProcessFlag = ['request', 'setup', 'io'].includes(native.stop) ||
      (native.stop === 'cancelled' && !isAborted());
    if (native.owned && !native.ioError && !stoppedWithoutProcessFlag) {
      const check = Object.freeze({ scope, authorization, writerPolicy: authorized.writerPolicy, recordHash });
      try {
        const proof = wire(await excludeWriters(check),
          ['kind', 'scope', 'authorization', 'writerPolicy', 'recordHash', 'postflight']);
        if (proof.kind === 'compile_host_writers_excluded_v1' && sameScope(proof.scope, scope) &&
            proof.authorization === authorization && proof.writerPolicy === check.writerPolicy &&
            proof.recordHash === recordHash && digest(proof.postflight)) writerProof = jsonHash(proof);
      } catch { /* Keep the measured process receipt with writer closure unproven. */ }
    }
    const process = { version: 1, kind: 'worker_artifact_process_v1', attempt: context.attempt,
      recipe: context.recipe, baseline: context.baseline, closure: context.closure, index: 0,
      pid: native.pid, exitCode: native.exitCode, elapsedMs: Number(native.elapsedMs),
      stdoutBytes: native.stdoutBytes, stderrBytes: native.stderrBytes, stdoutHash: native.stdoutHash,
      stderrHash: native.stderrHash, closed: native.closed, unknown: !native.closed,
      timedOut: native.stop === 'deadline' || native.stop === 'drain', overflow: native.overflow,
      killAttempted: native.killAttempted, ioError: native.ioError, processTreeContained: false };
    return JSON.stringify({ version: 1, kind: 'worker_artifact_compile_writer_v1', process,
      writersClosed: writerProof !== null, writerProof });
  }

  return Object.freeze({ launch });
}
