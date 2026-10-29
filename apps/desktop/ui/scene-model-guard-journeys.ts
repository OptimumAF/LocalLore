// Fixed application-owned native IPC guard proof; no model or render claim.
import { structural, type ErrorBuffer } from "./model";
type Invoke = (
    name: string,
    args?: Record<string, unknown>,
) => Promise<unknown>;
type Snapshot = {
    version: 1;
    kind: "scene_model_guard_fixture";
    synthetic: true;
    protocol_version: 4;
    case: string;
    publication: Record<string, { bytes: number; sha256: string }>;
    control: Record<string, { bytes: number; sha256: string }>;
    picker_calls: number;
    control_status: unknown;
    models_executed: false;
    runtime_started: false;
    approved_basename_created: false;
};
export async function sceneModelGuardJourneys({
    invoke,
    dispose,
    errors,
}: {
    invoke: Invoke;
    dispose: () => Promise<void>;
    errors: ErrorBuffer;
}) {
    const checks: string[] = [];
    let failedCheck = "guard-start";
    const check = (value: unknown, label: string) => {
        failedCheck = label;
        if (!value) throw Error(label);
        checks.push(label);
    };
    const fixture = async (caseName: "snapshot" | "counterfactual") => {
        const value = (await invoke("harness_scene_model_guards", {
            case: caseName,
        })) as Snapshot;
        check(
            value?.version === 1 &&
                value.kind === "scene_model_guard_fixture" &&
                value.synthetic === true &&
                value.protocol_version === 4 &&
                value.models_executed === false &&
                value.runtime_started === false &&
                value.approved_basename_created === false &&
                value.case === caseName,
            "actual-closed-native-guard-fixture",
        );
        return value;
    };
    try {
        const before = await fixture("snapshot");
        check(
            Object.keys(before.publication).length === 1 &&
                Object.keys(before.control).length === 1,
            "two-private-staging-sentinels-present",
        );
        const statusBefore = (await invoke("model_status")) as Record<
            string,
            unknown
        >;
        check(
            statusBefore.loaded === false &&
                statusBefore.resident === false &&
                statusBefore.imported === false &&
                statusBefore.phase === "unloaded" &&
                statusBefore.operation_id === 0,
            "actual-application-manager-has-no-model-or-job",
        );
        const refusals: Record<string, string> = {};
        for (const command of ["model_import", "model_load"] as const) {
            let refusal = "";
            try {
                await invoke(command);
            } catch (error) {
                refusal = String(error);
            }
            refusals[command] = refusal;
            check(
                refusal === "Forbidden",
                `actual-${command}-refuses-before-manager-side-effects`,
            );
        }
        const after = await fixture("snapshot");
        const statusAfter = await invoke("model_status");
        check(
            structural(before.publication) === structural(after.publication) &&
                structural(before.control) === structural(after.control),
            "both-complete-private-inventories-unchanged-by-command-guards",
        );
        check(
            structural(statusBefore) === structural(statusAfter),
            "actual-application-manager-not-begun-or-loaded",
        );
        const control = await fixture("counterfactual");
        check(
            control.picker_calls === 1 &&
                Object.keys(control.control).length === 0,
            "actual-private-manager-import-reaped-before-picker-none",
        );
        check(
            structural(control.publication) === structural(before.publication),
            "counterfactual-never-modified-private-publication",
        );
        const finalStatus = await invoke("model_status");
        check(
            structural(statusBefore) === structural(finalStatus),
            "counterfactual-does-not-own-application-manager",
        );
        check(
            errors.snapshot().length === 0,
            "no-unexpected-frontend-or-native-errors",
        );
        await dispose();
        await invoke("harness_finish", {
            report: {
                version: 1,
                passed: true,
                synthetic: true,
                kind: "scene_model_guard_cohort",
                checks,
                refusals,
                before,
                after,
                control,
                statusBefore,
                statusAfter,
                nativeIpc: true,
                rendering: "unqualified-no-images",
                modelExecution: false,
                desktopInput: false,
                nativeDialogsAutomated: false,
                errors: errors.snapshot(),
            },
        });
    } catch (error) {
        const original = {
            failedCheck,
            error:
                error instanceof Error
                    ? error.message.slice(0, 256)
                    : String(error).slice(0, 256),
            errors: errors.snapshot(),
        };
        let disposed = false;
        try {
            await dispose();
            disposed = true;
        } catch {
            /* Original failure stays failed. */
        }
        await invoke("harness_finish", {
            report: {
                version: 1,
                passed: false,
                synthetic: true,
                kind: "scene_model_guard_cohort",
                checks,
                original,
                disposed,
                nativeIpc: true,
                rendering: "unqualified-no-images",
                modelExecution: false,
                desktopInput: false,
            },
        });
    }
}
