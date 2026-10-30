"""Original synthetic live/death consistency checks; no SDK or process authority.

Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import json
import unittest

from benchmarks import android_live_death_witness as witness


BOOT = 'b26f8418-218c-4f6d-a9b8-ff2095b51172'
PROCESS = dict(pid=8123, uid=10452, start_elapsed_ms=34567)
PINS = dict(author_proof_sha256='a' * 64, import_proof_sha256='b' * 64,
            catalog_sha256='c' * 64, snapshot_sha256='d' * 64)
READY = 90_000_000_000
EXPIRES = READY + 120_000_000_000
TICKS = 456789


def raw(value):
    return json.dumps(value, separators=(',', ':')).encode('utf-8')


def checkpoint():
    return dict(version=1, protocol='original-author-live-checkpoint-v1',
                package='org.locallore.app.litertverify',
                process={**PROCESS, 'start_ticks': TICKS}, **PINS,
                workspace_open=True, model_owner_closed=True, pending=False,
                ready_elapsed_ns=READY, expires_elapsed_ns=EXPIRES)


def packet(state='alive', clock=READY + 1):
    value = dict(version=2, protocol='android-author-process-probe-v2',
                 mode='snapshot', boot_id=BOOT, pid=PROCESS['pid'],
                 expected_uid=PROCESS['uid'], observed_uid=PROCESS['uid'],
                 start_ticks=TICKS, state=state, pidfd_opened=True,
                 poll_revents=0, pidfd_closed=True, proc_opened=True,
                 proc_closed=True, error=None, errno=0, observed_boottime_ns=clock)
    if state == 'exited':
        value['poll_revents'] = 1
    elif state == 'absent':
        value.update(observed_uid=None, start_ticks=None, pidfd_opened=False,
                     poll_revents=None, pidfd_closed=None, proc_opened=False,
                     proc_closed=None, errno=3)
    return value


class LiveProcessDeathWitnessTests(unittest.TestCase):
    def validate(self, value=None, **changes):
        expected = dict(expected_process=copy.deepcopy(PROCESS), **PINS)
        expected.update(changes)
        return witness.validate_checkpoint(raw(checkpoint() if value is None else value), **expected)

    def before(self, value=None, selected=None):
        return witness.validate_before(self.validate() if selected is None else selected,
                                       raw(packet() if value is None else value), BOOT)

    def refused(self, action):
        with self.assertRaises(witness.LiveDeathRefused):
            action()

    def test_complete_checkpoint_is_bound_and_returned_without_aliasing(self):
        source = checkpoint()
        selected = self.validate(source)
        self.assertEqual(selected, source)
        selected['process']['start_ticks'] = 1
        self.assertEqual(source['process']['start_ticks'], TICKS)
        self.assertEqual(self.validate()['process']['start_ticks'], TICKS)
        self.assertNotEqual(TICKS, PROCESS['start_elapsed_ms'])

    def test_checkpoint_rejects_changed_provenance_process_and_fixed_package(self):
        for key in PINS:
            changed = checkpoint(); changed[key] = 'e' * 64
            with self.subTest(pin=key):
                self.refused(lambda: self.validate(changed))
        for key in PROCESS:
            changed = checkpoint(); changed['process'][key] += 1
            with self.subTest(process=key):
                self.refused(lambda: self.validate(changed))
        for change in (dict(package='org.locallore.app'), dict(workspace_open=False),
                       dict(model_owner_closed=False), dict(pending=True)):
            changed = checkpoint(); changed.update(change)
            self.refused(lambda: self.validate(changed))

    def test_checkpoint_closed_schema_types_and_exact_hold_are_required(self):
        for field, value in (('version', True), ('ready_elapsed_ns', True),
                             ('expires_elapsed_ns', float(EXPIRES)), ('workspace_open', 1),
                             ('pending', 0), ('model_owner_closed', 1),
                             ('expires_elapsed_ns', EXPIRES - 1),
                             ('expires_elapsed_ns', EXPIRES + 1),
                             ('ready_elapsed_ns', -1), ('private', 'PRIVATE_CANARY')):
            changed = checkpoint(); changed[field] = value
            with self.subTest(field=field, value=value):
                self.refused(lambda: self.validate(changed))
        for field in checkpoint():
            changed = checkpoint(); del changed[field]
            with self.subTest(missing=field):
                self.refused(lambda: self.validate(changed))
        for field in ('pid', 'uid', 'start_elapsed_ms', 'start_ticks'):
            changed = checkpoint(); changed['process'][field] = True
            with self.subTest(process_bool=field):
                self.refused(lambda: self.validate(changed))
        for encoded in (b'\xff', b'{} trailing', b'{"version":1,"version":1}',
                        raw(checkpoint()).replace(b'"pending":false', b'"pending":NaN')):
            self.refused(lambda: witness.validate_checkpoint(encoded,
                         expected_process=PROCESS, **PINS))

    def test_before_alive_uses_exact_self_ticks_and_reserves_fault_window(self):
        for clock in (READY, EXPIRES - 60_000_000_000):
            source = packet(clock=clock)
            selected = self.before(source)
            self.assertEqual(selected, source)
            selected['start_ticks'] = 1
            self.assertEqual(source['start_ticks'], TICKS)
        for clock in (READY - 1, EXPIRES - 60_000_000_000 + 1, True, 1.5, -1):
            self.refused(lambda: self.before(packet(clock=clock)))
        changed = packet(); changed['start_ticks'] = PROCESS['start_elapsed_ms']
        self.refused(lambda: self.before(changed))

    def test_terminal_or_uncertain_before_never_establishes_live_process(self):
        for state in ('absent', 'exited'):
            with self.subTest(state=state):
                self.refused(lambda: self.before(packet(state)))
        for field, value in (('proc_closed', None), ('proc_closed', False),
                             ('pidfd_closed', None), ('pidfd_closed', False),
                             ('proc_opened', False), ('pidfd_opened', False),
                             ('error', 'close'), ('errno', 5), ('poll_revents', 1)):
            changed = packet(); changed[field] = value
            with self.subTest(field=field, value=value):
                self.refused(lambda: self.before(changed))
        changed = packet(); changed.update(state='refused', error='proc_race', errno=3)
        self.refused(lambda: self.before(changed))

    def test_before_identity_boot_and_v2_packet_are_not_caller_selectable(self):
        for field, value in (('pid', PROCESS['pid'] + 1), ('expected_uid', PROCESS['uid'] + 1),
                             ('observed_uid', PROCESS['uid'] + 1), ('start_ticks', TICKS + 1),
                             ('boot_id', '11223344-5566-7788-99aa-bbccddeeff00'),
                             ('version', 1), ('version', True),
                             ('protocol', 'android-author-process-probe-v1'),
                             ('private', 'PRIVATE_CANARY')):
            changed = packet(); changed[field] = value
            with self.subTest(field=field):
                self.refused(lambda: self.before(changed))
        old = packet(); old.update(version=1, protocol='android-author-process-probe-v1')
        del old['observed_boottime_ns']
        self.refused(lambda: self.before(old))

    def test_after_preserves_matching_absent_and_exited_observations(self):
        selected = self.validate(); before = self.before()
        for state in ('absent', 'exited'):
            source = packet(state, READY + 2)
            result = witness.validate_after(selected, before, raw(source))
            self.assertEqual(result, source)
            result['pid'] = 1
            self.assertEqual(source['pid'], PROCESS['pid'])
        for revents in (1, 16, 17):
            source = packet('exited', READY + 2); source['poll_revents'] = revents
            self.assertEqual(witness.validate_after(selected, before, raw(source)), source)
        source = packet('absent', READY + 2); source.update(proc_opened=True, proc_closed=True)
        self.assertEqual(witness.validate_after(selected, before, raw(source)), source)

    def test_after_rejects_clock_reuse_identity_change_and_unknown_close(self):
        selected = self.validate(); before = self.before()
        for field, value in (('observed_boottime_ns', READY),
                             ('observed_boottime_ns', READY + 1),
                             ('observed_boottime_ns', EXPIRES),
                             ('observed_boottime_ns', True), ('pid', PROCESS['pid'] + 1),
                             ('expected_uid', PROCESS['uid'] + 1),
                             ('start_ticks', TICKS + 1), ('observed_uid', PROCESS['uid'] + 1),
                             ('boot_id', '11223344-5566-7788-99aa-bbccddeeff00'),
                             ('proc_closed', None), ('pidfd_closed', False)):
            changed = packet('exited', READY + 2); changed[field] = value
            with self.subTest(field=field, value=value):
                self.refused(lambda: witness.validate_after(selected, before, raw(changed)))
        for state in ('alive', 'refused'):
            changed = packet(state, READY + 2)
            if state == 'refused': changed.update(error='io', errno=5)
            self.refused(lambda: witness.validate_after(selected, before, raw(changed)))

    def test_after_revalidates_pre_witness_instead_of_trusting_returned_dict(self):
        selected = self.validate()
        for field, value in (('state', 'absent'), ('start_ticks', TICKS + 1),
                             ('observed_boottime_ns', EXPIRES), ('pidfd_closed', None)):
            changed = self.before(); changed[field] = value
            with self.subTest(field=field):
                self.refused(lambda: witness.validate_after(selected, changed,
                             raw(packet('absent', READY + 2))))
        changed = self.validate(); changed['process']['start_ticks'] += 1
        self.refused(lambda: witness.validate_after(changed, self.before(),
                     raw(packet('absent', READY + 2))))


if __name__ == '__main__':
    unittest.main()
