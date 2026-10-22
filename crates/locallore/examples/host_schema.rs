#[cfg(feature = "host")]
fn main() {
    println!(
        "{}",
        serde_json::to_string_pretty(&locallore::host::schema()).unwrap()
    );
}
#[cfg(not(feature = "host"))]
fn main() {
    eprintln!("Enable --features host to generate host-v1.schema.json");
}
