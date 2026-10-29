// Independent FIRST fixtures only: synthetic transport metadata, not Rust output,
// native permission, canonical effects, an inference provider or a product hook.
import assert from "node:assert/strict";
export const scope = Object.freeze({
    story: "synthetic-live-diagnostic",
    branch: "main",
});
export const baseRevision = 4;
export const originalTurn = "original-turn";
export const originalAttempt = 2;
export const clone = (value) => structuredClone(value);
export const plain = (value) => JSON.parse(JSON.stringify(value));
export const decisionTuples = [
    { version: 1, outcome: "accepted", error: null, reason: null },
    { version: 1, outcome: "cancelled", error: "cancelled", reason: null },
    { version: 1, outcome: "stale", error: "stale", reason: null },
    ...["unclassified", "scene_first_person", "scene_unapproved_movement"].map(
        (reason) => ({
            version: 1,
            outcome: "rejected",
            error: "narration",
            reason,
        }),
    ),
    ...[
        "malformed",
        "version",
        "scope",
        "rule",
        "agency",
        "deadline",
        "retry_mismatch",
        "too_large",
        "author_ui_required",
        "clarification_required",
        "unknown_reference",
        "dead_actor",
        "location",
        "inventory",
        "resource",
        "ability",
        "knowledge",
        "provider",
        "corrupt_history",
    ].map((error) => ({
        version: 1,
        outcome: "rejected",
        error,
        reason: null,
    })),
];
export function deferred() {
    let resolve, reject;
    const promise = new Promise((a, b) => {
        resolve = a;
        reject = b;
    });
    return { promise, resolve, reject };
}
export async function tick() {
    for (let n = 0; n < 64; n++) await Promise.resolve();
}
export function query(
    session = "live-session",
    selectedScope = scope,
    head = 5,
) {
    return {
        op: "trace_narration_validation_read_v1",
        session,
        scope: clone(selectedScope),
        expected_head: head,
        base_revision: baseRevision,
        turn: originalTurn,
        attempt: originalAttempt,
    };
}
export function data(
    q = query(),
    status = "recorded",
    decision = decisionTuples[4],
) {
    return {
        version: 1,
        session: q.session,
        scope: clone(q.scope),
        head: q.expected_head,
        base_revision: q.base_revision,
        turn: q.turn,
        attempt: q.attempt,
        observer: "player",
        generation_grant: false,
        status,
        ...(status === "recorded" ? { decision: clone(decision) } : {}),
    };
}
const provenance = Object.fromEntries(
    [
        "model_sha256",
        "worker_sha256",
        "profile_sha256",
        "config_sha256",
        "prompt_sha256",
        "schema_sha256",
        "runtime_revision",
        "engine_revision",
        "profile_label",
        "prompt_label",
        "schema_label",
    ].map((key) => [key, null]),
);
export function traceReply(q, player, enabled = true, empty = false) {
    const actor = q.observer.kind === "character" ? q.observer.id : player;
    const attempt = (turn, number) => ({
        identity: {
            scope: clone(q.scope),
            base_revision: q.base_revision,
            observer: actor,
            turn,
            attempt: number,
        },
        provenance: clone(provenance),
        outcome: "committed",
        elapsed_us: 12,
        truncated: false,
        stages: [
            {
                stage: "narration_validation",
                outcome: "rejected",
                started_us: 1,
                duration_us: 2,
                counts: {
                    eligible_records: 0,
                    input_tokens: null,
                    output_tokens: null,
                    operations: 0,
                    repairs: 0,
                },
                error: "narration",
            },
        ],
    });
    return {
        scope: clone(q.scope),
        head: q.expected_head,
        base_revision: q.base_revision,
        observer: clone(q.observer),
        configuration_scope: "window_host",
        capture: "metadata_only",
        full_capture: "unsupported",
        snapshot: {
            version: 1,
            status: enabled ? "bounded_metadata_window" : "disabled",
            exact_reconstruction: false,
            attempts:
                enabled && !empty
                    ? [
                          attempt(originalTurn, originalAttempt),
                          attempt("later-turn", 7),
                      ]
                    : [],
        },
    };
}
export function page(q) {
    return {
        version: q.version,
        scope: clone(q.scope),
        head: q.expected_head,
        revision: q.at_revision ?? q.expected_head,
        story_time: 100,
        observer: clone(q.observer),
        view: q.view,
        privacy:
            q.observer.kind === "player"
                ? "player_visible"
                : q.observer.kind === "character"
                  ? "private_character"
                  : "private_omniscient",
        status: "supported",
        total: 0,
        rows: [],
        next_cursor: null,
        unsupported: [],
    };
}
export function syntheticHost({
    domain = 1,
    player = "player",
    thin = false,
} = {}) {
    const calls = [],
        nativeCalls = [],
        diagnosticQueue = [],
        traceQueue = [],
        gameplayHolds = new Map(),
        allHolds = [];
    let head = 5,
        sessionNumber = 0,
        enabled = false,
        emptyTrace = false,
        lastTrace = null;
    let lastRequest = null,
        diagnosticObserver = null,
        gameplayObserver = null,
        configureHold = null;
    const thinSnapshot = (selectedScope = scope) => ({
        version: 2,
        domain_version: domain,
        scope: clone(selectedScope),
        revision: head,
        rules: "fantasy_v1",
        player: {
            observer: player,
            self_state: {
                name: "Synthetic original player",
                location: "quay",
                alive: true,
                energy: 2,
                abilities: {},
                attributes: {},
                injuries: [],
                affiliations: [],
                goals: [],
            },
        },
        inventory: {},
    });
    const legacySnapshot = (selectedScope = scope) => ({
        scope: clone(selectedScope),
        revision: head,
        rules: "fantasy_v1",
        inventory: {},
        receipts: [],
        player: {
            scope: clone(selectedScope),
            revision: head,
            observer: player,
            self_state: { name: "Synthetic", energy: 2, location: "quay" },
            observations: [],
            facts: {},
            beliefs: [],
        },
    });
    const hold = (queue, kind = "other") => {
        assert(allHolds.length < 32, "BoundedSyntheticHolds");
        const result = {
            entered: deferred(),
            release: deferred(),
            command: null,
            kind,
        };
        allHolds.push(result);
        queue.push(result);
        return result;
    };
    async function call(q) {
        assert(calls.length < 640, "BoundedSyntheticHostCalls");
        calls.push(clone(q));
        if (q.op === "workspace")
            return {
                persistent: true,
                location: "synthetic",
                schema_version: 1,
                database_schema_version: 5,
                stories: [
                    {
                        scope: clone(scope),
                        title: "Synthetic",
                        revision: head,
                        drafts: 0,
                    },
                ],
            };
        if (q.op === "resume" || q.op === "create")
            return {
                session: `session-${++sessionNumber}`,
                scope: clone(q.scope ?? scope),
                revision: head,
                drafts: 0,
            };
        if (q.op === "open") return { revision: head };
        if (q.op === "play_snapshot_v2") return thinSnapshot(q.scope);
        if (q.op === "play_snapshot") return legacySnapshot(q.scope);
        if (q.op === "inspection_query") return page(q.query);
        if (q.op === "inspect") return { synthetic: true };
        if (q.op === "close") return null;
        if (q.op === "trace_capture_revoke")
            return { version: 1, scope: clone(q.scope), revoked: true };
        if (q.op === "trace_configure" || q.op === "trace_clear") {
            if (configureHold) {
                const h = configureHold;
                configureHold = null;
                h.entered.resolve();
                await h.release.promise;
            }
            enabled = q.op === "trace_clear" ? enabled : q.enabled;
            if (q.op === "trace_clear" || !enabled) emptyTrace = true;
            return {
                configuration_scope: "window_host",
                capture: "metadata_only",
                full_capture: "unsupported",
                ...(q.op === "trace_clear" ? { cleared: true } : { enabled }),
            };
        }
        if (q.op === "trace_read") {
            const reply = traceReply(q, player, enabled, emptyTrace);
            lastTrace = reply;
            if (traceQueue.length) {
                const h = traceQueue.shift();
                h.command = clone(q);
                h.entered.resolve();
                await h.release.promise;
            }
            return reply; // Deliberately retained external transport alias for one labeled adversarial case.
        }
        if (q.op === "trace_narration_validation_read_v1") {
            diagnosticObserver?.(clone(q));
            if (diagnosticQueue.length) {
                const next = diagnosticQueue.shift();
                if (next instanceof Error) throw next;
                if (next?.entered) {
                    next.command = clone(q);
                    next.entered.resolve();
                    return next.release.promise;
                }
                return next;
            }
            return data(q);
        }
        if (
            [
                "submit",
                "free_text",
                "prepare",
                "commit",
                "turn_status",
                "cancel",
            ].includes(q.op)
        ) {
            gameplayObserver?.(clone(q));
            if (q.request) lastRequest = clone(q.request);
            const waiting = gameplayHolds.get(q.op);
            if (waiting?.length) {
                const h = waiting.shift();
                h.command = clone(q);
                h.entered.resolve();
                await h.release.promise;
            }
            const request = q.request ?? lastRequest;
            assert(request, "SyntheticGameplayNeedsActualPublicRequest");
            return {
                scope: clone(request.scope),
                turn: request.turn,
                expected_revision: request.expected_revision,
                phase:
                    q.op === "cancel"
                        ? "cancelled"
                        : q.op === "submit" || q.op === "free_text"
                          ? "queued"
                          : "running",
                error: null,
                receipt: null,
            };
        }
        throw Error(`UnexpectedSyntheticHost:${q.op}`);
    }
    const model = {
        operation_id: 1,
        resident: false,
        phase: "unloaded",
        percent: 0,
        imported: false,
        loaded: false,
        error: null,
        profile: null,
        available_profile: {
            id: "synthetic",
            model_bytes: 1,
            model_sha256: "a".repeat(64),
            runtime_revision: "synthetic",
            device: "synthetic",
            qualification: "not-qualified",
        },
    };
    async function invoke(command, args = {}) {
        nativeCalls.push({ command, args: clone(args) });
        if (command === "author_context")
            return {
                version: 1,
                root_incarnation: "synthetic-root",
                window_epoch: 1,
                story_lab_granted: true,
            }; // Existing synthetic native-metadata fixture, not UI authority.
        if (command === "author_preview_discard") return true;
        if (command === "model_status") return clone(model); // No model action or SDK is performed.
        assert.equal(command, "host_call", "ClosedSyntheticNativeRoster");
        const envelope = JSON.parse(args.input);
        assert.equal(envelope.version, 1);
        try {
            return {
                version: 1,
                status: "ok",
                data: await call(envelope.command),
            };
        } catch (error) {
            return {
                version: 1,
                status: "rejected",
                error: String(error.message),
            };
        }
    }
    return {
        calls,
        nativeCalls,
        invoke,
        gateway: {
            playSnapshotV2: thin || domain === 2 || player !== "player",
            call,
        },
        get head() {
            return head;
        },
        set head(value) {
            head = value;
        },
        player,
        setEmptyTrace(value) {
            emptyTrace = value;
        },
        setEnabled(value) {
            enabled = value;
        },
        get lastTrace() {
            return lastTrace;
        },
        queueDiagnostic(value) {
            diagnosticQueue.push(value);
        },
        holdDiagnostic() {
            return hold(diagnosticQueue, "diagnostic");
        },
        holdTrace() {
            return hold(traceQueue);
        },
        holdConfigure() {
            const h = hold([]);
            configureHold = h;
            return h;
        },
        holdGameplay(op) {
            const queue = gameplayHolds.get(op) ?? [];
            gameplayHolds.set(op, queue);
            return hold(queue);
        },
        observeDiagnostic(fn) {
            diagnosticObserver = fn;
        },
        observeGameplay(fn) {
            gameplayObserver = fn;
        },
        releaseAll() {
            for (const h of allHolds)
                h.release.resolve(
                    h.kind === "diagnostic" && h.command
                        ? data(h.command)
                        : undefined,
                );
        },
        thinSnapshot,
        legacySnapshot,
    };
}
export function fence(controller, host, patch = {}) {
    const s = controller.get(),
        selected = controller.selected(),
        snapshot = s.play ?? s.playV2;
    assert(
        selected && snapshot,
        "PublicSnapshotRequiredForSyntheticPresentationFence",
    );
    return {
        session: selected.id,
        story: snapshot.scope.story,
        branch: snapshot.scope.branch,
        head: snapshot.revision,
        player: host.player,
        pending: false,
        uncertain: false,
        ...patch,
    };
}
export async function readyController(Controller, options = {}) {
    const host = syntheticHost(options),
        c = new Controller(host.gateway);
    await c.attach({
        id: "live-session",
        scope: clone(scope),
        name: "Synthetic",
        revision: host.head,
    });
    c.requestLab();
    c.acknowledgeLab(true);
    await tick();
    await c.showTrace(true);
    await c.controlTrace("enable");
    await c.traceBasis(baseRevision);
    host.setEmptyTrace(false);
    await c.readTrace();
    c.selectTrace(`${originalTurn}:${originalAttempt}`);
    c.setTraceGameplayFence(fence(c, host));
    return {
        c,
        host,
        async close() {
            host.releaseAll();
            await c.dispose();
        },
    };
}
// Existing comparison source DTO only. No report/receipt/canonical fixture is invented.
export const readerToken = "22222222-2222-2222-2222-222222222222";
export const readerBinding = "a".repeat(64);
export const readerRow = Object.freeze({ turn: originalTurn, arm: "left" });
export const readerSource = {
    binding: readerBinding,
    protocol_version: 4,
    rows: ["left", "right"].map((arm) => ({
        row: { turn: originalTurn, arm },
        source: {
            status: "available",
            scope: clone(scope),
            before_head: 4,
            after_head: 5,
            input_semantic_sha256: "1".repeat(64),
        },
        capture_available: true,
        receipt_available: true,
        recording_available: true,
        unavailable: [],
    })),
    read_only: true,
    execution_available: false,
};
export function readerEnvelope(decision = decisionTuples[4]) {
    const q = { ...query("historical-session"), expected_head: 4 };
    return {
        version: 1,
        kind: "comparison_reader_narration_diagnostic_v1",
        run_token: readerToken,
        diagnostic: {
            version: 1,
            protocol_version: 4,
            kind: "narration_diagnostic_v1",
            binding: readerBinding,
            row: clone(readerRow),
            generation_grant: false,
            status: "recorded",
            observation: {
                version: 1,
                kind: "full_scene_narration_observation_v1",
                declaration_sha256: "d".repeat(64),
                run_binding_sha256: "b".repeat(64),
                source_sha256: "c".repeat(64),
                arm: "left",
                index: 0,
                admission: 1,
                checkpoint_sha256: "e".repeat(64),
                host_query: { version: 1, command: q },
                host_reply: {
                    version: 1,
                    status: "ok",
                    data: data(q, "recorded", decision),
                },
                generation_grant: false,
            },
        },
    };
}
export async function comparisonFixture(m) {
    const calls = [],
        errors = [];
    let reply = readerEnvelope();
    const status = (client, phase = "ready") => ({
        version: 1,
        kind: "comparison_reader",
        client_id: client,
        operation_id: 1,
        phase,
        running: false,
        run_token: phase === "ready" ? readerToken : null,
        binding: phase === "ready" ? readerBinding : null,
        error: null,
        read_only: true,
        execution_available: false,
    });
    const c = new m.ComparisonReaderController(
        async (command, args) => {
            calls.push(clone({ command, args }));
            assert.equal(command, "evaluation_comparison");
            if (["pick", "status"].includes(args.action))
                return status(args.query.clientId);
            if (args.action === "source")
                return {
                    version: 1,
                    kind: "comparison_reader",
                    run_token: readerToken,
                    source: clone(readerSource),
                };
            if (args.action === "narration_diagnostic_v1") return reply;
            if (args.action === "close")
                return status(args.query.clientId, "closed");
            throw Error("UnexpectedComparisonFixtureAction");
        },
        (error) => errors.push(error),
    );
    c.contextChanged("synthetic-live-codec-compatibility", true);
    await c.pick();
    c.select(readerRow);
    return {
        c,
        calls,
        errors,
        setReply(value) {
            reply = value;
        },
        async close() {
            await c.close();
            c.dispose();
        },
    };
}
