"""Fresh SDK6 metadata adversaries; no device, native or filesystem authority."""
import copy
from pathlib import PureWindowsPath
import unittest

from benchmarks import owned_live_death_contract as live
from benchmarks import owned_restart_contract as restart
from scripts.tests import test_owned_restart_contract as fixture


def admission():
    """Original synthetic metadata, never a retagged captured admission."""
    value = fixture.admission()
    value['protocol'] = 'owned-emulator-live-death-target-v1'
    value['guest']['root'] = 'D:/Dev/Experiments/LocalLore/2026-10-30-live-death-v1/avd-v1'
    value['sources'] = [fixture.f.pin(PureWindowsPath('D:/Synthetic/LocalLore/benchmarks') / name)
                        for name in sorted(live.SOURCE_NAMES)]
    by_name = {PureWindowsPath(row['path']).name: row for row in value['sources']}
    value['server']['sources'] = [copy.deepcopy(by_name[PureWindowsPath(row['path']).name])
                                for row in value['server']['sources']]
    return value


def instrumentation(kind):
    selected = {
        'import': 'org.locallore.app.OriginalAuthorModelInstrumentedTest#importsTheVerifiedOriginalAuthorModelOnce',
        'author_live': 'org.locallore.app.OriginalAuthorModelInstrumentedTest#recordsOneRealAuthorCreationWithLiveDeathCheckpoint',
        'restart': 'org.locallore.app.OriginalAuthorRestartInstrumentedTest#recordsOriginalAuthorAfterExternalRestartWithoutInference',
    }[kind]
    return ['am', 'instrument', '-w', '-r', '-e', 'class', selected,
            'org.locallore.app.litertverify.test/androidx.test.runner.AndroidJUnitRunner']


class OwnedLiveDeathContractTests(unittest.TestCase):
    def setUp(self):
        self.admission = admission()

    def operation(self, argv, stdin=None):
        return live.validate_operation({'argv': argv, 'stdin': stdin}, self.admission)

    def snapshot(self, pid='8123', uid='10421'):
        return [fixture.PROBE_PATH, '--snapshot-v2', pid, uid]

    def refused(self, action):
        with self.assertRaises(live.TargetRefused):
            action()

    def test_fresh_profile_has_complete_fixed_source_closure(self):
        self.assertEqual(live.validate_admission(self.admission), self.admission)
        self.assertEqual(len(live.SOURCE_NAMES), 30)
        self.assertEqual(live.SOURCE_NAMES - restart.SOURCE_NAMES, {
            'owned_live_death_contract.py', 'owned_live_death_owner.py',
            'android_process_client_v6.py', 'android_process_verification_v6.py',
            'android_live_death_witness.py', 'original_author_live_death_controller.py',
        })
        for removed in ('owned_live_death_contract.py', 'android_live_death_witness.py',
                        'receipt_avd_storage.py'):
            with self.subTest(removed=removed):
                changed = copy.deepcopy(self.admission)
                changed['sources'] = [pin for pin in changed['sources']
                                      if PureWindowsPath(pin['path']).name != removed]
                self.refused(lambda: live.validate_admission(changed))

    def test_spent_or_older_guest_cannot_be_relabelled_as_the_new_target(self):
        for root in (fixture.GUEST_ROOT,
                     'D:/Dev/Experiments/LocalLore/2026-10-29-restart-after-metadata-v1/avd-v1',
                     'D:/Dev/Experiments/LocalLore/2026-10-30-live-death-v1/another-avd'):
            with self.subTest(root=root):
                changed = copy.deepcopy(self.admission)
                changed['guest']['root'] = root
                self.refused(lambda: live.validate_admission(changed))
        self.refused(lambda: live.validate_admission(fixture.admission()))

    def test_json_cannot_select_another_implementation_or_relax_the_profile(self):
        for key, value in (('module', 'benchmarks.owned_restart_contract'),
                           ('verifier', 'always_accept'), ('guest_root', fixture.GUEST_ROOT)):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.admission)
                changed[key] = value
                self.refused(lambda: live.validate_admission(changed))
        for key, value in (('memory_mib', 4096), ('cores', 2), ('max_seconds', 1801),
                           ('adb_port', 5555), ('serial', 'emulator-5554')):
            with self.subTest(key=key):
                changed = copy.deepcopy(self.admission)
                changed['guest'][key] = value
                self.refused(lambda: live.validate_admission(changed))

    def test_only_the_new_selected_author_method_claims_author_live(self):
        for kind in ('import', 'author_live', 'restart'):
            with self.subTest(kind=kind):
                argv = instrumentation(kind)
                self.assertEqual(self.operation(argv)['argv'], argv)
                self.assertEqual(live.instrumentation_kind(argv), kind)
        self.assertEqual(live.CLAIM_KINDS, ('import', 'author_live', 'restart'))
        self.refused(lambda: self.operation(fixture.instrumentation('author')))
        changed = instrumentation('author_live')
        changed[6] += ',org.other.Test#run'
        self.refused(lambda: self.operation(changed))

    def test_snapshot_v2_accepts_real_integer_boundaries_and_returns_owned_data(self):
        for pid, uid in (('1', '10000'), ('2147483647', '2147483647')):
            with self.subTest(pid=pid, uid=uid):
                value = {'argv': self.snapshot(pid, uid), 'stdin': None}
                original = copy.deepcopy(value)
                accepted = live.validate_operation(value, self.admission)
                self.assertEqual(accepted, original)
                accepted['argv'][2] = '999'
                self.assertEqual(value, original)

    def test_snapshot_v2_refuses_ambiguous_or_out_of_range_process_identity(self):
        for pid, uid in (('0', '10000'), ('01', '10000'), ('-1', '10000'),
                         ('+1', '10000'), ('1 ', '10000'), ('1\n', '10000'),
                         ('１', '10000'), ('2147483648', '10000'), ('1', '9999'),
                         ('1', '010000'), ('1', '2147483648'), (True, '10000'),
                         ('1', True), (8123, '10000'), ('1', None)):
            with self.subTest(pid=pid, uid=uid):
                self.refused(lambda: self.operation(self.snapshot(pid, uid)))

    def test_snapshot_v2_is_exact_read_only_command_with_no_input_payload(self):
        for argv in (self.snapshot() + ['extra'], self.snapshot()[:-1],
                     [fixture.PROBE_PATH + '-other', '--snapshot-v2', '8123', '10421'],
                     [fixture.PROBE_PATH, '--snapshot', '8123', '10421']):
            with self.subTest(argv=argv):
                self.refused(lambda: self.operation(argv))
        self.refused(lambda: self.operation(self.snapshot(), self.admission['artifacts']['probe']))
        self.assertEqual(self.operation([fixture.PROBE_PATH, '--boot'])['argv'],
                         [fixture.PROBE_PATH, '--boot'])
        changed = copy.deepcopy(self.admission)
        changed['protocol'] = restart.PROTOCOL
        self.refused(lambda: live.validate_operation({'argv': self.snapshot(), 'stdin': None}, changed))

    def test_checkpoint_collection_uses_inherited_read_only_relative_commands(self):
        paths = ['no_backup/original-author-live-checkpoint-v1/' + leaf
                 for leaf in ('ready-v1.json', 'terminal-v1.json', 'catalog-v1.json', 'snapshot-v1.json')]
        for command in ('cat', 'sha256sum', 'stat', 'ls'):
            argv = ['run-as', live.APP, '--user', '0', command, *paths]
            with self.subTest(command=command):
                self.assertEqual(self.operation(argv)['argv'], argv)
        argv = ['run-as', live.APP, '--user', '0', 'tar', '-cf', '-', *paths]
        self.assertEqual(self.operation(argv)['argv'], argv)

    def test_checkpoint_reads_cannot_escape_or_select_another_uid_or_shell(self):
        prefix = ['run-as', live.APP, '--user', '0']
        for suffix in (['cat', '/data/system/users/0.xml'], ['cat', 'no_backup/../secret'],
                       ['cat', 'no_backup//secret'], ['cat', 'no_backup/ready;id'],
                       ['sh', '-c', 'cat no_backup/original-author-live-checkpoint-v1/ready-v1.json'],
                       ['dd', 'of=no_backup/original-author-live-checkpoint-v1/ready-v1.json', 'bs=65536']):
            with self.subTest(suffix=suffix):
                self.refused(lambda: self.operation(prefix + suffix))
        for changed in (['run-as', live.TEST, '--user', '0', 'cat', 'no_backup/ready-v1.json'],
                        ['run-as', live.APP, '--user', '10', 'cat', 'no_backup/ready-v1.json']):
            self.refused(lambda: self.operation(changed))

    def test_original_sdk5_still_accepts_only_its_original_identity_and_probe(self):
        prior = fixture.admission()
        self.assertEqual(restart.validate_admission(prior), prior)
        old_probe = [fixture.PROBE_PATH, '--snapshot', '8123', '10421']
        self.assertEqual(restart.validate_operation({'argv': old_probe, 'stdin': None}, prior)['argv'], old_probe)
        self.assertEqual(restart.instrumentation_kind(fixture.instrumentation('author')), 'author')
        for argv in (self.snapshot(), instrumentation('author_live')):
            with self.subTest(argv=argv):
                with self.assertRaises(restart.TargetRefused):
                    restart.validate_operation({'argv': argv, 'stdin': None}, prior)
        self.assertEqual(str(restart.GUEST_ROOT).replace('\\', '/'), fixture.GUEST_ROOT)
        self.assertEqual(restart.CLIENT_VERSION, 5)
        self.assertEqual(restart.SESSION_FILE, 'sdk-session-v5.json')


if __name__ == '__main__':
    unittest.main()
