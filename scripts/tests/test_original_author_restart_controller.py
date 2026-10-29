"""Original controller flow fixtures; target, native, and SDK IO are simulated."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock,patch

from benchmarks import original_author_restart_controller as c
from scripts.tests.test_owned_restart_contract import ClosedRestartGraph


@unittest.skipUnless(os.name=='nt','physical D controller fixtures')
class ControllerBoundaryTests(unittest.TestCase):
    def test_package_getter_stderr_stops_before_any_following_sdk_operation(self):
        g=ClosedRestartGraph();rows=g.rows[3:9];calls=[]
        first=rows[0];first['stderr']=g.save(first['stderr']['path'],b'original getter warning\0\x1a')
        g.save(g.row_pins[3]['path'],first)
        class Capture:
            directory=g.sdk/'clients';count=0
            def shell(self,argv,label,**kwargs):
                row=rows[len(calls)];calls.append(list(argv));self.count=row['index']
                if argv!=row['operation']['argv']:raise AssertionError('unexpected SDK recipe')
                return Path(row['stdout']['path']).read_bytes()
        live=Mock();manifest={'apks':[dict(package=c.contract.APP,sha256=g.a['artifacts']['product_apk']['sha256']),
            dict(package=c.contract.TEST,sha256=g.a['artifacts']['test_apk']['sha256'])]}
        with self.assertRaises((ValueError,c.env.EnvironmentRefused)):
            c._installed(Capture(),live,manifest)
        self.assertEqual(len(calls),1)

    def test_output_under_git_refuses_before_creating_evidence_or_input_dispatch(self):
        base=Path(tempfile.mkdtemp(prefix='locallore-restart-controller-git-',dir='D:/Dev/_Temp'))
        (base/'.git').mkdir();output=base/'output';before=list(base.iterdir())
        with patch.object(c,'_verify_inputs',side_effect=ValueError('unexpected input dispatch'))as inputs:
            with self.assertRaises((ValueError,c.env.EnvironmentRefused)):
                c.run({}, {}, {}, output)
        inputs.assert_not_called();self.assertFalse(output.exists());self.assertEqual(list(base.iterdir()),before)


if __name__=='__main__':unittest.main()
