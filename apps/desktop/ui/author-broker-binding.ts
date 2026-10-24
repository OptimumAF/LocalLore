// Memory-only shared-owner identity. This is not permission or canonical validation.
import {
    authorRaw, checkedAuthorInput, checkedAuthorStatus, checkedAuthorPreview,
    checkedAuthorCompletion, type AuthorInput, type AuthorStatus,
} from "./author-model";

export interface AuthorBrokerBinding {
    readonly action: "prepare" | "commit" | "lookup";
    readonly session: string;
    readonly input: AuthorInput;
}
export function checkedAuthorBrokerBinding(value: unknown): AuthorBrokerBinding {
    if (!value || typeof value !== "object" || Array.isArray(value) ||
        ![Object.prototype,null].includes(Object.getPrototypeOf(value)) ||
        Reflect.ownKeys(value).length !== 3 ||
        !["action","session","input"].every(key => Object.hasOwn(value,key)))
        throw Error("InvalidInput");
    for (const key of Reflect.ownKeys(value)) {
        const descriptor=Object.getOwnPropertyDescriptor(value,key)!;
        if (!descriptor.enumerable || !("value" in descriptor)) throw Error("InvalidInput");
    }
    const v=value as Record<string,unknown>;
    if (typeof v.action !== "string" || !["prepare","commit","lookup"].includes(v.action) ||
        typeof v.session !== "string" || !/^[A-Za-z0-9_-]{1,128}$/.test(v.session))
        throw Error("InvalidInput");
    const input=checkedAuthorInput(v.input);
    const result:AuthorBrokerBinding=Object.freeze({action:v.action as AuthorBrokerBinding["action"],session:v.session,input});
    authorRaw(result);
    return result;
}
// Exclusion only. Do not execute a getter to decide which reservation owns a reply.
export function authorBrokerOperationId(value:unknown):number|undefined {
    if (!value || typeof value !== "object") return undefined;
    const descriptor=Object.getOwnPropertyDescriptor(value,"operation_id");
    if (!descriptor || !("value" in descriptor) || !Number.isSafeInteger(descriptor.value) || descriptor.value<1) return undefined;
    return descriptor.value as number;
}
export async function checkedAuthorBrokerOperation(value:unknown,binding:AuthorBrokerBinding,operation?:number):Promise<AuthorStatus> {
    const bound=checkedAuthorBrokerBinding(binding);
    const status=checkedAuthorStatus(value);
    if (operation !== undefined && status.operation_id !== operation) throw Error("Wire");
    const phase=bound.action === "prepare"?"author_preparing":bound.action === "commit"?"author_applying":"author_lookup";
    if (status.running) {
        if (status.phase !== "starting" && status.phase !== phase) throw Error("Wire");
    } else if (!status.error) {
        if (bound.action === "prepare") await checkedAuthorPreview(status.result,bound.input,bound.session);
        else checkedAuthorCompletion(status.result,bound.action,bound.input,bound.session);
    }
    return status;
}
