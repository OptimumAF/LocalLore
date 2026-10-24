import { EvaluationController } from "./evaluation-controller";
import { ArchiveController } from "./archive-controller";
import { archiveBinding } from "./archive-model";
import { ForkController } from "./fork-controller";
import { MemoryMaintenanceController } from "./memory-maintenance-controller";
import { memoryContext } from "./memory-context";
import { BrokerRetention, type BrokerIdentity } from "./broker-retention";
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
            curated?: boolean;
            archiving?: boolean;
            timelining?: boolean;
            forking?: boolean;
            maintaining?: boolean;
            archiveStage?:
                "source" | "import" | "restarted" | "uncertain" | "retire";
        };
    }
}
const errors = new ErrorBuffer();
const brokerRetention = new BrokerRetention((surface) =>
    surface === "archive"
        ? archive.get().busy ||
          ["Wire", "Transport"].includes(archive.get().error ?? "")
        : surface === "fork"
          ? fork.get().busy || fork.get().status === "uncertain"
          : maintenance.get().busy || maintenance.get().uncertain,
);
const invoke = (command: string, args: Record<string, unknown> = {}) => {
    // One native broker retains one operation result. Keep the other surface
    // from replacing a completed result before its frontend consumes the reply.
    if (
        (command === "fork_start" && archive.get().busy) ||
        (command === "memory_maintenance_start" &&
            (archive.get().busy || fork.get().busy)) ||
        ([
            "archive_export_preview",
            "archive_import_preview",
            "archive_export",
            "archive_import",
        ].includes(command) &&
            (fork.get().busy ||
                maintenance.get().busy ||
                maintenance.get().operation?.running))
    )
        return Promise.reject("ArchiveBusy");
    const native = () => window.__TAURI__.core.invoke(command, args);
    if (command === "memory_maintenance_start") {
        const request = args.request as {
            session: string;
            scope: { story: string; branch: string };
            expected_head: number;
            action: string;
        };
        if (request.action !== "status" && controller.get().pending)
            return Promise.reject("Busy");
        const identity: BrokerIdentity = {
            surface: "memory",
            session: request.session,
            story: request.scope.story,
            branch: request.scope.branch,
            head: request.expected_head,
            action: request.action,
        };
        const retained = brokerRetention.get();
        if (
            request.action === "status" &&
            retained?.identity.surface === "memory" &&
            (retained.unknown ||
                !retained.terminal ||
                maintenance.get().uncertain) &&
            !retained.acknowledgedUnresolved
        )
            return brokerRetention.recoverMemory(identity, async () => {
                if (retained.operation !== null && !retained.unknown) {
                    const status = await window.__TAURI__.core.invoke(
                        "archive_status",
                        { operationId: retained.operation },
                    );
                    brokerRetention.observe(status);
                    if (!(
                        status &&
                        typeof status === "object" &&
                        (status as { running?: boolean }).running === false
                    ))
                        throw Error("ArchiveBusy");
                }
                return native();
            });
        return brokerRetention.start(identity, native);
    }
    if (command === "fork_start") {
        const input = args.input as {
            parent: { story: string; branch: string };
            expected_parent_revision: number;
            child_branch: string;
            at_revision: number;
        };
        return brokerRetention.start(
            {
                surface: "fork",
                session: String(args.session),
                story: input.parent.story,
                branch: input.parent.branch,
                head: input.expected_parent_revision,
                child: input.child_branch,
                at: input.at_revision,
                action: "fork",
            },
            native,
        );
    }
    if (
        [
            "archive_export_preview",
            "archive_import_preview",
            "archive_export",
            "archive_import",
        ].includes(command)
    ) {
        const selected = controller.selected();
        const isPreview = command.endsWith("_preview");
        const preview = archive.get().preview;
        // Capture the validated request binding before dispatch/context retirement.
        if (!isPreview && (!preview || args.token !== preview.token))
            return Promise.reject("InvalidArchiveInput");
        return brokerRetention.start(
            {
                surface: "archive",
                action: command,
                ...(selected
                    ? {
                          session: selected.id,
                          story: selected.scope.story,
                          branch: selected.scope.branch,
                          head:
                              controller.get().play?.revision ??
                              selected.revision,
                      }
                    : {}),
                ...(typeof args.token === "string"
                    ? { token: args.token }
                    : {}),
                ...(!isPreview ? { archive: archiveBinding(preview!) } : {}),
            },
            native,
        );
    }
    if (command === "archive_status" || command === "archive_cancel")
        return native().then((value) => {
            brokerRetention.observe(value);
            return value;
        });
    return native();
};
const driver =
    __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.enabled
        ? await import("./journeys")
        : null;
const evaluation = new EvaluationController(invoke, (code) =>
    errors.add("native", code),
);
const base = new IpcGateway(invoke, errors),
    gateway = driver ? new driver.FaultGateway(base) : base;
const controller = new Controller(gateway, errors, undefined, (work) =>
    capture.metadataControl(work),
);
const archive = new ArchiveController(invoke, () => controller.library());
const maintenance = new MemoryMaintenanceController(invoke);
let memorySelectionEpoch = 0,
    memorySelectionKey = "";
const forkRecoveryKey = "locallore-fork-recovery-v1";
const fork = new ForkController(
    invoke,
    () => controller.library(),
    (request) => {
        try {
            localStorage.setItem(forkRecoveryKey, JSON.stringify(request));
        } catch {
            throw Error("StorageUnavailable");
        }
    },
);
const releaseBrokerConsumption = [archive, fork, maintenance].map((surface) =>
    surface.subscribe(brokerRetention.refreshConsumption),
);
try {
    const saved = localStorage.getItem(forkRecoveryKey);
    if (saved !== null)
        fork.restore(saved.length <= 1024 ? JSON.parse(saved) : null);
} catch {
    fork.restore(null);
}
const capture = new CaptureController(gateway, () => controller.readTrace());
const timeline = new TimelineController(gateway, (scope) =>
    resumeTimeline(controller, scope),
);
// Invalidate evaluation replies before React observes a changed story/lens/Play
// context. Evaluation is independent of gameplay; no gameplay controller changes.
const syncEvaluationContext = () => {
    const s = controller.get();
    const memoryKey = JSON.stringify([
        s.selectedId,
        s.play?.scope,
        s.play?.revision,
        s.play?.player.observer,
        s.view,
        s.observer,
        s.disposed,
    ]);
    if (memoryKey !== memorySelectionKey) {
        memorySelectionKey = memoryKey;
        memorySelectionEpoch++;
    }
    maintenance.contextChanged(memoryContext(controller, memorySelectionEpoch));
    timeline.contextChanged(timelineContext(controller));
    fork.contextChanged(timelineContext(controller));
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
        fork={fork}
        maintenance={maintenance}
        maintenanceContext={() =>
            memoryContext(controller, memorySelectionEpoch)
        }
        brokerRetention={brokerRetention}
    />,
);
const dispose = async () => {
    for (const release of releaseBrokerConsumption) release();
    releaseEvaluationContext();
    evaluation.dispose();
    archive.dispose();
    timeline.dispose();
    fork.dispose();
    maintenance.dispose();
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
    if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.maintaining) {
        const { memoryNativeJourneys } =
            await import("./memory-native-journeys");
        await memoryNativeJourneys({
            controller,
            maintenance,
            brokerRetention,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.forking) {
        const { forkNativeJourneys } = await import("./fork-native-journeys");
        await forkNativeJourneys({
            controller,
            fork,
            timeline,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.timelining) {
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
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.curated) {
        const { curatedJourneys } = await import("./curated-journeys");
        await curatedJourneys({
            controller,
            evaluation,
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
