fn main() {
    // tauri-winres 0.3.7 canonicalizes paths then escapes apostrophes for RC.EXE,
    // which treats that escape literally. Copy only the public build icon to a
    // fresh temporary directory; gameplay data never enters this path.
    let temporary = std::env::temp_dir().join(format!("locallore-d01-icon-{}", std::process::id()));
    std::fs::create_dir(&temporary).expect("fresh icon build directory");
    let icon = temporary.join("icon.ico");
    std::fs::write(&icon, include_bytes!("icons/icon.ico")).expect("public icon copy");
    let result = tauri_build::try_build(
        tauri_build::Attributes::new()
            .windows_attributes(tauri_build::WindowsAttributes::new().window_icon_path(&icon))
            .app_manifest(tauri_build::AppManifest::new().commands(&[
                "host_call",
                "author_context",
                "author_prepare_start",
                "author_commit_start",
                "author_lookup_start",
                "author_preview_discard",
                "harness_author_case",
                "capture_preview",
                "capture_save",
                "capture_revoke",
                "harness_capture_case",
                "archive_catalog",
                "fork_start",
                "fork_lookup",
                "memory_maintenance_start",
                "harness_memory_case",
                "harness_fork_case",
                "archive_export_preview",
                "archive_import_preview",
                "archive_export",
                "archive_import",
                "archive_status",
                "archive_cancel",
                "archive_discard",
                "harness_archive_case",
                "evaluation_catalog",
                "evaluation_curated",
                "evaluation_start",
                "evaluation_open",
                "evaluation_status",
                "evaluation_read",
                "evaluation_cancel",
                "evaluation_resume",
                "evaluation_rerun",
                "harness_evaluation_case",
                "model_status",
                "model_import",
                "model_load",
                "model_unload",
                "model_cancel",
                "inspection_preview",
                "inspection_database_preview",
                "inspection_save",
                "inspection_cancel",
                "inspection_open",
                "inspection_storage",
                "inspection_load",
                "harness_export_case",
                "harness_model_case",
                "harness_checkpoint",
                "harness_viewport",
                "harness_finish",
                "harness_stats",
                "harness_oracle",
                "harness_reopen",
            ])),
    );
    std::fs::remove_file(&icon).expect("remove public icon copy");
    std::fs::remove_dir(&temporary).expect("remove empty build directory");
    result.expect("Tauri build");
}
