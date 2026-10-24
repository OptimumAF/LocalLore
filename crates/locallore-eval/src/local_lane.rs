//! Opt-in curated synthetic stories over the existing durable Host and production Play path.
use super::*;
use crate::local_recording::{ForbiddenByRole, RawRef, Recording, RecordingProvider};
use std::{
    fs::File,
    path::PathBuf,
    sync::atomic::Ordering,
    time::{Duration, Instant},
};

pub const MAX_ADMISSIONS: usize = 32;
pub const MAX_ROLES: usize = 96;
pub const MAX_ACTIVE_MS: u64 = 30 * 60 * 1000;
const TURN_MS: u64 = 60_000;
const PREPARATION_MS: u64 = 120_000;
const CLEANUP_RESERVE_MS: u64 = 3_000;
const FIXTURES: &[u8] = include_bytes!("../fixtures/curated-local-v1.json");
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Corpus {
    version: u16,
    synthetic: bool,
    stories: Vec<Story>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Story {
    id: String,
    seed: Seed,
    setup_waits: u8,
    lineage: bool,
    steps: Vec<LocalStep>,
    context_assertions: Vec<ContextSpec>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct LocalStep {
    id: String,
    branch: String,
    kind: PlayInputKind,
    text: String,
    error: Option<String>,
    commands: Vec<Command>,
    narration: String,
    prohibited_narration: Vec<String>,
    cancel: bool,
    prompt_targets: Vec<Target>,
    assertions: Vec<StateCheck>,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct StateCheck {
    pointer: String,
    equals: Value,
}
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct ContextSpec {
    observer: String,
    query: String,
    required: Vec<Target>,
    forbidden: Vec<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct TurnEvidence {
    id: String,
    execution: String,
    roles: usize,
    role_metrics: Option<Value>,
    raw: Vec<RawRef>,
    fallback: Option<bool>,
    quality_candidate: bool,
    native_epoch: Option<usize>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct LocalMetadata {
    turns: Vec<TurnEvidence>,
    not_run: Vec<String>,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct LocalStored {
    version: u16,
    binding_sha256: String,
    result_sha256: String,
    attempt: u8,
    result: CaseResult,
    metadata: LocalMetadata,
}

/// Trusted native construction only; no renderer/provider/path/grant deserialization.
#[derive(Clone)]
pub enum LaneFactory {
    ScriptedBaseline,
    #[cfg(feature = "local-model")]
    Native {
        runtime: locallore_local_runtime::adapter::SharedRuntime,
        profile: PlayProfile,
    },
    #[cfg(test)]
    TestFault(TestFault),
}
#[cfg(test)]
#[derive(Clone, Copy, Debug)]
pub enum TestFault {
    WrongCommand,
    MalformedRepair,
    UnfaithfulNarrator,
    SecretNarrator,
    Pending,
    UnsupportedProse,
}
impl LaneFactory {
    fn native(&self) -> bool {
        match self {
            #[cfg(feature = "local-model")]
            Self::Native { .. } => true,
            _ => false,
        }
    }
    fn profile(&self) -> Result<PlayProfile> {
        #[cfg(feature = "local-model")]
        if let Self::Native { runtime, profile } = self {
            profile.validate().map_err(|_| "Profile")?;
            let runtime = runtime.try_lock().map_err(|_| "RuntimeBusy")?;
            if profile.id != locallore_local_runtime::PROFILE
                || profile.model_sha256 != locallore_local_runtime::MODEL_SHA256
                || profile.runtime_revision != locallore_local_runtime::RUNTIME_COMMIT
                || profile.worker_sha256 != runtime.worker_sha256()
                || profile.worker_sha256
                    != "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434"
                || profile.profile_manifest_sha256 != runtime.profile_manifest_sha256()
                || profile.template_sha256
                    != "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361"
                || profile.context_tokens != 4096
                || profile.director_tokens != 350
                || profile.narrator_tokens != 350
                || profile.deadline_ms != 120_000
                || profile.repair_limit != 1
            {
                return Err("Profile".into());
            }
            return Ok(profile.clone());
        }
        let mut p = profile();
        p.narrator_tokens = 350;
        p.deadline_ms = 120_000;
        Ok(p)
    }
    fn provider(
        &self,
        step: &LocalStep,
        state: Arc<Recording>,
        forbidden: ForbiddenByRole,
    ) -> Box<dyn InferenceProvider + Send> {
        #[cfg(feature = "local-model")]
        if let Self::Native { runtime, .. } = self {
            let log = locallore_local_runtime::RoleMetricsLog::new();
            let inner = locallore_local_runtime::adapter::RuntimeProvider::with_resource_metrics(
                runtime.clone(),
                log.clone(),
            );
            return Box::new(
                RecordingProvider::new(
                    Box::new(inner),
                    state,
                    step.prompt_targets.clone(),
                    forbidden,
                )
                .with_native_log(log),
            );
        }
        let plan = ScriptPlan {
            commands: step.commands.clone(),
            narration: step.narration.clone(),
            prompt_targets: step.prompt_targets.clone(),
        };
        let script = Script {
            plan,
            captures: Arc::new(Mutex::new(vec![])),
            #[cfg(test)]
            drop_forwarded: false,
        };
        let inner: Box<dyn InferenceProvider + Send> = if step.cancel {
            Box::new(PendingFixture)
        } else {
            Box::new(script)
        };
        #[cfg(test)]
        let inner: Box<dyn InferenceProvider + Send> = if let Self::TestFault(fault) = self {
            Box::new(FaultProvider {
                inner,
                fault: *fault,
                directors: 0,
            })
        } else {
            inner
        };
        Box::new(RecordingProvider::new(
            inner,
            state,
            step.prompt_targets.clone(),
            forbidden,
        ))
    }
}
struct DeadlineGuard {
    stop: std::sync::mpsc::SyncSender<()>,
    worker: Option<std::thread::JoinHandle<()>>,
}
impl DeadlineGuard {
    fn finish(mut self) -> Result<()> {
        let _ = self.stop.try_send(());
        if let Some(worker) = self.worker.take() {
            worker.join().map_err(|_| "Watchdog")?;
        }
        Ok(())
    }
}
impl Drop for DeadlineGuard {
    fn drop(&mut self) {
        let _ = self.stop.try_send(());
        if let Some(worker) = self.worker.take() {
            let _ = worker.join();
        }
    }
}
#[cfg(test)]
static PENDING_POLLED: std::sync::atomic::AtomicBool = std::sync::atomic::AtomicBool::new(false);
struct PendingFixture;
impl InferenceProvider for PendingFixture {
    fn poll(
        &mut self,
        _: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            Poll::Ready(Err(Error::Cancelled))
        } else {
            Poll::Pending
        }
    }
}
#[cfg(test)]
struct FaultProvider {
    inner: Box<dyn InferenceProvider + Send>,
    fault: TestFault,
    directors: u8,
}
#[cfg(test)]
impl InferenceProvider for FaultProvider {
    fn poll(
        &mut self,
        r: &GenerationRequest,
        c: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, Error>> {
        let Input::Structured { role, schema, .. } = &r.input else {
            return Poll::Ready(Err(Error::Provider));
        };
        if matches!(self.fault, TestFault::Pending) {
            PENDING_POLLED.store(true, Ordering::Release);
            return PendingFixture.poll(r, c);
        }
        if role == "director" {
            self.directors += 1;
            match self.fault {
                TestFault::WrongCommand => {
                    return Poll::Ready(Ok(br#"{"commands":[{"op":"wait","ticks":1}]}"#.to_vec()))
                }
                TestFault::MalformedRepair if self.directors == 1 => {
                    return Poll::Ready(Ok(b"{".to_vec()))
                }
                _ => {}
            }
        }
        if role == "narrator"
            && matches!(
                self.fault,
                TestFault::UnfaithfulNarrator
                    | TestFault::SecretNarrator
                    | TestFault::UnsupportedProse
            )
        {
            let text = if matches!(self.fault, TestFault::SecretNarrator) {
                "SECRET-TIDE-731"
            } else if matches!(self.fault, TestFault::UnsupportedProse) {
                "You gain the blink ability and infinite energy."
            } else {
                "You gain a new power and infinite energy."
            };
            return Poll::Ready(Ok(serde_json::to_vec(&json!({"text":text,"speaker":"narrator","event_ids":schema["properties"]["event_ids"]["const"]})).unwrap()));
        }
        self.inner.poll(r, c)
    }
}
fn corpus() -> Result<Corpus> {
    if FIXTURES.len() > 128 * 1024 {
        return Err("SuiteBudget".into());
    }
    let corpus: Corpus = serde_json::from_slice(FIXTURES).map_err(|_| "InvalidSuite")?;
    if corpus.version != 1 || !corpus.synthetic || corpus.stories.len() != 6 {
        return Err("InvalidSuite".into());
    }
    let mut names = BTreeSet::new();
    for s in &corpus.stories {
        if !id(&s.id)
            || !names.insert(s.id.clone())
            || s.steps.len() != 4
            || s.setup_waits > 32
            || s.context_assertions.len() > 8
        {
            return Err("InvalidSuite".into());
        }
        Engine::new(s.seed.clone()).map_err(|_| "InvalidSeed")?;
        let mut turns = BTreeSet::new();
        for t in &s.steps {
            if !id(&t.id)
                || !turns.insert(&t.id)
                || !matches!(t.branch.as_str(), "main" | "child")
                || t.text.is_empty()
                || t.text.len() > 2048
                || t.commands.len() > 1
                || t.narration.len() > 1024
                || t.assertions.len() > 16
                || t.prompt_targets.len() > 8
                || t.prohibited_narration.len() > 8
                || t.prohibited_narration
                    .iter()
                    .any(|s| s.is_empty() || s.len() > 128)
                || t.error.as_ref().is_some_and(|e| e.len() > 48)
            {
                return Err("InvalidStep".into());
            }
        }
    }
    Ok(corpus)
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Reservation {
    version: u16,
    binding: String,
    index: usize,
    story: String,
    turn: String,
    ms: u64,
    roles: usize,
}
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
struct Settlement {
    version: u16,
    binding: String,
    index: usize,
    ms: u64,
    roles: usize,
}
struct Ledger {
    directory: PathBuf,
    binding: String,
    admissions: usize,
    invocations: usize,
    charged_ms: u64,
    charged_roles: usize,
    prior_ms: u64,
    started: Instant,
    turn_ms: u64,
    invocation: usize,
    // Comparison-only measured exclusions. Zero preserves the legacy clock exactly.
    excluded_ms: u64,
    shared_setup: Option<(u64, u64)>,
}
fn shared_setup_shares(ms: u64) -> (u64, u64) {
    (ms / 2 + ms % 2, ms / 2)
}
impl Ledger {
    fn load(directory: &Path, binding: &str) -> Result<Self> {
        let mut ledger = Self {
            directory: directory.into(),
            binding: binding.into(),
            admissions: 0,
            invocations: 0,
            charged_ms: 0,
            charged_roles: 0,
            prior_ms: 0,
            started: Instant::now(),
            turn_ms: 0,
            invocation: 0,
            excluded_ms: 0,
            shared_setup: None,
        };
        for (prefix, cap) in [("invocation", 32), ("admission", MAX_ADMISSIONS)] {
            let mut gap = false;
            for index in 0..cap {
                let path = directory.join(format!("{prefix}-{index:02}.json"));
                if !path.exists() {
                    if directory
                        .join(format!("{prefix}-{index:02}-settled.json"))
                        .exists()
                    {
                        return Err("LedgerIntegrity".into());
                    }
                    gap = true;
                    continue;
                }
                if gap {
                    return Err("LedgerIntegrity".into());
                }
                let r: Reservation =
                    serde_json::from_slice(&read(&path, 4096)?).map_err(|_| "LedgerIntegrity")?;
                let setup = prefix == "invocation";
                if r.version != 1
                    || r.binding != binding
                    || r.index != index
                    || r.ms != if setup { PREPARATION_MS } else { TURN_MS }
                    || r.roles != if setup { 0 } else { 3 }
                    || !id(&r.story)
                    || !id(&r.turn)
                {
                    return Err("LedgerIntegrity".into());
                }
                let settled = directory.join(format!("{prefix}-{index:02}-settled.json"));
                let (ms, roles) = if settled.exists() {
                    let s: Settlement = serde_json::from_slice(&read(&settled, 4096)?)
                        .map_err(|_| "LedgerIntegrity")?;
                    if s.version != 1
                        || s.binding != binding
                        || s.index != index
                        || s.roles > r.roles
                    {
                        return Err("LedgerIntegrity".into());
                    }
                    (s.ms, s.roles)
                } else {
                    (r.ms, r.roles)
                };
                ledger.charged_ms = ledger.charged_ms.checked_add(ms).ok_or("LedgerIntegrity")?;
                ledger.charged_roles += roles;
                if setup {
                    ledger.invocations += 1;
                } else {
                    ledger.admissions += 1;
                }
            }
        }
        ledger.prior_ms = ledger.charged_ms;
        Ok(ledger)
    }
    fn begin_invocation(&mut self) -> Result<()> {
        if self.invocations >= 32 || self.charged_ms.saturating_add(PREPARATION_MS) > MAX_ACTIVE_MS
        {
            return Err("RunBudget".into());
        }
        self.invocation = self.invocations;
        self.invocations += 1;
        self.reserve_file(
            "invocation",
            self.invocation,
            "preparation",
            "preparation",
            PREPARATION_MS,
            0,
        )?;
        self.charged_ms += PREPARATION_MS;
        Ok(())
    }
    fn reserve_file(
        &self,
        prefix: &str,
        index: usize,
        story: &str,
        turn: &str,
        ms: u64,
        roles: usize,
    ) -> Result<()> {
        write_new(
            &self.directory.join(format!("{prefix}-{index:02}.json")),
            &encode(&Reservation {
                version: 1,
                binding: self.binding.clone(),
                index,
                story: story.into(),
                turn: turn.into(),
                ms,
                roles,
            })?,
        )
    }
    fn active_elapsed(&self, wall_ms: u64) -> u64 {
        let elapsed = wall_ms.saturating_sub(self.excluded_ms);
        match self.shared_setup {
            Some((physical, share)) => elapsed.saturating_sub(physical).saturating_add(share),
            None => elapsed,
        }
    }
    fn exclude_measured_interval(&mut self, ms: u64) -> Result<()> {
        self.excluded_ms = self.excluded_ms.checked_add(ms).ok_or("ClockIntegrity")?;
        Ok(())
    }
    fn record_shared_setup(&mut self, physical: u64, share: u64) -> Result<()> {
        if self.shared_setup.is_some() || physical > PREPARATION_MS || share > physical {
            return Err("ClockIntegrity".into());
        }
        self.shared_setup = Some((physical, share));
        Ok(())
    }
    fn elapsed(&self) -> u64 {
        self.active_elapsed(self.started.elapsed().as_millis().min(u64::MAX as u128) as u64)
    }
    fn remaining(&self) -> u64 {
        MAX_ACTIVE_MS.saturating_sub(
            self.charged_ms
                .max(self.prior_ms.saturating_add(self.elapsed())),
        )
    }
    fn admit(&mut self, story: &str, turn: &str) -> Result<usize> {
        if self.admissions >= MAX_ADMISSIONS
            || self.charged_roles + 3 > MAX_ROLES
            || self.remaining() < TURN_MS + CLEANUP_RESERVE_MS
        {
            return Err("RunBudget".into());
        }
        let index = self.admissions;
        self.reserve_file("admission", index, story, turn, TURN_MS, 3)?;
        self.admissions += 1;
        self.charged_ms += TURN_MS;
        self.charged_roles += 3;
        Ok(index)
    }
    fn settle(&mut self, index: usize, ms: u64, roles: usize) -> Result<()> {
        if roles > 3 {
            return Err("RoleBudget".into());
        }
        write_new(
            &self
                .directory
                .join(format!("admission-{index:02}-settled.json")),
            &encode(&Settlement {
                version: 1,
                binding: self.binding.clone(),
                index,
                ms,
                roles,
            })?,
        )?;
        self.charged_ms = self
            .charged_ms
            .checked_sub(TURN_MS)
            .ok_or("LedgerIntegrity")?
            .checked_add(ms)
            .ok_or("LedgerIntegrity")?;
        self.charged_roles = self.charged_roles - 3 + roles;
        self.turn_ms = self.turn_ms.checked_add(ms).ok_or("LedgerIntegrity")?;
        Ok(())
    }
    fn finish(&mut self) -> Result<()> {
        let overhead = self.elapsed().saturating_sub(self.turn_ms);
        write_new(
            &self
                .directory
                .join(format!("invocation-{:02}-settled.json", self.invocation)),
            &encode(&Settlement {
                version: 1,
                binding: self.binding.clone(),
                index: self.invocation,
                ms: overhead,
                roles: 0,
            })?,
        )?;
        self.charged_ms = self
            .charged_ms
            .checked_sub(PREPARATION_MS)
            .ok_or("LedgerIntegrity")?
            .checked_add(overhead)
            .ok_or("LedgerIntegrity")?;
        Ok(())
    }
}
fn typed_setup(store: &mut Store, scope: &Scope, turn: &str, commands: Vec<Command>) -> Result<()> {
    let engine = store.resume(scope).map_err(|_| "SetupReplay")?.engine;
    let request = engine.request(turn, Intent::Actions(commands));
    let proposal = Engine::proposal(&request).map_err(|_| "SetupProposal")?;
    let candidate = engine
        .preview(&request, &proposal)
        .map_err(|_| "SetupValidation")?;
    store.begin_turn(&request).map_err(|_| "SetupBegin")?;
    store
        .commit_turn(&request, &proposal, candidate.narration())
        .map_err(|_| "SetupCommit")?;
    Ok(())
}
fn setup_story(story: &Story, path: &Path) -> Result<Scope> {
    let mut store = Store::open(path, None).map_err(|_| "Workspace")?;
    store
        .create_story("Curated synthetic evaluation", story.seed.clone())
        .map_err(|_| "Seed")?;
    let scope = story.seed.scope.clone();
    let mut foreign = story.seed.clone();
    foreign.scope.story = format!("foreign-{}", story.id);
    foreign.facts.get_mut("relic-location").unwrap().proposition =
        format!("FOREIGN-ONLY-{}", story.id);
    store
        .create_story("Foreign synthetic isolation", foreign)
        .map_err(|_| "Seed")?;
    for i in 0..story.setup_waits {
        typed_setup(
            &mut store,
            &scope,
            &format!("setup-wait-{i}"),
            vec![Command::Wait { ticks: 1 }],
        )?;
    }
    if story.lineage {
        typed_setup(
            &mut store,
            &scope,
            "setup-root",
            vec![Command::Say {
                text: "ROOT-VISIBLE-BELL".into(),
                audience: ["mira".into()].into(),
            }],
        )?;
        for child in ["child", "sibling"] {
            store
                .fork_branch(
                    &locallore_storage::ForkRequest {
                        parent: scope.clone(),
                        child_branch: child.into(),
                        expected_parent_revision: 1,
                        at_revision: 1,
                    },
                    &|| false,
                )
                .map_err(|_| "Fork")?;
        }
        typed_setup(
            &mut store,
            &scope,
            "setup-parent-future",
            vec![Command::Say {
                text: "PARENT-FUTURE-MIST".into(),
                audience: ["mira".into()].into(),
            }],
        )?;
        typed_setup(
            &mut store,
            &Scope {
                story: scope.story.clone(),
                branch: "sibling".into(),
            },
            "setup-sibling",
            vec![Command::Say {
                text: "SIBLING-ONLY-SALT".into(),
                audience: ["mira".into()].into(),
            }],
        )?;
    }
    Ok(scope)
}
fn resume_session(host: &Host, scope: &Scope) -> Result<String> {
    call(host, json!({"op":"resume","scope":scope}))["data"]["session"]
        .as_str()
        .map(str::to_owned)
        .ok_or("Resume".into())
}
fn empty_case(id: &str) -> CaseResult {
    CaseResult {
        id: id.into(),
        status: Status::Passed,
        checks: vec![],
        turns: vec![],
        provider_requests: vec![],
        unsupported: None,
    }
}
fn context_checks(out: &mut CaseResult, current: &Engine, spec: &ContextSpec) {
    let compiled = context_compiler::compile(
        current,
        &CompileRequest {
            version: 1,
            scope: current.scope().clone(),
            expected_head: current.revision(),
            at_revision: None,
            observer: spec.observer.clone(),
            role: Role::Character,
            query: spec.query.clone(),
            referenced_ids: vec![],
            budget: Budget::default(),
        },
    );
    check(
        out,
        format!("{}-context", spec.observer),
        None,
        "retrieval",
        json!(true),
        json!(compiled.is_ok()),
    );
    if let Ok(package) = compiled {
        let value = serde_json::to_value(&package).unwrap();
        let encoded = value.to_string();
        for (i, forbidden) in spec.forbidden.iter().enumerate() {
            check(
                out,
                format!("{}-hidden-{i}", spec.observer),
                None,
                "observer",
                json!(false),
                json!(encoded.contains(forbidden)),
            );
        }
        for (i, target) in spec.required.iter().enumerate() {
            let found = package.records.iter().any(|r| {
                let v = serde_json::to_value(r).unwrap();
                v["kind"] == target.kind
                    && v["sources"]
                        .as_array()
                        .is_some_and(|s| s.contains(&target.source))
                    && v.to_string().contains(&target.contains)
            });
            check(
                out,
                format!("{}-source-{i}", spec.observer),
                None,
                "retrieval",
                json!(true),
                json!(found),
            );
        }
    }
}
fn forbidden_by_role(story: &Story, step: &LocalStep) -> ForbiddenByRole {
    let mut director = vec![format!("FOREIGN-ONLY-{}", story.id)];
    if story.lineage && step.branch == "child" {
        director.extend(["PARENT-FUTURE-MIST".into(), "SIBLING-ONLY-SALT".into()]);
    }
    let mut narrator = director.clone();
    narrator.push("SECRET-TIDE-731".into());
    ForbiddenByRole { director, narrator }
}
fn run_story(
    story: &Story,
    directory: &Path,
    factory: &LaneFactory,
    cancel: &Cancellation,
    ledger: &mut Ledger,
) -> Result<(CaseResult, LocalMetadata)> {
    let path = directory.join("synthetic.sqlite");
    let root = setup_story(story, &path)?;
    let host = Arc::new(locallore_workspace::open(&path, true).map_err(|_| "Workspace")?);
    let mut out = empty_case(&story.id);
    let mut metadata = LocalMetadata {
        turns: vec![],
        not_run: vec![],
    };
    let mut last: Option<(Request, Value)> = None;
    let mut failed = false;
    let mut raw_index = 0;
    for step in &story.steps {
        if failed {
            metadata.not_run.push(step.id.clone());
            continue;
        }
        if cancel.is_cancelled() {
            host.close_all();
            return Err("Interrupted".into());
        }
        let admission = ledger.admit(&story.id, &step.id)?;
        let started = Instant::now();
        let scope = Scope {
            story: root.story.clone(),
            branch: step.branch.clone(),
        };
        let session = resume_session(&host, &scope)?;
        let before = engine(&path, &scope)?;
        let other_scope = if story.lineage {
            Some(Scope {
                story: root.story.clone(),
                branch: if step.branch == "child" {
                    "main"
                } else {
                    "child"
                }
                .into(),
            })
        } else {
            None
        };
        let other_before = other_scope
            .as_ref()
            .map(|scope| engine(&path, scope).map(|e| digest(&e.canonical_bytes())))
            .transpose()?;
        let request = before.request(
            &step.id,
            Intent::FreeText {
                kind: step.kind,
                text: step.text.clone(),
            },
        );
        let records = Arc::new(Recording::default());
        let make = factory.clone();
        let spec = step.clone();
        let capture = records.clone();
        let forbidden = forbidden_by_role(story, step);
        let provider = Arc::new(move || make.provider(&spec, capture.clone(), forbidden.clone()));
        let profile = factory.profile()?;
        if factory.native() {
            host.configure_local_provider(profile, provider)
        } else {
            host.configure_fixture_provider(profile, provider)
        }
        .map_err(|_| "Profile")?;
        let mut reply = call(
            &host,
            json!({"op":"free_text","session":session,"request":request}),
        );
        let (stop, stopped) = std::sync::mpsc::sync_channel(1);
        let watch_host = host.clone();
        let sid = session.clone();
        let watch_scope = scope.clone();
        let turn = step.id.clone();
        let external = cancel.clone();
        let watch_records = records.clone();
        let intentional = step.cancel;
        let active_remaining = MAX_ACTIVE_MS.saturating_sub(
            ledger
                .charged_ms
                .saturating_sub(TURN_MS)
                .max(ledger.prior_ms.saturating_add(ledger.elapsed())),
        );
        let limit = TURN_MS.min(active_remaining.saturating_sub(CLEANUP_RESERVE_MS));
        let watchdog = std::thread::Builder::new()
            .name("locallore-eval-deadline".into())
            .spawn(move || {
                let began = Instant::now();
                loop {
                    match stopped.recv_timeout(Duration::from_millis(5)) {
                        Ok(()) | Err(std::sync::mpsc::RecvTimeoutError::Disconnected) => break,
                        Err(std::sync::mpsc::RecvTimeoutError::Timeout) => {}
                    }
                    if external.is_cancelled()
                        || began.elapsed() >= Duration::from_millis(limit)
                        || (intentional
                            && watch_records.polled.load(Ordering::Acquire)
                            && began.elapsed() >= Duration::from_millis(25))
                    {
                        op(&watch_host, &sid, &watch_scope, &turn, "cancel");
                        break;
                    }
                }
            })
            .map_err(|_| "Watchdog")?;
        let watchdog = DeadlineGuard {
            stop,
            worker: Some(watchdog),
        };
        if reply["data"]["phase"] == "queued" {
            reply = op(&host, &session, &scope, &step.id, "prepare");
        }
        watchdog.finish()?;
        if cancel.is_cancelled() || started.elapsed() >= Duration::from_millis(limit) {
            reply = op(&host, &session, &scope, &step.id, "cancel");
        }
        if reply["data"]["phase"] == "ready" {
            reply = op(&host, &session, &scope, &step.id, "commit");
        }
        let after = engine(&path, &scope)?;
        let phase = if reply["status"] == "rejected" {
            json!("rejected")
        } else {
            reply["data"]["phase"].clone()
        };
        let error = if reply["status"] == "rejected" {
            reply["error"].clone()
        } else {
            reply["data"]["error"].clone()
        };
        let roles = records.roles.load(Ordering::Relaxed);
        let elapsed = started.elapsed().as_millis().min(u64::MAX as u128) as u64;
        ledger.settle(admission, elapsed, roles)?;
        if cancel.is_cancelled() {
            host.close_all();
            return Err("Interrupted".into());
        }
        let expected_phase = if step.cancel {
            "cancelled"
        } else if step.error.is_some() {
            "failed"
        } else {
            "committed"
        };
        check(
            &mut out,
            format!("{}-phase", step.id),
            Some(step.id.clone()),
            "pipeline",
            json!(expected_phase),
            phase.clone(),
        );
        // A cancelled terminal uses phase as authority; Host may leave the optional error null.
        if !step.cancel {
            check(
                &mut out,
                format!("{}-error", step.id),
                Some(step.id.clone()),
                "pipeline",
                json!(step.error),
                error.clone(),
            );
        }
        if step.error.is_some() {
            check(
                &mut out,
                format!("{}-atomic", step.id),
                Some(step.id.clone()),
                "canonical",
                json!(digest(&before.canonical_bytes())),
                json!(digest(&after.canonical_bytes())),
            );
        } else {
            check(
                &mut out,
                format!("{}-revision", step.id),
                Some(step.id.clone()),
                "canonical",
                json!(before.revision() + 1),
                json!(after.revision()),
            );
            let proposal = reply["data"]["receipt"]["proposal"]["commands"].clone();
            check(
                &mut out,
                format!("{}-command", step.id),
                Some(step.id.clone()),
                "agency",
                json!(step.commands),
                proposal,
            );
        }
        if phase == "committed" {
            check(
                &mut out,
                format!("{}-original-request", step.id),
                Some(step.id.clone()),
                "provenance",
                json!(request),
                reply["data"]["receipt"]["request"].clone(),
            );
            check(
                &mut out,
                format!("{}-profile", step.id),
                Some(step.id.clone()),
                "provenance",
                json!(factory.profile()?),
                reply["data"]["receipt"]["play"]["profile"].clone(),
            );
        }
        let state = serde_json::to_value(after.state()).map_err(|_| "Encoding")?;
        for (i, assertion) in step.assertions.iter().enumerate() {
            check(
                &mut out,
                format!("{}-state-{i}", step.id),
                Some(step.id.clone()),
                "canonical",
                assertion.equals.clone(),
                state
                    .pointer(&assertion.pointer)
                    .cloned()
                    .unwrap_or(json!({"missing":true})),
            );
        }
        if let (Some(other), Some(expected)) = (&other_scope, &other_before) {
            check(
                &mut out,
                format!("{}-other-branch", step.id),
                Some(step.id.clone()),
                "scope",
                json!(expected),
                json!(digest(&engine(&path, other)?.canonical_bytes())),
            );
        }
        let data = records.state.lock().map_err(|_| "Recording")?;
        let mut raw = vec![];
        for (role, bytes) in &data.outputs {
            let file = format!("raw-{raw_index:02}.json");
            raw_index += 1;
            write_new(&directory.join(&file), bytes)?;
            raw.push(RawRef {
                file,
                sha256: digest(bytes),
                bytes: bytes.len(),
                role: role.clone(),
            });
        }
        out.provider_requests.extend(data.captures.clone());
        check(
            &mut out,
            format!("{}-capture", step.id),
            Some(step.id.clone()),
            "provenance",
            json!(false),
            json!(records.lost.load(Ordering::Relaxed)),
        );
        for c in &data.captures {
            if c.role == "director" {
                check(
                    &mut out,
                    format!("{}-compiler-version", step.id),
                    Some(step.id.clone()),
                    "retrieval",
                    json!(Some(locallore::context_compiler::POLICY_COMPILER_VERSION)),
                    json!(c.compiler_version),
                );
                check(
                    &mut out,
                    format!("{}-input", step.id),
                    Some(step.id.clone()),
                    "agency",
                    json!(Some(digest(step.text.as_bytes()))),
                    json!(c.player_text_sha256),
                );
                check(
                    &mut out,
                    format!("{}-targets", step.id),
                    Some(step.id.clone()),
                    "retrieval",
                    json!(vec![true; step.prompt_targets.len()]),
                    json!(c.prompt_targets_present),
                );
            }
        }
        if data
            .captures
            .iter()
            .any(|capture| capture.role == "director")
        {
            check(
                &mut out,
                format!("{}-director-context", step.id),
                Some(step.id.clone()),
                "observer",
                json!(false),
                json!(data.forbidden_director_prompt),
            );
        }
        check(
            &mut out,
            format!("{}-narrator-context", step.id),
            Some(step.id.clone()),
            "observer",
            json!(false),
            json!(data.forbidden_narrator_prompt),
        );
        check(
            &mut out,
            format!("{}-candidate-canary", step.id),
            Some(step.id.clone()),
            "prohibited_claim",
            json!(false),
            json!(data.forbidden_narrator_output),
        );
        if step.error.is_some() && !step.cancel {
            check(
                &mut out,
                format!("{}-guard-no-model", step.id),
                Some(step.id.clone()),
                "guard",
                json!(0),
                json!(roles),
            );
        }
        let narration = reply["data"]["receipt"]["narration"]
            .as_str()
            .map(str::to_owned);
        let fallback = reply["data"]["receipt"]["play"]["fallback"].as_bool();
        if let Some(text) = &narration {
            for (n, forbidden) in step.prohibited_narration.iter().enumerate() {
                check(
                    &mut out,
                    format!("{}-prohibited-{n}", step.id),
                    Some(step.id.clone()),
                    "prohibited_claim",
                    json!(false),
                    json!(text.to_lowercase().contains(&forbidden.to_lowercase())),
                );
            }
        }
        if narration.as_ref().is_some_and(|s| s.len() > 4096) {
            return Err("CaseBudget".into());
        }
        let execution = if step.cancel {
            "cancelled"
        } else if roles == 0 && step.error.is_some() {
            "guard_only"
        } else if phase == "committed" {
            "inference_completed"
        } else {
            "inference_failed"
        };
        metadata.turns.push(TurnEvidence {
            id: step.id.clone(),
            execution: execution.into(),
            roles,
            role_metrics: data.role_metrics.clone(),
            raw,
            fallback,
            quality_candidate: factory.native() && phase == "committed" && fallback == Some(false),
            native_epoch: factory.native().then_some(ledger.invocation),
        });
        drop(data);
        out.turns.push(Turn {
            id: step.id.clone(),
            intent: request.intent.clone(),
            phase: phase.clone(),
            error,
            revision: after.revision(),
            canonical_sha256: digest(&after.canonical_bytes()),
            narration,
            fallback,
            repairs: reply["data"]["receipt"]["play"]["repairs"].as_u64(),
        });
        if phase == "committed" {
            last = Some((request, reply));
        }
        failed = out.checks.iter().any(|c| c.status == Status::Failed);
    }
    let current_scope = if story.lineage {
        Scope {
            story: root.story.clone(),
            branch: "child".into(),
        }
    } else {
        root.clone()
    };
    let current = engine(&path, &current_scope)?;
    if !failed {
        for spec in &story.context_assertions {
            context_checks(&mut out, &current, spec);
        }
    }
    // Same Store replay/resume/cache paths, without any provider after original completion.
    if let Some((request, accepted)) = last {
        host.disable_local_provider();
        host.close_all();
        drop(host);
        let reopened = locallore_workspace::open(&path, true).map_err(|_| "Workspace")?;
        let session = resume_session(&reopened, &request.scope)?;
        let resumed = engine(&path, &current_scope)?;
        check(
            &mut out,
            "reopen-canonical",
            None,
            "replay",
            json!(digest(&current.canonical_bytes())),
            json!(digest(&resumed.canonical_bytes())),
        );
        check(
            &mut out,
            "reopen-receipts",
            None,
            "replay",
            json!(digest(&encode(current.receipts())?)),
            json!(digest(&encode(resumed.receipts())?)),
        );
        let retried = call(
            &reopened,
            json!({"op":"free_text","session":session,"request":request}),
        );
        check(
            &mut out,
            "exact-retry-without-provider",
            Some(request.turn.clone()),
            "idempotency",
            json!(digest(&encode(&accepted)?)),
            json!(digest(&encode(&retried)?)),
        );
        let foreign = Scope {
            story: format!("foreign-{}", story.id),
            branch: "main".into(),
        };
        let before = engine(&path, &foreign)?;
        let wrong = call(
            &reopened,
            json!({"op":"open","session":session,"scope":foreign}),
        );
        check(
            &mut out,
            "foreign-session-refusal",
            None,
            "scope",
            json!("Scope"),
            wrong["error"].clone(),
        );
        check(
            &mut out,
            "foreign-canon-unchanged",
            None,
            "scope",
            json!(digest(&before.canonical_bytes())),
            json!(digest(&engine(&path, &foreign)?.canonical_bytes())),
        );
        reopened.close_all();
    } else {
        host.close_all();
    }
    if out.checks.iter().any(|c| c.status == Status::Failed) {
        out.status = Status::Failed;
    }
    Ok((out, metadata))
}
fn curated_basis(
    stories: &[Story],
    profile: PlayProfile,
    native: bool,
    preowned: bool,
) -> Result<Value> {
    let seed_hashes: BTreeMap<_, _> = stories
        .iter()
        .map(|s| Ok((s.id.clone(), digest(&encode(&s.seed)?))))
        .collect::<Result<_>>()?;
    let basis = json!({"version":1,"suite":"curated-local-v1","suite_sha256":digest(FIXTURES),"seed_sha256":seed_hashes,"selected_stories":stories.iter().map(|s|&s.id).collect::<Vec<_>>(),"profile":profile,"native":native,"preowned_runtime":preowned,"source":binding(&builtin()?,None)?,"limits":{"admissions":MAX_ADMISSIONS,"roles":MAX_ROLES,"active_ms":MAX_ACTIVE_MS,"turn_ms":TURN_MS,"preparation_reservation_ms":PREPARATION_MS,"raw_role_bytes":16384,"repair_limit":1}});
    Ok(basis)
}

fn coverage(
    metadata: &[LocalMetadata],
    selected_stories: usize,
    checkpointed_stories: usize,
) -> Value {
    let evidence: Vec<_> = metadata.iter().flat_map(|m| &m.turns).collect();
    let count = |class: &str| evidence.iter().filter(|e| e.execution == class).count();
    let coverage = json!({"selected_stories":selected_stories,"declared_turn_cases":selected_stories*4,"checkpointed_stories":checkpointed_stories,"executed_turn_cases":evidence.len(),"inference_completed":count("inference_completed"),"inference_failed":count("inference_failed"),"guard_only":count("guard_only"),"cancelled":count("cancelled"),"not_run":metadata.iter().map(|m|m.not_run.len()).sum::<usize>(),"quality_candidates":evidence.iter().filter(|e|e.quality_candidate).count(),"fallbacks":evidence.iter().filter(|e|e.fallback==Some(true)).count()});
    coverage
}

struct Session {
    directory: PathBuf,
    _lock: File,
    binding: String,
    stories: Vec<Story>,
    ledger: Ledger,
    report: Report,
    metadata: Vec<LocalMetadata>,
}
impl Session {
    fn open(
        directory: &Path,
        resume: bool,
        selected: Option<&str>,
        native: bool,
        profile: PlayProfile,
        preowned: bool,
    ) -> Result<Self> {
        let corpus = corpus()?;
        if selected.is_some_and(|id| !corpus.stories.iter().any(|s| s.id == id)) {
            return Err("UnknownCase".into());
        }
        let stories: Vec<_> = corpus
            .stories
            .into_iter()
            .filter(|s| selected.is_none_or(|id| s.id == id))
            .collect();
        let basis = curated_basis(&stories, profile.clone(), native, preowned)?;
        let bytes = encode(&basis)?;
        if bytes.len() > 128 * 1024 {
            return Err("BindingBudget".into());
        }
        let binding = digest(&bytes);
        ordinary(directory)?;
        if !resume {
            fs::create_dir(directory).map_err(|_| "OutputExists")?;
            write_new(&directory.join("run.json"), &bytes)?;
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
        if read(&directory.join("run.json"), 128 * 1024)? != bytes {
            return Err("CheckpointMismatch".into());
        }
        let mut ledger = Ledger::load(directory, &binding)?;
        ledger.begin_invocation()?;
        let report = Report {
            version: VERSION,
            lane: if native {
                "native_curated_shared_host"
            } else {
                "scripted_curated_shared_host"
            },
            synthetic: true,
            os: std::env::consts::OS,
            arch: std::env::consts::ARCH,
            hardware: None,
            model: native.then(|| profile.model_sha256.clone()),
            runtime: native.then(|| profile.runtime_revision.clone()),
            quality_accepted: false,
            android_parity: "not_run",
            unsupported_lanes: vec![
                "human_quality_acceptance",
                "npc_voice_distinctiveness",
                "transcript_only_baseline",
                "derived_summary_fts_generation",
                "android_emulator",
                "physical_device",
                "offline_observation",
            ],
            provider_profiles: if native {
                vec!["qwen3-0.6b-q8-cpu-v1"]
            } else {
                vec!["eval-scripted-fake-v1"]
            },
            binding_sha256: binding.clone(),
            provenance: json!({"binding":basis,"quality_rubric":{"faithfulness":"not_reviewed","agency":"not_reviewed","repetition":"not_reviewed","readability":"not_reviewed","enjoyment":"not_reviewed","npc_distinctiveness":"unsupported_narrator_only","human_acceptance":false,"lexical_checks":"finite_not_semantic_oracle","fallback":"not_generated_prose_acceptance"},"native_startup":if preowned{"outside_run_unknown"}else{"included_in_invocation"}}),
            completed: false,
            cancelled: false,
            cases: vec![],
        };
        Ok(Self {
            directory: directory.into(),
            _lock: lock,
            binding,
            stories,
            ledger,
            report,
            metadata: vec![],
        })
    }
    fn restore(&self, index: usize, story: &Story) -> Result<Option<LocalStored>> {
        restore_case(&self.directory, &self.binding, index, story)
    }
    fn execute(
        mut self,
        factory: LaneFactory,
        cancel: &Cancellation,
        max_stories: usize,
    ) -> Result<Report> {
        if !(1..=6).contains(&max_stories) {
            return Err("CaseBudget".into());
        }
        if factory.profile()?
            != serde_json::from_value::<PlayProfile>(
                self.report.provenance["binding"]["profile"].clone(),
            )
            .map_err(|_| "Profile")?
        {
            return Err("Profile".into());
        }
        let mut executed = 0;
        for index in 0..self.stories.len() {
            let story = self.stories[index].clone();
            if let Some(saved) = self.restore(index, &story)? {
                self.report.cases.push(saved.result);
                self.metadata.push(saved.metadata);
                continue;
            }
            if cancel.is_cancelled()
                || executed >= max_stories
                || self.ledger.remaining() < TURN_MS + CLEANUP_RESERVE_MS
            {
                self.report.cancelled = cancel.is_cancelled();
                break;
            }
            let mut destination = None;
            for attempt in 0..32u8 {
                let path = self
                    .directory
                    .join(format!("case-{index:02}-attempt-{attempt:02}"));
                match fs::create_dir(&path) {
                    Ok(()) => {
                        destination = Some((attempt, path));
                        break;
                    }
                    Err(e) if e.kind() == std::io::ErrorKind::AlreadyExists => {}
                    Err(_) => return Err("Io".into()),
                }
            }
            let (attempt, path) = destination.ok_or("AttemptLimit")?;
            let (result, metadata) =
                match run_story(&story, &path, &factory, cancel, &mut self.ledger) {
                    Ok(value) => value,
                    Err(error) if error == "Interrupted" || error == "RunBudget" => {
                        self.report.cancelled = cancel.is_cancelled();
                        break;
                    }
                    Err(error) => return Err(error),
                };
            let result_sha256 = digest(&encode(
                &json!({"result":result,"metadata":metadata,"attempt":attempt}),
            )?);
            let saved = LocalStored {
                version: 1,
                binding_sha256: self.binding.clone(),
                result_sha256,
                attempt,
                result: result.clone(),
                metadata: metadata.clone(),
            };
            let bytes = encode(&saved)?;
            if bytes.len() > MAX_CASE {
                return Err("CaseBudget".into());
            }
            let partial = path.join("completed.json");
            write_new(&partial, &bytes)?;
            fs::rename(
                partial,
                self.directory.join(format!("case-{index:02}.json")),
            )
            .map_err(|_| "Io")?;
            self.report.cases.push(result);
            self.metadata.push(metadata);
            executed += 1;
        }
        self.finalize()
    }
    fn all_saved(&self) -> Result<bool> {
        for (index, story) in self.stories.iter().enumerate() {
            if self.restore(index, story)?.is_none() {
                return Ok(false);
            }
        }
        Ok(true)
    }
    fn restore_completed(mut self) -> Result<Report> {
        for (index, story) in self.stories.iter().enumerate() {
            let saved = self.restore(index, story)?.ok_or("CheckpointIntegrity")?;
            self.report.cases.push(saved.result);
            self.metadata.push(saved.metadata);
        }
        self.report.provenance["native_startup"] = json!("not_run_all_checkpoints_complete");
        self.report.provenance["artifact_verification_this_invocation"] =
            json!("not_run_cached_only");
        self.finalize()
    }
    fn finalize(mut self) -> Result<Report> {
        self.report.completed = self.report.cases.len() == self.stories.len();
        self.ledger.finish()?;
        self.report.provenance["coverage"] =
            coverage(&self.metadata, self.stories.len(), self.report.cases.len());
        self.report.provenance["local_cases"] =
            serde_json::to_value(&self.metadata).map_err(|_| "Encoding")?;
        self.report.provenance["budget"] = json!({"admissions_across_attempts":self.ledger.admissions,"roles_charged":self.ledger.charged_roles,"active_ms_charged":self.ledger.charged_ms,"invocations":self.ledger.invocations,"max_admissions":MAX_ADMISSIONS,"max_roles":MAX_ROLES,"max_active_ms":MAX_ACTIVE_MS,"exceeded":self.ledger.charged_ms>MAX_ACTIVE_MS,"unknown_work":"conservatively_reserved_not_refunded","cleanup":"cooperative_not_hard_realtime"});
        publish_reports(&self.directory, &self.report)?;
        Ok(self.report)
    }
}
fn restore_case(
    directory: &Path,
    binding_hash: &str,
    index: usize,
    story: &Story,
) -> Result<Option<LocalStored>> {
    let path = directory.join(format!("case-{index:02}.json"));
    if !path.exists() {
        return Ok(None);
    }
    let saved: LocalStored =
        serde_json::from_slice(&read(&path, MAX_CASE)?).map_err(|_| "CheckpointIntegrity")?;
    if saved.version != 1
        || saved.binding_sha256 != binding_hash
        || saved.result.id != story.id
        || saved.attempt >= 32
        || saved.result_sha256
            != digest(&encode(
                &json!({"result":saved.result,"metadata":saved.metadata,"attempt":saved.attempt}),
            )?)
        || saved.metadata.turns.len() > 4
        || saved.metadata.not_run.len() > 4
    {
        return Err("CheckpointIntegrity".into());
    }
    if saved.result.turns.len() != saved.metadata.turns.len()
        || saved.result.provider_requests.len() > 12
        || saved
            .metadata
            .turns
            .iter()
            .zip(&story.steps)
            .any(|(turn, step)| {
                turn.id != step.id
                    || turn.roles > 3
                    || turn.raw.len() > 3
                    || turn.native_epoch.is_some_and(|epoch| epoch >= 32)
                    || !matches!(
                        turn.execution.as_str(),
                        "guard_only" | "inference_completed" | "inference_failed" | "cancelled"
                    )
            })
        || saved
            .result
            .turns
            .iter()
            .zip(&story.steps)
            .any(|(turn, step)| turn.id != step.id)
        || saved.metadata.not_run
            != story
                .steps
                .iter()
                .skip(saved.metadata.turns.len())
                .map(|s| s.id.clone())
                .collect::<Vec<_>>()
    {
        return Err("CheckpointIntegrity".into());
    }
    let attempt = directory.join(format!("case-{index:02}-attempt-{:02}", saved.attempt));
    for (n, raw) in saved.metadata.turns.iter().flat_map(|t| &t.raw).enumerate() {
        if n >= 12
            || raw.file != format!("raw-{n:02}.json")
            || raw.bytes > 16_384
            || !matches!(raw.role.as_str(), "director" | "narrator")
        {
            return Err("CheckpointIntegrity".into());
        }
        let bytes = read(&attempt.join(&raw.file), 16_384)?;
        if bytes.len() != raw.bytes || digest(&bytes) != raw.sha256 {
            return Err("CheckpointIntegrity".into());
        }
    }
    Ok(Some(saved))
}

/// Built-in synthetic fixtures only. Existing checkpoints are immutable at four-turn story boundaries.
/// Already-owned runtime startup is honestly outside this API's measured/budgeted invocation.
pub fn run_curated(
    directory: &Path,
    resume: bool,
    selected: Option<&str>,
    cancel: &Cancellation,
    max_new_stories: usize,
    factory: LaneFactory,
) -> Result<Report> {
    let native = factory.native();
    let profile = factory.profile()?;
    if !(1..=6).contains(&max_new_stories) {
        return Err("CaseBudget".into());
    }
    let session = Session::open(directory, resume, selected, native, profile, native)?;
    if session.all_saved()? {
        session.restore_completed()
    } else {
        session.execute(factory, cancel, max_new_stories)
    }
}
/// No active content or dynamic links; same bounded escaped JSON view as the original runner.
pub(crate) fn publish_local_report(directory: &Path, report: &Report) -> Result<()> {
    let data = serde_json::to_vec_pretty(report).map_err(|_| "Encoding")?;
    let heading = if report.lane == "native_curated_shared_host" {
        "Synthetic local-model evaluation"
    } else {
        "Synthetic scripted baseline evaluation"
    };
    let html=format!("<!doctype html><meta charset=utf-8><meta http-equiv=Content-Security-Policy content=\"default-src 'none'; style-src 'none'\"><title>{heading}</title><h1>{heading}</h1><p>No human quality acceptance, Android parity or network-block observation.</p><pre>{}</pre>",escape(std::str::from_utf8(&data).map_err(|_|"Encoding")?)).into_bytes();
    if data.len() > MAX_REPORT || html.len() > MAX_REPORT {
        return Err("ReportBudget".into());
    }
    for (name, bytes) in [("report.json", data), ("report.html", html)] {
        let path = directory.join(name);
        ordinary(&path)?;
        fs::write(path, bytes).map_err(|_| "Io")?;
    }
    Ok(())
}

#[cfg(feature = "local-model")]
fn native_profile() -> Result<PlayProfile> {
    use locallore_local_runtime::{MODEL_SHA256, PROFILE, RUNTIME_COMMIT};
    let manifest: Value =
        serde_json::from_str(include_str!("../../../native/llama-worker/profile-v1.json"))
            .map_err(|_| "Profile")?;
    let profile = PlayProfile {
        id: PROFILE.into(),
        model_sha256: MODEL_SHA256.into(),
        runtime_revision: RUNTIME_COMMIT.into(),
        template_sha256: "57f1fd00f0013a2be96aa79b857391f27e23df5b5f847072b524c897e24d0361".into(),
        worker_sha256: "b5dd124e484c67c9dda5aebb2cdff1878ccefd0fba99aba4788e00a166f68434".into(),
        profile_manifest_sha256: digest(&encode(&manifest)?),
        context_tokens: 4096,
        director_tokens: 350,
        narrator_tokens: 350,
        deadline_ms: 120_000,
        repair_limit: 1,
    };
    Ok(profile)
}

/// Trusted native assets; only the compiled reviewed worker identity is permitted.
#[cfg(feature = "local-model")]
pub struct NativeAssets<'a> {
    pub resource_dir: &'a Path,
    pub model: &'a Path,
}
/// Native CLI entry: reserve preparation BEFORE hashing/loading, then use the same runner.
#[cfg(feature = "local-model")]
pub fn run_native_curated(
    directory: &Path,
    resume: bool,
    selected: Option<&str>,
    cancel: &Cancellation,
    max_new_stories: usize,
    assets: NativeAssets<'_>,
) -> Result<Report> {
    use locallore_local_runtime::LocalRuntime;
    if !(1..=6).contains(&max_new_stories) {
        return Err("CaseBudget".into());
    }
    let profile = native_profile()?;
    let mut session = Session::open(directory, resume, selected, true, profile.clone(), false)?;
    if session.all_saved()? {
        return session.restore_completed();
    }
    let started = Instant::now();
    let limit = session
        .ledger
        .remaining()
        .saturating_sub(CLEANUP_RESERVE_MS)
        .min(PREPARATION_MS);
    let stopped = || cancel.is_cancelled() || started.elapsed() >= Duration::from_millis(limit);
    let prepared = (|| {
        let mut runtime = LocalRuntime::spawn_packaged_expected_cancelled(
            assets.resource_dir,
            assets.model,
            &profile.worker_sha256,
            stopped,
        )
        .map_err(|e| format!("Runtime{e:?}"))?;
        if runtime.profile_manifest_sha256() != profile.profile_manifest_sha256 {
            return Err("Profile".into());
        }
        let load = runtime.load(stopped).map_err(|e| format!("Runtime{e:?}"))?;
        Ok((runtime, load))
    })();
    let (runtime, load) = match prepared {
        Ok(value) => value,
        Err(error) => {
            session.ledger.finish()?;
            return Err(error);
        }
    };
    session.report.provenance["native_load"] =
        serde_json::to_value(load).map_err(|_| "Encoding")?;
    session.execute(
        LaneFactory::Native {
            runtime: Arc::new(Mutex::new(runtime)),
            profile,
        },
        cancel,
        max_new_stories,
    )
}

/// Fixed CLI grammar. No fixture/provider/hash/SQL/shell or renderer-controlled import.
pub fn cli(args: &[String]) -> Result<Report> {
    if args.len() < 2 || !matches!(args[0].as_str(), "run" | "resume") {
        return Err("Usage".into());
    }
    let mut lane = None;
    let mut selected = None;
    let mut max = 6;
    let mut resource = None;
    let mut model = None;
    let mut i = 2;
    while i < args.len() {
        if i + 1 >= args.len() {
            return Err("Usage".into());
        }
        match args[i].as_str() {
            "--lane" if lane.is_none() => lane = Some(args[i + 1].as_str()),
            "--story" if selected.is_none() => selected = Some(args[i + 1].as_str()),
            "--max-stories" => {
                max = args[i + 1].parse::<usize>().map_err(|_| "Usage")?;
                if !(1..=6).contains(&max) {
                    return Err("Usage".into());
                }
            }
            "--resource-dir" if resource.is_none() => resource = Some(Path::new(&args[i + 1])),
            "--model" if model.is_none() => model = Some(Path::new(&args[i + 1])),
            _ => return Err("Usage".into()),
        }
        i += 2;
    }
    let directory = Path::new(&args[1]);
    let resume = args[0] == "resume";
    let cancel = Cancellation::default();
    match lane {
        Some("scripted") if resource.is_none() && model.is_none() => run_curated(
            directory,
            resume,
            selected,
            &cancel,
            max,
            LaneFactory::ScriptedBaseline,
        ),
        Some("native") => {
            #[cfg(feature = "local-model")]
            {
                run_native_curated(
                    directory,
                    resume,
                    selected,
                    &cancel,
                    max,
                    NativeAssets {
                        resource_dir: resource.ok_or("Usage")?,
                        model: model.ok_or("Usage")?,
                    },
                )
            }
            #[cfg(not(feature = "local-model"))]
            {
                Err("NativeFeatureUnavailable".into())
            }
        }
        _ => Err("Usage".into()),
    }
}

#[cfg(test)]
mod tests;

// Read-only desktop adapter: it shares the runner's actual checkpoint validator.
pub mod desktop_api;

/// Version2 comparison uses the same native lane, provider recording and resource ledger.
pub mod comparison;
