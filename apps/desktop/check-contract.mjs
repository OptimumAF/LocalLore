import Ajv2020 from 'ajv/dist/2020.js';
import { readFileSync } from 'node:fs';
import assert from 'node:assert/strict';
import { envelope, actionRequest } from './ui/requests.js';
const read = file => JSON.parse(readFileSync(new URL(file, import.meta.url), 'utf8'));
const ajv = new Ajv2020();
for (const [format, maximum] of [['uint16', 65535], ['uint64', Number.MAX_SAFE_INTEGER]]) {
  ajv.addFormat(format, { type: 'number', validate: value => Number.isSafeInteger(value) && value >= 0 && value <= maximum });
}
const validate = ajv.compile(read('./host-v1.schema.json'));
const steps = read('./ui/smoke-requests.json');
for (const step of steps) assert(validate(step), JSON.stringify(validate.errors));
for (const kind of ['give', 'ability']) assert(validate(envelope({ op: 'submit', session: 'session-1', mode: 'accepted', request: actionRequest({ story: 'quay', branch: 'main' }, 'gift', 0, kind) })));
assert(!validate({ version: 2, command: { op: 'capabilities' } }));
assert(!validate(envelope({ op: 'capabilities', extra: true })));
assert(!validate(envelope({ op: 'run_sql', sql: 'DROP TABLE events' })));

console.log(`PASS: ${steps.length} native requests + frontend actions match generated host-v1 schema; hostile transport samples reject.`);
