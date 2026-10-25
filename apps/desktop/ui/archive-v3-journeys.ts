// Fixed synthetic actual-controller/native-IPC journeys. UNRUN at source freeze.
import type { Controller } from "./controller";
import type { ArchiveController } from "./archive-controller";
import type { V2PlayController } from "./v2-play-controller";
import type { BrokerRetention } from "./broker-retention";
import type { ErrorBuffer, Scope } from "./model";
import { structural } from "./model";

type Invoke = (
    command: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
interface Fixture {
    version: 1;
    synthetic: true;
    source_present: boolean;
    root: Scope;
    child: Scope;
    expected_revision: 3;
    expected_accepted_records: 3;
    player: "player";
    foreign: {
        scope: Scope;
        revision: number;
        canonical_sha256: string;
    } | null;
    proof: {
        canonical_sha256: string;
        basis_equal: true;
        full_records_equal: true;
        accepted_records: 3;
        all_actor_contexts_and_views_equal: true;
        player_current_mira_prior_sable_unaware: true;
    } | null;
}
const A = "ARCHIVE_V3_OBSERVED_A",
    B = "ARCHIVE_V3_WORLD_B",
    REASON = "ARCHIVE_V3_PRIVATE_REASON";
const pause = () => new Promise<void>((resolve) => setTimeout(resolve, 25));
async function until(test: () => boolean, label: string) {
    const deadline = performance.now() + 30000;
    while (performance.now() < deadline) {
        if (test()) return;
        await pause();
    }
    throw Error(`ArchiveV3Deadline:${label}`);
}
export async function archiveV3Journeys({
    controller: c,
    archive: a,
    v2,
    retention,
    invoke,
    dispose,
    errors,
    config,
}: {
    controller: Controller;
    archive: ArchiveController;
    v2: V2PlayController;
    retention: BrokerRetention;
    invoke: Invoke;
    dispose: () => Promise<void>;
    errors: ErrorBuffer;
    config: { archiveStage?: string };
}) {
    const checks: string[] = [],
        observerEvidence: {
            observer: string;
            prior: boolean;
            current: boolean;
            reason: boolean;
        }[] = [];
    let failedCheck = "v3-start",
        lastOracle: Fixture | null = null;
    const check = (value: unknown, label: string) => {
        failedCheck = label;
        if (!value) throw Error(label);
        checks.push(label);
    };
    const fixed = (scenario: string) =>
        invoke("harness_archive_case", { scenario });
    const oracle = async (scenario = "read-current-fixture") => {
        const result = (await invoke("harness_archive_v3_fixture", {
            scenario,
        })) as Fixture;
        check(
            result.version === 1 &&
                result.synthetic === true &&
                typeof result.source_present === "boolean" &&
                result.root?.story === "archive-v3-controls-synthetic" &&
                result.root.branch === "main" &&
                result.child?.story === result.root.story &&
                result.child.branch === "corrected" &&
                result.expected_revision === 3 &&
                result.expected_accepted_records === 3,
            "v3-fixed-native-fixture-metadata",
        );
        if (result.source_present)
            check(
                result.proof?.full_records_equal &&
                    result.proof.basis_equal &&
                    result.proof.accepted_records === 3 &&
                    result.proof.all_actor_contexts_and_views_equal &&
                    result.proof.player_current_mira_prior_sable_unaware,
                "v3-native-full-canon-basis-actor-view-oracle",
            );
        lastOracle = result;
        return result;
    };
    const revision = () =>
        c.get().playV2?.revision ?? c.get().play?.revision ?? 0;
    const lab = async () => {
        c.requestLab();
        c.acknowledgeLab(true);
        await until(() => c.get().view === "lab", "lab");
        await pause();
        a.show();
    };
    const selectedChild = async (fixture: Fixture) => {
        await c.resume(fixture.child);
        await until(
            () =>
                c.get().playV2?.domain_version === 2 &&
                revision() === 3 &&
                c.selected()?.scope.branch === fixture.child.branch,
            "selected-domain2",
        );
        check(
            c.get().play === null && !!c.get().playV2,
            "v3-selected-child-uses-actual-thin2-not-legacy-context",
        );
        await lab();
        await until(
            () =>
                v2.get().context?.scope.branch === fixture.child.branch &&
                v2.get().context?.revision === 3 &&
                !v2.get().readBusy,
            "v2-context",
        );
        await v2.refresh(false);
        check(
            v2.get().snapshot?.revision === 3 && !v2.get().error,
            "v3-actual-native-player-snapshot2",
        );
    };
    const capture = async (label: string) => {
        await new Promise<void>((resolve) =>
            requestAnimationFrame(() => requestAnimationFrame(() => resolve())),
        );
        const root = document.getElementById("root");
        check(!!root?.textContent?.trim(), `${label}-nonempty-native-ui`);
        const s = c.get(),
            scope = c.selected()?.scope,
            state = a.get();
        check(
            !!scope && root!.textContent!.includes(scope.story),
            `${label}-selected-story-visible`,
        );
        const target =
            root!.querySelector(".archive-panel") ??
            root!.querySelector(".v2-play") ??
            root!;
        target.scrollIntoView({ block: "start" });
        await pause();
        check(
            document.documentElement.scrollWidth <= innerWidth + 2,
            `${label}-no-horizontal-overflow`,
        );
        const snapshot = {
            ...c.semantic(),
            synthetic: true,
            uiRevision: revision(),
            workspace: s.workspace
                ? { ...s.workspace, location: "<synthetic-workspace>" }
                : null,
            aggregate: {
                selected: scope,
                observer: s.view === "play" ? "player" : s.observer,
                revision: revision(),
                pending: state.busy
                    ? state.status
                    : (v2.get().pending ?? s.pending),
                receipt: state.result ?? v2.get().receipt ?? c.receipt(),
                visibleError: state.error ?? v2.get().error ?? s.visibleError,
            },
            archive: {
                ...state,
                result: state.result?.location
                    ? { ...state.result, location: "<synthetic-archive>" }
                    : state.result,
            },
            v2: v2.get(),
            broker: retention.get(),
            oracle: lastOracle,
            observerEvidence,
            checks: [...checks],
            dom: {
                userAgent: navigator.userAgent,
                text: root!.textContent!.slice(0, 32000),
                viewport: { width: innerWidth, height: innerHeight },
                structure: [
                    ...root!.querySelectorAll(
                        "button,input,textarea,select,[role],h2,h3,dt,dd",
                    ),
                ]
                    .slice(0, 256)
                    .map((el) => ({
                        tag: el.tagName,
                        role: el.getAttribute("role"),
                        label: (
                            el.getAttribute("aria-label") ??
                            el.textContent ??
                            ""
                        ).slice(0, 160),
                        disabled: el.hasAttribute("disabled"),
                        checked:
                            el instanceof HTMLInputElement ? el.checked : null,
                    })),
            },
        };
        const rendered = (await invoke("harness_checkpoint", {
            label,
            snapshot,
        })) as { rendering: string };
        check(
            rendered.rendering === "native-webview2",
            `${label}-actual-native-webview2-image`,
        );
    };
    const exportSelected = async (label: string) => {
        const session = c.selected();
        check(!!session, "v3-export-real-selected-session");
        a.show();
        failedCheck = "v3-visible-export-control-ready";
        await until(
            () =>
                [...document.querySelectorAll(".archive-panel button")].some(
                    (button) =>
                        button.textContent?.trim() ===
                            "Preview private export" &&
                        !button.hasAttribute("disabled"),
                ),
            "visible-export-control",
        );
        await a.previewExport(session!.id, session!.scope, revision());
        const preview = a.get().preview;
        check(
            preview?.kind === "export" &&
                preview.preview.version === 3 &&
                preview.preview.committed_turns === 3,
            "v3-selected-child-private-export-preview",
        );
        await until(
            () =>
                !!document
                    .querySelector(".archive-preview")
                    ?.textContent?.includes("Accepted records"),
            "rendered-preview",
        );
        check(
            !a.get().consent &&
                document
                    .querySelector(".archive-preview")
                    ?.textContent?.includes("Accepted records"),
            "v3-rendered-canonical-record-label-and-explicit-consent",
        );
        if (label) await capture(label);
        a.consent(true);
        await fixed("normal");
        await a.confirm();
        check(
            a.get().result?.status === "exported" && !a.get().error,
            "v3-actual-native-private-file-published",
        );
    };
    const observers = async () => {
        for (const observer of ["mira", "sable", "player"]) {
            c.setObserver(observer);
            await until(() => {
                const lens = v2.get().context?.observer;
                return (
                    !!lens &&
                    (observer === "player"
                        ? lens.kind === "player"
                        : lens.kind === "character" && lens.id === observer)
                );
            }, `observer-${observer}`);
            await v2.refresh(false);
            const page = await v2.readQuery({
                view: "knowledge",
                atRevision: null,
                search: "",
            });
            check(!!page && !v2.get().error, `v3-${observer}-actual-query2`);
            const text = structural(page);
            const found = {
                observer,
                prior: text.includes(A),
                current: text.includes(B),
                reason: text.includes(REASON),
            };
            observerEvidence.push(found);
            check(
                !found.reason &&
                    (observer === "mira"
                        ? found.prior && !found.current
                        : observer === "sable"
                          ? !found.prior && !found.current
                          : found.current),
                `v3-${observer}-observed-truth-isolation`,
            );
            if (observer === "mira") await capture("observer");
        }
        await lab();
    };
    try {
        const stage = config.archiveStage;
        check(
            ["v3-source", "v3-import", "v3-restarted", "v3-uncertain"].includes(
                stage ?? "",
            ),
            "v3-closed-stage",
        );
        if (stage === "v3-source") await oracle("prepare-source");
        await c.start();
        check(c.get().workspace?.persistent, "v3-durable-native-workspace");
        const catalog = (await invoke("archive_catalog")) as {
            archive_version: number;
            supported_archive_versions: number[];
        };
        check(
            catalog.archive_version === 3 &&
                structural(catalog.supported_archive_versions) === "[1,2,3]",
            "v3-exact-native-capability-catalog",
        );
        let fixture = await oracle();
        if (stage === "v3-source") {
            await selectedChild(fixture);
            await exportSelected("initial");
            await capture("receipt");
            await a.previewExport(c.selected()!.id, c.selected()!.scope, 3);
            await invoke("harness_viewport", { preset: "narrow" });
            await capture("narrow");
            await invoke("harness_viewport", { preset: "wide" });
            await observers();
        } else if (stage === "v3-restarted") {
            check(
                fixture.source_present &&
                    fixture.foreign &&
                    a.get().preview === null &&
                    a.get().status === null &&
                    !a.get().consent,
                "v3-real-process-restart-restores-no-old-operation-or-consent",
            );
            await selectedChild(fixture);
            await capture("reopened");
            await observers();
            await exportSelected("copy");
            await capture("receipt");
        } else {
            check(
                !fixture.source_present && fixture.foreign,
                "v3-fresh-destination-retains-only-foreign-control",
            );
            const before = structural(c.get().play);
            const foreign = structural(fixture.foreign);
            await lab();
            await fixed("normal");
            await a.previewImport();
            check(
                a.get().preview?.preview.version === 3 && !a.get().consent,
                "v3-native-validates-before-consent",
            );
            await capture("copy");
            if (stage === "v3-import") {
                a.consent(true);
                await fixed("hold-import");
                const pending = a.confirm();
                await until(
                    () =>
                        a.get().status?.phase === "importing" || !a.get().busy,
                    "staged-import",
                );
                check(
                    a.get().busy &&
                        a.get().status?.running &&
                        a.get().status?.phase === "importing",
                    "v3-real-staged-pending-import",
                );
                await capture("pending");
                await a.cancel();
                await pending;
                await fixed("release-import");
                check(
                    a.get().error === "Cancelled",
                    "v3-preapply-cancel-is-actual-native-cancelled",
                );
                fixture = await oracle();
                check(
                    !fixture.source_present &&
                        structural(fixture.foreign) === foreign &&
                        structural(c.get().play) === before,
                    "v3-cancel-preserves-canonical-foreign-selection",
                );
                await capture("cancelled");
                await fixed("normal");
                await a.previewImport();
            }
            a.consent(true);
            if (stage === "v3-uncertain") await fixed("drop-import-ack");
            await a.confirm();
            if (stage === "v3-uncertain")
                check(
                    a.get().error === "ArchiveAcknowledgementUnavailable" &&
                        a.get().result?.status !== "imported",
                    "v3-lost-ack-is-not-false-success-or-rollback",
                );
            else
                check(
                    a.get().result?.status === "imported",
                    "v3-actual-native-destination-import",
                );
            fixture = await oracle();
            check(
                fixture.source_present &&
                    structural(fixture.foreign) === foreign &&
                    structural(c.get().play) === before,
                "v3-native-oracle-proves-durable-import-with-foreign-unchanged",
            );
            await capture(stage === "v3-uncertain" ? "failed" : "receipt");
            await c.library();
            if (retention.get()?.unknown)
                check(
                    retention.acknowledgeUnresolved(true),
                    "v3-explicit-synthetic-ack-unresolved-after-readonly-recovery",
                );
            await selectedChild(fixture);
            await observers();
            await fixed("normal");
            a.show();
            await a.previewImport();
            a.consent(true);
            await a.confirm();
            check(
                a.get().error === "Conflict",
                "v3-fresh-preview-same-identity-conflicts-without-overwrite",
            );
            const afterConflict = await oracle();
            check(
                structural(afterConflict.proof) === structural(fixture.proof),
                "v3-conflict-preserves-full-record-and-basis-proof",
            );
            if (stage === "v3-import") await exportSelected("");
        }
        await c.refreshModel();
        check(
            c.get().model?.loaded === false,
            "v3-transfer-does-not-load-or-run-inference",
        );
        fixture = await oracle();
        check(
            fixture.source_present && !!fixture.proof,
            "v3-final-native-full-history-proof",
        );
        check(
            errors.snapshot().length === 0,
            "v3-zero-frontend-unhandled-or-native-transport-errors",
        );
        c.returnToPlay();
        await pause();
        check(
            !a.get().shown && a.get().preview === null,
            "v3-play-return-revokes-private-preview",
        );
        await capture("finished");
        await dispose();
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: true,
                stage,
                checks,
                errors: errors.snapshot(),
                oracle: fixture,
                observerEvidence,
                generationExecuted: false,
                evidence: "actual-native-IPC-WebView2-fixed-synthetic-fixture",
            },
        });
    } catch (error) {
        await invoke("harness_finish", {
            report: {
                synthetic: true,
                passed: false,
                failedCheck,
                checks,
                category:
                    error instanceof Error
                        ? error.message.slice(0, 128)
                        : "ArchiveV3Failure",
                stage: config.archiveStage,
                archiveError: a.get().error,
                errors: errors.snapshot(),
                oracle: lastOracle,
            },
        });
    }
}
