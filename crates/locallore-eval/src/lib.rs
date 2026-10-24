//! Synthetic shared-Host evaluation: deterministic defaults and an explicit local-model lane.
//! No user-story import, GUI automation or network-observation lane.
use locallore::{
    context_compiler::{self, Budget, CompileRequest, Role},
    contracts::*,
    engine::Engine,
    host::Host,
    inference::*,
    play::{PlayProfile, NARRATION_POLICY, PROMPT_VERSION},
};
use locallore_storage::Store;
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs::{self, OpenOptions},
    io::Write,
    path::Path,
    sync::{Arc, Mutex},
    task::Poll,
};

pub mod local_lane;
mod local_recording;
pub mod memory_comparison;
pub mod memory_comparison_v2;

pub const VERSION: u16 = 1;
pub const MAX_REPORT: usize = 2 * 1024 * 1024;
const MAX_CASE: usize = 64 * 1024;
const SUITE: &[u8] = include_bytes!("../../../fixtures/eval/reference-v1.json");
const SEED: &[u8] = include_bytes!("../../../fixtures/lantern_quay.json");
include!(concat!(env!("OUT_DIR"), "/source_inputs.rs"));
type Result<T> = std::result::Result<T, String>;
pub fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn encode<T: Serialize + ?Sized>(value: &T) -> Result<Vec<u8>> {
    serde_json::to_vec(value).map_err(|_| "Encoding".into())
}
fn id(s: &str) -> bool {
    !s.is_empty() && s.len() <= 48 && s.bytes().all(|b| b.is_ascii_alphanumeric() || b == b'-')
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Suite {
    pub version: u16,
    pub synthetic: bool,
    pub seed_id: String,
    pub seed_sha256: String,
    pub scenarios: Vec<Scenario>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Scenario {
    pub id: String,
    pub steps: Vec<Step>,
    pub assertions: Vec<Assertion>,
    pub probes: Vec<Probe>,
    pub unsupported: Option<String>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Step {
    pub id: String,
    pub intent: Intent,
    pub repeat: u8,
    pub scripted: Option<ScriptPlan>,
    pub phase: String,
    pub error: Option<String>,
    pub revision_delta: u64,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ScriptPlan {
    pub commands: Vec<Command>,
    pub narration: String,
    pub prompt_targets: Vec<Target>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case", deny_unknown_fields)]
pub enum Assertion {
    Canonical {
        id: String,
        pointer: String,
        equals: Value,
    },
    Absent {
        id: String,
        pointer: String,
    },
    Context {
        id: String,
        observer: String,
        query: String,
        required: Vec<Target>,
        forbidden: Vec<String>,
        error: Option<String>,
    },
    ProhibitedNarration {
        id: String,
        text: String,
    },
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Target {
    pub kind: String,
    pub contains: String,
    pub source: Value,
}
#[derive(Clone, Copy, Debug, Deserialize, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum Probe {
    ReplayResume,
    Retry,
    Cancel,
    Stale,
    StoryScope,
}
#[derive(Clone, Debug, Deserialize, Serialize, PartialEq, Eq)]
#[serde(rename_all = "snake_case")]
pub enum Status {
    Passed,
    Failed,
    Unsupported,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Check {
    pub id: String,
    pub turn: Option<String>,
    pub stage: String,
    pub status: Status,
    pub expected: Value,
    pub actual: Value,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Turn {
    pub id: String,
    pub intent: Intent,
    pub phase: Value,
    pub error: Value,
    pub revision: u64,
    pub canonical_sha256: String,
    pub narration: Option<String>,
    pub fallback: Option<bool>,
    pub repairs: Option<u64>,
}
#[derive(Clone, Debug, Default, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct Capture {
    pub turn: String,
    pub role: String,
    pub prompt_sha256: String,
    pub schema_sha256: String,
    pub compiler_version: Option<u64>,
    pub player_text_sha256: Option<String>,
    pub prompt_targets: Vec<Target>,
    pub prompt_targets_present: Vec<bool>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CaseResult {
    pub id: String,
    pub status: Status,
    pub checks: Vec<Check>,
    pub turns: Vec<Turn>,
    pub provider_requests: Vec<Capture>,
    pub unsupported: Option<String>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Binding {
    version: u16,
    suite_sha256: String,
    seed_sha256: String,
    host_schema_sha256: String,
    engine_sha256: String,
    compiler_sha256: String,
    play_sha256: String,
    runner_sha256: String,
    host_sha256: String,
    workspace_sha256: String,
    storage_sha256: String,
    source_inputs: BTreeMap<String, String>,
    rules_profile: String,
    domain_version: u16,
    storage_schema_version: u32,
    prompt_version: String,
    narration_policy: String,
    cases: Vec<String>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Stored {
    version: u16,
    binding_sha256: String,
    result_sha256: String,
    result: CaseResult,
}
#[derive(Clone, Debug, Serialize)]
pub struct Report {
    pub version: u16,
    pub lane: &'static str,
    pub synthetic: bool,
    pub os: &'static str,
    pub arch: &'static str,
    pub hardware: Option<String>,
    pub model: Option<String>,
    pub runtime: Option<String>,
    pub quality_accepted: bool,
    pub android_parity: &'static str,
    pub unsupported_lanes: Vec<&'static str>,
    pub provider_profiles: Vec<&'static str>,
    pub binding_sha256: String,
    pub provenance: Value,
    pub completed: bool,
    pub cancelled: bool,
    pub cases: Vec<CaseResult>,
}

pub fn builtin() -> Result<Suite> {
    if SUITE.len() > 128 * 1024 {
        return Err("SuiteBudget".into());
    }
    let suite: Suite = serde_json::from_slice(SUITE).map_err(|_| "InvalidSuite")?;
    validate(&suite)?;
    Ok(suite)
}
fn validate(suite: &Suite) -> Result<()> {
    let seed: Value = serde_json::from_slice(SEED).map_err(|_| "Seed")?;
    if suite.version != VERSION
        || !suite.synthetic
        || suite.seed_id != "lantern-quay-v1"
        || suite.seed_sha256 != digest(&encode(&seed)?)
        || suite.scenarios.is_empty()
        || suite.scenarios.len() > 32
    {
        return Err("InvalidSuite".into());
    }
    let mut ids = BTreeSet::new();
    let mut total = 0usize;
    for case in &suite.scenarios {
        if !id(&case.id)
            || !ids.insert(&case.id)
            || case.assertions.len() > 32
            || case.probes.len() > 5
            || (case.assertions.is_empty() && case.probes.is_empty() && case.unsupported.is_none())
        {
            return Err("InvalidScenario".into());
        }
        if let Some(reason) = &case.unsupported {
            if reason.is_empty()
                || reason.len() > 1024
                || !case.steps.is_empty()
                || !case.assertions.is_empty()
                || !case.probes.is_empty()
            {
                return Err("InvalidUnsupported".into());
            }
        }
        let mut steps = BTreeSet::new();
        let mut expanded = 0;
        for step in &case.steps {
            expanded += usize::from(step.repeat);
            if !id(&step.id)
                || !steps.insert(&step.id)
                || step.repeat == 0
                || step.repeat > 48
                || !matches!(step.phase.as_str(), "committed" | "failed" | "rejected")
                || step.revision_delta > 8
                || encode(&step.intent)?.len() > 2048
                || (matches!(step.intent, Intent::FreeText { .. }) != step.scripted.is_some())
            {
                return Err("InvalidStep".into());
            }
            if let Some(plan) = &step.scripted {
                if plan.commands.len() > 8
                    || plan.narration.len() > 1024
                    || plan.prompt_targets.len() > 8
                    || plan.prompt_targets.iter().any(|target| {
                        target.kind.len() > 64
                            || target.contains.len() > 256
                            || target.source.to_string().len() > 512
                    })
                {
                    return Err("ScriptBudget".into());
                }
            }
        }
        if expanded > 48 {
            return Err("ScenarioBudget".into());
        }
        total += expanded;
        let mut checks = BTreeSet::new();
        for assertion in &case.assertions {
            let name = match assertion {
                Assertion::Canonical {
                    id,
                    pointer,
                    equals,
                } => {
                    if !pointer.starts_with('/')
                        || pointer.len() > 128
                        || encode(equals)?.len() > 2048
                    {
                        return Err("InvalidAssertion".into());
                    }
                    id
                }
                Assertion::Absent { id, pointer } => {
                    if !pointer.starts_with('/') || pointer.len() > 128 {
                        return Err("InvalidAssertion".into());
                    }
                    id
                }
                Assertion::Context {
                    id,
                    observer,
                    query,
                    required,
                    forbidden,
                    error,
                } => {
                    if !id_fn(observer)
                        || query.len() > 256
                        || required.len() > 8
                        || forbidden.len() > 8
                        || error.as_ref().is_some_and(|s| s.len() > 48)
                        || required
                            .iter()
                            .any(|t| t.kind.len() > 32 || t.contains.len() > 512)
                        || forbidden.iter().any(|s| s.is_empty() || s.len() > 512)
                    {
                        return Err("InvalidAssertion".into());
                    }
                    id
                }
                Assertion::ProhibitedNarration { id, text } => {
                    if text.is_empty() || text.len() > 512 {
                        return Err("InvalidAssertion".into());
                    }
                    id
                }
            };
            if !id(name) || !checks.insert(name) {
                return Err("InvalidAssertion".into());
            }
        }
    }
    if total > 256 {
        return Err("SuiteBudget".into());
    }
    Ok(())
}
fn id_fn(s: &str) -> bool {
    id(s)
}
fn binding(suite: &Suite, selected: Option<&str>) -> Result<Binding> {
    if selected.is_some_and(|s| !suite.scenarios.iter().any(|c| c.id == s)) {
        return Err("UnknownCase".into());
    }
    Ok(Binding {
        version: VERSION,
        suite_sha256: digest(SUITE),
        seed_sha256: suite.seed_sha256.clone(),
        host_schema_sha256: digest(&encode(&locallore::host::schema())?),
        engine_sha256: digest(include_bytes!("../../locallore/src/engine.rs")),
        compiler_sha256: digest(include_bytes!("../../locallore/src/context_compiler.rs")),
        play_sha256: digest(include_bytes!("../../locallore/src/play.rs")),
        runner_sha256: digest(include_bytes!("lib.rs")),
        host_sha256: digest(include_bytes!("../../locallore/src/host.rs")),
        workspace_sha256: digest(include_bytes!("../../locallore-workspace/src/lib.rs")),
        storage_sha256: digest(include_bytes!("../../locallore-storage/src/turns.rs")),
        source_inputs: SOURCE_INPUTS
            .iter()
            .map(|(name, bytes)| (name.to_string(), digest(bytes)))
            .collect(),
        rules_profile: "fantasy_v1".into(),
        domain_version: locallore::contracts::VERSION,
        storage_schema_version: locallore_storage::SCHEMA_VERSION,
        prompt_version: PROMPT_VERSION.into(),
        narration_policy: NARRATION_POLICY.into(),
        cases: suite
            .scenarios
            .iter()
            .filter(|c| selected.is_none_or(|s| s == c.id))
            .map(|c| c.id.clone())
            .collect(),
    })
}
fn call(host: &Host, command: Value) -> Value {
    host.call(&serde_json::to_vec(&json!({"version":1,"command":command})).unwrap())
}
fn op(host: &Host, session: &str, scope: &Scope, turn: &str, name: &str) -> Value {
    call(
        host,
        json!({"op":name,"session":session,"scope":scope,"turn":turn}),
    )
}
fn create(host: &Host) -> Result<(String, Scope)> {
    let value = call(host, json!({"op":"create","seed":"lantern-quay-v1"}));
    Ok((
        value["data"]["session"].as_str().ok_or("Create")?.into(),
        serde_json::from_value(value["data"]["scope"].clone()).map_err(|_| "Create")?,
    ))
}
fn engine(path: &Path, scope: &Scope) -> Result<Engine> {
    Store::open_read_only(path)
        .map_err(|_| "Storage")?
        .resume(scope)
        .map(|s| s.engine)
        .map_err(|_| "Replay".into())
}
fn profile() -> PlayProfile {
    PlayProfile {
        id: "eval-scripted-fake-v1".into(),
        model_sha256: "0".repeat(64),
        runtime_revision: "0".repeat(40),
        template_sha256: "0".repeat(64),
        worker_sha256: "0".repeat(64),
        profile_manifest_sha256: "0".repeat(64),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 220,
        deadline_ms: 5000,
        repair_limit: 1,
    }
}
struct Script {
    plan: ScriptPlan,
    captures: Arc<Mutex<Vec<Capture>>>,
    #[cfg(test)]
    drop_forwarded: bool,
}
fn contains_json(haystack: &Value, needle: &Value) -> bool {
    haystack == needle
        || match haystack {
            Value::Object(map) => map.values().any(|v| contains_json(v, needle)),
            Value::Array(items) => items.iter().any(|v| contains_json(v, needle)),
            _ => false,
        }
}
impl InferenceProvider for Script {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        let Input::Structured {
            role,
            prompt,
            schema,
        } = &request.input
        else {
            return Poll::Ready(Err(Error::Provider));
        };
        let mut captures = self.captures.lock().unwrap();
        if captures.len() >= 128 {
            return Poll::Ready(Err(Error::TooLarge));
        }
        // Read the actual production prompt envelope, not a second context compiler.
        // This fixed template boundary is deliberately asserted; format drift fails the case.
        let input = if role == "director" {
            prompt.split_once("Context data: ").and_then(|(_, suffix)| {
                Value::deserialize(&mut serde_json::Deserializer::from_str(suffix)).ok()
            })
        } else {
            None
        };
        // Test-only downstream forwarding fault: the actual compiler result is
        // untouched, but the observed director envelope has lost commitments.
        #[cfg(test)]
        let input = {
            let mut input = input;
            if self.drop_forwarded {
                if let Some(records) = input
                    .as_mut()
                    .and_then(|i| i["context"]["records"].as_array_mut())
                {
                    records.retain(|r| r["kind"] != "commitment");
                }
            }
            input
        };
        let targets = self
            .plan
            .prompt_targets
            .iter()
            .map(|target| {
                input
                    .as_ref()
                    .and_then(|i| i["context"]["records"].as_array())
                    .is_some_and(|records| {
                        records.iter().any(|r| {
                            r["kind"] == target.kind
                                && r.to_string().contains(&target.contains)
                                && contains_json(r, &target.source)
                        })
                    })
            })
            .collect();
        captures.push(Capture {
            turn: request.turn.clone(),
            role: role.clone(),
            prompt_sha256: digest(prompt.as_bytes()),
            schema_sha256: digest(&serde_json::to_vec(schema).unwrap()),
            compiler_version: input
                .as_ref()
                .and_then(|i| i["context"]["compiler_version"].as_u64()),
            player_text_sha256: input
                .as_ref()
                .and_then(|i| i["player_text"].as_str())
                .map(|s| digest(s.as_bytes())),
            prompt_targets: self.plan.prompt_targets.clone(),
            prompt_targets_present: targets,
        });
        let value = if role == "director" {
            json!({"commands":self.plan.commands})
        } else {
            json!({"text":self.plan.narration,"speaker":"narrator","event_ids":schema["properties"]["event_ids"]["const"]})
        };
        Poll::Ready(Ok(serde_json::to_vec(&value).unwrap()))
    }
}
fn check(
    case: &mut CaseResult,
    id: impl Into<String>,
    turn: Option<String>,
    stage: &str,
    expected: Value,
    actual: Value,
) {
    let status = if expected == actual {
        Status::Passed
    } else {
        Status::Failed
    };
    case.checks.push(Check {
        id: id.into(),
        turn,
        stage: stage.into(),
        status,
        expected,
        actual,
    });
}

#[derive(Clone, Copy)]
enum Fault {
    None,
    #[cfg(test)]
    DropCompiler,
    #[cfg(test)]
    DropForwarded,
}

fn evaluate(spec: &Scenario, directory: &Path, fault: Fault) -> Result<CaseResult> {
    #[cfg(not(test))]
    let _ = fault;
    let mut out = CaseResult {
        id: spec.id.clone(),
        status: Status::Passed,
        checks: vec![],
        turns: vec![],
        provider_requests: vec![],
        unsupported: spec.unsupported.clone(),
    };
    if spec.unsupported.is_some() {
        out.status = Status::Unsupported;
        return Ok(out);
    }
    let execution: Result<()> = (|| {
        let path = directory.join("synthetic.sqlite");
        let mut host = locallore_workspace::open(&path, true).map_err(|_| "Workspace")?;
        let (mut session, scope) = create(&host)?;
        let captures = Arc::new(Mutex::new(Vec::new()));
        let mut last: Option<(Request, Value, bool)> = None;
        for step in &spec.steps {
            for index in 0..step.repeat {
                let turn = format!("{}-{index}", step.id);
                let before = engine(&path, &scope)?;
                let request = Request {
                    version: 1,
                    scope: scope.clone(),
                    turn: turn.clone(),
                    expected_revision: before.revision(),
                    intent: step.intent.clone(),
                };
                if let Some(plan) = &step.scripted {
                    let plan = plan.clone();
                    let captures = captures.clone();
                    host.configure_local_provider(
                        profile(),
                        Arc::new(move || {
                            Box::new(Script {
                                plan: plan.clone(),
                                captures: captures.clone(),
                                #[cfg(test)]
                                drop_forwarded: matches!(fault, Fault::DropForwarded),
                            })
                        }),
                    )
                    .map_err(|_| "Provider")?;
                }
                let scripted = step.scripted.is_some();
                let mut result = call(
                    &host,
                    if scripted {
                        json!({"op":"free_text","session":session,"request":request})
                    } else {
                        json!({"op":"submit","session":session,"request":request,"mode":"accepted"})
                    },
                );
                if result["data"]["phase"] == "queued" {
                    result = op(&host, &session, &scope, &turn, "prepare");
                }
                if result["data"]["phase"] == "ready" {
                    result = op(&host, &session, &scope, &turn, "commit");
                }
                let after = engine(&path, &scope)?;
                let phase = if result["status"] == "rejected" {
                    json!("rejected")
                } else {
                    result["data"]["phase"].clone()
                };
                let error = if result["status"] == "rejected" {
                    result["error"].clone()
                } else {
                    result["data"]["error"].clone()
                };
                check(
                    &mut out,
                    format!("{turn}-phase"),
                    Some(turn.clone()),
                    "pipeline",
                    json!(step.phase),
                    phase.clone(),
                );
                check(
                    &mut out,
                    format!("{turn}-error"),
                    Some(turn.clone()),
                    "pipeline",
                    json!(step.error),
                    error.clone(),
                );
                check(
                    &mut out,
                    format!("{turn}-revision"),
                    Some(turn.clone()),
                    "canonical",
                    json!(before.revision() + step.revision_delta),
                    json!(after.revision()),
                );
                if step.revision_delta == 0 {
                    check(
                        &mut out,
                        format!("{turn}-atomic"),
                        Some(turn.clone()),
                        "canonical",
                        json!(digest(&before.canonical_bytes())),
                        json!(digest(&after.canonical_bytes())),
                    );
                }
                if let (Some(plan), Intent::FreeText { text, .. }) = (&step.scripted, &step.intent)
                {
                    if step.phase == "committed" {
                        let directors: Vec<_> = captures
                            .lock()
                            .unwrap()
                            .iter()
                            .filter(|c| c.turn == turn && c.role == "director")
                            .cloned()
                            .collect();
                        check(
                            &mut out,
                            format!("{turn}-director-count"),
                            Some(turn.clone()),
                            "pipeline",
                            json!(1),
                            json!(directors.len()),
                        );
                        for capture in directors {
                            check(
                                &mut out,
                                format!("{turn}-compiler-envelope"),
                                Some(turn.clone()),
                                "retrieval",
                                json!(context_compiler::POLICY_COMPILER_VERSION),
                                json!(capture.compiler_version),
                            );
                            check(
                                &mut out,
                                format!("{turn}-original-input"),
                                Some(turn.clone()),
                                "agency",
                                json!(digest(text.as_bytes())),
                                json!(capture.player_text_sha256),
                            );
                            check(
                                &mut out,
                                format!("{turn}-prompt-targets"),
                                Some(turn.clone()),
                                "retrieval",
                                json!(vec![true; plan.prompt_targets.len()]),
                                json!(capture.prompt_targets_present),
                            );
                        }
                    }
                }
                let narration = result["data"]["receipt"]["narration"]
                    .as_str()
                    .map(str::to_owned);
                out.turns.push(Turn {
                    id: turn.clone(),
                    intent: step.intent.clone(),
                    phase,
                    error,
                    revision: after.revision(),
                    canonical_sha256: digest(&after.canonical_bytes()),
                    narration,
                    fallback: result["data"]["receipt"]["play"]["fallback"].as_bool(),
                    repairs: result["data"]["receipt"]["play"]["repairs"].as_u64(),
                });
                if result["data"]["phase"] == "committed" {
                    last = Some((request, result, scripted));
                }
            }
        }
        let current = engine(&path, &scope)?;
        let state = serde_json::to_value(current.state()).map_err(|_| "Encoding")?;
        for assertion in &spec.assertions {
            match assertion {
                Assertion::Canonical {
                    id,
                    pointer,
                    equals,
                } => check(
                    &mut out,
                    id,
                    None,
                    "canonical",
                    equals.clone(),
                    state
                        .pointer(pointer)
                        .cloned()
                        .unwrap_or(json!({"missing":true})),
                ),
                Assertion::Absent { id, pointer } => check(
                    &mut out,
                    id,
                    None,
                    "canonical",
                    json!(true),
                    json!(state.pointer(pointer).is_none()),
                ),
                Assertion::ProhibitedNarration { id, text } => {
                    let hits: Vec<_> = out
                        .turns
                        .iter()
                        .filter(|t| t.narration.as_ref().is_some_and(|s| s.contains(text)))
                        .map(|t| t.id.clone())
                        .collect();
                    check(
                        &mut out,
                        id,
                        None,
                        "prohibited_claim",
                        json!([]),
                        json!(hits),
                    );
                }
                Assertion::Context {
                    id,
                    observer,
                    query,
                    required,
                    forbidden,
                    error,
                } => {
                    let result = context_compiler::compile(
                        &current,
                        &CompileRequest {
                            version: 1,
                            scope: scope.clone(),
                            expected_head: current.revision(),
                            at_revision: None,
                            observer: observer.clone(),
                            role: Role::Character,
                            query: query.clone(),
                            referenced_ids: vec![],
                            budget: Budget::default(),
                        },
                    );
                    let actual_error = result.as_ref().err().map(|e| format!("{e:?}"));
                    check(
                        &mut out,
                        format!("{id}-error"),
                        None,
                        "retrieval",
                        json!(error),
                        json!(actual_error),
                    );
                    if let Ok(package) = result {
                        #[cfg(test)]
                        let package = {
                            let mut package = package;
                            if matches!(fault, Fault::DropCompiler) {
                                package
                                    .records
                                    .retain(|r| r.kind != context_compiler::Kind::Commitment);
                            }
                            package
                        };
                        let serialized = serde_json::to_string(&package).map_err(|_| "Encoding")?;
                        for (index, text) in forbidden.iter().enumerate() {
                            check(
                                &mut out,
                                format!("{id}-forbidden-{index}"),
                                None,
                                "observer",
                                json!(false),
                                json!(serialized.contains(text)),
                            );
                        }
                        for (index, target) in required.iter().enumerate() {
                            let found = package.records.iter().any(|record| {
                                let value = serde_json::to_value(record).unwrap();
                                value["kind"] == target.kind
                                    && value["sources"]
                                        .as_array()
                                        .is_some_and(|s| s.contains(&target.source))
                                    && value.to_string().contains(&target.contains)
                            });
                            let source_turn = target.source["value"]
                                .as_u64()
                                .and_then(|sequence| {
                                    current.receipts().iter().find(|r| {
                                        r.events().iter().any(|e| e.sequence() == sequence)
                                    })
                                })
                                .map(|r| r.request().turn.clone())
                                .or_else(|| {
                                    target.source["value"].as_str().map(|s| format!("seed:{s}"))
                                });
                            check(
                                &mut out,
                                format!("{id}-target-{index}"),
                                source_turn,
                                "retrieval",
                                json!({"present":true,"target":target}),
                                json!({"present":found,"target":target}),
                            );
                        }
                    }
                }
            }
        }
        for probe in &spec.probes {
            match probe {
                Probe::ReplayResume => {
                    let current = engine(&path, &scope)?;
                    let replay = Engine::replay(current.seed().clone(), current.receipts())
                        .map_err(|_| "Replay")?;
                    check(
                        &mut out,
                        "recorded-replay",
                        None,
                        "replay",
                        json!(digest(&current.canonical_bytes())),
                        json!(digest(&replay.canonical_bytes())),
                    );
                    host.close_all();
                    drop(host);
                    host = locallore_workspace::open(&path, true).map_err(|_| "Workspace")?;
                    let resumed = call(&host, json!({"op":"resume","scope":scope}));
                    session = resumed["data"]["session"].as_str().ok_or("Resume")?.into();
                    check(
                        &mut out,
                        "durable-resume",
                        None,
                        "persistence",
                        json!(current.revision()),
                        resumed["data"]["revision"].clone(),
                    );
                    check(
                        &mut out,
                        "durable-receipts",
                        None,
                        "replay",
                        json!(digest(&encode(current.receipts())?)),
                        json!(digest(&encode(engine(&path, &scope)?.receipts())?)),
                    );
                }
                Probe::Retry => {
                    if let Some((request, accepted, scripted)) = &last {
                        host.disable_local_provider();
                        let before = captures.lock().unwrap().len();
                        let retried = call(
                            &host,
                            if *scripted {
                                json!({"op":"free_text","session":session,"request":request})
                            } else {
                                json!({"op":"submit","session":session,"request":request,"mode":"accepted"})
                            },
                        );
                        check(
                            &mut out,
                            "exact-retry",
                            Some(request.turn.clone()),
                            "idempotency",
                            json!(digest(&encode(accepted)?)),
                            json!(digest(&encode(&retried)?)),
                        );
                        check(
                            &mut out,
                            "retry-no-inference",
                            Some(request.turn.clone()),
                            "idempotency",
                            json!(before),
                            json!(captures.lock().unwrap().len()),
                        );
                    } else {
                        check(
                            &mut out,
                            "retry-no-source",
                            None,
                            "idempotency",
                            json!(true),
                            json!(false),
                        );
                    }
                }
                Probe::Cancel | Probe::Stale => {
                    let before = engine(&path, &scope)?;
                    let turn = if matches!(probe, Probe::Cancel) {
                        "probe-cancel"
                    } else {
                        "probe-stale"
                    };
                    let request =
                        before.request(turn, Intent::Actions(vec![Command::Wait { ticks: 1 }]));
                    call(
                        &host,
                        json!({"op":"submit","session":session,"request":request,"mode":"accepted"}),
                    );
                    if matches!(probe, Probe::Cancel) {
                        let cancelled = op(&host, &session, &scope, turn, "cancel");
                        check(
                            &mut out,
                            "cancel",
                            Some(turn.into()),
                            "cancellation",
                            json!("cancelled"),
                            cancelled["data"]["phase"].clone(),
                        );
                        let rejected = op(&host, &session, &scope, turn, "commit");
                        check(
                            &mut out,
                            "cancel-terminal",
                            Some(turn.into()),
                            "cancellation",
                            json!("cancelled"),
                            rejected["data"]["phase"].clone(),
                        );
                        check(
                            &mut out,
                            "cancel-no-canon",
                            Some(turn.into()),
                            "canonical",
                            json!(digest(&before.canonical_bytes())),
                            json!(digest(&engine(&path, &scope)?.canonical_bytes())),
                        );
                    } else {
                        op(&host, &session, &scope, turn, "prepare");
                        let other =
                            locallore_workspace::open(&path, true).map_err(|_| "Workspace")?;
                        let resumed = call(&other, json!({"op":"resume","scope":scope}));
                        let sid = resumed["data"]["session"].as_str().ok_or("Resume")?;
                        let winner = before.request(
                            "probe-winner",
                            Intent::Actions(vec![Command::Wait { ticks: 1 }]),
                        );
                        call(
                            &other,
                            json!({"op":"submit","session":sid,"request":winner,"mode":"accepted"}),
                        );
                        op(&other, sid, &scope, "probe-winner", "prepare");
                        op(&other, sid, &scope, "probe-winner", "commit");
                        let stale = op(&host, &session, &scope, turn, "commit");
                        check(
                            &mut out,
                            "stale-loser",
                            Some(turn.into()),
                            "stale",
                            json!("stale"),
                            stale["data"]["phase"].clone(),
                        );
                        check(
                            &mut out,
                            "one-winner",
                            Some(turn.into()),
                            "canonical",
                            json!(before.revision() + 1),
                            json!(engine(&path, &scope)?.revision()),
                        );
                    }
                }
                Probe::StoryScope => {
                    let (sid, foreign) = create(&host)?;
                    let before = engine(&path, &foreign)?;
                    let wrong = call(
                        &host,
                        json!({"op":"open","session":session,"scope":foreign}),
                    );
                    check(
                        &mut out,
                        "scope-reject",
                        None,
                        "scope",
                        json!("Scope"),
                        wrong["error"].clone(),
                    );
                    check(
                        &mut out,
                        "foreign-no-canon",
                        None,
                        "scope",
                        json!(digest(&before.canonical_bytes())),
                        json!(digest(&engine(&path, &foreign)?.canonical_bytes())),
                    );
                    call(&host, json!({"op":"close","session":sid,"scope":foreign}));
                }
            }
        }
        host.close_all();
        out.provider_requests = captures.lock().unwrap().clone();
        Ok(())
    })();
    if let Err(error) = execution {
        check(
            &mut out,
            "runner-error",
            None,
            "runner",
            json!("completed_case"),
            json!(error),
        );
    }
    if out.checks.iter().any(|c| c.status == Status::Failed) {
        out.status = Status::Failed;
    }
    Ok(out)
}

fn ordinary(path: &Path) -> Result<()> {
    for ancestor in path.ancestors() {
        if let Ok(meta) = fs::symlink_metadata(ancestor) {
            #[cfg(windows)]
            {
                use std::os::windows::fs::MetadataExt;
                if meta.file_attributes() & 0x400 != 0 {
                    return Err("Reparse".into());
                }
            }
            if meta.file_type().is_symlink() {
                return Err("Reparse".into());
            }
        }
    }
    Ok(())
}
fn read(path: &Path, cap: usize) -> Result<Vec<u8>> {
    ordinary(path)?;
    let meta = fs::metadata(path).map_err(|_| "Io")?;
    if !meta.is_file() || meta.len() > cap as u64 {
        return Err("OutputBudget".into());
    }
    fs::read(path).map_err(|_| "Io".into())
}
fn write_new(path: &Path, bytes: &[u8]) -> Result<()> {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .map_err(|_| "OutputExists")?;
    file.write_all(bytes)
        .and_then(|_| file.sync_all())
        .map_err(|_| "Io".into())
}
fn escape(text: &str) -> String {
    text.replace('&', "&amp;")
        .replace('<', "&lt;")
        .replace('>', "&gt;")
        .replace('"', "&quot;")
        .replace('\'', "&#39;")
}
fn publish_reports(dir: &Path, report: &Report) -> Result<()> {
    if report.lane != "deterministic_fake_shared_host" {
        return local_lane::publish_local_report(dir, report);
    }
    let data = serde_json::to_vec_pretty(report).map_err(|_| "Encoding")?;
    if data.len() > MAX_REPORT {
        return Err("ReportBudget".into());
    }
    for (name,bytes) in [("report.json",data.clone()),("report.html",format!("<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'none'\"><title>Synthetic deterministic evaluation</title><h1>Synthetic deterministic evaluation</h1><p>No real model, Android parity or human quality acceptance.</p><pre>{}</pre>",escape(std::str::from_utf8(&data).map_err(|_|"Encoding")?)).into_bytes())]{if bytes.len()>MAX_REPORT{return Err("ReportBudget".into());}let path=dir.join(name);ordinary(&path)?;fs::write(path,bytes).map_err(|_|"Io")?;}
    Ok(())
}

/// Built-ins only. Completed immutable case envelopes are scenario-boundary checkpoints.
/// A crashed in-flight case is rerun in a new isolated directory, never its old DB.
pub fn run_builtin(
    directory: &Path,
    resume: bool,
    selected: Option<&str>,
    cancel: &Cancellation,
    max_scenarios: usize,
) -> Result<Report> {
    let suite = builtin()?;
    let basis = binding(&suite, selected)?;
    let binding_bytes = encode(&basis)?;
    let binding_sha = digest(&binding_bytes);
    ordinary(directory)?;
    if resume {
        if read(&directory.join("run.json"), 128 * 1024)? != binding_bytes {
            return Err("CheckpointMismatch".into());
        }
    } else {
        fs::create_dir(directory).map_err(|_| "OutputExists")?;
        write_new(&directory.join("run.json"), &binding_bytes)?;
    }
    ordinary(&directory.join("run.lock"))?;
    let lock = OpenOptions::new()
        .read(true)
        .write(true)
        .create(true)
        .truncate(false)
        .open(directory.join("run.lock"))
        .map_err(|_| "Io")?;
    lock.try_lock().map_err(|_| "RunBusy")?;
    let mut report = Report {
        version: VERSION,
        lane: "deterministic_fake_shared_host",
        synthetic: true,
        os: std::env::consts::OS,
        arch: std::env::consts::ARCH,
        hardware: None,
        model: None,
        runtime: None,
        quality_accepted: false,
        android_parity: "not_run",
        unsupported_lanes: vec![
            "real_model",
            "transcript_only_baseline",
            "semantic_quality",
            "human_review",
            "android_emulator",
            "physical_device",
            "offline_observation",
        ],
        provider_profiles: vec!["deterministic-fake-v1", "eval-scripted-fake-v1"],
        binding_sha256: binding_sha.clone(),
        provenance: serde_json::to_value(&basis).map_err(|_| "Encoding")?,
        completed: false,
        cancelled: false,
        cases: vec![],
    };
    let mut executed = 0;
    for (index, name) in basis.cases.iter().enumerate() {
        let destination = directory.join(format!("case-{index:02}.json"));
        if destination.exists() {
            let saved: Stored = serde_json::from_slice(&read(&destination, MAX_CASE)?)
                .map_err(|_| "CheckpointIntegrity")?;
            if saved.version != VERSION
                || saved.binding_sha256 != binding_sha
                || saved.result.id != *name
                || saved.result_sha256 != digest(&encode(&saved.result)?)
            {
                return Err("CheckpointIntegrity".into());
            }
            report.cases.push(saved.result);
            continue;
        }
        if cancel.is_cancelled() || executed >= max_scenarios {
            report.cancelled = cancel.is_cancelled();
            break;
        }
        let mut attempt = None;
        for n in 0..32 {
            let candidate = directory.join(format!("case-{index:02}-attempt-{n:02}"));
            match fs::create_dir(&candidate) {
                Ok(()) => {
                    attempt = Some(candidate);
                    break;
                }
                Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(_) => return Err("Io".into()),
            }
        }
        let attempt = attempt.ok_or("AttemptLimit")?;
        let spec = suite
            .scenarios
            .iter()
            .find(|s| s.id == *name)
            .ok_or("InvalidSuite")?;
        let result = match evaluate(spec, &attempt, Fault::None) {
            Ok(r) => r,
            Err(category) => CaseResult {
                id: name.clone(),
                status: Status::Failed,
                checks: vec![Check {
                    id: "runner-error".into(),
                    turn: None,
                    stage: "runner".into(),
                    status: Status::Failed,
                    expected: json!("completed_case"),
                    actual: json!(category),
                }],
                turns: vec![],
                provider_requests: vec![],
                unsupported: None,
            },
        };
        let saved = Stored {
            version: VERSION,
            binding_sha256: binding_sha.clone(),
            result_sha256: digest(&encode(&result)?),
            result: result.clone(),
        };
        let bytes = encode(&saved)?;
        if bytes.len() > MAX_CASE {
            return Err("CaseBudget".into());
        }
        let partial = attempt.join("completed.json");
        write_new(&partial, &bytes)?;
        fs::rename(&partial, &destination).map_err(|_| "Io")?;
        report.cases.push(result);
        executed += 1;
    }
    report.completed = report.cases.len() == basis.cases.len();
    publish_reports(directory, &report)?;
    drop(lock);
    Ok(report)
}

#[cfg(test)]
mod tests;
