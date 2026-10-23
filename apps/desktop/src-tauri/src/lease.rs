//! Native-only window lifetime fence. No renderer token can create authority.
use std::sync::{
    atomic::{AtomicU64, Ordering},
    Mutex,
};
#[derive(Default)]
pub struct WindowLease {
    epoch: AtomicU64,
    closed: AtomicU64,
    gate: Mutex<()>,
}
impl WindowLease {
    pub fn begin(&self) -> Result<u64, &'static str> {
        let epoch = self.epoch.load(Ordering::SeqCst);
        if !epoch.is_multiple_of(2) || self.closed.load(Ordering::SeqCst) != epoch {
            return Err("Closed");
        }
        self.epoch
            .compare_exchange(epoch, epoch + 1, Ordering::SeqCst, Ordering::SeqCst)
            .map(|_| epoch + 1)
            .map_err(|_| "Closed")
    }
    pub fn capture(&self, label: &str) -> Result<u64, &'static str> {
        let epoch = label
            .strip_prefix("main-")
            .and_then(|s| s.parse().ok())
            .ok_or("Forbidden")?;
        if self.valid(epoch) {
            Ok(epoch)
        } else {
            Err("Closed")
        }
    }
    pub fn valid(&self, epoch: u64) -> bool {
        !epoch.is_multiple_of(2) && self.epoch.load(Ordering::SeqCst) == epoch
    }
    pub fn dispatch<T>(
        &self,
        epoch: u64,
        action: impl FnOnce() -> Result<T, String>,
    ) -> Result<T, String> {
        let _gate = self.gate.lock().map_err(|_| "Closed".to_owned())?;
        if !self.valid(epoch) {
            return Err("Closed".into());
        }
        action()
    }
    // Called synchronously by Destroyed, before scheduling any cleanup worker.
    pub fn invalidate(&self, label: &str) -> Option<u64> {
        let epoch = self.capture(label).ok()?;
        self.epoch
            .compare_exchange(epoch, epoch + 1, Ordering::SeqCst, Ordering::SeqCst)
            .ok()
            .map(|_| epoch + 1)
    }
    pub fn finish_close(&self, closed_epoch: u64, close: impl FnOnce()) {
        if let Ok(_gate) = self.gate.lock() {
            close();
            self.closed.store(closed_epoch, Ordering::SeqCst);
        }
    }
    #[cfg(any(feature = "dev-harness", test))]
    pub fn can_open(&self) -> bool {
        let epoch = self.epoch.load(Ordering::SeqCst);
        epoch.is_multiple_of(2) && self.closed.load(Ordering::SeqCst) == epoch
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::{atomic::AtomicBool, Arc, Barrier};
    #[test]
    fn captured_create_after_destroy_cannot_dispatch_or_write() {
        let lease = Arc::new(WindowLease::default());
        let epoch = lease.begin().unwrap();
        let entered = Arc::new(Barrier::new(2));
        let release = Arc::new(Barrier::new(2));
        let wrote = Arc::new(AtomicBool::new(false));
        let worker = {
            let lease = lease.clone();
            let entered = entered.clone();
            let release = release.clone();
            let wrote = wrote.clone();
            std::thread::spawn(move || {
                entered.wait();
                release.wait();
                lease.dispatch(epoch, || {
                    wrote.store(true, Ordering::SeqCst);
                    Ok(())
                })
            })
        };
        entered.wait();
        let closed = lease.invalidate("main-1").unwrap();
        assert!(!lease.can_open());
        lease.finish_close(closed, || {});
        release.wait();
        assert_eq!(worker.join().unwrap(), Err("Closed".into()));
        assert!(!wrote.load(Ordering::SeqCst));
    }
    #[test]
    fn delayed_initialization_is_fenced_and_reopen_waits_for_cleanup() {
        let lease = WindowLease::default();
        let old = lease.begin().unwrap();
        let closed = lease.invalidate("main-1").unwrap();
        assert_eq!(
            lease.dispatch(old, || Ok("open database")),
            Err("Closed".into())
        );
        assert_eq!(lease.begin(), Err("Closed"));
        lease.finish_close(closed, || {});
        let fresh = lease.begin().unwrap();
        assert_ne!(fresh, old);
        assert_eq!(lease.capture("main-1"), Err("Closed"));
        assert!(lease.dispatch(fresh, || Ok(())).is_ok());
    }
}
