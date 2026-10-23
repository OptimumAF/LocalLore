// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Development-only fixed synthetic fixture. Absent from ordinary Android builds.
use jni::{
    objects::{JClass, JString},
    sys::jstring,
    JNIEnv,
};
use serde_json::json;
use std::path::Path;

fn bounded(env: &mut JNIEnv<'_>, value: JString<'_>, cap: usize) -> Option<String> {
    if value.is_null() {
        return None;
    }
    let length = env
        .call_method(&value, "length", "()I", &[])
        .ok()?
        .i()
        .ok()?;
    if length < 1 || length as usize > cap {
        return None;
    }
    let text: String = env.get_string(&value).ok()?.into();
    (text.len() <= cap).then_some(text)
}

#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchiveCapacityFixture_run(
    mut env: JNIEnv<'_>,
    _: JClass<'_>,
    root: JString<'_>,
    mode: JString<'_>,
) -> jstring {
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let root = bounded(&mut env, root, 4096).ok_or("FixtureInput".to_owned())?;
        let mode = bounded(&mut env, mode, 32).ok_or("FixtureInput".to_owned())?;
        locallore_storage::archive_capacity_fixture::run(Path::new(&root), &mode)
    }))
    .unwrap_or_else(|_| Err("FixturePanic".into()));
    let result = match result {
        Ok(value) => value,
        // Native fixture errors are fixed categories, never paths, SQL or private values.
        Err(error) if error.len() <= 64 && error.bytes().all(|b| b.is_ascii_alphanumeric()) => {
            json!({"version":1,"status":"error","error":error})
        }
        Err(_) => json!({"version":1,"status":"error","error":"FixtureFailure"}),
    }
    .to_string();
    if env.exception_check().unwrap_or(true) || result.len() > 4096 {
        return std::ptr::null_mut();
    }
    env.new_string(result)
        .map_or(std::ptr::null_mut(), JString::into_raw)
}
