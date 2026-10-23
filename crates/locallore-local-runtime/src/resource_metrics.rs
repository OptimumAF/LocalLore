// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Private, opt-in observations of the already-owned worker. No PID lookup or process control.
use serde::Serialize;
use std::process::Child;
#[cfg(windows)]
use std::time::Duration;

pub const RESOURCE_SAMPLE_INTERVAL_MS: u64 = 250;
#[cfg(windows)]
const MAX_SAMPLES: u16 = 262;
#[cfg(windows)]
const MAX_DURATION: Duration = Duration::from_secs(65);

#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ResourceStatus {
    Sampled,
    Partial,
    Unavailable,
    Unsupported,
}
#[derive(Clone, Copy, Debug, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ResourceError {
    HandleUnavailable,
    SamplerUnavailable,
    QueryFailed,
    SamplerFailed,
    Unsupported,
}
#[derive(Clone, Debug, PartialEq, Eq, Serialize)]
pub struct ResourceMetrics {
    pub status: ResourceStatus,
    pub error: Option<ResourceError>,
    pub sample_interval_ms: u64,
    pub successful_samples: u16,
    pub failed_samples: u16,
    pub observed_ms: u64,
    /// Maximum sampled resident working set. A lower bound, not the exact role peak.
    pub sampled_peak_working_set_bytes: Option<u64>,
    /// Maximum sampled private committed bytes, NOT private working set or resident bytes.
    pub sampled_peak_private_committed_bytes: Option<u64>,
    /// Historical high-water mark since worker creation, potentially predating this role/story.
    pub process_lifetime_peak_working_set_bytes: Option<u64>,
    pub limit_reached: bool,
}
impl ResourceMetrics {
    fn unavailable(error: ResourceError) -> Self {
        Self {
            status: if error == ResourceError::Unsupported {
                ResourceStatus::Unsupported
            } else {
                ResourceStatus::Unavailable
            },
            error: Some(error),
            sample_interval_ms: RESOURCE_SAMPLE_INTERVAL_MS,
            successful_samples: 0,
            failed_samples: 0,
            observed_ms: 0,
            sampled_peak_working_set_bytes: None,
            sampled_peak_private_committed_bytes: None,
            process_lifetime_peak_working_set_bytes: None,
            limit_reached: false,
        }
    }
}

#[cfg(windows)]
mod windows {
    use super::*;
    use std::{
        ffi::c_void,
        os::windows::io::{AsHandle, AsRawHandle, OwnedHandle},
        sync::mpsc::{self, Receiver, SyncSender},
        thread::{self, JoinHandle},
        time::Instant,
    };
    #[repr(C)]
    #[derive(Default)]
    struct MemoryCounters {
        cb: u32,
        page_fault_count: u32,
        peak_working_set_size: usize,
        working_set_size: usize,
        quota_peak_paged_pool_usage: usize,
        quota_paged_pool_usage: usize,
        quota_peak_non_paged_pool_usage: usize,
        quota_non_paged_pool_usage: usize,
        pagefile_usage: usize,
        peak_pagefile_usage: usize,
        private_usage: usize,
    }
    #[link(name = "kernel32")]
    unsafe extern "system" {
        fn K32GetProcessMemoryInfo(
            process: *mut c_void,
            counters: *mut MemoryCounters,
            cb: u32,
        ) -> i32;
    }
    #[derive(Clone, Copy)]
    struct Sample {
        working_set: u64,
        private_committed: u64,
        lifetime_peak: u64,
    }
    fn query(handle: *mut c_void) -> Option<Sample> {
        let mut counters = MemoryCounters {
            cb: std::mem::size_of::<MemoryCounters>() as u32,
            ..Default::default()
        };
        // SAFETY: only the retained owned child handle is supplied in production. The stack
        // buffer has the official PROCESS_MEMORY_COUNTERS_EX layout and advertised size.
        let ok = unsafe {
            K32GetProcessMemoryInfo(
                handle,
                &mut counters,
                std::mem::size_of::<MemoryCounters>() as u32,
            )
        };
        (ok != 0).then_some(Sample {
            working_set: counters.working_set_size as u64,
            private_committed: counters.private_usage as u64,
            lifetime_peak: counters.peak_working_set_size as u64,
        })
    }
    fn observe(metrics: &mut ResourceMetrics, sample: Option<Sample>) {
        if let Some(sample) = sample {
            metrics.successful_samples += 1;
            for (peak, value) in [
                (
                    &mut metrics.sampled_peak_working_set_bytes,
                    sample.working_set,
                ),
                (
                    &mut metrics.sampled_peak_private_committed_bytes,
                    sample.private_committed,
                ),
                (
                    &mut metrics.process_lifetime_peak_working_set_bytes,
                    sample.lifetime_peak,
                ),
            ] {
                *peak = Some(peak.map_or(value, |previous| previous.max(value)));
            }
        } else {
            metrics.failed_samples += 1;
            metrics.error = Some(ResourceError::QueryFailed);
        }
    }
    fn at_limit(elapsed: Duration, attempts: u16) -> bool {
        elapsed >= MAX_DURATION || attempts >= MAX_SAMPLES
    }
    fn collect(handle: OwnedHandle, stop: Receiver<()>) -> ResourceMetrics {
        let started = Instant::now();
        let mut metrics = ResourceMetrics::unavailable(ResourceError::QueryFailed);
        metrics.error = None;
        observe(&mut metrics, query(handle.as_raw_handle()));
        loop {
            let remaining = MAX_DURATION.saturating_sub(started.elapsed());
            if at_limit(
                started.elapsed(),
                metrics.successful_samples + metrics.failed_samples,
            ) {
                metrics.limit_reached = true;
                break;
            }
            let wait = remaining.min(Duration::from_millis(RESOURCE_SAMPLE_INTERVAL_MS));
            let stopped = match stop.recv_timeout(wait) {
                Ok(()) | Err(mpsc::RecvTimeoutError::Disconnected) => true,
                Err(mpsc::RecvTimeoutError::Timeout) => false,
            };
            if started.elapsed() >= MAX_DURATION {
                metrics.limit_reached = true;
                break;
            }
            observe(&mut metrics, query(handle.as_raw_handle()));
            if stopped {
                break;
            }
        }
        metrics.observed_ms = started.elapsed().as_millis().min(u64::MAX as u128) as u64;
        metrics.status = if metrics.successful_samples == 0 {
            ResourceStatus::Unavailable
        } else if metrics.failed_samples != 0 || metrics.limit_reached {
            ResourceStatus::Partial
        } else {
            ResourceStatus::Sampled
        };
        metrics
    }
    pub(crate) struct Sampler {
        stop: Option<SyncSender<()>>,
        worker: Option<JoinHandle<ResourceMetrics>>,
        unavailable: Option<ResourceMetrics>,
    }
    impl Sampler {
        pub(crate) fn start(child: &Child) -> Self {
            // Duplicate the existing authority, never reopen a PID or broaden access rights.
            let handle = match child.as_handle().try_clone_to_owned() {
                Ok(handle) => handle,
                Err(_) => return Self::unavailable(ResourceError::HandleUnavailable),
            };
            let (stop, receiver) = mpsc::sync_channel(1);
            match thread::Builder::new()
                .name("locallore-owned-memory".into())
                .spawn(move || collect(handle, receiver))
            {
                Ok(worker) => Self {
                    stop: Some(stop),
                    worker: Some(worker),
                    unavailable: None,
                },
                Err(_) => Self::unavailable(ResourceError::SamplerUnavailable),
            }
        }
        fn unavailable(error: ResourceError) -> Self {
            Self {
                stop: None,
                worker: None,
                unavailable: Some(ResourceMetrics::unavailable(error)),
            }
        }
        fn stop_join(&mut self) -> ResourceMetrics {
            if let Some(stop) = self.stop.take() {
                let _ = stop.try_send(());
            }
            match self.worker.take() {
                Some(worker) => worker
                    .join()
                    .unwrap_or_else(|_| ResourceMetrics::unavailable(ResourceError::SamplerFailed)),
                None => self
                    .unavailable
                    .take()
                    .unwrap_or_else(|| ResourceMetrics::unavailable(ResourceError::SamplerFailed)),
            }
        }
        pub(crate) fn finish(mut self) -> ResourceMetrics {
            self.stop_join()
        }
    }
    impl Drop for Sampler {
        fn drop(&mut self) {
            if self.worker.is_some() {
                let _ = self.stop_join();
            }
        }
    }

    #[cfg(test)]
    mod tests {
        use super::*;
        #[test]
        fn query_failure_is_unknown_and_accumulation_keeps_distinct_peak_meanings() {
            assert!(query(std::ptr::null_mut()).is_none());
            let mut metrics = ResourceMetrics::unavailable(ResourceError::QueryFailed);
            observe(&mut metrics, None);
            assert_eq!(metrics.sampled_peak_working_set_bytes, None);
            observe(
                &mut metrics,
                Some(Sample {
                    working_set: 12,
                    private_committed: 30,
                    lifetime_peak: 100,
                }),
            );
            observe(
                &mut metrics,
                Some(Sample {
                    working_set: 20,
                    private_committed: 25,
                    lifetime_peak: 110,
                }),
            );
            assert_eq!(metrics.sampled_peak_working_set_bytes, Some(20));
            assert_eq!(metrics.sampled_peak_private_committed_bytes, Some(30));
            assert_eq!(metrics.process_lifetime_peak_working_set_bytes, Some(110));
            assert_eq!((metrics.successful_samples, metrics.failed_samples), (2, 1));
        }
        #[test]
        fn fixed_limits_unavailable_and_panicked_sampler_never_invent_memory() {
            assert!(!at_limit(Duration::from_secs(64), 261));
            assert!(at_limit(Duration::from_secs(65), 1));
            assert!(at_limit(Duration::ZERO, 262));
            for error in [
                ResourceError::HandleUnavailable,
                ResourceError::SamplerUnavailable,
            ] {
                let metrics = Sampler::unavailable(error).finish();
                assert_eq!(metrics.status, ResourceStatus::Unavailable);
                assert_eq!(metrics.error, Some(error));
                assert_eq!(metrics.sampled_peak_working_set_bytes, None);
                assert_eq!(metrics.sampled_peak_private_committed_bytes, None);
            }
            let sampler = Sampler {
                stop: None,
                worker: Some(std::thread::spawn(|| panic!("synthetic sampler failure"))),
                unavailable: None,
            };
            let metrics = sampler.finish();
            assert_eq!(metrics.error, Some(ResourceError::SamplerFailed));
            assert_eq!(metrics.successful_samples, 0);
            assert_eq!(metrics.process_lifetime_peak_working_set_bytes, None);
        }
        #[cfg(feature = "development-worker")]
        #[test]
        fn owned_child_sampler_stop_drop_and_process_authority_are_bounded() {
            let fixture = std::env::current_exe()
                .unwrap()
                .parent()
                .unwrap()
                .parent()
                .unwrap()
                .join("protocol-fixture.exe");
            let mut child = std::process::Command::new(fixture)
                .args(["--model", "no-read"])
                .stdin(std::process::Stdio::null())
                .stdout(std::process::Stdio::null())
                .stderr(std::process::Stdio::null())
                .spawn()
                .unwrap();
            let sampler = Sampler::start(&child);
            std::thread::sleep(Duration::from_millis(550));
            let before = Instant::now();
            let result = sampler.finish();
            assert!(before.elapsed() < Duration::from_secs(2));
            assert_eq!(result.status, ResourceStatus::Sampled);
            assert!((2..=5).contains(&result.successful_samples));
            assert_eq!(result.failed_samples, 0);
            assert!(result.sampled_peak_working_set_bytes.unwrap() > 0);
            assert!(result.sampled_peak_private_committed_bytes.unwrap() > 0);
            assert!(
                result.process_lifetime_peak_working_set_bytes
                    >= result.sampled_peak_working_set_bytes
            );
            assert!(!result.limit_reached);
            assert!(child.try_wait().unwrap().is_none()); // Sampling never terminates the owner.
            let sampler = Sampler::start(&child);
            drop(sampler); // Joined even without explicit finish.
            assert!(child.try_wait().unwrap().is_none());
            child.kill().unwrap();
            child.wait().unwrap();
        }
    }
}
#[cfg(windows)]
pub(crate) use windows::Sampler;
#[cfg(not(windows))]
pub(crate) struct Sampler;
#[cfg(not(windows))]
impl Sampler {
    pub(crate) fn start(_: &Child) -> Self {
        Self
    }
    pub(crate) fn finish(self) -> ResourceMetrics {
        ResourceMetrics::unavailable(ResourceError::Unsupported)
    }
}
