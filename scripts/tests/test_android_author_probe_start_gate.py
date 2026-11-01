"""Original bounded D fixtures; compiler I/O is mocked, validation is real."""
import io
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

from scripts import build_android_author_process_probe as builder


@unittest.skipUnless(os.name == 'nt', 'The actual native builder requires Windows physical D paths')
class NativeAuthorProbeStartGateTests(unittest.TestCase):
    def setUp(self):
        root = Path(os.environ.get('LOCALLORE_NATIVE_GATE_ROOT', tempfile.gettempdir()))
        if root.drive.upper() != 'D:':
            self.skipTest('Provide a physical D temporary artifact root for this Windows builder')
        root.mkdir(parents=True, exist_ok=True)
        self.base = Path(tempfile.mkdtemp(prefix='native-start-gate-', dir=root))
        self.output = self.base / 'output'; self.output.mkdir()
        self.ndk = self.base / builder.NDK; self.ndk.mkdir()
        llvm = self.ndk / 'toolchains/llvm/prebuilt/windows-x86_64'
        files = {
            self.ndk / 'source.properties': ('Pkg.Revision = ' + builder.NDK + '\n').encode(),
            llvm / 'bin/clang.exe': b'SYNTHETIC compiler bytes, never executable',
            llvm / 'bin/ld.lld.exe': b'SYNTHETIC linker bytes, never executable',
            llvm / 'sysroot/usr/include/asm-generic/unistd.h': b'SYNTHETIC generic header',
            llvm / 'sysroot/usr/include/x86_64-linux-android/asm/unistd_64.h': b'SYNTHETIC x86 header',
        }
        for path, raw in files.items():
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        actual_llvm, tools = builder.tool_inputs(self.ndk)
        self.request = dict(version=1, scope=builder.SCOPE, ndk_revision=builder.NDK,
            target=builder.TARGET, ndk=str(self.ndk), output=str(self.output),
            source=builder.env.binding(builder.ROOT / 'benchmarks/native/android_author_process_probe.c'),
            builder=builder.env.binding(Path(builder.__file__)), tools=tools,
            command=builder.command(actual_llvm, self.output),
            environment={key:str(builder.TEMP) for key in ('TEMP','TMP','TMPDIR')})
        builder.env.create_json(self.output / 'request-v1.json', self.request)
        self.pin = builder.env.binding(self.output / 'request-v1.json')
        self.identity = dict(pid=os.getpid(), creation_filetime=123456789,
                             executable=str(Path(sys.executable)))

    def receipt(self, **changes):
        value = dict(worker=dict(self.identity), request=dict(self.pin)); value.update(changes)
        builder.env.create_json(self.output / 'started-v1.json', value)

    def invoke(self, compile_io, *, clock=100.0, sleep=None):
        stream = SimpleNamespace(buffer=io.BytesIO(builder.GO))
        with mock.patch.object(builder.sys, 'stdin', stream), \
             mock.patch.object(builder.capture, 'run_command', side_effect=compile_io) as dispatch, \
             mock.patch.object(builder.env, 'process_identity', return_value=dict(self.identity)), \
             mock.patch('time.monotonic', return_value=clock), \
             mock.patch('time.sleep', side_effect=sleep) as pause:
            try:
                result = builder.worker(self.output, self.pin['sha256'])
                return result, dispatch, pause
            except builder.env.EnvironmentRefused as error:
                return error, dispatch, pause

    def refused_before_compile(self, *, clock=100.0):
        def forbidden(*args, **kwargs):
            raise builder.env.EnvironmentRefused('synthetic_dispatch_reached')
        result, dispatch, pause = self.invoke(forbidden, clock=clock,
            sleep=lambda _: (_ for _ in ()).throw(AssertionError('Present receipt must not be retried')))
        self.assertIsInstance(result, builder.env.EnvironmentRefused)
        dispatch.assert_not_called()
        pause.assert_not_called()

    @staticmethod
    def tiny_elf():
        # Original 1KiB metadata fixture, not a compiled or runnable SDK artifact.
        raw = bytearray(1024); raw[:7] = b'\x7fELF\x02\x01\x01'
        struct.pack_into('<HH',raw,16,3,62);struct.pack_into('<Q',raw,32,64)
        struct.pack_into('<HH',raw,54,56,3)
        interpreter = b'/system/bin/linker64\0'; raw[256:256+len(interpreter)] = interpreter
        raw[512:521] = b'\0libc.so\0'
        for index, pair in enumerate(((5,512),(10,9),(1,1),(0,0))):
            struct.pack_into('<QQ',raw,768+16*index,*pair)
        for index, header in enumerate(((1,5,0,0,0,1024,1024,16384),
                (3,4,256,256,256,len(interpreter),len(interpreter),1),
                (2,6,768,768,768,64,64,8))):
            struct.pack_into('<IIQQQQQQ',raw,64+56*index,*header)
        return bytes(raw)

    def compile_fixture(self, output, label, command, cwd, environment):
        self.assertEqual(output,self.output);self.assertEqual(label,'compile')
        self.assertEqual(command,self.request['command']);self.assertEqual(cwd,builder.ROOT)
        (output/'android-author-process-probe-v1').write_bytes(self.tiny_elf())

    def test_missing_started_receipt_cannot_dispatch(self):
        # Fixed time crosses the five-second admission boundary without a real sleep.
        ticks=iter((100.0,106.0))
        with mock.patch('time.monotonic',side_effect=lambda:next(ticks)):
            def forbidden(*args,**kwargs):raise builder.env.EnvironmentRefused('synthetic_dispatch_reached')
            with mock.patch.object(builder.sys,'stdin',SimpleNamespace(buffer=io.BytesIO(builder.GO))), \
                 mock.patch.object(builder.capture,'run_command',side_effect=forbidden) as dispatch, \
                 mock.patch.object(builder.env,'process_identity',return_value=dict(self.identity)), \
                 mock.patch('time.sleep',side_effect=AssertionError('Expired barrier must not sleep')):
                with self.assertRaises(builder.env.EnvironmentRefused):builder.worker(self.output,self.pin['sha256'])
                dispatch.assert_not_called()

    def test_present_malformed_receipt_refuses_without_retry(self):
        (self.output/'started-v1.json').write_bytes(b'{malformed')
        self.refused_before_compile()

    def test_foreign_worker_cannot_borrow_request(self):
        self.receipt(worker=dict(self.identity,pid=self.identity['pid']+1))
        self.refused_before_compile()

    def test_foreign_request_cannot_borrow_worker(self):
        self.receipt(request=dict(self.pin,sha256='0'*64))
        self.refused_before_compile()

    def test_extra_started_keys_are_not_authority(self):
        self.receipt(qualified=True)
        self.refused_before_compile()

    def test_valid_started_join_reaches_real_ELF_validation(self):
        self.receipt();result,dispatch,_=self.invoke(self.compile_fixture)
        self.assertEqual(result,0);dispatch.assert_called_once()
        self.assertEqual(builder.elf_image(self.output/'android-author-process-probe-v1')['machine'],62)

    def test_only_absence_may_wait_until_valid_receipt_is_published(self):
        def publish(_):self.receipt()
        result,dispatch,pause=self.invoke(self.compile_fixture,sleep=publish)
        self.assertEqual(result,0);dispatch.assert_called_once();pause.assert_called_once()

    def test_changed_request_bytes_refuse_without_compiler(self):
        self.receipt();(self.output/'request-v1.json').write_bytes(b'{}')
        self.refused_before_compile()

    def test_changed_installed_input_refuses_without_compiler(self):
        self.receipt();(self.ndk/'source.properties').write_bytes(b'Pkg.Revision = changed\n')
        self.refused_before_compile()

    def test_parent_publication_binds_actual_child_and_request_atomically(self):
        output=self.base/'parent-output';identity=dict(self.identity,pid=54321)
        def supervised(command,request,root,seconds,on_started):
            self.assertEqual(seconds,300);self.assertEqual(root,output)
            self.assertTrue(on_started(SimpleNamespace(pid=54321)))
            raise builder.env.EnvironmentRefused('synthetic_parent_stopped')
        with mock.patch.object(builder.env,'supervise',side_effect=supervised), \
             mock.patch.object(builder.env,'process_identity',return_value=identity):
            with self.assertRaises(builder.env.EnvironmentRefused):builder.build(self.ndk,output)
        started=builder.env.read_json(output/'started-v1.json')
        self.assertEqual(set(started),{'worker','request'})
        self.assertEqual(started['worker'],identity)
        self.assertEqual(started['request'],builder.env.binding(output/'request-v1.json'))
        self.assertFalse((output/'started.pending-v1.json').exists())


if __name__ == '__main__':unittest.main()
