"""Private identity review data, never acquisition or human authorization.

No import-time capture, filesystem, runtime, socket or device operations.
Copyright 2026 LocalLore contributors. SPDX-License-Identifier: Apache-2.0
"""
import copy
import hashlib
import html
import json
from pathlib import PureWindowsPath
import re

from benchmarks import adb_device_roster as roster
from benchmarks import physical_phone_inventory as inventory

PROTOCOL = 'phone-identity-enrollment-v1'
CHOICE_PROTOCOL = 'phone-identity-choice-v1'
PURPOSE = 'read_only_inventory_identity'
ACTION = 'select_for_read_only_inventory'
MAX_JSON = 2 * 1024 * 1024
MAX_CANDIDATES = 256
FLAGS = ('feature_acceptance', 'authority_authenticated', 'grants_device_actions')
PROPOSAL_KEYS = {'version', 'protocol', 'purpose', *FLAGS, 'capture', 'status', 'candidates'}
DECISION_KEYS = {'version', 'protocol', 'proposal_sha256', 'candidate_id', 'action', 'human_choice_recorded'}
IDENTITY_KEYS = {'version', 'protocol', 'purpose', *FLAGS, 'status', 'capture', 'proposal',
                 'decision', 'candidate_id', 'identity'}
REASONS = {'input', 'capture', 'owner', 'source', 'worker', 'version', 'proposal',
           'decision', 'identity', 'path', 'output', 'bindings'}


class EnrollmentRefused(ValueError):
    def __init__(self, reason='input'):
        self.reason = reason if type(reason) is str and reason in REASONS else 'input'
        super().__init__(self.reason)


def need(value, reason='input'):
    if not value:
        raise EnrollmentRefused(reason)


def _obj(value, keys, reason='input'):
    need(type(value) is dict and set(value) == set(keys), reason)


def digest(value, reason='input'):
    need(type(value) is str and re.fullmatch('[0-9a-f]{64}', value) is not None, reason)
    return value


def pin(value, reason='input'):
    _obj(value, ('path', 'bytes', 'sha256'), reason)
    path = value['path']
    need(type(path) is str and 1 <= len(path) <= 32767 and
         not any(ord(c) < 32 or ord(c) == 127 for c in path), reason)
    parsed = PureWindowsPath(path)
    need(parsed.is_absolute() and parsed.drive.upper() == 'D:' and '..' not in parsed.parts, reason)
    need(type(value['bytes']) is int and 0 <= value['bytes'] <= MAX_JSON, reason)
    digest(value['sha256'], reason)
    return copy.deepcopy(value)


def encoded(value):
    raw = (json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                      allow_nan=False)+'\n').encode('utf-8')
    need(0 < len(raw) <= MAX_JSON)
    return raw


def _serial(value):
    return (type(value) is str and re.fullmatch('[A-Za-z0-9_-]{4,128}', value) is not None
            and not value.startswith('emulator-'))


def _metadata(value):
    return (type(value) is str and 0 < len(value.encode('utf-8')) <= 256
            and not any(ord(c) < 32 or ord(c) == 127 for c in value))


def eligible(row):
    """Compatibility with inventory, never proof of USB, hardware or authority."""
    return (type(row) is dict and set(row) == roster.ROW_KEYS and _serial(row['serial'])
            and row['state'] == 'device' and type(row['state']) is str
            and all(_metadata(row[key]) for key in ('product', 'model', 'device'))
            and (row['devpath'] is None or _metadata(row['devpath']))
            and type(row['transport_id']) is int and 1 <= row['transport_id'] <= 2**64-1)


def candidate_id(capture_sha, row):
    digest(capture_sha, 'proposal')
    need(eligible(row), 'proposal')
    canonical = json.dumps(row, sort_keys=True, separators=(',', ':'), ensure_ascii=True,
                           allow_nan=False).encode('utf-8')
    return hashlib.sha256((capture_sha+'\0').encode('ascii')+canonical).hexdigest()


def _header(value, keys, reason):
    _obj(value, keys, reason)
    need(type(value['version']) is int and value['version'] == 1 and
         value['protocol'] == PROTOCOL and value['purpose'] == PURPOSE and
         all(value[name] is False for name in FLAGS), reason)


def make_proposal(capture_pin, admission, report):
    capture = pin(capture_pin, 'capture')
    admitted = roster.validate_admission(admission)
    need(roster.report_verified(report, admitted), 'capture')
    candidates = [dict(candidate_id=candidate_id(capture['sha256'], row), row=copy.deepcopy(row))
                  for row in report['rows'] if eligible(row)]
    proposal = dict(version=1, protocol=PROTOCOL, purpose=PURPOSE,
        feature_acceptance=False, authority_authenticated=False, grants_device_actions=False,
        capture=capture, status='needs_human_selection' if candidates else 'no_candidates', candidates=candidates)
    return validate_proposal(proposal)


def validate_proposal(value):
    _header(value, PROPOSAL_KEYS, 'proposal')
    capture = pin(value['capture'], 'proposal')
    candidates = value['candidates']
    need(type(candidates) is list and len(candidates) <= MAX_CANDIDATES, 'proposal')
    need(value['status'] == ('needs_human_selection' if candidates else 'no_candidates'), 'proposal')
    ids, serials, transports = set(), set(), set()
    for candidate in candidates:
        _obj(candidate, ('candidate_id', 'row'), 'proposal')
        row = candidate['row']
        need(eligible(row) and candidate['candidate_id'] == candidate_id(capture['sha256'], row), 'proposal')
        need(candidate['candidate_id'] not in ids and row['serial'] not in serials
             and row['transport_id'] not in transports, 'proposal')
        ids.add(candidate['candidate_id']); serials.add(row['serial']); transports.add(row['transport_id'])
    encoded(value)
    return copy.deepcopy(value)


def render_review(proposal, proposal_sha256):
    value = validate_proposal(proposal)
    digest(proposal_sha256, 'proposal')
    esc = lambda item: html.escape(str(item), quote=True)
    rows = []
    for index, candidate in enumerate(value['candidates'], 1):
        row = candidate['row']
        cells = (index, candidate['candidate_id'], row['serial'], row['model'], row['product'],
                 row['device'], row['transport_id'], row['devpath'] if row['devpath'] is not None else '(not supplied)')
        rows.append('<tr>'+''.join('<td>'+esc(cell)+'</td>' for cell in cells)+'</tr>')
    message = ('Choose only the exact phone you intend to use, and give the coordinator its row number. '
               'The coordinator must bind your direct choice to the proposal hash below. '
               'A single row is never automatically selected.' if rows else
               'No compatible online candidate was recorded. No identity can be selected from this proposal.')
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; '
        'base-uri &#39;none&#39;; form-action &#39;none&#39;; style-src &#39;unsafe-inline&#39;">'
        '<title>LocalLore phone identity review</title><style>'
        'body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:2rem auto;padding:0 1rem;color:#18202a;background:#fafafa}'
        'table{border-collapse:collapse;width:100%}td,th{border:1px solid #687482;padding:.6rem;text-align:left;overflow-wrap:anywhere}'
        'code{overflow-wrap:anywhere}caption{text-align:left;font-weight:bold;margin:1rem 0}'
        '</style></head><body><h1>Review a phone identity</h1><p>'+esc(message)+'</p>'
        '<p>These are untrusted host metadata, not proof of USB transport, physical hardware, availability or permission. '
        'Review is local. Keep serial numbers and this file out of public reports.</p>'
        '<p>Proposal SHA-256: <code>'+esc(proposal_sha256)+'</code></p>'
        '<table><caption>Recorded candidates</caption><thead><tr>'+''.join('<th>'+esc(label)+'</th>' for label in
            ('Row', 'Candidate ID', 'Serial', 'Model', 'Product', 'Device', 'Transport ID', 'Devpath'))+
        '</tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
        '<p>This page performs no action and grants no device access. After a direct human choice, '
        'fresh inventory must independently verify USB selection before sending any phone command. '
        'Installation and model testing need separate admission.</p></body></html>')


def select_identity(proposal, proposal_pin, decision, decision_pin):
    value = validate_proposal(proposal)
    proposed, chosen = pin(proposal_pin, 'proposal'), pin(decision_pin, 'decision')
    need(proposed['bytes'] == len(encoded(value)) and
         proposed['sha256'] == hashlib.sha256(encoded(value)).hexdigest(), 'proposal')
    _obj(decision, DECISION_KEYS, 'decision')
    need(type(decision['version']) is int and decision['version'] == 1 and
         decision['protocol'] == CHOICE_PROTOCOL and decision['proposal_sha256'] == proposed['sha256']
         and decision['action'] == ACTION and decision['human_choice_recorded'] is True, 'decision')
    digest(decision['candidate_id'], 'decision')
    need(chosen['bytes'] == len(encoded(decision)) and
         chosen['sha256'] == hashlib.sha256(encoded(decision)).hexdigest(), 'decision')
    matches = [item for item in value['candidates'] if item['candidate_id'] == decision['candidate_id']]
    need(len(matches) == 1, 'decision')
    receipt = dict(version=1, protocol=PROTOCOL, purpose=PURPOSE, status='declared_identity',
        feature_acceptance=False, authority_authenticated=False, grants_device_actions=False,
        capture=copy.deepcopy(value['capture']), proposal=proposed, decision=chosen,
        candidate_id=matches[0]['candidate_id'], identity=dict(serial=matches[0]['row']['serial']))
    return validate_identity(receipt)


def validate_identity(value):
    _header(value, IDENTITY_KEYS, 'identity')
    need(value['status'] == 'declared_identity', 'identity')
    for key in ('capture', 'proposal', 'decision'):
        pin(value[key], 'identity')
    digest(value['candidate_id'], 'identity')
    _obj(value['identity'], ('serial',), 'identity')
    need(_serial(value['identity']['serial']), 'identity')
    encoded(value)
    return copy.deepcopy(value)


def inventory_admission(fresh_roster_admission, identity):
    """Declare an IO-validated identity; this never grants execution authority."""
    admitted = roster.validate_admission(fresh_roster_admission)
    declared = validate_identity(identity)
    admitted['protocol'] = inventory.PROTOCOL
    admitted['authorized_serial'] = declared['identity']['serial']
    return inventory.validate_admission(admitted)
