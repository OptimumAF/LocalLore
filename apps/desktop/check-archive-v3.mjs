// Frozen D08.01/.02/.07 + M08.03 consumer oracles; source-only at freeze.
// Run from apps/desktop: node check-archive-v3.mjs
// Uses the actual decoder/controller and headless React renderer, not native IPC,
// WebView, a model, or newly captured native fixture output. Root owns execution.
//
// Shapes follow storage::ArchivePreview's actual serde fields and desktop Work's
// token wrapper. Empty preview retired IDs are OMITTED (Vec::is_empty), unlike
// the required possibly-empty array in the private Archive3 payload. Nonempty
// IDs are sorted. Root also accepts explicit [] for V3 as input compatibility;
// that positive is distinguished from actual producer omission. committed_turns
// counts canonical records, including author records, and cannot be reconstructed
// by summing branch heads. These tests do
// not make a renderer/decoder an authority for archive contents or checksums.
// First baseline is expected to reject the valid V3 shapes; that prediction is
// not measured RED. Unknown-field/label checks also freeze the required closure.
import assert from "node:assert/strict";
import { build } from "esbuild";
import { mkdir, writeFile } from "node:fs/promises";
import { fileURLToPath, pathToFileURL } from "node:url";
import path from "node:path";
import { randomUUID } from "node:crypto";

const root = fileURLToPath(new URL(".", import.meta.url));
const output =
    process.env.LOCALLORE_CHECK_OUTPUT_DIR ??
    path.join(root, "artifacts/checks");
await mkdir(output, { recursive: true });
const cohort = randomUUID();
const bundled = path.join(output, `archive-v3-${cohort}.cjs`);
const built = await build({
    stdin: {
        contents:
            'export {ArchiveController} from "./ui/archive-controller";export {ArchivePanel} from "./ui/ArchivePanel";export {decodePreview,decodeStatus,decodeArchiveCompletion,archiveBinding} from "./ui/archive-model";export {createElement} from "react";export {renderToStaticMarkup} from "react-dom/server";',
        resolveDir: root,
        loader: "tsx",
    },
    bundle: true,
    platform: "node",
    format: "cjs",
    write: false,
});
await writeFile(bundled, built.outputFiles[0].contents);
const {
    ArchiveController,
    ArchivePanel,
    decodePreview,
    decodeStatus,
    decodeArchiveCompletion,
    archiveBinding,
    createElement,
    renderToStaticMarkup,
} = (await import(pathToFileURL(bundled).href)).default;

const token = "11111111-1111-1111-1111-111111111111";
const warning =
    "Full private story: all timelines, hidden seed facts, author corrections/reasons/prior truth, private discovery source bindings, accepted input/narration and model/timing/provenance metadata. Accepted records include play and author corrections. No weights, separate traces/raw prompts, caches or noncommitted workflow keys/status. Imported sessions must not resume old pending operations.";
const legacyWarning =
    "Full private story: all timelines, hidden seed facts, accepted input/narration and model/timing/provenance metadata. No weights, separate traces/raw prompt logs, caches or noncommitted workflow keys/status. Imported sessions must not resume old pending operations.";
const nativeWarning =
    "Full private whole story: hidden facts, original accepted requests, narration, provenance and every branch. Checksums are not authenticity. Manual snapshot transfer is not synchronization. Workflow keys, noncommitted drafts/status, traces, caches and weights are excluded. Models are never loaded.";
function preview(version = 3, retired = false, kind = "import") {
    const value = {
        version: 1,
        token,
        kind,
        warning: nativeWarning,
        preview: {
            version,
            story_id: "synthetic-mixed",
            title: "Synthetic mixed accepted history",
            root_branch: "main",
            branch_heads: retired
                ? { main: 1, parent: 2, child: 3 }
                : { main: 1, child: 3 },
            committed_turns: 3,
            bytes: 1024,
            payload_sha256: "a".repeat(64),
            privacy_warning: version === 3 ? warning : legacyWarning,
            noncommitted_workflow_transferred: false,
        },
    };
    if (retired) value.preview.retired_branch_ids = ["collected", "parent"];
    return value;
}
const terminal = (result) => ({
    version: 1,
    operation_id: 17,
    running: false,
    phase: "completed",
    error: null,
    result,
});
const cases = [];
const test = (name, run) => cases.push({ name, run });
const reject = (name, version, mutate) =>
    test(name, () => {
        const value = preview(version, version === 2);
        mutate(value);
        assert.throws(() => decodePreview(value), /Wire/);
    });

for (const [version, shape] of [
    [1, "omitted"],
    [2, "retired"],
    [3, "omitted"],
    [3, "retired"],
    [3, "explicit-empty"],
]) {
    const retired = shape === "retired";
    for (const kind of ["import", "export"]) {
        test(`accept preview${version}/${shape}/${kind}`, () => {
            const wire = preview(version, retired, kind);
            if (shape === "explicit-empty")
                wire.preview.retired_branch_ids = [];
            const decoded = decodePreview(wire);
            assert.deepEqual(decoded, wire);
            assert.equal(decoded.preview.committed_turns, 3);
            assert.equal(decoded.preview.branch_heads.child, 3);
            assert.notEqual(
                Object.values(decoded.preview.branch_heads).reduce(
                    (a, b) => a + b,
                    0,
                ),
                3,
            );
            assert.equal(
                Object.hasOwn(decoded.preview, "retired_branch_ids"),
                shape !== "omitted",
            );
            assert.deepEqual(
                decoded.preview.retired_branch_ids ?? [],
                retired ? ["collected", "parent"] : [],
            );
            const status = decodeStatus(terminal(wire));
            assert.deepEqual(
                decodeArchiveCompletion(status, `archive_${kind}_preview`),
                wire,
            );
            assert.deepEqual(archiveBinding(decoded), {
                token,
                kind,
                story: "synthetic-mixed",
                branch: "main",
                payload_sha256: "a".repeat(64),
            });
        });
    }
}

// Exercise negatives on already-supported V1 as well as V3. Blanket V3 refusal
// must not disguise an open unknown-field/type guard as successful validation.
for (const version of [1, 3]) {
    for (const [name, mutate] of [
        [
            "null preview",
            (v) => {
                v.preview = null;
            },
        ],
        [
            "array preview",
            (v) => {
                v.preview = [];
            },
        ],
        [
            "unknown envelope field",
            (v) => {
                v.future = true;
            },
        ],
        [
            "unknown preview field",
            (v) => {
                v.preview.future = true;
            },
        ],
        [
            "private payload field",
            (v) => {
                v.preview.author_reason = "synthetic reason";
            },
        ],
        [
            "null version",
            (v) => {
                v.preview.version = null;
            },
        ],
        [
            "string version",
            (v) => {
                v.preview.version = String(version);
            },
        ],
        [
            "future version",
            (v) => {
                v.preview.version = 4;
            },
        ],
        [
            "fractional version",
            (v) => {
                v.preview.version = 1.5;
            },
        ],
        [
            "future envelope version",
            (v) => {
                v.version = 2;
            },
        ],
        [
            "null token",
            (v) => {
                v.token = null;
            },
        ],
        [
            "wrong kind",
            (v) => {
                v.kind = "delete";
            },
        ],
        [
            "null heads",
            (v) => {
                v.preview.branch_heads = null;
            },
        ],
        [
            "root missing from heads",
            (v) => {
                delete v.preview.branch_heads.main;
            },
        ],
        [
            "negative head",
            (v) => {
                v.preview.branch_heads.child = -1;
            },
        ],
        [
            "string head",
            (v) => {
                v.preview.branch_heads.child = "3";
            },
        ],
        [
            "null count",
            (v) => {
                v.preview.committed_turns = null;
            },
        ],
        [
            "fractional count",
            (v) => {
                v.preview.committed_turns = 0.5;
            },
        ],
        [
            "negative count",
            (v) => {
                v.preview.committed_turns = -1;
            },
        ],
        [
            "over count cap",
            (v) => {
                v.preview.committed_turns = 4097;
            },
        ],
        [
            "over artifact cap",
            (v) => {
                v.preview.bytes = 32 * 1024 * 1024 + 1;
            },
        ],
        [
            "invalid checksum",
            (v) => {
                v.preview.payload_sha256 = "not-a-checksum";
            },
        ],
        [
            "workflow transfer true",
            (v) => {
                v.preview.noncommitted_workflow_transferred = true;
            },
        ],
        [
            "null warning",
            (v) => {
                v.preview.privacy_warning = null;
            },
        ],
    ])
        reject(`reject V${version}: ${name}`, version, mutate);
}
for (const [name, retired] of [
    ["null", null],
    ["not an array", "parent"],
    ["duplicate", ["parent", "parent"]],
    ["unsorted", ["parent", "collected"]],
    ["root retired", ["main"]],
    ["invalid identifier", ["bad/id"]],
    ["wrong item type", [1]],
    [
        "over tombstone cap",
        Array.from(
            { length: 257 },
            (_, i) => `old-${String(i).padStart(3, "0")}`,
        ),
    ],
    [
        "combined identity cap",
        Array.from(
            { length: 255 },
            (_, i) => `old-${String(i).padStart(3, "0")}`,
        ),
    ],
]) {
    for (const version of [2, 3])
        reject(`reject V${version} retired: ${name}`, version, (v) => {
            v.preview.retired_branch_ids = retired;
        });
}
reject("V1 cannot acquire retired metadata", 1, (v) => {
    v.preview.retired_branch_ids = ["parent"];
});
reject("V2 forbids an explicitly empty retirement array", 2, (v) => {
    v.preview.retired_branch_ids = [];
});
reject("V2 requires its nonempty retirement metadata", 2, (v) => {
    delete v.preview.retired_branch_ids;
});
test("V3 accepts bounded canonical-record and artifact maxima without inferring canon", () => {
    const wire = preview();
    wire.preview.committed_turns = 4096;
    wire.preview.bytes = 32 * 1024 * 1024;
    assert.equal(decodePreview(wire).preview.committed_turns, 4096);
    assert.equal(decodePreview(wire).preview.bytes, 32 * 1024 * 1024);
});
test("V3 imported completion retains actual native count and explicit-open flags", () => {
    const binding = archiveBinding(decodePreview(preview()));
    const result = {
        version: 1,
        status: "imported",
        root: { story: "synthetic-mixed", branch: "main" },
        branches: 2,
        committed_turns: 3,
        staging_cleanup_complete: true,
        pending_workflow_resumed: false,
        model_loaded: false,
    };
    const status = decodeStatus(terminal(result));
    assert.equal(
        decodeArchiveCompletion(status, "archive_import", binding)
            .committed_turns,
        3,
    );
});
test("V3 actual controller and headless panel show accepted records, not accepted turns", async () => {
    const wire = preview();
    const calls = [];
    const archive = new ArchiveController(
        async (name) => {
            calls.push(name);
            assert.equal(name, "archive_import_preview");
            return terminal(wire);
        },
        async () => {
            assert.fail("Preview must not refresh/open the library");
        },
    );
    const context = "synthetic|lab|omniscient";
    archive.contextChanged(context, true);
    archive.show();
    await archive.previewImport();
    assert.equal(archive.get().error, null);
    assert.deepEqual(archive.get().preview, wire);
    assert.equal(archive.get().consent, false);
    assert.deepEqual(calls, ["archive_import_preview"]);
    const html = renderToStaticMarkup(
        createElement(ArchivePanel, {
            archive,
            controller: {
                get: () => ({ play: { revision: 3 } }),
                selected: () => ({
                    id: "synthetic-session",
                    scope: { story: "synthetic-mixed", branch: "child" },
                }),
            },
            context,
            allowed: true,
        }),
    );
    assert.match(html, /<dt>Accepted records<\/dt><dd>3<\/dd>/);
    assert.doesNotMatch(html, /<dt>Accepted turns<\/dt>/);
    assert.match(html, /author corrections/);
    assert.match(html, /Confirm staged import/);
    assert.match(html, /disabled/);
});

const results = [];
for (const { name, run } of cases) {
    try {
        await run();
        results.push({ name, status: "pass" });
    } catch (error) {
        results.push({
            name,
            status: "fail",
            error: String(error?.message ?? error).slice(0, 512),
        });
    }
}
const failed = results.filter((r) => r.status === "fail").length;
const report = {
    suite: "archive-v3-consumer",
    execution: "synthetic transport + headless React; no native IPC or WebView",
    passed: results.length - failed,
    failed,
    results,
};
await writeFile(
    path.join(output, `archive-v3-${cohort}.json`),
    JSON.stringify(report, null, 2),
);
console.log(JSON.stringify(report));
assert.equal(failed, 0, `${failed} Archive3 consumer oracle(s) failed`);
