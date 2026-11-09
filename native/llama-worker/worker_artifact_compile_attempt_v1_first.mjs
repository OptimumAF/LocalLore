// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { verifyWorkerArtifactCompileParentReadyV1 as verify,
  workerArtifactCompileAttemptScopeV1 as scope } from './worker_artifact_compile_attempt_v1.mjs';
import { workerArtifactCompileInputCatalogV1 as inputCatalog } from './worker_artifact_compile_checks_v1.mjs';

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
  spend: hash('spent grant'), writerPolicy: hash('writer policy'), namespace: hash('namespace'),
  inputCatalog: hash('fixed input catalog')
};
const observed = { pid: 103, ppid: 101, entryBytes: 2048, entrySha256: hash('entry fixture bytes') };
const ready = {
  version: 1, kind: 'compile_parent_ready_v1', scope: scope(profile), spend: profile.spend,
  writerPolicy: profile.writerPolicy, namespace: profile.namespace, inputCatalog: profile.inputCatalog,
  inputSeal: hash('actual native seal'), inputFiles: 4, absenceSlots: 1,
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
    for (const field of ['scope', 'spend', 'writerPolicy', 'namespace', 'inputCatalog'])
      refuseReady({ [field]: hash('stale ' + field) });
  }],
  ['native input seal and bounds', () => {
    refuseReady({ inputSeal: '0'.repeat(64) });
    refuseReady({ inputFiles: 3 });
    refuseReady({ inputFiles: 1025 });
    refuseReady({ absenceSlots: 0 });
    refuseReady({ absenceSlots: 2049 });
    assert.notEqual(scope({ ...profile, inputCatalog: hash('different input catalog') }), ready.scope);
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
  ['canonical UTF-8 input catalog', () => {
    const bounds = identity => ({ identity, maxBytes: 8192, maxEntries: 20,
      maxDepth: 2, pending: { admit: 4096, before: 4096, after: 0 } });
    const manifest = {
      topology: 'a'.repeat(64),
      pins: [
        { role: 'source', path: 'D:/worker source/main.cpp', identity: '7:11', bytes: 1, sha256: 'b'.repeat(64) },
        { role: 'headers', path: 'C:/SDK/include/café.hpp', identity: '8:12', bytes: 2, sha256: 'c'.repeat(64) },
        { role: 'tool', path: 'C:/Build Tools/cl.exe', identity: '8:13', bytes: 3, sha256: 'd'.repeat(64) },
        { role: 'normal', path: 'D:/normal fixture/normal.exe', identity: '7:14', bytes: 4, sha256: 'e'.repeat(64) }
      ],
      absent: [{ path: 'C:/Build Tools/cl.exe.extra', parentIdentity: '8:15' }],
      roots: { temp: bounds('7:1'), target: bounds('7:2'), evidence: bounds('7:3') },
      diskFloor: 1048576
    };
    const fixed = '05438523f3bd48325c9a85c557641abf30aacc5eb10543d2345dba1e28d3c838';
    assert.equal(inputCatalog(manifest, 'D:/outputs'), fixed);
    assert.notEqual(inputCatalog({ ...manifest, pins: [...manifest.pins].reverse() }, 'D:/outputs'), fixed);
    assert.notEqual(inputCatalog(manifest, 'D:/other outputs'), fixed);
    const header = manifest.pins[1];
    assert.notEqual(inputCatalog({ ...manifest, pins: [manifest.pins[0],
      { ...header, path: 'C:/SDK/include/cafe.hpp' }, ...manifest.pins.slice(2)] }, 'D:/outputs'), fixed);
    assert.throws(() => inputCatalog({ ...manifest, absent: [{ ...manifest.absent[0], path: 'C:/SDK/x.lib' }] }, 'D:/outputs'));
    assert.throws(() => inputCatalog({ ...manifest, absent: [{ ...manifest.absent[0],
      path: 'C:/SDK/' + '\u00e9'.repeat(128) }] }, 'D:/outputs'));
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
