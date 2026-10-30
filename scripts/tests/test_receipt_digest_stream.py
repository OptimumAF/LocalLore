"""Original byte-stream digest semantics; no performance acceptance or target IO.

All real files are tiny synthetic D fixtures retained for closed-run evidence.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import hashlib
import mmap
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from benchmarks import receipt_avd_environment as env


class FragmentedBinary:
    """One binary stream supports either read API without prescribing selection."""
    def __init__(self,data,fragments=(129,7,1,17),failure=None):
        self.data=data;self.fragments=fragments;self.failure=failure
        self.position=0;self.calls=0;self.closed=False;self.exit_exception=None
        self.read_calls=0;self.readinto_calls=0
    def __enter__(self):return self
    def __exit__(self,kind,value,traceback):
        self.closed=True;self.exit_exception=value;return False
    def chunk(self,capacity):
        self.calls+=1
        if self.failure is not None and self.calls==2:raise self.failure
        size=min(capacity,self.fragments[(self.calls-1)%len(self.fragments)],len(self.data)-self.position)
        value=self.data[self.position:self.position+size];self.position+=size;return value
    def read(self,size=-1):
        self.read_calls+=1
        return self.chunk(len(self.data)if size<0 else size)
    def readinto(self,target):
        self.readinto_calls+=1
        # Poison every unfilled byte, including EOF, to detect stale-tail hashing.
        target[:]=b'\xd3'*len(target)
        value=self.chunk(len(target));target[:len(value)]=value;return len(value)


class ReceiptDigestStreamTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-digest-stream-',dir='D:/Dev/_Temp'))
        self.assertEqual(self.base.drive.upper(),'D:')
        self.path=self.base/'synthetic.bin';self.path.write_bytes(b'placeholder')

    def stream_digest(self,stream):
        original_open=Path.open
        def selected(path,*args,**kwargs):
            if path==self.path:
                self.assertEqual(args,('rb',));self.assertEqual(kwargs,{})
                return stream
            return original_open(path,*args,**kwargs)
        with patch.object(Path,'open',autospec=True,side_effect=selected):
            return env.digest(self.path)

    def test_exact_empty_all_byte_values_and_boundary_tails(self):
        pattern=bytes(range(256))
        self.assertEqual(hashlib.sha256(b'').hexdigest(),'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
        self.assertEqual(hashlib.sha256(pattern).hexdigest(),'40aff2e9d2d8922e47afd4648e6967497158785fbd1da870e7110266bf944880')
        for size in (0,1,255,256,257,65535,65536,65537,1048575,1048576,1048577,2097183):
            with self.subTest(size=size):
                raw=pattern*(size//256)+pattern[:size%256]
                path=self.base/('vector-%d.bin'%size);path.write_bytes(raw)
                self.assertEqual(env.digest(path),hashlib.sha256(raw).hexdigest())

    def test_short_reads_and_poisoned_unfilled_tails_hash_only_observed_bytes(self):
        raw=bytes(range(256))+b'\x1a\x00last original tail\xff'
        stream=FragmentedBinary(raw)
        self.assertEqual(self.stream_digest(stream),hashlib.sha256(raw).hexdigest())
        self.assertEqual(stream.position,len(raw));self.assertGreater(stream.calls,3)
        self.assertTrue(stream.closed);self.assertIsNone(stream.exit_exception)

    def test_empty_stream_context_closes_without_hashing_poison(self):
        stream=FragmentedBinary(b'')
        self.assertEqual(self.stream_digest(stream),hashlib.sha256(b'').hexdigest())
        self.assertTrue(stream.closed);self.assertIsNone(stream.exit_exception)

    def test_read_failures_and_cancellation_keep_exact_exception_and_close_context(self):
        for error in (OSError('original synthetic read failure'),KeyboardInterrupt(),SystemExit(9)):
            with self.subTest(error=type(error).__name__):
                stream=FragmentedBinary(bytes(range(256)),failure=error)
                try:self.stream_digest(stream)
                except BaseException as actual:self.assertIs(actual,error)
                else:self.fail('digest swallowed a read failure')
                self.assertTrue(stream.closed);self.assertIs(stream.exit_exception,error)
                self.assertGreater(stream.position,0)

    def test_missing_and_noncanonical_paths_refuse_before_open(self):
        for path,reason in ((self.base/'missing.bin','missing_path'),(Path('relative-synthetic.bin'),'unsafe_path')):
            with self.subTest(reason=reason),patch.object(Path,'open',side_effect=AssertionError('refused path was opened')):
                with self.assertRaisesRegex(env.EnvironmentRefused,'^'+reason+'$'):env.digest(path)

    def test_reparse_or_symlink_ancestor_refuses_before_open(self):
        original_lstat=Path.lstat
        for mode,attributes in ((stat.S_IFDIR|0o700,0x400),(stat.S_IFLNK|0o700,0)):
            def metadata(path,*args,**kwargs):
                if path==self.base:return SimpleNamespace(st_mode=mode,st_file_attributes=attributes)
                return original_lstat(path,*args,**kwargs)
            with self.subTest(attributes=attributes),patch.object(Path,'lstat',autospec=True,side_effect=metadata),patch.object(Path,'open',side_effect=AssertionError('linked ancestor was followed')):
                with self.assertRaisesRegex(env.EnvironmentRefused,'^unsafe_path$'):env.digest(self.path)

    def test_binding_detects_same_size_change_even_when_mtime_is_restored(self):
        first=bytes(range(256))*16;second=first[::-1]
        self.path.write_bytes(first);saved=env.binding(self.path);metadata=self.path.stat()
        self.path.write_bytes(second)
        os.utime(self.path,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
        self.assertEqual((self.path.stat().st_size,self.path.stat().st_mtime_ns),(len(first),metadata.st_mtime_ns))
        with self.assertRaisesRegex(env.EnvironmentRefused,'^binding_changed$'):env.check_binding(saved)
        current=env.binding(self.path)
        self.assertEqual(current['bytes'],saved['bytes'])
        self.assertEqual(current['sha256'],hashlib.sha256(second).hexdigest())
        self.assertNotEqual(current['sha256'],saved['sha256'])

    def test_binding_detects_flushed_mmap_mutation_with_unchanged_size_and_mtime(self):
        raw=bytes(range(256))*16;self.path.write_bytes(raw)
        saved=env.binding(self.path);metadata=self.path.stat()
        with self.path.open('r+b')as stream:
            with mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_WRITE)as mapped:
                mapped[0:4]=b'\x1a\x00\xfe\xff';mapped[-1]=17;mapped.flush()
        os.utime(self.path,ns=(metadata.st_atime_ns,metadata.st_mtime_ns))
        self.assertEqual((self.path.stat().st_size,self.path.stat().st_mtime_ns),(len(raw),metadata.st_mtime_ns))
        with self.assertRaisesRegex(env.EnvironmentRefused,'^binding_changed$'):env.check_binding(saved)
        expected=b'\x1a\x00\xfe\xff'+raw[4:-1]+bytes([17])
        self.assertEqual(env.digest(self.path),hashlib.sha256(expected).hexdigest())


if __name__=='__main__':unittest.main()
