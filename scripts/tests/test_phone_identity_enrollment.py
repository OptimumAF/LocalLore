"""Original metadata-only enrollment oracles, never human/device authority.

The version and roster fixtures pass their actual pure readers. A synthetic
pin is still only data and cannot authenticate an acquisition or human intent.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import html
import json
import unittest

from benchmarks import phone_identity_enrollment as enrollment
from scripts.tests import test_adb_device_roster as fixture


def encoded(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode('utf-8')


def pin(name, value):
    raw = value if type(value) is bytes else encoded(value)
    return dict(path='D:\\Synthetic\\enrollment\\'+name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def proof(body=fixture.BODY):
    value = fixture.roster.probe(fixture.RosterBackend(body=body), fixture.admission(), fixture.version_proof())
    if not fixture.roster.report_verified(value, fixture.admission()):
        raise AssertionError('original version/roster fixture is invalid')
    return value


def proposal(body=fixture.BODY):
    captured = proof(body)
    return enrollment.make_proposal(pin('result-v1.json', captured), fixture.admission(), captured)


def choice(value, index=0):
    proposal_pin = pin('proposal-v1.json', value)
    selected = dict(version=1, protocol='phone-identity-choice-v1', proposal_sha256=proposal_pin['sha256'],
        candidate_id=value['candidates'][index]['candidate_id'], action='select_for_read_only_inventory',
        human_choice_recorded=True)
    return proposal_pin, selected, pin('human-choice-v1.json', selected)


class PhoneIdentityEnrollmentTests(unittest.TestCase):
    def test_proposal_preserves_eligible_order_without_sole_row_or_usb_authority(self):
        body = b''.join([fixture.device_row('SECOND_USB', transport_id=9, product='second', model='Second', device='two'),
            fixture.device_row('192.0.2.1:5555', transport_id=10, product='network', model='Network', device='net'),
            fixture.device_row('emulator-5554', transport_id=11, product='emu', model='Emulator', device='emu'),
            fixture.device_row('OFFLINE_USB', state='offline', transport_id=12, product='off', model='Offline', device='off'),
            fixture.device_row('FIRST_USB', transport_id=13, product='first', model='First', device='one')])
        value = proposal(body)
        self.assertEqual([candidate['row']['serial'] for candidate in value['candidates']], ['SECOND_USB', 'FIRST_USB'])
        self.assertEqual(value['status'], 'needs_human_selection')
        self.assertEqual(value['purpose'], 'read_only_inventory_identity')
        for name in ('feature_acceptance', 'authority_authenticated', 'grants_device_actions'):
            self.assertIs(value[name], False)
        single = proposal()
        self.assertEqual(single['status'], 'needs_human_selection')
        self.assertNotIn('identity', single); self.assertNotIn('selected', single)
        empty = proposal(b'')
        self.assertEqual((empty['status'], empty['candidates']), ('no_candidates', []))

    def test_candidate_ids_bind_capture_and_exact_row_and_outputs_are_independent(self):
        captured = proof(); capture = pin('result-v1.json', captured)
        original = copy.deepcopy(captured)
        first = enrollment.make_proposal(capture, fixture.admission(), captured)
        self.assertEqual(captured, original)
        self.assertEqual(first, enrollment.make_proposal(copy.deepcopy(capture), fixture.admission(), captured))
        identifier = first['candidates'][0]['candidate_id']
        self.assertRegex(identifier, r'^[0-9a-f]{64}$')
        row_bytes = json.dumps(captured['rows'][0], sort_keys=True, separators=(',', ':'),
                               ensure_ascii=True, allow_nan=False).encode('utf-8')
        self.assertEqual(identifier, hashlib.sha256((capture['sha256']+'\0').encode('ascii')+row_bytes).hexdigest())
        changed_pin = copy.deepcopy(capture); changed_pin['sha256'] = 'a'*64
        self.assertNotEqual(identifier, enrollment.make_proposal(changed_pin, fixture.admission(), captured)['candidates'][0]['candidate_id'])
        changed_report = proof(fixture.device_row('ORIGINAL_USB', transport_id=7,
            product='different product', model='Original_Model', device='fixture'))
        self.assertNotEqual(identifier, enrollment.make_proposal(capture, fixture.admission(), changed_report)['candidates'][0]['candidate_id'])
        copied = enrollment.validate_proposal(first)
        copied['candidates'][0]['row']['serial'] = 'MUTATION'
        self.assertEqual(first['candidates'][0]['row']['serial'], 'ORIGINAL_USB')

    def test_unqualified_roster_never_becomes_an_enrollment_proposal(self):
        for mutate in (lambda r: r.update(socket_closed=False), lambda r: r.update(ownership_verified=False),
                       lambda r: r.update(elapsed_ms=True), lambda r: r['version_proof'].update(response_complete=False),
                       lambda r: r['rows'][0].update(serial='BORROWED_USB')):
            captured = proof(); mutate(captured)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                enrollment.make_proposal(pin('result-v1.json', captured), fixture.admission(), captured)

    def test_proposal_schema_rejects_forged_ids_duplicate_candidates_or_new_authority(self):
        value = proposal()
        for mutate in (lambda p: p.update(version=True), lambda p: p.update(authority_authenticated=True),
                       lambda p: p.update(grants_device_actions=True), lambda p: p.update(purpose='install'),
                       lambda p: p.update(selected_serial='ORIGINAL_USB'),
                       lambda p: p['candidates'][0].update(candidate_id='b'*64),
                       lambda p: p['candidates'].append(copy.deepcopy(p['candidates'][0]))):
            changed = copy.deepcopy(value); mutate(changed)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                enrollment.validate_proposal(changed)

    def test_human_choice_is_exact_sha_and_candidate_binding_not_a_serial_selector(self):
        value = proposal()
        proposal_pin, decision, decision_pin = choice(value)
        identity = enrollment.select_identity(value, proposal_pin, decision, decision_pin)
        self.assertEqual(identity['identity'], {'serial': 'ORIGINAL_USB'})
        self.assertEqual(identity['status'], 'declared_identity')
        self.assertEqual(identity['capture'], value['capture'])
        self.assertEqual(identity['proposal'], proposal_pin); self.assertEqual(identity['decision'], decision_pin)
        for name in ('feature_acceptance', 'authority_authenticated', 'grants_device_actions'):
            self.assertIs(identity[name], False)
        for field, replacement in (('version', True), ('proposal_sha256', 'b'*64),
            ('candidate_id', 'b'*64), ('action', 'install'), ('human_choice_recorded', False), ('serial', 'OTHER_USB')):
            bad = copy.deepcopy(decision); bad[field] = replacement
            with self.subTest(field=field), self.assertRaises(ValueError):
                enrollment.select_identity(value, proposal_pin, bad, pin('human-choice-v1.json', bad))
        bad_pin = copy.deepcopy(proposal_pin); bad_pin['sha256'] = 'c'*64
        with self.assertRaises(ValueError): enrollment.select_identity(value, bad_pin, decision, decision_pin)

    def test_declared_identity_only_adds_serial_to_fresh_roster_metadata(self):
        value = proposal(); proposal_pin, decision, decision_pin = choice(value)
        identity = enrollment.select_identity(value, proposal_pin, decision, decision_pin)
        fresh = fixture.admission()
        admitted = enrollment.inventory_admission(fresh, identity)
        self.assertEqual(admitted['protocol'], 'physical-phone-inventory-v1')
        self.assertEqual(admitted['authorized_serial'], 'ORIGINAL_USB')
        self.assertEqual({key: admitted[key] for key in fresh if key != 'protocol'},
                         {key: fresh[key] for key in fresh if key != 'protocol'})
        admitted['server']['pid'] += 1
        self.assertEqual(fresh, fixture.admission())
        for mutate in (lambda r: r.update(grants_device_actions=True), lambda r: r.update(status='authorized'),
                       lambda r: r['identity'].update(transport_id=7), lambda r: r.update(version=True)):
            bad = copy.deepcopy(identity); mutate(bad)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError): enrollment.validate_identity(bad)

    def test_review_escapes_hostile_metadata_and_cannot_execute_or_autoapprove(self):
        hostile = '<img src=x onerror="alert(1)"> & café'
        value = proposal(fixture.device_row('ORIGINAL_USB', transport_id=7,
            product=hostile, model='Original_Model', device='<a href="https://invalid/">device</a>'))
        rendered = enrollment.render_review(value, pin('proposal-v1.json', value)['sha256'])
        self.assertIn(html.escape(hostile), rendered)
        self.assertNotIn('<img', rendered.lower()); self.assertNotIn('<a ', rendered.lower())
        self.assertNotIn('<script', rendered.lower()); self.assertNotIn('<form', rendered.lower())
        self.assertNotIn('http-equiv="refresh"', rendered.lower())
        self.assertIn('Content-Security-Policy', rendered)
        self.assertIn("default-src 'none'", html.unescape(rendered))
        self.assertIn(value['candidates'][0]['candidate_id'], rendered)
        self.assertIn(pin('proposal-v1.json', value)['sha256'], rendered)


if __name__ == '__main__': unittest.main()
