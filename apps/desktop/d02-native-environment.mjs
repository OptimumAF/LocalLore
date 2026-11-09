import path from "node:path";

export function nativeHarnessEnvironment(environment, directory) {
    // Windows environment names are case-insensitive. Keep the base fixture
    // and its app-owned WebView profile separate from ambient test/debug modes.
    return {
        ...Object.fromEntries(
            Object.entries(environment).filter(
                ([name]) =>
                    !/^(LOCALLORE_|WEBVIEW2_|COREWEBVIEW2_)/i.test(name),
            ),
        ),
        LOCALLORE_D02_HARNESS: "1",
        LOCALLORE_TEST_MEMORY: "1",
        LOCALLORE_TEST_WORKSPACE: path.join(directory, "legacy-unused.sqlite"),
        LOCALLORE_D02_ARTIFACT_DIR: directory,
    };
}
