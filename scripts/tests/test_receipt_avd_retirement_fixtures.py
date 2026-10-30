"""Tiny synthetic D: retirement inputs; never a production registry or real AVD.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
from pathlib import Path
import tempfile

from benchmarks import receipt_avd_storage as storage

CLEANUP = (
    'auth_handle_closed','client_sockets_closed','guest_output_capture_complete',
    'guest_pipes_closed','guest_preflight_sockets_closed','guest_process_handle_closed',
    'guest_terminate_attempted','guest_wait_completed','preflight_sockets_closed',
    'process_handles_closed','server_output_capture_complete','server_pipes_closed',
    'server_process_handle_closed','server_terminate_attempted','server_wait_completed',
)

class TinyRetirement:
    def __init__(self, change=None):
        self.base = Path(tempfile.mkdtemp(prefix='locallore-retirement-tiny-'))
        assert self.base.drive.upper() == 'D:'
        self.registry = self.base/'synthetic-registry'
        self.root = self.base/'synthetic-guest'
        self.output = self.base/'execution'
        self.proposal_sha = '7'*64
        storage.reserve_prepare(self.root,self.proposal_sha,self.registry)
        self.root.mkdir()
        self.images = []
        for index,name in enumerate(('sdcard.img','userdata-qemu.img.qcow2')):
            path = self.root/storage.CONTENT/name
            self.write(path,b'SYNTHETIC TINY IMAGE ONLY '+bytes([65+index])*9)
            self.images.append(path)
        self.write(self.root/'config.ini',b'SYNTHETIC config retained\n')
        self.write(self.root/'failed-output.bin',b'SYNTHETIC failed evidence retained\n')
        self.identities = [dict(pid=8100+i,creation_filetime=100000+i,
                               executable=str(self.base/'synthetic-python.exe')) for i in range(5)]
        self.proof_paths = {role:self.root/'proofs'/(role+'.json') for role in storage.ADAPTER_PROOFS}
        admission = dict(version=1,protocol='owned-emulator-archive-ui-v1',
                         guest=dict(root=str(self.root),proposal=dict(sha256=self.proposal_sha)))
        self.write(self.proof_paths['admission'],admission)
        admitted = storage.binding(self.proof_paths['admission'])
        self.proofs = {
            'admission':admission,
            'owner_result':dict(status='child_exited',worker_returncode=0,
                                cleanup_complete=True,output_capture_complete=True),
            'worker_result':dict(protocol=admission['protocol'],admission=admitted,
                worker=self.identities[1],server=self.identities[2],guest=self.identities[4],
                guest_ancestry=[self.identities[3],self.identities[4]],
                cleanup=dict.fromkeys(CLEANUP,True)),
            'after':dict(owner=self.identities[0],admission=admitted,process_handles_closed=True),
        }
        if change is not None:
            change(self.proofs)
        # Rebind the admission role after any deliberately malformed producer
        # fixture so closed-proof semantic tests do not fail on an old hash first.
        self.write(self.proof_paths['admission'],self.proofs['admission'])
        admitted = storage.binding(self.proof_paths['admission'])
        if change is None:
            self.proofs['worker_result']['admission'] = admitted
            self.proofs['after']['admission'] = admitted
        for role,value in self.proofs.items(): self.write(self.proof_paths[role],value)
        closure = dict(proposal_sha256=self.proposal_sha,closure_verified=True,cleanup_complete=True,
                       **{role:storage.binding(path) for role,path in self.proof_paths.items()})
        self.closure = self.root/'guest-storage-closure-v1.json'
        self.write(self.closure,closure)
        storage.record_closed(self.root,self.closure,self.registry)
        self.evidence = self.base/'evidence/manifest-v1.json'
        copies = []
        for relative,path in sorted(storage._files(self.root).items()):
            if relative in storage.DISPOSABLE: continue
            destination = self.base/'evidence/files'/relative
            self.write(destination,path.read_bytes())
            copies.append(dict(relative=relative,binding=storage.binding(destination)))
        self.write(self.evidence,dict(version=1,root=str(self.root),complete=True,files=copies))
        self.plan = storage.plan_retirement(self.root,self.evidence,self.registry)
        self.plan_path = self.base/'reviewed-plan-v1.json'
        self.write(self.plan_path,self.plan)
        self.plan_binding = storage.binding(self.plan_path)
        self.original_charge = storage._charge(self.entry())

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value if isinstance(value,bytes) else storage.encoded(value))

    def entry(self):
        ledger = storage.read_json(self.registry/'ledger-v1.json')
        return copy.deepcopy(next(e for e in ledger['entries'] if e['root'] == str(self.root)))

    def assert_closed_charge(self, test):
        entry = self.entry()
        test.assertEqual(entry['state'],'closed')
        test.assertEqual(storage._charge(entry),self.original_charge)


class FakeNative:
    """Simulates native ownership only; can remove ONLY this fixture's tiny images on close."""
    def __init__(self, fixture, error_class, *, fail_mark=None, cleanup=True, process_error=False,
                 acquire_error=False, after_mark=None, before_mark=None):
        self.fixture=fixture; self.error=error_class; self.fail_mark=fail_mark; self.cleanup=cleanup
        self.process_error=process_error; self.acquire_error=acquire_error
        self.after_mark=after_mark; self.before_mark=before_mark
        self.events=[]; self.instances=[]; self.process_inputs=[]
        fake=self
        class ImageSet:
            def __init__(self,bindings,deadline):
                fake.events.append('acquire-all')
                assert bindings == fake.fixture.plan['remove']
                assert all(Path(p['path']) in fake.fixture.images for p in bindings)
                if fake.acquire_error: raise fake.error('ownership')
                self.bindings=copy.deepcopy(bindings);self.marked=[];self.closed=False;self.close_calls=0
                fake.instances.append(self)
            @property
            def snapshots(self):
                return [dict(binding=copy.deepcopy(pin),identity=dict(volume_serial=1,file_index=i+1,
                    bytes=pin['bytes'],links=1,creation_filetime=100+i,write_filetime=200+i,attributes=32))
                    for i,pin in enumerate(self.bindings)]
            def verify(self): fake.events.append('verify');return True
            def mark_delete(self,index):
                fake.events.append('mark:'+str(index))
                if fake.before_mark: fake.before_mark(index)
                if index == fake.fail_mark: raise fake.error('mark')
                self.marked.append(index)
                if fake.after_mark: fake.after_mark(index)
            def close(self):
                self.close_calls+=1;fake.events.append('close')
                for index in self.marked:
                    path=Path(self.bindings[index]['path'])
                    assert path in fake.fixture.images and path.is_relative_to(fake.fixture.root)
                    assert path.read_bytes().startswith(b'SYNTHETIC TINY IMAGE ONLY ')
                    path.unlink()
                self.closed=fake.cleanup
                if not fake.cleanup: raise fake.error('close',cleanup_known=False)
                return True
        self.ImageSet=ImageSet

    def processes(self,identities,deadline):
        self.events.append('processes');self.process_inputs=copy.deepcopy(identities)
        assert all(value in self.fixture.identities for value in identities)
        if self.process_error: raise self.error('process',cleanup_known=False)
        return [dict(identity=copy.deepcopy(value),status='exited') for value in identities]
