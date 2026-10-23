// Bind checkpoint interpretation to public shared source and dependency locks at build time.
// No Git commands, arbitrary paths, model files or user workspaces are opened.
use std::{collections::BTreeSet, env, fs, path::Path};
fn collect(directory: &Path, files: &mut BTreeSet<std::path::PathBuf>) {
    println!("cargo:rerun-if-changed={}", directory.display());
    for entry in fs::read_dir(directory).expect("public source directory") {
        let path = entry.expect("source entry").path();
        let meta = fs::symlink_metadata(&path).expect("source metadata");
        assert!(!meta.file_type().is_symlink(), "source links unsupported");
        if meta.is_dir() {
            collect(&path, files);
        } else if matches!(
            path.extension().and_then(|e| e.to_str()),
            Some("rs" | "sql")
        ) {
            files.insert(path);
        }
    }
}
fn main() {
    let manifest = std::path::PathBuf::from(env::var_os("CARGO_MANIFEST_DIR").unwrap());
    let root = manifest.parent().unwrap().parent().unwrap();
    let mut files = BTreeSet::new();
    for package in [
        "locallore",
        "locallore-storage",
        "locallore-workspace",
        "locallore-eval",
    ] {
        let package = root.join("crates").join(package);
        collect(&package.join("src"), &mut files);
        files.insert(package.join("Cargo.toml"));
    }
    collect(
        &root.join("crates/locallore-storage/migrations"),
        &mut files,
    );
    for path in [
        "Cargo.toml",
        "Cargo.lock",
        "rust-toolchain.toml",
        "fixtures/lantern_quay.json",
        "fixtures/eval/reference-v1.json",
        "crates/locallore-eval/Cargo.lock",
        "crates/locallore-eval/build.rs",
    ] {
        files.insert(root.join(path));
    }
    let mut generated = String::from("const SOURCE_INPUTS: &[(&str, &[u8])] = &[\n");
    for path in files {
        println!("cargo:rerun-if-changed={}", path.display());
        assert!(
            fs::metadata(&path).unwrap().len() <= 4 * 1024 * 1024,
            "source budget"
        );
        let relative = path
            .strip_prefix(root)
            .unwrap()
            .to_str()
            .unwrap()
            .replace('\\', "/");
        generated.push_str(&format!(
            "({relative:?}, include_bytes!({:?})),\n",
            path.to_str().unwrap()
        ));
    }
    generated.push_str("];\n");
    fs::write(
        std::path::PathBuf::from(env::var_os("OUT_DIR").unwrap()).join("source_inputs.rs"),
        generated,
    )
    .unwrap();
}
