import { build } from "esbuild";
import { compile } from "json-schema-to-typescript";
import { readFile, writeFile, mkdir, copyFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const at = (path) => new URL(path, import.meta.url);
await writeFile(
    at("ui/host.generated.ts"),
    await compile(
        JSON.parse(await readFile(at("host-v1.schema.json"), "utf8")),
        "HostEnvelope",
        {
            bannerComment:
                "/* Generated from Rust host-v1.schema.json. Do not edit. */",
            unknownAny: false,
            style: JSON.parse(await readFile(at(".prettierrc.json"), "utf8")),
        },
    ),
);
const harness = process.argv.includes("--harness");
await mkdir(at("dist"), { recursive: true });
await build({
    entryPoints: [fileURLToPath(at("ui/main.tsx"))],
    bundle: true,
    outfile: fileURLToPath(at("dist/app.js")),
    platform: "browser",
    format: "esm",
    target: "es2022",
    minify: !harness,
    legalComments: "linked",
    define: {
        __DEV_HARNESS__: String(harness),
        "process.env.NODE_ENV": '"production"',
    },
});
for (const file of ["index.html", "style.css"])
    await copyFile(at("ui/" + file), at("dist/" + file));
console.log(
    `Built local ${harness ? "DEVELOPMENT HARNESS" : "normal"} frontend; no dev server.`,
);
