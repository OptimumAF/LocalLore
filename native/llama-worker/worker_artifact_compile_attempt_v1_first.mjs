// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { verifyWorkerArtifactCompileParentReadyV1 as verify,
  workerArtifactCompileAttemptScopeV1 as scope } from './worker_artifact_compile_attempt_v1.mjs';

const hash = value => createHash('sha256').update(value).digest('hex');
const id = (n, volume = 7) => volume + ':' + n.toString(16).padStart(32, '0');
const profile = {
  config: {
    compiler: 'C:/Build Tools/cl.exe', linker: 'C:/Build Tools/link.exe',
    manifestTool: 'C:/Build Tools/mt.exe', workerRoot: 'D:/worker source',
    upstreamA: 'D:/upstream A', upstreamB: 'D:/upstream B', buildA: 'D:/build A',
    buildB: 'D:/build B', targetRoot: 'D:/outputs', sdkUmRoot: 'C:/SDK/um/x64'
  },
  authority: { attempt: hash('attempt'), baseline: hash('baseline'), closure: hash('closure'), grant: hash('grant') },
  environment: { windows: 'C:/Windows', path: 'C:/Build Tools;C:/Windows/System32',
    include: 'C:/SDK/include;D:/fixture headers', temp: 'D:/temp fixture' },
  node: { path: 'D:/Node fixture/node.exe', bytes: 613, sha256: hash('Node fixture bytes') },
  helper: { path: 'D:/Helper fixture/locallore-compile-host-v1.exe', bytes: 421, sha256: hash('helper fixture bytes') },
  entry: 'D:/Entry fixture/worker_artifact_compile_attempt_v1.mjs', evidenceRoot: 'D:/evidence fixture',
  outputParentIdentity: '7:33', outputMaxBytes: 67108864,
  spend: hash('spent grant'), writerPolicy: hash('writer policy'), namespace: hash('namespace')
};
const observed = { pid: 103, ppid: 101, entryBytes: 2048, entrySha256: hash('entry fixture bytes') };
const ready = {
  version: 1, kind: 'compile_parent_ready_v1', scope: scope(profile), spend: profile.spend,
  writerPolicy: profile.writerPolicy, namespace: profile.namespace,
  evidenceId: id(1), tempId: id(2), parentPid: observed.ppid, nodePid: observed.pid,
  jobFlags: 0x2000, parentInJob: false, activeProcesses: 1,
  pins: [
    { id: id(3), sha256: profile.node.sha256, bytes: profile.node.bytes },
    { id: id(4), sha256: observed.entrySha256, bytes: observed.entryBytes },
    { id: id(5), sha256: profile.helper.sha256, bytes: profile.helper.bytes }
  ]
};
const wire = JSON.stringify(ready);
const refuseReady = patch => assert.throws(() => verify(JSON.stringify({ ...ready, ...patch }), profile, observed));
const refuseProfile = patch => assert.throws(() => scope({ ...profile, ...patch }));

const cases = [
  ['positive exact wire', () => {
    const verified = verify(wire, profile, observed);
    assert.equal(verified.readyHash, hash(wire));
    assert.equal(verified.scope, ready.scope);
    assert.equal(verified.context.attempt, profile.authority.attempt);
    assert(Object.isFrozen(verified.profile.config));
    assert(Object.isFrozen(verified.ready.pins[0]));
  }],
  ['stable scope under input key order', () => {
    const reverse = value => Object.fromEntries(Object.entries(value).reverse());
    assert.equal(scope(reverse({ ...profile, config: reverse(profile.config),
      authority: reverse(profile.authority), environment: reverse(profile.environment) })), ready.scope);
  }],
  ['scope changes when retained bindings or paths change', () => {
    for (const patch of [{ spend: hash('other spend') }, { writerPolicy: hash('other policy') },
      { namespace: hash('other namespace') }, { outputMaxBytes: 8192 }, { outputParentIdentity: '7:34' },
      { config: { ...profile.config, workerRoot: 'D:/other worker source' } },
      { environment: { ...profile.environment, include: 'C:/other include' } },
      { authority: { ...profile.authority, grant: hash('another grant') } }])
      assert.notEqual(scope({ ...profile, ...patch }), ready.scope);
  }],
  ['replaced READY authorization', () => {
    for (const field of ['scope', 'spend', 'writerPolicy', 'namespace'])
      refuseReady({ [field]: hash('stale ' + field) });
  }],
  ['wrong and ambiguous pids', () => {
    refuseReady({ parentPid: 102 });
    refuseReady({ nodePid: 102 });
    assert.throws(() => verify(wire, profile, { ...observed, ppid: observed.pid }));
    assert.throws(() => verify(wire, profile, { ...observed, pid: '103' }));
  }],
  ['job state exact', () => {
    refuseReady({ jobFlags: 0x2800 });
    refuseReady({ activeProcesses: 2 });
    refuseReady({ parentInJob: 'false' });
    assert.equal(verify(JSON.stringify({ ...ready, parentInJob: true }), profile, observed).ready.parentInJob, true);
  }],
  ['entry actual length and digest', () => {
    assert.throws(() => verify(wire, profile, { ...observed, entrySha256: hash('changed entry') }));
    assert.throws(() => verify(wire, profile, { ...observed, entryBytes: observed.entryBytes + 1 }));
  }],
  ['node, helper, and order are fixed', () => {
    refuseReady({ pins: [...ready.pins].reverse() });
    refuseReady({ pins: [ready.pins[0], ready.pins[1], { ...ready.pins[2], bytes: 422 }] });
    refuseReady({ pins: [{ ...ready.pins[0], sha256: hash('other node') }, ...ready.pins.slice(1)] });
  }],
  ['distinct native identities on one volume', () => {
    refuseReady({ evidenceId: ready.tempId });
    refuseReady({ tempId: id(2, 8) });
    refuseReady({ evidenceId: id(0) });
    refuseReady({ evidenceId: '07:' + '1'.repeat(32) });
    refuseReady({ evidenceId: '18446744073709551616:' + '1'.repeat(32) });
  }],
  ['canonical bounded wire', () => {
    for (const text of [wire + '\n', ' '.repeat(4096) + wire,
      wire.replace('"version":1', '"version":1,"version":1'),
      JSON.stringify({ ...Object.fromEntries(Object.entries(ready).reverse()) })])
      assert.throws(() => verify(text, profile, observed));
    refuseReady({ extra: true });
  }],
  ['canonical profile and leaf paths', () => {
    refuseProfile({ spend: profile.spend + '\n' });
    refuseProfile({ entry: 'D:/Entry fixture/other.mjs' });
    refuseProfile({ evidenceRoot: 'D:/outputs/evidence' });
    refuseProfile({ environment: { ...profile.environment, temp: 'D:/Helper fixture/temp' } });
    refuseProfile({ environment: { ...profile.environment, path: 'C:/Build Tools;' } });
    refuseProfile({ evidenceRoot: 'D:/CONIN$/evidence' });
    refuseProfile({ evidenceRoot: 'D:/bad\uD800/evidence' });
  }],
  ['budget limits and Node output-parent identity', () => {
    refuseProfile({ outputMaxBytes: 333 });
    refuseProfile({ outputMaxBytes: 67108865 });
    refuseProfile({ outputParentIdentity: '7:0' });
    refuseProfile({ outputParentIdentity: id(1) });
  }]
];

for (const [name, run] of cases) {
  try { run(); } catch (error) { throw Error(name, { cause: error }); }
}
process.stdout.write(JSON.stringify({ kind: 'compile_attempt_first_v1', groups: cases.length }) + '\n');
