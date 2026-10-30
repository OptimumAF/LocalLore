import { EvaluationController } from "./evaluation-controller";
import { ComparisonReaderController } from "./comparison-reader-controller";
import {
    ComparisonRunController,
    createNativeComparisonRunController,
} from "./comparison-run-controller";
import { SelectedEvaluationController } from "./selected-evaluation-controller";
import { NativeCloseController } from "./native-close-controller";
import { ArchiveController } from "./archive-controller";
import { archiveBinding } from "./archive-model";
import { ForkController } from "./fork-controller";
import { MemoryMaintenanceController } from "./memory-maintenance-controller";
import { MemoryInspectionController } from "./memory-inspection-controller";
import { memoryInspectionContext } from "./memory-inspection-context";
import { memoryContext } from "./memory-context";
import { BrokerRetention, type BrokerIdentity } from "./broker-retention";
import { AuthorController } from "./author-controller";
import type { AuthorContext } from "./author-model";
import { checkedAuthorBrokerBinding } from "./author-broker-binding";
import { V2PlayController } from "./v2-play-controller";
import { CaptureController } from "./capture-controller";
import {
    TimelineController,
    timelineContext,
    resumeTimeline,
} from "./timeline-controller";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { Controller } from "./controller";
import { ErrorBuffer, IpcGateway, category } from "./model";
declare const __DEV_HARNESS__: boolean;
declare global {
    interface Window {
        __TAURI__: {
            event?: {
                listen: (
                    name: string,
                    listener: (event: { payload: unknown }) => void,
                ) => Promise<() => void>;
            };
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
            liveNarrationDiagnostic?: boolean;
            capturing?: boolean;
            legacy?: boolean;
            evaluating?: boolean;
            curated?: boolean;
            comparisonReading?: boolean;
            selectedEvaluating?: boolean;
            fullComparing?: boolean;
            nativeFullComparing?: boolean;
            sceneFullComparing?: boolean;
            sceneModelGuard?: boolean;
            inspectorPaging?: boolean;
            timelineBrowser?: boolean;
            domain2Fork?: boolean;
            nativeComparisonDenied?: boolean;
            archiving?: boolean;
            timelining?: boolean;
            forking?: boolean;
            maintaining?: boolean;
            inspectingMemory?: boolean;
            authoring?: boolean;
            sceneCase?: "literal" | "memory" | "";
            archiveStage?:
                | "source"
                | "import"
                | "restarted"
                | "uncertain"
                | "retire"
                | "v3-source"
                | "v3-import"
                | "v3-restarted"
                | "v3-continued"
                | "v3-continued-restarted"
                | "v3-uncertain";
        };
    }
}
const errors = new ErrorBuffer();
const sceneHarnessModule =
    __DEV_HARNESS__ &&
    ["literal", "memory"].includes(window.__LOCALLORE_TEST__?.sceneCase ?? "")
        ? await import("./scene-native-journeys")
        : null;
const authorHarnessModule =
    __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.authoring
        ? await import("./author-native-journeys")
        : null;
const authorTransport = authorHarnessModule
    ? new authorHarnessModule.AuthorHarnessTransport()
    : null;
const domain2ForkModule =
    __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.domain2Fork
        ? await import("./domain2-fork-native-journeys")
        : null;
const domain2ForkTrace = domain2ForkModule
    ? new domain2ForkModule.Domain2ForkTrace()
    : null;
const brokerRetention = new BrokerRetention((surface) =>
    surface === "author"
        ? author.get().busy ||
          author.get().uncertain ||
          ["Wire", "Transport", "UnknownArchiveOperation"].includes(
              author.get().error ?? "",
          )
        : surface === "archive"
          ? archive.get().busy ||
            ["Wire", "Transport"].includes(archive.get().error ?? "")
          : surface === "fork"
            ? fork.get().busy || fork.get().status === "uncertain"
            : maintenance.get().busy || maintenance.get().uncertain,
);
const invoke = (command: string, args: Record<string, unknown> = {}) => {
    if (
        command === "host_call" &&
        (author.get().busy || sharedBrokerBlocked())
    ) {
        // The UI gateway admits no new gameplay write while another surface
        // owns the shared operation. Rust still validates every native request.
        try {
            if (
                typeof args.input === "string" &&
                args.input.length <= 262144 &&
                ["prepare", "submit", "free_text", "commit"].includes(
                    JSON.parse(args.input)?.command?.op,
                )
            )
                return Promise.reject("Busy");
        } catch {
            /* Malformed wire is rejected by the native parser. */
        }
    }
    const authorStart = [
        "author_prepare_start",
        "author_commit_start",
        "author_lookup_start",
    ].includes(command);
    const otherSharedStart = [
        "fork_start",
        "memory_maintenance_start",
        "archive_export_preview",
        "archive_import_preview",
        "archive_export",
        "archive_import",
    ].includes(command);
    if (
        (otherSharedStart && author.get().busy) ||
        (authorStart &&
            (archive.get().busy ||
                fork.get().busy ||
                maintenance.get().busy ||
                !!controller.get().pending ||
                !!v2.get().pending ||
                !!v2.get().uncertain))
    )
        return Promise.reject("ArchiveBusy");
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
    const rawNative = () =>
        domain2ForkTrace
            ? domain2ForkTrace.dispatch(command, args, () =>
                  window.__TAURI__.core.invoke(command, args),
              )
            : window.__TAURI__.core.invoke(command, args);
    const native = () =>
        authorTransport
            ? authorTransport.native(command, args, rawNative)
            : rawNative();
    if (authorStart) {
        try {
            if (typeof args.request !== "string") throw Error("InvalidInput");
            const request = JSON.parse(args.request);
            const action =
                command === "author_prepare_start"
                    ? "prepare"
                    : command === "author_commit_start"
                      ? "commit"
                      : "lookup";
            const binding = checkedAuthorBrokerBinding({
                action,
                session: request.session ?? controller.selected()?.id,
                input: request.input,
            });
            return brokerRetention.start(
                {
                    surface: "author",
                    action,
                    session: binding.session,
                    story: binding.input.parent.story,
                    branch: binding.input.parent.branch,
                    head: binding.input.expected_parent_revision,
                    child: binding.input.child_branch,
                    at: binding.input.fork_revision,
                    author: binding,
                },
                native,
            );
        } catch (error) {
            return Promise.reject(error);
        }
    }
    if (command === "memory_maintenance_start") {
        const request = args.request as {
            session: string;
            scope: { story: string; branch: string };
            expected_head: number;
            action: string;
        };
        if (
            request.action !== "status" &&
            (controller.get().pending || v2.get().pending || v2.get().uncertain)
        )
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
    if (command === "archive_status" || command === "archive_cancel") {
        const owner = brokerRetention.get()?.identity;
        const operationId = args.operationId;
        return native().then(
            async (value) => {
                if (owner?.surface === "author") {
                    if (brokerRetention.get()?.identity === owner)
                        await brokerRetention.observeAuthor(value);
                } else brokerRetention.observe(value);
                return value;
            },
            (error) => {
                if (owner?.surface === "author")
                    brokerRetention.observeAuthorFailure(owner, operationId);
                throw error;
            },
        );
    }
    return native();
};
const driver =
    __DEV_HARNESS__ && window.__LOCALLORE_TEST__?.enabled
        ? await import("./journeys")
        : null;
const evaluation = new EvaluationController(invoke, (code) =>
    errors.add("native", code),
);
const comparison = new ComparisonReaderController(invoke, (code) =>
    errors.add("native", code),
);
const comparisonRun = new ComparisonRunController(invoke, (code) =>
    errors.add("native", code),
);
const nativeComparisonRun = createNativeComparisonRunController(
    invoke,
    (code) => errors.add("native", code),
);
const selectedEvaluation = new SelectedEvaluationController(invoke, (code) =>
    errors.add("native", code),
);
const nativeClose = new NativeCloseController(invoke, () =>
    errors.add("native", "NativeCloseStatusUnavailable"),
);
const releaseNativeClose = await window.__TAURI__.event
    ?.listen("locallore-close-status", (event) =>
        nativeClose.receive(event.payload),
    )
    .catch(() => {
        errors.add("native", "NativeCloseStatusUnavailable");
        return undefined;
    });
const base = new IpcGateway(invoke, errors),
    gateway = driver ? new driver.FaultGateway(base) : base;
const controller = new Controller(
    gateway,
    errors,
    undefined,
    (work, closingSession) => capture.metadataControl(work, closingSession),
    !!sceneHarnessModule,
);
const archive = new ArchiveController(invoke, () => controller.library());
const maintenance = new MemoryMaintenanceController(invoke);
const memoryInspection = new MemoryInspectionController(invoke);
const v2 = new V2PlayController(gateway, async () => {
    await controller.refresh();
    if (controller.get().workspace) await controller.library();
});
const author = new AuthorController(
    {
        prepareStart: (request) => invoke("author_prepare_start", { request }),
        commitStart: (request) => invoke("author_commit_start", { request }),
        lookupStart: (request) => invoke("author_lookup_start", { request }),
        status: (operationId) => invoke("archive_status", { operationId }),
        cancel: (operationId) => invoke("archive_cancel", { operationId }),
        discardPreview: (session, preview_token) =>
            invoke("author_preview_discard", {
                request: JSON.stringify({ version: 1, session, preview_token }),
            }).then((value) => {
                if (typeof value !== "boolean") throw Error("Wire");
                return value;
            }),
    },
    {
        refreshLibrary: () => controller.library(),
        openChild: (scope) => resumeTimeline(controller, scope),
    },
);
let authorNativeContext: { root: string; granted: boolean } | null = null;
let stopping = false;
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
const releaseBrokerConsumption = [archive, fork, maintenance, author].map(
    (surface) => surface.subscribe(brokerRetention.refreshConsumption),
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
function sharedBrokerBlocked() {
    const retained = brokerRetention.get();
    return (
        !!retained &&
        (retained.inFlight ||
            (!retained.acknowledgedUnresolved &&
                (retained.unknown || !retained.terminal || !retained.consumed)))
    );
}
function syncV2Context() {
    const s = controller.get(),
        selected = controller.selected();
    v2.selectedContextChanged(
        selected && s.playV2 && !s.disposed
            ? {
                  session: selected.id,
                  scope: selected.scope,
                  revision: s.playV2.revision,
                  player: s.playV2.player.observer,
                  view: s.view,
                  observer:
                      s.view === "play" || s.observer === "player"
                          ? { kind: "player" }
                          : s.observer === "omniscient"
                            ? { kind: "omniscient" }
                            : { kind: "character", id: s.observer },
                  persistent: !!s.workspace,
                  pending: !!s.pending,
                  blocked: author.get().busy || sharedBrokerBlocked(),
                  playMode: s.playMode,
                  freeTextProvider: s.freeTextProvider,
                  inputKind: s.inputKind,
                  action: s.action,
                  fakeMode: s.fakeMode,
              }
            : null,
    );
}
function syncTraceGameplayFence() {
    const s = controller.get(),
        selected = controller.selected(),
        play = s.play ?? s.playV2,
        gameplay = v2.get();
    controller.setTraceGameplayFence(
        !stopping && !s.disposed && selected && play
            ? {
                  session: selected.id,
                  story: play.scope.story,
                  branch: play.scope.branch,
                  head: play.revision,
                  player: play.player.observer,
                  pending: !!s.pending || !!gameplay.pending,
                  uncertain: !!gameplay.uncertain,
              }
            : null,
    );
}
function syncForkAdmission() {
    const s = controller.get(),
        gameplay = v2.get();
    fork.setAdmissionBlocked(
        stopping ||
            s.starting ||
            !!s.pending ||
            s.disposed ||
            !!gameplay.pending ||
            !!gameplay.uncertain ||
            !fork.matchesContext(timelineContext(controller)),
    );
}
// Invalidate evaluation replies before React observes a changed story/lens/Play
// context. Evaluation is independent of gameplay; no gameplay controller changes.
const syncEvaluationContext = () => {
    const s = controller.get();
    const play = s.play ?? s.playV2;
    const memoryKey = JSON.stringify([
        s.selectedId,
        play?.scope,
        play?.revision,
        play?.player.observer,
        s.view,
        s.observer,
        s.disposed,
    ]);
    if (memoryKey !== memorySelectionKey) {
        memorySelectionKey = memoryKey;
        memorySelectionEpoch++;
    }
    syncV2Context();
    syncForkAdmission();
    syncTraceGameplayFence();
    author.contextChanged(authorContext());
    maintenance.contextChanged(memoryContext(controller, memorySelectionEpoch));
    memoryInspection.contextChanged(
        memoryInspectionContext(
            controller,
            memorySelectionEpoch,
            authorNativeContext?.granted === true,
        ),
    );
    timeline.contextChanged(timelineContext(controller));
    fork.contextChanged(timelineContext(controller));
    syncForkAdmission();
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
    // Only actual selection/head/native context changes retire a reader. Its
    // own pending/read updates are excluded from this presentation identity.
    comparison.contextChanged(
        JSON.stringify([
            authorNativeContext?.root ?? null,
            authorNativeContext?.granted ?? false,
            s.selectedId,
            play?.scope ?? null,
            play?.revision ?? null,
            s.view,
            s.observer,
            s.disposed,
        ]),
        !!authorNativeContext?.granted && s.view === "lab" && !s.disposed,
    );
    // The observer is a read lens. It never changes an experiment's execution
    // identity, admission, cancellation or generation permissions.
    const comparisonExecutionKey = JSON.stringify([
        authorNativeContext?.root ?? null,
        authorNativeContext?.granted ?? false,
        s.selectedId,
        play?.scope ?? null,
        play?.revision ?? null,
        s.view,
        s.disposed,
    ]);
    const comparisonAllowed =
        !!authorNativeContext?.granted && s.view === "lab" && !s.disposed;
    comparisonRun.setContext(comparisonExecutionKey, comparisonAllowed);
    nativeComparisonRun.setContext(comparisonExecutionKey, comparisonAllowed);
    selectedEvaluation.setContext(
        JSON.stringify([
            authorNativeContext?.root ?? null,
            authorNativeContext?.granted ?? false,
            s.selectedId,
            play?.scope ?? null,
            play?.revision ?? null,
            s.view,
            s.disposed,
        ]),
        !!authorNativeContext?.granted && s.view === "lab" && !s.disposed,
    );
    archive.contextChanged(
        `${s.selectedId}|${s.view}|${s.observer}`,
        s.view === "lab",
    );
};
function authorContext(): AuthorContext | null {
    const s = controller.get(),
        selected = controller.selected(),
        play = s.play ?? s.playV2,
        retained = brokerRetention.get();
    if (!selected || !play || !authorNativeContext || s.disposed) return null;
    return {
        rootIncarnation: authorNativeContext.root,
        selectionEpoch: memorySelectionEpoch,
        session: selected.id,
        scope: selected.scope,
        head: play.revision,
        player: play.player.observer,
        observer: s.view === "play" ? "player" : s.observer,
        view: s.view,
        persistent: !!s.workspace,
        spoilerGranted: authorNativeContext.granted && s.view === "lab",
        pending: !!s.pending || !!v2.get().pending || !!v2.get().uncertain,
        brokerUncertain:
            !!retained && !retained.acknowledgedUnresolved && retained.unknown,
    };
}
const releaseEvaluationContext = controller.subscribe(syncEvaluationContext);
const releaseV2Context = v2.subscribe(() => {
    syncForkAdmission();
    syncTraceGameplayFence();
    author.contextChanged(authorContext());
});
const releaseAuthorContext = author.subscribe(syncV2Context);
const releaseRetainedContext = brokerRetention.subscribe(syncEvaluationContext);
syncEvaluationContext();
void invoke("author_context")
    .then((value) => {
        if (!value || typeof value !== "object" || Array.isArray(value))
            throw Error("Wire");
        const metadata = value as Record<string, unknown>;
        if (
            Object.keys(metadata).sort().join(",") !==
                "root_incarnation,story_lab_granted,version,window_epoch" ||
            metadata.version !== 1 ||
            typeof metadata.root_incarnation !== "string" ||
            !/^[A-Za-z0-9_-]{1,64}$/.test(metadata.root_incarnation) ||
            !Number.isSafeInteger(metadata.window_epoch) ||
            Number(metadata.window_epoch) < 1 ||
            typeof metadata.story_lab_granted !== "boolean"
        )
            throw Error("Wire");
        authorNativeContext = {
            root: `${metadata.root_incarnation}_${metadata.window_epoch}`,
            granted: metadata.story_lab_granted,
        };
        syncEvaluationContext();
    })
    .catch((error) => {
        errors.add("native", category(error));
        authorNativeContext = null;
        author.contextChanged(null);
        syncEvaluationContext();
    });
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
        comparison={comparison}
        selectedEvaluation={selectedEvaluation}
        comparisonRun={comparisonRun}
        nativeComparisonRun={nativeComparisonRun}
        nativeClose={nativeClose}
        archive={archive}
        capture={capture}
        timeline={timeline}
        fork={fork}
        maintenance={maintenance}
        memoryInspection={memoryInspection}
        memoryInspectionContext={() =>
            memoryInspectionContext(
                controller,
                memorySelectionEpoch,
                authorNativeContext?.granted === true,
            )
        }
        maintenanceContext={() =>
            memoryContext(controller, memorySelectionEpoch)
        }
        brokerRetention={brokerRetention}
        author={author}
        authorContext={authorContext}
        v2={v2}
    />,
);
const dispose = async () => {
    stopping = true;
    syncForkAdmission();
    controller.setTraceGameplayFence(null);
    for (const release of releaseBrokerConsumption) release();
    releaseEvaluationContext();
    releaseV2Context();
    releaseAuthorContext();
    releaseRetainedContext();
    author.dispose();
    await v2.dispose();
    evaluation.dispose();
    comparison.dispose();
    selectedEvaluation.dispose();
    comparisonRun.dispose();
    nativeComparisonRun.dispose();
    releaseNativeClose?.();
    archive.dispose();
    timeline.dispose();
    fork.dispose();
    maintenance.dispose();
    memoryInspection.dispose();
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
    const sceneCase = window.__LOCALLORE_TEST__?.sceneCase;
    if (
        __DEV_HARNESS__ &&
        window.__LOCALLORE_TEST__?.domain2Fork &&
        domain2ForkModule &&
        domain2ForkTrace
    ) {
        await domain2ForkModule.domain2ForkNativeJourneys({
            controller,
            fork,
            timeline,
            v2,
            errors,
            invoke,
            trace: domain2ForkTrace,
            dispose,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.timelineBrowser) {
        const { domain2TimelineBrowserNativeJourneys } =
            await import("./domain2-timeline-browser-native-journeys");
        await domain2TimelineBrowserNativeJourneys({
            controller,
            timeline,
            v2,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.inspectorPaging) {
        const { v2InspectorPagingNativeJourneys } =
            await import("./v2-inspector-paging-native-journeys");
        await v2InspectorPagingNativeJourneys({
            controller,
            v2,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
        });
    } else if (
        __DEV_HARNESS__ &&
        window.__LOCALLORE_TEST__?.liveNarrationDiagnostic === true &&
        sceneHarnessModule &&
        sceneCase === "literal"
    ) {
        const { liveNarrationNativeJourneys } =
            await import("./live-narration-native-journeys");
        await liveNarrationNativeJourneys({
            controller,
            v2,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: {
                stage: window.__LOCALLORE_TEST__.stage,
                sceneCase,
                liveNarrationDiagnostic: true,
            },
        });
    } else if (
        sceneHarnessModule &&
        (sceneCase === "literal" || sceneCase === "memory")
    ) {
        await sceneHarnessModule.sceneNativeJourneys({
            controller,
            v2,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: { stage: window.__LOCALLORE_TEST__!.stage, sceneCase },
        });
    } else if (authorHarnessModule && authorTransport) {
        await authorHarnessModule.authorNativeJourneys({
            controller,
            author,
            v2,
            brokerRetention,
            gateway: gateway as InstanceType<typeof driver.FaultGateway>,
            errors,
            invoke,
            dispose,
            config: window.__LOCALLORE_TEST__,
            transport: authorTransport,
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.maintaining) {
        if (window.__LOCALLORE_TEST__.inspectingMemory) {
            const { memoryInspectionNativeJourneys } =
                await import("./memory-inspection-native-journeys");
            await memoryInspectionNativeJourneys({
                controller,
                maintenance,
                inspection: memoryInspection,
                brokerRetention,
                gateway: gateway as InstanceType<typeof driver.FaultGateway>,
                errors,
                invoke,
                dispose,
                config: window.__LOCALLORE_TEST__,
            });
        } else {
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
        }
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
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.sceneModelGuard) {
        const { sceneModelGuardJourneys } =
            await import("./scene-model-guard-journeys");
        await sceneModelGuardJourneys({ invoke, dispose, errors });
    } else if (
        __DEV_HARNESS__ &&
        window.__LOCALLORE_TEST__?.nativeFullComparing
    ) {
        const { comparisonRunNativeJourneys } =
            await import("./comparison-run-native-journeys");
        await comparisonRunNativeJourneys({
            controller,
            comparison,
            full: nativeComparisonRun,
            errors,
            invoke,
            dispose,
            config: {
                stage: window.__LOCALLORE_TEST__.stage,
                scene: window.__LOCALLORE_TEST__.sceneFullComparing === true,
            },
        });
    } else if (__DEV_HARNESS__ && window.__LOCALLORE_TEST__?.fullComparing) {
        const { comparisonRunJourneys } =
            await import("./comparison-run-journeys");
        await comparisonRunJourneys({
            controller,
            comparison,
            full: comparisonRun,
            errors,
            invoke,
            dispose,
            config: {
                stage: window.__LOCALLORE_TEST__.stage,
                nativeGrantDenied:
                    window.__LOCALLORE_TEST__.nativeComparisonDenied === true,
            },
        });
    } else if (
        __DEV_HARNESS__ &&
        window.__LOCALLORE_TEST__?.selectedEvaluating
    ) {
        const { selectedEvaluationJourneys } =
            await import("./selected-evaluation-journeys");
        await selectedEvaluationJourneys({
            controller,
            comparison,
            selected: selectedEvaluation,
            errors,
            invoke,
            dispose,
            config: { stage: window.__LOCALLORE_TEST__.stage },
        });
    } else if (
        __DEV_HARNESS__ &&
        window.__LOCALLORE_TEST__?.comparisonReading
    ) {
        const { comparisonReaderJourneys } =
            await import("./comparison-reader-journeys");
        await comparisonReaderJourneys({
            controller,
            comparison,
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
        if (window.__LOCALLORE_TEST__.archiveStage?.startsWith("v3-")) {
            const { archiveV3Journeys } = await import("./archive-v3-journeys");
            await archiveV3Journeys({
                controller,
                archive,
                v2,
                retention: brokerRetention,
                errors,
                invoke,
                dispose,
                config: window.__LOCALLORE_TEST__,
            });
        } else {
            const { archiveJourneys } = await import("./archive-journeys");
            await archiveJourneys({
                controller,
                archive,
                errors,
                invoke,
                dispose,
                config: window.__LOCALLORE_TEST__,
            });
        }
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
