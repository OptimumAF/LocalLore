// SOURCE ONLY / UNRUN at freeze. Actual bundled controller, synthetic native
// event values and transport only; no native IPC, app, rendering or proof.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const built = await build({
    entryPoints: [path.join(root, "ui/native-close-controller.ts")],
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
const bundle = path.join(output, `native-close-review-${randomUUID()}.cjs`);
await writeFile(bundle, built.outputFiles[0].contents, { flag: "wx" });
const { NativeCloseController } = (await import(pathToFileURL(bundle).href))
    .default;
let cases = 0;
async function test(name, action) {
    await action();
    cases += 1;
    console.log(`PASS ${name}`);
}
for (const [name, phase] of [
    ["array closed", ["closed"]],
    ["array cleanup", ["cleanup_required"]],
    ["empty array", []],
    ["object", {}],
    ["null", null],
    ["number", 1],
    ["boolean", true],
    ["unknown", "finished"],
]) {
    await test(`reject ${name} without false confirmation`, () => {
        let errors = 0,
            notices = 0;
        const c = new NativeCloseController(
            async () => ({}),
            () => {
                errors += 1;
            },
        );
        c.receive({ version: 1, phase: "closing" });
        c.subscribe(() => {
            notices += 1;
        });
        c.receive({ version: 1, phase });
        assert.equal(c.get(), "closing");
        assert.equal(errors, 1);
        assert.equal(notices, 0);
    });
}
for (const invalid of [
    null,
    [],
    "closed",
    { version: 1 },
    { version: "1", phase: "closed" },
    { version: 1, phase: "closed", cleanup: true },
]) {
    await test("reject malformed envelope preserving last real phase", () => {
        let errors = 0;
        const c = new NativeCloseController(
            async () => ({}),
            () => {
                errors += 1;
            },
        );
        c.receive({ version: 1, phase: "cleanup_required" });
        c.receive(invalid);
        assert.equal(c.get(), "cleanup_required");
        assert.equal(errors, 1);
    });
}
await test("phase object is never coerced or invoked", () => {
    let coerced = false,
        errors = 0;
    const c = new NativeCloseController(
        async () => ({}),
        () => {
            errors += 1;
        },
    );
    c.receive({
        version: 1,
        phase: {
            toString() {
                coerced = true;
                return "closed";
            },
        },
    });
    assert.equal(coerced, false);
    assert.equal(errors, 1);
    assert.equal(c.get(), "open");
});
await test("exact fixed phases notify; unsubscribe stops notifications", () => {
    let errors = 0,
        notices = 0;
    const c = new NativeCloseController(
        async () => ({}),
        () => {
            errors += 1;
        },
    );
    const stop = c.subscribe(() => {
        notices += 1;
    });
    for (const phase of ["closing", "cleanup_required", "closing", "closed"]) {
        c.receive({ version: 1, phase });
        assert.equal(c.get(), phase);
    }
    assert.equal(notices, 4);
    stop();
    c.receive({ version: 1, phase: "closed" });
    assert.equal(notices, 4);
    assert.equal(errors, 0);
});
await test("retry transport rejection does not fabricate cleanup acknowledgement", async () => {
    let errors = 0;
    const calls = [];
    const c = new NativeCloseController(
        async (...args) => {
            calls.push(args);
            throw Error("synthetic transport failure");
        },
        () => {
            errors += 1;
        },
    );
    c.receive({ version: 1, phase: "cleanup_required" });
    await c.retry();
    await c.retry();
    assert.deepEqual(calls, [["application_close"], ["application_close"]]);
    assert.equal(errors, 2);
    assert.equal(c.get(), "cleanup_required");
});
assert.ok(cases > 0);
console.log(
    `${cases} actual-controller synthetic status checks PASS; no native cleanup proof`,
);
