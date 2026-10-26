//! Closed native construction over one shared execution pipeline. A literal
//! source is not a memory compilation or coverage result.
use super::*;
use crate::context_compiler::{ContextPackage, LiteralTranscriptSourceV1};

pub(super) enum DirectorInput<'a> {
    Memory(MemoryInput<'a>),
    LiteralV1,
}
struct MemoryDirector {
    frame: director_budget::DirectorEnvelopeV25,
    package: ContextPackage,
    record: PlayContextRecord,
    policy: PlayContextPolicy,
    forwarded: ForwardedEstimateV1,
}
struct LiteralDirector {
    source: LiteralTranscriptSourceV1,
    initial: RenderedLiteralDirectorV1,
}
enum Body {
    Memory(Box<MemoryDirector>),
    Literal(Box<LiteralDirector>),
}
pub(super) struct PreparedDirector(Body);

pub(super) fn compile_error(error: crate::context_compiler::CompileError) -> Error {
    use crate::context_compiler::CompileError as C;
    match error {
        C::Cancelled => Error::Cancelled,
        C::Scope => Error::Scope,
        C::Stale => Error::Stale,
        C::Observer => Error::Knowledge,
        C::MandatoryBudget | C::TooLarge => Error::TooLarge,
        C::UnknownReference | C::AmbiguousAlias => Error::ClarificationRequired,
        _ => Error::Rule,
    }
}

impl PreparedDirector {
    pub(super) fn new(
        engine: &Engine,
        request: &Request,
        profile: &PlayProfile,
        frame: Option<director_budget::DirectorEnvelopeV25>,
        input: DirectorInput<'_>,
        cancel: &Cancellation,
    ) -> Result<Self, Error> {
        match input {
            DirectorInput::Memory(input) => {
                let frame = frame.ok_or(Error::Rule)?;
                let Intent::FreeText { kind, text } = &request.intent else {
                    return Err(Error::Agency);
                };
                let reserved_tokens = 512.min(profile.context_tokens.saturating_sub(1));
                let compilation = crate::context_compiler::compile_for_director_cancelled(
                    engine,
                    &crate::context_compiler::CompileRequest {
                        version: crate::context_compiler::POLICY_COMPILER_VERSION,
                        scope: request.scope.clone(),
                        expected_head: request.expected_revision,
                        at_revision: None,
                        observer: engine.seed().player.clone(),
                        role: crate::context_compiler::Role::Director,
                        query: if matches!(kind, PlayInputKind::Action) {
                            text.clone()
                        } else {
                            String::new()
                        },
                        referenced_ids: vec![],
                        budget: crate::context_compiler::Budget {
                            estimated_tokens: profile.context_tokens,
                            reserved_tokens,
                            ..crate::context_compiler::Budget::default()
                        },
                    },
                    input.policy,
                    input.proof,
                    &frame,
                    &|| cancel.is_cancelled(),
                )
                .map_err(compile_error)?;
                let record = PlayContextRecord::from_policy_compilation(
                    &compilation.policy,
                    input.source_fallback_reason,
                );
                Ok(Self(Body::Memory(Box::new(MemoryDirector {
                    frame,
                    package: compilation.policy.compilation.package,
                    record,
                    policy: input.policy,
                    forwarded: compilation.forwarded,
                }))))
            }
            DirectorInput::LiteralV1 => {
                let source = crate::context_compiler::player_literal_transcript_v1_cancelled(
                    engine,
                    engine.scope(),
                    engine.revision(),
                    &engine.seed().player,
                    &|| cancel.is_cancelled(),
                )
                .map_err(compile_error)?;
                let initial = render_player_literal_director_v1_cancelled(
                    engine,
                    request,
                    &source,
                    profile,
                    DirectorPassV25::Initial,
                    &|| cancel.is_cancelled(),
                )?;
                Ok(Self(Body::Literal(Box::new(LiteralDirector {
                    source,
                    initial,
                }))))
            }
        }
    }
    pub(super) fn package(&self) -> Option<&ContextPackage> {
        match &self.0 {
            Body::Memory(m) => Some(&m.package),
            Body::Literal(_) => None,
        }
    }
    pub(super) fn context_record(&self) -> Option<PlayContextRecord> {
        match &self.0 {
            Body::Memory(m) => Some(m.record.clone()),
            Body::Literal(_) => None,
        }
    }
    pub(super) fn policy(&self) -> Option<PlayContextPolicy> {
        match &self.0 {
            Body::Memory(m) => Some(m.policy),
            Body::Literal(_) => None,
        }
    }
    pub(super) fn retrieval_count(&self) -> u32 {
        match &self.0 {
            Body::Memory(m) => m.package.diagnostics.eligible_candidates as u32,
            Body::Literal(l) => l.source.units().len().min(u32::MAX as usize) as u32,
        }
    }
    pub(super) fn input_tokens(&self) -> u32 {
        match &self.0 {
            Body::Memory(m) => m.forwarded.actual_prompt_schema_estimated_tokens(),
            Body::Literal(l) => l
                .initial
                .forwarded()
                .actual_prompt_schema_estimated_tokens(),
        }
    }
    pub(super) fn frame_count(&self) -> u32 {
        match &self.0 {
            Body::Memory(m) => m.frame.eligible_count(&m.package),
            Body::Literal(l) => (l.initial.selected_units() + 1) as u32,
        }
    }
    pub(super) fn ensure_audience(&self) -> Result<(), Error> {
        match &self.0 {
            Body::Memory(m) => m.frame.ensure_audience(),
            Body::Literal(_) => Ok(()),
        }
    }
    pub(super) fn render(
        &self,
        engine: &Engine,
        request: &Request,
        profile: &PlayProfile,
        pass: DirectorPassV25,
        cancel: &Cancellation,
    ) -> Result<director_budget::RenderedDirectorV25, Error> {
        match &self.0 {
            Body::Memory(m) => m.frame.render_checked(&m.package, pass),
            Body::Literal(l) => {
                let rendered = if pass == DirectorPassV25::Initial {
                    &l.initial
                } else {
                    // The owned source and exact Engine are rebound on repair.
                    return render_player_literal_director_v1_cancelled(
                        engine,
                        request,
                        &l.source,
                        profile,
                        pass,
                        &|| cancel.is_cancelled(),
                    )
                    .map(|r| director_budget::RenderedDirectorV25 {
                        prompt: r.prompt().to_owned(),
                        schema: r.schema().clone(),
                    });
                };
                Ok(director_budget::RenderedDirectorV25 {
                    prompt: rendered.prompt().to_owned(),
                    schema: rendered.schema().clone(),
                })
            }
        }
    }
}
