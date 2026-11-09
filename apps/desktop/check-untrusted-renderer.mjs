// App-owned headless check. The saved state is synthetic; this is not WebView or IPC evidence.
import assert from "node:assert/strict";
import { mkdir, mkdtemp, readFile, writeFile } from "node:fs/promises";
import { createRequire } from "node:module";
import path from "node:path";
import { fileURLToPath } from "node:url";

const require = createRequire(import.meta.url);
const { build, stop } = require("esbuild");
const { chromium } = require("playwright");
const root = fileURLToPath(new URL(".", import.meta.url));
const origin = "https://locallore.test";
const fixture = {
    title: 'Synthetic <a href="https://renderer-text.invalid/title">Title</a>',
    dialogue:
        '<img src="https://renderer-text.invalid/image.png" onerror="window.rendererTextCanary=1"> 雪',
    narration:
        '<iframe src="https://renderer-text.invalid/frame"></iframe> <script>window.rendererTextCanary=2</script>',
};
const program = `
    import { createElement } from "react";
    import { createRoot } from "react-dom/client";
    import { App } from "./ui/App";
    import { Controller } from "./ui/controller";

    const fixture = ${JSON.stringify(fixture)};
    const scope = { story: "synthetic-story", branch: "main" };
    const session = "synthetic-session";
    const revision = 1;
    const receipt = {
        request: {
            turn: "synthetic-turn", scope, expected_revision: 0,
            intent: { kind: "dialogue", value: { text: fixture.dialogue } },
        },
        events: [{ scope, sequence: revision }],
        narration: fixture.narration,
    };
    const commands = [];
    const controller = new Controller({
        async call(command) {
            commands.push(command.op);
            switch (command.op) {
                case "workspace":
                    return {
                        persistent: true, location: "Synthetic fixture", schema_version: 1,
                        stories: [{ scope, title: fixture.title, revision, drafts: 0 }],
                    };
                case "resume":
                case "open":
                    if (command.scope.story !== scope.story || command.scope.branch !== scope.branch)
                        throw new Error("Unexpected fixture scope");
                    return { session, scope, revision };
                case "play_snapshot":
                    if (command.session !== session || command.expected_revision !== revision)
                        throw new Error("Unexpected fixture read");
                    return {
                        scope, revision, inventory: { potion: 1 }, receipts: [receipt],
                        player: { scope, revision, observer: "player", self_state: { name: "Rowan" } },
                    };
                default:
                    throw new Error("Unexpected fixture command");
            }
        },
    }, undefined, "untrusted-renderer");
    createRoot(document.getElementById("root")).render(createElement(App, { controller }));
    await controller.start();
    controller.selectReceipt(receipt.request.turn);
    const state = controller.get();
    window.__untrustedRendererEvidence = {
        commands, story: controller.selected()?.scope.story, observer: state.observer,
        revision: state.play?.revision, pending: state.pending, error: state.visibleError,
        receipt: controller.receipt()?.request.turn,
    };
`;
let bundle;
try {
    bundle = await build({
        stdin: { contents: program, resolveDir: root, loader: "tsx" },
        bundle: true,
        nodePaths: (process.env.NODE_PATH ?? "")
            .split(path.delimiter)
            .filter(Boolean),
        jsx: "automatic",
        platform: "browser",
        format: "esm",
        write: false,
        define: {
            __DEV_HARNESS__: "false",
            "process.env.NODE_ENV": '"production"',
        },
    });
} finally {
    stop();
}
const assets = new Map([
    [
        "/",
        {
            contentType: "text/html",
            body: await readFile(path.join(root, "ui/index.html")),
        },
    ],
    [
        "/app.js",
        { contentType: "text/javascript", body: bundle.outputFiles[0].text },
    ],
    [
        "/style.css",
        {
            contentType: "text/css",
            body: await readFile(path.join(root, "ui/style.css")),
        },
    ],
]);
const browser = await chromium.launch({
    headless: true,
    timeout: 10_000,
    args: ["--host-resolver-rules=MAP * ~NOTFOUND"],
});
let snapshot, png;
try {
    const context = await browser.newContext({
        viewport: { width: 1180, height: 900 },
        serviceWorkers: "block",
    });
    const requested = new Set();
    let blocked = 0;
    let errors = 0;
    await context.route("**/*", async (route) => {
        const request = route.request();
        const url = new URL(request.url());
        const asset = assets.get(url.pathname);
        if (
            url.origin !== origin ||
            url.search ||
            request.method() !== "GET" ||
            !asset
        ) {
            blocked += 1;
            await route.abort();
            return;
        }
        requested.add(url.pathname);
        await route.fulfill(asset);
    });
    const page = await context.newPage();
    page.on("pageerror", () => errors++);
    page.on("console", (message) => {
        if (message.type() === "error") errors++;
    });
    await page.goto(origin, { waitUntil: "networkidle", timeout: 10_000 });
    const transcript = page.getByLabel("Finalized transcript");
    const turn = transcript.locator("article.turn");
    await turn.waitFor({ timeout: 5_000 });
    const title = await page
        .getByRole("heading", { name: fixture.title, exact: true })
        .textContent();
    const text = await turn.textContent();
    const state = await page.evaluate(() => ({
        ...window.__untrustedRendererEvidence,
        canary: window.rendererTextCanary ?? null,
    }));
    assert.equal(title, fixture.title);
    assert(text.includes(fixture.dialogue));
    assert(text.includes(fixture.narration));
    assert.equal(
        await page.locator("#root img, #root iframe, #root script").count(),
        0,
    );
    assert.equal(
        await turn
            .getByRole("button", { name: "Inspect receipt synthetic-turn" })
            .count(),
        1,
    );
    assert.deepEqual(
        await page
            .locator("#root a")
            .evaluateAll((links) =>
                links.map((link) => link.getAttribute("href")),
            ),
        ["#composer"],
    );
    assert.deepEqual(state, {
        commands: ["workspace", "resume", "open", "play_snapshot"],
        story: "synthetic-story",
        observer: "player",
        revision: 1,
        pending: null,
        error: null,
        receipt: "synthetic-turn",
        canary: null,
    });
    png = await page.screenshot({ animations: "disabled", timeout: 5_000 });
    assert.deepEqual([...requested].sort(), [...assets.keys()].sort());
    assert.equal(blocked, 0);
    assert.equal(errors, 0);
    snapshot = {
        synthetic: true,
        rendering: "headless-chromium",
        browser: browser.version(),
        requested: [...requested].sort(),
        blocked,
        errors,
        ...state,
        title,
        transcript: text,
    };
} finally {
    await browser.close();
}
const summary = JSON.stringify(snapshot, null, 2) + "\n";
assert(
    png.length + Buffer.byteLength(summary) <= 2 * 1024 * 1024,
    "ArtifactBudget",
);
const outputRoot = path.join(root, "artifacts");
await mkdir(outputRoot, { recursive: true });
const output = await mkdtemp(path.join(outputRoot, "untrusted-renderer-"));
await writeFile(path.join(output, "snapshot.json"), summary, { flag: "wx" });
await writeFile(path.join(output, "play.png"), png, { flag: "wx" });
console.log(JSON.stringify({ ...snapshot, pngBytes: png.length, output }));
