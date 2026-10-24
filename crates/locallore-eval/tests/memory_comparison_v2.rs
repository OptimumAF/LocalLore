//! Protocol2 pure binding oracles. Existing protocol1 remains an immutable refusal.
use locallore::{contracts::*,engine::Engine};
use locallore_eval::{memory_comparison as old,memory_comparison_v2::*};
#[test]
fn original_protocol_stays_refused_and_frozen_scenario_punctuation_is_reused() {
 let suite=old::frozen_suite().unwrap();assert_eq!(suite.steps().len(),24);
 for p in [old::HistoryPolicy::StateRecentTranscriptV1,old::HistoryPolicy::StateRelevantMemoryV1] {
  assert_eq!(old::require_execution(p),Err(old::ProtocolError::UnsupportedPolicy));
 }
 let expected:Vec<_>=suite.steps().iter().map(|s|(s.id().to_owned(),s.text().to_owned())).collect();
 assert_eq!(suite_identity().unwrap().turns,expected);
 assert_eq!(suite_identity().unwrap().sha256,suite.sha256().unwrap());
}
#[test]
fn semantic_input_is_actual_canon_request_not_policy_or_profile_metadata() {
 let suite=old::frozen_suite().unwrap();let e=Engine::new(suite.seed().clone()).unwrap();
 let r=suite.steps()[0].request(&e);
 assert_eq!(semantic_input(&e,&r).unwrap(),semantic_input(&e.clone(),&r).unwrap());
 let mut other=r.clone();if let Intent::FreeText{text,..}=&mut other.intent {text.push(' ');}
 assert_ne!(semantic_input(&e,&r).unwrap(),semantic_input(&e,&other).unwrap());
 other=r.clone();other.scope.story="foreign".into();assert!(semantic_input(&e,&other).is_err());
 other=r.clone();other.expected_revision=1;assert!(semantic_input(&e,&other).is_err());
}
#[test]
fn source_binding_requires_closed_current_tuple_and_actual_policies() {
 let b=current_binding(false).unwrap();
 assert_eq!(b.protocol_version,2);assert_eq!(b.prompt_version,"locallore-play-v2.5");
 assert_eq!(b.compiler_version,2);assert_eq!(b.context_version,2);
 assert_eq!(b.narration_policy,"grounded-prose-v2.2");
 assert_eq!(b.policies.len(),2);assert_ne!(b.policies[0],b.policies[1]);
 assert_eq!(b.max_admissions,32);assert_eq!(b.max_roles,96);assert_eq!(b.max_active_ms,1_800_000);
 assert_eq!(b.attempts,24);assert_eq!(b.expected_accepted,21);assert_eq!(b.expected_guard_only,3);
}
