// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const files = [
  'library_inputs.mjs', 'worker_artifact_recipe_v1.mjs', 'worker_artifact_output_roots_v1.mjs',
  'worker_artifact_held_outputs_v1.mjs', 'worker_artifact_held_outputs_v1_first.mjs',
  'worker_artifact_compile_observation_v1.mjs', 'worker_artifact_compile_observation_v1_first.mjs',
  'worker_artifact_compile_host_v1.mjs', 'worker_artifact_compile_supervisor_v1.mjs',
  'worker_artifact_compile_attempt_v1.mjs', 'worker_artifact_compile_attempt_v1_first.mjs'
];

const sourceRoot = join(process.cwd(), 'native', 'llama-worker');
const allowed = [fileURLToPath(import.meta.url), ...files.map(name => join(sourceRoot, name))];
const flags = new Set(['--permission', ...allowed.map(name => '--allow-fs-read=' + name)]);
if (process.platform !== 'win32' || process.arch !== 'x64' || process.versions.node !== '24.22.1' ||
    process.argv.length !== 2 || process.execArgv.length !== flags.size ||
    new Set(process.execArgv).size !== flags.size || !process.execArgv.every(flag => flags.has(flag)) ||
    !process.permission || !allowed.every(name => process.permission.has('fs.read', name)) ||
    ['fs.write', 'child', 'worker', 'addon', 'wasi', 'inspector'].some(scope => process.permission.has(scope))) {
  throw Error('CompileStackCodePermission');
}

function load(name) {
  if (!files.includes(name)) throw Error('CompileStackCodeSource');
  return import(pathToFileURL(join(sourceRoot, name)).href);
}

function emit(summary, kind, count) {
  process.stdout.write(JSON.stringify(summary) + '\n');
  return summary.version === 1 && summary.kind === kind && summary.executed === count &&
    summary.passed === count && summary.failed === 0 &&
    Array.isArray(summary.failed_case_ids) && summary.failed_case_ids.length === 0;
}

const held = await load('worker_artifact_held_outputs_v1.mjs');
const heldFirst = await load('worker_artifact_held_outputs_v1_first.mjs');
if (!emit(await heldFirst.runWorkerArtifactHeldOutputsSelfchecksV1({ ...held }),
          'worker_artifact_held_outputs_first_v1', 14)) {
  process.exitCode = 1;
} else {
  const observation = await load('worker_artifact_compile_observation_v1.mjs');
  const observationFirst = await load('worker_artifact_compile_observation_v1_first.mjs');
  if (!emit(await observationFirst.runWorkerArtifactCompileObservationSelfchecksV1({ ...observation }),
            'worker_artifact_compile_observation_first_v1', 11)) {
    process.exitCode = 1;
  } else {
    await load('worker_artifact_compile_attempt_v1_first.mjs');
  }
}
