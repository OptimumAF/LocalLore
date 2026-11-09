// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Development-only orchestration; no filesystem/process/native adapter or Author authority.
// Independent FIRST frozen at 8c1168cb / integration eb6b4b6a BEFORE this producer.
import { createHash } from 'node:crypto';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const PORTS = ['admit', 'launchStep', 'inspectOutputs', 'prepareManifest', 'recheck', 'compare', 'record'];
const CHECKS = ['source', 'headers', 'tools', 'inputs', 'physicalRoots', 'environment', 'searchOrder',
  'noShadow', 'ownership', 'exclusiveOutputs', 'storage', 'reserve', 'authority', 'normalWorker'];
const COMMON = ['version', 'kind', 'attempt', 'recipe', 'baseline', 'closure'];
const OUTPUT_FLAGS = ['owned', 'ordinary', 'rosterComplete', 'withinBudget', 'directivesValidated', 'resolutionComplete'];
const MANIFEST_FLAGS = ['ordinary', 'exclusive', 'equal', 'withinBudget'];
const COMPARE_FLAGS = ['ordinary', 'withinBudget', 'objectEqual', 'executableEqual'];
const EXTRA = {
  admit: ['runCount', 'checks'], recheck: ['index', 'when', 'checks'],
  launchStep: ['index', 'pid', 'closed', 'unknown', 'exitCode', 'timedOut', 'overflow', 'killAttempted',
    'ioError', 'elapsedMs', 'stdoutBytes', 'stderrBytes', 'stdoutHash', 'stderrHash', 'processTreeContained'],
  inspectOutputs: ['index', ...OUTPUT_FLAGS, 'object', 'executable', 'manifest'],
  prepareManifest: ['index', ...MANIFEST_FLAGS, 'manifest', 'preEmbed', 'copy'],
  compare: ['index', ...COMPARE_FLAGS]
};
const KINDS = { admit: 'worker_artifact_admission_v1', recheck: 'worker_artifact_recheck_v1',
  launchStep: 'worker_artifact_process_v1', inspectOutputs: 'worker_artifact_outputs_v1',
  prepareManifest: 'worker_artifact_manifest_v1', compare: 'worker_artifact_compare_v1' };
const bytes = value => Buffer.byteLength(value, 'utf8');
const sha = value => createHash('sha256').update(JSON.stringify(value)).digest('hex');
const integer = (value, min, max) => Number.isSafeInteger(value) && value >= min && value <= max;
const digest = value => typeof value === 'string' && value.length === 64 && !/[^a-f0-9]/.test(value);
const nonzero = value => digest(value) && value !== '0'.repeat(64);
class Stop extends Error {
  constructor(code, unknown = false) { super(code); this.code = code; this.unknown = unknown; }
}
const requireReceipt = value => { if (!value) throw new Stop('RECEIPT'); };
const requireSemantic = (value, code, unknown = false) => { if (!value) throw new Stop(code, unknown); };
function ownData(value, names) {
  try {
    if (value === null || typeof value !== 'object' ||
      ![Object.prototype, null].includes(Object.getPrototypeOf(value))) throw Error();
    const found = Reflect.ownKeys(value);
    if (found.length !== names.length || found.some(key => typeof key !== 'string' || !names.includes(key))) throw Error();
    const result = {};
    for (const name of names) {
      const d = Object.getOwnPropertyDescriptor(value, name);
      if (!d || !d.enumerable || !Object.hasOwn(d, 'value')) throw Error();
      result[name] = d.value;
    }
    return result;
  } catch { throw Error('WorkerArtifactCoordinatorV1Invalid'); }
}
function exact(value, names) {
  requireReceipt(value !== null && typeof value === 'object' && !Array.isArray(value) &&
    Object.getPrototypeOf(value) === Object.prototype && Object.keys(value).length === names.length &&
    Object.keys(value).every(key => names.includes(key)));
}
function freeze(value) {
  if (value !== null && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  return value;
}
function decode(wire) {
  requireReceipt(typeof wire === 'string' && bytes(wire) <= 4096);
  let value;
  try { value = JSON.parse(wire); } catch { throw new Stop('RECEIPT'); }
  requireReceipt(JSON.stringify(value) === wire);
  return value;
}
function booleans(value, names) { for (const name of names) requireReceipt(typeof value[name] === 'boolean'); }
function proofChecks(value) { exact(value, CHECKS); booleans(value, CHECKS); }
const allTrue = (value, names) => names.every(name => value[name] === true);
function fileFact(value, maximum = 67108864) {
  exact(value, ['sha256', 'bytes']);
  requireReceipt(digest(value.sha256) && integer(value.bytes, 1, maximum));
}
const equalFact = (a, b) => a !== null && b !== null && a.sha256 === b.sha256 && a.bytes === b.bytes;
function policy(step) {
  return freeze({ timeoutMs: step.stage === 'manifest' ? 30000 : 120000,
    stdoutCap: step.stage === 'compile' ? 65536 : step.stage === 'link' ? 16384 : 4096,
    stderrCap: 4096, drainMs: 5000 });
}

export function createWorkerArtifactCoordinatorV1(options) {
  const input = ownData(options, ['config', 'ports', 'clock']);
  const ports = ownData(input.ports, PORTS), clock = ownData(input.clock, ['set', 'clear']);
  if (!Object.values(ports).every(value => typeof value === 'function') ||
    !Object.values(clock).every(value => typeof value === 'function')) throw Error('WorkerArtifactCoordinatorV1Invalid');
  const recipe = planWorkerArtifactComparisonV1(input.config), recipeHash = sha(recipe);
  const clockSet = clock.set, clockClear = clock.clear, controller = new AbortController();
  const receipts = [], facts = { A: {}, B: {} };
  let used = false, terminal = false, cancelled = false, activeCancel = null;
  let context = null, attempted = 0, completed = 0, unknownClosure = false;
  const checkpoint = () => { if (cancelled) throw new Stop('CANCELLED'); };
  const abort = () => { try { controller.abort(); } catch { /* closure still requires a valid port receipt */ } };

  function timed(name, request, milliseconds) {
    return new Promise((resolve, reject) => {
      let done = false, offered = false, grace = false;
      const timers = [];
      const unknown = () => name === 'launchStep' && offered;
      const finish = (good, value) => {
        if (done) return;
        done = true;
        if (activeCancel === beginGrace) activeCancel = null;
        let clearFailed = false;
        for (const token of timers) { try { clockClear(token); } catch { clearFailed = true; } }
        // Preserve the first detected failure through subsequent cleanup faults.
        if (!good) reject(value);
        else if (clearFailed) reject(new Stop('PORT_ERROR', unknown()));
        else resolve(value);
      };
      const expire = code => { if (!done) { abort(); finish(false, new Stop(code, unknown())); } };
      const beginGrace = () => {
        if (done || grace) return;
        grace = true;
        try { timers.push(clockSet(() => expire(name === 'launchStep' ? 'CLOSURE' : 'CANCELLED'), 5000)); }
        catch { finish(false, new Stop('PORT_ERROR', unknown())); }
      };
      try { timers.push(clockSet(() => expire('PORT_TIMEOUT'), milliseconds)); }
      catch { reject(new Stop('PORT_ERROR')); return; }
      activeCancel = beginGrace;
      try {
        if (name === 'launchStep') { offered = true; attempted++; }
        const operation = ports[name];
        const pending = name === 'prepareManifest' ? operation(request, controller.signal) : operation(request);
        Promise.resolve(pending).then(value => finish(true, value),
          () => finish(false, new Stop('PORT_ERROR', unknown())));
      } catch { finish(false, new Stop('PORT_ERROR', unknown())); }
    });
  }

  function validate(name, value, request) {
    exact(value, [...COMMON, ...EXTRA[name]]);
    requireReceipt(value.version === 1 && value.kind === KINDS[name] &&
      ['attempt', 'recipe', 'baseline', 'closure'].every(key => nonzero(value[key])));
    if (name === 'admit') requireReceipt(value.recipe === recipeHash);
    else {
      requireReceipt(['attempt', 'recipe', 'baseline', 'closure'].every(key => value[key] === context[key]));
      requireReceipt(integer(value.index, 0, 6) && value.index === request.index);
    }
    if (name === 'admit' || name === 'recheck') {
      proofChecks(value.checks);
      if (name === 'admit') requireReceipt(value.runCount === 1);
      else requireReceipt(value.when === request.when);
    } else if (name === 'launchStep') {
      booleans(value, ['closed', 'unknown', 'timedOut', 'overflow', 'killAttempted', 'ioError', 'processTreeContained']);
      const p = request.policy;
      requireReceipt(value.processTreeContained === false && integer(value.pid, 1, 2147483647) &&
        (value.exitCode === null || integer(value.exitCode, -2147483648, 2147483647)) &&
        integer(value.elapsedMs, 0, p.timeoutMs + 5000) &&
        integer(value.stdoutBytes, 0, p.stdoutCap) && integer(value.stderrBytes, 0, p.stderrCap) &&
        digest(value.stdoutHash) && digest(value.stderrHash));
    } else if (name === 'inspectOutputs') {
      booleans(value, OUTPUT_FLAGS); fileFact(value.object);
      if (request.stage === 'compile') requireReceipt(value.executable === null && value.manifest === null);
      else { fileFact(value.executable); fileFact(value.manifest, 65536); }
    } else if (name === 'prepareManifest') {
      booleans(value, MANIFEST_FLAGS);
      fileFact(value.manifest, 65536); fileFact(value.preEmbed); fileFact(value.copy);
    } else booleans(value, COMPARE_FLAGS);
  }

  async function receive(name, request) {
    checkpoint();
    const milliseconds = name === 'launchStep' ? request.policy.timeoutMs + 5000 : 5000;
    const wire = await timed(name, request, milliseconds);
    try {
      const value = decode(wire);
      validate(name, value, request);
      requireReceipt(receipts.length < 30);
      receipts.push(freeze(value));
      return value;
    } catch { throw new Stop('RECEIPT', name === 'launchStep'); }
  }
  const stepRequest = (step, extra = {}) => freeze({ version: 1, context, index: step.index, step, ...extra });
  async function recheck(step, when) {
    const value = await receive('recheck', stepRequest(step, { when }));
    requireSemantic(allTrue(value.checks, CHECKS), 'RECHECK');
  }
  function report(code, firstCode = null) {
    return freeze({ version: 1, kind: 'worker_artifact_coordinator_report_v1',
      status: code === null ? 'passed' : code === 'CANCELLED' ? 'cancelled' : 'failed', code, firstCode,
      attempt: context?.attempt ?? null, recipe: recipeHash, baseline: context?.baseline ?? null,
      closure: context?.closure ?? null, attempted, completed, receipts: [...receipts], unknownClosure,
      qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true,
      normalWorkerUnchangedRequired: true, processTreeContained: false });
  }

  async function run() {
    if (used) throw Error('WorkerArtifactCoordinatorV1Used');
    used = true;
    let code = null;
    try {
      const admission = await receive('admit', freeze({ version: 1, recipe, recipeHash }));
      requireSemantic(allTrue(admission.checks, CHECKS), 'ADMISSION');
      context = freeze({ attempt: admission.attempt, recipe: admission.recipe,
        baseline: admission.baseline, closure: admission.closure });
      checkpoint();
      for (const step of recipe.steps) {
        const candidate = facts[step.candidate];
        await recheck(step, 'before'); checkpoint();
        if (step.stage === 'manifest') {
          const value = await receive('prepareManifest', stepRequest(step,
            { linked: { executable: candidate.linked, manifest: candidate.manifest } }));
          requireSemantic(allTrue(value, MANIFEST_FLAGS) && equalFact(value.manifest, candidate.manifest) &&
            equalFact(value.preEmbed, candidate.linked) && equalFact(value.copy, candidate.linked), 'MANIFEST');
          checkpoint();
          await recheck(step, 'manifest'); checkpoint();
        }
        const process = await receive('launchStep', Object.freeze({ version: 1, context, index: step.index,
          step, policy: policy(step), signal: controller.signal }));
        requireSemantic(process.closed && !process.unknown && !process.ioError, 'CLOSURE', true);
        requireSemantic(!process.timedOut && !process.overflow, 'PROCESS');
        checkpoint();
        requireSemantic(!process.killAttempted && process.exitCode === 0, 'PROCESS');
        const outputs = await receive('inspectOutputs', stepRequest(step, { stage: step.stage }));
        requireSemantic(allTrue(outputs, OUTPUT_FLAGS), 'OUTPUT');
        if (step.stage === 'compile') candidate.object = outputs.object;
        else {
          requireSemantic(equalFact(outputs.object, candidate.object), 'OUTPUT');
          if (step.stage === 'link') { candidate.linked = outputs.executable; candidate.manifest = outputs.manifest; }
          else {
            requireSemantic(equalFact(outputs.manifest, candidate.manifest), 'OUTPUT');
            candidate.final = outputs.executable;
          }
        }
        checkpoint();
        await recheck(step, 'after');
        completed++;
        checkpoint();
      }
      const comparison = await receive('compare', freeze({ version: 1, context, index: 6,
        candidates: ['A', 'B'].map(id => ({ id, object: facts[id].object, executable: facts[id].final })) }));
      requireSemantic(allTrue(comparison, COMPARE_FLAGS) && equalFact(facts.A.object, facts.B.object) &&
        equalFact(facts.A.final, facts.B.final), 'COMPARE');
      checkpoint();
    } catch (error) {
      code = error instanceof Stop ? error.code : 'PORT_ERROR';
      unknownClosure = error instanceof Stop && error.unknown;
    }
    terminal = true;
    let finalReport = report(code), retained = false;
    try {
      const acknowledgement = decode(await timed('record', finalReport, 5000));
      exact(acknowledgement, ['version', 'kind', 'retained', 'report']);
      requireReceipt(acknowledgement.version === 1 && acknowledgement.kind === 'worker_artifact_record_v1' &&
        acknowledgement.retained === true && acknowledgement.report === sha(finalReport));
      retained = true;
    } catch { finalReport = report('EVIDENCE', code); }
    return freeze({ report: finalReport, retained });
  }
  function cancel() {
    if (terminal || cancelled) return false;
    cancelled = true;
    if (activeCancel !== null) activeCancel();
    abort();
    return true;
  }
  return Object.freeze({ run, cancel });
}
