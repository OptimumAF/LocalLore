// Explicit stateless reads. No inference, job mutation, grants or native owner registry.
import {
    checkedMemoryInspection, checkedMemoryInspectionContext, checkedMemorySourceRef,
    memoryInspectionAllowed, memoryInspectionContextIdentity, memoryInspectionError, memorySourceIdentity,
} from "./memory-inspection-model";
import type {
    MemoryInspectionContext, MemoryInspectionRead, MemoryInspectionState,
    MemoryPacketDescriptor, MemorySourceRef,
} from "./memory-inspection-model";

type Invoke = (command: string, args: Record<string, unknown>) => Promise<unknown>;
const PAGE_LIMIT = 16;
const empty = {busy:false,action:null,packets:null,selected:null,entries:null,source:null,error:null,notice:""};
export class MemoryInspectionController {
    private state: MemoryInspectionState = Object.freeze({context:null,allowed:false,...empty});
    private listeners = new Set<() => void>();
    private epoch = 0;
    private key = "none";
    private disposed = false;
    constructor(private invoke: Invoke) {}
    get = () => this.state;
    subscribe = (listener: () => void) => {
        this.listeners.add(listener);
        return () => { this.listeners.delete(listener); };
    };
    private patch(value: Partial<MemoryInspectionState>) {
        this.state = Object.freeze({...this.state,...value});
        for (const listener of [...this.listeners]) listener();
    }
    matchesContext(context: MemoryInspectionContext | null) {
        try { return !this.disposed && this.key === memoryInspectionContextIdentity(context); }
        catch { return false; }
    }
    contextChanged(context: MemoryInspectionContext | null) {
        if (this.disposed) return;
        let next: MemoryInspectionContext | null = null, key = "none";
        try {
            next = context === null ? null : checkedMemoryInspectionContext(context);
            key = memoryInspectionContextIdentity(next);
        } catch { key = "invalid"; }
        if (key === this.key) return;
        // Retire BEFORE any subscriber can try work for the previous selection.
        this.epoch++;
        this.key = key;
        this.patch({context:next,allowed:memoryInspectionAllowed(next),...empty,
            error:key === "invalid" ? "Wire" : null});
    }
    canRead() { return !this.disposed && this.state.allowed && !this.state.busy; }
    clear() {
        if (this.disposed) return;
        this.epoch++;
        this.patch({...empty});
    }
    dispose() {
        if (this.disposed) return;
        this.disposed = true;
        this.epoch++;
        this.key = "none";
        this.patch({context:null,allowed:false,...empty});
        this.listeners.clear();
    }
    private owns(epoch: number, key: string) {
        return !this.disposed && this.epoch === epoch && this.key === key && this.state.allowed;
    }
    private async read(read: MemoryInspectionRead, pending: Partial<MemoryInspectionState>) {
        if (!this.canRead() || !this.state.context) return;
        const context = this.state.context, key = this.key, epoch = ++this.epoch;
        const common = {version:1,session:context.session,scope:{...context.scope},
            expected_head:context.expected_head,observer:{kind:"player"},binding:read.binding};
        const request = read.action === "packets"
            ? {...common,cursor:read.cursor,limit:read.limit}
            : read.action === "entries"
                ? {...common,packet_index:read.packet.index,cursor:read.cursor,limit:read.limit}
                : {...common,packet_index:read.packet.index,source:read.source};
        const encoded = JSON.stringify(request);
        if (new TextEncoder().encode(encoded).length > 4096) return;
        this.patch({...pending,busy:true,action:read.action,error:null,notice:"Waiting for this read."});
        try {
            // Listeners may synchronously change selection/grant/lens/dispose.
            if (!this.owns(epoch,key)) return;
            const value = await this.invoke("memory_inspection",{action:read.action,request:encoded});
            if (!this.owns(epoch,key)) return;
            const reply = checkedMemoryInspection(value,context,read);
            if (!this.owns(epoch,key)) return;
            if (reply.kind === "memory_source") {
                this.patch({busy:false,source:reply,notice:"Original scope and event matched shared history."});
            } else if (reply.view === "packets") {
                this.patch({busy:false,packets:reply,notice:"Read one snapshot of derived packets."});
            } else {
                this.patch({busy:false,entries:reply,notice:"Read extractive entries from this verified packet."});
            }
        } catch (error) {
            if (this.owns(epoch,key)) this.patch({...empty,error:memoryInspectionError(error),
                notice:"Read unavailable. Use Read packets to obtain a fresh snapshot."});
        }
    }
    async refresh() {
        if (!this.canRead()) return;
        await this.read({action:"packets",binding:null,cursor:null,limit:PAGE_LIMIT},empty);
    }
    async packetPage(cursor: string) {
        const page = this.state.packets;
        if (!this.canRead() || !page || page.next_cursor === null || cursor !== page.next_cursor) return;
        await this.read({action:"packets",binding:page.binding,cursor,limit:PAGE_LIMIT},{});
    }
    async selectPacket(index: number) {
        const page = this.state.packets;
        if (!this.canRead() || !page || !Number.isSafeInteger(index)) return;
        const packet: MemoryPacketDescriptor | undefined = page.rows.find(row => row.index === index)
            ?? (this.state.selected?.index === index ? this.state.selected : undefined);
        if (!packet) return;
        await this.read({action:"entries",binding:page.binding,cursor:null,limit:PAGE_LIMIT,packet},
            {selected:packet,entries:null,source:null});
    }
    async entryPage(cursor: string) {
        const {packets,selected,entries} = this.state;
        if (!this.canRead() || !packets || !selected || !entries || entries.binding !== packets.binding
            || entries.packet_index !== selected.index || entries.next_cursor === null || cursor !== entries.next_cursor) return;
        await this.read({action:"entries",binding:entries.binding,cursor,limit:PAGE_LIMIT,packet:selected},{source:null});
    }
    async source(value: MemorySourceRef) {
        const {context,packets,selected,entries} = this.state;
        if (!this.canRead() || !context || !packets || !selected || !entries
            || entries.binding !== packets.binding || entries.packet_index !== selected.index) return;
        let source: MemorySourceRef;
        try { source = checkedMemorySourceRef(value,context,selected); } catch { return; }
        const permitted = entries.rows.some(row => {
            const refs = row.value.class === "observation" ? [row.value.source] : row.value.source_events;
            return refs.some(ref => memorySourceIdentity(ref) === memorySourceIdentity(source));
        });
        if (!permitted) return;
        await this.read({action:"source",binding:entries.binding,packet:selected,source},{source:null});
    }
}
