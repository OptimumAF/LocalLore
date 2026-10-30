import Ajv2020 from "ajv/dist/2020.js";
import { readFileSync, mkdirSync, writeFileSync } from "node:fs";
import { build } from "esbuild";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import evidencePath from "node:path";
import assert from "node:assert/strict";
const folder = process.env.LOCALLORE_CHECK_OUTPUT_DIR
    ? pathToFileURL(
          evidencePath.resolve(process.env.LOCALLORE_CHECK_OUTPUT_DIR) +
              evidencePath.sep,
      )
    : new URL("./artifacts/checks/", import.meta.url);
mkdirSync(folder, { recursive: true });
const file = new URL(`model-${randomUUID()}.mjs`, folder);
const bundled = await build({
    entryPoints: [fileURLToPath(new URL("./ui/model.ts", import.meta.url))],
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
writeFileSync(file, bundled.outputFiles[0].contents);
const { request, ErrorBuffer, composerShortcut, playView } = await import(
    file.href
);
const envelope = (command) => ({ version: 1, command });
const read = (file) =>
    JSON.parse(readFileSync(new URL(file, import.meta.url), "utf8"));
const ajv = new Ajv2020();
for (const [format, maximum] of [
    ["uint16", 65535],
    ["uint64", Number.MAX_SAFE_INTEGER],
]) {
    ajv.addFormat(format, {
        type: "number",
        validate: (value) =>
            Number.isSafeInteger(value) && value >= 0 && value <= maximum,
    });
}
const validate = ajv.compile(read("./host-v1.schema.json"));
const steps = read("./ui/smoke-requests.json");
for (const step of steps)
    assert(validate(step), JSON.stringify(validate.errors));
for (const kind of ["give", "ability", "wait", "dialogue"])
    assert(
        validate(
            envelope({
                op: "submit",
                session: "session-1",
                mode: "accepted",
                request: request(
                    { story: "quay", branch: "main" },
                    "gift",
                    0,
                    kind,
                    "Synthetic dialogue",
                ),
            }),
        ),
    );
assert(!validate({ version: 2, command: { op: "capabilities" } }));
assert(!validate(envelope({ op: "capabilities", extra: true })));
assert(!validate(envelope({ op: "run_sql", sql: "DROP TABLE events" })));
const thinSnapshot = envelope({
    op: "play_snapshot_v2",
    session: "session-1",
    scope: { story: "quay", branch: "main" },
    expected_revision: 0,
});
assert(validate(thinSnapshot), JSON.stringify(validate.errors));
assert(
    !validate({
        ...thinSnapshot,
        command: { ...thinSnapshot.command, observer: "mira" },
    }),
);

for (const bad of [
    null,
    {},
    {
        revision: 0,
        scope: { story: "q", branch: "b" },
        player: { revision: 0, observer: "player" },
        receipts: [null],
    },
])
    assert.throws(() => playView(bad, { story: "q", branch: "b" }, 0), {
        message: "Wire",
    });
const buffer = new ErrorBuffer();
for (let i = 0; i < 100; i++)
    buffer.add("frontend", new Error("private input must not be retained"));
assert.equal(buffer.snapshot().length, 64);
assert(
    buffer
        .snapshot()
        .every(
            (row) =>
                row.category === "Transport" && Object.keys(row).length === 2,
        ),
);
assert.equal(
    composerShortcut({ key: "Enter", shiftKey: false, isComposing: false }),
    "submit",
);
assert.equal(
    composerShortcut({ key: "Enter", shiftKey: true, isComposing: false }),
    "edit",
);
assert.equal(
    composerShortcut({ key: "Enter", shiftKey: false, isComposing: true }),
    "edit",
);
console.log(
    `PASS: ${steps.length} original native fixtures + four current controller action builders match Rust schema; hostile wire, bounded errors and keyboard policy checks pass.`,
);
