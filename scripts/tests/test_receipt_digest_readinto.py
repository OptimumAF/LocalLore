"""Selected readinto candidate boundaries; no baseline regression is claimed.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from benchmarks import receipt_avd_environment as env
from scripts.tests import test_receipt_digest_stream as fixtures


class CountStream:
    def __init__(self,counts):
        self.counts=counts;self.calls=0;self.closed=False;self.exit_exception=None
    def __enter__(self):return self
    def __exit__(self,kind,value,traceback):
        self.closed=True;self.exit_exception=value;return False
    def read(self,*args):raise AssertionError('selected-candidate checks require readinto')
    def readinto(self,target):
        self.calls+=1
        if self.calls>len(self.counts):raise AssertionError('invalid count was retried')
        target[:3]=b'xyz'
        return self.counts[self.calls-1](len(target))


class ReceiptDigestReadintoTests(unittest.TestCase):
    def setUp(self):
        self.base=Path(tempfile.mkdtemp(prefix='locallore-digest-count-',dir='D:/Dev/_Temp'))
        self.assertEqual(self.base.drive.upper(),'D:')
        self.path=self.base/'synthetic.bin';self.path.write_bytes(b'original synthetic bytes')

    def digest(self,stream,hasher):
        original=Path.open
        def opened(path,*args,**kwargs):
            if path==self.path:
                self.assertEqual(args,('rb',));self.assertEqual(kwargs,{})
                return stream
            return original(path,*args,**kwargs)
        with patch.object(Path,'open',autospec=True,side_effect=opened),patch.object(env.hashlib,'sha256',return_value=hasher):
            return env.digest(self.path)

    def test_malformed_counts_refuse_once_before_hash_update_and_close_context(self):
        class CountSubclass(int):pass
        factories=(lambda n:None,lambda n:False,lambda n:True,lambda n:-1,
                   lambda n:n+1,lambda n:1.0,lambda n:float('nan'),
                   lambda n:'private-count-canary',lambda n:object(),lambda n:CountSubclass(1))
        for index,factory in enumerate(factories):
            with self.subTest(case=index):
                stream=CountStream([factory]);hasher=Mock()
                try:self.digest(stream,hasher)
                except env.EnvironmentRefused as error:
                    self.assertEqual(str(error),'invalid_hash_read')
                    self.assertIs(stream.exit_exception,error)
                else:self.fail('malformed count produced a digest')
                self.assertEqual(stream.calls,1);self.assertTrue(stream.closed)
                hasher.update.assert_not_called();hasher.hexdigest.assert_not_called()

    def test_invalid_count_after_valid_short_read_does_not_hash_invalid_bytes_or_finalize(self):
        accepted=[];hasher=Mock();hasher.update.side_effect=lambda value:accepted.append(bytes(value))
        stream=CountStream([lambda n:1,lambda n:None])
        with self.assertRaisesRegex(env.EnvironmentRefused,'^invalid_hash_read$'):
            self.digest(stream,hasher)
        self.assertEqual(accepted,[b'x']);self.assertEqual(stream.calls,2)
        self.assertTrue(stream.closed);hasher.hexdigest.assert_not_called()

    def test_hash_update_failure_or_cancellation_keeps_exception_identity_and_closes_stream(self):
        for failure in (RuntimeError('original hash update failure'),KeyboardInterrupt(),SystemExit(11)):
            with self.subTest(error=type(failure).__name__):
                stream=fixtures.FragmentedBinary(bytes(range(256)))
                hasher=Mock();hasher.update.side_effect=failure
                try:self.digest(stream,hasher)
                except BaseException as actual:self.assertIs(actual,failure)
                else:self.fail('hash update failure was swallowed')
                self.assertEqual(stream.calls,1);self.assertTrue(stream.closed)
                self.assertIs(stream.exit_exception,failure)
                hasher.hexdigest.assert_not_called()


if __name__=='__main__':unittest.main()
