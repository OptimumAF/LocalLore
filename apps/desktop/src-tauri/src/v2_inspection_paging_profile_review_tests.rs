// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Independent profile-path FIRST at 33e85a38. SOURCE ONLY / UNREGISTERED /
//! UNCOMPILED / UNRUN. Missing helper/registration/admission is SETUP_UNRUN.
//! Windows physical D only, no temporary fallback or environment mutation.
//! At most seven tiny packet roots plus two padding ancestors, <=1KiB payload,
//! all retained under the admitted D05 base. No SQLite, fixture producer, model,
//! WebView, link/reparse creation, OS isolation probe or failure-cause claim.
//! These tests do not establish a remedy for the observed WebView HRESULT.
use super::webview_profile;
use std::{
    ffi::OsString,
    fs::{self, OpenOptions},
    io::Write,
    path::{Path, PathBuf},
};

fn admitted_base() -> PathBuf {
    const {
        assert!(
            cfg!(windows),
            "SETUP_UNRUN: Windows physical D profile tests only"
        )
    };
    let base = PathBuf::from(
        std::env::var_os("LOCALLORE_D05_ARTIFACT_ROOT")
            .expect("SETUP_UNRUN: coordinator must admit an existing D05 base"),
    );
    assert!(
        base.is_absolute() && base.is_dir(),
        "SETUP_UNRUN: existing absolute base"
    );
    let base = fs::canonicalize(base).unwrap();
    #[cfg(windows)]
    {
        use std::path::{Component, Prefix};
        assert!(
            matches!(base.components().next(), Some(Component::Prefix(prefix))
            if matches!(prefix.kind(), Prefix::Disk(d) | Prefix::VerbatimDisk(d)
                if d.eq_ignore_ascii_case(&b'D'))),
            "SETUP_UNRUN: physical D base"
        );
        use std::os::windows::fs::MetadataExt;
        for ancestor in base.ancestors() {
            let metadata = fs::symlink_metadata(ancestor).unwrap();
            assert!(metadata.is_dir() && !metadata.file_type().is_symlink());
            assert_eq!(metadata.file_attributes() & 0x400, 0);
        }
    }
    base
}
fn unique() -> String {
    crate::exports::identifier().unwrap()
}
fn packet_at(base: &Path, name: String) -> (PathBuf, PathBuf) {
    let packet = base.join(name);
    fs::create_dir(&packet).unwrap();
    let workspace = packet.join(format!("d05-v2-inspector-paging-native-{}", unique()));
    fs::create_dir(&workspace).unwrap();
    (packet, workspace.join("stories-v1.sqlite"))
}
fn packet() -> (PathBuf, PathBuf) {
    let pair = packet_at(&admitted_base(), format!("p-{}", unique()));
    assert!(
        units(&pair.0.join("webview-profile")) <= 190,
        "SETUP_UNRUN: admitted base must allow the short positive profile"
    );
    pair
}
fn units(path: &Path) -> usize {
    path.to_str().unwrap().encode_utf16().count()
}
fn names(path: &Path) -> Vec<OsString> {
    let mut result = fs::read_dir(path)
        .unwrap()
        .map(|entry| entry.unwrap().file_name())
        .collect::<Vec<_>>();
    result.sort();
    result
}
fn absent(path: &Path) {
    assert_eq!(
        fs::symlink_metadata(path).unwrap_err().kind(),
        std::io::ErrorKind::NotFound
    );
}
fn write_new(path: &Path, value: &[u8]) {
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(path)
        .unwrap();
    file.write_all(value).unwrap();
    file.sync_all().unwrap();
}
fn refused(path: &Path) {
    assert_eq!(
        webview_profile(path),
        Err("SyntheticWorkspaceRequired".into())
    );
}

#[test]
fn short_profile_is_exact_packet_sibling_and_validation_creates_nothing() {
    let (packet, workspace) = packet();
    let expected = packet.join("webview-profile");
    let parent = workspace.parent().unwrap();
    let before_packet = names(&packet);
    let before_workspace = names(parent);
    absent(&workspace);
    absent(&expected);
    assert_eq!(webview_profile(&workspace).unwrap(), expected);
    assert_eq!(names(&packet), before_packet);
    assert_eq!(names(parent), before_workspace);
    absent(&workspace);
    absent(&expected);
    assert_ne!(expected.parent(), workspace.parent());
    assert_eq!(expected.parent(), workspace.parent().and_then(Path::parent));
    // The guard validates paths, not database content; this is a tiny ordinary
    // file control, not a SQLite fixture or successful application startup.
    write_new(&workspace, b"profile-path-control");
    let before_packet = names(&packet);
    let before_workspace = names(parent);
    assert_eq!(webview_profile(&workspace).unwrap(), expected);
    assert_eq!(fs::read(&workspace).unwrap(), b"profile-path-control");
    assert_eq!(names(&packet), before_packet);
    assert_eq!(names(parent), before_workspace);
    absent(&expected);
}

#[test]
fn existing_profile_file_refuses_without_repair_or_workspace_creation() {
    let (packet, workspace) = packet();
    let profile = packet.join("webview-profile");
    write_new(&profile, b"retained-profile-file");
    let before_packet = names(&packet);
    let before_workspace = names(workspace.parent().unwrap());
    refused(&workspace);
    assert_eq!(fs::read(&profile).unwrap(), b"retained-profile-file");
    assert_eq!(names(&packet), before_packet);
    assert_eq!(names(workspace.parent().unwrap()), before_workspace);
    absent(&workspace);
}

#[test]
fn existing_profile_directory_refuses_without_repair_or_workspace_creation() {
    let (packet, workspace) = packet();
    let profile = packet.join("webview-profile");
    fs::create_dir(&profile).unwrap();
    write_new(&profile.join("retained.txt"), b"retained");
    let before_packet = names(&packet);
    let before_profile = names(&profile);
    refused(&workspace);
    assert_eq!(names(&packet), before_packet);
    assert_eq!(names(&profile), before_profile);
    assert_eq!(fs::read(profile.join("retained.txt")).unwrap(), b"retained");
    absent(&workspace);
}

#[test]
fn wrong_packet_workspace_leaf_raw_dot_and_nonunicode_refuse_without_writes() {
    let (packet, workspace) = packet();
    let before = names(&packet);
    refused(&workspace.with_file_name("other.sqlite"));
    let dot = PathBuf::from(format!(
        "{}\\.\\stories-v1.sqlite",
        workspace.parent().unwrap().display()
    ));
    refused(&dot);
    #[cfg(windows)]
    {
        use std::os::windows::ffi::OsStringExt;
        let mut raw = workspace.parent().unwrap().as_os_str().to_os_string();
        raw.push("\\");
        raw.push(OsString::from_wide(&[0xd800]));
        raw.push("\\stories-v1.sqlite");
        refused(Path::new(&raw));
    }
    assert_eq!(names(&packet), before);
    absent(&workspace);
    absent(&packet.join("webview-profile"));
    let (wrong, wrong_workspace) = packet_at(&admitted_base(), format!("q-{}", unique()));
    let before = names(&wrong);
    refused(&wrong_workspace);
    assert_eq!(names(&wrong), before);
    absent(&wrong_workspace);
    absent(&wrong.join("webview-profile"));
}

#[test]
fn profile_limit_counts_utf16_units_with_exact190_and191_unicode_boundaries() {
    let base = admitted_base();
    for target in [190usize, 191] {
        let packet_name = format!("p-{}", unique());
        let trial = base.join("x").join(&packet_name).join("webview-profile");
        let padding = target
            .checked_sub(units(&trial) - 1)
            .expect("SETUP_UNRUN: admitted D05 base too long for boundary");
        assert!(
            (3..=200).contains(&padding),
            "SETUP_UNRUN: ordinary bounded padding component required"
        );
        // One supplementary scalar occupies TWO UTF16 units. A chars() or
        // UTF8-byte cap would misclassify at least one of these exact cases.
        let material = unique().replace('-', "").repeat(7);
        let parent = base.join(format!("😀{}", &material[..padding - 2]));
        fs::create_dir(&parent).unwrap();
        let (packet, workspace) = packet_at(&parent, packet_name);
        let expected = packet.join("webview-profile");
        assert_eq!(units(&expected), target);
        let before_packet = names(&packet);
        let before_workspace = names(workspace.parent().unwrap());
        if target == 190 {
            assert_eq!(webview_profile(&workspace).unwrap(), expected);
        } else {
            refused(&workspace);
        }
        assert_eq!(names(&packet), before_packet);
        assert_eq!(names(workspace.parent().unwrap()), before_workspace);
        absent(&workspace);
        absent(&expected);
    }
}
