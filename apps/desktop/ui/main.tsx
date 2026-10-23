import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Controller } from "./controller";
import { ErrorBuffer, IpcGateway } from "./model";
declare const __DEV_HARNESS__: boolean;
declare global {
    interface Window {
        __TAURI__: {
            core: {
                invoke: (
                    command: string,
                    args?: Record<string, unknown>,
                ) => Promise<unknown>;
            };
        };
        __LOCALLORE_TEST__?: {
            enabled: boolean;
            backend: "native" | "headless";
            stage: "initial" | "reopened";
        };
    }
}
const errors = new ErrorBuffer();
const invoke = (command: string, args: Record<string, unknown> = {}) =>
    window.__TAURI__.core.invoke(command, args);
const driver =
    __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.enabled
        ? await import("./journeys")
        : null;
const base = new IpcGateway(invoke, errors),
    gateway = driver ? new driver.FaultGateway(base) : base,
    controller = new Controller(gateway, errors);
const onError = () => errors.add("frontend", "UnhandledError");
window.addEventListener("error", onError);
window.addEventListener("unhandledrejection", onError);
const root = createRoot(document.getElementById("root")!, {
    onUncaughtError: () => errors.add("frontend", "RenderError"),
    onRecoverableError: () => errors.add("frontend", "RenderError"),
});
root.render(<App controller={controller} />);
const dispose = async () => {
    await controller.dispose();
    root.unmount();
    window.removeEventListener("error", onError);
    window.removeEventListener("unhandledrejection", onError);
};
if (driver && window.__LOCALLORE_TEST__?.enabled) {
    await driver.journeys({
        controller,
        gateway: gateway as InstanceType<typeof driver.FaultGateway>,
        errors,
        invoke,
        dispose,
        config: window.__LOCALLORE_TEST__,
    });
} else {
    await controller.create();
}
window.addEventListener(
    "pagehide",
    () => {
        void dispose();
    },
    { once: true },
);
