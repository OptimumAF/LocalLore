// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Closed inspection metadata only. No Host reconstruction, provider, canonical
//! writer or permission constructor. Files are create-new, not atomic renames.
use crate::{digest, encode, ordinary, write_new, Result};
use crate::local_lane::comparison::read_narration_diagnostic_file_v1 as held;
use locallore::contracts::{Request, Scope};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::{fs::{self, File}, path::{Path, PathBuf}};

pub(crate) const DECLARATION: &str = "narration-diagnostics-v1.json";
pub(crate) const RECORD_CAP: usize = 7168;
const HEADER_CAP: usize = 4096;
const TOTAL_CAP: u64 = 512 * 1024;
const PREFIX: &str = "narration-diagnostic-v1-";

fn wire() -> String { "DiagnosticWire".into() }
fn binding() -> String { "DiagnosticBinding".into() }
fn identifier(s: &str) -> bool {
    !s.is_empty() && s.len() <= 64 && s.bytes().all(|b| b.is_ascii_alphanumeric() || b"-_".contains(&b))
}
fn hash(s: &str) -> bool { s.len() == 64 && s.bytes().all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase()) }
fn required_nullable<'de, D: serde::Deserializer<'de>, T: Deserialize<'de>>(d: D) -> std::result::Result<Option<T>, D::Error> {
    Option::<T>::deserialize(d)
}
pub(crate) fn present(path: &Path) -> Result<bool> {
    match fs::symlink_metadata(path) {
        Ok(_) => Ok(true),
        Err(e) if e.kind() == std::io::ErrorKind::NotFound => Ok(false),
        Err(_) => Err("DiagnosticIo".into()),
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Declaration {
    version: u16, kind: String, source_protocol_version: u16,
    run_binding_sha256: String, run_manifest_sha256: String, source_sha256: String,
    harvest: String, generation_grant: bool,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Query { version: u16, command: QueryCommand }
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct QueryCommand {
    op: String, session: String, scope: Scope, expected_head: u64,
    base_revision: u64, turn: String, attempt: u32,
}
impl Query {
    pub(crate) fn attempt(&self) -> u32 { self.command.attempt }
    pub(crate) fn bytes(&self) -> Result<Vec<u8>> { encode(self) }
    fn validate(&self) -> Result<()> {
        let q = &self.command;
        if self.version != 1 || q.op != "trace_narration_validation_read_v1" ||
            !identifier(&q.session) || !identifier(&q.scope.story) || !identifier(&q.scope.branch) || !identifier(&q.turn) {
            return Err(wire());
        }
        Ok(())
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum Outcome { Accepted, Rejected, Cancelled, Stale }
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum Category {
    Malformed, Version, Scope, Rule, Agency, Deadline, RetryMismatch, TooLarge,
    AuthorUiRequired, ClarificationRequired, UnknownReference, DeadActor, Location,
    Inventory, Resource, Ability, Knowledge, Provider, CorruptHistory, Narration, Cancelled, Stale,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
enum Reason { Unclassified, SceneFirstPerson, SceneUnapprovedMovement }
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Decision {
    version: u16, outcome: Outcome,
    #[serde(deserialize_with = "required_nullable")]
    error: Option<Category>,
    #[serde(deserialize_with = "required_nullable")]
    reason: Option<Reason>,
}
impl Decision {
    fn validate(&self) -> Result<()> {
        let valid = match (&self.outcome, &self.error, &self.reason) {
            (Outcome::Accepted, None, None) => true,
            (Outcome::Cancelled, Some(Category::Cancelled), None) => true,
            (Outcome::Stale, Some(Category::Stale), None) => true,
            (Outcome::Rejected, Some(Category::Narration), Some(_)) => true,
            (Outcome::Rejected, Some(e), None) => !matches!(e, Category::Narration | Category::Cancelled | Category::Stale),
            _ => false,
        };
        if self.version != 1 || !valid { return Err(wire()); }
        Ok(())
    }
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Recorded {
    version: u16, session: String, scope: Scope, head: u64, base_revision: u64,
    turn: String, attempt: u32, observer: String, generation_grant: bool,
    status: String, decision: Decision,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Unavailable {
    version: u16, session: String, scope: Scope, head: u64, base_revision: u64,
    turn: String, attempt: u32, observer: String, generation_grant: bool, status: String,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
enum Data { Recorded(Recorded), Unavailable(Unavailable) }
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct OkReply { version: u16, status: String, data: Data }
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
enum Rejection {
    TooLarge, Malformed, Version, Forbidden, Closed, Scope, Stale, InvalidRequest,
    InvalidSelection, Internal, Io, Database, ForeignDatabase, FutureVersion,
    SchemaMismatch, BackupRequired, BackupExists, Busy, InvalidSeed, DuplicateStory,
    NotFound, InvalidInput, Integrity, UnknownTurn, RetryMismatch, Cancelled, Full,
    Agency, AuthorUiRequired, ClarificationRequired, UnknownReference, DeadActor,
    Location, Inventory, Resource, Ability, Knowledge, Rule, Provider, Timeout,
    Narration, CorruptHistory, Storage,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct RejectedReply { version: u16, status: String, error: Rejection }
#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(untagged)]
enum Reply { Ok(OkReply), Rejected(RejectedReply) }
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum HarvestKind { Recorded, Unavailable, Rejected }
impl Reply {
    fn validate(&self, query: &Query) -> Result<()> {
        let q = &query.command;
        match self {
            Self::Rejected(r) => {
                if r.version != 1 || r.status != "rejected" { return Err(wire()); }
            }
            Self::Ok(r) => {
                if r.version != 1 || r.status != "ok" { return Err(wire()); }
                let (version,session,scope,head,base,turn,attempt,observer,grant) = match &r.data {
                    Data::Recorded(d) => {
                        if d.status != "recorded" { return Err(wire()); }
                        d.decision.validate()?;
                        (d.version,&d.session,&d.scope,d.head,d.base_revision,&d.turn,d.attempt,&d.observer,d.generation_grant)
                    }
                    Data::Unavailable(d) => {
                        if d.status != "unavailable" { return Err(wire()); }
                        (d.version,&d.session,&d.scope,d.head,d.base_revision,&d.turn,d.attempt,&d.observer,d.generation_grant)
                    }
                };
                if version != 1 || session != &q.session || scope != &q.scope || head != q.expected_head ||
                    base != q.base_revision || turn != &q.turn || attempt != q.attempt || observer != "player" || grant {
                    return Err(binding());
                }
            }
        }
        if encode(self)?.len() > 4096 { return Err("DiagnosticBudget".into()); }
        Ok(())
    }
    fn kind(&self) -> HarvestKind {
        match self {
            Self::Ok(OkReply { data: Data::Recorded(_), .. }) => HarvestKind::Recorded,
            Self::Ok(_) => HarvestKind::Unavailable,
            Self::Rejected(_) => HarvestKind::Rejected,
        }
    }
}
#[derive(Clone, Debug)]
pub(crate) struct Harvest { query: Query, reply: Reply }
impl Harvest {
    pub(crate) fn decode(query: Query, value: &Value) -> Result<Self> {
        let bytes = encode(value)?;
        if bytes.len() > 4096 { return Err("DiagnosticBudget".into()); }
        let reply: Reply = serde_json::from_slice(&bytes).map_err(|_| wire())?;
        query.validate()?; reply.validate(&query)?;
        Ok(Self { query, reply })
    }
    #[cfg(test)]
    pub(crate) fn kind(&self) -> HarvestKind { self.reply.kind() }
}
pub(crate) fn select_query(trace: &Value, session: &str, head: u64, player: &str, r: &Request) -> Result<Option<Query>> {
    if trace["status"] != "ok" { return Ok(None); }
    if trace["version"] != 1 || trace["data"]["scope"] != serde_json::to_value(&r.scope).map_err(|_| wire())? ||
        trace["data"]["head"] != head || trace["data"]["base_revision"] != r.expected_revision ||
        trace["data"]["snapshot"]["version"] != 1 { return Err(wire()); }
    let attempts = trace["data"]["snapshot"]["attempts"].as_array().ok_or_else(wire)?;
    if attempts.len() > 32 { return Err(wire()); }
    let scope = serde_json::to_value(&r.scope).map_err(|_| wire())?;
    let exact = attempts.iter().rev().find(|a| {
        let id = &a["identity"];
        id["scope"] == scope && id["base_revision"] == r.expected_revision && id["turn"] == r.turn && id["observer"] == player
    });
    let Some(exact) = exact else { return Ok(None); };
    let attempt = u32::try_from(exact["identity"]["attempt"].as_u64().ok_or_else(wire)?).map_err(|_| wire())?;
    let query = Query { version:1, command: QueryCommand { op:"trace_narration_validation_read_v1".into(), session:session.into(),
        scope:r.scope.clone(), expected_head:head, base_revision:r.expected_revision, turn:r.turn.clone(), attempt } };
    query.validate()?; Ok(Some(query))
}

#[derive(Clone, Debug, PartialEq, Eq, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct Observation {
    version:u16, kind:String, declaration_sha256:String, run_binding_sha256:String, source_sha256:String,
    arm:String, index:usize, admission:usize, checkpoint_sha256:String,
    host_query:Query, host_reply:Reply, generation_grant:bool,
}
impl Observation {
    pub(crate) fn arm(&self) -> &str { &self.arm }
    pub(crate) fn index(&self) -> usize { self.index }
    pub(crate) fn admission(&self) -> usize { self.admission }
    pub(crate) fn status(&self) -> &'static str {
        match self.host_reply.kind() { HarvestKind::Recorded => "recorded", HarvestKind::Unavailable => "host_unavailable", HarvestKind::Rejected => "host_rejected" }
    }
    pub(crate) fn value(&self) -> Result<Value> { serde_json::to_value(self).map_err(|_| wire()) }
    fn validate(&self) -> Result<()> {
        if self.version != 1 || self.kind != "full_scene_narration_observation_v1" || self.generation_grant ||
            !["left","right"].contains(&self.arm.as_str()) || self.index >= 24 || self.admission >= 32 ||
            ![&self.declaration_sha256,&self.run_binding_sha256,&self.source_sha256,&self.checkpoint_sha256].iter().all(|h| hash(h)) {
            return Err(wire());
        }
        self.host_query.validate()?; self.host_reply.validate(&self.host_query)
    }
    pub(crate) fn bind_checkpoint(&self, checkpoint: &Value, bytes: &[u8], player: &str) -> Result<()> {
        let q = &self.host_query.command;
        if checkpoint["version"] != 4 || checkpoint["binding"] != self.run_binding_sha256 || checkpoint["index"] != self.index ||
            checkpoint["arm"] != self.arm || checkpoint["row"]["admission"] != self.admission || digest(bytes) != self.checkpoint_sha256 ||
            checkpoint["request"]["scope"] != serde_json::to_value(&q.scope).map_err(|_| binding())? ||
            checkpoint["request"]["turn"] != q.turn || checkpoint["request"]["expected_revision"] != q.base_revision ||
            checkpoint["before_head"] != q.expected_head { return Err(binding()); }
        let attempts = checkpoint["row"]["trace"]["attempts"].as_array().ok_or_else(binding)?;
        if attempts.len() > 32 || !attempts.iter().any(|a| {
            let id=&a["identity"];
            id["scope"] == checkpoint["request"]["scope"] && id["base_revision"] == q.base_revision &&
                id["turn"] == q.turn && id["observer"] == player && id["attempt"] == q.attempt
        }) { return Err(binding()); }
        Ok(())
    }
}
pub(crate) struct Loaded {
    declaration:Option<Declaration>, declaration_hash:String,
    pub(crate) observations:Vec<Observation>, _pins:Vec<File>,
}
impl Loaded {
    pub(crate) fn declared(&self) -> bool { self.declaration.is_some() }
    pub(crate) fn retain_pin(&mut self,file:File){self._pins.push(file);}
}
fn name(admission:usize) -> String { format!("{PREFIX}{admission:02}.json") }
pub(crate) fn observation_path(dir:&Path, admission:usize) -> PathBuf { dir.join(name(admission)) }
// Same existing run boundary as the native manager, only for opt-in writes.
// The manager still owns its256MiB whole-library boundary; no allowance is added.
fn run_budget(root:&Path,extra:usize)->Result<()> {
    fn visit(path:&Path,depth:usize,entries:&mut usize,total:&mut u64)->Result<()> {
        if depth>6 {return Err("DiagnosticBudget".into());}
        ordinary(path)?;
        let metadata=fs::symlink_metadata(path).map_err(|_|"DiagnosticIo")?;
        *entries=entries.checked_add(1).ok_or("DiagnosticBudget")?;
        if *entries>8192 {return Err("DiagnosticBudget".into());}
        if metadata.is_file() {
            *total=total.checked_add(metadata.len()).ok_or("DiagnosticBudget")?;
            if *total>32*1024*1024 {return Err("DiagnosticBudget".into());}
        }else if metadata.is_dir(){
            for entry in fs::read_dir(path).map_err(|_|"DiagnosticIo")? {
                visit(&entry.map_err(|_|"DiagnosticIo")?.path(),depth+1,entries,total)?;
            }
        }else{return Err("DiagnosticWire".into());}
        Ok(())
    }
    let mut entries=0usize;let mut total=0u64;
    visit(root,0,&mut entries,&mut total)?;
    if entries>=8192 || total.checked_add(extra as u64).ok_or("DiagnosticBudget")?>32*1024*1024 {
        return Err("DiagnosticBudget".into());
    }
    Ok(())
}
fn namespace(root:&Path) -> Result<Vec<(String,usize,PathBuf)>> {
    if present(&root.join("selected.json"))? { return Err(binding()); }
    let mut records=Vec::new(); let mut total=0u64; let mut count=0usize; let mut entries=0usize;
    for arm in ["", "left", "right"] {
        let dir=if arm.is_empty(){root.to_owned()}else{root.join(arm)};
        ordinary(&dir)?;
        for entry in fs::read_dir(dir).map_err(|_| "DiagnosticIo")? {
            entries=entries.checked_add(1).ok_or("DiagnosticBudget")?;
            if entries>8192 { return Err("DiagnosticBudget".into()); }
            let entry=entry.map_err(|_| "DiagnosticIo")?;
            let Some(file)=entry.file_name().to_str().map(str::to_owned) else { return Err(wire()); };
            if !file.to_ascii_lowercase().starts_with("narration-diagnostic") { continue; }
            ordinary(&entry.path())?;
            let meta=fs::symlink_metadata(entry.path()).map_err(|_| "DiagnosticIo")?;
            if !meta.is_file() { return Err(wire()); }
            let cap=if arm.is_empty() && file==DECLARATION { HEADER_CAP } else {
                let admission=file.strip_prefix(PREFIX).and_then(|s|s.strip_suffix(".json")).and_then(|s|s.parse::<usize>().ok()).ok_or_else(wire)?;
                if arm.is_empty() || admission>=32 || file!=name(admission) { return Err(wire()); }
                records.push((arm.to_owned(),admission,entry.path())); RECORD_CAP
            };
            count=count.checked_add(1).ok_or("DiagnosticBudget")?;
            total=total.checked_add(meta.len()).ok_or("DiagnosticBudget")?;
            if meta.len()>cap as u64 || count>65 || total>TOTAL_CAP { return Err("DiagnosticBudget".into()); }
        }
    }
    records.sort_by(|a,b| (&a.0,a.1).cmp(&(&b.0,b.1))); Ok(records)
}
pub(crate) fn load(root:&Path, key:&str, source:&str) -> Result<Loaded> {
    let records=namespace(root)?;
    if !present(&root.join(DECLARATION))? {
        if !records.is_empty() { return Err(binding()); }
        return Ok(Loaded{declaration:None,declaration_hash:String::new(),observations:vec![],_pins:vec![]});
    }
    let (header_file,bytes)=held(&root.join(DECLARATION),HEADER_CAP)?;
    let declaration:Declaration=serde_json::from_slice(&bytes).map_err(|_|wire())?;
    let (manifest_file,manifest)=held(&root.join("run.json"),128*1024)?;
    if declaration.version!=1 || declaration.kind!="full_scene_narration_diagnostics_v1" || declaration.source_protocol_version!=4 ||
        declaration.harvest!="first_exact_precommit_host_v1" || declaration.generation_grant ||
        ![&declaration.run_binding_sha256,&declaration.run_manifest_sha256,&declaration.source_sha256].iter().all(|h|hash(h)) ||
        declaration.run_binding_sha256!=key || declaration.source_sha256!=source || declaration.run_manifest_sha256!=digest(&manifest) {
        return Err(binding());
    }
    let declaration_hash=digest(&bytes); let mut pins=vec![header_file,manifest_file]; let mut observations=Vec::new();
    for (arm,admission,path) in records {
        let (file,bytes)=held(&path,RECORD_CAP)?;
        let ob:Observation=serde_json::from_slice(&bytes).map_err(|_|wire())?; ob.validate()?;
        if ob.arm!=arm || ob.admission!=admission || ob.declaration_sha256!=declaration_hash || ob.run_binding_sha256!=key || ob.source_sha256!=source { return Err(binding()); }
        pins.push(file); observations.push(ob);
    }
    Ok(Loaded{declaration:Some(declaration),declaration_hash,observations,_pins:pins})
}
pub(crate) fn declare(root:&Path,key:&str,source:&str) -> Result<()> {
    if !namespace(root)?.is_empty() || present(&root.join(DECLARATION))? { return Err(binding()); }
    for arm in ["left","right"] {
        for entry in fs::read_dir(root.join(arm)).map_err(|_|"DiagnosticIo")? {
            let entry=entry.map_err(|_|"DiagnosticIo")?;
            let s=entry.file_name().to_str().ok_or_else(wire)?.to_owned();
            if s.starts_with("attempt-") || s.starts_with("admission-") || s.starts_with("invocation-") { return Err(binding()); }
        }
    }
    let (_pin,manifest)=held(&root.join("run.json"),128*1024)?;
    let d=Declaration {version:1,kind:"full_scene_narration_diagnostics_v1".into(),source_protocol_version:4,
        run_binding_sha256:key.into(),run_manifest_sha256:digest(&manifest),source_sha256:source.into(),
        harvest:"first_exact_precommit_host_v1".into(),generation_grant:false};
    let bytes=encode(&d)?; if bytes.len()>HEADER_CAP { return Err("DiagnosticBudget".into()); }
    run_budget(root,bytes.len())?;
    ordinary(&root.join(DECLARATION))?; write_new(&root.join(DECLARATION),&bytes)
}
fn build_observation(dir:&Path,index:usize,admission:usize,checkpoint:&Value,bytes:&[u8],player:&str,harvest:&Harvest) -> Result<(Observation,Loaded)> {
    let root=dir.parent().ok_or_else(binding)?;
    let arm=dir.file_name().and_then(|s|s.to_str()).ok_or_else(binding)?;
    let key=checkpoint["binding"].as_str().ok_or_else(binding)?;
    let (_manifest_file,manifest_bytes)=held(&root.join("run.json"),128*1024)?;
    let manifest:Value=serde_json::from_slice(&manifest_bytes).map_err(|_|wire())?;
    let source=manifest["source_sha256"].as_str().ok_or_else(binding)?;
    let loaded=load(root,key,source)?;
    if !loaded.declared() { return Err(binding()); }
    let ob=Observation {version:1,kind:"full_scene_narration_observation_v1".into(),declaration_sha256:loaded.declaration_hash.clone(),
        run_binding_sha256:key.into(),source_sha256:source.into(),arm:arm.into(),index,admission,checkpoint_sha256:digest(bytes),
        host_query:harvest.query.clone(),host_reply:harvest.reply.clone(),generation_grant:false};
    ob.validate()?; ob.bind_checkpoint(checkpoint,bytes,player)?;
    Ok((ob,loaded))
}
pub(crate) fn publish(dir:&Path,index:usize,admission:usize,checkpoint:&Value,bytes:&[u8],player:&str,harvest:&Harvest) -> Result<()> {
    let (ob,_pins)=build_observation(dir,index,admission,checkpoint,bytes,player,harvest)?;
    let root=dir.parent().ok_or_else(binding)?;
    let encoded=encode(&ob)?; if encoded.len()>RECORD_CAP { return Err("DiagnosticBudget".into()); }
    let path=observation_path(dir,admission);
    if present(&path)? {
        let (_file,existing)=held(&path,RECORD_CAP)?;
        let prior:Observation=serde_json::from_slice(&existing).map_err(|_|wire())?;
        if prior!=ob { return Err(binding()); }
        prior.validate()?; prior.bind_checkpoint(checkpoint,bytes,player)?;
        return Ok(());
    }
    run_budget(root,encoded.len())?;
    ordinary(&path)?; write_new(&path,&encoded)?; namespace(root)?; Ok(())
}
#[cfg(test)]
pub(crate) fn write_test_fault(dir:&Path,index:usize,admission:usize,checkpoint:&Value,bytes:&[u8],player:&str,fault:(&Harvest,bool))->Result<()> {
    let (harvest,partial)=fault;
    let (mut observation,_pins)=build_observation(dir,index,admission,checkpoint,bytes,player,harvest)?;
    let path=observation_path(dir,admission);
    if partial {write_new(&path,b"{\"version\":")}
    else {observation.checkpoint_sha256="0".repeat(64);write_new(&path,&encode(&observation)?)}
}
