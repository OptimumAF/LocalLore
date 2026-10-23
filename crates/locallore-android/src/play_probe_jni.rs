// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! JNI for the explicitly enabled development harness. Every Java value is borrowed per call.
use crate::play_probe::{error_bytes, ProbeRegistry, MAX_PROFILE, MAX_RESPONSE};
use jni::{
    objects::{JByteArray, JClass, JString},
    sys::{jbyteArray, jlong},
    JNIEnv,
};
use locallore::host::MAX_INPUT;
use std::{path::Path, sync::OnceLock};

static REGISTRY: OnceLock<ProbeRegistry> = OnceLock::new();
fn registry() -> &'static ProbeRegistry {
    REGISTRY.get_or_init(ProbeRegistry::default)
}
fn input(env: &JNIEnv<'_>, input: JByteArray<'_>, cap: usize) -> Result<Vec<u8>, &'static str> {
    if input.is_null() {
        return Err("Malformed");
    }
    let size = env.get_array_length(&input).map_err(|_| "Malformed")?;
    if size as usize > cap {
        return Err("TooLarge");
    }
    env.convert_byte_array(input).map_err(|_| "Malformed")
}
fn output(env: &JNIEnv<'_>, bytes: &[u8]) -> jbyteArray {
    // JNI failure may leave an exception pending. Preserve it without further allocation.
    if env.exception_check().unwrap_or(true) {
        return std::ptr::null_mut();
    }
    env.byte_array_from_slice(bytes)
        .map_or(std::ptr::null_mut(), |array| array.into_raw())
}
fn guarded(operation: impl FnOnce() -> Vec<u8>) -> Vec<u8> {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(operation))
        .unwrap_or_else(|_| error_bytes("Internal"))
}

#[no_mangle]
pub extern "system" fn Java_org_locallore_runtimebench_litert_NativePlayProbe_open(
    mut env: JNIEnv<'_>,
    _: JClass<'_>,
    path: JString<'_>,
    profile: JByteArray<'_>,
) -> jlong {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let profile = input(&env, profile, MAX_PROFILE).ok()?;
        if path.is_null() {
            return None;
        }
        let path: String = env.get_string(&path).ok()?.into();
        if path.len() > 4096 || !Path::new(&path).is_absolute() {
            return None;
        }
        registry()
            .open(Path::new(&path), &profile)
            .ok()
            .map(|handle| handle as jlong)
    }))
    .ok()
    .flatten()
    .unwrap_or(0)
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_runtimebench_litert_NativePlayProbe_call(
    env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
    envelope: JByteArray<'_>,
) -> jbyteArray {
    let bytes = guarded(|| match input(&env, envelope, MAX_INPUT) {
        Ok(bytes) => registry().call(handle as u64, &bytes),
        Err(error) => error_bytes(error),
    });
    output(&env, &bytes)
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_runtimebench_litert_NativePlayProbe_poll(
    env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
) -> jbyteArray {
    output(&env, &guarded(|| registry().poll(handle as u64)))
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_runtimebench_litert_NativePlayProbe_respond(
    env: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
    ticket: jlong,
    untrusted: JByteArray<'_>,
) -> jbyteArray {
    let bytes = guarded(|| {
        if ticket <= 0 {
            return error_bytes("InvalidTicket");
        }
        match input(&env, untrusted, MAX_RESPONSE) {
            Ok(bytes) => registry().respond(handle as u64, ticket as u64, &bytes),
            Err(error) => error_bytes(error),
        }
    });
    output(&env, &bytes)
}
#[no_mangle]
pub extern "system" fn Java_org_locallore_runtimebench_litert_NativePlayProbe_close(
    _: JNIEnv<'_>,
    _: JClass<'_>,
    handle: jlong,
) {
    let _ = std::panic::catch_unwind(|| registry().close(handle as u64));
}
