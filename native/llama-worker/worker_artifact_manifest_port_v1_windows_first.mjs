// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Fixed Windows development check. The owning collector must admit and supervise it.
import { createHash } from 'node:crypto';
import { lstat, mkdir, open, realpath } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { createWorkerArtifactManifestPortV1 } from './worker_artifact_manifest_port_v1.mjs';
import { createWorkerArtifactOutputRootsV1 } from './worker_artifact_output_roots_v1.mjs';
import { createWorkerArtifactPreembedCopyV1 } from './worker_artifact_preembed_copy_v1.mjs';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const TEMP = 'D:/Dev/_Temp';
const TARGET = TEMP + '/locallore-runtime-resource-manifest-port-v1-20261109-v1';
const MARKER = '.locallore-output-owner-v1';
const MAX = 350;
const DEADLINE = 5000;
const STOP = Symbol('Windows manifest selfcheck stopped');
const normalize = path => path.replaceAll('\\', '/').replace(/[A-Z]/g, character => character.toLowerCase());
const sha = value => createHash('sha256').update(value).digest('hex');
const config = Object.freeze({
  compiler: 'C:/locallore-manifest-synthetic-unaccessed/compiler/cl.exe',
  linker: 'C:/locallore-manifest-synthetic-unaccessed/linker/link.exe',
  manifestTool: 'C:/locallore-manifest-synthetic-unaccessed/manifest/mt.exe',
  workerRoot: 'D:/locallore-manifest-synthetic-unaccessed/worker',
  upstreamA: 'D:/locallore-manifest-synthetic-unaccessed/upstream-a',
  upstreamB: 'D:/locallore-manifest-synthetic-unaccessed/upstream-b',
  buildA: 'D:/locallore-manifest-synthetic-unaccessed/build-a',
  buildB: 'D:/locallore-manifest-synthetic-unaccessed/build-b',
  targetRoot: TARGET,
  sdkUmRoot: 'C:/locallore-manifest-synthetic-unaccessed/um'
});
const FIXTURE = Object.freeze([
  Object.freeze({ object: 'a', executable: 'A\n', manifest: 'ma\n' }),
  Object.freeze({ object: 'b', executable: 'B\n', manifest: 'mb\n' })
]);

function requireProof(condition) {
  if (!condition) throw STOP;
}

function identity(stat) {
  requireProof(typeof stat.dev === 'bigint' && stat.dev >= 0n &&
    typeof stat.ino === 'bigint' && stat.ino > 0n);
  return stat.dev.toString() + ':' + stat.ino.toString();
}

async function ordinaryDirectory(path) {
  const stat = await lstat(path, { bigint: true });
  requireProof(stat.isDirectory() && !stat.isSymbolicLink());
  requireProof(normalize(await realpath(path)) === normalize(path));
  return stat;
}

function ordinaryFile(stat, expectedIdentity, bytes) {
  requireProof(stat.isFile() && !stat.isSymbolicLink() && stat.nlink === 1n &&
    stat.size === BigInt(bytes) && identity(stat) === expectedIdentity);
}

async function withHandle(path, flags, use, markUnknown) {
  let handle;
  try {
    handle = await open(path, flags);
  } catch {
    markUnknown();
    throw STOP;
  }
  try {
    await use(handle);
  } finally {
    try {
      await handle.close();
    } catch {
      markUnknown();
      throw STOP;
    }
  }
}

async function writeFixture(path, content, markUnknown) {
  const data = Buffer.from(content, 'ascii');
  await withHandle(path, 'wx', async handle => {
    const result = await handle.write(data, 0, data.length, 0);
    requireProof(result.bytesWritten === data.length);
    await handle.sync();
    const held = await handle.stat({ bigint: true });
    ordinaryFile(held, identity(held), data.length);
    ordinaryFile(await lstat(path, { bigint: true }), identity(held), data.length);
  }, markUnknown);
}

async function readCopy(path, expectedIdentity, content, markUnknown) {
  const expected = Buffer.from(content, 'ascii');
  ordinaryFile(await lstat(path, { bigint: true }), expectedIdentity, expected.length);
  requireProof(normalize(await realpath(path)) === normalize(path));
  await withHandle(path, 'r', async handle => {
    ordinaryFile(await handle.stat({ bigint: true }), expectedIdentity, expected.length);
    const data = Buffer.alloc(expected.length);
    const result = await handle.read(data, 0, data.length, 0);
    const eof = await handle.read(Buffer.alloc(1), 0, 1, data.length);
    requireProof(result.bytesRead === expected.length && eof.bytesRead === 0 && data.equals(expected));
    ordinaryFile(await handle.stat({ bigint: true }), expectedIdentity, expected.length);
    ordinaryFile(await lstat(path, { bigint: true }), expectedIdentity, expected.length);
  }, markUnknown);
}

function expectedRows(candidate, fixture, stage) {
  const name = path => path.slice(candidate.outputRoot.length + 1);
  const rows = [[MARKER, '167']];
  if (stage > 0) {
    rows.push([name(candidate.object), String(fixture.object.length)]);
    rows.push([name(candidate.executable), String(fixture.executable.length)]);
    if (stage === 2) rows.push([name(candidate.preEmbedCopy), String(fixture.executable.length)]);
    rows.push([name(candidate.manifest), String(fixture.manifest.length)]);
  }
  return rows;
}

function verifyRoster(view, candidates, stages, bytes, rootIdentities) {
  requireProof(view.version === 1 && view.kind === 'worker_artifact_output_roots_v1' &&
    view.qualified === false && view.state === 'Ready' && view.pending === null && view.stop === null &&
    view.withinBudget === true && view.observedBytes === String(bytes) && view.roots.length === 2);
  for (const [index, candidate] of candidates.entries()) {
    const root = view.roots[index];
    requireProof(root.candidate === candidate.id && root.identity === rootIdentities[index] &&
      root.creation === 'created' && root.marker === 'created' && root.markerClosure === 'open' &&
      root.directoryClosure === 'closed' && root.complete === true &&
      JSON.stringify(root.files.map(file => [file.name, file.bytes])) ===
        JSON.stringify(expectedRows(candidate, FIXTURE[index], stages[index])));
  }
}

async function manifestReceipt(port, step, context, fixture, controller) {
  const executable = { sha256: sha(fixture.executable), bytes: fixture.executable.length };
  const manifest = { sha256: sha(fixture.manifest), bytes: fixture.manifest.length };
  const request = { version: 1, context, index: step.index, step, linked: { executable, manifest } };
  const started = performance.now();
  const timeout = setTimeout(() => controller.abort(), DEADLINE);
  let wire;
  try {
    wire = await port.prepareManifest(request, controller.signal);
  } finally {
    clearTimeout(timeout);
    if (performance.now() - started >= DEADLINE) controller.abort();
  }
  requireProof(!controller.signal.aborted);
  const expected = { version: 1, kind: 'worker_artifact_manifest_v1', ...context, index: step.index,
    ordinary: true, exclusive: true, equal: true, withinBudget: true, manifest,
    preEmbed: executable, copy: executable };
  requireProof(wire === JSON.stringify(expected));
}

export async function runWorkerArtifactManifestWindowsSelfchecksV1(...args) {
  let phase = 'preflight', failure = null, bytes = 0, receipts = 0, knownClosed = true;
  let lease = null, copy = null, port = null, finalRoster = null;
  const rosters = [];
  const markUnknown = () => { knownClosed = false; };

  try {
    requireProof(args.length === 0 && process.platform === 'win32' &&
      [process.env.TEMP, process.env.TMP].every(path => typeof path === 'string' && normalize(path) === normalize(TEMP)));
    // Node ordinary-file and realpath checks complement the owner's Windows attribute checks.
    for (const ancestor of ['D:/', 'D:/Dev', TEMP]) await ordinaryDirectory(ancestor);
    const recipe = planWorkerArtifactComparisonV1(config);
    const context = Object.freeze({
      attempt: sha('worker artifact manifest Windows v1 fixed synthetic attempt 20261109'),
      recipe: sha(JSON.stringify(recipe)),
      baseline: sha('worker artifact manifest Windows v1 synthetic baseline'),
      closure: sha('worker artifact manifest Windows v1 synthetic closure')
    });

    phase = 'parent';
    await mkdir(TARGET, { recursive: false });
    const parentIdentity = identity(await ordinaryDirectory(TARGET));

    phase = 'prepare';
    lease = createWorkerArtifactOutputRootsV1({ config, attemptSha256: context.attempt, parentIdentity, maxBytes: MAX });
    copy = createWorkerArtifactPreembedCopyV1({ config });
    port = createWorkerArtifactManifestPortV1({ config, context, outputRoots: lease, preembedCopy: copy, maxBytes: MAX });
    const prepared = await lease.prepare();
    const rootIdentities = prepared.roots.map(root => root.identity);
    const stages = [0, 0];
    function recordRoster(view, expectedBytes) {
      verifyRoster(view, recipe.candidates, stages, expectedBytes, rootIdentities);
      rosters.push(expectedBytes);
      bytes = expectedBytes;
      finalRoster = view;
    }
    recordRoster(prepared, 334);

    const controller = new AbortController();
    for (const [index, candidate] of recipe.candidates.entries()) {
      const suffix = index === 0 ? 'a' : 'b';
      const fixture = FIXTURE[index];
      phase = 'fixture-' + suffix;
      requireProof(identity(await ordinaryDirectory(TARGET)) === parentIdentity &&
        identity(await ordinaryDirectory(candidate.outputRoot)) === rootIdentities[index]);
      for (const [role, content] of Object.entries(fixture)) {
        await writeFixture(candidate[role], content, markUnknown);
      }
      phase = 'before-' + suffix;
      stages[index] = 1;
      recordRoster(await lease.recheck(), index === 0 ? 340 : 348);

      phase = 'manifest-' + suffix;
      await manifestReceipt(port, recipe.steps[2 + 3 * index], context, fixture, controller);
      receipts++;

      phase = 'after-' + suffix;
      stages[index] = 2;
      recordRoster(await lease.recheck(), index === 0 ? 342 : 350);
    }

    phase = 'readback';
    for (const [index, candidate] of recipe.candidates.entries()) {
      requireProof(identity(await ordinaryDirectory(TARGET)) === parentIdentity &&
        identity(await ordinaryDirectory(candidate.outputRoot)) === rootIdentities[index]);
      const name = candidate.preEmbedCopy.slice(candidate.outputRoot.length + 1);
      const row = finalRoster.roots[index].files.find(file => file.name === name);
      requireProof(row?.bytes === '2');
      await readCopy(candidate.preEmbedCopy, row.identity, FIXTURE[index].executable, markUnknown);
    }
  } catch {
    failure = phase;
  } finally {
    let settled = true;
    try {
      if (port) {
        const view = await port.drain();
        settled = view.pending === null;
        if (!settled || view.uncertain) markUnknown();
        if (failure === null && (!settled || view.uncertain || view.stop !== null || view.completed !== 2)) {
          failure = 'settlement';
        }
      }
      if (copy) {
        const view = copy.snapshot();
        settled = settled && !view.busy;
        if (!settled || view.unknownClosure || view.ioUncertain) markUnknown();
        if (failure === null && (!settled || view.unknownClosure || view.ioUncertain || view.stopped ||
          view.nextCandidate !== null)) failure = 'settlement';
      }
    } catch {
      settled = false;
      markUnknown();
      failure ??= 'settlement';
    }

    if (lease && settled) {
      try {
        const closed = await lease.close();
        requireProof(closed.state === 'Closed' && closed.pending === null && closed.roots.length === 2 &&
          closed.roots.every(root => (root.marker === 'created' ? root.markerClosure === 'closed' :
            root.marker === 'unattempted' && root.markerClosure === 'none') &&
            ['none', 'closed'].includes(root.directoryClosure)));
      } catch {
        markUnknown();
        failure ??= 'close';
      }
    } else if (!settled) {
      markUnknown();
      failure ??= 'settlement';
    }
  }

  const passed = failure === null && knownClosed && receipts === 2 && bytes === MAX;
  return Object.freeze({ version: 1, kind: 'worker_artifact_manifest_windows_v1', passed,
    phase: passed ? 'closed' : failure ?? 'settlement', bytes, rosters: Object.freeze(rosters), receipts, knownClosed });
}
