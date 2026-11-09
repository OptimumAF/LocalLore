// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
import { createHash } from 'node:crypto';
import { lstat, open, opendir, realpath, statfs } from 'node:fs/promises';
import { performance } from 'node:perf_hooks';
import { planWorkerArtifactComparisonV1 } from './worker_artifact_recipe_v1.mjs';

const ROLES = ['source', 'headers', 'tool', 'normal'];
const PHASES = ['admit', 'before', 'after'];
const ROOTS = ['temp', 'target', 'evidence'];
const CONTEXT = ['attempt', 'recipe', 'baseline', 'closure', 'grant'];
const LIMIT = 4 * 1024 ** 3;
const EVIDENCE = Object.freeze({
  'parent-ready.json': 4096, 'check-admit.json': 4096, 'START.json': 4096,
  'check-before.json': 4096, 'OFFER.json': 4096, 'request.bin': 65548,
  'response.bin': 69712, 'stderr.bin': 4096, 'transport.json': 4096, 'CAPTURE.json': 4096,
  'check-after.json': 4096, 'terminal.json': 16384
});
const EVIDENCE_COUNT = [1, 3, 10];
const MARKER = '.locallore-output-owner-v1';
const statOptions = { bigint: true };
const aborted = Object.getOwnPropertyDescriptor(AbortSignal.prototype, 'aborted').get;

const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const hash = value => sha(JSON.stringify(value));
const digest = value => typeof value === 'string' && value.length === 64 &&
  !/[^0-9a-f]/.test(value) && value !== '0'.repeat(64);
const int = (value, lo, hi) => Number.isSafeInteger(value) && value >= lo && value <= hi;
const norm = value => value.replaceAll('\\', '/').toLowerCase();
const inside = (path, root) => norm(path).startsWith(norm(root) + '/');
const id = stat => stat.dev.toString() + ':' + stat.ino.toString();
const stamp = stat => [id(stat), stat.size, stat.mode, stat.mtimeNs, stat.ctimeNs].join(':');
const parent = value => value.slice(0, value.lastIndexOf('/'));

function requireCheck(ok) {
  if (!ok) throw Error('WorkerArtifactCompileChecksV1');
}

function data(value, keys) {
  requireCheck(value !== null && typeof value === 'object' &&
    [Object.prototype, null].includes(Object.getPrototypeOf(value)));
  const own = Reflect.ownKeys(value);
  requireCheck(own.length === keys.length && own.every(key => keys.includes(key)));
  return Object.fromEntries(keys.map(key => {
    const property = Object.getOwnPropertyDescriptor(value, key);
    requireCheck(property?.enumerable && Object.hasOwn(property, 'value'));
    return [key, property.value];
  }));
}

function array(value, maximum) {
  requireCheck(Array.isArray(value) && value.length <= maximum && Reflect.ownKeys(value).length === value.length + 1);
  return Array.from({ length: value.length }, (_, index) => {
    const field = Object.getOwnPropertyDescriptor(value, index);
    requireCheck(field?.enumerable && Object.hasOwn(field, 'value'));
    return field.value;
  });
}

function leaf(value) {
  return typeof value === 'string' && value.length > 0 && Buffer.byteLength(value) <= 255 &&
    Buffer.from(value).toString('utf8') === value && !/[\x00-\x1f\x7f:\\/"*?<>|]/.test(value) &&
    !/[ .]$/.test(value) &&
    !/^(?:con|prn|aux|nul|conin\$|conout\$|(?:com|lpt)[1-9¹²³])$/i.test(value.split('.')[0].trimEnd());
}

function path(value) {
  requireCheck(typeof value === 'string' && Buffer.byteLength(value) <= 1024 &&
    /^[CD]:\//.test(value) && value.slice(3).split('/').every(leaf));
  return value;
}

function identity(value) {
  requireCheck(typeof value === 'string' && value.length <= 41 &&
    /^(?:0|[1-9][0-9]{0,19}):[1-9][0-9]{0,19}$/.test(value) && !/[^0-9:]/.test(value));
  return value;
}

function setup(manifest) {
  const spec = data(manifest, ['pins', 'absent', 'topology', 'roots', 'diskFloor']);
  requireCheck(digest(spec.topology) && int(spec.diskFloor, 1048576, LIMIT));
  const seen = new Set(), identities = new Set();
  let readBytes = 0;
  const pins = array(spec.pins, 1024).map(value => {
    const pin = data(value, ['role', 'path', 'identity', 'bytes', 'sha256']);
    requireCheck(ROLES.includes(pin.role) && !seen.has(norm(path(pin.path))) &&
      !identities.has(identity(pin.identity)) && int(pin.bytes, 1, 128 * 1024 ** 2) && digest(pin.sha256) &&
      !/\.(?:lib|gguf)$/i.test(pin.path));
    seen.add(norm(pin.path));
    identities.add(pin.identity);
    readBytes += pin.bytes + 1;
    requireCheck(readBytes <= 512 * 1024 ** 2);
    return Object.freeze(pin);
  });
  const absent = array(spec.absent, 2048).map(value => {
    const slot = data(value, ['path', 'parentIdentity']);
    requireCheck(path(slot.path).slice(3).includes('/') && !seen.has(norm(slot.path)));
    identity(slot.parentIdentity);
    seen.add(norm(slot.path));
    return Object.freeze(slot);
  });
  requireCheck(absent.length > 0 && ROLES.every(role => pins.some(pin => pin.role === role)) &&
    pins.filter(pin => pin.role === 'normal').length === 1);
  const rootConfig = data(spec.roots, ROOTS);
  const roots = ROOTS.map(role => {
    const root = data(rootConfig[role], ['identity', 'maxBytes', 'maxEntries', 'maxDepth', 'pending']);
    identity(root.identity);
    const pending = Object.freeze(data(root.pending, PHASES));
    requireCheck(int(root.maxBytes, 1, LIMIT) && int(root.maxEntries, 1, 512) && int(root.maxDepth, 1, 8) &&
      PHASES.every(phase => int(pending[phase], 0, root.maxBytes)));
    return Object.freeze({ role, ...root, pending });
  });
  requireCheck(new Set(roots.map(root => root.identity)).size === ROOTS.length &&
    roots.every(root => root.identity.split(':')[0] === roots[0].identity.split(':')[0]));
  return Object.freeze({ pins: Object.freeze(pins), absent: Object.freeze(absent), roots: Object.freeze(roots),
    topology: spec.topology, diskFloor: spec.diskFloor });
}

function ioFor(sourceSignal) {
  const signal = AbortSignal.any([sourceSignal]), start = performance.now();
  let last = start;
  function live() {
    const now = performance.now();
    requireCheck(!aborted.call(signal) && Number.isFinite(now) && now >= last && now - start < 10000);
    last = now;
  }
  async function checked(call) {
    live();
    const result = await call();
    live();
    return result;
  }
  async function named(file, directory) {
    const stat = await checked(() => lstat(file, statOptions));
    requireCheck(stat.ino > 0n && !stat.isSymbolicLink() &&
      (directory ? stat.isDirectory() : stat.isFile() && stat.nlink === 1n) &&
      norm(await checked(() => realpath(file))) === norm(file));
    return stat;
  }
  async function pinned(pin, block) {
    const namedBefore = await named(pin.path, false);
    requireCheck(id(namedBefore) === pin.identity && namedBefore.size === BigInt(pin.bytes));
    const expected = stamp(namedBefore);
    live();
    const sha = createHash('sha256');
    const file = await open(pin.path, 'r');
    let actual;
    try {
      const held = await checked(() => file.stat(statOptions));
      requireCheck(held.isFile() && held.nlink === 1n && stamp(held) === expected);
      for (let offset = 0; offset < pin.bytes;) {
        const count = Math.min(block.length, pin.bytes - offset);
        const { bytesRead } = await checked(() => file.read(block, 0, count, offset));
        requireCheck(int(bytesRead, 1, count));
        sha.update(block.subarray(0, bytesRead));
        offset += bytesRead;
      }
      requireCheck((await checked(() => file.read(block, 0, 1, pin.bytes))).bytesRead === 0);
      actual = sha.digest('hex');
      requireCheck(actual === pin.sha256 && stamp(await checked(() => file.stat(statOptions))) === expected);
    } finally {
      await file.close();
    }
    requireCheck(stamp(await named(pin.path, false)) === expected);
    return { path: pin.path, identity: pin.identity, bytes: pin.bytes, sha256: actual };
  }
  async function missing(slot) {
    const folder = parent(slot.path);
    const before = await named(folder, true);
    requireCheck(id(before) === slot.parentIdentity);
    try {
      await checked(() => lstat(slot.path, statOptions));
      requireCheck(false);
    } catch (error) {
      requireCheck(error?.code === 'ENOENT');
    }
    requireCheck(stamp(await named(folder, true)) === stamp(before));
    return slot;
  }
  async function inventory(root, phase) {
    const rows = [], seen = new Set([root.identity]);
    const device = root.identity.split(':')[0];
    let total = 0n;
    async function walk(folder, relative, depth, expectedId) {
      const before = await named(folder, true);
      requireCheck(id(before) === expectedId);
      live();
      const directory = await opendir(folder);
      try {
        for (;;) {
          const entry = await checked(() => directory.read());
          if (entry === null) break;
          requireCheck(rows.length < root.maxEntries && depth < root.maxDepth && leaf(entry.name) &&
            !entry.isSymbolicLink() && (entry.isDirectory() || entry.isFile()));
          const next = folder + '/' + entry.name;
          const rowPath = relative ? relative + '/' + entry.name : entry.name;
          const isDirectory = entry.isDirectory();
          const stat = await named(next, isDirectory);
          const key = id(stat);
          requireCheck(stat.dev.toString() === device && !seen.has(key));
          seen.add(key);
          const bytes = isDirectory ? 0n : stat.size;
          requireCheck(bytes >= 0n);
          total += bytes;
          requireCheck(total <= BigInt(root.maxBytes));
          rows.push({ name: rowPath, identity: key, directory: isDirectory, bytes: bytes.toString() });
          if (isDirectory) await walk(next, rowPath, depth + 1, key);
        }
      } finally {
        await directory.close();
      }
      requireCheck(stamp(await named(folder, true)) === stamp(before));
    }
    await walk(root.path, '', 0, root.identity);
    const pending = root.pending[phase];
    requireCheck(total + BigInt(pending) <= BigInt(root.maxBytes));
    rows.sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
    return { role: root.role, identity: root.identity, bytes: total.toString(), pending, rows };
  }
  async function available(root) {
    const info = await checked(() => statfs(root, statOptions));
    requireCheck(typeof info.bsize === 'bigint' && typeof info.bavail === 'bigint' &&
      info.bsize > 0n && info.bsize <= 1048576n && info.bavail >= 0n && info.bavail <= (1n << 64n) - 1n);
    return info.bsize * info.bavail;
  }
  return { pinned, missing, inventory, available, live };
}

function checkTarget(target, lease, recipe, request) {
  if (request.when === 'admit') {
    requireCheck(request.roster === null && lease === null && target.rows.length === 0);
    return;
  }
  requireCheck(digest(request.roster) && hash(lease) === request.roster &&
    lease.state === 'Ready' && lease.pending === null && lease.withinBudget && lease.roots.length === 2 &&
    lease.rechecks === (request.when === 'before' ? 0 : 1));
  const rows = new Map(target.rows.map(row => [row.name, row]));
  for (const [index, candidate] of recipe.candidates.entries()) {
    const name = candidate.outputRoot.slice(candidate.outputRoot.lastIndexOf('/') + 1);
    const root = lease.roots[index], directory = rows.get(name);
    requireCheck(root.candidate === candidate.id && root.complete && root.markerClosure === 'open' &&
      directory?.directory && directory.identity === root.identity);
    rows.delete(name);
    const marker = root.files.find(file => file.name === MARKER);
    requireCheck(marker?.bytes === '167');
    for (const file of root.files) {
      const key = name + '/' + file.name;
      const row = rows.get(key);
      requireCheck(row && !row.directory && row.identity === file.identity && row.bytes === file.bytes);
      rows.delete(key);
    }
  }
  requireCheck(rows.size === 0 && target.bytes === lease.observedBytes);
}

function checkEvidence(evidence, phase) {
  const expected = Object.keys(EVIDENCE).slice(0, EVIDENCE_COUNT[PHASES.indexOf(phase)]);
  requireCheck(evidence.rows.length === expected.length &&
    evidence.rows.every(row => !row.directory && expected.includes(row.name) &&
      BigInt(row.bytes) <= BigInt(EVIDENCE[row.name]) &&
      (BigInt(row.bytes) > 0n || row.name === 'stderr.bin')));
  const future = Object.entries(EVIDENCE).filter(([name]) => !expected.includes(name));
  requireCheck(evidence.pending >= future.reduce((sum, [, maximum]) => sum + maximum, 0));
}

export function createWorkerArtifactCompileChecksV1(manifest) {
  const spec = setup(manifest);
  let next = 0, pending = false, stopped = false, scope = null;

  return async function check(value, signal, admitted, lease) {
    requireCheck(!pending && !stopped && next < PHASES.length);
    pending = true;
    try {
      const request = data(value, ['version', 'context', 'index', 'when', 'roster']);
      const phase = PHASES[next], context = data(request.context, CONTEXT);
      requireCheck(process.platform === 'win32' && request.version === 1 && request.index === 0 &&
        request.when === phase && digest(admitted.scope) &&
        (scope === null || scope === admitted.scope) &&
        CONTEXT.every(key => digest(context[key]) && context[key] === admitted.context[key]));
      scope ??= admitted.scope;
      const { config, environment, evidenceRoot, outputParentIdentity, outputMaxBytes } = admitted.profile;
      const recipe = planWorkerArtifactComparisonV1(config);
      const includeRoots = [config.workerRoot, config.upstreamA, ...environment.include.split(';')];
      const toolRoot = parent(config.compiler);
      const inIncludes = file => includeRoots.some(root => inside(file, root));
      requireCheck(hash(recipe) === context.recipe &&
        spec.pins.some(pin => pin.role === 'source' && pin.path === config.workerRoot + '/main.cpp') &&
        spec.pins.some(pin => pin.role === 'tool' && pin.path === config.compiler) &&
        spec.pins.every(pin => (pin.role !== 'source' || inside(pin.path, config.workerRoot)) &&
          (pin.role !== 'headers' || inIncludes(pin.path)) &&
          (pin.role !== 'tool' || inside(pin.path, toolRoot)) &&
          (pin.role !== 'normal' || pin.path.startsWith('D:/'))) &&
        spec.absent.every(slot => inIncludes(slot.path) || inside(slot.path, toolRoot)));
      const rootPaths = [environment.temp, config.targetRoot, evidenceRoot];
      const roots = spec.roots.map((root, index) => ({ ...root, path: path(rootPaths[index]) }));
      const target = roots[1];
      requireCheck(target.identity === outputParentIdentity && target.maxBytes >= outputMaxBytes && target.maxDepth >= 2 &&
        (phase === 'after' || target.pending[phase] >= outputMaxBytes - (phase === 'before' ? 334 : 0)) &&
        roots.every(root => root.path.startsWith('D:/')) &&
        spec.pins.every(pin => roots.every(root => !inside(pin.path, root.path))) &&
        spec.absent.every(slot => roots.every(root => !inside(slot.path, root.path))));
      const io = ioFor(signal);
      const facts = Object.fromEntries(ROLES.map(role => [role, []]));
      const block = Buffer.alloc(65536);
      for (const pin of spec.pins) facts[pin.role].push(await io.pinned(pin, block));
      const absent = [];
      for (const slot of spec.absent) absent.push(await io.missing(slot));
      const inventories = [];
      for (const root of roots) inventories.push(await io.inventory(root, phase));
      checkTarget(inventories[1], lease, recipe, request);
      checkEvidence(inventories[2], phase);
      const free = await io.available(config.targetRoot);
      const reserved = inventories.reduce((sum, root) => sum + BigInt(root.pending), BigInt(spec.diskFloor));
      requireCheck(free >= reserved);
      io.live();
      next++;
      return JSON.stringify({ version: 1, kind: 'worker_artifact_compile_check_v1', context, when: phase,
        roster: request.roster, source: hash(facts.source), headers: hash({ facts: facts.headers, absent, topology: spec.topology }),
        tool: hash(facts.tool), environment: hash(environment), normal: hash(facts.normal),
        temp: hash({ namespace: admitted.profile.namespace, policy: roots[0] }),
        storage: hash(inventories), reserve: hash({ phase, free: free.toString(), reserved: reserved.toString() }) });
    } catch (error) {
      stopped = true;
      throw error;
    } finally {
      pending = false;
    }
  };
}
