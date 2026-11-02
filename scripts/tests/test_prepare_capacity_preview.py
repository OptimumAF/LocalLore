"""Original observational capacity oracles; tiny retained D-only metadata.

No real ledger, VM, SDK, resource/native/process query or admission is used.
Fixtures use real storage reserve/close/finalization APIs on isolated files.
Synthetic historical byte floors avoid allocating GiB payloads. Nothing cleans
up these fixtures: original and deliberately changed bytes remain for review.
"""
import ast
from contextlib import ExitStack, contextmanager
import ctypes
import os
from pathlib import Path
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_storage as storage
from benchmarks import prepare_recovery_contract as recovery

HOME = Path('D:/Dev/Experiments/LocalLore/2026-11-02-knowledge-fresh-capacity-v1/test-agent-v1/fixtures')
GIB = 1024 ** 3
KEYS = {'version','scope','root','ledger','max_guests','budget_bytes','reservation_bytes',
        'active_count','charged_bytes','projected_bytes','root_limit_exceeded',
        'byte_limit_exceeded','would_fit','admission_granted'}


class Tiny:
    def __init__(self):
        assert HOME.drive.upper() == 'D:'
        HOME.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix='capacity-', dir=HOME))
        assert self.base.is_relative_to(HOME) and self.base.drive.upper() == 'D:'
        self.registry = self.base/'registry'
        self.candidate = self.base/'fresh-never-created'
        self.serial = 0

    def write(self, path, value):
        assert path.is_relative_to(self.base)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value if isinstance(value, bytes) else storage.encoded(value))

    def ledger(self):
        return storage.read_json(self.registry/'ledger-v1.json')

    def replace_ledger(self, value):
        path = self.registry/'ledger-v1.json'
        if path.exists(): self.preserve(path)
        self.write(path, value)

    def preserve(self, path):
        self.serial += 1
        dest = self.base/'originals'/('%03d-' % self.serial + path.name)
        self.write(dest, path.read_bytes())
        return dest

    def change(self, path, raw):
        self.preserve(path)
        self.write(path, raw)

    def empty(self):
        self.write(self.registry/'ledger-v1.json', dict(version=1,max_guests=2,
            budget_bytes=64*GIB,reservation_bytes=40*GIB,entries=[]))

    def closed(self, name='closed', proofs=False):
        root = self.base/name; digest = ('%064x' % (self.serial + len(name) + 1))
        storage.reserve_prepare(root, digest, registry=self.registry)
        root.mkdir()
        self.write(root/'payload.bin', b'original tiny retained payload')
        proof_paths = []
        if proofs:
            for role in ('admission','owner_result','worker_result','after'):
                p = root/'proofs'/(role+'.json')
                self.write(p, {'synthetic_storage_binding_only': role})
                proof_paths.append(p)
        closure = root/'closure.json'
        value = dict(proposal_sha256=digest,closure_verified=True,cleanup_complete=True)
        if proofs:
            value.update({role:storage.binding(path) for role,path in
                          zip(('admission','owner_result','worker_result','after'),proof_paths)})
        self.write(closure, value)
        storage.record_closed(root, closure, registry=self.registry)
        return root, closure, proof_paths

    def retired(self):
        root, closure, _ = self.closed()
        image = root/storage.CONTENT/'cache.img'
        self.write(image, b'SYNTHETIC tiny disposable sentinel, retained outside root')
        storage.record_closed(root, closure, registry=self.registry)
        evidence = self.base/'evidence/manifest.json'; files=[]
        for path in sorted(p for p in root.rglob('*') if p.is_file() and p != image):
            rel = path.relative_to(root).as_posix();copy=self.base/'evidence/files'/rel
            self.write(copy, path.read_bytes());files.append(dict(relative=rel,binding=storage.binding(copy)))
        self.write(evidence, dict(version=1,root=str(root),complete=True,files=files))
        plan = storage.plan_retirement(root, evidence, registry=self.registry)
        quarantine = self.base/'quarantine-cache.bin'
        assert image.is_relative_to(self.base) and quarantine.is_relative_to(self.base)
        assert image.read_bytes().startswith(b'SYNTHETIC tiny disposable sentinel')
        image.rename(quarantine)  # Preserve this test's sentinel; never delete an image.
        storage.record_retired(root, plan, registry=self.registry)
        entry = self.ledger()['entries'][0]
        charge_paths = list(p for p in root.rglob('*') if p.is_file())
        charge_paths += [Path(row['binding']['path']) for row in files]
        charge_paths += [evidence, Path(entry['retirement_receipt']['path'])]
        expected = sum(len(p.read_bytes()) for p in {str(p).casefold():p for p in charge_paths}.values())
        return root, expected, quarantine


def snapshot(root):
    result={}
    for path in sorted(root.rglob('*')):
        info=path.lstat()
        result[path.relative_to(root).as_posix()] = (info.st_ino,info.st_size,info.st_mtime_ns,
            path.read_bytes() if path.is_file() else None)
    return result


@contextmanager
def readonly():
    original_open=Path.open; original_low=os.open
    def opened(path, mode='r', *args, **kwargs):
        assert not any(c in mode for c in 'wax+'), 'Preview attempted a write'
        return original_open(path, mode, *args, **kwargs)
    def low(path, flags, *args, **kwargs):
        assert not flags & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND), 'Preview attempted os.open write'
        return original_low(path, flags, *args, **kwargs)
    with ExitStack() as stack:
        stack.enter_context(patch.object(Path,'open',opened))
        stack.enter_context(patch.object(os,'open',low))
        for name in ('mkdir','unlink','rmdir','rename','replace','write_bytes','write_text'):
            stack.enter_context(patch.object(Path,name,side_effect=AssertionError('Preview mutated path')))
        for name in ('mkdir','unlink','remove','rmdir','rename','replace','system'):
            stack.enter_context(patch.object(os,name,side_effect=AssertionError('Preview mutated/launched')))
        for name in ('_initialize_registry','_locked','_atomic_write','reserve_prepare','record_state',
                     'record_closed','record_retired','plan_retirement'):
            stack.enter_context(patch.object(storage,name,side_effect=AssertionError('Preview invoked mutator')))
        stack.enter_context(patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('Preview invoked native API')))
        stack.enter_context(patch.object(subprocess,'Popen',side_effect=AssertionError('Preview spawned')))
        stack.enter_context(patch.object(subprocess,'run',side_effect=AssertionError('Preview spawned')))
        stack.enter_context(patch.object(socket,'socket',side_effect=AssertionError('Preview queried socket')))
        yield


@unittest.skipUnless(os.name == 'nt', 'Storage contract requires tiny physical D: fixture paths')
class PrepareCapacityPreviewTests(unittest.TestCase):
    def call(self, f, candidate=None):
        return storage.preview_prepare(f.candidate if candidate is None else candidate, registry=f.registry)

    def observe(self, f, candidate=None):
        before=snapshot(f.base)
        with readonly(): result=self.call(f,candidate)
        self.assertEqual(snapshot(f.base),before)
        self.assertEqual(set(result),KEYS)
        for name in ('version','max_guests','budget_bytes','reservation_bytes','active_count','charged_bytes','projected_bytes'):
            self.assertIs(type(result[name]),int)
        for name in ('root_limit_exceeded','byte_limit_exceeded','would_fit','admission_granted'):
            self.assertIs(type(result[name]),bool)
        self.assertIs(result['admission_granted'],False)
        self.assertEqual((result['version'],result['scope']),(1,'receipt-avd-prepare-capacity-preview-v1'))
        self.assertEqual((result['max_guests'],result['budget_bytes'],result['reservation_bytes']),(2,64*GIB,40*GIB))
        self.assertEqual(result['ledger'],storage.binding(f.registry/'ledger-v1.json'))
        self.assertEqual(result['root'],str(f.candidate if candidate is None else candidate))
        return result

    def refused(self, f, candidate=None):
        before=snapshot(f.base)
        with readonly(), self.assertRaises(storage.StorageRefused):self.call(f,candidate)
        self.assertEqual(snapshot(f.base),before)

    def test_empty_registry_exact_observation_never_grants_or_reserves(self):
        f=Tiny();f.empty();result=self.observe(f)
        self.assertEqual((result['active_count'],result['charged_bytes'],result['projected_bytes']),(0,0,40*GIB))
        self.assertIs(result['would_fit'],True)
        self.assertIs(result['root_limit_exceeded'],False);self.assertIs(result['byte_limit_exceeded'],False)
        result['ledger']['sha256']='0'*64
        self.assertNotEqual(self.observe(f)['ledger']['sha256'],'0'*64)
        self.assertEqual(f.ledger()['entries'],[]);self.assertFalse(f.candidate.exists())

    def test_exact_byte_and_count_boundaries_keep_both_independent_limit_reasons(self):
        for floor,fit in ((24*GIB,True),(24*GIB+1,False)):
            f=Tiny();f.closed();ledger=f.ledger();ledger['entries'][0]['reserved_bytes']=floor;f.replace_ledger(ledger)
            result=self.observe(f)
            self.assertEqual((result['active_count'],result['charged_bytes'],result['projected_bytes']),(1,floor,floor+40*GIB))
            self.assertIs(result['would_fit'],fit);self.assertIs(result['byte_limit_exceeded'],not fit)
            self.assertIs(result['root_limit_exceeded'],False)
        f=Tiny();f.closed('first');f.closed('second');result=self.observe(f)
        self.assertEqual(result['active_count'],2);self.assertIs(result['root_limit_exceeded'],True)
        self.assertIs(result['byte_limit_exceeded'],False);self.assertIs(result['would_fit'],False)
        f=Tiny();storage.reserve_prepare(f.base/'absent-preparing','1'*64,registry=f.registry)
        result=self.observe(f)
        self.assertEqual(result['charged_bytes'],40*GIB);self.assertIs(result['byte_limit_exceeded'],True)
        self.assertIs(result['root_limit_exceeded'],False);self.assertFalse((f.base/'absent-preparing').exists())

    def test_closed_charge_retains_recorded_peak_and_reobserves_new_files_without_writing(self):
        f=Tiny();root,closure,_=f.closed();payload=root/'payload.bin'
        f.change(payload,b'x'*4096);storage.record_closed(root,closure,registry=f.registry)
        floor=f.ledger()['entries'][0]['reserved_bytes']
        f.change(payload,b'x');small=self.observe(f)
        self.assertEqual(small['charged_bytes'],floor)
        f.write(root/'later-extra.bin',b'y'*8192);grown=self.observe(f)
        expected=sum(len(p.read_bytes()) for p in root.rglob('*') if p.is_file())
        self.assertEqual(grown['charged_bytes'],max(floor,expected))
        self.assertGreater(grown['charged_bytes'],small['charged_bytes'])
        self.assertEqual(f.ledger()['entries'][0]['reserved_bytes'],floor)

    def test_retired_records_still_charge_evidence_and_refuse_descendant_reuse(self):
        f=Tiny();root,expected,quarantine=f.retired();result=self.observe(f)
        self.assertEqual(result['active_count'],0);self.assertEqual(result['charged_bytes'],expected)
        self.assertGreater(result['charged_bytes'],0);self.assertIs(result['would_fit'],True)
        self.assertTrue(quarantine.exists());self.refused(f,root/'never-reuse')

    def test_missing_locked_corrupt_or_policy_changed_ledger_never_initializes_or_reclaims(self):
        f=Tiny();self.refused(f);self.assertFalse(f.registry.exists())
        f=Tiny();f.registry.mkdir();self.refused(f);self.assertEqual(list(f.registry.iterdir()),[])
        f=Tiny();f.empty();f.write(f.registry/'admission.lock',b'old or live owner is not reclaimed');self.refused(f)
        for corruption in (b'broken',b'{"version":1,"version":1}',b'{}'):
            f=Tiny();f.empty();f.change(f.registry/'ledger-v1.json',corruption);self.refused(f)
        for key,value in (('version',True),('max_guests',3),('budget_bytes',65*GIB),('reservation_bytes',39*GIB)):
            f=Tiny();f.empty();ledger=f.ledger();ledger[key]=value;f.replace_ledger(ledger);self.refused(f)

    def test_stale_or_rebound_bad_closure_and_orphan_recovery_history_refuse(self):
        f=Tiny();_,_,proofs=f.closed(proofs=True);f.change(proofs[0],b'changed evidence');self.refused(f)
        f=Tiny();_,closure,_=f.closed();value=storage.read_json(closure);value['cleanup_complete']=False
        f.change(closure,storage.encoded(value));ledger=f.ledger();ledger['entries'][0]['closure']=storage.binding(closure)
        f.replace_ledger(ledger);self.refused(f)
        f=Tiny();root,_,_=f.closed();ledger=f.ledger();ledger['version']=2
        for entry in ledger['entries']:entry['recovery']=None
        f.replace_ledger(ledger);self.assertIs(self.observe(f)['would_fit'],True)
        claim=recovery.claim_path(f.registry,root);f.write(claim,{'orphaned_one_use_intent':True});self.refused(f)

    def test_existing_unsafe_missing_parent_and_absent_tracked_ancestor_paths_refuse(self):
        f=Tiny();f.empty();existing=f.base/'existing';existing.mkdir();self.refused(f,existing)
        self.refused(f,f.base/'missing-parent/new')
        for path in (Path('relative-candidate'),Path('C:/not-created-by-this-test'),f.base/'..'/'noncanonical'):
            self.refused(f,path)
        self.refused(f,f.registry/'inside-registry')
        f=Tiny();tracked=f.base/'absent-ancestor/tracked-leaf'
        storage.reserve_prepare(tracked,'2'*64,registry=f.registry)
        self.refused(f,f.base/'absent-ancestor')
        # Similar spelling is not an ancestry relation.
        f=Tiny();root,_,_=f.closed();self.assertIs(self.observe(f,f.base/(root.name+'-different'))['would_fit'],True)

    def test_detected_ledger_lock_root_or_proof_change_refuses_instead_of_returning_admission(self):
        for fault in ('ledger','lock','root','proof'):
            f=Tiny();root,_,proofs=f.closed(proofs=True);changed=[]
            original_binding=storage.binding;original_charge=storage._charge
            def mutate():
                if changed:return
                changed.append(fault)
                if fault=='ledger':
                    ledger=f.ledger();ledger['entries'][0]['reserved_bytes']+=1;f.replace_ledger(ledger)
                elif fault=='lock':f.write(f.registry/'admission.lock',b'concurrent owner')
                elif fault=='root':f.candidate.mkdir()
                else:f.change(proofs[0],b'proof drift after its first actual charge read')
            def bound(path):
                result=original_binding(path)
                if fault!='proof' and Path(path)==f.registry/'ledger-v1.json':mutate()
                return result
            def charge(entry):
                result=original_charge(entry)
                if fault=='proof':mutate()
                return result
            # Only these explicit tiny fixture race writes are allowed here;
            # semantic validation and the first actual charge still execute.
            with self.subTest(fault=fault),patch.object(storage,'binding',side_effect=bound), \
                 patch.object(storage,'_charge',side_effect=charge),self.assertRaises(storage.StorageRefused):
                self.call(f)
            self.assertEqual(changed,[fault])
            self.assertFalse(any(e['root']==str(f.candidate) for e in f.ledger()['entries']))

    def test_import_definitions_do_no_io_and_remain_python39_syntax(self):
        path=Path(storage.__file__);raw=path.read_bytes();ast.parse(raw,feature_version=(3,9))
        with ExitStack() as stack:
            for method in ('open','stat','lstat','mkdir'):
                stack.enter_context(patch.object(Path,method,side_effect=AssertionError('Import IO')))
            stack.enter_context(patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('Import native')))
            stack.enter_context(patch.object(subprocess,'Popen',side_effect=AssertionError('Import process')))
            exec(compile(raw,str(path),'exec'),{'__name__':'benchmarks._capacity_import_probe','__file__':str(path),'__package__':'benchmarks'})


if __name__=='__main__':unittest.main()
