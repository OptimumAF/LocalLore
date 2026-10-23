// Actual frontend controller, MOCK IPC. No native app/WebView/model/device execution.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import { randomUUID } from "node:crypto";
import path from "node:path";
const directory =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    fileURLToPath(new URL("artifacts/checks/", import.meta.url));
await mkdir(directory, { recursive: true });
const compiled = await build({
    stdin: {
        contents:
            'export { ForkController, decodeForkRequest } from "./ui/fork-controller";',
        resolveDir: fileURLToPath(new URL(".", import.meta.url)),
        loader: "ts",
    },
    bundle: true,
    platform: "node",
    format: "esm",
    write: false,
});
const file = path.join(directory, `fork-controller-${randomUUID()}.mjs`);
await writeFile(file, compiled.outputFiles[0].contents);
const { ForkController, decodeForkRequest } = await import(
    pathToFileURL(file).href
);
const checks = [];
function check(value, label) {
    assert(value, label);
    checks.push(label);
}
const scope = { story: "fork-synthetic", branch: "main" };
const context = (patch = {}) => ({
    session: "session-main",
    scope: { ...scope },
    revision: 4,
    view: "play",
    observer: "player",
    persistent: true,
    ...patch,
});
const request = () => ({
    parent: { ...scope },
    child_branch: "fixed-child",
    expected_parent_revision: 4,
    at_revision: 2,
});
const result = (patch = {}) => ({
    version: 1,
    scope: { story: scope.story, branch: "fixed-child" },
    parent: { ...scope },
    fork_revision: 2,
    head_revision: 2,
    created: true,
    ...patch,
});
const status = (patch = {}) => ({
    version: 1,
    operation_id: 7,
    running: false,
    phase: "completed",
    error: null,
    result: { kind: "fork", outcome: result() },
    ...patch,
});
const gate = () => {
    let resolve;
    const promise = new Promise((r) => (resolve = r));
    return { promise, resolve };
};
function setup(handler = () => status(), persist = () => {}) {
    const calls = [];
    let refresh = 0;
    const controller = new ForkController(
        async (name, args) => {
            calls.push({ name, args: structuredClone(args) });
            return handler(name, args);
        },
        async () => {
            refresh++;
        },
        persist,
    );
    controller.contextChanged(context());
    return {
        controller,
        calls,
        get refresh() {
            return refresh;
        },
    };
}
{
    let remembered;
    const s = setup(undefined, (r) => {
        remembered = r;
        check(s.calls.length === 0, "recovery-identity-saved-before-IPC");
    });
    s.controller.prepare(2, "fixed-child");
    check(
        Object.isFrozen(remembered) && Object.isFrozen(remembered.parent),
        "request-and-parent-immutable",
    );
    await s.controller.confirm(false);
    check(
        !s.calls.length && s.controller.get().error === "ForkConsentRequired",
        "consent-refused-without-dispatch",
    );
    await s.controller.confirm(true);
    check(
        s.controller.get().status === "complete" && s.refresh === 1,
        "accepted-result-refreshes-library",
    );
    check(
        s.calls[0].name === "fork_start" &&
            s.calls[0].args.session === "session-main" &&
            JSON.stringify(s.calls[0].args.input) === JSON.stringify(request()),
        "exact-parent-boundary-head-and-fixed-child-dispatch",
    );
    check(
        !s.calls.some((c) => /resume|inspect|prepare/.test(c.name)),
        "success-does-not-switch-session-or-generate",
    );
}
for (const error of [
    "Stale",
    "Busy",
    "Cancelled",
    "Full",
    "Mismatch",
    "Integrity",
    "Transport",
    "Rule",
    "RetryMismatch",
]) {
    const s = setup(() => {
        throw Error(error);
    });
    s.controller.prepare(2, "fixed-child");
    await s.controller.confirm(true);
    check(
        s.controller.get().status === "uncertain" &&
            s.controller.get().error === error &&
            s.controller.get().request.child_branch === "fixed-child",
        `failure-${error}-retains-original-identity`,
    );
    check(s.calls.length === 1, `failure-${error}-never-auto-retries`);
}
{
    let attempt = 0;
    const s = setup(() => {
        if (attempt++ === 0) throw Error("Transport");
        return status({
            result: {
                kind: "fork",
                outcome: result({ created: false, head_revision: 6 }),
            },
        });
    });
    s.controller.prepare(2, "fixed-child");
    await s.controller.confirm(true);
    await s.controller.confirm(true);
    assert.deepEqual(s.calls[0], s.calls[1]);
    checks.push("explicit-exact-retry-keeps-original-complete-request");
    check(
        s.controller.get().result.head_revision === 6 &&
            !s.controller.get().result.created,
        "exact-retry-displays-current-child-head",
    );
}
for (const found of [false, true]) {
    const s = setup((name) => {
        assert.equal(name, "fork_lookup");
        return {
            version: 1,
            kind: "fork_lookup",
            found,
            outcome: found
                ? result({ created: false, head_revision: 8 })
                : null,
        };
    });
    const original = request();
    s.controller.restore(original);
    original.child_branch = "mutated-after-restore";
    await s.controller.confirm(true);
    check(s.calls.length === 0, `restart-${found}-cannot-execute`);
    await s.controller.lookup();
    check(
        s.calls.length === 1 &&
            s.calls[0].args.input.child_branch === "fixed-child",
        `restart-${found}-uses-copy-and-only-lookup`,
    );
    check(
        s.controller.get().status === (found ? "complete" : "not_found"),
        `restart-${found}-reports-catalog-result`,
    );
    await s.controller.confirm(true);
    check(
        s.calls.length === 1,
        `restart-${found}-still-cannot-recreate-after-lookup`,
    );
}
for (const changed of [
    context({ session: "new-session" }),
    context({ scope: { story: "other", branch: "main" } }),
    context({ observer: "sable", view: "lab" }),
    context({ revision: 5 }),
]) {
    const ack = gate();
    const s = setup((name) => (name === "fork_start" ? ack.promise : {}));
    s.controller.prepare(2, "fixed-child");
    const action = s.controller.confirm(true);
    s.controller.contextChanged(changed);
    ack.resolve(status({ running: true, result: null, phase: "starting" }));
    await action;
    check(
        s.calls.some(
            (c) => c.name === "archive_cancel" && c.args.operationId === 7,
        ),
        `changed-${JSON.stringify(changed)}-late-operation-cancelled`,
    );
    check(
        s.controller.get().result === null &&
            s.controller.get().lookupOnly &&
            !s.refresh,
        "stale-reply-never-selects-or-refreshes",
    );
}
{
    const ack = gate();
    const s = setup((name) =>
        name === "fork_start"
            ? ack.promise
            : name === "archive_status"
              ? status()
              : {},
    );
    s.controller.prepare(2, "fixed-child");
    const action = s.controller.confirm(true);
    await s.controller.cancel();
    ack.resolve(status({ running: true, result: null, phase: "forking" }));
    await action;
    check(
        s.calls.some((c) => c.name === "archive_cancel"),
        "pending-cancel-before-ack-latches-until-operation-id",
    );
    check(
        s.controller.get().status === "complete" &&
            s.controller.get().result.created,
        "committed-result-wins-late-cancel",
    );
}
{
    const s = setup((name) =>
        name === "fork_start"
            ? status({ running: true, result: null })
            : status({ operation_id: 8 }),
    );
    s.controller.prepare(2, "fixed-child");
    await s.controller.confirm(true);
    check(
        s.controller.get().error === "Wire" && !s.refresh,
        "changed-operation-id-refused",
    );
}
for (const mutate of [
    (v) => (v.outcome.parent.branch = "sibling"),
    (v) => (v.outcome.scope.story = "other"),
    (v) => (v.outcome.fork_revision = 3),
    (v) => (v.outcome.head_revision = 1),
    (v) => (v.outcome.extra = "spoiler"),
    (v) => (v.kind = "archive"),
]) {
    const r = { kind: "fork", outcome: result() };
    mutate(r);
    const s = setup(() => status({ result: r }));
    s.controller.prepare(2, "fixed-child");
    await s.controller.confirm(true);
    check(
        s.controller.get().error === "Wire" &&
            s.controller.get().result === null,
        "mismatched-or-open-ended-outcome-refused",
    );
}
for (const mutate of [
    (r) => (r.observer = "omniscient"),
    (r) => (r.parent.extra = true),
    (r) => (r.child_branch = "../outside"),
    (r) => (r.child_branch = "main"),
    (r) => (r.at_revision = 5),
    (r) => (r.expected_parent_revision = Number.MAX_SAFE_INTEGER + 1),
]) {
    const r = request();
    mutate(r);
    assert.throws(() => decodeForkRequest(r));
    checks.push("closed-request-input-refused");
}
{
    const s = setup(undefined, () => {
        throw Error("Io");
    });
    s.controller.prepare(2, "fixed-child");
    await s.controller.confirm(true);
    check(
        !s.calls.length && s.controller.get().request === null,
        "failed-recovery-save-prevents-native-dispatch",
    );
}
{
    const s = setup();
    s.controller.contextChanged(context({ persistent: false }));
    s.controller.prepare(2, "fixed-child");
    await s.controller.confirm(true);
    check(
        !s.calls.length && s.controller.get().request === null,
        "in-memory-session-does-not-offer-durable-fork",
    );
}
{
    const ack = gate();
    const s = setup(() => ack.promise);
    s.controller.prepare(2, "fixed-child");
    const action = s.controller.confirm(true);
    s.controller.dispose();
    ack.resolve(status());
    await action;
    check(
        s.controller.get().result === null && !s.refresh,
        "disposed-controller-suppresses-completion",
    );
}
await writeFile(
    path.join(directory, "fork-controller-summary.json"),
    JSON.stringify(
        {
            backend: "mock-native-IPC",
            checks: checks.length,
            failures: 0,
            labels: checks,
        },
        null,
        2,
    ) + "\n",
);
console.log(
    `PASS ${checks.length} frontend controller assertions; MOCK native IPC, no native/WebView execution.`,
);
