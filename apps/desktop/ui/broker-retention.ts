// Presentation retention only. Native broker/Host/Store remain authoritative.
export type BrokerSurface = "memory" | "fork" | "archive";
export interface BrokerIdentity {
    surface: BrokerSurface;
    session?: string;
    story?: string;
    branch?: string;
    head?: number;
    action: string;
    token?: string;
    child?: string;
    at?: number;
}
interface Retained {
    identity: BrokerIdentity;
    inFlight: boolean;
    operation: number | null;
    terminal: boolean;
    unknown: boolean;
    acknowledgedUnresolved: boolean;
}
function identity(value: BrokerIdentity): BrokerIdentity {
    if (!value || typeof value !== "object" || Object.keys(value).some(k=>!["surface","session","story","branch","head","action","token","child","at"].includes(k)) || !["memory","fork","archive"].includes(value.surface)) throw Error("InvalidInput");
    for (const [key,v] of Object.entries(value)) {
        if (["head","at"].includes(key)) {if(!Number.isSafeInteger(v)||Number(v)<0)throw Error("InvalidInput");}
        else if(typeof v!=="string"||v.length<1||v.length>128||!/^[A-Za-z0-9_-]+$/.test(v)) throw Error("InvalidInput");
    }
    if(typeof value.action!=="string")throw Error("InvalidInput");
    if(value.surface==="memory"&&(!value.session||!value.story||!value.branch||value.head===undefined))throw Error("InvalidInput");
    return {...value};
}
export class BrokerRetention {
    private retained: Retained | null = null;
    private listeners = new Set<()=>void>();
    constructor(private awaitingConsumption: (surface: BrokerSurface)=>boolean) {}
    get = ()=>this.retained;
    subscribe = (listener:()=>void)=>{this.listeners.add(listener);return()=>{this.listeners.delete(listener);};};
    private patch(value: Partial<Retained>) {if(this.retained)this.retained={...this.retained,...value};for(const f of this.listeners)f();}
    private blocked() {const r=this.retained;return !!r&&!r.acknowledgedUnresolved&&(r.inFlight||r.unknown||!r.terminal||this.awaitingConsumption(r.identity.surface));}
    async start(value: BrokerIdentity, work: ()=>Promise<unknown>): Promise<unknown> {
        const selected=identity(value);
        if(this.blocked())throw Error("ArchiveBusy");
        this.retained={identity:selected,inFlight:true,operation:null,terminal:false,unknown:false,acknowledgedUnresolved:false};
        this.patch({});
        try {const result=await work();this.observe(result);this.patch({inFlight:false});return result;}
        catch(error) {const name=error instanceof Error?error.message:String(error);this.patch({inFlight:false,unknown:name!=="ArchiveBusy",terminal:name==="ArchiveBusy"});throw error;}
    }
    observe(value: unknown) {
        const r=this.retained;
        if(!r||!value||typeof value!=="object")return;
        const v=value as Record<string,unknown>;
        if(Object.keys(v).length!==6||!["version","operation_id","running","phase","error","result"].every(k=>Object.hasOwn(v,k))||v.version!==1||!Number.isSafeInteger(v.operation_id)||Number(v.operation_id)<1||typeof v.running!=="boolean"||!((v.error===null)||(typeof v.error==="string"&&v.error.length<=64)))return;
        if(r.operation!==null&&r.operation!==v.operation_id)return;
        if(v.running ? !["starting","memory_maintenance","forking","export_preview","import_preview","exporting","importing"].includes(String(v.phase))||v.result!==null||v.error!==null : v.phase==="completed" ? !v.result||typeof v.result!=="object"||v.error!==null : v.phase!=="error"||typeof v.error!=="string"||v.result!==null)return;
        this.patch({operation:Number(v.operation_id),terminal:!v.running,unknown:false});
    }
    async recoverMemory(value: BrokerIdentity, work: ()=>Promise<unknown>) {
        const selected=identity(value),r=this.retained;
        if(!r||r.identity.surface!=="memory"||selected.surface!=="memory"||selected.action!=="status"||r.inFlight||!["session","story","branch","head"].every(k=>selected[k as keyof BrokerIdentity]===r.identity[k as keyof BrokerIdentity]))throw Error("ArchiveBusy");
        const oldOperation=r.operation;
        this.patch({inFlight:true});
        try {
            const result=await work();
            // A successful explicit passive read has a new broker operation.
            // Exact original selection is required; no different-scope recovery.
            this.patch({operation:null});this.observe(result);
            if(this.retained?.operation===null)this.patch({operation:oldOperation,unknown:true});
            this.patch({inFlight:false});return result;
        }catch(error){this.patch({inFlight:false,unknown:true});throw error;}
    }
    acknowledgeUnresolved(consent: boolean) {
        if(!consent||!this.retained?.unknown||this.retained.inFlight)return false;
        this.patch({acknowledgedUnresolved:true});return true;
    }
}
