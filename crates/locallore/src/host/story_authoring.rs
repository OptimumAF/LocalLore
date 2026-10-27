//! Process-local original-world generation and explicit reviewed creation.
//! Generation never owns a Store write transaction or an existing story context.
use super::*;
use crate::story_authoring::{
    self as core, InitialGenerationV1, InitialProviderKindV1, InitialStoryInputV1,
    InitialWorldOriginV1, InitialWorldProposalV1,
};
use sha2::{Digest, Sha256};

#[derive(Default)]
pub(super) struct AuthoringState {
    next: u64,
    job: Option<Job>,
    running: Option<Arc<()>>,
}
struct Job {
    id: String,
    input: InitialStoryInputV1,
    cancel: Cancellation,
    phase: &'static str,
    error: Option<String>,
    generation: Option<InitialGenerationV1>,
    reviewed: Option<(InitialWorldOriginV1, String)>,
}
impl AuthoringState {
    pub(super) fn cancel_current(&mut self) {
        if let Some(job) = self.job.as_mut().filter(|job| job.phase != "created") {
            job.cancel.cancel();
            job.phase = "cancelled";
            job.error = None;
            job.generation = None;
            job.reviewed = None;
        }
    }
}
struct GenerationOwner {
    state: Arc<Mutex<State>>,
    identity: Arc<()>,
}
impl Drop for GenerationOwner {
    fn drop(&mut self) {
        let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
        state.workers -= 1;
        if state
            .authoring
            .running
            .as_ref()
            .is_some_and(|id| Arc::ptr_eq(id, &self.identity))
        {
            state.authoring.running = None;
        }
    }
}
fn provider_kind(local: &LocalPlay) -> InitialProviderKindV1 {
    if local.real_model {
        InitialProviderKindV1::Local
    } else {
        InitialProviderKindV1::Scripted
    }
}
fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}
fn hash_shape(value: &str) -> bool {
    value.len() == 64
        && value
            .bytes()
            .all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b))
}
fn preview(job: &str, origin: &InitialWorldOriginV1, hash: &str) -> Result<Value, String> {
    let seed = core::materialize(
        origin,
        Scope {
            story: "initial-review".into(),
            branch: "main".into(),
        },
    )?;
    Engine::new(seed.clone()).map_err(|_| "InvalidInput".to_owned())?;
    let mut details = vec!["Author review: world truth and private beliefs are distinct. This is not player knowledge.".to_owned()];
    for fact in seed.facts.values() {
        let names: Vec<_> = fact
            .known_by
            .iter()
            .map(|id| seed.actors[id].name.as_str())
            .collect();
        details.push(format!(
            "World truth · {} · Known to: {}",
            fact.proposition,
            names.join(", ")
        ));
    }
    for belief in &seed.beliefs {
        details.push(format!(
            "Character belief (may be false) · {} · {:?} · {}",
            seed.actors[&belief.believer].name, belief.confidence, belief.proposition
        ));
    }
    Ok(
        json!({"job":job,"review_sha256":hash,"input":origin.reviewed,"proposal":origin.accepted,"title":origin.title,"details":details}),
    )
}
impl Host {
    pub(super) fn generate_initial_world(&self, job_id: &str) -> Value {
        let (input, local, cancel, _owner) = {
            let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
            if state.persistence.is_none() {
                return reject("Unsupported");
            }
            if state.authoring.running.is_some() || state.workers >= MAX_WORKERS {
                return reject("Busy");
            }
            let Some(local) = state.local_play.clone() else {
                return reject("Unsupported");
            };
            let Some(job) = state.authoring.job.as_mut().filter(|job| job.id == job_id) else {
                return reject("NotFound");
            };
            if job.cancel.is_cancelled() {
                return reject("Cancelled");
            }
            if job.phase != "draft" {
                return reject("Stale");
            }
            job.phase = "generating";
            let input = job.input.clone();
            let cancel = job.cancel.clone();
            let identity = Arc::new(());
            state.authoring.running = Some(identity.clone());
            state.workers += 1;
            (
                input,
                local,
                cancel,
                GenerationOwner {
                    state: self.state.clone(),
                    identity,
                },
            )
        };
        let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(
            || -> Result<InitialGenerationV1, String> {
                let request = core::generation_request(&input, &local.profile.id, job_id)?;
                let mut provider = (local.provider)();
                let response =
                    generate(provider.as_mut(), &request, &cancel).map_err(|e| e.to_string())?;
                // Dropping the bridge provider invalidates its exact ticket before publication.
                drop(provider);
                if cancel.is_cancelled() {
                    return Err("Cancelled".into());
                }
                if response.len() > 8192 {
                    return Err("TooLarge".into());
                }
                let proposal: InitialWorldProposalV1 =
                    serde_json::from_slice(&response).map_err(|_| "Malformed".to_owned())?;
                core::validate_proposal(&input, &proposal)?;
                let response_sha256 = digest(&response);
                let response = String::from_utf8(response).map_err(|_| "Malformed".to_owned())?;
                Ok(InitialGenerationV1 {
                    input: input.clone(),
                    proposal,
                    model_profile: local.profile.id.clone(),
                    provider: provider_kind(&local),
                    prompt_version: "initial-world-v1".into(),
                    schema_version: "initial-world-v1".into(),
                    response,
                    response_sha256,
                })
            },
        ))
        .unwrap_or_else(|_| Err("Internal".into()));
        let mut state = self.state.lock().unwrap_or_else(|p| p.into_inner());
        let Some(job) = state.authoring.job.as_mut().filter(|job| job.id == job_id) else {
            return reject("Cancelled");
        };
        if cancel.is_cancelled() || job.phase != "generating" {
            return reject("Cancelled");
        }
        match result {
            Ok(generation) => {
                let reply = ok(
                    json!({"job":job.id,"input":generation.input,"proposal":generation.proposal,"provider":generation.provider}),
                );
                job.generation = Some(generation);
                job.phase = "ready";
                reply
            }
            Err(error) => {
                job.phase = "failed";
                job.error = Some(error.clone());
                reject(error)
            }
        }
    }
    pub(super) fn dispatch_authoring(
        &self,
        state: &mut State,
        command: &HostCommand,
    ) -> Option<Value> {
        let result = (|| -> Result<Value, String> {
            match command {
                HostCommand::AuthoringCapabilities {} => {
                    let available = state.persistence.is_some() && state.local_play.is_some();
                    Ok(ok(
                        json!({"available":available,"provider":state.local_play.as_ref().filter(|_| available).map(provider_kind),"max_tokens":1024}),
                    ))
                }
                HostCommand::AuthoringBegin { input } => {
                    core::validate_input(input)?;
                    if state.persistence.is_none() || state.local_play.is_none() {
                        return Err("Unsupported".into());
                    }
                    if state.authoring.running.is_some() {
                        return Err("Busy".into());
                    }
                    let next = state.authoring.next.checked_add(1).ok_or("IdExhausted")?;
                    let input_sha256 =
                        digest(&serde_json::to_vec(input).map_err(|_| "InvalidInput")?);
                    state.authoring.cancel_current();
                    let provider = provider_kind(state.local_play.as_ref().unwrap());
                    let id = format!("initial-{next}");
                    state.authoring.next = next;
                    state.authoring.job = Some(Job {
                        id: id.clone(),
                        input: input.clone(),
                        cancel: Cancellation::default(),
                        phase: "draft",
                        error: None,
                        generation: None,
                        reviewed: None,
                    });
                    Ok(ok(
                        json!({"job":id,"input_sha256":input_sha256,"provider":provider}),
                    ))
                }
                HostCommand::AuthoringReview {
                    job,
                    input,
                    proposal,
                    title,
                } => {
                    if state.authoring.running.is_some() {
                        return Err("Busy".into());
                    }
                    let current = state
                        .authoring
                        .job
                        .as_mut()
                        .filter(|j| &j.id == job)
                        .ok_or("NotFound")?;
                    // Any submitted edit revokes the old review, including an invalid edit.
                    current.reviewed = None;
                    if current.cancel.is_cancelled() {
                        return Err("Cancelled".into());
                    }
                    if !matches!(current.phase, "ready" | "reviewed") {
                        return Err("Stale".into());
                    }
                    current.phase = "ready";
                    let generation = current.generation.clone().ok_or("Stale")?;
                    let origin = InitialWorldOriginV1 {
                        version: 1,
                        generation,
                        reviewed: input.clone(),
                        accepted: proposal.clone(),
                        title: title.clone(),
                    };
                    let hash = core::origin_hash(&origin)?;
                    let reply = preview(job, &origin, &hash)?;
                    current.reviewed = Some((origin, hash));
                    current.phase = "reviewed";
                    Ok(ok(reply))
                }
                HostCommand::AuthoringCreate {
                    job,
                    review_sha256,
                    creation_id,
                } => {
                    if !crate::story_setup::valid_creation_id(creation_id)
                        || !hash_shape(review_sha256)
                    {
                        return Err("InvalidInput".into());
                    }
                    let port = state.persistence.as_mut().ok_or("Unsupported")?;
                    // A completed creation can be recovered without a generation job or model.
                    if let Some(starter) = port.lookup_original(creation_id, review_sha256)? {
                        return attach_named_starter(state, &starter).map_err(|reply| {
                            reply["error"].as_str().unwrap_or("Internal").to_owned()
                        });
                    }
                    if state.authoring.running.is_some() {
                        return Err("Busy".into());
                    }
                    let current = state
                        .authoring
                        .job
                        .as_ref()
                        .filter(|j| &j.id == job)
                        .ok_or("NotFound")?;
                    if current.cancel.is_cancelled() {
                        return Err("Cancelled".into());
                    }
                    if current.phase != "reviewed" {
                        return Err("Stale".into());
                    }
                    let (origin, expected) = current.reviewed.as_ref().ok_or("Stale")?;
                    if expected != review_sha256 || core::origin_hash(origin)? != *expected {
                        return Err("Stale".into());
                    }
                    let starter = crate::story_setup::prepare_original(origin, creation_id)?;
                    let reply = attach_named_starter(state, &starter).map_err(|reply| {
                        reply["error"].as_str().unwrap_or("Internal").to_owned()
                    })?;
                    // The Store commit won; a later cancellation cannot undo it.
                    if let Some(current) = state.authoring.job.as_mut() {
                        current.phase = "created";
                    }
                    Ok(reply)
                }
                HostCommand::AuthoringCancel { job } => {
                    let current = state
                        .authoring
                        .job
                        .as_ref()
                        .filter(|j| &j.id == job)
                        .ok_or("NotFound")?;
                    let cancelled = current.phase != "created";
                    state.authoring.cancel_current();
                    Ok(ok(json!({"cancelled":cancelled})))
                }
                HostCommand::AuthoringStatus { job } => {
                    let current = state
                        .authoring
                        .job
                        .as_ref()
                        .filter(|j| &j.id == job)
                        .ok_or("NotFound")?;
                    Ok(ok(
                        json!({"job":job,"phase":current.phase,"error":current.error}),
                    ))
                }
                _ => return Err("NotAuthoringCommand".into()),
            }
        })();
        match result {
            Err(error) if error == "NotAuthoringCommand" => None,
            Err(error) => Some(reject(error)),
            Ok(reply) => Some(reply),
        }
    }
}
