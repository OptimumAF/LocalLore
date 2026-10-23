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
