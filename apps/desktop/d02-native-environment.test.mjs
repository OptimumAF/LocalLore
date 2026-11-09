import assert from "node:assert/strict";
import path from "node:path";
import test from "node:test";
import { nativeHarnessEnvironment } from "./d02-native-environment.mjs";

const directory = path.resolve("synthetic evidence é");
const fixture = {
    LOCALLORE_D02_HARNESS: "1",
    LOCALLORE_TEST_MEMORY: "1",
    LOCALLORE_TEST_WORKSPACE: path.join(directory, "legacy-unused.sqlite"),
    LOCALLORE_D02_ARTIFACT_DIR: directory,
};

test("the native app child receives only the fixed LocalLore fixture selectors", () => {
    const parent = Object.freeze({
        LOCALLORE_D04_WORKER_SOURCE: "other-worker",
        locallore_d08_fork_harness: "1",
        LOCALLORE_TEST_MEMORY: "0",
        LocalLore_Test_Workspace: "other-workspace",
        LOCALLORE_D02_ARTIFACT_DIR: "other-evidence",
        LOCALLORE_D09_SHUTDOWN_CASE: "seven",
    });
    assert.deepEqual(nativeHarnessEnvironment(parent, directory), fixture);
    assert.equal(parent.LOCALLORE_TEST_MEMORY, "0");
    assert.equal(parent.LocalLore_Test_Workspace, "other-workspace");
});

test("the native child drops WebView2 runtime, profile and debug overrides", () => {
    assert.deepEqual(
        nativeHarnessEnvironment(
            {
                WEBVIEW2_BROWSER_EXECUTABLE_FOLDER: "other-runtime",
                WebView2_User_Data_Folder: "other-profile",
                WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS:
                    "--remote-debugging-port=9222",
                webview2_pipe_for_script_debugger: "other-debugger",
                WEBVIEW2_WAIT_FOR_SCRIPT_DEBUGGER: "1",
                COREWEBVIEW2_MAX_INSTANCES: "1",
            },
            directory,
        ),
        fixture,
    );
});

test("the native child retains ordinary operating system variables verbatim", () => {
    const ordinary = {
        Path: "tool location",
        SystemRoot: "windows",
        TEMP: "scratch",
    };
    assert.deepEqual(nativeHarnessEnvironment(ordinary, directory), {
        ...ordinary,
        ...fixture,
    });
});
