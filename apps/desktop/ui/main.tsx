import { EvaluationController } from "./evaluation-controller";
import { ArchiveController } from "./archive-controller";
import { CaptureController } from "./capture-controller";
import {
    TimelineController,
    timelineContext,
    resumeTimeline,
} from "./timeline-controller";
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
            stage: "initial" | "reopened" | "restart";
            durable?: boolean;
            failure?: boolean;
            exporting?: boolean;
            localplay?: boolean;
            inspecting?: boolean;
            debugging?: boolean;
            capturing?: boolean;
            legacy?: boolean;
            evaluating?: boolean;
            archiving?: boolean;
            timelining?: boolean;
            archiveStage?:
                "source" | "import" | "restarted" | "uncertain" | "retire";
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
const evaluation = new EvaluationController(invoke);
const base = new IpcGateway(invoke, errors),
    gateway = driver ? new driver.FaultGateway(base) : base;
const controller = new Controller(gateway, errors, undefined, (work) =>
    capture.metadataControl(work),
);
const archive = new ArchiveController(invoke, () => controller.library());
const capture = new CaptureController(gateway, () => controller.readTrace());
const timeline = new TimelineController(gateway, (scope) =>
    resumeTimeline(controller, scope),
);
// Invalidate evaluation replies before React observes a changed story/lens/Play
// context. Evaluation is independent of gameplay; no gameplay controller changes.
const syncEvaluationContext = () => {
    const s = controller.get();
    timeline.contextChanged(timelineContext(controller));
    capture.contextChanged(
        controller.selected(),
        s.play?.revision ?? 0,
        s.view === "lab" &&
            s.observer === "omniscient" &&
            s.trace.shown &&
            !s.disposed,
        controller.traceAttempt(),
    );
    evaluation.contextChanged(
        `${s.selectedId}|${s.view}|${s.observer}`,
        s.view === "lab",
    );
    archive.contextChanged(
        `${s.selectedId}|${s.view}|${s.observer}`,
        s.view === "lab",
    );
};
const releaseEvaluationContext = controller.subscribe(syncEvaluationContext);
syncEvaluationContext();
const onError = () => errors.add("frontend", "UnhandledError");
window.addEventListener("error", onError);
window.addEventListener("unhandledrejection", onError);
const root = createRoot(document.getElementById("root")!, {
    onUncaughtError: () => errors.add("frontend", "RenderError"),
    onRecoverableError: () => errors.add("frontend", "RenderError"),
});
root.render(
    <App
        controller={controller}
        evaluation={evaluation}
        archive={archive}
        capture={capture}
        timeline={timeline}
    />,
);
const dispose = async () => {
    releaseEvaluationContext();
    evaluation.dispose();
    archive.dispose();
    timeline.dispose();
    await capture.dispose();
    await controller.dispose();
    root.unmount();
    window.removeEventListener("error", onError);
    window.removeEventListener("unhandledrejection", onError);
};
if (driver && window.__LOCALLORE_TEST__?.enabled) {
    const durableDriver =
        __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.durable
            ? await import("./durable-journeys")
            : null;
    const exportDriver =
        __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.exporting
            ? await import("./export-journeys")
            : null;
    const modelDriver =
        __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.localplay
            ? await import("./model-journeys")
            : null;
    const queryDriver =
        __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.inspecting
            ? await import("./query-journeys")
            : null;
    const traceDriver =
        __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.debugging
            ? await import("./trace-journeys")
            : null;
    const legacyDriver =
        __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.legacy
            ? await import("./legacy-journeys")
            : null;
    const run = legacyDriver
        ? legacyDriver.legacyJourneys
        : traceDriver
          ? traceDriver.traceJourneys
          : queryDriver
            ? queryDriver.queryJourneys
            : modelDriver
              ? modelDriver.modelJourneys
              : exportDriver
                ? exportDriver.exportJourneys
                : durableDriver
                  ? durableDriver.durableJourneys
                  : driver.journeys;
    if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.timelining) {
        const { timelineNativeJourneys } =
            await import("./timeline-native-journeys");
        await timelineNativeJourneys({
            controller,
            timeline,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.capturing) {
        const { captureJourneys } = await import("./capture-journeys");
        await captureJourneys({
            controller,
            capture,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.archiving) {
        const { archiveJourneys } = await import("./archive-journeys");
        await archiveJourneys({
            controller,
            archive,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.evaluating) {
        const { evaluationJourneys } = await import("./evaluation-journeys");
        await evaluationJourneys({
            controller,
            evaluation,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
    } else
        await run({
            controller,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
} else {
    await controller.start();
}
window.addEventListener(
    "pagehide",
    () => {
        void dispose();
    },
    { once: true },
);
