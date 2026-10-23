// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Bounded per-call JNI copies only. No Java reference, callback or native thread is retained.
use crate::archive::{error_bytes, ArchiveRegistry, MAX_CONTROL_BYTES};
use jni::{
    objects::{JByteArray, JClass, JString},
    sys::{jbyteArray, jlong},
    JNIEnv,
};
use locallore_storage::playable_archive::MAX_ARCHIVE_BYTES;
use std::{path::Path, sync::OnceLock};
static REGISTRY: OnceLock<ArchiveRegistry> = OnceLock::new();
fn registry() -> &'static ArchiveRegistry {
    REGISTRY.get_or_init(ArchiveRegistry::default)
}
fn input(env: &JNIEnv<'_>, array: JByteArray<'_>, cap: usize) -> Result<Vec<u8>, &'static str> {
    if array.is_null() {
        return Err("Malformed");
    }
    let size = env.get_array_length(&array).map_err(|_| "Malformed")?;
    if size as usize > cap {
        return Err("TooLarge");
    }
    env.convert_byte_array(array).map_err(|_| "Malformed")
}
fn output(env: &JNIEnv<'_>, bytes: &[u8]) -> jbyteArray {
    if env.exception_check().unwrap_or(true) {
        return std::ptr::null_mut();
    }
    env.byte_array_from_slice(bytes)
        .map_or(std::ptr::null_mut(), |array| array.into_raw())
}
fn path(env: &mut JNIEnv<'_>, value: JString<'_>) -> Option<String> {
    if value.is_null() {
        return None;
    }
    // Bound UTF-16 units before converting/copying Java string contents.
    let units = env
        .call_method(&value, "length", "()I", &[])
        .ok()?
        .i()
        .ok()?;
    if !(1..=4096).contains(&units) {
        return None;
    }
    let value: String = env.get_string(&value).ok()?.into();
    (value.len() <= 4096 && Path::new(&value).is_absolute()).then_some(value)
}
fn guarded(operation: impl FnOnce() -> Vec<u8>) -> Vec<u8> {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(operation))
        .unwrap_or_else(|_| error_bytes("Internal"))
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_open(
    mut env: JNIEnv<'_>,
    _: JClass<'_>,
    database: JString<'_>,
    staging: JString<'_>,
) -> jlong {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let database = path(&mut env, database)?;
        let staging = path(&mut env, staging)?;
        registry()
            .open(Path::new(&database), Path::new(&staging))
            .ok()
            .map(|handle| handle as jlong)
    }))
    .ok()
    .flatten()
    .unwrap_or(0)
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_prepareExport(
    env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
    request: JByteArray<'_>,
) -> jbyteArray {
    let bytes = guarded(|| match input(&env, request, MAX_CONTROL_BYTES) {
        Ok(bytes) => registry().prepare_export(handle as u64, &bytes),
        Err(error) => registry().reject_prepare(handle as u64, error),
    });
    output(&env, &bytes)
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_prepareImport(
    env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
    archive: JByteArray<'_>,
) -> jbyteArray {
    let bytes = guarded(|| match input(&env, archive, MAX_ARCHIVE_BYTES) {
        Ok(bytes) => registry().prepare_import(handle as u64, &bytes),
        Err(error) => registry().reject_prepare(handle as u64, error),
    });
    output(&env, &bytes)
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_exportBytes(
    mut env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
    token: jlong,
) -> jbyteArray {
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        registry().export_bytes(handle as u64, token as u64)
    }))
    .unwrap_or_else(|_| Err("Internal".into()));
    match result {
        Ok(bytes) => output(&env, &bytes),
        Err(error) => {
            if !env.exception_check().unwrap_or(true) {
                let _ = env.throw_new("java/lang/IllegalStateException", error);
            }
            std::ptr::null_mut()
        }
    }
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_commitImport(
    env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
    token: jlong,
) -> jbyteArray {
    output(
        &env,
        &guarded(|| registry().commit_import(handle as u64, token as u64)),
    )
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_cancel(
    _: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
) {
    let _ = std::panic::catch_unwind(|| registry().cancel(handle as u64));
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeArchive_close(
    _: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
) {
    let _ = std::panic::catch_unwind(|| registry().close(handle as u64));
}
