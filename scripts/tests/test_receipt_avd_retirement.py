"""Original exact-plan orchestrator adversaries over tiny isolated D: data.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import contextlib
import copy
import ctypes
import importlib
import io
import os
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_retirement as retirement
from benchmarks import receipt_avd_storage as storage
from scripts.tests import test_receipt_avd_retirement_fixtures as f


class RetirementImportAndConsentTests(unittest.TestCase):
    def test_import_performs_no_metadata_file_native_or_process_io(self):
        try:
            with contextlib.ExitStack() as stack:
                for method in ('resolve','open','stat','lstat','mkdir'):
                    stack.enter_context(patch.object(Path,method,side_effect=AssertionError('import filesystem IO')))
                stack.enter_context(patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('import native IO')))
                stack.enter_context(patch.object(subprocess,'Popen',side_effect=AssertionError('import process IO')))
                importlib.reload(retirement)
        finally:
            importlib.reload(retirement)

    def test_absent_or_nonboolean_consent_refuses_before_any_io_for_both_apis(self):
        for flag in (False,None,0,1,'true',[]):
            with self.subTest(flag=flag), contextlib.ExitStack() as stack:
                for method in ('resolve','open','stat','lstat','mkdir'):
                    stack.enter_context(patch.object(Path,method,side_effect=AssertionError('unauthorized filesystem IO')))
                native=stack.enter_context(patch.object(retirement.windows,'WindowsImageSet',side_effect=AssertionError('unauthorized native IO')))
                for call in (lambda:retirement.execute({},'D:/Synthetic/no-output',execute_reviewed_plan=flag),
                             lambda:retirement._execute({},'D:/Synthetic/no-output','D:/Synthetic/no-registry',execute_reviewed_plan=flag)):
                    with self.assertRaises(retirement.RetirementRefused) as error: call()
                    self.assertEqual(error.exception.reason,'not_authorized')
                native.assert_not_called()


@unittest.skipUnless(os.name=='nt','D-only synthetic retirement registry')
class RetirementExecutorTests(unittest.TestCase):
    def execute(self, fixture, fake, **kwargs):
        with patch.object(retirement.windows,'WindowsImageSet',fake.ImageSet), \
             patch.object(retirement.windows,'closed_processes',side_effect=fake.processes):
            return retirement._execute(fixture.plan_binding,fixture.output,fixture.registry,
                                       execute_reviewed_plan=True,**kwargs)

    def assert_refused(self, fixture, fake):
        try:
            result=self.execute(fixture,fake)
        except (retirement.RetirementRefused,storage.StorageRefused,retirement.windows.RetirementWindowsError,OSError):
            result=None
        if result is not None: self.assertEqual(result['outcome'],'refused')
        fixture.assert_closed_charge(self)
        return result

    def test_complete_exact_plan_keeps_lock_and_durable_intent_through_finalization(self):
        fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
        original=storage._record_retired_locked
        def before_mark(index):
            self.assertTrue((fixture.registry/'admission.lock').is_file())
            intent=storage.read_json(fixture.output/('attempt-%02d-v1.json'%(index+1)))
            self.assertEqual(intent['planned'],fixture.plan['remove'][index]);self.assertEqual(intent['phase'],'before_mark')
            with self.assertRaisesRegex(storage.StorageRefused,'^registry_locked$'):
                storage.reserve_prepare(fixture.base/('contender-%d'%index),'a'*64,fixture.registry)
        fake.before_mark=before_mark
        def finalize(*args):
            self.assertTrue((fixture.registry/'admission.lock').is_file())
            self.assertTrue(fake.instances[0].closed)
            self.assertTrue(all(not path.exists()for path in fixture.images))
            return original(*args)
        with patch.object(storage,'_record_retired_locked',side_effect=finalize) as finalizer:
            result=self.execute(fixture,fake)
        self.assertEqual(result['outcome'],'completed');self.assertTrue(result['cleanup_known'])
        self.assertTrue(result['retirement_recorded']);self.assertEqual(result['marked_count'],2)
        self.assertEqual(result['attempted_count'],2);self.assertEqual(finalizer.call_count,1)
        self.assertEqual(fake.events[:2],['acquire-all','processes'])
        self.assertEqual(fake.process_inputs,fixture.identities)
        self.assertFalse((fixture.registry/'admission.lock').exists())
        self.assertEqual(fixture.entry()['state'],'retired');self.assertEqual(storage._charge(fixture.entry()),0)
        self.assertEqual((fixture.root/'failed-output.bin').read_bytes(),b'SYNTHETIC failed evidence retained\n')

    def test_stale_plan_pin_or_changed_plan_cannot_acquire_or_mark_images(self):
        for variant in ('stale_hash','reordered','boolean_version'):
            fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
            value=copy.deepcopy(fixture.plan)
            if variant=='reordered':value['remove'].reverse()
            elif variant=='boolean_version':value['version']=True
            else:value['action']='changed'
            fixture.write(fixture.plan_path,value)
            if variant!='stale_hash':fixture.plan_binding=storage.binding(fixture.plan_path)
            with self.subTest(variant=variant):
                self.assert_refused(fixture,fake);self.assertEqual(fake.events,[])

    def test_changed_evidence_preserved_files_or_added_image_refuse_before_ownership(self):
        for variant in ('evidence','preserved','extra_image','unknown_image','proof'):
            fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
            if variant=='evidence':fixture.evidence.write_bytes(b'changed')
            elif variant=='preserved':(fixture.root/'failed-output.bin').write_bytes(b'changed')
            elif variant=='extra_image':fixture.write(fixture.root/storage.CONTENT/'cache.img',b'SYNTHETIC extra')
            elif variant=='unknown_image':fixture.write(fixture.root/'unknown.img',b'SYNTHETIC unknown')
            else:fixture.proof_paths['after'].write_bytes(b'changed')
            with self.subTest(variant=variant):
                self.assert_refused(fixture,fake);self.assertEqual(fake.events,[])

    def test_coherent_rebound_proofs_still_require_typed_owner_cleanup_and_identity(self):
        changes=(lambda x:x['owner_result'].update(worker_returncode=False),
                 lambda x:x['owner_result'].update(output_capture_complete=False),
                 lambda x:x['after'].update(process_handles_closed=False),
                 lambda x:x['worker_result']['cleanup'].update(server_pipes_closed=False),
                 lambda x:x['worker_result'].update(protocol='unreviewed-profile'),
                 lambda x:x['after']['owner'].update(pid=True),
                 lambda x:x['after']['owner'].update(pid=2**32),
                 lambda x:x['after']['owner'].update(creation_filetime=2**64),
                 lambda x:x['worker_result']['guest_ancestry'].append(dict(x['worker_result']['guest'],creation_filetime=999)))
        for index,change in enumerate(changes):
            fixture=f.TinyRetirement(change);fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
            with self.subTest(case=index):
                self.assert_refused(fixture,fake);self.assertEqual(fake.events,[])

    def test_ownership_and_process_uncertainty_close_resources_without_marking(self):
        for variant in ('acquire','process'):
            fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError,
                acquire_error=variant=='acquire',process_error=variant=='process')
            with self.subTest(variant=variant):
                result=self.assert_refused(fixture,fake)
                self.assertEqual(result['marked_count'],0)
                self.assertFalse(any(e.startswith('mark:')for e in fake.events))
                self.assertTrue(all(path.exists()for path in fixture.images))
                if variant=='process':
                    self.assertEqual(fake.instances[0].close_calls,1)
                    self.assertFalse(result['cleanup_known'])

    def test_partial_mark_and_unknown_close_preserve_closed_charge_and_stop(self):
        for variant in ('second_mark','unknown_close'):
            fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError,
                fail_mark=1 if variant=='second_mark'else None,cleanup=variant!='unknown_close')
            with self.subTest(variant=variant):
                result=self.assert_refused(fixture,fake)
                self.assertFalse(result['retirement_recorded']);self.assertEqual(fake.instances[0].close_calls,1)
                self.assertEqual(result['attempted_count'],2)
                self.assertEqual(result['marked_count'],1 if variant=='second_mark'else 2)
                if variant=='unknown_close':self.assertFalse(result['cleanup_known'])

    def test_proof_drift_after_first_mark_stops_before_the_next_mark(self):
        fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError,
            after_mark=lambda index:fixture.proof_paths['after'].write_bytes(b'changed after first mark'))
        result=self.assert_refused(fixture,fake)
        self.assertEqual(result['marked_count'],1);self.assertEqual(result['attempted_count'],1)
        self.assertNotIn('mark:1',fake.events);self.assertTrue(fixture.images[1].exists())

    def test_intent_write_failure_prevents_mark_and_postmark_write_failure_cannot_finalize(self):
        for failed_name,marked in (('attempt-01-v1.json',0),('marked-01-v1.json',1)):
            fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
            original=retirement._write
            def write(output,identity,name,value):
                if name==failed_name:raise OSError('synthetic durable output failure')
                return original(output,identity,name,value)
            with self.subTest(name=failed_name),patch.object(retirement,'_write',side_effect=write):
                result=self.assert_refused(fixture,fake)
                self.assertEqual(result['marked_count'],marked)
                self.assertFalse(result['retirement_recorded'])

    def test_finalizer_failure_never_infers_committed_state_from_mutated_entry(self):
        fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
        def fail(root,plan,registry,ledger,entry):
            entry['state']='retired'
            raise OSError('synthetic finalization failure before durable commit')
        with patch.object(storage,'_record_retired_locked',side_effect=fail):
            result=self.assert_refused(fixture,fake)
        self.assertIsNone(result['retirement_recorded']);self.assertEqual(result['marked_count'],2)

    def test_result_publication_failure_after_commit_does_not_pretend_rollback(self):
        fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
        original=retirement._write
        def fail(output,identity,name,value):
            if name=='result-v1.json':raise OSError('synthetic final result publication failure')
            return original(output,identity,name,value)
        with patch.object(retirement,'_write',side_effect=fail),self.assertRaises(OSError):self.execute(fixture,fake)
        self.assertEqual(fixture.entry()['state'],'retired')
        self.assertFalse((fixture.output/'result-v1.json').exists())
        self.assertFalse((fixture.registry/'admission.lock').exists())

    def test_unlock_failure_after_commit_reports_recorded_retirement_without_completion(self):
        fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
        original=Path.unlink;lock=fixture.registry/'admission.lock'
        def unlink(path,*args,**kwargs):
            if path==lock:raise OSError('synthetic unlock failure after durable commit')
            return original(path,*args,**kwargs)
        with patch.object(Path,'unlink',new=unlink):result=self.execute(fixture,fake)
        self.assertEqual(result['outcome'],'refused');self.assertEqual(result['phase'],'unlock')
        self.assertIs(result['retirement_recorded'],True);self.assertIs(result['cleanup_known'],True)
        self.assertEqual(fixture.entry()['state'],'retired');self.assertEqual(storage._charge(fixture.entry()),0)
        self.assertTrue(lock.exists());self.assertEqual(fake.instances[0].close_calls,1)

    def test_output_inside_guest_or_registry_refuses_before_native_ownership(self):
        for role in ('guest','registry'):
            fixture=f.TinyRetirement();fake=f.FakeNative(fixture,retirement.windows.RetirementWindowsError)
            fixture.output=(fixture.root if role=='guest'else fixture.registry)/'forbidden-output'
            with self.subTest(role=role):
                self.assert_refused(fixture,fake)
                self.assertFalse(fixture.output.exists());self.assertEqual(fake.events,[])
