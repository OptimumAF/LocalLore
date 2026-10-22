// Host requests are validated against the Rust-generated schema in check-contract.mjs.
import { actionRequest, envelope } from './requests.js';
const invoke = window.__TAURI__.core.invoke;
const result = document.querySelector('#result');
const inspection = document.querySelector('#inspection');
let session, scope, revision = 0, next = 0;
async function call(command) {
  const reply = await invoke('host_call', { input: JSON.stringify(envelope(command)) });
  if (reply.status !== 'ok') throw new Error(reply.error);
  return reply.data;
}
async function inspect() {
  const snapshot = await call({ op: 'inspect', session, scope, expected_revision: revision, observer: document.querySelector('#observer').value });
  inspection.textContent = JSON.stringify(snapshot, null, 2);
}
async function open() {
  if (session) await call({ op: 'close', session, scope });
  const created = await call({ op: 'create', seed: 'lantern-quay-v1' });
  ({ session, scope, revision } = created);
  result.textContent = 'Revision 0 · One potion in Rowan’s inventory.';
  await inspect();
}
async function act(kind) {
  const turn = `desktop-${++next}`;
  const request = actionRequest(scope, turn, revision, kind);
  await call({ op: 'submit', session, request, mode: 'accepted' });
  await call({ op: 'prepare', session, scope, turn });
  let outcome;
  try { outcome = await call({ op: 'commit', session, scope, turn }); }
  catch {
    // An uncertain response is resolved via the original turn, never by creating a new one.
    outcome = await call({ op: 'turn_status', session, scope, turn });
  }
  if (outcome.phase !== 'committed') throw new Error(outcome.error || outcome.phase);
  revision = outcome.receipt.events.at(-1).sequence;
  result.textContent = `Revision ${revision} · ${outcome.receipt.narration}`;
  await inspect();
}
async function busy(work) {
  document.querySelectorAll('button').forEach(button => button.disabled = true);
  try { await work(); } catch (error) { result.textContent = `Engine: ${error.message}.`; }
  finally { document.querySelectorAll('button').forEach(button => button.disabled = false); }
}
document.querySelector('#give').addEventListener('click', () => busy(() => act('give')));
document.querySelector('#again').addEventListener('click', () => busy(() => act('give')));
document.querySelector('#ability').addEventListener('click', () => busy(() => act('ability')));
document.querySelector('#reset').addEventListener('click', () => busy(open));
document.querySelector('#observer').addEventListener('change', () => busy(inspect));
if (window.__D01_SMOKE__) {
  try {
    const steps = await (await fetch('smoke-requests.json')).json();
    const report = [];
    for (const step of steps) report.push(await invoke('host_call', { input: JSON.stringify(step) }));
    await invoke('smoke_finish', { report });
  } catch (error) { result.textContent = `Native smoke failed: ${error}`; }
} else { await busy(open); }
