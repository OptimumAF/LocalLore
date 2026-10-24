// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Fixed-name atomic publication for the development model setup profile only.
//! No fallback to a replacing rename or hard link; unsupported kernels fail closed.
use jni::{
    objects::{JByteArray, JObject},
    sys::jint,
    JNIEnv,
};
use std::{
    ffi::{c_char, c_int, c_void, CString},
    fs::OpenOptions,
    os::{fd::AsRawFd, unix::fs::OpenOptionsExt},
    path::Path,
};

const RENAME_NOREPLACE: u32 = 1;
// Pinned NDK 29 Linux UAPI flags differ between the supported Android ABIs.
#[cfg(target_arch = "x86_64")]
const O_DIRECTORY: c_int = 0x10000;
#[cfg(target_arch = "x86_64")]
const O_NOFOLLOW: c_int = 0x20000;
#[cfg(target_arch = "aarch64")]
const O_DIRECTORY: c_int = 0x4000;
#[cfg(target_arch = "aarch64")]
const O_NOFOLLOW: c_int = 0x8000;
type RenameAt2 = unsafe extern "C" fn(c_int, *const c_char, c_int, *const c_char, u32) -> c_int;

#[link(name = "dl")]
extern "C" {
    fn dlsym(handle: *mut c_void, symbol: *const c_char) -> *mut c_void;
}

fn publish(root: &[u8]) -> jint {
    let Ok(root) = std::str::from_utf8(root) else {
        return 4;
    };
    let path = Path::new(root);
    if root.is_empty() || root.len() > 4096 || root.contains('\0') || !path.is_absolute() {
        return 4;
    }
    // The caller holds the import lock and validated the stage's identity and full digest.
    // Pin one canonical directory fd for both fixed child names.
    if std::fs::canonicalize(path).ok().as_deref() != Some(path)
        || !std::fs::symlink_metadata(path).is_ok_and(|metadata| metadata.is_dir())
    {
        return 4;
    }
    let Ok(directory) = OpenOptions::new()
        .read(true)
        .custom_flags(O_DIRECTORY | O_NOFOLLOW)
        .open(path)
    else {
        return 3;
    };
    if !std::fs::symlink_metadata(path.join("model.part")).is_ok_and(|metadata| metadata.is_file())
    {
        return 4;
    }
    let old = CString::new("model.part").unwrap();
    let new = CString::new("model.litertlm").unwrap();
    // Bionic's public wrapper starts at API 30. Resolve at runtime so minSdk 26 can still
    // load the library; a missing symbol fails closed without invoking a raw syscall.
    // Android's supported 64-bit ABIs define RTLD_DEFAULT as null.
    let symbol = unsafe { dlsym(std::ptr::null_mut(), c"renameat2".as_ptr()) };
    if symbol.is_null() {
        return 2;
    }
    // dlsym resolved this exact public C signature. Pointers and directory fd outlive the call.
    let rename: RenameAt2 = unsafe { std::mem::transmute(symbol) };
    let result = unsafe {
        rename(
            directory.as_raw_fd(),
            old.as_ptr(),
            directory.as_raw_fd(),
            new.as_ptr(),
            RENAME_NOREPLACE,
        )
    };
    if result == 0 {
        return 0;
    }
    match std::io::Error::last_os_error().raw_os_error() {
        Some(17) => 1, // EEXIST: any existing destination, including a dangling symlink.
        Some(22 | 38 | 95) => 2, // EINVAL, ENOSYS, EOPNOTSUPP: unsupported, no fallback.
        _ => 3,
    }
}

#[no_mangle]
pub extern "system" fn Java_org_locallore_app_NativeModelPublication_publishNoReplace(
    env: JNIEnv<'_>,
    _: JObject<'_>,
    root: JByteArray<'_>,
) -> jint {
    std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        if root.is_null() {
            return 4;
        }
        let Ok(size) = env.get_array_length(&root) else {
            return 4;
        };
        if !(1..=4096).contains(&size) {
            return 4;
        }
        match env.convert_byte_array(root) {
            Ok(bytes) => publish(&bytes),
            Err(_) => 4,
        }
    }))
    .unwrap_or(3)
}
