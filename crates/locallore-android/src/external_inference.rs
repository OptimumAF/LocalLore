// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! SDK-neutral external inference for a production workspace owner. No model, JNI reference or thread.
use locallore::{
    contracts::{Error, Scope, VERSION},
    host::{Host, HostPlayConstructionV1},
    inference::{Cancellation, GenerationRequest, InferenceProvider, Input},
    play::{PlayContextPolicy, PlayProfile},
};
use serde_json::{json, Value};
use std::{
    sync::{
        atomic::{AtomicU64, Ordering},
        Arc, Mutex,
    },
    task::Poll,
};

pub const MAX_PROFILE: usize = 4096;
pub const MAX_RESPONSE: usize = 16_384;
const MAX_WORKER_REQUEST: usize = 32_768;
pub const MAX_POLL: usize = 40_000;

pub(crate) fn profile(bytes: &[u8]) -> Result<PlayProfile, String> {
    if bytes.len() > MAX_PROFILE {
        return Err("TooLarge".into());
    }
    let profile: PlayProfile = serde_json::from_slice(bytes).map_err(|_| "Profile")?;
    profile.validate().map_err(|_| "Profile")?;
    Ok(profile)
}
fn ok(data: Value) -> Value {
    json!({"version":1,"status":"ok","data":data})
}
fn rejected(error: &str) -> Value {
    json!({"version":1,"status":"rejected","error":error})
}
pub(crate) fn bounded(limit: usize, operation: impl FnOnce() -> Value) -> Vec<u8> {
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(operation))
        .unwrap_or_else(|_| rejected("Internal"));
    match serde_json::to_vec(&result) {
        Ok(bytes) if bytes.len() <= limit => bytes,
        _ => serde_json::to_vec(&rejected("TooLarge")).unwrap_or_default(),
    }
}
impl Bridge {
    pub(crate) fn configure(
        host: &Host,
        profile: PlayProfile,
        tickets: Arc<AtomicU64>,
    ) -> Result<Arc<Self>, String> {
        let bridge = Arc::new(Self {
            state: Mutex::new(BridgeState::default()),
            tickets,
        });
        let provider_bridge = bridge.clone();
        let provider_profile = profile.clone();
        host.configure_local_provider_with_construction(
            profile,
            Arc::new(move || {
                Box::new(BridgeProvider {
                    bridge: provider_bridge.clone(),
                    owner: Arc::new(()),
                    profile: provider_profile.clone(),
                    ticket: None,
                })
            }),
            HostPlayConstructionV1::MemoryStorySceneV1(PlayContextPolicy::StateRelevantMemoryV1),
        )
        .map_err(|_| "Profile")?;
        Ok(bridge)
    }
    pub(crate) fn poll(&self) -> Value {
        let Ok(state) = self.state.lock() else {
            return rejected("Internal");
        };
        if state.closed {
            return rejected("InvalidHandle");
        }
        let pending = state
            .active
            .as_ref()
            .filter(|active| !active.cancel.is_cancelled())
            .and_then(|active| active.pending.as_ref())
            .filter(|pending| pending.response.is_none());
        ok(
            json!({"pending":pending.map(|pending| json!({"ticket":pending.ticket,"request":pending.request.worker}))}),
        )
    }
    pub(crate) fn respond(&self, ticket: u64, text: &[u8]) -> Value {
        let Ok(mut state) = self.state.lock() else {
            return rejected("Internal");
        };
        if state.closed {
            return rejected("InvalidHandle");
        }
        let pending = state
            .active
            .as_mut()
            .filter(|active| !active.cancel.is_cancelled())
            .and_then(|active| active.pending.as_mut());
        let Some(pending) =
            pending.filter(|pending| pending.ticket == ticket && pending.response.is_none())
        else {
            return rejected("InvalidTicket");
        };
        if ticket == 0 || ticket > i64::MAX as u64 {
            return rejected("InvalidTicket");
        }
        if text.len() > MAX_RESPONSE || text.len() > pending.request.max_output_bytes {
            return rejected("TooLarge");
        }
        if text.is_empty() || std::str::from_utf8(text).is_err() {
            return rejected("Malformed");
        }
        pending.response = Some(text.to_vec());
        ok(json!({"accepted":true}))
    }
    pub(crate) fn close(&self) {
        let mut state = self
            .state
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        state.closed = true;
        state.active = None;
    }
}

pub(crate) struct Bridge {
    state: Mutex<BridgeState>,
    tickets: Arc<AtomicU64>,
}
#[derive(Default)]
struct BridgeState {
    closed: bool,
    active: Option<Active>,
}
struct Active {
    owner: Arc<()>,
    scope: Scope,
    turn: String,
    revision: u64,
    cancel: Cancellation,
    pending: Option<Pending>,
}
struct Pending {
    ticket: u64,
    request: Packet,
    response: Option<Vec<u8>>,
}
struct Packet {
    worker: Value,
    role: String,
    prompt: String,
    schema: Value,
    max_tokens: u32,
    schema_label: String,
    max_output_bytes: usize,
    max_pending_polls: u16,
    deadline_ms: u64,
}
impl Packet {
    fn new(request: &GenerationRequest, profile: &PlayProfile) -> Result<Self, Error> {
        if request.version != VERSION || request.model_profile != profile.id {
            return Err(Error::Provider);
        }
        let Input::Structured {
            role,
            prompt,
            schema,
        } = &request.input
        else {
            return Err(Error::Provider);
        };
        let cap = match role.as_str() {
            "director" => profile.director_tokens,
            "narrator" => profile.narrator_tokens,
            "author"
                if request.schema == "initial-world-v1"
                    && request.revision == 0
                    && request.scope.branch == "draft"
                    && request.scope.story == format!("author-draft-{}", request.turn)
                    && request.budget.max_output_bytes <= 8192
                    && request.budget.deadline_ms <= 120_000 =>
            {
                1024
            }
            _ => return Err(Error::Provider),
        };
        if request.budget.max_output_tokens == 0
            || request.budget.max_output_tokens > u32::from(cap)
        {
            return Err(Error::Provider);
        }
        let worker = json!({"version":1,"role":role,"prompt":prompt,"max_tokens":request.budget.max_output_tokens,
            "context_tokens":profile.context_tokens,"threads":4,"schema":schema});
        if serde_json::to_vec(&worker)
            .map_err(|_| Error::Provider)?
            .len()
            > MAX_WORKER_REQUEST
        {
            return Err(Error::TooLarge);
        }
        Ok(Self {
            worker,
            role: role.clone(),
            prompt: prompt.clone(),
            schema: schema.clone(),
            max_tokens: request.budget.max_output_tokens,
            schema_label: request.schema.clone(),
            max_output_bytes: request.budget.max_output_bytes,
            max_pending_polls: request.budget.max_pending_polls,
            deadline_ms: request.budget.deadline_ms,
        })
    }
    fn matches(&self, request: &GenerationRequest, profile: &PlayProfile) -> bool {
        request.version == VERSION
            && request.model_profile == profile.id
            && request.budget.max_output_tokens == self.max_tokens
            && request.schema == self.schema_label
            && request.budget.max_output_bytes == self.max_output_bytes
            && request.budget.max_pending_polls == self.max_pending_polls
            && request.budget.deadline_ms == self.deadline_ms
            && matches!(&request.input, Input::Structured { role, prompt, schema } if role == &self.role && prompt == &self.prompt && schema == &self.schema)
    }
}
struct BridgeProvider {
    bridge: Arc<Bridge>,
    owner: Arc<()>,
    profile: PlayProfile,
    ticket: Option<u64>,
}
impl InferenceProvider for BridgeProvider {
    fn poll(
        &mut self,
        request: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<Result<Vec<u8>, Error>> {
        if cancel.is_cancelled() {
            self.release();
            return Poll::Ready(Err(Error::Cancelled));
        }
        let Ok(mut state) = self.bridge.state.lock() else {
            return Poll::Ready(Err(Error::Provider));
        };
        if state.closed {
            return Poll::Ready(Err(Error::Cancelled));
        }
        if let Some(active) = state.active.as_ref() {
            if !Arc::ptr_eq(&active.owner, &self.owner) {
                return Poll::Ready(Err(Error::Provider));
            }
            if active.cancel.is_cancelled() {
                return Poll::Ready(Err(Error::Cancelled));
            }
            if active.scope != request.scope
                || active.turn != request.turn
                || active.revision != request.revision
            {
                return Poll::Ready(Err(Error::Provider));
            }
        }
        if let Some(ticket) = self.ticket {
            let pending = state
                .active
                .as_mut()
                .and_then(|active| active.pending.as_mut());
            let Some(pending) = pending.filter(|pending| pending.ticket == ticket) else {
                return Poll::Ready(Err(Error::Provider));
            };
            if !pending.request.matches(request, &self.profile) {
                return Poll::Ready(Err(Error::Provider));
            }
            if let Some(response) = pending.response.take() {
                state.active.as_mut().unwrap().pending = None;
                self.ticket = None;
                return Poll::Ready(Ok(response));
            }
            return Poll::Pending;
        }
        let packet = match Packet::new(request, &self.profile) {
            Ok(packet) => packet,
            Err(error) => return Poll::Ready(Err(error)),
        };
        let ticket =
            match self
                .bridge
                .tickets
                .fetch_update(Ordering::SeqCst, Ordering::SeqCst, |last| {
                    last.checked_add(1).filter(|next| *next <= i64::MAX as u64)
                }) {
                Ok(last) => last + 1,
                Err(_) => return Poll::Ready(Err(Error::Provider)),
            };
        let active = state.active.get_or_insert_with(|| Active {
            owner: self.owner.clone(),
            scope: request.scope.clone(),
            turn: request.turn.clone(),
            revision: request.revision,
            cancel: cancel.clone(),
            pending: None,
        });
        active.pending = Some(Pending {
            ticket,
            request: packet,
            response: None,
        });
        self.ticket = Some(ticket);
        Poll::Pending
    }
}
impl BridgeProvider {
    fn release(&mut self) {
        if let Ok(mut state) = self.bridge.state.lock() {
            if state
                .active
                .as_ref()
                .is_some_and(|active| Arc::ptr_eq(&active.owner, &self.owner))
            {
                state.active = None;
            }
        }
        self.ticket = None;
    }
}
impl Drop for BridgeProvider {
    fn drop(&mut self) {
        self.release();
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use locallore::inference::Budget;
    #[test]
    fn author_role_is_separate_bounded_and_cannot_expand_existing_play_roles() {
        let input = serde_json::from_str(include_str!(
            "../../../fixtures/initial_world/ashglass-input.json"
        ))
        .unwrap();
        let author =
            locallore::story_authoring::generation_request(&input, &profile().id, "author-job")
                .unwrap();
        let packet = Packet::new(&author, &profile()).unwrap();
        assert_eq!(packet.worker["role"], "author");
        assert_eq!(packet.worker["max_tokens"], 1024);
        for mutate in [
            (|r: &mut GenerationRequest| r.scope.branch = "main".into())
                as fn(&mut GenerationRequest),
            |r| r.revision = 1,
            |r| r.schema = "foreign".into(),
            |r| r.scope.story = "another-draft".into(),
            |r| r.budget.max_output_tokens = 1025,
            |r| r.budget.max_output_bytes = 8193,
            |r| r.budget.deadline_ms = 120001,
        ] {
            let mut changed = author.clone();
            mutate(&mut changed);
            assert!(Packet::new(&changed, &profile()).is_err());
        }
        let mut director = generation();
        director.budget.max_output_tokens = 351;
        assert!(Packet::new(&director, &profile()).is_err());
        let mut narrator = generation();
        narrator.budget.max_output_tokens = 221;
        if let Input::Structured { role, .. } = &mut narrator.input {
            *role = "narrator".into();
        }
        assert!(Packet::new(&narrator, &profile()).is_err());
    }
    #[test]
    fn author_response_cap_and_late_ticket_refusal_apply_before_delivery() {
        let input = serde_json::from_str(include_str!(
            "../../../fixtures/initial_world/ashglass-input.json"
        ))
        .unwrap();
        let author =
            locallore::story_authoring::generation_request(&input, &profile().id, "author-job")
                .unwrap();
        let bridge = bridge();
        let mut provider = provider(&bridge);
        let cancel = Cancellation::default();
        assert!(matches!(provider.poll(&author, &cancel), Poll::Pending));
        let ticket = provider.ticket.unwrap();
        assert_eq!(
            bridge.respond(ticket, &vec![b'x'; 8193])["error"],
            "TooLarge"
        );
        assert!(!bridge.poll()["data"]["pending"].is_null());
        cancel.cancel();
        assert_eq!(bridge.respond(ticket, b"late")["error"], "InvalidTicket");
        drop(provider);
        assert!(bridge.state.lock().unwrap().active.is_none());
    }
    fn profile() -> PlayProfile {
        PlayProfile {
            id: "synthetic-production-owner-v1".into(),
            model_sha256: "a".repeat(64),
            runtime_revision: "b".repeat(40),
            template_sha256: "c".repeat(64),
            worker_sha256: "d".repeat(64),
            profile_manifest_sha256: "e".repeat(64),
            context_tokens: 2048,
            director_tokens: 350,
            narrator_tokens: 220,
            deadline_ms: 5000,
            repair_limit: 1,
        }
    }
    fn generation() -> GenerationRequest {
        GenerationRequest {
            version: 1,
            scope: Scope {
                story: "synthetic".into(),
                branch: "main".into(),
            },
            turn: "first".into(),
            revision: 0,
            model_profile: "synthetic-production-owner-v1".into(),
            schema: "locallore-director-v2".into(),
            budget: Budget {
                max_output_tokens: 350,
                ..Budget::default()
            },
            input: Input::Structured {
                role: "director".into(),
                prompt: "UNTRUSTED literal prompt\n\"canary\"".into(),
                schema: json!({"oneOf":[{"const":"preserve this schema exactly"}]}),
            },
        }
    }
    fn bridge() -> Arc<Bridge> {
        Arc::new(Bridge {
            state: Mutex::new(BridgeState::default()),
            tickets: Arc::new(AtomicU64::new(0)),
        })
    }
    fn provider(bridge: &Arc<Bridge>) -> BridgeProvider {
        BridgeProvider {
            bridge: bridge.clone(),
            owner: Arc::new(()),
            profile: profile(),
            ticket: None,
        }
    }

    #[test]
    fn packet_preserves_original_structured_prompt_schema_and_budget_without_extension() {
        let request = generation();
        let packet = Packet::new(&request, &profile()).unwrap();
        let Input::Structured { prompt, schema, .. } = &request.input else {
            unreachable!()
        };
        assert_eq!(
            packet.worker,
            json!({"version":1,"role":"director","prompt":prompt,"schema":schema,
            "max_tokens":350,"context_tokens":2048,"threads":4})
        );
        assert!(packet.matches(&request, &profile()));
        let mut changed = request;
        changed.budget.max_output_tokens -= 1;
        assert!(!packet.matches(&changed, &profile()));
        changed.model_profile = "foreign-profile".into();
        assert!(matches!(
            Packet::new(&changed, &profile()),
            Err(Error::Provider)
        ));
        changed = generation();
        changed.input = Input::Structured {
            role: "executor".into(),
            prompt: String::new(),
            schema: json!({}),
        };
        assert!(matches!(
            Packet::new(&changed, &profile()),
            Err(Error::Provider)
        ));
        changed.input = Input::Structured {
            role: "director".into(),
            prompt: "X".repeat(MAX_WORKER_REQUEST),
            schema: json!({}),
        };
        assert!(matches!(
            Packet::new(&changed, &profile()),
            Err(Error::TooLarge)
        ));
    }
    #[test]
    fn competing_provider_and_old_provider_drop_cannot_clear_another_owners_pending_request() {
        let bridge = bridge();
        let request = generation();
        let cancel = Cancellation::default();
        let mut first = provider(&bridge);
        assert!(matches!(first.poll(&request, &cancel), Poll::Pending));
        let ticket = first.ticket.unwrap();
        let mut second = provider(&bridge);
        assert!(matches!(
            second.poll(&request, &Cancellation::default()),
            Poll::Ready(Err(Error::Provider))
        ));
        drop(second);
        assert_eq!(
            bridge
                .state
                .lock()
                .unwrap()
                .active
                .as_ref()
                .unwrap()
                .pending
                .as_ref()
                .unwrap()
                .ticket,
            ticket
        );
        cancel.cancel();
        assert!(matches!(
            first.poll(&request, &cancel),
            Poll::Ready(Err(Error::Cancelled))
        ));
        let mut replacement = provider(&bridge);
        assert!(matches!(
            replacement.poll(&request, &Cancellation::default()),
            Poll::Pending
        ));
        let next = replacement.ticket.unwrap();
        assert!(next > ticket);
        drop(first);
        assert_eq!(
            bridge
                .state
                .lock()
                .unwrap()
                .active
                .as_ref()
                .unwrap()
                .pending
                .as_ref()
                .unwrap()
                .ticket,
            next
        );
        drop(replacement);
        assert!(bridge.state.lock().unwrap().active.is_none());
    }
    #[test]
    fn pending_request_mutation_and_ticket_exhaustion_fail_closed() {
        let mutations: Vec<fn(&mut GenerationRequest)> = vec![
            |request| request.version += 1,
            |request| request.scope.story.push_str("-foreign"),
            |request| request.scope.branch.push_str("-foreign"),
            |request| request.turn.push_str("-foreign"),
            |request| request.revision += 1,
            |request| request.schema.push_str("-forged"),
            |request| request.model_profile.push_str("-foreign"),
            |request| request.budget.max_output_bytes -= 1,
            |request| request.budget.max_output_tokens -= 1,
            |request| request.budget.max_pending_polls += 1,
            |request| request.budget.deadline_ms += 1,
            |request| {
                if let Input::Structured { prompt, .. } = &mut request.input {
                    prompt.push_str("-forged");
                }
            },
            |request| {
                if let Input::Structured { role, .. } = &mut request.input {
                    *role = "narrator".into();
                }
            },
        ];
        for mutate in mutations {
            let bridge = bridge();
            let mut provider = provider(&bridge);
            let request = generation();
            assert!(matches!(
                provider.poll(&request, &Cancellation::default()),
                Poll::Pending
            ));
            let mut changed = request.clone();
            mutate(&mut changed);
            assert!(matches!(
                provider.poll(&changed, &Cancellation::default()),
                Poll::Ready(Err(Error::Provider))
            ));
            drop(provider);
            assert!(bridge.state.lock().unwrap().active.is_none());
        }
        let bridge = bridge();
        let mut provider = provider(&bridge);
        let mut request = generation();
        assert!(matches!(
            provider.poll(&request, &Cancellation::default()),
            Poll::Pending
        ));
        if let Input::Structured { schema, .. } = &mut request.input {
            *schema = json!({"forged":true});
        }
        assert!(matches!(
            provider.poll(&request, &Cancellation::default()),
            Poll::Ready(Err(Error::Provider))
        ));
        drop(provider);
        assert!(bridge.state.lock().unwrap().active.is_none());
        bridge.tickets.store(i64::MAX as u64, Ordering::SeqCst);
        let mut provider = super::tests::provider(&bridge);
        assert!(matches!(
            provider.poll(&generation(), &Cancellation::default()),
            Poll::Ready(Err(Error::Provider))
        ));
        assert!(bridge.state.lock().unwrap().active.is_none());
    }
    #[test]
    fn cancelled_and_closed_tickets_are_unobservable_and_cannot_accept_late_output() {
        let bridge = bridge();
        let mut provider = provider(&bridge);
        let cancel = Cancellation::default();
        assert!(matches!(
            provider.poll(&generation(), &cancel),
            Poll::Pending
        ));
        let ticket = provider.ticket.unwrap();
        assert!(!bridge.poll()["data"]["pending"].is_null());
        cancel.cancel();
        assert!(bridge.poll()["data"]["pending"].is_null());
        assert_eq!(bridge.respond(ticket, b"late")["error"], "InvalidTicket");
        bridge.close();
        assert_eq!(bridge.poll()["error"], "InvalidHandle");
        assert_eq!(bridge.respond(ticket, b"late")["error"], "InvalidHandle");
    }
}
