// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
// Independent Windows Node-filesystem FIRST, contract97012224. ALL2 UNRUN.
// No filesystem helper/import/fixture creation: ONLY the supplied production
// factory may read the separately admitted, already-created original D: fixture.
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';

const PIN = ['slot', 'kind', 'path', 'root', 'bytes', 'sha256', 'rootIdentity', 'leafIdentity'];
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const digest = value => sha(Buffer.from(JSON.stringify(value)));
const eq = (a, b) => assert.deepEqual(a, b);
const payload = () => Buffer.from('LocalLoreWindowsInputFixtureV1\n', 'utf8');
function own(value, names) {
  if (value === null || typeof value !== 'object' || ![Object.prototype, null].includes(Object.getPrototypeOf(value))) throw Error('UNRUN_SETUP');
  const keys = Reflect.ownKeys(value); if (keys.length !== names.length || keys.some(k => typeof k !== 'string' || !names.includes(k))) throw Error('UNRUN_SETUP');
  return Object.fromEntries(names.map(key => {
    const descriptor = Object.getOwnPropertyDescriptor(value, key);
    if (!descriptor || !descriptor.enumerable || !Object.hasOwn(descriptor, 'value')) throw Error('UNRUN_SETUP');
    return [key, descriptor.value];
  }));
}
function completeIO(n) {
  return { reservedInputs: 1, reservedBytes: n, reservedReadBytes: 2 * n, actualReadBytes: 2 * n,
    openAttempts: 1, opened: 1, closeAttempts: 1, closed: 1, verifiedScans: 2, unknownClosures: 0 };
}
function summary(executed, passed, failed_case_ids) {
  return { version: 1, kind: 'worker_artifact_windows_inputs_native_first_v1', executed, passed,
    failed: failed_case_ids.length, failed_case_ids };
}
function frozen(value) {
  if (value !== null && typeof value === 'object') { assert(Object.isFrozen(value)); Object.values(value).forEach(frozen); }
}

export async function runWorkerArtifactWindowsInputsNativeSelfchecksV1(api, fixtureSpec) {
  if (process.platform !== 'win32') throw Error('UNRUN_PLATFORM: Windows filesystem FIRST requires win32');
  const methods = own(api, ['createWorkerArtifactWindowsInputsV1']), fixture = own(fixtureSpec, ['pin']);
  const pin = own(fixture.pin, PIN), expected = payload();
  if (typeof methods.createWorkerArtifactWindowsInputsV1 !== 'function' || pin.slot !== 1 || pin.kind !== 'project' ||
      typeof pin.path !== 'string' || !pin.path.startsWith('D:/') || typeof pin.root !== 'string' || !pin.root.startsWith('D:/') ||
      pin.bytes !== expected.length || pin.sha256 !== sha(expected) || typeof pin.rootIdentity !== 'string' || typeof pin.leafIdentity !== 'string') {
    throw Error('UNRUN_SETUP: original precreated D: fixture required');
  }
  const create = methods.createWorkerArtifactWindowsInputsV1;
  let firstReader;
  try { firstReader = create({ pins: [{ ...pin }] }); }
  catch { throw Error('UNRUN_SETUP: production factory rejected fixture setup'); }
  try {
    const reader = firstReader, result = await reader.readNext();
    assert(Buffer.isBuffer(result.buffer)); assert(result.buffer.equals(expected)); assert(Object.isFrozen(result));
    eq(result.proof, { version: 1, kind: 'worker_artifact_windows_input_v1', slot: 1, role: 'project',
      bytes: pin.bytes, sha256: pin.sha256, pinHash: digest(pin),
      identityHash: digest({ root: pin.rootIdentity, leaf: pin.leafIdentity, bytes: pin.bytes }), io: completeIO(pin.bytes),
      qualified: false, linkQualification: false, closureComplete: false, requiresFreshAdmission: true });
    frozen(result.proof);
    const snapshot = reader.snapshot(); assert.equal(snapshot.status, 'complete'); assert.equal(snapshot.critical, null);
    frozen(snapshot);
    for (const key of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(snapshot[key], false);
    assert.equal(snapshot.requiresFreshAdmission, true);
    assert.equal(snapshot.completedInputs, 1); eq(snapshot.io, completeIO(pin.bytes)); assert.equal(reader.cancel(), false);
  } catch { return summary(1, 0, ['N01']); } // N02 is UNRUN, never a retry after unexpected filesystem failure.
  try {
    const wrong = { ...pin, sha256: (pin.sha256[0] === '0' ? '1' : '0') + pin.sha256.slice(1) };
    assert.notEqual(wrong.sha256, pin.sha256);
    const reader = create({ pins: [wrong] }); await assert.rejects(() => reader.readNext(), { message: 'IdentityFailure' });
    const snapshot = reader.snapshot(); assert.equal(snapshot.status, 'stopped'); assert.equal(snapshot.critical, 'IdentityFailure');
    frozen(snapshot);
    for (const key of ['qualified', 'linkQualification', 'closureComplete']) assert.equal(snapshot[key], false);
    assert.equal(snapshot.requiresFreshAdmission, true);
    assert.equal(snapshot.completedInputs, 0); assert.equal(snapshot.lastProof, null);
    eq(snapshot.io, { ...completeIO(pin.bytes), actualReadBytes: pin.bytes, verifiedScans: 0 });
    assert.equal(reader.cancel(), false);
  } catch { return summary(2, 1, ['N02']); }
  return summary(2, 2, []);
}
