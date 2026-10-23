use crate::{
    contracts::*,
    engine::{check_json_budget, CharacterContext, Engine},
};
use std::{
    sync::{
        atomic::{AtomicBool, Ordering},
        Arc,
    },
    task::Poll,
    time::Instant,
};

#[derive(Clone, Debug, Default)]
pub struct Cancellation(Arc<AtomicBool>);
impl Cancellation {
    pub fn cancel(&self) {
        self.0.store(true, Ordering::SeqCst);
    }
    pub fn is_cancelled(&self) -> bool {
        self.0.load(Ordering::SeqCst)
    }
}

#[derive(Clone, Debug)]
pub struct Budget {
    pub max_output_bytes: usize,
    pub max_output_tokens: u32,
    pub max_pending_polls: u16,
    pub deadline_ms: u64,
}
impl Default for Budget {
    fn default() -> Self {
        Self {
            max_output_bytes: MAX_PROPOSAL_BYTES,
            max_output_tokens: 512,
            max_pending_polls: 8,
            deadline_ms: 1000,
        }
    }
}

#[derive(Clone, Debug)]
pub enum Input {
    Director {
        request: Request,
        context: Box<CharacterContext>,
    },
    /// Only an approved public description reaches the narrator, never the hidden world seed.
    Narrator { accepted_description: String },
    /// Shared play-v2 compiler supplies a bounded prompt and constrained JSON schema.
    Structured { role: String, prompt: String, schema: serde_json::Value },
}

#[derive(Clone, Debug)]
pub struct GenerationRequest {
    pub version: u16,
    pub scope: Scope,
    pub turn: String,
    pub revision: u64,
    pub model_profile: String,
    pub schema: String,
    pub budget: Budget,
    pub input: Input,
}

/// A native adapter must return promptly, honor the cancellation token, keep sessions scoped
/// to this immutable request, and release resources on drop. No DB, filesystem or tool handles.
/// Each call to generate owns one exclusive provider session. No concurrent poll on a session.
pub trait InferenceProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>>;
}

pub(crate) fn generate(
    provider: &mut (impl InferenceProvider + ?Sized),
    request: &GenerationRequest,
    cancel: &Cancellation,
) -> Result<Vec<u8>, Error> {
    if request.version != VERSION {
        return Err(Error::Version);
    }
    if request.budget.max_output_bytes == 0
        || request.budget.max_output_bytes > MAX_PROPOSAL_BYTES
        || request.budget.max_output_tokens == 0
        || request.budget.max_output_tokens > 2048
        || request.budget.deadline_ms == 0
        || request.budget.deadline_ms > 120_000
    {
        return Err(Error::Rule);
    }
    let start = Instant::now();
    for _ in 0..=request.budget.max_pending_polls {
        if cancel.is_cancelled() {
            return Err(Error::Cancelled);
        }
        if start.elapsed().as_millis() >= u128::from(request.budget.deadline_ms) {
            return Err(Error::Timeout);
        }
        match provider.poll(request, cancel) {
            Poll::Pending => std::thread::sleep(std::time::Duration::from_millis(5)),
            Poll::Ready(result) => {
                if cancel.is_cancelled() {
                    return Err(Error::Cancelled);
                }
                if start.elapsed().as_millis() >= u128::from(request.budget.deadline_ms) {
                    return Err(Error::Timeout);
                }
                let bytes = result?;
                if bytes.len() > request.budget.max_output_bytes {
                    return Err(Error::TooLarge);
                }
                return Ok(bytes);
            }
        }
    }
    Err(Error::Timeout)
}

/// Conservative proof pipeline: one director and one narrator attempt, zero repair attempts.
/// Failure leaves in-memory canon unchanged; model output is never applied directly.
pub fn execute(
    engine: &mut Engine,
    request: &Request,
    provider: &mut impl InferenceProvider,
    cancel: &Cancellation,
    budget: Budget,
) -> Result<Receipt, Error> {
    if let Some(receipt) = engine.recorded(request)? {
        return Ok(receipt);
    }
    engine.preflight(request)?;
    // Check intent before spending inference work; free text needs explicit clarification.
    let expected = Engine::proposal(request)?;
    let _ = engine.preview(request, &expected)?;
    if request.expected_revision != engine.revision() {
        return Err(Error::Stale);
    }
    let context = engine.character_context(
        &engine.seed().player,
        &request.scope,
        request.expected_revision,
    )?;
    check_json_budget(&context, 32_768)?;
    let director = GenerationRequest {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        revision: request.expected_revision,
        model_profile: "deterministic-fake-v1".into(),
        schema: "locallore-proposal-v1".into(),
        budget: budget.clone(),
        input: Input::Director {
            request: request.clone(),
            context: Box::new(context),
        },
    };
    let proposal = Proposal::parse(&generate(provider, &director, cancel)?)?;
    let preview = engine.preview(request, &proposal)?;
    let narrator = GenerationRequest {
        version: VERSION,
        scope: request.scope.clone(),
        turn: request.turn.clone(),
        revision: request.expected_revision,
        model_profile: "deterministic-fake-v1".into(),
        schema: "locallore-safe-narration-v1".into(),
        budget,
        input: Input::Narrator {
            accepted_description: preview.narration().into(),
        },
    };
    let bytes = generate(provider, &narrator, cancel)?;
    let narration = std::str::from_utf8(&bytes).map_err(|_| Error::Malformed)?;
    if cancel.is_cancelled() {
        return Err(Error::Cancelled);
    }
    engine.commit(request, &proposal, narration)
}

#[derive(Clone, Debug)]
pub enum FakeMode {
    Accepted,
    Malformed,
    Rejected,
    Delayed { polls: u16 },
    Cancelled,
    Failed,
    InventedNarration,
    Oversized,
}

/// Synthetic plumbing only. No inference, tokenizer, model-quality or device-performance claim.
pub struct FakeProvider {
    pub mode: FakeMode,
    pub calls: u32,
}
impl FakeProvider {
    pub fn new(mode: FakeMode) -> Self {
        Self { mode, calls: 0 }
    }
}
impl InferenceProvider for FakeProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        self.calls += 1;
        if cancel.is_cancelled() {
            return Poll::Ready(Err(Error::Cancelled));
        }
        match &mut self.mode {
            FakeMode::Delayed { polls } if *polls > 0 => {
                *polls -= 1;
                return Poll::Pending;
            }
            FakeMode::Cancelled => {
                cancel.cancel();
                return Poll::Ready(Err(Error::Cancelled));
            }
            FakeMode::Failed => return Poll::Ready(Err(Error::Provider)),
            FakeMode::Malformed => return Poll::Ready(Ok(b"{not-json".to_vec())),
            FakeMode::Oversized => return Poll::Ready(Ok(vec![b'x'; MAX_PROPOSAL_BYTES + 1])),
            _ => (),
        }
        let result = match &request.input {
            Input::Director { request, .. } => {
                Engine::proposal(request).and_then(|mut proposal| {
                    if matches!(self.mode, FakeMode::Rejected) {
                        proposal.commands = vec![Command::UseAbility {
                            ability: "invented-teleport".into(),
                        }];
                    }
                    serde_json::to_vec(&proposal).map_err(|_| Error::Malformed)
                })
            }
            Input::Narrator {
                accepted_description,
            } => {
                if matches!(self.mode, FakeMode::InventedNarration) {
                    Ok(b"A golden key appears in your hand.".to_vec())
                } else {
                    Ok(accepted_description.as_bytes().to_vec())
                }
            }
            Input::Structured { .. } => Err(Error::Provider),
        };
        Poll::Ready(result)
    }
}
