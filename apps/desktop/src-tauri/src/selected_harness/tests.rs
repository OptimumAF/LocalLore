// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Pure fixture guards only; SOURCE UNCOMPILED/UNRUN, no app or model proof.
use super::*;

fn path() -> std::path::PathBuf {
    std::env::temp_dir()
        .join("comparison-reader-native-00000000-0000-0000-0000-000000000001")
        .join("stories-v1.sqlite")
}
#[test]
fn workspace_requires_exact_native_env_identity_and_existing_fixture_layout() {
    let good = path();
    assert_eq!(
        workspace_parent(&good, Some(&good)).unwrap(),
        good.parent().unwrap()
    );
    assert_eq!(workspace_parent(&good, None).unwrap_err(), "Forbidden");
    let other = good.with_file_name("other.sqlite");
    assert_eq!(
        workspace_parent(&good, Some(&other)).unwrap_err(),
        "Forbidden"
    );
    for bad in [
        std::path::PathBuf::from(
            "comparison-reader-native-00000000-0000-0000-0000-000000000001/stories-v1.sqlite",
        ),
        good.with_file_name("other.sqlite"),
        std::env::temp_dir().join("comparison-reader-native-not-an-id/stories-v1.sqlite"),
        std::env::temp_dir().join("ordinary-user-story/stories-v1.sqlite"),
        good.parent().unwrap().join("..").join("stories-v1.sqlite"),
    ] {
        assert_eq!(
            workspace_parent(&bad, Some(&bad)).unwrap_err(),
            "SyntheticWorkspaceRequired"
        );
    }
}
#[test]
fn consent_accepts_only_bounded_native_shared_metadata_kinds() {
    // Source-shaped synthetic metadata, not an executed Core/native fixture.
    for kind in ["selected_prepared", "selected_read"] {
        assert!(metadata_kind(&json!({"version":1,"kind":kind})).is_ok());
    }
    for bad in [
        json!(null),
        json!([]),
        json!({"version":2,"kind":"selected_prepared"}),
        json!({"version":1,"kind":"comparison_reader"}),
        json!({"version":1,"kind":"selected_diagnostics"}),
        json!({"version":1,"kind":"selected_prepared","padding":"x".repeat(16*1024)}),
    ] {
        assert!(metadata_kind(&bad).is_err());
    }
}
#[test]
fn closed_scenarios_change_only_declared_synthetic_flags() {
    let state = SelectedHarness::default();
    assert!(!state.hold.load(Ordering::SeqCst));
    assert!(finish_consent(&state));
    apply(&state, Scenario::DenyConsent);
    assert!(!finish_consent(&state));
    assert!(finish_consent(&state));
    let reply = apply(&state, Scenario::HoldConsent);
    assert_eq!(reply["synthetic"], true);
    assert_eq!(reply["kind"], "selected_fixture");
    assert!(state.hold.load(Ordering::SeqCst));
    apply(&state, Scenario::ReleaseConsent);
    assert!(!state.hold.load(Ordering::SeqCst));
    apply(&state, Scenario::LoseStartAck);
    assert!(consume_lost_ack(&state));
    assert!(!consume_lost_ack(&state));
    for bad in [
        "prepare",
        "seed",
        "run",
        "shell",
        "path",
        "hold-runtime",
        "fail-inference",
        "",
    ] {
        assert!(scenario(bad).is_err());
    }
    for valid in [
        "hold-consent",
        "release-consent",
        "deny-consent",
        "lose-start-ack",
    ] {
        assert!(scenario(valid).is_ok());
    }
}
