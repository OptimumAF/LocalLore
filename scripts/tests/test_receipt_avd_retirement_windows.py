"""Native adversaries and actual tiny Windows-owned objects, never real AVDs.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import ctypes
import importlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_retirement_windows as native
from benchmarks import receipt_avd_environment as environment
from benchmarks import receipt_avd_storage as storage

IDENTITY_KEYS={'volume_serial','file_index','bytes','links','creation_filetime','write_filetime','attributes'}


class NativeImportTests(unittest.TestCase):
    def test_import_has_no_file_kernel_or_process_observation(self):
        try:
            with patch.object(ctypes,'WinDLL',create=True,side_effect=AssertionError('import native call')), \
                 patch.object(Path,'open',side_effect=AssertionError('import file read')), \
                 patch.object(Path,'resolve',side_effect=AssertionError('import metadata')), \
                 patch.object(Path,'stat',side_effect=AssertionError('import metadata')), \
                 patch.object(subprocess,'Popen',side_effect=AssertionError('import process')):
                importlib.reload(native)
        finally:
            importlib.reload(native)


@unittest.skipUnless(os.name=='nt','actual tiny Windows handle tests')
class TinyWindowsImageTests(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='locallore-retirement-native-'))
        self.assertEqual(self.root.drive.upper(),'D:')

    def files(self):
        paths=[]
        for index,name in enumerate(('sdcard.img','userdata-qemu.img.qcow2')):
            path=self.root/name;path.write_bytes(b'SYNTHETIC TINY NATIVE IMAGE '+bytes([65+index])*17)
            paths.append(path)
        return paths,[storage.binding(path)for path in paths]

    def test_hash_held_snapshot_copy_and_by_handle_delete_touch_only_owned_tiny_images(self):
        paths,pins=self.files();sentinel=self.root/'evidence.txt';sentinel.write_bytes(b'preserve me')
        images=native.WindowsImageSet(pins,time.monotonic()+30.0)
        try:
            snapshots=images.snapshots
            self.assertEqual([row['binding']for row in snapshots],pins)
            self.assertTrue(all(set(row)=={'binding','identity'} and set(row['identity'])==IDENTITY_KEYS
                and all(type(value)is int for value in row['identity'].values())for row in snapshots))
            snapshots[0]['binding']['bytes']=999;snapshots[0]['identity']['file_index']=0
            self.assertEqual(images.snapshots[0]['binding'],pins[0])
            self.assertNotEqual(images.snapshots[0]['identity']['file_index'],0)
            self.assertTrue(images.verify())
            images.mark_delete(1)
            self.assertTrue(images.verify()) # Already marked path must not be reopened.
            images.mark_delete(0)
        finally:
            images.close()
        self.assertTrue(images.closed);self.assertTrue(images.close())
        self.assertTrue(all(not path.exists()for path in paths))
        self.assertEqual(sentinel.read_bytes(),b'preserve me')

    def test_held_read_delete_access_refuses_write_and_rename_until_known_close(self):
        paths,pins=self.files();images=native.WindowsImageSet(pins,time.monotonic()+30.0)
        try:
            with self.assertRaises(OSError):
                with paths[0].open('r+b') as stream:stream.write(b'changed')
            with self.assertRaises(OSError):paths[0].rename(self.root/'renamed.img')
            self.assertTrue(images.verify())
        finally:images.close()
        moved=paths[0].rename(self.root/'renamed.img')
        self.assertEqual(storage.binding(moved)['sha256'],pins[0]['sha256'])
        self.assertEqual(storage.binding(paths[1])['sha256'],pins[1]['sha256'])

    def test_hash_size_and_hardlink_refusals_never_delete_and_release_acquired_handles(self):
        for variant in ('hash','size','hardlink'):
            case=self.root/variant;case.mkdir()
            first=case/'sdcard.img';second=case/'userdata-qemu.img'
            first.write_bytes(b'SYNTHETIC first');second.write_bytes(b'SYNTHETIC second')
            pins=[storage.binding(first),storage.binding(second)]
            if variant=='hash':pins[1]['sha256']='0'*64
            elif variant=='size':pins[1]['bytes']+=1
            else:os.link(second,case/'linked-copy.bin')
            with self.subTest(variant=variant),self.assertRaises(native.RetirementWindowsError):
                native.WindowsImageSet(pins,time.monotonic()+30.0)
            self.assertTrue(first.exists());self.assertTrue(second.exists())
            # A lingering DELETE handle would prevent the CRT rename below.
            first.rename(case/'first-still-preserved.bin')

    def test_later_sharing_refusal_releases_every_earlier_acquisition_without_marking(self):
        paths,pins=self.files()
        with paths[1].open('r+b'):
            with self.assertRaises(native.RetirementWindowsError):
                native.WindowsImageSet(pins,time.monotonic()+30.0)
        moved=paths[0].rename(self.root/'first-not-leaked.bin')
        self.assertEqual(storage.binding(moved)['sha256'],pins[0]['sha256'])
        self.assertEqual(storage.binding(paths[1])['sha256'],pins[1]['sha256'])

    def test_mark_indices_and_expired_deadline_cannot_mutate_unreviewed_objects(self):
        paths,pins=self.files()
        with self.assertRaises(native.RetirementWindowsError):
            native.WindowsImageSet(pins,time.monotonic()-1.0)
        for index in (True,-1,2,0.0):
            images=native.WindowsImageSet(pins,time.monotonic()+30.0)
            try:
                with self.subTest(index=index),self.assertRaises(native.RetirementWindowsError):images.mark_delete(index)
            finally:images.close()
        self.assertTrue(all(path.exists()for path in paths))

    def test_owned_live_child_refuses_reused_identity_is_distinct_and_exit_259_is_exited(self):
        script=self.root/'owned-child.py'
        script.write_text('import sys\nsys.stdin.buffer.read(1)\nraise SystemExit(259)\n',encoding='utf8')
        child=subprocess.Popen([sys.executable,'-I','-S','-B',str(script)],cwd=self.root,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        try:
            identity=environment.process_identity(child.pid)
            with self.assertRaises(native.RetirementWindowsError):
                native.closed_processes([identity],time.monotonic()+10.0)
            reused=dict(identity,creation_filetime=identity['creation_filetime']+1)
            self.assertEqual(native.closed_processes([reused],time.monotonic()+10.0),
                             [dict(identity=reused,status='pid_reused')])
            self.assertIsNone(child.poll())
            stdout,stderr=child.communicate(b'x',timeout=10)
            self.assertEqual(child.returncode,259);self.assertEqual(stdout,b'');self.assertEqual(stderr,b'')
            self.assertEqual(native.closed_processes([identity],time.monotonic()+10.0),
                             [dict(identity=identity,status='exited')])
            child._handle.Close()
            rows=native.closed_processes([identity],time.monotonic()+10.0)
            self.assertEqual(rows[0]['identity'],identity)
            self.assertIn(rows[0]['status'],('pid_absent','pid_reused','exited'))
        finally:
            if child.poll() is None:child.kill();child.wait(timeout=10)
            for stream in (child.stdin,child.stdout,child.stderr):
                if stream is not None:stream.close()
            child._handle.Close()


class FakeApi:
    def __init__(self,paths,*,filesystem='NTFS',links=1,fail_close=None,probe_swap=False):
        self.paths=list(paths);self.fs=filesystem;self.links=links;self.fail_close=fail_close
        self.probe_swap=probe_swap;self.events=[];self.handles={};self.positions={};self.next_handle=100
    def allocate(self,path,kind):
        self.next_handle+=1;handle=self.next_handle;self.handles[handle]=(Path(path),kind)
        self.positions[handle]=0;self.events.append((kind,handle));return handle
    def open_image(self,path):return self.allocate(path,'image')
    def open_probe(self,path):return self.allocate(path,'probe')
    def information(self,handle):
        path,kind=self.handles[handle];index=self.paths.index(path)+1
        return dict(volume_serial=1,file_index=index+(100 if kind=='probe'and self.probe_swap else 0),
            bytes=path.stat().st_size,links=self.links,creation_filetime=1000+index,
            write_filetime=2000+index,attributes=32)
    def filesystem(self,handle):return self.fs
    def read(self,handle,limit):
        self.events.append(('read',handle));path,_=self.handles[handle]
        raw=path.read_bytes();start=self.positions[handle];self.positions[handle]+=min(limit,len(raw)-start)
        return raw[start:start+limit]
    def mark(self,handle):self.events.append(('mark',handle));return True
    def close(self,handle):
        self.events.append(('close',handle))
        return handle!=self.fail_close


@unittest.skipUnless(os.name=='nt','D-only native-API simulation')
class NativeApiAdversaries(unittest.TestCase):
    def setUp(self):
        self.root=Path(tempfile.mkdtemp(prefix='locallore-retirement-api-'))
        self.paths=[]
        for index in range(2):
            path=self.root/('image-%d.bin'%index);path.write_bytes(b'SYNTHETIC API '+bytes([65+index])*5)
            self.paths.append(path)
        self.pins=[storage.binding(path)for path in self.paths]

    def test_all_images_are_acquired_before_hashing_or_any_mark(self):
        api=FakeApi(self.paths)
        with patch.object(native,'_WindowsApi',return_value=api):
            images=native.WindowsImageSet(self.pins,time.monotonic()+30.0)
            try:
                first_read=next(i for i,event in enumerate(api.events)if event[0]=='read')
                self.assertEqual(len([e for e in api.events[:first_read]if e[0]=='image']),2)
                self.assertFalse(any(e[0]=='mark'for e in api.events))
                images.mark_delete(0);images.mark_delete(1)
                with self.assertRaises(native.RetirementWindowsError):images.mark_delete(0)
            finally:images.close()

    def test_unsupported_or_unknown_filesystem_links_and_probe_identity_refuse_before_mark(self):
        for variant in ('ReFS','unknown','links','probe_swap'):
            api=FakeApi(self.paths,filesystem='ReFS'if variant=='ReFS'else ''if variant=='unknown'else'NTFS',
                        links=2 if variant=='links'else 1,probe_swap=variant=='probe_swap')
            with self.subTest(variant=variant),patch.object(native,'_WindowsApi',return_value=api):
                with self.assertRaises(native.RetirementWindowsError):
                    native.WindowsImageSet(self.pins,time.monotonic()+30.0)
                self.assertFalse(any(e[0]=='mark'for e in api.events))
                opened=[h for kind,h in api.events if kind in ('image','probe')]
                self.assertTrue(all(('close',h)in api.events for h in opened))

    def test_unknown_close_attempts_all_once_and_cannot_be_retried_as_a_reused_handle(self):
        api=FakeApi(self.paths)
        with patch.object(native,'_WindowsApi',return_value=api):
            images=native.WindowsImageSet(self.pins,time.monotonic()+30.0)
            handles=[h for kind,h in api.events if kind=='image'];api.fail_close=handles[0]
            with self.assertRaises(native.RetirementWindowsError)as error:images.close()
            self.assertFalse(error.exception.cleanup_known);self.assertFalse(images.closed)
            before=list(api.events)
            try:images.close()
            except native.RetirementWindowsError:pass
            self.assertEqual(api.events,before)
            self.assertTrue(all(api.events.count(('close',h))==1 for h in handles))

    def test_held_path_identity_drift_or_expired_clock_refuses_mark_but_still_closes(self):
        for variant in ('identity','deadline'):
            api=FakeApi(self.paths);deadline=time.monotonic()+30.0
            with self.subTest(variant=variant),patch.object(native,'_WindowsApi',return_value=api):
                images=native.WindowsImageSet(self.pins,deadline)
                try:
                    if variant=='identity':
                        api.probe_swap=True
                        with self.assertRaises(native.RetirementWindowsError):images.mark_delete(0)
                    else:
                        with patch.object(native.time,'monotonic',return_value=deadline+1),self.assertRaises(native.RetirementWindowsError):
                            images.mark_delete(0)
                    self.assertFalse(any(kind=='mark'for kind,_ in api.events))
                finally:images.close()
                self.assertTrue(images.closed)

    def test_pid_and_creation_bounds_reject_before_any_api_and_absence_is_explicit(self):
        identity=dict(pid=999,creation_filetime=123,executable=str(self.root/'synthetic.exe'))
        for field,values in (('pid',(True,0,-1,2**32,1.0)),
                             ('creation_filetime',(True,0,-1,2**64,1.0))):
            for value in values:
                bad=dict(identity,**{field:value})
                with self.subTest(field=field,value=value),patch.object(native,'_WindowsApi')as factory:
                    with self.assertRaises(native.RetirementWindowsError):
                        native.closed_processes([identity,bad],time.monotonic()+30.0)
                    factory.assert_not_called()
        with patch.object(native,'_WindowsApi')as factory:
            factory.return_value.open_process.return_value=None
            self.assertEqual(native.closed_processes([identity],time.monotonic()+30.0),
                             [dict(identity=identity,status='pid_absent')])

    def test_same_birth_signaled_process_needs_no_terminated_image_query_and_unknown_states_refuse(self):
        identity=dict(pid=999,creation_filetime=123,executable=str(self.root/'historical-owned.exe'))
        for variant,wait in (('exited',0),('live',258),('unknown_wait',0xffffffff),('unknown_birth',0)):
            with self.subTest(variant=variant),patch.object(native,'_WindowsApi') as factory:
                api=factory.return_value
                api.open_process.return_value=801
                api.process_creation.return_value=identity['creation_filetime']
                if variant=='unknown_birth':api.process_creation.side_effect=OSError('synthetic creation query failure')
                api.process_wait.return_value=wait
                api.process_image.side_effect=OSError('terminated image query unavailable')
                api.close.return_value=True
                rows=None;error=None
                try:rows=native.closed_processes([identity],time.monotonic()+30.0)
                except native.RetirementWindowsError as refused:error=refused
                api.close.assert_called_once_with(801)
                if variant=='exited':
                    self.assertIsNone(error)
                    self.assertEqual(rows,[dict(identity=identity,status='exited')])
                else:
                    self.assertIsInstance(error,native.RetirementWindowsError)
                    self.assertIsNone(rows)
                api.process_image.assert_not_called()
                if variant=='unknown_birth':api.process_wait.assert_not_called()
                else:api.process_wait.assert_called_once_with(801)
