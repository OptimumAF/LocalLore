// Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
//! Frozen FIRST at fe54ee18, before child implementation. UNCOMPILED/UNRUN.
//! Actual shared scripted producer/native owner tests, no OS picker/model/UI.
//! Root: cargo test --locked --offline --manifest-path apps/desktop/src-tauri/Cargo.toml evaluation::comparison::tests:: -- --nocapture --test-threads=1
use super::*;
use locallore::inspection_query::{Observer, View};
use locallore_eval::local_lane::{comparison as producer, LaneFactory};
use std::{collections::BTreeSet, sync::{atomic::{AtomicUsize, Ordering}, Barrier, OnceLock}};

struct Fixture { manager:Arc<EvaluationManager>, lease:Arc<WindowLease>, epoch:u64 }
impl Fixture {
    fn new()->Self {
        let root=std::env::temp_dir().join(format!("comparison-native-reader-{}",uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        let manager=Arc::new(EvaluationManager::new(root.join("evaluations")));
        let lease=Arc::new(WindowLease::default());
        let epoch=lease.begin().unwrap();
        manager.catalog(&lease,epoch).unwrap();
        Self{manager,lease,epoch}
    }
    fn status(&self,client:&str)->Value { self.manager.comparison_status(&self.lease,self.epoch,true,client).unwrap() }
    fn done(&self,client:&str)->Value {
        let until=Instant::now()+Duration::from_secs(30);
        loop { let value=self.status(client); if value["running"]==false{return value}
            assert!(Instant::now()<until,"bounded native fixture wait: {value}");
            std::thread::sleep(Duration::from_millis(5)); }
    }
    fn pick(&self,client:&str,path:&Path)->Value {
        let path=path.to_path_buf();
        self.manager.comparison_pick(&self.lease,self.epoch,true,client,move||Ok(Some(path))).unwrap();
        let ready=self.done(client); assert_eq!(ready["phase"],"ready","{ready}"); ready
    }
    fn close(&self,client:&str,token:Option<&str>)->Value {
        self.manager.comparison_close(&self.lease,self.epoch,client,token).unwrap()
    }
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let closed=self.lease.invalidate(&format!("main-{}",self.epoch));
        self.manager.retire(self.epoch); self.manager.drain(self.epoch);
        if let Some(closed)=closed { self.lease.finish_close(closed,||{}); }
    }
}
fn producer_root()->&'static Path {
    static SOURCE:OnceLock<PathBuf>=OnceLock::new();
    SOURCE.get_or_init(||{
        let root=std::env::temp_dir().join(format!("comparison-native-producer-{}",uuid().unwrap()));
        fs::create_dir(&root).unwrap();
        let reference=root.join("reference");
        producer::prepare_reference(&reference,&Cancellation::default()).unwrap();
        let opened=producer::open_reference(&reference).unwrap();
        for (name,kind) in [("paired",producer::ComparisonKind::PairedSnapshots),("rollout",producer::ComparisonKind::ContinuousRollout)] {
            let report=producer::run_comparison(&root.join(name),false,kind,&Cancellation::default(),1,LaneFactory::ScriptedBaseline,if name=="paired"{Some(&opened)}else{None}).unwrap();
            assert_eq!(report.turns.len(),12); assert!(report.turns.iter().all(|r|r.passed));
        }
        root
    }).as_path()
}
#[derive(PartialEq,Eq)]
struct Inventory{dirs:BTreeSet<PathBuf>,files:BTreeMap<PathBuf,Vec<u8>>}
fn inventory(root:&Path)->Inventory {
    fn visit(root:&Path,rel:&Path,depth:usize,out:&mut Inventory,total:&mut usize){
        assert!(depth<=8);let path=root.join(rel);let m=fs::symlink_metadata(&path).unwrap();assert!(!m.file_type().is_symlink());
        if m.is_dir(){out.dirs.insert(rel.into());for c in fs::read_dir(path).unwrap(){visit(root,&rel.join(c.unwrap().file_name()),depth+1,out,total)}}
        else{assert!(m.is_file()&&m.len()<=8*1024*1024);let bytes=fs::read(path).unwrap();*total+=bytes.len();assert!(*total<=64*1024*1024);out.files.insert(rel.into(),bytes);}
        assert!(out.dirs.len()+out.files.len()<=2048);
    }
    let mut out=Inventory{dirs:BTreeSet::new(),files:BTreeMap::new()};visit(root,Path::new(""),0,&mut out,&mut 0);out
}
fn copy_run(name:&str)->PathBuf {
    let source=inventory(&producer_root().join(name));
    let root=std::env::temp_dir().join(format!("comparison-native-copy-{}",uuid().unwrap()));fs::create_dir(&root).unwrap();
    for d in &source.dirs{if !d.as_os_str().is_empty(){fs::create_dir_all(root.join(d)).unwrap();}}
    for(p,b)in &source.files{fs::write(root.join(p),b).unwrap();}assert!(inventory(&root)==source);root
}
fn reacquire(path:&Path){let run=shared::open_read_only(path).unwrap();shared::summary(&run,true).unwrap();drop(run);}
fn request(token:&str,binding:&str,observer:Observer)->ComparisonEvidenceRequest {
    ComparisonEvidenceRequest{token:token.into(),binding:binding.into(),row:shared::RowId{turn:"courier-01".into(),arm:shared::Arm::Left},request:shared::EvidenceRequest::Query{edge:shared::Edge::After,observer,view:View::History}}
}
fn err<T>(r:Result<T>)->String{r.err().expect("native refusal")}

#[test]
fn native_grant_and_closed_ids_refuse_before_picker_or_private_existence(){
    let f=Fixture::new();let calls=Arc::new(AtomicUsize::new(0));let count=calls.clone();
    let denied=locallore::host::Host::new(false).story_lab_granted();assert!(!denied);
    assert_eq!(err(f.manager.comparison_pick(&f.lease,f.epoch,denied,"bad",move||{count.fetch_add(1,Ordering::SeqCst);Ok(None)})),"Forbidden");
    assert_eq!(calls.load(Ordering::SeqCst),0);
    assert_eq!(err(f.manager.comparison_status(&f.lease,f.epoch,false,"bad")),"Forbidden");
    assert_eq!(err(f.manager.comparison_source(&f.lease,f.epoch,false,"bad")),"Forbidden");
    assert_eq!(err(f.manager.comparison_summary(&f.lease,f.epoch,false,"bad")),"Forbidden");
    let mut input=request("bad","bad",Observer::Player);input.request=shared::EvidenceRequest::Outputs{observer:Observer::Character{id:"mira".into()}};
    assert_eq!(err(f.manager.comparison_evidence(&f.lease,f.epoch,true,input)),"Forbidden");
    assert_eq!(err(f.manager.comparison_evidence(&f.lease,f.epoch,false,request("bad","bad",Observer::Player))),"Forbidden");
    assert_eq!(err(f.manager.comparison_pick(&f.lease,f.epoch,true,"../bad",||Ok(None))),"InvalidEvaluationInput");
    assert!(f.manager.state().unwrap().job.is_none());
}

#[test]
fn actual_paired_and_rollout_wrappers_recover_same_client_without_reopening_or_run_writes(){
    for name in ["paired","rollout"]{
        let f=Fixture::new();let path=copy_run(name);let before=inventory(&path);let client=uuid().unwrap();
        let ready=f.pick(&client,&path);let token=ready["run_token"].as_str().unwrap();let binding=ready["binding"].as_str().unwrap();
        assert_eq!(ready["kind"],"comparison_reader");assert_eq!(ready["execution_available"],false);assert_eq!(ready["read_only"],true);
        assert!(ready["operation_id"].as_u64().unwrap()>0);assert_eq!(ready["error"],Value::Null);
        let hits=Arc::new(AtomicUsize::new(0));let h=hits.clone();
        assert_eq!(f.manager.comparison_pick(&f.lease,f.epoch,true,&client,move||{h.fetch_add(1,Ordering::SeqCst);Ok(None)}).unwrap(),ready);
        assert_eq!(hits.load(Ordering::SeqCst),0);assert_eq!(f.status(&client),ready);
        let wrapped=f.manager.comparison_summary(&f.lease,f.epoch,true,token).unwrap();
        assert_eq!(wrapped["run_token"],token);assert_eq!(wrapped["snapshot"]["report"],serde_json::to_value(producer::inspect_comparison(&path).unwrap()).unwrap());
        let source=f.manager.comparison_source(&f.lease,f.epoch,true,token).unwrap();
        assert_eq!(source["source"]["binding"],binding);assert_eq!(source["source"]["rows"],wrapped["snapshot"]["rows"]);assert!(source["source"].get("report").is_none());
        let view=f.manager.comparison_evidence(&f.lease,f.epoch,true,request(token,binding,Observer::Character{id:"mira".into()})).unwrap();
        assert_eq!(view["evidence"]["body"]["kind"],"query");assert!(!view.to_string().contains("SECRET-TIDE-731"));assert_eq!(view["evidence"]["generation_grant"],false);
        assert_eq!(f.close(&client,Some(token))["phase"],"closed");reacquire(&path);assert!(inventory(&path)==before);
    }
}

#[test]
fn pending_picker_close_is_nonblocking_and_late_open_cannot_publish_or_retain_lock(){
    let f=Fixture::new();let path=copy_run("rollout");let before=inventory(&path);let client=uuid().unwrap();
    let (entered,seen)=std::sync::mpsc::channel();let(release,wait)=std::sync::mpsc::channel();let picked=path.clone();
    f.manager.comparison_pick(&f.lease,f.epoch,true,&client,move||{entered.send(()).unwrap();wait.recv_timeout(Duration::from_secs(10)).unwrap();Ok(Some(picked))}).unwrap();
    seen.recv_timeout(Duration::from_secs(5)).unwrap();let closing=f.close(&client,None);assert_eq!(closing["phase"],"closing");assert_eq!(closing["running"],true);
    release.send(()).unwrap();let closed=f.done(&client);assert_eq!(closed["phase"],"closed");assert!(closed["run_token"].is_null());reacquire(&path);assert!(inventory(&path)==before);
}

#[test]
fn same_existing_worker_rejects_execution_while_picker_waits_and_picker_while_execution_runs(){
    let f=Fixture::new();let client=uuid().unwrap();let(entered,seen)=std::sync::mpsc::channel();let(release,wait)=std::sync::mpsc::channel();
    f.manager.comparison_pick(&f.lease,f.epoch,true,&client,move||{entered.send(()).unwrap();wait.recv_timeout(Duration::from_secs(10)).unwrap();Ok(None)}).unwrap();seen.recv_timeout(Duration::from_secs(5)).unwrap();
    assert_eq!(err(f.manager.start(&f.lease,f.epoch,None,"one")),"EvaluationBusy");release.send(()).unwrap();assert_eq!(f.done(&client)["phase"],"cancelled");f.close(&client,None);
    f.manager.test_case("hold-boundary").unwrap();let run=f.manager.start(&f.lease,f.epoch,None,"all").unwrap();
    let token=run["run_token"].as_str().unwrap();let operation=run["operation_id"].as_u64().unwrap();
    let until=Instant::now()+Duration::from_secs(30);loop{let status=f.manager.status(&f.lease,f.epoch,token).unwrap();if status["completed_cases"]==1{break}assert!(Instant::now()<until);std::thread::sleep(Duration::from_millis(5));}
    assert_eq!(err(f.manager.comparison_pick(&f.lease,f.epoch,true,&uuid().unwrap(),||Ok(None))),"EvaluationBusy");
    f.manager.cancel(&f.lease,f.epoch,token,operation).unwrap();f.manager.test_case("release-boundary").unwrap();f.manager.drain(f.epoch);
}

#[test]
fn foreign_window_equal_epoch_and_wrong_client_or_token_cannot_read_or_close_capability(){
    let f=Fixture::new();let path=copy_run("rollout");let client=uuid().unwrap();let ready=f.pick(&client,&path);let token=ready["run_token"].as_str().unwrap();
    let other=WindowLease::default();assert_eq!(other.begin().unwrap(),f.epoch);
    assert_eq!(err(f.manager.comparison_status(&other,f.epoch,true,&client)),"UnknownEvaluationRun");
    assert_eq!(err(f.manager.comparison_summary(&other,f.epoch,true,token)),"UnknownEvaluationRun");
    assert_eq!(err(f.manager.comparison_close(&other,f.epoch,&client,Some(token))),"UnknownEvaluationRun");
    assert_eq!(err(f.manager.comparison_close(&f.lease,f.epoch,&uuid().unwrap(),Some(token))),"UnknownEvaluationRun");
    assert_eq!(err(f.manager.comparison_close(&f.lease,f.epoch,&client,Some(&uuid().unwrap()))),"UnknownEvaluationRun");
    assert_eq!(f.status(&client)["phase"],"ready");f.close(&client,Some(token));reacquire(&path);
}

#[test]
fn retirement_during_open_publication_drops_private_result_before_window_reopens(){
    let f=Fixture::new();let path=copy_run("rollout");let before=inventory(&path);let client=uuid().unwrap();let entered=Arc::new(Barrier::new(2));let release=Arc::new(Barrier::new(2));
    *f.manager.before_publish.lock().unwrap()=Some((entered.clone(),release.clone()));let selected=path.clone();
    f.manager.comparison_pick(&f.lease,f.epoch,true,&client,move||Ok(Some(selected))).unwrap();entered.wait();
    let closed=f.lease.invalidate(&format!("main-{}",f.epoch)).unwrap();f.manager.retire(f.epoch);release.wait();f.manager.drain(f.epoch);f.lease.finish_close(closed,||{});
    let fresh=f.lease.begin().unwrap();assert_eq!(err(f.manager.comparison_status(&f.lease,fresh,true,&client)),"UnknownEvaluationRun");reacquire(&path);assert!(inventory(&path)==before);
}

#[test]
fn close_during_evidence_suppresses_reply_and_same_worker_releases_the_read_lock(){
    let f=Fixture::new();let path=copy_run("rollout");let before=inventory(&path);let client=uuid().unwrap();let ready=f.pick(&client,&path);
    let token=ready["run_token"].as_str().unwrap().to_owned();let binding=ready["binding"].as_str().unwrap().to_owned();let entered=Arc::new(Barrier::new(2));let release=Arc::new(Barrier::new(2));
    *f.manager.before_publish.lock().unwrap()=Some((entered.clone(),release.clone()));
    let worker={let m=f.manager.clone();let l=f.lease.clone();let t=token.clone();let e=f.epoch;std::thread::spawn(move||m.comparison_evidence(&l,e,true,request(&t,&binding,Observer::Player)))};
    entered.wait();assert_eq!(f.status(&client)["phase"],"reading");assert_eq!(f.status(&client)["running"],true);
    assert_eq!(f.close(&client,Some(&token))["phase"],"closing");release.wait();assert_eq!(err(worker.join().unwrap()),"Closed");assert_eq!(f.done(&client)["phase"],"closed");reacquire(&path);assert!(inventory(&path)==before);
}

#[test]
fn idle_expiry_drops_before_unknown_and_unacknowledged_terminal_is_not_evicted(){
    let f=Fixture::new();let client=uuid().unwrap();f.manager.comparison_pick(&f.lease,f.epoch,true,&client,||Ok(None)).unwrap();assert_eq!(f.done(&client)["phase"],"cancelled");
    assert_eq!(err(f.manager.comparison_pick(&f.lease,f.epoch,true,&uuid().unwrap(),||Ok(None))),"EvaluationBusy");f.close(&client,None);
    let path=copy_run("rollout");let active=uuid().unwrap();let ready=f.pick(&active,&path);let token=ready["run_token"].as_str().unwrap();
    {let mut state=f.manager.comparison.lock().unwrap();for record in state.records.values_mut(){record.touched=Instant::now().checked_sub(Duration::from_secs(901)).unwrap();}}
    assert_eq!(err(f.manager.comparison_summary(&f.lease,f.epoch,true,token)),"UnknownEvaluationRun");reacquire(&path);f.close(&active,Some(token));
    for _ in 0..6{let id=uuid().unwrap();f.manager.comparison_pick(&f.lease,f.epoch,true,&id,||Ok(None)).unwrap();f.done(&id);f.close(&id,None);}
    assert!(f.manager.comparison.lock().unwrap().records.len()<=4);
}

#[test]
fn picker_failure_spawn_refusal_and_worker_panic_leave_no_busy_job_or_private_lock(){
    let f=Fixture::new();let client=uuid().unwrap();f.manager.fail_spawn.store(true,Ordering::SeqCst);
    assert_eq!(err(f.manager.comparison_pick(&f.lease,f.epoch,true,&client,||Ok(None))),"EvaluationInternal");assert!(f.manager.state().unwrap().job.is_none());f.close(&client,None);
    let broken=uuid().unwrap();f.manager.comparison_pick(&f.lease,f.epoch,true,&broken,||Err("SYNTHETIC_PRIVATE_OS_PATH".into())).unwrap();let failure=f.done(&broken);assert_eq!(failure["phase"],"failed");assert_eq!(failure["error"],"EvaluationIo");assert!(failure["run_token"].is_null());f.close(&broken,None);
    f.manager.panic_worker.store(true,Ordering::SeqCst);let panics=uuid().unwrap();f.manager.comparison_pick(&f.lease,f.epoch,true,&panics,||Ok(None)).unwrap();let failure=f.done(&panics);assert_eq!(failure["phase"],"failed");assert_eq!(failure["error"],"EvaluationInternal");assert!(f.manager.state().unwrap().job.is_none());f.close(&panics,None);
    let path=copy_run("rollout");let good=uuid().unwrap();let ready=f.pick(&good,&path);f.close(&good,ready["run_token"].as_str());reacquire(&path);
}
