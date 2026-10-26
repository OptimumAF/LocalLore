import { EvaluationPanel } from "./EvaluationPanel";
import { ComparisonReaderPanel } from "./ComparisonReaderPanel";
import {
    ComparisonRunView,
    ComparisonRunCleanupView,
} from "./comparison-run-view";
import type { ComparisonRunController } from "./comparison-run-controller";
import { SelectedEvaluationView } from "./selected-evaluation-view";
import type { SelectedEvaluationController } from "./selected-evaluation-controller";
import type { NativeCloseController } from "./native-close-controller";
import type { ComparisonReaderController } from "./comparison-reader-controller";
import { ArchivePanel } from "./ArchivePanel";
import type { ArchiveController } from "./archive-controller";
import { TimelinePanel } from "./TimelinePanel";
import { ForkPanel } from "./ForkPanel";
import { MemoryMaintenancePanel } from "./MemoryMaintenancePanel";
import { BrokerRetentionPanel } from "./BrokerRetentionPanel";
import { AuthorPanel } from "./AuthorPanel";
import type { AuthorController } from "./author-controller";
import type { AuthorContext } from "./author-model";
import { V2PlayPanel } from "./V2PlayPanel";
import type { V2PlayController, V2PlayState } from "./v2-play-controller";
import type { BrokerRetention } from "./broker-retention";
import type {
    MemoryContext,
    MemoryMaintenanceController,
} from "./memory-maintenance-controller";
import type { ForkController } from "./fork-controller";
import { timelineContext } from "./timeline-controller";
import type { TimelineController } from "./timeline-controller";
import type { EvaluationController } from "./evaluation-controller";
import { TurnDebugger } from "./TurnDebugger";
import { CapturePanel } from "./CapturePanel";
import type { CaptureController } from "./capture-controller";
import {
    useCallback,
    useEffect,
    useRef,
    useState,
    useSyncExternalStore,
} from "react";
import { Controller } from "./controller";
import { ModelPanel } from "./ModelPanel";
import { QueryInspector } from "./QueryInspector";
import { InspectionPanel } from "./InspectionPanel";
import { PAGE_SIZE, composerShortcut } from "./model";
import type { Action, FakeMode, Receipt } from "./model";
const actions: Record<Action, string> = {
    give: "Give last potion to Mira",
    wait: "Wait one tide tick",
    ability: "Attempt unlearned teleport",
    dialogue: "Say draft aloud to Mira",
};
const noScopedSubscription = () => () => {};
const noScopedSnapshot = () => null;
function useComparisonSnapshot(controller?: ComparisonRunController) {
    const subscribe = useCallback(
        (listener: () => void) => controller?.subscribe(listener) ?? (() => {}),
        [controller],
    );
    const get = useCallback(() => controller?.get() ?? null, [controller]);
    return useSyncExternalStore(subscribe, get, get);
}
function comparisonBlocked(controller?: ComparisonRunController): boolean {
    const state = controller?.get();
    return (
        !!state &&
        (state.busy ||
            !!state.pending ||
            state.uncertain ||
            (state.mode === "approved_native" &&
                (state.cleanupPending !== null ||
                    state.cleanupUncertain ||
                    state.cleanup?.cleanup_required === true ||
                    state.cleanup?.running === true ||
                    state.cleanup?.error != null ||
                    state.status?.cleanup_required === true ||
                    state.status?.cleanup_running === true)))
    );
}
function intent(r: Receipt) {
    return r.request.intent.kind === "free_text"
        ? r.request.intent.value.text
        : r.request.intent.kind === "dialogue"
          ? r.request.intent.value.text
          : r.request.intent.kind === "actions"
            ? r.request.intent.value
                  .map((c) => c.op.replaceAll("_", " "))
                  .join(", ")
            : r.request.intent.kind;
}
function LabAcknowledgement({ controller: c }: { controller: Controller }) {
    const dialog = useRef<HTMLDialogElement>(null);
    useEffect(() => {
        dialog.current?.showModal();
        return () => dialog.current?.close();
    }, []);
    return (
        <dialog
            ref={dialog}
            className="spoiler-dialog"
            aria-labelledby="spoiler-title"
            onCancel={(event) => {
                event.preventDefault();
                c.acknowledgeLab(false);
            }}
        >
            <h2 id="spoiler-title">Open Story Lab?</h2>
            <p>
                Private character and omniscient inspection can reveal spoilers.
                This lens never grants characters knowledge or changes the
                player.
            </p>
            <button autoFocus onClick={() => c.acknowledgeLab(true)}>
                I understand; reveal spoilers
            </button>
            <button onClick={() => c.acknowledgeLab(false)}>
                Stay in Play
            </button>
        </dialog>
    );
}
function SelectedExperiment({
    comparison,
    selected,
}: {
    comparison: ComparisonReaderController;
    selected: SelectedEvaluationController;
}) {
    const snapshot = useSyncExternalStore(
        (listener) => comparison.subscribe(listener),
        () => comparison.get(),
        () => comparison.get(),
    );
    const source =
        snapshot.clientId &&
        snapshot.status?.run_token &&
        snapshot.source &&
        (snapshot.source.protocol_version === 2 ||
            snapshot.source.protocol_version === 3)
            ? {
                  readerClientId: snapshot.clientId,
                  runToken: snapshot.status.run_token,
                  binding: snapshot.source.binding,
              }
            : null;
    return (
        <SelectedEvaluationView
            controller={selected}
            source={source}
            row={snapshot.selected}
            observer={snapshot.observer}
        />
    );
}
function NativeCloseNotice({
    controller,
}: {
    controller: NativeCloseController;
}) {
    const phase = useSyncExternalStore(
        controller.subscribe,
        controller.get,
        controller.get,
    );
    if (phase === "open") return null;
    return (
        <aside
            role="status"
            aria-live="assertive"
            className="comparison-unavailable"
            data-native-close={phase}
        >
            {phase === "close_failed" ? (
                <>
                    Worker cleanup is confirmed. LocalLore could not close its
                    window.{" "}
                    <button onClick={() => void controller.retry()}>
                        Retry close
                    </button>
                </>
            ) : phase === "cleanup_required" ? (
                <>
                    Worker cleanup is not confirmed. LocalLore is staying open
                    and new work is blocked.{" "}
                    <button onClick={() => void controller.retry()}>
                        Retry cleanup and close
                    </button>
                </>
            ) : phase === "closing" ? (
                "Stopping work and confirming local worker cleanup…"
            ) : (
                "Cleanup confirmed. Closing LocalLore…"
            )}
        </aside>
    );
}
export function App({
    controller: c,
    capture,
    evaluation,
    comparison,
    selectedEvaluation,
    comparisonRun,
    nativeComparisonRun,
    nativeClose,
    archive,
    timeline,
    fork,
    maintenance,
    maintenanceContext,
    brokerRetention,
    author,
    authorContext,
    v2,
}: {
    controller: Controller;
    capture?: CaptureController;
    evaluation?: EvaluationController;
    comparison?: ComparisonReaderController;
    selectedEvaluation?: SelectedEvaluationController;
    comparisonRun?: ComparisonRunController;
    nativeComparisonRun?: ComparisonRunController;
    nativeClose?: NativeCloseController;
    archive?: ArchiveController;
    timeline?: TimelineController;
    fork?: ForkController;
    maintenance?: MemoryMaintenanceController;
    maintenanceContext?: () => MemoryContext | null;
    brokerRetention?: BrokerRetention;
    author?: AuthorController;
    authorContext?: () => AuthorContext | null;
    v2?: V2PlayController;
}) {
    const s = useSyncExternalStore(c.subscribe, c.get),
        selected = c.selected(),
        receipt = c.receipt();
    const scoped = useSyncExternalStore<V2PlayState | null>(
        v2?.subscribe ?? noScopedSubscription,
        v2?.get ?? noScopedSnapshot,
    );
    const receipts = s.play?.receipts ?? [],
        rows = receipts.slice(s.page * PAGE_SIZE, (s.page + 1) * PAGE_SIZE);
    const play = s.play ?? s.playV2;
    useComparisonSnapshot(comparisonRun);
    useComparisonSnapshot(nativeComparisonRun);
    type RunMode = "scripted_baseline" | "approved_native";
    const [runMode, setRunMode] = useState<RunMode>("scripted_baseline");
    const modeRef = useRef<RunMode>("scripted_baseline");
    const switchRef = useRef({ epoch: 0, active: false });
    const [switching, setSwitching] = useState(false);
    const activeRun =
        runMode === "approved_native" && nativeComparisonRun
            ? nativeComparisonRun
            : comparisonRun;
    const inactiveRun =
        activeRun === nativeComparisonRun ? comparisonRun : nativeComparisonRun;
    // Reading both snapshots subscribes the selector to real operation/cleanup
    // changes. None of these presentation observations rekeys execution.
    const runBlocked =
        comparisonBlocked(comparisonRun) ||
        comparisonBlocked(nativeComparisonRun);
    const switchRunMode = async (requested: string) => {
        if (
            (requested !== "scripted_baseline" &&
                requested !== "approved_native") ||
            requested === modeRef.current ||
            switchRef.current.active ||
            !comparisonRun ||
            !nativeComparisonRun ||
            comparisonBlocked(comparisonRun) ||
            comparisonBlocked(nativeComparisonRun)
        )
            return;
        const old =
            modeRef.current === "approved_native"
                ? nativeComparisonRun
                : comparisonRun;
        const contexts = [
            comparisonRun.get().context,
            nativeComparisonRun.get().context,
        ];
        const epoch = ++switchRef.current.epoch;
        switchRef.current.active = true;
        setSwitching(true);
        try {
            await old.close();
            if (
                switchRef.current.epoch !== epoch ||
                comparisonRun.get().context !== contexts[0] ||
                nativeComparisonRun.get().context !== contexts[1] ||
                comparisonBlocked(comparisonRun) ||
                comparisonBlocked(nativeComparisonRun)
            )
                return;
            modeRef.current = requested;
            setRunMode(requested);
        } finally {
            if (switchRef.current.epoch === epoch) {
                switchRef.current.active = false;
                setSwitching(false);
            }
        }
    };
    const inspectRun = async (
        origin: ComparisonRunController,
        runId: string,
    ) => {
        if (!comparison || switchRef.current.active) return;
        const mode: RunMode =
            origin === nativeComparisonRun
                ? "approved_native"
                : "scripted_baseline";
        const before = origin.get();
        const epoch = switchRef.current.epoch;
        if (
            modeRef.current !== mode ||
            !before.allowed ||
            comparisonBlocked(origin) ||
            before.status?.run_id !== runId ||
            !before.status.report_ready ||
            before.status.phase === "closed"
        )
            return;
        await comparison.close();
        const current = origin.get();
        if (
            switchRef.current.active ||
            switchRef.current.epoch !== epoch ||
            modeRef.current !== mode ||
            current.context !== before.context ||
            !current.allowed ||
            comparisonBlocked(origin) ||
            current.clientId !== before.clientId ||
            current.status?.run_id !== runId ||
            current.status.operation_id !== before.status.operation_id ||
            !current.status.report_ready ||
            current.status.phase === "closed"
        )
            return;
        if (mode === "approved_native")
            await comparison.pickManaged({ runId, mode });
        else await comparison.pick(runId);
    };
    return (
        <div
            className={`app text-${s.textScale} side-${s.sidebarSize} detail-${s.inspectorSize}`}
        >
            {nativeClose && <NativeCloseNotice controller={nativeClose} />}
            <a
                href={
                    s.playV2
                        ? "#v2-play"
                        : s.trace.shown
                          ? "#trace-controls"
                          : s.query.shown
                            ? "#memory-controls"
                            : "#composer"
                }
                className="skip"
            >
                {s.playV2
                    ? "Skip to current timeline"
                    : s.trace.shown
                      ? "Skip to trace controls"
                      : s.query.shown
                        ? "Skip to memory controls"
                        : "Skip to composer"}
            </a>
            <header className="brandbar">
                <strong className="brand">LocalLore</strong>
                <nav className="mode-tabs" aria-label="Workspace mode">
                    <button
                        aria-pressed={s.view === "play"}
                        onClick={() => c.setView("play")}
                    >
                        Play
                    </button>
                    <button
                        aria-pressed={s.view === "lab"}
                        onClick={() => c.requestLab()}
                    >
                        Story Lab · spoilers
                    </button>
                </nav>
                <span className="limitation">
                    Local Rust |{" "}
                    {s.playMode === "local"
                        ? "Experimental local CPU"
                        : "Fake fixture inference"}{" "}
                    |{" "}
                    {s.workspace
                        ? "Saved locally"
                        : s.ephemeral
                          ? "In-memory only · not saved"
                          : s.starting
                            ? "Opening storage..."
                            : "Storage unavailable"}
                </span>
            </header>
            {s.labPending && <LabAcknowledgement controller={c} />}
            <div
                className={`workspace ${!s.playV2 && s.inspectorOpen && !s.query.shown && !s.trace.shown ? "" : "collapsed"}`}
            >
                <aside className="sidebar" aria-label="Story sessions">
                    <h2>
                        {s.ephemeral ? "Fixture sessions" : "Saved stories"}
                    </h2>
                    {s.workspace?.stories.map((story) => (
                        <button
                            className="session"
                            key={`${story.scope.story}/${story.scope.branch}`}
                            onClick={() => void c.resume(story.scope)}
                            disabled={s.starting}
                        >
                            <span>{story.title}</span>
                            <small>
                                {story.scope.story} / {story.scope.branch} |
                                revision {story.revision}
                            </small>
                        </button>
                    ))}
                    <div className="export-actions">
                        <button
                            onClick={() => void c.showQuery(!s.query.shown)}
                            aria-pressed={s.query.shown}
                            disabled={!!s.playV2}
                        >
                            Memory & evidence
                        </button>
                        <button
                            onClick={() => void c.showTrace(!s.trace.shown)}
                            aria-pressed={s.trace.shown}
                            disabled={!!s.playV2}
                        >
                            Turn debugger
                        </button>
                        <button onClick={() => c.showModel()}>
                            Local model management
                        </button>
                        <button
                            disabled={!!s.playV2}
                            onClick={() => c.showExports()}
                        >
                            Inspection snapshots
                        </button>
                        <button onClick={() => void c.revealStorage()}>
                            Reveal storage in app
                        </button>
                    </div>
                    <h3>Open in this window</h3>
                    <button
                        className="new"
                        disabled={
                            s.sessions.length >= 4 ||
                            s.starting ||
                            (!s.workspace && !s.ephemeral)
                        }
                        onClick={() => void c.create()}
                    >
                        ＋ New Lantern Quay
                    </button>
                    <div className="session-list">
                        {s.sessions.map((session) => (
                            <button
                                className="session"
                                key={session.id}
                                aria-current={session.id === s.selectedId}
                                onClick={() => void c.switchSession(session.id)}
                            >
                                <span>{session.name}</span>
                                <small>
                                    {session.scope.branch} · revision{" "}
                                    {session.revision}
                                </small>
                            </button>
                        ))}
                    </div>
                    <p>
                        {s.ephemeral
                            ? "Progress stays in memory. Closing or resetting discards this fixture session; nothing is saved."
                            : "Close releases this window's session; the saved story remains. New and Reset create a separate saved story."}
                    </p>
                    <p>
                        Unsubmitted composer text stays in this session only.
                        Arbitrary story creation remains unavailable. Local
                        inference is an explicit experimental CPU profile.
                    </p>
                    {s.workspace && (
                        <details>
                            <summary>Saved workspace</summary>
                            <p className="storage-path">
                                {s.workspace.location}
                            </p>
                            <p>
                                SQLite schema{" "}
                                {s.workspace.database_schema_version ??
                                    "Not reported"}{" "}
                                | Workspace contract{" "}
                                {s.workspace.schema_version} | Domain contract
                                domain-v{s.playV2?.domain_version ?? 1} | Rules{" "}
                                {play?.rules ?? "unavailable"} | Canonical
                                receipts and validated replay
                            </p>
                        </details>
                    )}
                    {!s.workspace && !s.ephemeral && !s.starting && (
                        <button onClick={() => void c.start()}>
                            Retry opening saved workspace
                        </button>
                    )}
                    <details className="layout-controls">
                        <summary>Layout & text</summary>
                        <label>
                            Session pane width
                            <input
                                type="range"
                                min="0"
                                max="2"
                                value={s.sidebarSize}
                                onChange={(e) =>
                                    c.layout(
                                        +e.target.value,
                                        s.inspectorSize,
                                        s.textScale,
                                    )
                                }
                            />
                        </label>
                        <label>
                            Inspector width
                            <input
                                type="range"
                                min="0"
                                max="2"
                                value={s.inspectorSize}
                                onChange={(e) =>
                                    c.layout(
                                        s.sidebarSize,
                                        +e.target.value,
                                        s.textScale,
                                    )
                                }
                            />
                        </label>
                        <label>
                            Text size
                            <select
                                value={s.textScale}
                                onChange={(e) =>
                                    c.layout(
                                        s.sidebarSize,
                                        s.inspectorSize,
                                        +e.target.value,
                                    )
                                }
                            >
                                {[100, 125, 150, 200].map((n) => (
                                    <option key={n} value={n}>
                                        {n}%
                                    </option>
                                ))}
                            </select>
                        </label>
                    </details>
                </aside>
                <main className="play">
                    <div className="scene-head">
                        <div className="topline">
                            <div>
                                <h1>
                                    {selected?.name ?? "Open an original scene"}
                                </h1>
                                <small>
                                    {selected
                                        ? `${selected.scope.story} / ${selected.scope.branch}`
                                        : "Choose New Lantern Quay to begin."}
                                </small>
                            </div>
                            {!s.playV2 && (
                                <button
                                    aria-expanded={s.inspectorOpen}
                                    onClick={() =>
                                        c.setInspector(!s.inspectorOpen)
                                    }
                                >
                                    {s.inspectorOpen
                                        ? "Hide inspector"
                                        : "Show inspector"}
                                </button>
                            )}
                        </div>
                        <div
                            className="scene-status"
                            aria-label="Engine status"
                        >
                            <span>Revision {play?.revision ?? "—"}</span>
                            <span>Rules: {play?.rules ?? "unavailable"}</span>
                            <span>
                                Provider:{" "}
                                {s.playMode === "local"
                                    ? s.model?.loaded
                                        ? "Qwen3 local CPU (experimental)"
                                        : "Local model unavailable"
                                    : "deterministic fake v1"}
                            </span>
                            <span>
                                Turn:{" "}
                                {s.playV2
                                    ? scoped?.uncertain
                                        ? "outcome unknown"
                                        : (scoped?.pending?.stage ??
                                          scoped?.status?.phase ??
                                          "idle")
                                    : (s.pending?.stage ??
                                      s.turnStatus?.phase ??
                                      "idle")}
                            </span>
                        </div>
                    </div>
                    {s.view === "lab" && (
                        <div className="lab-warning" role="note">
                            Story Lab shows spoilers. Its inspection lens does
                            not change character knowledge or permissions.
                        </div>
                    )}
                    {brokerRetention && (
                        <BrokerRetentionPanel retention={brokerRetention} />
                    )}
                    {s.view === "lab" && s.playV2 && (
                        <label>
                            Inspection lens
                            <select
                                value={s.observer}
                                onChange={(event) =>
                                    c.setObserver(event.target.value)
                                }
                            >
                                <option value="omniscient">
                                    Omniscient developer
                                </option>
                                <option value="player">Player history</option>
                                <option value="mira">Mira</option>
                                <option value="sable">
                                    Sable · unwitnessed
                                </option>
                            </select>
                        </label>
                    )}
                    {author && authorContext && s.view === "lab" && (
                        <AuthorPanel
                            author={author}
                            context={authorContext()}
                        />
                    )}
                    {!s.playV2 &&
                        maintenance &&
                        maintenanceContext &&
                        selected && (
                            <MemoryMaintenancePanel
                                maintenance={maintenance}
                                context={maintenanceContext()}
                                receipt={
                                    receipt
                                        ? {
                                              turn: receipt.request.turn,
                                              revision:
                                                  receipt.events.at(-1)
                                                      ?.sequence ?? 0,
                                          }
                                        : undefined
                                }
                            />
                        )}
                    {!s.playV2 && timeline && selected && (
                        <TimelinePanel
                            timeline={timeline}
                            context={timelineContext(c)}
                        />
                    )}
                    {!s.playV2 && fork && selected && (
                        <ForkPanel
                            fork={fork}
                            gameplay={c}
                            context={timelineContext(c)}
                        />
                    )}
                    {evaluation && (
                        <EvaluationPanel
                            controller={evaluation}
                            context={`${s.selectedId}|${s.view}|${s.observer}`}
                            allowed={s.view === "lab"}
                        />
                    )}
                    {comparisonRun &&
                        nativeComparisonRun &&
                        comparison &&
                        s.view === "lab" && (
                            <div className="comparison-controls">
                                <label>
                                    Full comparison inference lane{" "}
                                    <select
                                        aria-label="Full comparison inference lane"
                                        value={runMode}
                                        disabled={switching || runBlocked}
                                        onChange={(event) =>
                                            void switchRunMode(
                                                event.target.value,
                                            )
                                        }
                                    >
                                        <option value="scripted_baseline">
                                            Scripted baseline · fake inference
                                        </option>
                                        <option value="approved_native">
                                            Installed local model · native
                                            inference
                                        </option>
                                    </select>
                                </label>
                                {(switching || runBlocked) && (
                                    <p role="status">
                                        Reconcile pending comparison access and
                                        cleanup before changing lanes.
                                    </p>
                                )}
                            </div>
                        )}
                    {activeRun && comparison && s.view === "lab" && (
                        <ComparisonRunView
                            key={runMode}
                            controller={activeRun}
                            onInspect={(runId) => inspectRun(activeRun, runId)}
                        />
                    )}
                    {inactiveRun &&
                        comparison &&
                        s.view === "lab" &&
                        comparisonBlocked(inactiveRun) && (
                            <details open>
                                <summary>
                                    Pending comparison in the other lane
                                </summary>
                                <ComparisonRunView
                                    controller={inactiveRun}
                                    onInspect={(runId) =>
                                        inspectRun(inactiveRun, runId)
                                    }
                                />
                            </details>
                        )}
                    {nativeComparisonRun && (
                        <ComparisonRunCleanupView
                            controller={nativeComparisonRun}
                        />
                    )}
                    {comparison && (
                        <ComparisonReaderPanel controller={comparison} />
                    )}
                    {comparison && selectedEvaluation && (
                        <SelectedExperiment
                            comparison={comparison}
                            selected={selectedEvaluation}
                        />
                    )}
                    {archive && (
                        <ArchivePanel
                            archive={archive}
                            controller={c}
                            context={`${s.selectedId}|${s.view}|${s.observer}`}
                            allowed={s.view === "lab"}
                        />
                    )}
                    {s.playV2 && v2 ? (
                        <div id="v2-play" tabIndex={-1}>
                            <ModelPanel controller={c} state={s} />
                            <V2PlayPanel
                                controller={v2}
                                controls={{
                                    action: (value) => c.setAction(value),
                                    fakeMode: (value) => c.setFakeMode(value),
                                    playMode: (value) => c.setPlayMode(value),
                                    inputKind: (value) => c.setInputKind(value),
                                }}
                            />
                            <p className="muted">
                                This timeline uses scoped native views. Legacy
                                debugger, inspection exports, timeline
                                navigation and derived-memory maintenance remain
                                unavailable for this domain version until their
                                shared adapters support it.
                            </p>
                            <button
                                disabled={!selected}
                                onClick={() => void c.closeSession()}
                            >
                                Close session | keep save
                            </button>
                        </div>
                    ) : s.query.shown ? (
                        <QueryInspector controller={c} state={s} />
                    ) : (
                        <>
                            <TurnDebugger controller={c} state={s} />
                            {capture && (
                                <CapturePanel
                                    controller={capture}
                                    gameplay={c}
                                    receipts={receipts}
                                    session={selected}
                                />
                            )}
                            <ModelPanel controller={c} state={s} />
                            <InspectionPanel controller={c} state={s} />
                            <div
                                className="transcript"
                                aria-label="Finalized transcript"
                                aria-live="polite"
                            >
                                {!rows.length && (
                                    <div className="empty">
                                        <h2>Lantern Quay</h2>
                                        <p>
                                            {s.playMode === "local"
                                                ? "Write an attempted action or speak dialogue through the local director and narrator. Only approved engine receipts enter this transcript."
                                                : "Exercise the original fixture with explicit actions or dialogue. Only accepted engine receipts enter this transcript."}
                                        </p>
                                        <p className="muted">
                                            Rowan has one potion. Mira is
                                            nearby; Sable is unwitnessed.
                                        </p>
                                    </div>
                                )}
                                {rows.map((r) => (
                                    <article
                                        className="turn"
                                        key={r.request.turn}
                                    >
                                        <div className="turn-head">
                                            <small>
                                                {r.request.turn} · accepted
                                                revision{" "}
                                                {r.events.at(-1)?.sequence}
                                            </small>
                                            <button
                                                onClick={() =>
                                                    c.selectReceipt(
                                                        r.request.turn,
                                                    )
                                                }
                                                aria-label={`Inspect receipt ${r.request.turn}`}
                                            >
                                                Inspect receipt
                                            </button>
                                        </div>
                                        <p className="intent">
                                            You: {intent(r)}
                                        </p>
                                        <p>{r.narration}</p>
                                        {r.play && (
                                            <p className="muted">
                                                Local play v{r.play.version} -{" "}
                                                {r.play.fallback
                                                    ? "Engine fallback narration after validation"
                                                    : "Generated narration accepted by shared policy"}
                                                ; repairs {r.play.repairs}.
                                                Profile{" "}
                                                {String(r.play.profile.id)}
                                            </p>
                                        )}
                                    </article>
                                ))}
                            </div>
                            {receipts.length > PAGE_SIZE && (
                                <nav
                                    className="pagination"
                                    aria-label="Transcript pages"
                                >
                                    <button
                                        disabled={s.page === 0}
                                        onClick={() => c.page(s.page - 1)}
                                    >
                                        Previous
                                    </button>
                                    <span>
                                        Page {s.page + 1} /{" "}
                                        {Math.ceil(receipts.length / PAGE_SIZE)}{" "}
                                        · {receipts.length} accepted turns
                                    </span>
                                    <button
                                        disabled={
                                            (s.page + 1) * PAGE_SIZE >=
                                            receipts.length
                                        }
                                        onClick={() => c.page(s.page + 1)}
                                    >
                                        Next
                                    </button>
                                </nav>
                            )}
                            {s.visibleError && (
                                <div className="message error" role="alert">
                                    {s.visibleError} ·{" "}
                                    {s.visibleError === "TransportUnknown"
                                        ? "Outcome uncertain. Retry checks the original turn; no rollback is assumed."
                                        : "No new transcript entry was added by this failed attempt."}
                                </div>
                            )}
                            {s.visibleError === "ClarificationRequired" && (
                                <p className="message" role="note">
                                    Please rephrase as one clear supported
                                    action. This experimental profile supports a
                                    limited set of English scene actions; it
                                    does not guess alternate effects. Try: I
                                    give my last potion to Mira. Choose Dialogue
                                    to speak your exact words.
                                </p>
                            )}
                            <div className="message notice" role="status">
                                {s.pending ? (
                                    <span className="pending">
                                        {s.pending.stage} · {s.pending.turn} -
                                        Not canonical until accepted
                                    </span>
                                ) : (
                                    s.notice ||
                                    (s.turnStatus?.phase === "cancelled"
                                        ? "Cancelled before commit. Draft preserved."
                                        : "")
                                )}
                            </div>
                            <form
                                id="composer"
                                className="compose"
                                onSubmit={(e) => {
                                    e.preventDefault();
                                    void c.send();
                                }}
                            >
                                <label>
                                    Inference profile{" "}
                                    <select
                                        value={s.playMode}
                                        disabled={!!s.pending}
                                        onChange={(e) =>
                                            c.setPlayMode(
                                                e.target.value as
                                                    "fixture" | "local",
                                            )
                                        }
                                    >
                                        <option value="fixture">
                                            Deterministic fake fixture
                                        </option>
                                        <option
                                            value="local"
                                            disabled={!s.model?.loaded}
                                        >
                                            Experimental local Qwen CPU
                                        </option>
                                    </select>
                                </label>
                                {s.playMode === "local" ? (
                                    <label>
                                        Player input{" "}
                                        <select
                                            value={s.inputKind}
                                            disabled={!!s.pending}
                                            onChange={(e) =>
                                                c.setInputKind(
                                                    e.target.value as
                                                        "action" | "dialogue",
                                                )
                                            }
                                        >
                                            <option value="action">
                                                Attempt an action
                                            </option>
                                            <option value="dialogue">
                                                Speak dialogue
                                            </option>
                                        </select>
                                    </label>
                                ) : (
                                    <div className="compose-row">
                                        <label>
                                            Explicit fixture action
                                            <select
                                                value={s.action}
                                                disabled={!!s.pending}
                                                onChange={(e) =>
                                                    c.setAction(
                                                        e.target
                                                            .value as Action,
                                                    )
                                                }
                                            >
                                                {Object.entries(actions).map(
                                                    ([key, label]) => (
                                                        <option
                                                            key={key}
                                                            value={key}
                                                        >
                                                            {label}
                                                        </option>
                                                    ),
                                                )}
                                            </select>
                                        </label>
                                        <label>
                                            Fake provider behavior
                                            <select
                                                value={s.fakeMode}
                                                disabled={!!s.pending}
                                                onChange={(e) =>
                                                    c.setFakeMode(
                                                        e.target
                                                            .value as FakeMode,
                                                    )
                                                }
                                            >
                                                <option value="accepted">
                                                    Accepted plumbing
                                                </option>
                                                <option value="delayed">
                                                    Delayed plumbing
                                                </option>
                                                <option value="malformed">
                                                    Malformed output
                                                </option>
                                                <option value="rejected">
                                                    Invalid proposal
                                                </option>
                                                <option value="failed">
                                                    Provider failure
                                                </option>
                                                <option value="cancelled">
                                                    Provider cancellation
                                                </option>
                                            </select>
                                        </label>
                                    </div>
                                )}
                                {s.playMode === "local" && (
                                    <p className="hint">
                                        Experimental English single-action
                                        support: try "I give my last potion to
                                        Mira." Use Dialogue for exact spoken
                                        words. Unknown, ambiguous, negated or
                                        compound actions require clarification.
                                    </p>
                                )}
                                <label className="sr-only" htmlFor="draft">
                                    Dialogue draft
                                </label>
                                <textarea
                                    id="draft"
                                    value={s.draft}
                                    maxLength={2048}
                                    placeholder={
                                        s.playMode === "local"
                                            ? "Describe an attempted action, or choose Dialogue to speak. Your text cannot grant author powers."
                                            : "Draft dialogue for Mira. Select Say draft aloud to submit it."
                                    }
                                    onChange={(e) => c.setDraft(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (
                                            composerShortcut({
                                                key: e.key,
                                                shiftKey: e.shiftKey,
                                                isComposing:
                                                    e.nativeEvent.isComposing,
                                            }) === "submit"
                                        ) {
                                            e.preventDefault();
                                            if (!s.pending) void c.send();
                                        }
                                    }}
                                />
                                <p className="hint">
                                    Enter submits the selected action ·
                                    Shift+Enter adds a newline. Pending
                                    generation is not canonical; only finalized
                                    approved receipts change the story. Dialogue
                                    never grants author powers.
                                </p>
                                <div className="send-row">
                                    <button
                                        className="primary"
                                        disabled={!selected || !!s.pending}
                                    >
                                        Submit action
                                    </button>
                                    <button
                                        type="button"
                                        disabled={
                                            !s.pending ||
                                            s.pending.stage === "cancelling"
                                        }
                                        onClick={() => void c.cancel()}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        type="button"
                                        disabled={
                                            !!s.pending ||
                                            !s.turnStatus ||
                                            s.turnStatus.phase === "committed"
                                        }
                                        onClick={() => void c.retry()}
                                    >
                                        Retry
                                    </button>
                                    <button
                                        type="button"
                                        disabled={!selected}
                                        onClick={() => void c.reset()}
                                    >
                                        {s.ephemeral
                                            ? "Reset fixture"
                                            : "Reset as new story"}
                                    </button>
                                </div>
                            </form>
                        </>
                    )}
                </main>
                {!s.playV2 &&
                    s.inspectorOpen &&
                    !s.query.shown &&
                    !s.trace.shown && (
                        <aside
                            className="inspector"
                            aria-label="Revision inspector"
                        >
                            <div className="head">
                                <h2>
                                    {s.view === "lab"
                                        ? "Story Lab inspector"
                                        : "Player & receipt"}
                                </h2>
                                <button
                                    disabled={!receipt}
                                    onClick={() =>
                                        void c.copyReceipt((text) =>
                                            navigator.clipboard.writeText(text),
                                        )
                                    }
                                >
                                    Copy receipt
                                </button>
                            </div>
                            <p className="scope">
                                {selected?.scope.story ?? "No session"} ·
                                revision {s.play?.revision ?? "—"}
                            </p>
                            {s.view === "lab" && (
                                <label>
                                    Inspection lens
                                    <select
                                        value={s.observer}
                                        onChange={(e) =>
                                            c.setObserver(e.target.value)
                                        }
                                    >
                                        <option value="omniscient">
                                            Omniscient developer
                                        </option>
                                        <option value="player">
                                            Rowan · player
                                        </option>
                                        <option value="mira">Mira</option>
                                        <option value="sable">
                                            Sable · unwitnessed
                                        </option>
                                    </select>
                                </label>
                            )}
                            <section>
                                <h3>Player sheet</h3>
                                <dl>
                                    <dt>Name</dt>
                                    <dd>
                                        {s.play?.player.self_state.name ?? "—"}
                                    </dd>
                                    <dt>Location</dt>
                                    <dd>
                                        {s.play?.player.self_state.location ??
                                            "—"}
                                    </dd>
                                    <dt>Energy</dt>
                                    <dd>
                                        {s.play?.player.self_state.energy ??
                                            "—"}
                                    </dd>
                                    <dt>Owned items</dt>
                                    <dd>
                                        {Object.keys(
                                            s.play?.inventory ?? {},
                                        ).join(", ") || "None"}
                                    </dd>
                                </dl>
                            </section>
                            <section>
                                <h3>Finalized receipt</h3>
                                {receipt && (
                                    <button
                                        onClick={() => void c.traceReceipt()}
                                    >
                                        Trace turn & evidence
                                    </button>
                                )}
                                {receipt ? (
                                    <>
                                        <p className="scope">
                                            {receipt.request.turn} · revision{" "}
                                            {receipt.events.at(-1)?.sequence}
                                        </p>
                                        <details>
                                            <summary>
                                                Accepted events (
                                                {receipt.events.length})
                                            </summary>
                                            <pre tabIndex={0}>
                                                {JSON.stringify(
                                                    receipt.events,
                                                    null,
                                                    2,
                                                )}
                                            </pre>
                                        </details>
                                        <details>
                                            <summary>
                                                Request & proposal
                                            </summary>
                                            <pre tabIndex={0}>
                                                {JSON.stringify(
                                                    {
                                                        request:
                                                            receipt.request,
                                                        proposal:
                                                            receipt.proposal,
                                                    },
                                                    null,
                                                    2,
                                                )}
                                            </pre>
                                        </details>
                                        {receipt.play && (
                                            <details>
                                                <summary>
                                                    Local play provenance &amp;
                                                    stage timing
                                                </summary>
                                                <pre tabIndex={0}>
                                                    {JSON.stringify(
                                                        receipt.play,
                                                        null,
                                                        2,
                                                    )}
                                                </pre>
                                            </details>
                                        )}
                                    </>
                                ) : (
                                    <p className="muted">
                                        No accepted turn yet.
                                    </p>
                                )}
                            </section>
                            <section>
                                <h3>
                                    Latest state diff{" "}
                                    {s.diffRevision === null
                                        ? ""
                                        : `→ r${s.diffRevision}`}
                                </h3>
                                <p className="muted">
                                    Compared player snapshots from Rust.
                                </p>
                                <ul className="diff">
                                    {s.diff.map((row) => (
                                        <li key={row.path}>
                                            <code>{row.path}</code>
                                            {JSON.stringify(row.before)} →{" "}
                                            {JSON.stringify(row.after)}
                                        </li>
                                    ))}
                                </ul>
                            </section>
                            {s.view === "lab" && (
                                <section>
                                    <h3>Scoped inspection</h3>
                                    <p className="scope">
                                        {s.inspectionObserver ?? "Loading"} ·
                                        revision {s.inspectionRevision ?? "—"}
                                    </p>
                                    <pre tabIndex={0}>
                                        {s.inspection === null
                                            ? "No inspection snapshot."
                                            : JSON.stringify(
                                                  s.inspection,
                                                  null,
                                                  2,
                                              )}
                                    </pre>
                                    <p className="muted">
                                        Summaries, retrieval traces and advanced
                                        memory views await their shared
                                        features.
                                    </p>
                                </section>
                            )}
                            <button
                                className="danger"
                                disabled={!selected}
                                onClick={() => void c.closeSession()}
                            >
                                {s.ephemeral
                                    ? "Close fixture session"
                                    : "Close session | keep save"}
                            </button>
                        </aside>
                    )}
            </div>
            <footer className="footer">
                <span>
                    {s.playMode === "local"
                        ? "Experimental local CPU"
                        : "Fake fixture inference"}{" "}
                    |{" "}
                    {s.workspace
                        ? "Accepted progress saved locally"
                        : s.ephemeral
                          ? "In-memory progress · lost on close"
                          : "Storage must open before play"}
                </span>
                <span>
                    {s.model?.loaded
                        ? "One local model loaded; no cloud fallback"
                        : "No model loaded; fake fixtures require explicit selection"}
                </span>
            </footer>
        </div>
    );
}
