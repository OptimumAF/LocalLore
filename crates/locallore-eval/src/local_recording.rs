//! Passive bounded request/output capture around the actual production provider.
use super::*;
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub(crate) struct RawRef {
    pub file: String,
    pub sha256: String,
    pub bytes: usize,
    pub role: String,
}
#[derive(Default)]
pub(crate) struct Records {
    pub captures: Vec<Capture>,
    pub outputs: Vec<(String, Vec<u8>)>,
    pub role_metrics: Option<Value>,
    pub forbidden_narrator_prompt: bool,
    pub forbidden_narrator_output: bool,
}
pub(crate) struct Recording {
    pub state: Mutex<Records>,
    pub roles: AtomicUsize,
    pub polled: AtomicBool,
    pub lost: AtomicBool,
}
impl Default for Recording {
    fn default() -> Self {
        Self {
            state: Mutex::new(Records::default()),
            roles: AtomicUsize::new(0),
            polled: AtomicBool::new(false),
            lost: AtomicBool::new(false),
        }
    }
}
struct Identity {
    version: u16,
    scope: Scope,
    turn: String,
    revision: u64,
    profile: String,
    schema_id: String,
    bytes: usize,
    tokens: u32,
    polls: u16,
    deadline: u64,
    role: String,
    prompt: String,
    schema: Value,
}
impl Identity {
    fn matches(&self, r: &GenerationRequest, role: &str, prompt: &str, schema: &Value) -> bool {
        self.version == r.version
            && self.scope == r.scope
            && self.turn == r.turn
            && self.revision == r.revision
            && self.profile == r.model_profile
            && self.schema_id == r.schema
            && self.bytes == r.budget.max_output_bytes
            && self.tokens == r.budget.max_output_tokens
            && self.polls == r.budget.max_pending_polls
            && self.deadline == r.budget.deadline_ms
            && self.role == role
            && self.prompt == prompt
            && self.schema == *schema
    }
    fn new(r: &GenerationRequest, role: &str, prompt: &str, schema: &Value) -> Self {
        Self {
            version: r.version,
            scope: r.scope.clone(),
            turn: r.turn.clone(),
            revision: r.revision,
            profile: r.model_profile.clone(),
            schema_id: r.schema.clone(),
            bytes: r.budget.max_output_bytes,
            tokens: r.budget.max_output_tokens,
            polls: r.budget.max_pending_polls,
            deadline: r.budget.deadline_ms,
            role: role.into(),
            prompt: prompt.into(),
            schema: schema.clone(),
        }
    }
}
pub(crate) struct RecordingProvider {
    inner: Option<Box<dyn InferenceProvider + Send>>,
    state: Arc<Recording>,
    targets: Vec<Target>,
    forbidden: Vec<String>,
    identity: Option<Identity>,
    terminal_recorded: bool,
    #[cfg(feature = "local-model")]
    native_log: Option<locallore_local_runtime::RoleMetricsLog>,
}
impl RecordingProvider {
    pub fn new(
        inner: Box<dyn InferenceProvider + Send>,
        state: Arc<Recording>,
        targets: Vec<Target>,
        forbidden: Vec<String>,
    ) -> Self {
        Self {
            inner: Some(inner),
            state,
            targets,
            forbidden,
            identity: None,
            terminal_recorded: false,
            #[cfg(feature = "local-model")]
            native_log: None,
        }
    }
    #[cfg(feature = "local-model")]
    pub fn with_native_log(mut self, log: locallore_local_runtime::RoleMetricsLog) -> Self {
        self.native_log = Some(log);
        self
    }
    fn capture(&self, r: &GenerationRequest, role: &str, prompt: &str, schema: &Value) {
        let input = if role == "director" {
            prompt.split_once("Context data: ").and_then(|(_, s)| {
                Value::deserialize(&mut serde_json::Deserializer::from_str(s)).ok()
            })
        } else {
            None
        };
        let present = self
            .targets
            .iter()
            .map(|target| {
                input
                    .as_ref()
                    .and_then(|v| v["context"]["records"].as_array())
                    .is_some_and(|records| {
                        records.iter().any(|record| {
                            record["kind"] == target.kind
                                && record.to_string().contains(&target.contains)
                                && contains_json(record, &target.source)
                        })
                    })
            })
            .collect();
        let capture = Capture {
            turn: r.turn.clone(),
            role: role.into(),
            prompt_sha256: digest(prompt.as_bytes()),
            schema_sha256: digest(&serde_json::to_vec(schema).unwrap_or_default()),
            compiler_version: input
                .as_ref()
                .and_then(|v| v["context"]["compiler_version"].as_u64()),
            player_text_sha256: input
                .as_ref()
                .and_then(|v| v["player_text"].as_str())
                .map(|s| digest(s.as_bytes())),
            prompt_targets: self.targets.clone(),
            prompt_targets_present: present,
        };
        match self.state.state.try_lock() {
            Ok(mut records) => {
                if records.captures.len() < 3 {
                    records.captures.push(capture);
                } else {
                    self.state.lost.store(true, Ordering::Relaxed);
                }
                if role == "narrator" && self.forbidden.iter().any(|v| prompt.contains(v)) {
                    records.forbidden_narrator_prompt = true;
                }
            }
            Err(_) => self.state.lost.store(true, Ordering::Relaxed),
        }
    }
}
impl InferenceProvider for RecordingProvider {
    fn poll(
        &mut self,
        r: &GenerationRequest,
        cancel: &Cancellation,
    ) -> Poll<std::result::Result<Vec<u8>, Error>> {
        let Input::Structured {
            role,
            prompt,
            schema,
        } = &r.input
        else {
            return Poll::Ready(Err(Error::Provider));
        };
        if !self
            .identity
            .as_ref()
            .is_some_and(|id| id.matches(r, role, prompt, schema))
        {
            if self
                .state
                .roles
                .fetch_update(Ordering::Relaxed, Ordering::Relaxed, |n| {
                    (n < 3).then_some(n + 1)
                })
                .is_err()
            {
                return Poll::Ready(Err(Error::TooLarge));
            }
            self.capture(r, role, prompt, schema);
            self.identity = Some(Identity::new(r, role, prompt, schema));
            self.terminal_recorded = false;
        }
        self.state.polled.store(true, Ordering::Release);
        let result = self.inner.as_mut().unwrap().poll(r, cancel);
        if let Poll::Ready(Ok(bytes)) = &result {
            if !self.terminal_recorded {
                self.terminal_recorded = true;
                if bytes.len() <= 16_384 {
                    match self.state.state.try_lock() {
                        Ok(mut records) => {
                            if records.outputs.len() < 3 {
                                records.outputs.push((role.clone(), bytes.clone()));
                            } else {
                                self.state.lost.store(true, Ordering::Relaxed);
                            }
                            if role == "narrator"
                                && self
                                    .forbidden
                                    .iter()
                                    .any(|v| String::from_utf8_lossy(bytes).contains(v))
                            {
                                records.forbidden_narrator_output = true;
                            }
                        }
                        Err(_) => self.state.lost.store(true, Ordering::Relaxed),
                    }
                } else {
                    self.state.lost.store(true, Ordering::Relaxed);
                }
            }
        }
        result
    }
}
impl Drop for RecordingProvider {
    fn drop(&mut self) {
        drop(self.inner.take()); // The same production provider drains/reaps before snapshot.
        #[cfg(feature = "local-model")]
        if let Some(log) = &self.native_log {
            let value = serde_json::to_value(log.snapshot()).ok();
            if let Ok(mut state) = self.state.state.try_lock() {
                state.role_metrics = value;
            } else {
                self.state.lost.store(true, Ordering::Relaxed);
            }
        }
    }
}
